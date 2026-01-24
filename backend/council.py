"""Executive Board Council orchestration with role-based perspectives and cross-evaluation."""

from typing import List, Dict, Any, Tuple
from .openrouter import query_model, query_executives_parallel
from .config import (
    EXECUTIVE_ROLES,
    COUNCIL_SPEAKER_MODEL,
    COUNCIL_SPEAKER_PERSONA
)


async def stage1_collect_perspectives(user_query: str) -> List[Dict[str, Any]]:
    """
    Stage 1: Collect individual perspectives from all executive board members.

    Each executive analyzes the situation from their specific role and expertise.

    Args:
        user_query: The business situation/question to analyze

    Returns:
        List of dicts with 'role', 'title', 'model', and 'response' keys
    """
    # Prepare executive configs for parallel querying
    executives = {
        role_key: {
            'model': role_config['model'],
            'persona': role_config['persona']
        }
        for role_key, role_config in EXECUTIVE_ROLES.items()
    }

    # Build the prompt for executives
    executive_prompt = f"""The Executive Board is meeting to discuss the following business situation:

---
{user_query}
---

Please analyze this situation from your specific executive perspective. Consider:
1. Key issues and concerns from your area of responsibility
2. Potential impacts on your domain
3. Risks and opportunities you identify
4. Your recommendations and priorities

Provide a thoughtful, detailed analysis that reflects your role's expertise and concerns."""

    # Query all executives in parallel
    responses = await query_executives_parallel(executives, executive_prompt)

    # Format results
    stage1_results = []
    for role_key, response in responses.items():
        if response is not None:
            stage1_results.append({
                "role": role_key,
                "title": EXECUTIVE_ROLES[role_key]["title"],
                "model": EXECUTIVE_ROLES[role_key]["model"],
                "response": response.get('content', '')
            })

    return stage1_results


async def stage2_cross_evaluation(
    user_query: str,
    stage1_results: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Stage 2: Each executive evaluates other executives' perspectives.

    Executives review each other's analyses and provide feedback,
    identifying strengths, weaknesses, and areas of agreement/disagreement.

    Args:
        user_query: The original business situation
        stage1_results: Results from Stage 1

    Returns:
        Tuple of (evaluations list, role_to_label mapping)
    """
    # Create anonymized labels for responses
    labels = [chr(65 + i) for i in range(len(stage1_results))]  # A, B, C, ...

    # Create mapping from label to role
    label_to_role = {
        f"Perspective {label}": result['role']
        for label, result in zip(labels, stage1_results)
    }

    # Build the perspectives text
    perspectives_text = "\n\n".join([
        f"Perspective {label} ({result['title']}):\n{result['response']}"
        for label, result in zip(labels, stage1_results)
    ])

    # Prepare evaluation configs
    executives = {
        role_key: {
            'model': role_config['model'],
            'persona': role_config['persona']
        }
        for role_key, role_config in EXECUTIVE_ROLES.items()
    }

    evaluation_prompt = f"""The Executive Board is discussing the following business situation:

---
{user_query}
---

Your fellow board members have provided their initial analyses:

{perspectives_text}

As a board member, please:
1. Evaluate each perspective - what are the strengths and potential blind spots?
2. Identify where you agree and disagree with other executives
3. Highlight any critical points that may have been overlooked
4. Consider how different perspectives complement or conflict with each other

At the end, provide a RANKING of the perspectives from most valuable to least valuable for this specific situation, considering:
- Relevance to the core issue
- Completeness of analysis
- Practical applicability of recommendations

FINAL RANKING:
1. [Most valuable perspective]
2. [Second most valuable]
... and so on"""

    # Query all executives in parallel for their evaluations
    responses = await query_executives_parallel(executives, evaluation_prompt)

    # Format results
    stage2_results = []
    for role_key, response in responses.items():
        if response is not None:
            full_text = response.get('content', '')
            parsed = parse_ranking_from_text(full_text)
            stage2_results.append({
                "role": role_key,
                "title": EXECUTIVE_ROLES[role_key]["title"],
                "model": EXECUTIVE_ROLES[role_key]["model"],
                "evaluation": full_text,
                "parsed_ranking": parsed
            })

    return stage2_results, label_to_role


async def stage3_council_speaker_synthesis(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Stage 3: Council Speaker synthesizes all perspectives into a final decision.

    The Council Speaker acts as a neutral facilitator, weighing all perspectives
    and their cross-evaluations to produce a balanced, actionable recommendation.

    Args:
        user_query: The original business situation
        stage1_results: Individual executive perspectives from Stage 1
        stage2_results: Cross-evaluations from Stage 2

    Returns:
        Dict with 'model' and 'response' keys
    """
    # Build comprehensive context for the Council Speaker
    stage1_text = "\n\n".join([
        f"**{result['title']} ({result['role']})**:\n{result['response']}"
        for result in stage1_results
    ])

    stage2_text = "\n\n".join([
        f"**Evaluation by {result['title']} ({result['role']})**:\n{result['evaluation']}"
        for result in stage2_results
    ])

    speaker_prompt = f"""{COUNCIL_SPEAKER_PERSONA}

---

EXECUTIVE BOARD MEETING

**Business Situation Under Discussion:**
{user_query}

---

**STAGE 1 - Individual Executive Perspectives:**

{stage1_text}

---

**STAGE 2 - Cross-Evaluations and Rankings:**

{stage2_text}

---

As the Council Speaker, please synthesize all perspectives and evaluations into a comprehensive final recommendation for the board. Follow the structure outlined in your role description."""

    messages = [{"role": "user", "content": speaker_prompt}]

    # Query the Council Speaker model
    response = await query_model(COUNCIL_SPEAKER_MODEL, messages)

    if response is None:
        return {
            "model": COUNCIL_SPEAKER_MODEL,
            "response": "Error: Unable to generate final synthesis. The Council Speaker was unable to provide a response."
        }

    return {
        "model": COUNCIL_SPEAKER_MODEL,
        "response": response.get('content', '')
    }


def parse_ranking_from_text(ranking_text: str) -> List[str]:
    """
    Parse the FINAL RANKING section from an executive's evaluation.

    Args:
        ranking_text: The full text response from the executive

    Returns:
        List of perspective labels in ranked order
    """
    import re

    # Look for "FINAL RANKING:" section
    if "FINAL RANKING:" in ranking_text:
        parts = ranking_text.split("FINAL RANKING:")
        if len(parts) >= 2:
            ranking_section = parts[1]
            # Try to extract numbered list format (e.g., "1. Perspective A")
            numbered_matches = re.findall(r'\d+\.\s*Perspective [A-Z]', ranking_section)
            if numbered_matches:
                return [re.search(r'Perspective [A-Z]', m).group() for m in numbered_matches]

            # Fallback: Extract all "Perspective X" patterns in order
            matches = re.findall(r'Perspective [A-Z]', ranking_section)
            return matches

    # Fallback: try to find any "Perspective X" patterns in order
    matches = re.findall(r'Perspective [A-Z]', ranking_text)
    return matches


def calculate_aggregate_rankings(
    stage2_results: List[Dict[str, Any]],
    label_to_role: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Calculate aggregate rankings across all executives.

    Args:
        stage2_results: Evaluations from each executive
        label_to_role: Mapping from anonymous labels to role names

    Returns:
        List of dicts with role name and average rank, sorted best to worst
    """
    from collections import defaultdict

    # Track positions for each role
    role_positions = defaultdict(list)

    for evaluation in stage2_results:
        parsed_ranking = evaluation.get('parsed_ranking', [])

        for position, label in enumerate(parsed_ranking, start=1):
            if label in label_to_role:
                role_name = label_to_role[label]
                role_positions[role_name].append(position)

    # Calculate average position for each role
    aggregate = []
    for role, positions in role_positions.items():
        if positions:
            avg_rank = sum(positions) / len(positions)
            aggregate.append({
                "role": role,
                "title": EXECUTIVE_ROLES.get(role, {}).get("title", role),
                "average_rank": round(avg_rank, 2),
                "rankings_count": len(positions)
            })

    # Sort by average rank (lower is better)
    aggregate.sort(key=lambda x: x['average_rank'])

    return aggregate


async def generate_meeting_title(user_query: str) -> str:
    """
    Generate a short title for the board meeting based on the topic.

    Args:
        user_query: The business situation being discussed

    Returns:
        A short title (3-7 words)
    """
    title_prompt = f"""Generate a very short title (3-7 words maximum) that summarizes this executive board meeting topic.
The title should be concise and professional, like a board meeting agenda item.
Do not use quotes or punctuation in the title.

Topic: {user_query}

Title:"""

    messages = [{"role": "user", "content": title_prompt}]

    # Use a fast model for title generation
    response = await query_model("google/gemini-2.0-flash-001", messages, timeout=30.0)

    if response is None:
        return "Executive Board Meeting"

    title = response.get('content', 'Executive Board Meeting').strip()
    title = title.strip('"\'')

    if len(title) > 60:
        title = title[:57] + "..."

    return title


async def run_executive_board_meeting(user_query: str) -> Tuple[List, List, Dict, Dict]:
    """
    Run the complete 3-stage executive board meeting process.

    Args:
        user_query: The business situation/question to discuss

    Returns:
        Tuple of (stage1_results, stage2_results, stage3_result, metadata)
    """
    # Stage 1: Collect individual executive perspectives
    stage1_results = await stage1_collect_perspectives(user_query)

    # If no executives responded successfully, return error
    if not stage1_results:
        return [], [], {
            "model": "error",
            "response": "All executive board members failed to respond. Please try again."
        }, {}

    # Stage 2: Cross-evaluations
    stage2_results, label_to_role = await stage2_cross_evaluation(user_query, stage1_results)

    # Calculate aggregate rankings
    aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_role)

    # Stage 3: Council Speaker synthesizes final recommendation
    stage3_result = await stage3_council_speaker_synthesis(
        user_query,
        stage1_results,
        stage2_results
    )

    # Prepare metadata
    metadata = {
        "label_to_role": label_to_role,
        "aggregate_rankings": aggregate_rankings,
        "executive_roles": {
            role_key: {
                "title": role_config["title"],
                "model": role_config["model"]
            }
            for role_key, role_config in EXECUTIVE_ROLES.items()
        }
    }

    return stage1_results, stage2_results, stage3_result, metadata

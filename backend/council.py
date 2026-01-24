"""Executive Board Council orchestration with role-based perspectives, cross-evaluation, debate, and risk analysis."""

import json
import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

from .openrouter import query_model, query_executives_parallel
from .config import (
    EXECUTIVE_ROLES,
    COUNCIL_SPEAKER_MODEL,
    COUNCIL_SPEAKER_PERSONA,
    RISK_SEVERITY_LEVELS,
    RISK_LIKELIHOOD_LEVELS
)
from .industries import (
    get_industry_executives,
    get_council_speaker_persona,
    COUNCIL_SPEAKER_MODEL as INDUSTRY_COUNCIL_MODEL
)

logger = logging.getLogger(__name__)


async def stage1_collect_perspectives(user_query: str, industry: str = "manufacturing") -> List[Dict[str, Any]]:
    """
    Stage 1: Collect individual perspectives from all executive board members.

    Each executive analyzes the situation from their specific role and expertise,
    including their confidence level and key uncertainties.

    Args:
        user_query: The business situation/question to analyze
        industry: Industry context for specialized executives

    Returns:
        List of dicts with 'role', 'title', 'model', 'response', 'confidence', and 'uncertainties'
    """
    # Get industry-specific executives (fallback to default if not found)
    industry_executives = get_industry_executives(industry) or EXECUTIVE_ROLES

    # Prepare executive configs for parallel querying
    executives = {
        role_key: {
            'model': role_config['model'],
            'persona': role_config['persona']
        }
        for role_key, role_config in industry_executives.items()
    }

    # Build the prompt for executives with confidence scoring
    executive_prompt = f"""The Executive Board is meeting to discuss the following business situation:

---
{user_query}
---

Please analyze this situation from your specific executive perspective. Consider:
1. Key issues and concerns from your area of responsibility
2. Potential impacts on your domain
3. Risks and opportunities you identify
4. Your recommendations and priorities

Provide a thoughtful, detailed analysis that reflects your role's expertise and concerns.

**IMPORTANT: At the end of your analysis, you MUST include:**

## Confidence Assessment
- **CONFIDENCE LEVEL:** [HIGH/MEDIUM/LOW]
- **KEY UNCERTAINTIES:**
  - [List 2-4 main unknowns or assumptions that affect your analysis]

This helps the board understand where more information might be needed."""

    # Query all executives in parallel
    responses = await query_executives_parallel(executives, executive_prompt)

    # Format results with parsed confidence
    stage1_results = []
    for role_key, response in responses.items():
        if response is not None and role_key in industry_executives:
            content = response.get('content', '')
            confidence, uncertainties = parse_confidence_assessment(content)

            stage1_results.append({
                "role": role_key,
                "title": industry_executives[role_key]["title"],
                "model": industry_executives[role_key]["model"],
                "response": content,
                "confidence": confidence,
                "uncertainties": uncertainties
            })

    return stage1_results


def parse_confidence_assessment(text: str) -> Tuple[str, List[str]]:
    """
    Parse confidence level and uncertainties from executive response.

    Args:
        text: The full response text

    Returns:
        Tuple of (confidence_level, list_of_uncertainties)
    """
    confidence = "MEDIUM"  # Default
    uncertainties = []

    # Extract confidence level
    confidence_match = re.search(
        r'\*?\*?CONFIDENCE\s*(?:LEVEL)?[:\s]*\*?\*?\s*(HIGH|MEDIUM|LOW)',
        text, re.IGNORECASE
    )
    if confidence_match:
        confidence = confidence_match.group(1).upper()

    # Extract uncertainties
    uncertainties_section = re.search(
        r'(?:KEY\s*)?UNCERTAINTIES[:\s]*\n?((?:[-•*]\s*.+\n?)+)',
        text, re.IGNORECASE
    )
    if uncertainties_section:
        uncertainty_lines = re.findall(r'[-•*]\s*(.+)', uncertainties_section.group(1))
        uncertainties = [u.strip() for u in uncertainty_lines if u.strip()][:5]

    return confidence, uncertainties


async def stage2_cross_evaluation(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    industry: str = "manufacturing"
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Stage 2: Each executive evaluates other executives' perspectives.

    Executives review each other's analyses and provide feedback,
    identifying strengths, weaknesses, and areas of agreement/disagreement.

    Args:
        user_query: The original business situation
        stage1_results: Results from Stage 1
        industry: Industry context for specialized executives

    Returns:
        Tuple of (evaluations list, label_to_role mapping)
    """
    # Get industry-specific executives
    industry_executives = get_industry_executives(industry) or EXECUTIVE_ROLES

    # Create anonymized labels for responses
    labels = [chr(65 + i) for i in range(len(stage1_results))]  # A, B, C, ...

    # Create mapping from label to role
    label_to_role = {
        f"Perspective {label}": result['role']
        for label, result in zip(labels, stage1_results)
    }

    # Build the perspectives text with confidence info
    perspectives_text = "\n\n".join([
        f"Perspective {label} ({result['title']}) [Confidence: {result.get('confidence', 'N/A')}]:\n{result['response']}"
        for label, result in zip(labels, stage1_results)
    ])

    # Prepare evaluation configs
    executives = {
        role_key: {
            'model': role_config['model'],
            'persona': role_config['persona']
        }
        for role_key, role_config in industry_executives.items()
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
5. Note which executives expressed low confidence and whether their uncertainties are valid concerns

**At the end, provide your RANKING in this exact JSON format:**

```json
{{
  "ranking": [
    {{"perspective": "A", "rank": 1, "strength": "brief reason"}},
    {{"perspective": "B", "rank": 2, "strength": "brief reason"}},
    ...
  ],
  "key_agreements": ["point 1", "point 2"],
  "key_disagreements": ["point 1", "point 2"]
}}
```

Rank all perspectives from most valuable (1) to least valuable for this specific situation."""

    # Query all executives in parallel for their evaluations
    responses = await query_executives_parallel(executives, evaluation_prompt)

    # Format results
    stage2_results = []
    for role_key, response in responses.items():
        if response is not None and role_key in industry_executives:
            full_text = response.get('content', '')
            parsed = parse_structured_ranking(full_text)
            stage2_results.append({
                "role": role_key,
                "title": industry_executives[role_key]["title"],
                "model": industry_executives[role_key]["model"],
                "evaluation": full_text,
                "parsed_ranking": parsed.get('ranking', []),
                "key_agreements": parsed.get('key_agreements', []),
                "key_disagreements": parsed.get('key_disagreements', [])
            })

    return stage2_results, label_to_role


def parse_structured_ranking(text: str) -> Dict[str, Any]:
    """
    Parse structured ranking from executive's evaluation, with multiple fallbacks.

    Args:
        text: The full evaluation text

    Returns:
        Dict with 'ranking', 'key_agreements', 'key_disagreements'
    """
    result = {
        'ranking': [],
        'key_agreements': [],
        'key_disagreements': []
    }

    # Try to find JSON block first
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if 'ranking' in parsed:
                # Convert ranking format
                for item in parsed['ranking']:
                    if isinstance(item, dict) and 'perspective' in item:
                        result['ranking'].append(f"Perspective {item['perspective']}")
                    elif isinstance(item, str):
                        result['ranking'].append(item)

                result['key_agreements'] = parsed.get('key_agreements', [])
                result['key_disagreements'] = parsed.get('key_disagreements', [])
                return result
        except json.JSONDecodeError:
            logger.debug("Failed to parse JSON ranking, falling back to regex")

    # Fallback: Look for "FINAL RANKING:" section with numbered list
    if "FINAL RANKING:" in text or "RANKING:" in text:
        parts = re.split(r'(?:FINAL\s+)?RANKING[:\s]*', text, flags=re.IGNORECASE)
        if len(parts) >= 2:
            ranking_section = parts[-1]
            # Try numbered format: "1. Perspective A"
            numbered_matches = re.findall(r'\d+\.\s*(?:Perspective\s+)?([A-Z])', ranking_section)
            if numbered_matches:
                result['ranking'] = [f"Perspective {m}" for m in numbered_matches]
                return result

    # Final fallback: Extract all "Perspective X" patterns in order of appearance
    matches = re.findall(r'Perspective ([A-Z])', text)
    seen = set()
    for m in matches:
        if m not in seen:
            result['ranking'].append(f"Perspective {m}")
            seen.add(m)

    return result


async def stage2_5_debate(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    label_to_role: Dict[str, str],
    industry: str = "manufacturing"
) -> List[Dict[str, Any]]:
    """
    Stage 2.5: Executives respond to critiques and refine their positions.

    After seeing cross-evaluations, executives can defend, modify, or
    acknowledge valid points about their original analysis.

    Args:
        user_query: The original business situation
        stage1_results: Original perspectives from Stage 1
        stage2_results: Cross-evaluations from Stage 2
        label_to_role: Mapping from perspective labels to roles
        industry: Industry context for specialized executives

    Returns:
        List of debate responses
    """
    # Get industry-specific executives
    industry_executives = get_industry_executives(industry) or EXECUTIVE_ROLES

    # Create reverse mapping: role to label
    role_to_label = {v: k for k, v in label_to_role.items()}

    debate_results = []

    for stage1_item in stage1_results:
        role_key = stage1_item['role']
        role_label = role_to_label.get(role_key, '')

        # Skip if this executive isn't in the industry's roster
        if role_key not in industry_executives:
            continue

        # Collect critiques of this executive's perspective from other executives
        critiques = []
        for eval_item in stage2_results:
            if eval_item['role'] != role_key:  # Don't include self-evaluation
                # Look for mentions of this executive's perspective label in the evaluation
                evaluation_text = eval_item['evaluation']
                if role_label and role_label.split()[-1] in evaluation_text:
                    critiques.append({
                        'from': eval_item['title'],
                        'content': evaluation_text
                    })

        if not critiques:
            continue

        # Prepare critiques summary
        critiques_text = "\n\n".join([
            f"**Critique from {c['from']}:**\n{c['content'][:1500]}..."
            for c in critiques[:3]  # Limit to 3 critiques
        ])

        debate_prompt = f"""In the Executive Board meeting about:

---
{user_query}
---

You provided this analysis:
{stage1_item['response'][:2000]}...

Your colleagues have provided feedback on your perspective:

{critiques_text}

Please provide a brief response (200-400 words):

1. **Defend** - Which criticisms do you disagree with and why?
2. **Acknowledge** - Which valid points do you accept?
3. **Refine** - How would you modify your recommendation based on this feedback?

Be constructive and focused on improving the final decision."""

        # Query this executive using industry-specific config
        executives = {
            role_key: {
                'model': industry_executives[role_key]['model'],
                'persona': industry_executives[role_key]['persona']
            }
        }

        responses = await query_executives_parallel(executives, debate_prompt)

        if role_key in responses and responses[role_key]:
            debate_results.append({
                "role": role_key,
                "title": industry_executives[role_key]["title"],
                "response": responses[role_key].get('content', ''),
                "critiques_addressed": len(critiques)
            })

    return debate_results


async def generate_risk_matrix(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    industry: str = "manufacturing"
) -> Dict[str, Any]:
    """
    Generate a structured risk matrix from all executive perspectives.

    Args:
        user_query: The business situation
        stage1_results: All executive perspectives
        stage2_results: Cross-evaluations
        industry: Industry context for role names in risk ownership

    Returns:
        Dict containing structured risk matrix
    """
    # Get industry-specific executives for role names
    industry_executives = get_industry_executives(industry) or EXECUTIVE_ROLES
    role_names = "|".join(industry_executives.keys())
    # Compile all perspectives
    all_perspectives = "\n\n".join([
        f"**{r['title']}:**\n{r['response'][:1500]}"
        for r in stage1_results
    ])

    risk_prompt = f"""Based on these executive board perspectives on the following situation:

---
{user_query}
---

Perspectives:
{all_perspectives}

Extract and structure ALL identified risks into a risk matrix. For EACH risk, provide:

Respond ONLY with valid JSON in this exact format:
```json
{{
  "risks": [
    {{
      "id": "R1",
      "description": "Brief risk description",
      "category": "Financial|Operational|Strategic|Legal|Reputational|Technical",
      "likelihood": "unlikely|possible|likely|very_likely",
      "impact": "low|medium|high|critical",
      "owner": "{role_names}",
      "mitigation": "Suggested mitigation strategy",
      "source_executive": "Who identified this risk"
    }}
  ],
  "risk_summary": {{
    "total_risks": 0,
    "critical_count": 0,
    "high_count": 0,
    "medium_count": 0,
    "low_count": 0,
    "top_risk_categories": ["category1", "category2"]
  }}
}}
```

Identify 6-12 distinct risks from the perspectives. Be specific and actionable."""

    messages = [{"role": "user", "content": risk_prompt}]
    response = await query_model(COUNCIL_SPEAKER_MODEL, messages, timeout=60.0)

    if response is None:
        return {"risks": [], "risk_summary": {"total_risks": 0}}

    content = response.get('content', '')

    # Try to parse JSON from response
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', content)
    if json_match:
        try:
            risk_data = json.loads(json_match.group(1))
            # Add risk scores
            for risk in risk_data.get('risks', []):
                likelihood = risk.get('likelihood', 'possible')
                impact = risk.get('impact', 'medium')
                likelihood_score = RISK_LIKELIHOOD_LEVELS.get(likelihood, {}).get('score', 2)
                impact_score = RISK_SEVERITY_LEVELS.get(impact, {}).get('score', 2)
                risk['risk_score'] = likelihood_score * impact_score
                risk['risk_level'] = 'critical' if risk['risk_score'] >= 12 else \
                                     'high' if risk['risk_score'] >= 8 else \
                                     'medium' if risk['risk_score'] >= 4 else 'low'
            return risk_data
        except json.JSONDecodeError:
            logger.warning("Failed to parse risk matrix JSON")

    return {"risks": [], "risk_summary": {"total_risks": 0}, "raw_response": content}


async def stage3_council_speaker_synthesis(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    debate_results: Optional[List[Dict[str, Any]]] = None,
    risk_matrix: Optional[Dict[str, Any]] = None,
    industry: str = "manufacturing"
) -> Dict[str, Any]:
    """
    Stage 3: Council Speaker synthesizes all perspectives into a final decision.

    The Council Speaker acts as a neutral facilitator, weighing all perspectives,
    debate responses, and risk analysis to produce a balanced recommendation.

    Args:
        user_query: The original business situation
        stage1_results: Individual executive perspectives from Stage 1
        stage2_results: Cross-evaluations from Stage 2
        debate_results: Optional debate responses from Stage 2.5
        risk_matrix: Optional structured risk analysis
        industry: Industry context for specialized Council Speaker

    Returns:
        Dict with 'model' and 'response' keys
    """
    # Get industry-specific Council Speaker persona (fallback to default)
    speaker_persona = get_council_speaker_persona(industry) or COUNCIL_SPEAKER_PERSONA

    # Build comprehensive context for the Council Speaker
    stage1_text = "\n\n".join([
        f"**{result['title']} ({result['role']})** [Confidence: {result.get('confidence', 'N/A')}]:\n{result['response']}"
        for result in stage1_results
    ])

    stage2_text = "\n\n".join([
        f"**Evaluation by {result['title']} ({result['role']})**:\n{result['evaluation']}"
        for result in stage2_results
    ])

    # Add debate results if available
    debate_text = ""
    if debate_results:
        debate_text = "\n\n**STAGE 2.5 - Debate Responses:**\n\n" + "\n\n".join([
            f"**{result['title']} responds:**\n{result['response']}"
            for result in debate_results
        ])

    # Add risk matrix summary if available
    risk_text = ""
    if risk_matrix and risk_matrix.get('risks'):
        high_risks = [r for r in risk_matrix['risks'] if r.get('risk_level') in ['critical', 'high']]
        if high_risks:
            risk_text = "\n\n**RISK ANALYSIS - High Priority Risks:**\n"
            for risk in high_risks[:5]:
                risk_text += f"\n- [{risk.get('risk_level', 'high').upper()}] {risk.get('description', 'Unknown')} (Owner: {risk.get('owner', 'TBD')})"

    speaker_prompt = f"""{speaker_persona}

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
{debate_text}
{risk_text}

---

As the Council Speaker, please synthesize all perspectives, debates, and risk analysis into a comprehensive final recommendation for the board.

Pay special attention to:
1. Areas where executives expressed LOW confidence - these may need more investigation
2. Points raised during the debate that refined initial positions
3. High-priority risks that need mitigation
4. The Devil's Advocate perspective if present - ensure concerns are addressed

Follow the structure outlined in your role description."""

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


def calculate_aggregate_rankings(
    stage2_results: List[Dict[str, Any]],
    label_to_role: Dict[str, str],
    industry: str = "manufacturing"
) -> List[Dict[str, Any]]:
    """
    Calculate aggregate rankings across all executives.

    Args:
        stage2_results: Evaluations from each executive
        label_to_role: Mapping from anonymous labels to role names
        industry: Industry context for executive titles

    Returns:
        List of dicts with role name and average rank, sorted best to worst
    """
    # Get industry-specific executives for titles
    industry_executives = get_industry_executives(industry) or EXECUTIVE_ROLES

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
                "title": industry_executives.get(role, {}).get("title", role),
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


async def run_executive_board_meeting(
    user_query: str,
    include_debate: bool = True,
    include_risk_matrix: bool = True,
    industry: str = "manufacturing"
) -> Tuple[List, List, Dict, Dict, Optional[List], Optional[Dict]]:
    """
    Run the complete executive board meeting process with all stages.

    Args:
        user_query: The business situation/question to discuss
        include_debate: Whether to run the debate stage (Stage 2.5)
        include_risk_matrix: Whether to generate risk matrix
        industry: Industry context for specialized executives

    Returns:
        Tuple of (stage1_results, stage2_results, stage3_result, metadata,
                  debate_results, risk_matrix)
    """
    # Get industry-specific executives for metadata
    industry_executives = get_industry_executives(industry) or EXECUTIVE_ROLES

    # Stage 1: Collect individual executive perspectives
    stage1_results = await stage1_collect_perspectives(user_query, industry)

    # If no executives responded successfully, return error
    if not stage1_results:
        return [], [], {
            "model": "error",
            "response": "All executive board members failed to respond. Please try again."
        }, {}, None, None

    # Stage 2: Cross-evaluations
    stage2_results, label_to_role = await stage2_cross_evaluation(
        user_query, stage1_results, industry
    )

    # Calculate aggregate rankings
    aggregate_rankings = calculate_aggregate_rankings(
        stage2_results, label_to_role, industry
    )

    # Stage 2.5: Debate (optional)
    debate_results = None
    if include_debate and stage2_results:
        debate_results = await stage2_5_debate(
            user_query, stage1_results, stage2_results, label_to_role, industry
        )

    # Risk Matrix (optional)
    risk_matrix = None
    if include_risk_matrix:
        risk_matrix = await generate_risk_matrix(
            user_query, stage1_results, stage2_results, industry
        )

    # Stage 3: Council Speaker synthesizes final recommendation
    stage3_result = await stage3_council_speaker_synthesis(
        user_query,
        stage1_results,
        stage2_results,
        debate_results,
        risk_matrix,
        industry
    )

    # Prepare metadata with industry-specific executives
    metadata = {
        "label_to_role": label_to_role,
        "aggregate_rankings": aggregate_rankings,
        "industry": industry,
        "confidence_summary": {
            role['role']: {
                'confidence': role.get('confidence', 'MEDIUM'),
                'uncertainties': role.get('uncertainties', [])
            }
            for role in stage1_results
        },
        "executive_roles": {
            role_key: {
                "title": role_config["title"],
                "model": role_config["model"]
            }
            for role_key, role_config in industry_executives.items()
        }
    }

    return stage1_results, stage2_results, stage3_result, metadata, debate_results, risk_matrix


async def compare_scenarios(
    scenarios: List[str],
    include_debate: bool = False,
    include_risk_matrix: bool = True,
    industry: str = "manufacturing"
) -> Dict[str, Any]:
    """
    Run the council process on multiple scenarios and generate a comparison.

    Args:
        scenarios: List of scenario descriptions to compare
        include_debate: Whether to include debate stage
        include_risk_matrix: Whether to include risk analysis
        industry: Industry context for specialized executives

    Returns:
        Dict with scenario results and comparison synthesis
    """
    scenario_results = []

    for i, scenario in enumerate(scenarios):
        result = await run_executive_board_meeting(
            scenario,
            include_debate=include_debate,
            include_risk_matrix=include_risk_matrix,
            industry=industry
        )
        scenario_results.append({
            "scenario_id": i + 1,
            "scenario": scenario[:200] + "..." if len(scenario) > 200 else scenario,
            "stage1": result[0],
            "stage2": result[1],
            "stage3": result[2],
            "metadata": result[3],
            "risk_matrix": result[5]
        })

    # Generate comparison synthesis
    comparison_prompt = f"""As the Council Speaker, compare these {len(scenarios)} scenarios that the board has analyzed:

"""
    for i, result in enumerate(scenario_results):
        comparison_prompt += f"""
**SCENARIO {i + 1}:** {result['scenario']}
**Final Recommendation:** {result['stage3'].get('response', 'N/A')[:500]}...
"""

    comparison_prompt += """

Please provide:
1. **Side-by-Side Comparison** - Key differences in recommendations
2. **Risk Comparison** - Which scenario has lower overall risk?
3. **Resource Requirements** - Which requires more resources/investment?
4. **Recommended Choice** - Which scenario does the board recommend and why?
5. **Conditions for Alternative** - Under what conditions should the other option(s) be reconsidered?"""

    messages = [{"role": "user", "content": comparison_prompt}]
    comparison_response = await query_model(COUNCIL_SPEAKER_MODEL, messages)

    return {
        "scenarios": scenario_results,
        "comparison": comparison_response.get('content', '') if comparison_response else "Unable to generate comparison"
    }

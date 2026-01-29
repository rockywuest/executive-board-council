# Executive Board Council

A multi-LLM decision support system modeled after a German production company's executive board (Vorstand). Present business situations to a virtual board of executives, each powered by a different LLM and representing a specific area of the company.

Inspired by [Karpathy's LLM Council](https://github.com/karpathy/llm-council).

## Concept

Instead of asking a single LLM for advice, this system convenes a full executive board where each member:
1. Analyzes the situation from their specific expertise
2. Evaluates and ranks other executives' perspectives
3. A Council Speaker synthesizes all viewpoints into a final recommendation

## Executive Board Members

| Role | German Title | Focus Area |
|------|--------------|------------|
| **CEO** | Vorstandsvorsitzender | Strategy, stakeholders, governance |
| **CFO** | Finanzvorstand | Financial analysis, ROI, risk |
| **CTO** | Technischer Vorstand | Technology, production, quality |
| **CHRO** | Personalvorstand | Workforce, labor law, culture |
| **CSO** | Vertriebsvorstand | Sales, customers, market |
| **CPO/CSCO** | Einkaufs- und Supply Chain Vorstand | Procurement, supply chain, logistics |

## How It Works

### Stage 1: Individual Perspectives
Each executive analyzes the business situation from their role's perspective, identifying key issues, risks, opportunities, and recommendations.

### Stage 2: Cross-Evaluation
Executives review each other's analyses (anonymized), identify strengths and blind spots, and rank perspectives by value for the specific situation.

### Stage 3: Council Speaker Synthesis
The Council Speaker (Vorstandssprecher) integrates all perspectives and evaluations into a balanced final recommendation with clear next steps.

## Setup

### 1. Install Dependencies

Using [uv](https://docs.astral.sh/uv/) (recommended):
```bash
uv sync
```

Or with pip:
```bash
pip install -e .
```

### 2. Configure API Key

Copy the example environment file and add your OpenRouter API key:
```bash
cp .env.example .env
# Edit .env and add your key
```

Get your API key at [openrouter.ai](https://openrouter.ai/).

### 3. Configure Models (Optional)

Edit `backend/config.py` to customize which models represent each executive role:

```python
EXECUTIVE_MODELS = {
    "CEO": "anthropic/claude-sonnet-4",
    "CFO": "openai/gpt-4o",
    "CTO": "google/gemini-2.0-flash-001",
    # ... etc
}
```

## Usage

### Command Line Interface

**Interactive mode:**
```bash
uv run python cli.py
```

**Single query:**
```bash
uv run python cli.py -q "We are considering acquiring a competitor. What should we consider?"
```

**Brief output (final synthesis only):**
```bash
uv run python cli.py -b -q "Should we expand into the US market?"
```

**From file:**
```bash
uv run python cli.py -f situation.txt
```

### API Server

Start the backend:
```bash
uv run python main.py
```

Then use the API endpoints:
- `POST /api/meetings` - Create a new meeting
- `POST /api/meetings/{id}/discuss` - Submit a situation for discussion
- `POST /api/meetings/{id}/discuss/stream` - Stream the discussion (SSE)
- `GET /api/meetings` - List all meetings
- `GET /api/meetings/{id}` - Get meeting details

## Customizing Executive Personas

You can customize each executive's persona in `backend/config.py` by editing the `EXECUTIVE_ROLES` dictionary. Each role has:

- `title`: The official title (German and English)
- `model`: The OpenRouter model identifier
- `persona`: Detailed description of the role's responsibilities, decision-making style, and analysis focus

## Example Situations

Here are some example business situations to test:

1. **Market Expansion**: "We are considering expanding our production capacity by building a new factory in Eastern Europe. What factors should we consider?"

2. **Technology Investment**: "A startup is offering us an exclusive AI-powered quality control system. They want €2M investment and a 3-year contract. Should we proceed?"

3. **Supply Chain Crisis**: "Our main supplier for critical components just announced a 40% price increase and 8-week delays. How should we respond?"

4. **Workforce Challenge**: "We need to reduce costs by 15% this year. The works council is strongly opposed to any layoffs. What options do we have?"

5. **Strategic Partnership**: "A competitor is proposing a joint venture for a new product line. They would handle sales, we would handle production. Is this a good opportunity?"

## Tech Stack

- **Backend**: FastAPI, async httpx, OpenRouter API
- **Storage**: JSON files in `data/conversations/`
- **Package Management**: uv for Python

## License

MIT

---

## Support

If you find this useful, consider buying me a coffee ☕

https://ko-fi.com/rockywuest

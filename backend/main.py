"""FastAPI backend for Executive Board Council."""

import logging
import re
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
import uuid
import json
import asyncio

from . import storage
from .config import EXAMPLE_TEMPLATES, EXECUTIVE_ROLES
from .auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    AuthResponse,
    UserTier,
    register_user,
    login_user,
    logout_user,
    get_optional_user,
    require_auth,
    get_client_ip,
)
from .usage import get_usage_tracker
from .stripe_billing import (
    create_checkout_session,
    create_portal_session,
    handle_webhook,
    get_subscription_status,
    is_stripe_configured,
)
from .industries import (
    get_industry,
    get_industry_list,
    get_industry_executives,
    get_industry_templates,
    INDUSTRIES
)
from .council import (
    run_executive_board_meeting,
    generate_meeting_title,
    stage1_collect_perspectives,
    stage2_cross_evaluation,
    stage2_5_debate,
    stage3_council_speaker_synthesis,
    calculate_aggregate_rankings,
    generate_risk_matrix,
    compare_scenarios
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vorstandsgremium API",
    description="Multi-LLM Entscheidungsunterstützung mit simuliertem deutschen Unternehmensvorstand",
    version="2.0.0"
)

# Enable CORS for local development
# NOTE: Restrict methods and headers in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


class CreateMeetingRequest(BaseModel):
    """Request to create a new executive board meeting."""
    title: Optional[str] = Field(default=None, max_length=200)
    industry: Optional[str] = Field(default="manufacturing", description="Industry for the meeting")


class SubmitSituationRequest(BaseModel):
    """Request to submit a business situation for board discussion."""
    content: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="Business situation to discuss (10-50000 characters)"
    )
    include_debate: bool = Field(default=True, description="Include debate stage (Stage 2.5)")
    include_risk_matrix: bool = Field(default=True, description="Generate risk matrix")

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate content is not just whitespace."""
        if not v or not v.strip():
            raise ValueError('Content cannot be empty or whitespace only')
        return v.strip()


class CompareScenarioRequest(BaseModel):
    """Request to compare multiple scenarios."""
    scenarios: List[str] = Field(
        ...,
        min_length=2,
        max_length=4,
        description="2-4 scenarios to compare"
    )
    include_debate: bool = Field(default=False, description="Include debate stage (slower)")
    include_risk_matrix: bool = Field(default=True, description="Include risk analysis")


class MeetingMetadata(BaseModel):
    """Meeting metadata for list view."""
    id: str
    created_at: str
    title: str
    industry: Optional[str] = "manufacturing"
    discussion_count: int


class Meeting(BaseModel):
    """Full meeting with all discussions."""
    id: str
    created_at: str
    title: str
    industry: Optional[str] = "manufacturing"
    discussions: List[Dict[str, Any]]


class ExampleTemplate(BaseModel):
    """Example situation template."""
    id: str
    name: str
    category: str
    description: str
    prompt: str


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Vorstandsgremium API",
        "version": "2.0.0",
        "features": ["debate_stage", "risk_matrix", "confidence_scores", "scenario_comparison", "devils_advocate"]
    }


# =========================================================================
# AUTHENTICATION ENDPOINTS
# =========================================================================

@app.post("/api/auth/register", response_model=AuthResponse)
async def auth_register(request: UserCreate):
    """
    Register a new user account.

    Returns access token and user info. New users start on the 'free' tier
    with 5 requests per month.
    """
    return await register_user(request.email, request.password)


@app.post("/api/auth/login", response_model=AuthResponse)
async def auth_login(request: UserLogin):
    """
    Login with email and password.

    Returns access token and user info including current tier.
    """
    return await login_user(request.email, request.password)


@app.post("/api/auth/logout")
async def auth_logout(user: UserResponse = Depends(require_auth)):
    """Logout current user (invalidates token)."""
    # Note: Supabase JWTs are stateless, so we just acknowledge the logout
    return {"status": "logged_out"}


@app.get("/api/auth/me", response_model=UserResponse)
async def auth_me(user: UserResponse = Depends(require_auth)):
    """Get current authenticated user info."""
    return user


# =========================================================================
# USAGE ENDPOINTS
# =========================================================================

@app.get("/api/usage")
async def get_usage(
    request: Request,
    user: Optional[UserResponse] = Depends(get_optional_user)
):
    """
    Get current usage limits and remaining requests.

    Returns usage info based on authentication state:
    - Anonymous: IP-based tracking, 2 requests/day
    - Free tier: 5 requests/month
    - Pro tier: 50 requests/month
    - Enterprise: Unlimited
    """
    tracker = get_usage_tracker()

    if user:
        usage = tracker.get_user_usage(user.id, user.tier)
        return {
            "authenticated": True,
            "tier": user.tier,
            "email": user.email,
            **usage
        }
    else:
        ip = get_client_ip(request)
        usage = tracker.get_ip_usage(ip)
        return {
            "authenticated": False,
            "tier": UserTier.ANONYMOUS,
            **usage
        }


@app.get("/api/tiers")
async def get_tiers():
    """Get information about available subscription tiers."""
    return {
        "tiers": [
            {
                "id": UserTier.ANONYMOUS,
                "name": "Anonym",
                "price": 0,
                "requests_per_day": UserTier.LIMITS[UserTier.ANONYMOUS]["daily"],
                "requests_per_month": UserTier.LIMITS[UserTier.ANONYMOUS]["monthly"],
                "features": ["Basiszugang", "2 Anfragen pro Tag"]
            },
            {
                "id": UserTier.FREE,
                "name": "Kostenlos",
                "price": 0,
                "requests_per_day": -1,
                "requests_per_month": UserTier.LIMITS[UserTier.FREE]["monthly"],
                "features": ["5 Anfragen pro Monat", "Sitzungsverlauf", "Exportfunktion"]
            },
            {
                "id": UserTier.PRO,
                "name": "Pro",
                "price": 29,
                "price_yearly": 290,
                "requests_per_day": -1,
                "requests_per_month": UserTier.LIMITS[UserTier.PRO]["monthly"],
                "features": ["50 Anfragen pro Monat", "Priorisierte Verarbeitung", "Alle Exportformate", "E-Mail-Support"]
            },
            {
                "id": UserTier.ENTERPRISE,
                "name": "Enterprise",
                "price": 99,
                "price_yearly": 990,
                "requests_per_day": -1,
                "requests_per_month": -1,
                "features": ["Unbegrenzte Anfragen", "Persönlicher Support", "Individuelle Integrationen", "SLA-Garantie"]
            }
        ]
    }


# =========================================================================
# BILLING ENDPOINTS (Stripe)
# =========================================================================

class CheckoutRequest(BaseModel):
    """Request for creating a checkout session."""
    tier: str = Field(default="pro", pattern="^(pro|enterprise)$")
    interval: str = Field(default="monthly", pattern="^(monthly|yearly)$")


@app.post("/api/billing/checkout")
async def create_checkout(
    request: CheckoutRequest,
    user: UserResponse = Depends(require_auth)
):
    """
    Create a Stripe Checkout session for subscription upgrade.

    Requires authentication. Returns URL to redirect user to Stripe Checkout.
    """
    checkout_url = await create_checkout_session(
        user_id=user.id,
        email=user.email,
        tier=request.tier,
        interval=request.interval
    )
    return {"url": checkout_url}


@app.get("/api/billing/portal")
async def get_billing_portal(user: UserResponse = Depends(require_auth)):
    """
    Get URL for Stripe Customer Portal.

    Allows users to manage their subscription, update payment method, etc.
    """
    portal_url = await create_portal_session(
        user_id=user.id,
        email=user.email
    )
    return {"url": portal_url}


@app.get("/api/billing/status")
async def get_billing_status(user: UserResponse = Depends(require_auth)):
    """
    Get current subscription status for authenticated user.

    Returns subscription details including tier, period end, etc.
    """
    status = await get_subscription_status(user.email)
    return status


@app.post("/api/billing/webhook")
async def stripe_webhook(request: Request):
    """
    Stripe webhook endpoint.

    Receives subscription lifecycle events from Stripe.
    Must be configured in Stripe Dashboard.
    """
    return await handle_webhook(request)


@app.get("/api/billing/configured")
async def billing_configured():
    """Check if Stripe billing is configured."""
    return {"configured": is_stripe_configured()}


@app.get("/api/templates", response_model=List[ExampleTemplate])
async def get_templates():
    """Get example situation templates (legacy - use industry-specific templates instead)."""
    return EXAMPLE_TEMPLATES


# =========================================================================
# INDUSTRY ENDPOINTS
# =========================================================================

@app.get("/api/industries")
async def list_industries():
    """Get list of all available industries."""
    return get_industry_list()


@app.get("/api/industries/{industry_id}")
async def get_industry_details(industry_id: str):
    """Get full details for a specific industry."""
    industry = get_industry(industry_id)
    if not industry:
        raise HTTPException(status_code=404, detail=f"Branche nicht gefunden: {industry_id}")
    return {
        "id": industry["id"],
        "name": industry["name"],
        "icon": industry["icon"],
        "description": industry["description"],
        "german_context": industry["german_context"]
    }


@app.get("/api/industries/{industry_id}/executives")
async def get_industry_executive_roles(industry_id: str):
    """Get executive roles configured for a specific industry."""
    executives = get_industry_executives(industry_id)
    if not executives:
        raise HTTPException(status_code=404, detail=f"Branche nicht gefunden: {industry_id}")
    return {
        role_key: {
            "title": role_config["title"],
            "model": role_config["model"]
        }
        for role_key, role_config in executives.items()
    }


@app.get("/api/industries/{industry_id}/templates")
async def get_industry_template_list(industry_id: str):
    """Get example templates for a specific industry."""
    templates = get_industry_templates(industry_id)
    if templates is None:
        raise HTTPException(status_code=404, detail=f"Branche nicht gefunden: {industry_id}")
    return templates


@app.get("/api/executives")
async def get_executives():
    """Get list of executive roles and their configuration."""
    return {
        role_key: {
            "title": role_config["title"],
            "model": role_config["model"]
        }
        for role_key, role_config in EXECUTIVE_ROLES.items()
    }


@app.get("/api/meetings", response_model=List[MeetingMetadata])
async def list_meetings():
    """List all executive board meetings (metadata only)."""
    return storage.list_meetings()


@app.post("/api/meetings", response_model=Meeting)
async def create_meeting(request: CreateMeetingRequest):
    """Create a new executive board meeting."""
    # Validate industry if provided
    if request.industry and request.industry not in INDUSTRIES:
        raise HTTPException(status_code=400, detail=f"Unbekannte Branche: {request.industry}")

    meeting_id = str(uuid.uuid4())
    meeting = storage.create_meeting(meeting_id, industry=request.industry)
    return meeting


def validate_meeting_id(meeting_id: str) -> bool:
    """Validate meeting ID is a valid UUID."""
    try:
        uuid.UUID(meeting_id)
        return True
    except ValueError:
        return False


@app.get("/api/meetings/{meeting_id}", response_model=Meeting)
async def get_meeting(meeting_id: str):
    """Get a specific meeting with all its discussions."""
    if not validate_meeting_id(meeting_id):
        raise HTTPException(status_code=400, detail="Ungültiges Meeting-ID-Format")
    meeting = storage.get_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Sitzung nicht gefunden")
    return meeting


@app.delete("/api/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str):
    """Delete a meeting."""
    if not validate_meeting_id(meeting_id):
        raise HTTPException(status_code=400, detail="Ungültiges Meeting-ID-Format")
    success = storage.delete_meeting(meeting_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sitzung nicht gefunden")
    return {"status": "deleted", "meeting_id": meeting_id}


@app.post("/api/meetings/{meeting_id}/discuss")
async def submit_situation(
    meeting_id: str,
    request: SubmitSituationRequest,
    http_request: Request,
    user: Optional[UserResponse] = Depends(get_optional_user)
):
    """
    Submit a business situation and run the complete executive board process.
    Includes: perspectives, cross-evaluation, optional debate, optional risk matrix, synthesis.

    This endpoint is rate-limited:
    - Anonymous: 2 requests/day
    - Free tier: 5 requests/month
    - Pro tier: 50 requests/month
    - Enterprise: Unlimited
    """
    # Check usage limits before processing (this will raise 429 if limit exceeded)
    tracker = get_usage_tracker()
    usage_info = tracker.check_and_record_request(http_request, user)

    # Validate meeting ID format
    if not validate_meeting_id(meeting_id):
        raise HTTPException(status_code=400, detail="Ungültiges Meeting-ID-Format")

    # Check if meeting exists
    meeting = storage.get_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Sitzung nicht gefunden")

    # Check if this is the first discussion
    is_first_discussion = len(meeting["discussions"]) == 0

    # Add the business situation
    storage.add_situation(meeting_id, request.content)

    # If this is the first discussion, generate a title
    if is_first_discussion:
        title = await generate_meeting_title(request.content)
        storage.update_meeting_title(meeting_id, title)

    # Get industry from meeting
    industry = meeting.get("industry", "manufacturing")

    # Run the complete executive board process
    stage1_results, stage2_results, stage3_result, metadata, debate_results, risk_matrix = \
        await run_executive_board_meeting(
            request.content,
            include_debate=request.include_debate,
            include_risk_matrix=request.include_risk_matrix,
            industry=industry
        )

    # Add board response with all stages
    storage.add_board_response(
        meeting_id,
        stage1_results,
        stage2_results,
        stage3_result,
        debate_results=debate_results,
        risk_matrix=risk_matrix
    )

    # Return the complete response with metadata and usage info
    return {
        "stage1_perspectives": stage1_results,
        "stage2_evaluations": stage2_results,
        "stage2_5_debate": debate_results,
        "stage3_synthesis": stage3_result,
        "risk_matrix": risk_matrix,
        "metadata": metadata,
        "usage": usage_info
    }


@app.post("/api/meetings/{meeting_id}/discuss/stream")
async def submit_situation_stream(
    meeting_id: str,
    request: SubmitSituationRequest,
    http_request: Request,
    user: Optional[UserResponse] = Depends(get_optional_user)
):
    """
    Submit a business situation and stream the executive board process.
    Returns Server-Sent Events as each stage completes.

    This endpoint is rate-limited (same limits as /discuss).
    """
    # Check usage limits before processing (this will raise 429 if limit exceeded)
    tracker = get_usage_tracker()
    usage_info = tracker.check_and_record_request(http_request, user)

    # Validate meeting ID format
    if not validate_meeting_id(meeting_id):
        raise HTTPException(status_code=400, detail="Ungültiges Meeting-ID-Format")

    # Check if meeting exists
    meeting = storage.get_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Sitzung nicht gefunden")

    # Check if this is the first discussion
    is_first_discussion = len(meeting["discussions"]) == 0

    # Get industry from meeting
    industry = meeting.get("industry", "manufacturing")

    async def event_generator():
        try:
            # Send usage info first
            yield f"data: {json.dumps({'type': 'usage', 'data': usage_info})}\n\n"

            # Add the business situation
            storage.add_situation(meeting_id, request.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_discussion:
                title_task = asyncio.create_task(generate_meeting_title(request.content))

            # Stage 1: Collect executive perspectives (with confidence scores)
            yield f"data: {json.dumps({'type': 'stage1_start', 'message': 'Vorstandsperspektiven werden gesammelt...'})}\n\n"
            stage1_results = await stage1_collect_perspectives(request.content, industry=industry)
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2: Cross-evaluations
            yield f"data: {json.dumps({'type': 'stage2_start', 'message': 'Vorstände bewerten gegenseitig ihre Perspektiven...'})}\n\n"
            stage2_results, label_to_role = await stage2_cross_evaluation(request.content, stage1_results, industry=industry)
            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_role)
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_role': label_to_role, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Stage 2.5: Debate (optional)
            debate_results = None
            if request.include_debate:
                yield f"data: {json.dumps({'type': 'stage2_5_start', 'message': 'Vorstände debattieren und verfeinern ihre Positionen...'})}\n\n"
                debate_results = await stage2_5_debate(request.content, stage1_results, stage2_results, label_to_role, industry=industry)
                yield f"data: {json.dumps({'type': 'stage2_5_complete', 'data': debate_results})}\n\n"

            # Risk Matrix (optional, run in parallel with other tasks)
            risk_matrix = None
            risk_task = None
            if request.include_risk_matrix:
                yield f"data: {json.dumps({'type': 'risk_matrix_start', 'message': 'Risikomatrix wird erstellt...'})}\n\n"
                risk_task = asyncio.create_task(generate_risk_matrix(request.content, stage1_results, stage2_results, industry=industry))

            # Stage 3: Council Speaker synthesis
            yield f"data: {json.dumps({'type': 'stage3_start', 'message': 'Vorstandssprecher erstellt Schlussempfehlung...'})}\n\n"

            # Wait for risk matrix if it was started
            if risk_task:
                risk_matrix = await risk_task
                yield f"data: {json.dumps({'type': 'risk_matrix_complete', 'data': risk_matrix})}\n\n"

            # Generate synthesis with all available data
            stage3_result = await stage3_council_speaker_synthesis(
                request.content, stage1_results, stage2_results,
                debate_results=debate_results, risk_matrix=risk_matrix, industry=industry
            )
            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                title = await title_task
                storage.update_meeting_title(meeting_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete board response
            storage.add_board_response(
                meeting_id,
                stage1_results,
                stage2_results,
                stage3_result,
                debate_results=debate_results,
                risk_matrix=risk_matrix
            )

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            # Log full error internally, send generic message to client
            logger.error(f"Stream processing error: {type(e).__name__}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'Verarbeitung fehlgeschlagen. Bitte versuchen Sie es erneut.'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/api/compare")
async def compare_scenarios_endpoint(
    request: CompareScenarioRequest,
    http_request: Request,
    user: Optional[UserResponse] = Depends(get_optional_user)
):
    """
    Compare multiple business scenarios side-by-side.
    Runs the council process on each scenario and generates a comparison.

    Note: This counts as multiple requests based on the number of scenarios.
    """
    if len(request.scenarios) < 2:
        raise HTTPException(status_code=400, detail="Mindestens 2 Szenarien erforderlich")
    if len(request.scenarios) > 4:
        raise HTTPException(status_code=400, detail="Maximal 4 Szenarien erlaubt")

    # Check usage limits - comparison counts as one request per scenario
    tracker = get_usage_tracker()
    for _ in request.scenarios:
        tracker.check_and_record_request(http_request, user)

    result = await compare_scenarios(
        request.scenarios,
        include_debate=request.include_debate,
        include_risk_matrix=request.include_risk_matrix
    )

    return result


@app.get("/api/meetings/{meeting_id}/export")
async def export_meeting(meeting_id: str, format: str = "json"):
    """
    Export a meeting in various formats.
    Supported formats: json, markdown
    """
    if not validate_meeting_id(meeting_id):
        raise HTTPException(status_code=400, detail="Ungültiges Meeting-ID-Format")

    meeting = storage.get_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Sitzung nicht gefunden")

    if format == "json":
        return meeting

    elif format == "markdown":
        md = generate_meeting_markdown(meeting)
        return StreamingResponse(
            iter([md]),
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename={meeting_id}.md"
            }
        )

    else:
        raise HTTPException(status_code=400, detail=f"Nicht unterstütztes Format: {format}")


def generate_meeting_markdown(meeting: Dict[str, Any]) -> str:
    """Generate markdown export of a meeting."""
    md = f"# Vorstandssitzung: {meeting['title']}\n\n"
    md += f"**Datum:** {meeting['created_at']}\n\n"
    md += f"**Sitzungs-ID:** {meeting['id']}\n\n"
    md += "---\n\n"

    for i, discussion in enumerate(meeting.get('discussions', []), 1):
        if discussion.get('role') == 'user':
            md += f"## Geschäftssituation {i}\n\n"
            md += f"{discussion.get('content', '')}\n\n"
        elif discussion.get('role') == 'board':
            md += "### Vorstandsperspektiven\n\n"
            for perspective in discussion.get('stage1_perspectives', []):
                md += f"#### {perspective.get('title', perspective.get('role', 'Unbekannt'))}\n\n"
                confidence = perspective.get('confidence', 'k.A.')
                md += f"**Konfidenz:** {confidence}\n\n"
                md += f"{perspective.get('response', '')}\n\n"

            md += "### Gegenseitige Bewertungen\n\n"
            for evaluation in discussion.get('stage2_evaluations', []):
                md += f"#### Bewertung durch {evaluation.get('title', evaluation.get('role', 'Unbekannt'))}\n\n"
                md += f"{evaluation.get('evaluation', '')}\n\n"

            if discussion.get('debate_results'):
                md += "### Debattenbeiträge\n\n"
                for debate in discussion['debate_results']:
                    md += f"#### {debate.get('title', debate.get('role', 'Unbekannt'))} antwortet\n\n"
                    md += f"{debate.get('response', '')}\n\n"

            if discussion.get('risk_matrix', {}).get('risks'):
                md += "### Risikomatrix\n\n"
                md += "| Risiko | Kategorie | Wahrscheinlichkeit | Auswirkung | Verantwortlich |\n"
                md += "|--------|-----------|-------------------|------------|----------------|\n"
                for risk in discussion['risk_matrix']['risks']:
                    md += f"| {risk.get('description', '')} | {risk.get('category', '')} | "
                    md += f"{risk.get('likelihood', '')} | {risk.get('impact', '')} | {risk.get('owner', '')} |\n"
                md += "\n"

            md += "### Schlussempfehlung\n\n"
            md += f"{discussion.get('stage3_synthesis', {}).get('response', '')}\n\n"

            md += "---\n\n"

    md += "\n*Erstellt mit dem Vorstandsgremium*\n"
    return md


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

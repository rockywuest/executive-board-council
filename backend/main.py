"""FastAPI backend for Executive Board Council."""

import logging
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
import uuid
import json
import asyncio

from . import storage
from .config import EXAMPLE_TEMPLATES, EXECUTIVE_ROLES
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
    title="Executive Board Council API",
    description="Multi-LLM decision support system simulating a German executive board",
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
        "service": "Executive Board Council API",
        "version": "2.0.0",
        "features": ["debate_stage", "risk_matrix", "confidence_scores", "scenario_comparison", "devils_advocate"]
    }


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
        raise HTTPException(status_code=404, detail=f"Industry not found: {industry_id}")
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
        raise HTTPException(status_code=404, detail=f"Industry not found: {industry_id}")
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
        raise HTTPException(status_code=404, detail=f"Industry not found: {industry_id}")
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
        raise HTTPException(status_code=400, detail=f"Unknown industry: {request.industry}")

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
        raise HTTPException(status_code=400, detail="Invalid meeting ID format")
    meeting = storage.get_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@app.delete("/api/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str):
    """Delete a meeting."""
    if not validate_meeting_id(meeting_id):
        raise HTTPException(status_code=400, detail="Invalid meeting ID format")
    success = storage.delete_meeting(meeting_id)
    if not success:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"status": "deleted", "meeting_id": meeting_id}


@app.post("/api/meetings/{meeting_id}/discuss")
async def submit_situation(meeting_id: str, request: SubmitSituationRequest):
    """
    Submit a business situation and run the complete executive board process.
    Includes: perspectives, cross-evaluation, optional debate, optional risk matrix, synthesis.
    """
    # Validate meeting ID format
    if not validate_meeting_id(meeting_id):
        raise HTTPException(status_code=400, detail="Invalid meeting ID format")

    # Check if meeting exists
    meeting = storage.get_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

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

    # Return the complete response with metadata
    return {
        "stage1_perspectives": stage1_results,
        "stage2_evaluations": stage2_results,
        "stage2_5_debate": debate_results,
        "stage3_synthesis": stage3_result,
        "risk_matrix": risk_matrix,
        "metadata": metadata
    }


@app.post("/api/meetings/{meeting_id}/discuss/stream")
async def submit_situation_stream(meeting_id: str, request: SubmitSituationRequest):
    """
    Submit a business situation and stream the executive board process.
    Returns Server-Sent Events as each stage completes.
    """
    # Validate meeting ID format
    if not validate_meeting_id(meeting_id):
        raise HTTPException(status_code=400, detail="Invalid meeting ID format")

    # Check if meeting exists
    meeting = storage.get_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Check if this is the first discussion
    is_first_discussion = len(meeting["discussions"]) == 0

    # Get industry from meeting
    industry = meeting.get("industry", "manufacturing")

    async def event_generator():
        try:
            # Add the business situation
            storage.add_situation(meeting_id, request.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_discussion:
                title_task = asyncio.create_task(generate_meeting_title(request.content))

            # Stage 1: Collect executive perspectives (with confidence scores)
            yield f"data: {json.dumps({'type': 'stage1_start', 'message': 'Collecting executive perspectives...'})}\n\n"
            stage1_results = await stage1_collect_perspectives(request.content, industry=industry)
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2: Cross-evaluations
            yield f"data: {json.dumps({'type': 'stage2_start', 'message': 'Executives evaluating each others perspectives...'})}\n\n"
            stage2_results, label_to_role = await stage2_cross_evaluation(request.content, stage1_results, industry=industry)
            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_role)
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_role': label_to_role, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Stage 2.5: Debate (optional)
            debate_results = None
            if request.include_debate:
                yield f"data: {json.dumps({'type': 'stage2_5_start', 'message': 'Executives debating and refining positions...'})}\n\n"
                debate_results = await stage2_5_debate(request.content, stage1_results, stage2_results, label_to_role, industry=industry)
                yield f"data: {json.dumps({'type': 'stage2_5_complete', 'data': debate_results})}\n\n"

            # Risk Matrix (optional, run in parallel with other tasks)
            risk_matrix = None
            risk_task = None
            if request.include_risk_matrix:
                yield f"data: {json.dumps({'type': 'risk_matrix_start', 'message': 'Generating risk matrix...'})}\n\n"
                risk_task = asyncio.create_task(generate_risk_matrix(request.content, stage1_results, stage2_results, industry=industry))

            # Stage 3: Council Speaker synthesis
            yield f"data: {json.dumps({'type': 'stage3_start', 'message': 'Council Speaker synthesizing final recommendation...'})}\n\n"

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
            yield f"data: {json.dumps({'type': 'error', 'message': 'Processing failed. Please try again.'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/api/compare")
async def compare_scenarios_endpoint(request: CompareScenarioRequest):
    """
    Compare multiple business scenarios side-by-side.
    Runs the council process on each scenario and generates a comparison.
    """
    if len(request.scenarios) < 2:
        raise HTTPException(status_code=400, detail="At least 2 scenarios required")
    if len(request.scenarios) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 scenarios allowed")

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
        raise HTTPException(status_code=400, detail="Invalid meeting ID format")

    meeting = storage.get_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

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
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")


def generate_meeting_markdown(meeting: Dict[str, Any]) -> str:
    """Generate markdown export of a meeting."""
    md = f"# Executive Board Meeting: {meeting['title']}\n\n"
    md += f"**Date:** {meeting['created_at']}\n\n"
    md += f"**Meeting ID:** {meeting['id']}\n\n"
    md += "---\n\n"

    for i, discussion in enumerate(meeting.get('discussions', []), 1):
        if discussion.get('role') == 'user':
            md += f"## Business Situation {i}\n\n"
            md += f"{discussion.get('content', '')}\n\n"
        elif discussion.get('role') == 'board':
            md += "### Executive Perspectives\n\n"
            for perspective in discussion.get('stage1_perspectives', []):
                md += f"#### {perspective.get('title', perspective.get('role', 'Unknown'))}\n\n"
                confidence = perspective.get('confidence', 'N/A')
                md += f"**Confidence:** {confidence}\n\n"
                md += f"{perspective.get('response', '')}\n\n"

            md += "### Cross-Evaluations\n\n"
            for evaluation in discussion.get('stage2_evaluations', []):
                md += f"#### Evaluation by {evaluation.get('title', evaluation.get('role', 'Unknown'))}\n\n"
                md += f"{evaluation.get('evaluation', '')}\n\n"

            if discussion.get('debate_results'):
                md += "### Debate Responses\n\n"
                for debate in discussion['debate_results']:
                    md += f"#### {debate.get('title', debate.get('role', 'Unknown'))} responds\n\n"
                    md += f"{debate.get('response', '')}\n\n"

            if discussion.get('risk_matrix', {}).get('risks'):
                md += "### Risk Matrix\n\n"
                md += "| Risk | Category | Likelihood | Impact | Owner |\n"
                md += "|------|----------|------------|--------|-------|\n"
                for risk in discussion['risk_matrix']['risks']:
                    md += f"| {risk.get('description', '')} | {risk.get('category', '')} | "
                    md += f"{risk.get('likelihood', '')} | {risk.get('impact', '')} | {risk.get('owner', '')} |\n"
                md += "\n"

            md += "### Final Recommendation\n\n"
            md += f"{discussion.get('stage3_synthesis', {}).get('response', '')}\n\n"

            md += "---\n\n"

    md += "\n*Generated by Executive Board Council*\n"
    return md


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

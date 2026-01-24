"""FastAPI backend for Executive Board Council."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
import json
import asyncio

from . import storage
from .council import (
    run_executive_board_meeting,
    generate_meeting_title,
    stage1_collect_perspectives,
    stage2_cross_evaluation,
    stage3_council_speaker_synthesis,
    calculate_aggregate_rankings
)

app = FastAPI(title="Executive Board Council API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateMeetingRequest(BaseModel):
    """Request to create a new executive board meeting."""
    pass


class SubmitSituationRequest(BaseModel):
    """Request to submit a business situation for board discussion."""
    content: str


class MeetingMetadata(BaseModel):
    """Meeting metadata for list view."""
    id: str
    created_at: str
    title: str
    discussion_count: int


class Meeting(BaseModel):
    """Full meeting with all discussions."""
    id: str
    created_at: str
    title: str
    discussions: List[Dict[str, Any]]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Executive Board Council API"}


@app.get("/api/meetings", response_model=List[MeetingMetadata])
async def list_meetings():
    """List all executive board meetings (metadata only)."""
    return storage.list_meetings()


@app.post("/api/meetings", response_model=Meeting)
async def create_meeting(request: CreateMeetingRequest):
    """Create a new executive board meeting."""
    meeting_id = str(uuid.uuid4())
    meeting = storage.create_meeting(meeting_id)
    return meeting


@app.get("/api/meetings/{meeting_id}", response_model=Meeting)
async def get_meeting(meeting_id: str):
    """Get a specific meeting with all its discussions."""
    meeting = storage.get_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@app.post("/api/meetings/{meeting_id}/discuss")
async def submit_situation(meeting_id: str, request: SubmitSituationRequest):
    """
    Submit a business situation and run the 3-stage executive board process.
    Returns the complete response with all stages.
    """
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

    # Run the 3-stage executive board process
    stage1_results, stage2_results, stage3_result, metadata = await run_executive_board_meeting(
        request.content
    )

    # Add board response with all stages
    storage.add_board_response(
        meeting_id,
        stage1_results,
        stage2_results,
        stage3_result
    )

    # Return the complete response with metadata
    return {
        "stage1_perspectives": stage1_results,
        "stage2_evaluations": stage2_results,
        "stage3_synthesis": stage3_result,
        "metadata": metadata
    }


@app.post("/api/meetings/{meeting_id}/discuss/stream")
async def submit_situation_stream(meeting_id: str, request: SubmitSituationRequest):
    """
    Submit a business situation and stream the 3-stage executive board process.
    Returns Server-Sent Events as each stage completes.
    """
    # Check if meeting exists
    meeting = storage.get_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Check if this is the first discussion
    is_first_discussion = len(meeting["discussions"]) == 0

    async def event_generator():
        try:
            # Add the business situation
            storage.add_situation(meeting_id, request.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_discussion:
                title_task = asyncio.create_task(generate_meeting_title(request.content))

            # Stage 1: Collect executive perspectives
            yield f"data: {json.dumps({'type': 'stage1_start', 'message': 'Collecting executive perspectives...'})}\n\n"
            stage1_results = await stage1_collect_perspectives(request.content)
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2: Cross-evaluations
            yield f"data: {json.dumps({'type': 'stage2_start', 'message': 'Executives evaluating each other\\'s perspectives...'})}\n\n"
            stage2_results, label_to_role = await stage2_cross_evaluation(request.content, stage1_results)
            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_role)
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_role': label_to_role, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Stage 3: Council Speaker synthesis
            yield f"data: {json.dumps({'type': 'stage3_start', 'message': 'Council Speaker synthesizing final recommendation...'})}\n\n"
            stage3_result = await stage3_council_speaker_synthesis(request.content, stage1_results, stage2_results)
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
                stage3_result
            )

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

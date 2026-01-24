"""JSON-based storage for executive board meetings/conversations."""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from .config import DATA_DIR


def ensure_data_dir():
    """Ensure the data directory exists."""
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)


def get_meeting_path(meeting_id: str) -> str:
    """Get the file path for a meeting."""
    return os.path.join(DATA_DIR, f"{meeting_id}.json")


def create_meeting(meeting_id: str) -> Dict[str, Any]:
    """
    Create a new executive board meeting.

    Args:
        meeting_id: Unique identifier for the meeting

    Returns:
        New meeting dict
    """
    ensure_data_dir()

    meeting = {
        "id": meeting_id,
        "created_at": datetime.utcnow().isoformat(),
        "title": "Executive Board Meeting",
        "discussions": []
    }

    # Save to file
    path = get_meeting_path(meeting_id)
    with open(path, 'w') as f:
        json.dump(meeting, f, indent=2)

    return meeting


def get_meeting(meeting_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a meeting from storage.

    Args:
        meeting_id: Unique identifier for the meeting

    Returns:
        Meeting dict or None if not found
    """
    path = get_meeting_path(meeting_id)

    if not os.path.exists(path):
        return None

    with open(path, 'r') as f:
        return json.load(f)


def save_meeting(meeting: Dict[str, Any]):
    """
    Save a meeting to storage.

    Args:
        meeting: Meeting dict to save
    """
    ensure_data_dir()

    path = get_meeting_path(meeting['id'])
    with open(path, 'w') as f:
        json.dump(meeting, f, indent=2)


def list_meetings() -> List[Dict[str, Any]]:
    """
    List all meetings (metadata only).

    Returns:
        List of meeting metadata dicts
    """
    ensure_data_dir()

    meetings = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            path = os.path.join(DATA_DIR, filename)
            with open(path, 'r') as f:
                data = json.load(f)
                meetings.append({
                    "id": data["id"],
                    "created_at": data["created_at"],
                    "title": data.get("title", "Executive Board Meeting"),
                    "discussion_count": len(data["discussions"])
                })

    # Sort by creation time, newest first
    meetings.sort(key=lambda x: x["created_at"], reverse=True)

    return meetings


def add_situation(meeting_id: str, content: str):
    """
    Add a business situation/question to discuss.

    Args:
        meeting_id: Meeting identifier
        content: The business situation description
    """
    meeting = get_meeting(meeting_id)
    if meeting is None:
        raise ValueError(f"Meeting {meeting_id} not found")

    meeting["discussions"].append({
        "role": "user",
        "content": content
    })

    save_meeting(meeting)


def add_board_response(
    meeting_id: str,
    stage1: List[Dict[str, Any]],
    stage2: List[Dict[str, Any]],
    stage3: Dict[str, Any]
):
    """
    Add the complete board response with all 3 stages.

    Args:
        meeting_id: Meeting identifier
        stage1: List of individual executive perspectives
        stage2: List of cross-evaluations
        stage3: Council Speaker's final synthesis
    """
    meeting = get_meeting(meeting_id)
    if meeting is None:
        raise ValueError(f"Meeting {meeting_id} not found")

    meeting["discussions"].append({
        "role": "board",
        "stage1_perspectives": stage1,
        "stage2_evaluations": stage2,
        "stage3_synthesis": stage3
    })

    save_meeting(meeting)


def update_meeting_title(meeting_id: str, title: str):
    """
    Update the title of a meeting.

    Args:
        meeting_id: Meeting identifier
        title: New title for the meeting
    """
    meeting = get_meeting(meeting_id)
    if meeting is None:
        raise ValueError(f"Meeting {meeting_id} not found")

    meeting["title"] = title
    save_meeting(meeting)

"""JSON-based storage for executive board meetings/conversations."""

import json
import os
import logging
import tempfile
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
from .config import DATA_DIR

logger = logging.getLogger(__name__)


def ensure_data_dir():
    """Ensure the data directory exists."""
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)


def get_meeting_path(meeting_id: str) -> str:
    """Get the file path for a meeting."""
    # Validate meeting_id to prevent path traversal
    if not meeting_id or '/' in meeting_id or '\\' in meeting_id or '..' in meeting_id:
        raise ValueError(f"Invalid meeting ID: {meeting_id}")
    return os.path.join(DATA_DIR, f"{meeting_id}.json")


def _atomic_write(path: str, data: Dict[str, Any]):
    """Write data atomically using temp file + rename."""
    ensure_data_dir()
    dir_path = os.path.dirname(path)

    # Write to temp file first, then rename (atomic on POSIX)
    fd, temp_path = tempfile.mkstemp(dir=dir_path, suffix='.json')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, path)  # Atomic rename
    except Exception:
        # Clean up temp file on failure
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def create_meeting(meeting_id: str) -> Dict[str, Any]:
    """
    Create a new executive board meeting.

    Args:
        meeting_id: Unique identifier for the meeting

    Returns:
        New meeting dict
    """
    meeting = {
        "id": meeting_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "title": "Executive Board Meeting",
        "discussions": []
    }

    # Save to file atomically
    path = get_meeting_path(meeting_id)
    _atomic_write(path, meeting)

    return meeting


def get_meeting(meeting_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a meeting from storage.

    Args:
        meeting_id: Unique identifier for the meeting

    Returns:
        Meeting dict or None if not found or corrupted
    """
    try:
        path = get_meeting_path(meeting_id)
    except ValueError:
        logger.warning(f"Invalid meeting ID attempted: {meeting_id}")
        return None

    if not os.path.exists(path):
        return None

    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Corrupted meeting file {meeting_id}: {e}")
        return None
    except IOError as e:
        logger.error(f"Error reading meeting file {meeting_id}: {e}")
        return None


def save_meeting(meeting: Dict[str, Any]):
    """
    Save a meeting to storage atomically.

    Args:
        meeting: Meeting dict to save
    """
    path = get_meeting_path(meeting['id'])
    _atomic_write(path, meeting)


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
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    meetings.append({
                        "id": data["id"],
                        "created_at": data["created_at"],
                        "title": data.get("title", "Executive Board Meeting"),
                        "discussion_count": len(data.get("discussions", []))
                    })
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping corrupted meeting file {filename}: {e}")
                continue
            except (KeyError, TypeError) as e:
                logger.warning(f"Skipping malformed meeting file {filename}: {e}")
                continue

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

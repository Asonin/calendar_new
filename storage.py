"""
Storage module for Agentic Calendar.
Handles JSON session persistence to disk.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from models import Session


SESSIONS_DIR = Path(__file__).parent / "sessions"


def ensure_sessions_dir():
    """Ensure the sessions directory exists."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def get_session_path(session_id: str) -> Path:
    """Get the file path for a session."""
    return SESSIONS_DIR / f"session_{session_id}.json"


def create_session() -> Session:
    """Create a new session and save it to disk."""
    ensure_sessions_dir()
    session = Session()
    save_session(session)
    return session


def save_session(session: Session) -> None:
    """Save a session to disk."""
    ensure_sessions_dir()
    session.update_timestamp()
    path = get_session_path(session.session_id)

    # Convert to JSON-serializable dict
    data = session.model_dump(mode='json')

    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def load_session(session_id: str) -> Optional[Session]:
    """Load a session from disk."""
    path = get_session_path(session_id)

    if not path.exists():
        return None

    with open(path, 'r') as f:
        data = json.load(f)

    return Session.model_validate(data)


def list_sessions() -> list[dict]:
    """List all saved sessions with basic info."""
    ensure_sessions_dir()
    sessions = []

    for file in SESSIONS_DIR.glob("session_*.json"):
        try:
            with open(file, 'r') as f:
                data = json.load(f)
            sessions.append({
                'session_id': data.get('session_id'),
                'created_at': data.get('created_at'),
                'updated_at': data.get('updated_at'),
                'has_goal': data.get('goal_understanding') is not None,
                'task_count': len(data.get('task_blocks', [])),
            })
        except (json.JSONDecodeError, KeyError):
            continue

    # Sort by updated_at, most recent first
    sessions.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
    return sessions


def delete_session(session_id: str) -> bool:
    """Delete a session from disk."""
    path = get_session_path(session_id)

    if path.exists():
        path.unlink()
        return True
    return False


def get_exports_dir() -> Path:
    """Get the exports directory path."""
    exports_dir = Path(__file__).parent / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    return exports_dir

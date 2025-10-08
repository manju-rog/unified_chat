"""Session management utilities."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

from .config import get_settings
from .models import SessionState


class SessionManager:
    """In-memory session registry (replace with Redis/DB in production)."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._sessions: Dict[str, SessionState] = {}

    def get_or_create(self, session_id: Optional[str]) -> SessionState:
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
        else:
            session = SessionState(session_id=session_id or self._generate_id())
            self._sessions[session.session_id] = session
        return session

    def touch(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if session:
            session.last_activity = datetime.utcnow()

    def cleanup_expired(self) -> None:
        expiry_minutes = self._settings.session_expiry_minutes
        threshold = datetime.utcnow() - timedelta(minutes=expiry_minutes)
        expired = [sid for sid, sess in self._sessions.items() if sess.last_activity < threshold]
        for sid in expired:
            del self._sessions[sid]

    def _generate_id(self) -> str:
        return uuid.uuid4().hex


session_manager = SessionManager()

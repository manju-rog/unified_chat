from typing import Dict, Optional
from datetime import datetime, timedelta
import logging
from app.models.sow_models import SessionData, ConversationStage
from app.config import settings

logger = logging.getLogger(__name__)

class StateService:
    """Service for managing session state (in-memory)"""
    
    def __init__(self):
        # In-memory storage (use Redis in production)
        self._sessions: Dict[str, SessionData] = {}
        self.session_timeout = settings.SESSION_TIMEOUT
    
    def create_session(self, session_id: str, template_id: str = None, template_path: str = None) -> SessionData:
        """Create new session"""
        session = SessionData(
            session_id=session_id,
            template_id=template_id,
            template_path=template_path
        )
        self._sessions[session_id] = session
        logger.info(f"Session created: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID"""
        session = self._sessions.get(session_id)
        
        if session:
            # Check if session has expired
            if self._is_session_expired(session):
                logger.warning(f"Session expired: {session_id}")
                self.delete_session(session_id)
                return None
        
        return session
    
    def update_session(self, session_id: str, session_data: SessionData):
        """Update session data"""
        session_data.updated_at = datetime.now()
        self._sessions[session_id] = session_data
        logger.info(f"Session updated: {session_id}")
    
    def delete_session(self, session_id: str):
        """Delete session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Session deleted: {session_id}")
    
    def _is_session_expired(self, session: SessionData) -> bool:
        """Check if session has expired"""
        expiry_time = session.updated_at + timedelta(seconds=self.session_timeout)
        return datetime.now() > expiry_time
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add message to conversation history"""
        session = self.get_session(session_id)
        if session:
            session.conversation_history.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
            self.update_session(session_id, session)
    
    def advance_stage(self, session_id: str, next_stage: ConversationStage):
        """Advance conversation to next stage"""
        session = self.get_session(session_id)
        if session:
            session.current_stage = next_stage
            self.update_session(session_id, session)
            logger.info(f"Session {session_id} advanced to stage: {next_stage}")
    
    def mark_completed(self, session_id: str):
        """Mark session as completed"""
        session = self.get_session(session_id)
        if session:
            session.is_completed = True
            session.current_stage = ConversationStage.COMPLETED
            self.update_session(session_id, session)
    
    def get_all_sessions(self) -> Dict[str, SessionData]:
        """Get all active sessions (for admin/debugging)"""
        return self._sessions
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        expired_sessions = [
            sid for sid, session in self._sessions.items()
            if self._is_session_expired(session)
        ]
        
        for sid in expired_sessions:
            self.delete_session(sid)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

# Global state service instance
state_service = StateService()

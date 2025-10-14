import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from ..models.sow_models import SessionData, ConversationStage

logger = logging.getLogger(__name__)

class StateService:
    """Service for managing SOW session state"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
        self.session_timeout = 3600  # 1 hour
    
    def create_session(
        self,
        session_id: str,
        template_id: str = None,
        template_path: str = None
    ) -> SessionData:
        """Create new session"""
        session = SessionData(
            session_id=session_id,
            template_id=template_id,
            template_path=template_path,
            current_stage=ConversationStage.INITIAL
        )
        
        self.sessions[session_id] = session
        logger.info(f"Created new SOW session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID"""
        session = self.sessions.get(session_id)
        if session:
            # Check if session is expired
            if self._is_session_expired(session):
                self.delete_session(session_id)
                return None
        return session
    
    def update_session(self, session_id: str, session_data: SessionData) -> bool:
        """Update session data"""
        if session_id in self.sessions:
            session_data.updated_at = datetime.now()
            self.sessions[session_id] = session_data
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted SOW session: {session_id}")
            return True
        return False
    
    def add_message(self, session_id: str, role: str, message: str) -> bool:
        """Add message to session history"""
        session = self.get_session(session_id)
        if session:
            session.conversation_history.append({
                "role": role,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
            session.updated_at = datetime.now()
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if self._is_session_expired(session):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def _is_session_expired(self, session: SessionData) -> bool:
        """Check if session is expired"""
        expiry_time = session.updated_at + timedelta(seconds=self.session_timeout)
        return datetime.now() > expiry_time

# Global instance
state_service = StateService()
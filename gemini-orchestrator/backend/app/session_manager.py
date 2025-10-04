"""
Session state manager for tracking conversation context.
Implements in-memory session storage with get/update operations.
Requirements: 5.1, 5.2, 5.3
"""

from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from app.models import SessionState

# In-memory session storage
_sessions: Dict[str, SessionState] = {}


def get_session(session_id: Optional[str] = None) -> SessionState:
    """
    Retrieve an existing session or create a new one.
    
    Args:
        session_id: Optional session identifier. If None, creates new session.
    
    Returns:
        SessionState: The session state object
    
    Requirements: 5.1
    """
    # Generate new session ID if not provided
    if session_id is None:
        session_id = str(uuid4())
    
    # Return existing session if found
    if session_id in _sessions:
        return _sessions[session_id]
    
    # Create new session
    new_session = SessionState(
        session_id=session_id,
        mode="IDLE",
        active_sow_id=None,
        collected_slots={},
        conversation_history=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    _sessions[session_id] = new_session
    return new_session


def update_session(
    session_id: str,
    mode: Optional[str] = None,
    active_sow_id: Optional[str] = None,
    collected_slots: Optional[Dict] = None,
    conversation_turn: Optional[Dict] = None
) -> SessionState:
    """
    Update session state with new information.
    
    Args:
        session_id: Session identifier
        mode: New mode (IDLE, ABSENCE, SOW) if changing
        active_sow_id: Active SOW session ID if in SOW mode
        collected_slots: Updated slots dictionary
        conversation_turn: New conversation turn to add to history
    
    Returns:
        SessionState: Updated session state
    
    Requirements: 5.2, 5.3
    """
    # Get or create session
    session = get_session(session_id)
    
    # Update mode if provided
    if mode is not None:
        session.mode = mode
    
    # Update active SOW ID if provided
    if active_sow_id is not None:
        session.active_sow_id = active_sow_id
    
    # Update collected slots if provided
    if collected_slots is not None:
        session.collected_slots.update(collected_slots)
    
    # Add conversation turn to history if provided
    if conversation_turn is not None:
        session.conversation_history.append(conversation_turn)
        
        # Keep only last 20 turns to prevent memory bloat
        if len(session.conversation_history) > 20:
            session.conversation_history = session.conversation_history[-20:]
    
    # Update timestamp
    session.updated_at = datetime.now()
    
    # Persist to storage
    _sessions[session_id] = session
    
    return session


def clear_session(session_id: str) -> bool:
    """
    Clear a session from storage.
    
    Args:
        session_id: Session identifier to clear
    
    Returns:
        bool: True if session was found and cleared, False otherwise
    """
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


def get_all_sessions() -> Dict[str, SessionState]:
    """
    Get all active sessions (for debugging/monitoring).
    
    Returns:
        Dict of session_id -> SessionState
    """
    return _sessions.copy()

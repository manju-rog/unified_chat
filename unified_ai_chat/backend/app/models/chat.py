"""Chat-related models and state containers."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


Role = Literal["user", "assistant", "system"]


@dataclass
class Message:
    """Represents a single chat message in a session."""

    role: Role
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SOWSessionState:
    """Holds state for an in-progress SOW generation flow."""

    generator: Any
    current_step: str
    collected_sections: Dict[str, str] = field(default_factory=dict)
    generated_files: List[str] = field(default_factory=list)


@dataclass
class SessionState:
    """Tracks the lifetime of a conversation session."""

    session_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    active_domain: Optional[str] = None
    sow_state: Optional[SOWSessionState] = None
    sow_session_id: Optional[str] = None  # Reference to new SOW session
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: Role, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        msg = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(msg)
        self.last_activity = msg.timestamp

    def recent_history(self, limit: int) -> List[Dict[str, str]]:
        """Return formatted history for Gemini requests."""

        history = []
        for message in self.messages[-limit:]:
            history.append({"role": message.role, "parts": [message.content]})
        return history


class ChatRequest(BaseModel):
    """Incoming chat request from the client UI."""

    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = Field(None, alias="session_id")


class DisambiguationOption(BaseModel):
    """Represents a clickable option for disambiguation."""
    
    id: str
    label: str
    value: Any
    metadata: Optional[Dict[str, Any]] = None


class ConfirmationButton(BaseModel):
    """Represents a confirmation button that can either submit or populate input."""
    
    id: str
    label: str
    value: Optional[str] = None  # For auto-submit behavior
    populate_input: Optional[str] = None  # For input population behavior
    style: Optional[str] = "primary"  # "primary" or "secondary"


class ChatResponse(BaseModel):
    """Outgoing response returned to the client."""

    session_id: str
    response: str
    intent: Optional[str] = None
    action_type: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None
    download_url: Optional[str] = None
    errors: Optional[List[str]] = None
    disambiguation_options: Optional[List[DisambiguationOption]] = None
    confirmation_buttons: Optional[List[ConfirmationButton]] = None
    requires_confirmation: bool = False
    thinking: Optional[str] = None  # Gemini's reasoning/thinking process

"""
Pydantic models for the Gemini Orchestrator.
Defines data structures for ChatResponse, SessionState, and tool schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import re


# ============================================================================
# ChatResponse Envelope (Subtask 2.1)
# ============================================================================

class ChatResponse(BaseModel):
    """
    Response envelope returned by the orchestrator.
    Requirements: 7.5
    """
    mode: str = Field(..., description="Current session mode: IDLE, ABSENCE, or SOW")
    intent: Optional[str] = Field(None, description="Detected intent (e.g., mark_absent, start_sow)")
    slots: Dict[str, Any] = Field(default_factory=dict, description="Collected information from conversation")
    tool_call: Optional[Dict[str, Any]] = Field(None, description="Tool call details: {name: str, args: dict}")
    message_to_user: str = Field(..., description="AI response text to display to user")


class SessionState(BaseModel):
    """
    In-memory session state for tracking conversation context.
    Requirements: 5.1, 5.2
    """
    session_id: str = Field(..., description="Unique session identifier")
    mode: str = Field(default="IDLE", description="Current mode: IDLE, ABSENCE, or SOW")
    active_sow_id: Optional[str] = Field(None, description="Active SOW session ID if in SOW mode")
    collected_slots: Dict[str, Any] = Field(default_factory=dict, description="Information collected during conversation")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Recent conversation turns")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")


# ============================================================================
# Absence Tool Models (Subtask 2.2)
# ============================================================================

class AbsenceRequest(BaseModel):
    """
    Request model for marking an employee absent.
    Requirements: 9.1
    """
    employee_id: str = Field(..., description="Employee identifier")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    reason: Optional[str] = Field(None, description="Optional reason for absence")
    
    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date is in YYYY-MM-DD format"""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v


class PresenceRequest(BaseModel):
    """
    Request model for marking an employee present.
    Requirements: 9.2
    """
    employee_id: str = Field(..., description="Employee identifier")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    
    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date is in YYYY-MM-DD format"""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v


# ============================================================================
# SOW Tool Models (Subtask 2.3)
# ============================================================================

class ContactInfo(BaseModel):
    """
    Contact information for SOW parties.
    Requirements: 10.1, 10.2
    """
    name: str = Field(..., description="Contact person name")
    email: str = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Physical address")


class ServiceItem(BaseModel):
    """
    Service item for SOW.
    Requirements: 10.1, 10.2
    """
    name: str = Field(..., description="Service name")
    description: str = Field(..., description="Service description")


class DeliverableItem(BaseModel):
    """
    Deliverable item for SOW.
    Requirements: 10.1, 10.2
    """
    name: str = Field(..., description="Deliverable name")
    description: str = Field(..., description="Deliverable description")


class SowStart(BaseModel):
    """
    Request model for starting a new SOW session.
    Requirements: 10.1
    """
    project_name: str = Field(..., description="Name of the project for the SOW")


class SowUpdate(BaseModel):
    """
    Request model for updating SOW session with collected information.
    Requirements: 10.2
    """
    sow_id: str = Field(..., description="SOW session identifier")
    oracle_rep: Optional[ContactInfo] = Field(None, description="Oracle representative contact")
    billing_contact: Optional[ContactInfo] = Field(None, description="Billing contact information")
    services: Optional[List[ServiceItem]] = Field(None, description="List of services")
    deliverables: Optional[List[DeliverableItem]] = Field(None, description="List of deliverables")
    acceptance: Optional[str] = Field(None, description="Acceptance criteria")

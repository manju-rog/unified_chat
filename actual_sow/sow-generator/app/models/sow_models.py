from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from enum import Enum

class ConversationStage(str, Enum):
    """Enumeration of conversation stages"""
    INITIAL = "initial"
    PROJECT_INFO = "project_info"
    SERVICES = "services"
    DELIVERABLES = "deliverables"
    TIMELINE = "timeline"
    RESOURCES = "resources"
    CONTACTS = "contacts"
    BUDGET = "budget"
    COMPLETED = "completed"

class ProjectInfo(BaseModel):
    """Project identification information"""
    document_number: Optional[str] = ""  # ✓ Allow None with default
    project_name: Optional[str] = ""  # ✓ Allow None with default
    objectives: List[str] = []

class Service(BaseModel):
    """Service definition"""
    name: str
    description: Optional[str] = "To be defined"  # ✓ Provide default
    duration: Optional[str] = "TBD"  # ✓ Provide default

class Deliverable(BaseModel):
    """Deliverable information"""
    id: int
    name: str
    description: str
    sprint_start: Optional[int] = None      # ← NEW: Starting sprint number
    sprint_end: Optional[int] = None        # ← NEW: Ending sprint number
    sprint_duration: Optional[int] = None   # ← NEW: Number of sprints
    
    def get_full_description(self) -> str:
        """Get description with sprint information"""
        if self.sprint_start and self.sprint_end:
            sprint_info = f"Delivery: Sprints {self.sprint_start}-{self.sprint_end} ({self.sprint_duration} sprints)"
            return f"{self.description}\n{sprint_info}"
        return self.description


class Resource(BaseModel):
    """Resource allocation information"""
    role: str
    team: Optional[str] = "General"  # ✓ Provide default
    count: int = 1
    allocation: Optional[str] = "TBD"  # ✓ Provide default

class Contact(BaseModel):
    """Contact information for contractor or client"""
    name: Optional[str] = ""  # ✓ Allow None
    company: Optional[str] = ""  # ✓ Allow None
    address: Optional[str] = ""  # ✓ Allow None
    phone: Optional[str] = ""  # ✓ Allow None
    email: Optional[str] = ""  # ✓ Allow None (changed from EmailStr)
    role: Optional[str] = ""  # ✓ Allow None

class Milestone(BaseModel):
    """Milestone with associated fee"""
    id: int = 0
    name: str
    fee: float
    description: Optional[str] = None

class ProjectTimeline(BaseModel):
    """Project timeline information"""
    start_date: Optional[date] = None  # ✓ Allow None
    end_date: Optional[date] = None  # ✓ Allow None
    total_sprints: Optional[int] = 0  # ✓ Allow None
    sprint_duration: str = "2 weeks"

# ... rest of the models remain the same


class SOWContext(BaseModel):
    """Complete SOW context for document generation"""
    # Project Information
    project_info: Optional[ProjectInfo] = None
    
    # Services and Deliverables
    services: List[Service] = []
    deliverables: List[Deliverable] = []
    
    # Timeline
    timeline: Optional[ProjectTimeline] = None
    
    # Resources
    resources: List[Resource] = []
    
    # Contacts
    contractor_contact: Optional[Contact] = None
    client_contact: Optional[Contact] = None
    
    # Budget
    milestones: List[Milestone] = []
    total_fee: float = 0.0
    estimated_expenses: float = 0.0
    
    # Additional Information
    assumptions: List[str] = []
    terms: List[str] = []
    
    def calculate_total_fee(self):
        """Calculate total fee from milestones"""
        self.total_fee = sum(m.fee for m in self.milestones)
        return self.total_fee

# Find the SessionData class and add raw_responses field

class SessionData(BaseModel):
    """Session data for conversation tracking"""
    session_id: str
    template_id: Optional[str] = None
    template_path: Optional[str] = None
    current_stage: ConversationStage = ConversationStage.INITIAL
    sow_context: SOWContext = SOWContext()
    conversation_history: List[Dict[str, str]] = []
    raw_responses: Dict[str, str] = {}  # ✓ Add this line
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_completed: bool = False


class TemplateUploadResponse(BaseModel):
    """Response for template upload"""
    template_id: str
    filename: str
    placeholders: List[str]
    message: str

class ConversationMessage(BaseModel):
    """WebSocket message structure"""
    session_id: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)

class BotResponse(BaseModel):
    """Bot response structure"""
    message: str
    stage: ConversationStage
    progress: float  # Percentage of completion
    is_complete: bool = False
    requires_input: bool = True

from pydantic import BaseModel, Field
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
    document_number: Optional[str] = ""
    project_name: Optional[str] = ""
    objectives: List[str] = []

class Service(BaseModel):
    """Service definition"""
    name: str
    description: Optional[str] = "To be defined"
    duration: Optional[str] = "TBD"

class Deliverable(BaseModel):
    """Deliverable information"""
    id: int
    name: str
    description: str
    sprint_start: Optional[int] = None
    sprint_end: Optional[int] = None
    sprint_duration: Optional[int] = None
    
    def get_full_description(self) -> str:
        """Get description with sprint information"""
        if self.sprint_start and self.sprint_end:
            sprint_info = f"Delivery: Sprints {self.sprint_start}-{self.sprint_end} ({self.sprint_duration} sprints)"
            return f"{self.description}\n{sprint_info}"
        return self.description

class Resource(BaseModel):
    """Resource allocation information"""
    role: str
    team: Optional[str] = "General"
    count: int = 1
    allocation: Optional[str] = "TBD"

class Contact(BaseModel):
    """Contact information for contractor or client"""
    name: Optional[str] = ""
    company: Optional[str] = ""
    address: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    role: Optional[str] = ""

class Milestone(BaseModel):
    """Milestone with associated fee"""
    id: int = 0
    name: str
    fee: float
    description: Optional[str] = None

class ProjectTimeline(BaseModel):
    """Project timeline information"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_sprints: Optional[int] = 0
    sprint_duration: str = "2 weeks"

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

class SessionData(BaseModel):
    """Session data for conversation tracking"""
    session_id: str
    template_id: Optional[str] = None
    template_path: Optional[str] = None
    current_stage: ConversationStage = ConversationStage.INITIAL
    sow_context: SOWContext = SOWContext()
    conversation_history: List[Dict[str, str]] = []
    raw_responses: Dict[str, str] = {}
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_completed: bool = False

class BotResponse(BaseModel):
    """Bot response structure"""
    message: str
    stage: ConversationStage
    progress: float  # Percentage of completion
    is_complete: bool = False
    requires_input: bool = True
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class ResourceItem:
    role: str
    count: int = 1

@dataclass
class ContactInfo:
    client_name: Optional[str] = None
    contractor_name: Optional[str] = None
    client_email: Optional[str] = None
    contractor_email: Optional[str] = None
    client_phone: Optional[str] = None
    contractor_phone: Optional[str] = None

@dataclass
class SowState:
    stage: str = "project_info"
    data: Dict = field(default_factory=lambda: {
        "project_info": "",
        "services": "",
        "deliverables": "",
        "timeline": "",
        "resources": [],   # list[{"role": str, "count": int}]
        "contacts": {},    # ContactInfo-like dict
        "budget": ""
    })
    
    def reset(self):
        self.stage = "project_info"
        self.data = {
            "project_info": "",
            "services": "",
            "deliverables": "",
            "timeline": "",
            "resources": [],
            "contacts": {},
            "budget": ""
        }

# Fixed order you asked for
STAGES = [
    "project_info",
    "services", 
    "deliverables",
    "timeline",
    "resources",
    "contacts",
    "budget"
]
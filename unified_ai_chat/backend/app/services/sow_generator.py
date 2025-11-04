"""
SOW Document Generator
Integrates with the use_sow system to generate professional SOW documents.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, date
import shutil

# Add use_sow to path for imports
use_sow_path = Path(__file__).parent.parent.parent.parent / "use_sow"
sys.path.insert(0, str(use_sow_path))

try:
    from app.services.document_service import DocumentService
    from app.models.sow_models import (
        SOWContext, ProjectInfo, Service, Deliverable, 
        ProjectTimeline, Resource, Contact, Milestone
    )
except ImportError as e:
    print(f"Warning: Could not import use_sow modules: {e}")
    # Fallback - we'll create minimal versions

class SOWDocumentGenerator:
    """Generates SOW documents using the use_sow system"""
    
    def __init__(self):
        self.template_path = use_sow_path / "sample_sow_template.docx"
        self.output_dir = Path("unified_ai_chat/backend/generated_docs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize document service
        try:
            self.doc_service = DocumentService()
        except:
            self.doc_service = None
    
    def generate_sow_document(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SOW document from session data"""
        try:
            # Convert session data to SOWContext
            sow_context = self._convert_session_to_sow_context(session_data)
            
            # Generate document using use_sow system
            if self.doc_service and self.template_path.exists():
                output_path = self.doc_service.generate_document(
                    str(self.template_path),
                    sow_context
                )
                
                # Move to our output directory
                filename = Path(output_path).name
                final_path = self.output_dir / filename
                shutil.move(output_path, final_path)
                
                return {
                    "success": True,
                    "filename": filename,
                    "path": str(final_path),
                    "download_url": f"/api/sow/download/{filename}",
                    "message": f"✅ SOW document generated successfully!\n\n📄 **{filename}**\n\nDocument is ready for download."
                }
            else:
                # Fallback generation
                return self._fallback_generation(session_data)
                
        except Exception as e:
            print(f"Error generating SOW: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "❌ Failed to generate SOW document. Please try again."
            }
    
    def _convert_session_to_sow_context(self, session_data: Dict[str, Any]) -> 'SOWContext':
        """Convert session data to SOWContext for use_sow system"""
        try:
            # Project Info
            project_info_data = session_data.get("project_info", {})
            project_info = ProjectInfo(
                document_number=project_info_data.get("document_number", ""),
                project_name=project_info_data.get("project_name", "Unnamed Project"),
                objectives=project_info_data.get("objectives", ["To be defined"])
            )
            
            # Services
            services = []
            for service_data in session_data.get("services", []):
                service = Service(
                    name=service_data.get("name", ""),
                    description=service_data.get("description", "To be defined"),
                    duration=service_data.get("duration", "TBD")
                )
                services.append(service)
            
            # Deliverables
            deliverables = []
            for deliv_data in session_data.get("deliverables", []):
                deliverable = Deliverable(
                    id=deliv_data.get("id", 1),
                    name=deliv_data.get("name", ""),
                    description=deliv_data.get("description", ""),
                    sprint_start=deliv_data.get("sprint_start"),
                    sprint_end=deliv_data.get("sprint_end"),
                    sprint_duration=deliv_data.get("sprint_duration")
                )
                deliverables.append(deliverable)
            
            # Timeline
            timeline_data = session_data.get("timeline", {})
            timeline = ProjectTimeline(
                start_date=self._parse_date(timeline_data.get("start_date")),
                end_date=self._parse_date(timeline_data.get("end_date")),
                total_sprints=timeline_data.get("total_sprints", 0),
                sprint_duration=timeline_data.get("sprint_duration", "2 weeks")
            )
            
            # Resources
            resources = []
            for resource_data in session_data.get("resources", []):
                resource = Resource(
                    role=resource_data.get("role", ""),
                    team=resource_data.get("team", "Development"),
                    count=resource_data.get("count", 1),
                    allocation=resource_data.get("allocation", "TBD")
                )
                resources.append(resource)
            
            # Contacts
            contacts_data = session_data.get("contacts", {})
            contractor_data = contacts_data.get("contractor", {})
            client_data = contacts_data.get("client", {})
            
            contractor_contact = Contact(
                name=contractor_data.get("name", ""),
                company=contractor_data.get("company", ""),
                address=contractor_data.get("address", ""),
                phone=contractor_data.get("phone", ""),
                email=contractor_data.get("email", ""),
                role=contractor_data.get("role", "Contractor")
            )
            
            client_contact = Contact(
                name=client_data.get("name", ""),
                company=client_data.get("company", ""),
                address=client_data.get("address", ""),
                phone=client_data.get("phone", ""),
                email=client_data.get("email", ""),
                role=client_data.get("role", "Client")
            )
            
            # Budget
            budget_data = session_data.get("budget", {})
            milestones = []
            for milestone_data in budget_data.get("milestones", []):
                milestone = Milestone(
                    id=milestone_data.get("id", 1),
                    name=milestone_data.get("name", ""),
                    fee=milestone_data.get("fee", 0.0),
                    description=milestone_data.get("description", "")
                )
                milestones.append(milestone)
            
            # Create SOWContext
            sow_context = SOWContext(
                project_info=project_info,
                services=services,
                deliverables=deliverables,
                timeline=timeline,
                resources=resources,
                contractor_contact=contractor_contact,
                client_contact=client_contact,
                milestones=milestones,
                total_fee=budget_data.get("total_fee", 0.0),
                estimated_expenses=budget_data.get("expenses", 0.0),
                assumptions=[],
                terms=[]
            )
            
            return sow_context
            
        except Exception as e:
            print(f"Error converting session data: {e}")
            raise
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            return None
        except:
            return None
    
    def _fallback_generation(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback document generation if use_sow system fails"""
        try:
            # Create a simple text-based SOW
            project_name = session_data.get("project_info", {}).get("project_name", "Unnamed Project")
            
            content = f"""
STATEMENT OF WORK
{project_name}

Generated on: {datetime.now().strftime("%B %d, %Y")}

PROJECT INFORMATION:
- Project Name: {project_name}
- Document Number: {session_data.get("project_info", {}).get("document_number", "TBD")}

SERVICES:
"""
            
            for service in session_data.get("services", []):
                content += f"- {service.get('name', 'Unnamed Service')}\n"
            
            content += "\nDELIVERABLES:\n"
            for deliv in session_data.get("deliverables", []):
                content += f"{deliv.get('id', 1)}. {deliv.get('name', 'Unnamed Deliverable')}\n"
            
            content += f"\nBUDGET:\n"
            budget = session_data.get("budget", {})
            content += f"Total Fee: ${budget.get('total_fee', 0):,.2f}\n"
            
            # Save as text file
            filename = f"SOW_{project_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            return {
                "success": True,
                "filename": filename,
                "path": str(filepath),
                "download_url": f"/api/sow/download/{filename}",
                "message": f"✅ SOW document generated (text format)!\n\n📄 **{filename}**\n\nDocument is ready for download."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "❌ Failed to generate SOW document."
            }

# Global instance
sow_generator = SOWDocumentGenerator()
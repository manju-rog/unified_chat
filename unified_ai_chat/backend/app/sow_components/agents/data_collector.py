import logging
from typing import Dict, Any, Optional, Tuple
import google.generativeai as genai
from ..models.sow_models import (
    SessionData, ConversationStage, ProjectInfo, Service,
    Deliverable, Resource, Contact, Milestone, ProjectTimeline
)
from ..utils.prompts import PromptTemplates
from ..services.contacts_service import ContactsService
from ..services.standard_services import STANDARD_SERVICES
from datetime import datetime
from ...config import get_settings

logger = logging.getLogger(__name__)

class DataCollectorAgent:
    """Agent responsible for collecting data through conversation"""
    
    def __init__(self):
        self.prompts = PromptTemplates()
        self.contacts_service = ContactsService()
        
        # Configure Gemini
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        
        # Create model with the latest Gemini model
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2048,
            }
        )
    
    async def process_user_input(
        self,
        session_data: SessionData,
        user_message: str
    ) -> Tuple[str, SessionData]:
        """Process user input and extract data"""
        current_stage = session_data.current_stage
        
        # Special handling for services stage
        if current_stage == ConversationStage.SERVICES:
            user_message_lower = user_message.strip().lower()
            
            if user_message_lower == "standard":
                logger.info("User selected STANDARD services - auto-populating")
                
                # Auto-fill with standard services
                for standard_service in STANDARD_SERVICES:
                    service = Service(
                        name=standard_service["name"],
                        description=standard_service["description"],
                        duration=standard_service.get("duration", "See project timeline")
                    )
                    session_data.sow_context.services.append(service)
                
                # Store the response
                session_data.raw_responses[current_stage.value] = "Standard services package selected"
                
                # Move to next stage
                next_stage, response_message = self._determine_next_stage(current_stage)
                session_data.current_stage = next_stage
                
                response_message = f"""✅ **Standard services package has been applied!**

The following comprehensive service package has been added to your SOW:

📋 **Design and Development / Test / Post-Go-live support for Data Extraction, Compression, and Transfer Implementation**

This includes all design, development, testing, and go-live activities with 15 detailed scope items.

{response_message}"""
                
                return response_message, session_data
            
            elif user_message_lower == "custom":
                logger.info("User selected CUSTOM services - waiting for input")
                
                # Store the choice but don't advance yet
                session_data.raw_responses[current_stage.value] = "Waiting for custom services input"
                
                return """Great! Please provide your custom services.

For each service, specify:
- Service name
- Description of what will be done
- Duration or timeline (e.g., "3 weeks", "2 months")

You can list multiple services at once.""", session_data
        
        # Store response
        session_data.raw_responses[current_stage.value] = user_message
        
        # Move to next stage
        next_stage, response_message = self._determine_next_stage(current_stage)
        session_data.current_stage = next_stage
        
        # If completed, extract all data
        if next_stage == ConversationStage.COMPLETED:
            logger.info("Reached COMPLETED stage - extracting all data")
            success = await self._extract_all_data(session_data)
            
            if success:
                session_data.is_completed = True
                response_message = """Perfect! I've collected all the necessary information for your Statement of Work.

**Summary of Information Collected:**
✓ Project Information
✓ Services  
✓ Deliverables
✓ Timeline
✓ Resources
✓ Contact Information
✓ Budget & Milestones

Your SOW document is ready to be generated!"""
            else:
                response_message = "Data collected, but there were some extraction issues. Please check server logs."
        
        return response_message, session_data
    
    async def _extract_all_data(self, session_data: SessionData) -> bool:
        """Extract all data using Gemini"""
        try:
            # Skip if services already populated
            services_already_populated = len(session_data.sow_context.services) > 0
            
            conversation = self._build_complete_conversation(session_data.raw_responses)
            
            prompt = f"""Extract complete SOW data from this conversation and return as JSON:

{conversation}

Return JSON with these fields:
- document_number: string
- project_name: string  
- objectives: array of strings
- services: array of objects with name, description, duration (only if not already populated)
- deliverables: array with name, description
- start_date: YYYY-MM-DD format
- end_date: YYYY-MM-DD format
- total_sprints: number
- sprint_duration: string
- resources: array with role, team, count, allocation
- contractor_contact: object with name, company, address, phone, email, role
- client_contact: object with name, company, address, phone, email, role
- milestones: array with name, fee, description
- estimated_expenses: number

Return only valid JSON, no explanations."""

            response = self.model.generate_content(prompt)
            
            if not response.text:
                logger.error("No response from Gemini")
                return False
            
            # Parse JSON response
            import json
            try:
                extracted_data = json.loads(response.text.strip())
            except json.JSONDecodeError:
                # Try to extract JSON from markdown
                text = response.text
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]
                extracted_data = json.loads(text.strip())
            
            # Skip services if already populated
            if services_already_populated:
                extracted_data.pop("services", None)
            
            # Populate context
            self._populate_context_from_dict(session_data, extracted_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in data extraction: {e}")
            return False
    
    def _build_complete_conversation(self, raw_responses: Dict[str, str]) -> str:
        """Build complete conversation from all raw responses"""
        conversation_parts = []
        
        for stage_name, response in raw_responses.items():
            question = self.prompts.STAGE_QUESTIONS.get(stage_name, "")
            conversation_parts.append(f"""
**Stage: {stage_name.upper()}**
Question: {question}
User Response: {response}
""")
        
        return "\n".join(conversation_parts)
    
    def _populate_context_from_dict(self, session_data: SessionData, data: Dict[str, Any]):
        """Populate SOW context from extracted dictionary"""
        try:
            # Project Info
            if "document_number" in data and "project_name" in data:
                session_data.sow_context.project_info = ProjectInfo(
                    document_number=data.get("document_number", ""),
                    project_name=data.get("project_name", ""),
                    objectives=list(data.get("objectives", []))
                )

            # Services (only if not already populated)
            if "services" in data and len(session_data.sow_context.services) == 0:
                services_data = data.get("services", [])
                for svc in services_data:
                    service = Service(
                        name=svc.get("name", ""),
                        description=svc.get("description", ""),
                        duration=svc.get("duration", "")
                    )
                    session_data.sow_context.services.append(service)
            
            # Deliverables
            deliverables_data = data.get("deliverables", [])
            for idx, deliv in enumerate(deliverables_data, 1):
                deliverable = Deliverable(
                    id=idx,
                    name=deliv.get("name", ""),
                    description=deliv.get("description", "")
                )
                session_data.sow_context.deliverables.append(deliverable)
            
            # Timeline
            if "start_date" in data or "end_date" in data:
                start_date = None
                end_date = None
                
                if data.get("start_date"):
                    try:
                        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
                    except:
                        logger.warning(f"Could not parse start date: {data['start_date']}")
                
                if data.get("end_date"):
                    try:
                        end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
                    except:
                        logger.warning(f"Could not parse end date: {data['end_date']}")
                
                session_data.sow_context.timeline = ProjectTimeline(
                    start_date=start_date,
                    end_date=end_date,
                    total_sprints=int(data.get("total_sprints", 0)),
                    sprint_duration=data.get("sprint_duration", "2 weeks")
                )
            
            # Resources
            resources_data = data.get("resources", [])
            for res in resources_data:
                resource = Resource(
                    role=res.get("role", ""),
                    team=res.get("team", "General"),
                    count=int(res.get("count", 1)),
                    allocation=res.get("allocation", "Full-time")
                )
                session_data.sow_context.resources.append(resource)
            
            # Contacts with lookup
            self._handle_contacts(session_data, data)
            
            # Milestones
            milestones_data = data.get("milestones", [])
            for idx, mile in enumerate(milestones_data, 1):
                milestone = Milestone(
                    id=idx,
                    name=mile.get("name", ""),
                    fee=float(mile.get("fee", 0)),
                    description=mile.get("description", "")
                )
                session_data.sow_context.milestones.append(milestone)
            
            # Expenses
            session_data.sow_context.estimated_expenses = float(data.get("estimated_expenses", 0))
            session_data.sow_context.calculate_total_fee()
            
            logger.info("All data populated successfully!")
            
        except Exception as e:
            logger.error(f"Error populating context: {e}")
    
    def _handle_contacts(self, session_data: SessionData, data: Dict[str, Any]):
        """Handle contact information with database lookup"""
        # Try to find contacts in database
        client_company = ""
        contractor_company = ""
        
        if "client_contact" in data:
            client_company = data["client_contact"].get("company", "")
        if "contractor_contact" in data:
            contractor_company = data["contractor_contact"].get("company", "")
        
        # Lookup contractor
        contractor_contact_data = self.contacts_service.get_contractor_contact(contractor_company) if contractor_company else None
        
        if contractor_contact_data:
            session_data.sow_context.contractor_contact = Contact(**contractor_contact_data)
        elif "contractor_contact" in data:
            cc = data["contractor_contact"]
            session_data.sow_context.contractor_contact = Contact(
                name=cc.get("name", ""),
                company=cc.get("company", ""),
                address=cc.get("address", ""),
                phone=cc.get("phone", ""),
                email=cc.get("email", ""),
                role=cc.get("role", "")
            )
        
        # Lookup client
        client_contact_data = self.contacts_service.get_client_contact(client_company) if client_company else None
        
        if client_contact_data:
            session_data.sow_context.client_contact = Contact(**client_contact_data)
        elif "client_contact" in data:
            cc = data["client_contact"]
            session_data.sow_context.client_contact = Contact(
                name=cc.get("name", ""),
                company=cc.get("company", ""),
                address=cc.get("address", ""),
                phone=cc.get("phone", ""),
                email=cc.get("email", ""),
                role=cc.get("role", "")
            )
    
    def _determine_next_stage(self, current_stage: ConversationStage) -> Tuple[ConversationStage, str]:
        """Determine next conversation stage"""
        stage_flow = [
            ConversationStage.PROJECT_INFO,
            ConversationStage.SERVICES,
            ConversationStage.DELIVERABLES,
            ConversationStage.TIMELINE,
            ConversationStage.RESOURCES,
            ConversationStage.CONTACTS,
            ConversationStage.BUDGET,
            ConversationStage.COMPLETED
        ]
        
        try:
            current_index = stage_flow.index(current_stage)
            
            if current_stage == ConversationStage.BUDGET:
                return ConversationStage.COMPLETED, ""
            
            if current_index + 1 < len(stage_flow):
                next_stage = stage_flow[current_index + 1]
                response = self.prompts.STAGE_QUESTIONS.get(next_stage.value, "")
                return next_stage, response
            else:
                return ConversationStage.COMPLETED, ""
                
        except (ValueError, IndexError):
            return ConversationStage.COMPLETED, ""
    
    def get_initial_message(self) -> str:
        """Get initial greeting message"""
        return self.prompts.STAGE_QUESTIONS["initial"]
    
    def get_stage_question(self, stage: ConversationStage) -> str:
        """Get question for specific stage"""
        return self.prompts.STAGE_QUESTIONS.get(stage.value, "")
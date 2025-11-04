import logging
from typing import Dict, Any, Optional
from app.services.gemini_service import GeminiService
from app.models.sow_models import (
    SessionData, ConversationStage, ProjectInfo, Service,
    Deliverable, Resource, Contact, Milestone, ProjectTimeline, SOWContext
)
from app.utils.prompts import PromptTemplates
from datetime import datetime

logger = logging.getLogger(__name__)

class DataCollectorAgent:
    """Agent responsible for collecting data through conversation"""
    
    def __init__(self):
        self.gemini_service = GeminiService()
        self.prompts = PromptTemplates()
    
    async def process_user_input(
        self,
        session_data: SessionData,
        user_message: str
    ) -> tuple[str, SessionData]:
        """Process user input and extract data"""
        current_stage = session_data.current_stage
        
        # Extract structured data from user message
        extracted_data = await self.gemini_service.extract_structured_data(
            user_message,
            current_stage.value
        )
        
        if not extracted_data:
            # If extraction failed, ask for clarification
            return ("I'm having trouble understanding that. Could you please rephrase or provide the information in a clearer format?", 
                    session_data)
        
        # Update SOW context based on stage
        session_data = self._update_context(session_data, current_stage, extracted_data)
        
        # Determine next stage and generate response
        next_stage, response_message = self._determine_next_stage(session_data, current_stage)
        session_data.current_stage = next_stage
        
        return response_message, session_data
    
    def _update_context(
        self,
        session_data: SessionData,
        stage: ConversationStage,
        extracted_data: Dict[str, Any]
    ) -> SessionData:
        """Update SOW context with extracted data"""
        
        try:
            if stage == ConversationStage.PROJECT_INFO:
                # Handle None values for project info
                if extracted_data.get('objectives') is None:
                    extracted_data['objectives'] = []
                if extracted_data.get('document_number') is None:
                    extracted_data['document_number'] = ""
                if extracted_data.get('project_name') is None:
                    extracted_data['project_name'] = ""
                
                session_data.sow_context.project_info = ProjectInfo(**extracted_data)
            
            elif stage == ConversationStage.SERVICES:
                services = [Service(**svc) for svc in extracted_data.get("services", [])]
                session_data.sow_context.services.extend(services)
            
            elif stage == ConversationStage.DELIVERABLES:
                deliverables_data = extracted_data.get("deliverables", [])
                for idx, deliv_data in enumerate(deliverables_data, start=len(session_data.sow_context.deliverables) + 1):
                    deliv_data["id"] = idx
                    deliverable = Deliverable(**deliv_data)
                    session_data.sow_context.deliverables.append(deliverable)
            
            elif stage == ConversationStage.TIMELINE:
                # Handle None dates safely
                start_date_str = extracted_data.get("start_date")
                end_date_str = extracted_data.get("end_date")
                
                start_date = None
                end_date = None
                
                # Parse start date
                if start_date_str and start_date_str != "None":
                    try:
                        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                    except:
                        try:
                            start_date = datetime.strptime(start_date_str, "%m/%d/%Y").date()
                        except:
                            logger.warning(f"Could not parse start date: {start_date_str}")
                
                # Parse end date
                if end_date_str and end_date_str != "None":
                    try:
                        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                    except:
                        try:
                            end_date = datetime.strptime(end_date_str, "%m/%d/%Y").date()
                        except:
                            logger.warning(f"Could not parse end date: {end_date_str}")
                
                timeline = ProjectTimeline(
                    start_date=start_date,
                    end_date=end_date,
                    total_sprints=extracted_data.get("total_sprints") or 0,
                    sprint_duration=extracted_data.get("sprint_duration") or "2 weeks"
                )
                session_data.sow_context.timeline = timeline
            
            elif stage == ConversationStage.RESOURCES:
                resources = [Resource(**res) for res in extracted_data.get("resources", [])]
                session_data.sow_context.resources.extend(resources)
            
            elif stage == ConversationStage.CONTACTS:
                # Handle contractor contact with None filtering
                if "contractor_contact" in extracted_data and extracted_data["contractor_contact"]:
                    contractor_data = {
                        k: v if v is not None else "" 
                        for k, v in extracted_data["contractor_contact"].items()
                    }
                    session_data.sow_context.contractor_contact = Contact(**contractor_data)
                
                # Handle client contact with None filtering
                if "client_contact" in extracted_data and extracted_data["client_contact"]:
                    client_data = {
                        k: v if v is not None else "" 
                        for k, v in extracted_data["client_contact"].items()
                    }
                    session_data.sow_context.client_contact = Contact(**client_data)
            
            elif stage == ConversationStage.BUDGET:
                milestones_data = extracted_data.get("milestones", [])
                for idx, mile_data in enumerate(milestones_data, start=1):
                    mile_data["id"] = idx
                    milestone = Milestone(**mile_data)
                    session_data.sow_context.milestones.append(milestone)
                
                session_data.sow_context.estimated_expenses = extracted_data.get("estimated_expenses", 0.0)
                session_data.sow_context.calculate_total_fee()
            
            logger.info(f"Context updated for stage: {stage.value}")
            
        except Exception as e:
            logger.error(f"Error updating context for stage {stage.value}: {e}")
            logger.error(f"Extracted data was: {extracted_data}")
        
        return session_data
    
    def _determine_next_stage(
        self,
        session_data: SessionData,
        current_stage: ConversationStage
    ) -> tuple[ConversationStage, str]:
        """Determine next conversation stage and generate appropriate message"""
        
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
            
            # Check if we're at the budget stage (last data collection stage)
            if current_stage == ConversationStage.BUDGET:
                next_stage = ConversationStage.COMPLETED
                response = """Perfect! I've collected all the necessary information for your Statement of Work.

**Summary of Information Collected:**
- Project Information ✓
- Services ✓
- Deliverables ✓
- Timeline ✓
- Resources ✓
- Contact Information ✓
- Budget & Milestones ✓

Your SOW document is ready to be generated. You can now request document generation to create your final SOW document."""
                return next_stage, response
            
            # Move to next stage
            if current_index + 1 < len(stage_flow):
                next_stage = stage_flow[current_index + 1]
                
                if next_stage == ConversationStage.COMPLETED:
                    response = """Perfect! I've collected all the necessary information for your Statement of Work.

**Summary of Information Collected:**
- Project Information ✓
- Services ✓
- Deliverables ✓
- Timeline ✓
- Resources ✓
- Contact Information ✓
- Budget & Milestones ✓

Your SOW document is ready to be generated."""
                    return next_stage, response
                else:
                    # Get question for next stage
                    response = self.prompts.STAGE_QUESTIONS.get(next_stage.value, "Let's continue...")
                    return next_stage, response
            else:
                return ConversationStage.COMPLETED, "Data collection complete!"
                
        except (ValueError, IndexError):
            return ConversationStage.COMPLETED, "Data collection complete!"
    
    def get_initial_message(self) -> str:
        """Get initial greeting message"""
        return self.prompts.STAGE_QUESTIONS["initial"]
    
    def get_stage_question(self, stage: ConversationStage) -> str:
        """Get question for specific stage"""
        return self.prompts.STAGE_QUESTIONS.get(stage.value, "Please provide the required information.")

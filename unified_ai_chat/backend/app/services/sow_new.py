"""New improved SOW service for unified chat integration."""
from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..config import get_settings
from ..models.chat import SessionState

# Import the new SOW components
from ..sow_components.agents.data_collector_v2 import DataCollectorAgentV2
from ..sow_components.services.contacts_service import ContactsService
from ..sow_components.services.document_service import DocumentService
from ..sow_components.services.state_service import state_service
from ..sow_components.models.sow_models import (
    SessionData, ConversationStage, SOWContext, ProjectInfo,
    Service, Deliverable, Resource, Contact, Milestone, ProjectTimeline
)
from ..sow_components.utils.helpers import generate_session_id
from ..sow_components.services.standard_services import STANDARD_SERVICES

logger = logging.getLogger(__name__)

class NewSOWAdapter:
    """New improved SOW adapter for unified chat."""
    
    def __init__(self):
        self._settings = get_settings()
        self.data_collector = DataCollectorAgentV2()
        self.contacts_service = ContactsService()
        self.document_service = DocumentService()
        self.state_service = state_service
        
    def start_session(self, session: SessionState, project_overview: str) -> Dict[str, Any]:
        """Start new SOW session with improved conversation flow."""
        try:
            # Initialize SOW session data
            sow_session_id = generate_session_id()
            
            # Create session data
            session_data = SessionData(
                session_id=sow_session_id,
                template_id="default",
                template_path=str(self._settings.sow_default_template),
                current_stage=ConversationStage.INITIAL
            )
            
            # Store the session data
            self.state_service.sessions[sow_session_id] = session_data
            
            # Store reference in unified chat session
            session.sow_session_id = sow_session_id
            session.active_domain = "sow"
            
            # Get initial question
            initial_message = self.data_collector.get_stage_question(ConversationStage.PROJECT_INFO)
            
            return {
                "success": True,
                "message": f"Great! Let's create your Statement of Work document.\n\n{initial_message}",
                "next_step": ConversationStage.PROJECT_INFO.value,
                "sow_session_id": sow_session_id
            }
            
        except Exception as e:
            logger.error(f"Error starting SOW session: {e}")
            return {
                "success": False,
                "message": "Failed to start SOW session. Please try again.",
                "error": str(e)
            }
    
    async def update_section(self, session: SessionState, section: str, content: str) -> Dict[str, Any]:
        """Update SOW section with new conversation-based approach."""
        try:
            if not hasattr(session, 'sow_session_id') or not session.sow_session_id:
                return {
                    "success": False,
                    "message": "No active SOW session. Please start a new SOW generation."
                }
            
            # Get SOW session data
            session_data = self.state_service.sessions.get(session.sow_session_id)
            if not session_data:
                return {
                    "success": False,
                    "message": "SOW session not found. Please start a new SOW generation."
                }
            
            # Process the user input through the conversation flow - FIXED: Proper async/await
            bot_message, updated_session_data = await self.data_collector.process_user_input(session_data, content)
            
            # Update session data
            self.state_service.sessions[session.sow_session_id] = updated_session_data
            
            # Check if we need special handling for services stage
            if updated_session_data.current_stage == ConversationStage.SERVICES:
                content_lower = content.strip().lower()
                if content_lower not in ["standard", "custom"]:
                    # User is providing custom services, show options
                    return {
                        "success": True,
                        "message": """You have two options for services:

**Standard Service Package** (Recommended)
- Comprehensive data extraction, compression, and transfer implementation
- Includes all design, development, testing, and go-live activities
- 15 detailed scope items pre-defined

**Custom Services**
- Define your own specific services
- Full control over service descriptions and timelines

Please choose:""",
                        "next_step": updated_session_data.current_stage.value,
                        "show_service_buttons": True
                    }
            
            # Check if we need contact lookup
            if updated_session_data.current_stage == ConversationStage.CONTACTS:
                # Check if user mentioned a company name that might be in our database
                available_clients = list(self.contacts_service.data["clients"].keys())
                available_contractors = list(self.contacts_service.data["contractors"].keys())
                
                return {
                    "success": True,
                    "message": f"""{bot_message}

**Available Registered Companies:**

**Clients:** {', '.join(available_clients)}
**Contractors:** {', '.join(available_contractors)}

You can simply mention a company name from the list above, or provide complete contact details manually.""",
                    "next_step": updated_session_data.current_stage.value,
                    "available_clients": available_clients,
                    "available_contractors": available_contractors
                }
            
            # Check if completed
            if updated_session_data.current_stage == ConversationStage.COMPLETED:
                return {
                    "success": True,
                    "message": bot_message,
                    "next_step": updated_session_data.current_stage.value,
                    "is_completed": True,
                    "can_generate": True
                }
            
            return {
                "success": True,
                "message": bot_message,
                "next_step": updated_session_data.current_stage.value
            }
            
        except Exception as e:
            logger.error(f"Error updating SOW section: {e}")
            return {
                "success": False,
                "message": f"Error processing your input: {str(e)}"
            }
    
    async def handle_service_selection(self, session: SessionState, service_type: str) -> Dict[str, Any]:
        """Handle standard/custom service selection."""
        try:
            if not hasattr(session, 'sow_session_id') or not session.sow_session_id:
                return {"success": False, "message": "No active SOW session."}
            
            session_data = self.state_service.sessions.get(session.sow_session_id)
            if not session_data:
                return {"success": False, "message": "SOW session not found."}
            
            if service_type.lower() == "standard":
                # Process standard services - FIXED: Proper async/await
                bot_message, updated_session_data = await self.data_collector.process_user_input(session_data, "standard")
                
                # Update session data
                self.state_service.sessions[session.sow_session_id] = updated_session_data
                
                return {
                    "success": True,
                    "message": bot_message,
                    "next_step": updated_session_data.current_stage.value
                }
            else:
                # Custom services - ask for details
                return {
                    "success": True,
                    "message": """Great! Please provide your custom services.

For each service, specify:
- Service name
- Description of what will be done  
- Duration or timeline (e.g., "3 weeks", "2 months")

You can list multiple services at once.""",
                    "next_step": ConversationStage.SERVICES.value
                }
                
        except Exception as e:
            logger.error(f"Error handling service selection: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    async def finalize(self, session: SessionState) -> Dict[str, Any]:
        """Generate final SOW document."""
        try:
            if not hasattr(session, 'sow_session_id') or not session.sow_session_id:
                return {"success": False, "message": "No active SOW session."}
            
            session_data = self.state_service.sessions.get(session.sow_session_id)
            if not session_data:
                return {"success": False, "message": "SOW session not found."}
            
            if session_data.current_stage != ConversationStage.COMPLETED:
                return {
                    "success": False,
                    "message": "Cannot generate document yet. Please complete all required information first."
                }
            
            # Generate document
            output_path = self.document_service.generate_document(
                template_path=session_data.template_path,
                sow_context=session_data.sow_context
            )
            
            # Move to unified chat output directory
            target_dir = self._settings.sow_output_dir / session.session_id
            target_dir.mkdir(parents=True, exist_ok=True)
            
            filename = os.path.basename(output_path)
            target_path = target_dir / filename
            shutil.move(output_path, target_path)
            
            return {
                "success": True,
                "message": "Your SOW document has been generated successfully!",
                "download_path": filename
            }
            
        except Exception as e:
            logger.error(f"Error finalizing SOW: {e}")
            return {"success": False, "message": f"Error generating document: {str(e)}"}
    
    def get_session_progress(self, session: SessionState) -> Dict[str, Any]:
        """Get current session progress."""
        try:
            if not hasattr(session, 'sow_session_id') or not session.sow_session_id:
                return {"progress": 0, "stage": "not_started"}
            
            session_data = self.state_service.sessions.get(session.sow_session_id)
            if not session_data:
                return {"progress": 0, "stage": "not_started"}
            
            # Calculate progress
            stage_progress = {
                ConversationStage.INITIAL: 0,
                ConversationStage.PROJECT_INFO: 12.5,
                ConversationStage.SERVICES: 25.0,
                ConversationStage.DELIVERABLES: 37.5,
                ConversationStage.TIMELINE: 50.0,
                ConversationStage.RESOURCES: 62.5,
                ConversationStage.CONTACTS: 75.0,
                ConversationStage.BUDGET: 87.5,
                ConversationStage.COMPLETED: 100.0
            }
            
            progress = stage_progress.get(session_data.current_stage, 0)
            
            return {
                "progress": progress,
                "stage": session_data.current_stage.value,
                "is_completed": session_data.current_stage == ConversationStage.COMPLETED
            }
            
        except Exception as e:
            logger.error(f"Error getting session progress: {e}")
            return {"progress": 0, "stage": "error"}

# Create adapter instance
new_sow_adapter = NewSOWAdapter()
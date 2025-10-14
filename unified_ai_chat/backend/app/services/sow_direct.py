"""Intelligent SOW conversation system using AI to gather comprehensive business requirements."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, List
from datetime import datetime
import json
import os
from pathlib import Path
import asyncio

from ..config import get_settings
from ..models.chat import SessionState, ConfirmationButton
# Removed GeminiClient - no AI during data collection

logger = logging.getLogger(__name__)

class IntelligentSOWAdapter:
    """AI-powered SOW conversation system that intelligently gathers business requirements."""
    
    def __init__(self):
        self._settings = get_settings()
        # No AI client needed - direct storage only
        
        # Load contacts data
        contacts_path = Path(__file__).parent.parent / "sow_components" / "contacts_data.json"
        if contacts_path.exists():
            with open(contacts_path, 'r') as f:
                self.contacts_data = json.load(f)
        else:
            self.contacts_data = {"clients": {}, "contractors": {}}
        
        # Conversation stages with intelligent questions
        self.conversation_stages = [
            {
                "stage": "project_info",
                "question": """Hello! I'll help you create a comprehensive Statement of Work document.

Let's start with the project basics. Please provide:
1. **Document Number** (e.g., SOW-2025-001)
2. **Project Name** 
3. **Key project objectives** (what are you trying to achieve?)

You can provide all information at once or we can go step by step.""",
                "system_context": "Extract project information including document number, project name, and objectives from user response."
            },
            {
                "stage": "services",
                "question": """Excellent! Now, tell me about the **services** that will be provided under this SOW.

You have two options:
- Type **'standard'** for our comprehensive standard service package (design, development, testing, deployment)
- Type **'custom'** to describe your specific service requirements

For custom services, please specify:
- What services will be provided?
- What work will be performed?
- Any specific methodologies or approaches?""",
                "system_context": "Handle service selection - either standard package or custom services with detailed descriptions."
            },
            {
                "stage": "deliverables",
                "question": """Perfect! Now let's define the specific **deliverables** - the tangible outputs of this project.

For each deliverable, please provide:
- **Deliverable name** (e.g., "Web Application", "API Documentation")
- **Detailed description** of what will be delivered
- **Acceptance criteria** (how will you know it's complete?)

What are all the deliverables for this project?""",
                "system_context": "Extract deliverables with names, descriptions, and any mentioned acceptance criteria or requirements."
            },
            {
                "stage": "timeline",
                "question": """Great! Now for the **project timeline and schedule**.

Please provide:
1. **Project start date** (YYYY-MM-DD format preferred)
2. **Project end date** 
3. **Number of sprints** or phases planned
4. **Sprint duration** (default is 2 weeks if not specified)
5. Any **key milestones** or deadlines

What's your timeline for this project?""",
                "system_context": "Extract timeline information including start/end dates, sprint details, and any key milestones."
            },
            {
                "stage": "resources",
                "question": """Now let's document the **resources and team allocation** for this project.

For each resource type, please specify:
- **Role/Position** (e.g., "Senior Developer", "QA Engineer", "Project Manager")
- **Team/Department** (e.g., "Development", "Testing", "DevOps")
- **Number of people** in each role
- **Allocation** (Full-time, Part-time, percentage like "50%")

What resources will be allocated to this project?""",
                "system_context": "Extract resource allocations including roles, teams, headcount, and time allocation percentages."
            },
            {
                "stage": "contacts",
                "question": """Excellent! Now I need **contact information** for both parties involved in this SOW.

**Quick Option:** If you're working with a registered company, just provide the company name and I'll auto-fill the details.

**Manual Option:** Please provide complete contact information for:

**Contractor Representative:**
- Name, Company, Address, Phone, Email, Role/Title

**Client Representative:**  
- Name, Company, Address, Phone, Email, Role/Title

Who are the key contacts for this project?""",
                "system_context": "Extract contact information for both contractor and client representatives, including all business contact details."
            },
            {
                "stage": "budget",
                "question": """Finally, let's document the **financial details and payment structure**.

Please provide:
- **Milestone payments** (milestone name and fee amount)
- **Total project value**
- **Payment schedule** (when payments are due)
- **Estimated expenses** (if any)
- **Currency** (USD assumed if not specified)
- **Payment terms** (Net 30, etc.)

What's the budget and payment structure for this project?""",
                "system_context": "Extract financial information including milestones, fees, payment terms, and any estimated expenses."
            }
        ]
        
    def start_session(self, session: SessionState, project_overview: str) -> Dict[str, Any]:
        """Start intelligent SOW conversation session."""
        try:
            # Initialize session
            session.sow_session_id = f"sow_{int(datetime.now().timestamp())}"
            session.active_domain = "sow"
            
            # Initialize data storage
            if not hasattr(session, 'metadata'):
                session.metadata = {}
                
            session.metadata['sow_data'] = {
                'current_stage_index': 0,
                'total_stages': len(self.conversation_stages),
                'conversation_history': [],
                'extracted_data': {},
                'created_at': datetime.now().isoformat()
            }
            
            # Return first question
            first_stage = self.conversation_stages[0]
            return {
                "success": True,
                "message": first_stage['question'],
                "stage": first_stage['stage'],
                "stage_progress": f"1/{len(self.conversation_stages)}"
            }
            
        except Exception as e:
            logger.error(f"Error starting SOW session: {e}")
            return {"success": False, "message": f"Error starting SOW session: {str(e)}"}
    
    async def process_user_input(self, session: SessionState, user_message: str) -> Dict[str, Any]:
        """Process user input - DIRECT storage, NO AI processing during data collection."""
        try:
            sow_data = session.metadata.get('sow_data', {})
            current_index = sow_data.get('current_stage_index', 0)
            current_stage = self.conversation_stages[current_index]
            
            # Store conversation - NO AI PROCESSING
            sow_data['conversation_history'].append({
                'stage': current_stage['stage'],
                'question': current_stage['question'],
                'user_response': user_message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Handle special cases for services
            if current_stage['stage'] == 'services':
                if user_message.lower().strip() == 'standard':
                    return await self._handle_standard_services(session, sow_data)
                elif user_message.lower().strip() == 'custom':
                    return {
                        "success": True,
                        "message": """Great! Please provide your custom services.

For each service, specify:
- **Service name**
- **Description** of what will be done  
- **Duration** or timeline (e.g., "3 weeks", "2 months")

You can list multiple services at once.""",
                        "stage": current_stage['stage'],
                        "awaiting_custom_input": True
                    }
            
            # DIRECT STORAGE - Accept whatever user provides, NO validation
            sow_data['extracted_data'][current_stage['stage']] = {
                'raw_input': user_message,
                'timestamp': datetime.now().isoformat()
            }
            
            # Always move to next stage - NO AI validation
            return await self._advance_to_next_stage(session, sow_data, current_index)
                
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            return {"success": False, "message": f"Error processing input: {str(e)}"}
    
    async def _handle_standard_services(self, session: SessionState, sow_data: Dict) -> Dict[str, Any]:
        """Handle standard services selection."""
        # Store standard services data
        sow_data['extracted_data']['services'] = {
            "type": "standard",
            "services": [{
                "name": "Design and Development / Test / Post-Go-live support for Data Extraction, Compression, and Transfer Implementation",
                "description": "Comprehensive service package including all design, development, testing, and go-live activities with 15 detailed scope items covering data extraction, compression, transfer implementation, security, monitoring, and post-deployment support.",
                "duration": "As per project timeline"
            }]
        }
        
        # Move to next stage
        current_index = sow_data.get('current_stage_index', 0)
        return await self._advance_to_next_stage(session, sow_data, current_index)
    
    # REMOVED - No AI extraction during data collection
    
    # REMOVED - No schemas needed for direct storage
    
    async def _advance_to_next_stage(self, session: SessionState, sow_data: Dict, current_index: int) -> Dict[str, Any]:
        """Advance to next conversation stage."""
        next_index = current_index + 1
        
        if next_index < len(self.conversation_stages):
            # Move to next stage
            next_stage = self.conversation_stages[next_index]
            sow_data['current_stage_index'] = next_index
            
            current_stage_name = self.conversation_stages[current_index]['stage']
            
            return {
                "success": True,
                "message": f"✅ **{current_stage_name.replace('_', ' ').title()} captured!**\n\n{next_stage['question']}",
                "stage": next_stage['stage'],
                "stage_progress": f"{next_index + 1}/{len(self.conversation_stages)}"
            }
        else:
            # All stages completed - process with AI
            return await self._finalize_sow_data(session, sow_data)
    
    async def _finalize_sow_data(self, session: SessionState, sow_data: Dict) -> Dict[str, Any]:
        """Process all collected data and generate SOW document."""
        try:
            # Build complete conversation for AI processing
            conversation_text = self._build_conversation_text(sow_data['conversation_history'])
            
            # Use the new_sow system for final processing
            success = await self._process_with_new_sow_system(session, conversation_text)
            
            if success:
                return {
                    "success": True,
                    "message": """🎉 **Your Statement of Work is ready!**

**Summary of Information Collected:**
✓ Project Information & Objectives
✓ Services & Scope of Work  
✓ Deliverables & Acceptance Criteria
✓ Timeline & Sprint Planning
✓ Resource Allocation
✓ Contact Information
✓ Budget & Payment Terms

Your professional SOW document has been generated and is ready for download!""",
                    "stage": "completed",
                    "can_generate": True
                }
            else:
                return {
                    "success": False,
                    "message": "There was an issue processing your SOW data. Please try again or contact support."
                }
                
        except Exception as e:
            logger.error(f"Error finalizing SOW: {e}")
            return {
                "success": False,
                "message": f"Error generating SOW: {str(e)}"
            }
    
    def _build_conversation_text(self, conversation_history: List[Dict]) -> str:
        """Build conversation text for AI processing."""
        conversation_parts = []
        
        for entry in conversation_history:
            conversation_parts.append(f"""
**Stage: {entry['stage'].upper()}**
Question: {entry['question']}
User Response: {entry['user_response']}
""")
        
        return "\n".join(conversation_parts)
    
    async def _process_with_new_sow_system(self, session: SessionState, conversation_text: str) -> bool:
        """Process conversation with the new_sow system."""
        try:
            # Import new_sow components
            import sys
            new_sow_path = str(Path(__file__).parent.parent.parent.parent / "new_sow")
            if new_sow_path not in sys.path:
                sys.path.insert(0, new_sow_path)
            
            from app.agents.data_collector_v2 import DataCollectorAgentV2
            from app.services.document_service import DocumentService
            from app.services.state_service import state_service
            from app.models.sow_models import SessionData, ConversationStage
            
            # Create session data for new_sow
            session_data = SessionData(
                session_id=session.sow_session_id,
                template_path=str(self._settings.sow_default_template),
                current_stage=ConversationStage.COMPLETED
            )
            
            # Convert conversation to raw responses format
            session_data.raw_responses = {}
            sow_data = session.metadata.get('sow_data', {})
            
            for entry in sow_data.get('conversation_history', []):
                stage = entry['stage']
                response = entry['user_response']
                session_data.raw_responses[stage] = response
            
            # Store in state service
            state_service.sessions[session.sow_session_id] = session_data
            
            # Process with data collector
            data_collector = DataCollectorAgentV2()
            success = await data_collector._extract_all_data_with_function_calling(session_data)
            
            if success:
                # Generate document
                doc_service = DocumentService()
                output_path = doc_service.generate_document(
                    template_path=session_data.template_path,
                    sow_context=session_data.sow_context
                )
                
                # Move to unified chat output directory
                target_dir = self._settings.sow_output_dir / session.session_id
                target_dir.mkdir(parents=True, exist_ok=True)
                
                filename = os.path.basename(output_path)
                target_path = target_dir / filename
                
                import shutil
                shutil.copy2(output_path, target_path)
                
                logger.info(f"SOW document generated: {target_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error processing with new_sow system: {e}")
            return False
    
    # Legacy methods for compatibility
    def update_section(self, session: SessionState, section: str, content: str) -> Dict[str, Any]:
        """Legacy method - redirect to process_user_input."""
        return asyncio.run(self.process_user_input(session, content))
    
    def finalize(self, session: SessionState) -> Dict[str, Any]:
        """Legacy method for document generation."""
        try:
            sow_data = session.metadata.get('sow_data', {})
            
            # Check if already completed
            if sow_data.get('current_stage_index', 0) >= len(self.conversation_stages):
                # Generate document
                target_dir = self._settings.sow_output_dir / session.session_id
                target_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"SOW_Document_{timestamp}.docx"
                target_path = target_dir / filename
                
                # Create simple document as fallback
                self._create_simple_document(sow_data.get('extracted_data', {}), target_path)
                
                return {
                    "success": True,
                    "message": "✅ Your SOW document has been generated successfully!",
                    "download_path": filename
                }
            else:
                return {
                    "success": False,
                    "message": "SOW conversation is not yet complete. Please continue answering the questions."
                }
                
        except Exception as e:
            logger.error(f"Error in finalize: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def _create_simple_document(self, extracted_data: Dict[str, Any], output_path: Path):
        """Create a simple document with extracted data."""
        try:
            from docx import Document
            
            doc = Document()
            doc.add_heading('Statement of Work', 0)
            
            # Add extracted data
            for stage, data in extracted_data.items():
                doc.add_heading(stage.replace('_', ' ').title(), level=1)
                if isinstance(data, dict):
                    for key, value in data.items():
                        doc.add_paragraph(f"{key}: {value}")
                else:
                    doc.add_paragraph(str(data))
            
            doc.save(str(output_path))
            logger.info(f"Simple SOW document created: {output_path}")
            
        except Exception as e:
            logger.error(f"Error creating simple document: {e}")
            output_path.touch()

# Create adapter instance
intelligent_sow_adapter = IntelligentSOWAdapter()
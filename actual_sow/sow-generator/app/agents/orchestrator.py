import logging
from typing import Dict, Any
from app.agents.data_collector_v2 import DataCollectorAgentV2  # ✓ Changed import
from app.services.state_service import state_service
from app.services.document_service import DocumentService
from app.models.sow_models import SessionData, ConversationStage, BotResponse
from app.utils.helpers import calculate_progress, log_conversation

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """Main orchestrator agent coordinating all other agents"""
    
    def __init__(self):
        self.data_collector = DataCollectorAgentV2()  # ✓ Use V2
        self.state_service = state_service
        self.document_service = DocumentService()
    
    async def handle_message(
        self,
        session_id: str,
        user_message: str
    ) -> BotResponse:
        """Handle incoming user message and coordinate response"""
        
        # Log conversation
        log_conversation(session_id, "user", user_message)
        
        # Get session data
        session_data = self.state_service.get_session(session_id)
        
        if not session_data:
            return BotResponse(
                message="Session not found or expired. Please start a new conversation.",
                stage=ConversationStage.INITIAL,
                progress=0.0,
                is_complete=False,
                requires_input=True
            )
        
        # Add user message to history
        self.state_service.add_message(session_id, "user", user_message)
        
        # Check current stage
        current_stage = session_data.current_stage
        
        if current_stage == ConversationStage.INITIAL:
            # Transition to PROJECT_INFO stage
            session_data.current_stage = ConversationStage.PROJECT_INFO
            self.state_service.update_session(session_id, session_data)
            
            bot_message = self.data_collector.get_stage_question(ConversationStage.PROJECT_INFO)
            
        elif current_stage == ConversationStage.COMPLETED:
            # Handle post-completion messages
            bot_message = "Your information has been collected. You can now generate the document."
        
        else:
            # Process user input (stores response and advances stage)
            bot_message, session_data = await self.data_collector.process_user_input(
                session_data,
                user_message
            )
            
            # Update session
            self.state_service.update_session(session_id, session_data)
        
        # Add bot response to history
        self.state_service.add_message(session_id, "assistant", bot_message)
        
        # Log bot response
        log_conversation(session_id, "assistant", bot_message)
        
        # Calculate progress
        progress = calculate_progress(session_data.current_stage.value)
        
        # Create response
        response = BotResponse(
            message=bot_message,
            stage=session_data.current_stage,
            progress=progress,
            is_complete=(session_data.current_stage == ConversationStage.COMPLETED),
            requires_input=(session_data.current_stage != ConversationStage.COMPLETED)
        )
        
        return response
    
    async def generate_document(self, session_id: str) -> str:
        """Generate final SOW document"""
        session_data = self.state_service.get_session(session_id)
        
        if not session_data:
            raise ValueError("Session not found")
        
        if session_data.current_stage != ConversationStage.COMPLETED:
            raise ValueError("Cannot generate document - data collection not complete")
        
        if not session_data.template_path:
            raise ValueError("No template associated with this session")
        
        # Generate document
        output_path = self.document_service.generate_document(
            template_path=session_data.template_path,
            sow_context=session_data.sow_context
        )
        
        logger.info(f"Document generated for session {session_id}: {output_path}")
        return output_path
    
    def initialize_session(
        self,
        session_id: str,
        template_id: str = None,
        template_path: str = None
    ) -> SessionData:
        """Initialize new session"""
        session = self.state_service.create_session(session_id, template_id, template_path)
        return session

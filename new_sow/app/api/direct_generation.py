"""
Direct generation endpoint for new_sow
Allows external applications to generate SOW documents without WebSocket
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from app.agents.orchestrator import OrchestratorAgent
from app.services.state_service import state_service
from app.models.sow_models import ConversationStage

logger = logging.getLogger(__name__)

router = APIRouter()

class DirectGenerationRequest(BaseModel):
    """Request model for direct SOW generation"""
    template_path: str
    project_data: Dict[str, Any]
    session_id: str

@router.post("/generate-direct")
async def generate_direct(request: DirectGenerationRequest):
    """
    Generate SOW document directly from collected data
    This endpoint mimics the conversation flow but processes all data at once
    """
    try:
        logger.info(f"📥 Direct generation request for session: {request.session_id}")
        
        # Create session
        orchestrator = OrchestratorAgent()
        session = orchestrator.initialize_session(
            session_id=request.session_id,
            template_id="direct_gen",
            template_path=request.template_path
        )
        
        # Process data through conversation stages to trigger special handling (e.g., standard services)
        project_data = request.project_data
        
        # Define stage order
        stages = [
            ("project_info", ConversationStage.PROJECT_INFO),
            ("services", ConversationStage.SERVICES),
            ("deliverables", ConversationStage.DELIVERABLES),
            ("timeline", ConversationStage.TIMELINE),
            ("resources", ConversationStage.RESOURCES),
            ("contacts", ConversationStage.CONTACTS),
            ("budget", ConversationStage.BUDGET)
        ]
        
        # Process each stage through the data collector to trigger special logic
        logger.info("🔄 Processing data through conversation stages...")
        for data_key, stage in stages:
            user_input = project_data.get(data_key, "")
            if user_input:
                session.current_stage = stage
                logger.info(f"   Processing stage: {stage.value} with input: {user_input[:50]}...")
                
                # Process through data collector (this triggers standard services detection)
                _, session = await orchestrator.data_collector.process_user_input(
                    session,
                    user_input
                )
        
        # After all stages, session should be at COMPLETED
        logger.info(f"✅ All stages processed. Current stage: {session.current_stage.value}")
        
        # Verify we reached COMPLETED stage
        if session.current_stage != ConversationStage.COMPLETED:
            logger.warning(f"⚠️ Expected COMPLETED stage but got {session.current_stage.value}")
            # Force completion if needed
            session.current_stage = ConversationStage.COMPLETED
            success = await orchestrator.data_collector._extract_all_data_with_function_calling(session)
        else:
            # Data extraction already happened in process_user_input
            success = session.is_completed
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Data extraction failed"
            )
        
        session.is_completed = True
        state_service.update_session(request.session_id, session)
        
        # Generate document
        logger.info("📄 Generating document...")
        output_path = await orchestrator.generate_document(request.session_id)
        
        import os
        filename = os.path.basename(output_path)
        
        logger.info(f"✅ Document generated: {filename}")
        
        return {
            "success": True,
            "session_id": request.session_id,
            "filename": filename,
            "download_url": f"/api/download/{request.session_id}",
            "message": "SOW document generated successfully via direct API"
        }
        
    except Exception as e:
        logger.error(f"❌ Direct generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Direct generation failed: {str(e)}"
        )

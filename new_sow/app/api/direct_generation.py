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
        
        # Store raw responses in the format expected by data collector
        project_data = request.project_data
        
        session.raw_responses = {
            "project_info": project_data.get("project_info", ""),
            "services": project_data.get("services", ""),
            "deliverables": project_data.get("deliverables", ""),
            "timeline": project_data.get("timeline", ""),
            "resources": project_data.get("resources", ""),
            "contacts": project_data.get("contacts", ""),
            "budget": project_data.get("budget", "")
        }
        
        # Mark as completed to trigger data extraction
        session.current_stage = ConversationStage.COMPLETED
        
        # Extract and process data using Gemini
        logger.info("🤖 Extracting data with Gemini AI...")
        success = await orchestrator.data_collector._extract_all_data_with_function_calling(session)
        
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

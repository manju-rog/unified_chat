from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
import os
import logging
from app.services.document_service import DocumentService
from app.services.state_service import state_service
from app.agents.orchestrator import OrchestratorAgent
from app.models.sow_models import TemplateUploadResponse
from app.utils.helpers import generate_session_id, log_conversation, validate_file_extension
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
document_service = DocumentService()
orchestrator = OrchestratorAgent()

@router.post("/upload-template", response_model=TemplateUploadResponse)
async def upload_template(file: UploadFile = File(...)):
    """Upload SOW template document"""
    try:
        # Validate file extension
        if not validate_file_extension(file.filename, settings.ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Save template
        template_id, template_path = document_service.save_template(content, file.filename)
        
        # Validate template
        if not document_service.validate_template(template_path):
            os.remove(template_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or corrupted DOCX template"
            )
        
        # Analyze template
        placeholders = document_service.analyze_template(template_path)
        
        logger.info(f"Template uploaded successfully: {template_id}")
        
        return TemplateUploadResponse(
            template_id=template_id,
            filename=file.filename,
            placeholders=placeholders,
            message="Template uploaded and analyzed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload template"
        )

@router.post("/create-session")
async def create_session(template_id: str):
    """Create new conversation session"""
    try:
        # Generate session ID
        session_id = generate_session_id()
        
        # Get template path
        template_files = [f for f in os.listdir(settings.TEMPLATE_DIR) if f.startswith(template_id)]
        if not template_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        template_path = os.path.join(settings.TEMPLATE_DIR, template_files[0])
        
        # Initialize session
        session = orchestrator.initialize_session(session_id, template_id, template_path)
        
        return {
            "session_id": session_id,
            "template_id": template_id,
            "message": "Session created successfully. Connect via WebSocket to start conversation."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )

@router.post("/generate-document/{session_id}")
async def generate_document(session_id: str):
    """Generate SOW document from collected data"""
    try:
        # Generate document
        output_path = await orchestrator.generate_document(session_id)
        
        filename = os.path.basename(output_path)
        
        return {
            "session_id": session_id,
            "filename": filename,
            "download_url": f"/download/{session_id}",
            "message": "Document generated successfully"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate document"
        )

@router.get("/download/{session_id}")
async def download_document(session_id: str):
    """Download generated SOW document"""
    try:
        session_data = state_service.get_session(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # ✓ Fixed - use sow_context.project_info
        output_files = [f for f in os.listdir(settings.OUTPUT_DIR) 
                       if session_data.sow_context.project_info and 
                       session_data.sow_context.project_info.project_name.replace(" ", "_") in f]
        
        if not output_files:
            # Fallback: just get the most recent file for this session
            all_files = sorted(
                [f for f in os.listdir(settings.OUTPUT_DIR) if f.endswith('.docx')],
                key=lambda x: os.path.getmtime(os.path.join(settings.OUTPUT_DIR, x)),
                reverse=True
            )
            
            if not all_files:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found. Please generate document first."
                )
            
            output_path = os.path.join(settings.OUTPUT_DIR, all_files[0])
        else:
            output_path = os.path.join(settings.OUTPUT_DIR, output_files[0])
        
        return FileResponse(
            path=output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=os.path.basename(output_path)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download document"
        )

@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session information and progress"""
    try:
        session_data = state_service.get_session(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        from app.utils.helpers import calculate_progress
        
        return {
            "session_id": session_id,
            "current_stage": session_data.current_stage,
            "progress": calculate_progress(session_data.current_stage.value),
            "is_completed": session_data.is_completed,
            "created_at": session_data.created_at,
            "updated_at": session_data.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session information"
        )

@router.get("/list-models")
async def list_models():
    """Endpoint to list available models"""
    # Here you would typically fetch the models from a database or an external API
    models = ["model_1", "model_2", "model_3"]  # Example models
    session_id = generate_session_id()
    
    # Log the request
    log_conversation(session_id, "user", "Requested list of models")
    
    return {"session_id": session_id, "models": models}
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
import os
import logging
import re
from datetime import datetime, date
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
        # For direct generation, session_data might not exist - that's OK
        session_data = state_service.get_session(session_id)
        logger.info(f"📄 Download request for session: {session_id}, session_data exists: {session_data is not None}")
        
        # For direct generation, session_data might not exist
        # Just get the most recent file for this session or any recent file
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
        
        # Try to find a file that matches the session_id, otherwise use the most recent
        session_file = None
        for file in all_files:
            if session_id in file:
                session_file = file
                break
        
        # If no session-specific file found, use the most recent file
        selected_file = session_file or all_files[0]
        output_path = os.path.join(settings.OUTPUT_DIR, selected_file)
        
        logger.info(f"📄 Serving file: {selected_file} for session: {session_id}")
        
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

@router.post("/generate-direct")
async def generate_direct(payload: dict):
    """
    Direct SOW generation endpoint for unified chat integration
    Bypasses the conversation flow and generates document directly from provided data
    """
    try:
        logger.info("🎯 Direct SOW generation requested from unified chat")
        
        # Extract data from payload
        template_filename = payload.get("template_path", "sample_sow_template.docx")
        project_data = payload.get("project_data", {})
        
        # Robust template search order
        import os
        from pathlib import Path
        
        template_locations = [
            template_filename,  # as-is
            os.path.join("use_sow", template_filename),
            os.path.join(os.getcwd(), template_filename),
            os.path.join(os.path.dirname(__file__), "..", "..", template_filename),
            "sample_sow_template.docx",  # final fallback
        ]
        
        template_path = None
        for location in template_locations:
            if os.path.exists(location):
                template_path = location
                logger.info(f"✅ Found template at: {location}")
                break
        
        if not template_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template not found. Searched: {template_locations}"
            )
        
        # Validate required data
        if not project_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No project data provided"
            )
        
        # Use Unified Chat session if provided; else generate one
        incoming_session_id = (payload or {}).get("session_id")
        session_id = incoming_session_id or generate_session_id()
        
        # Create SOW context from the provided data
        from app.models.sow_models import (
            SOWContext, ProjectInfo, Service, Deliverable, 
            ProjectTimeline, Resource, Contact, Milestone
        )
        from datetime import datetime, date
        
        # Parse project info
        project_info_text = project_data.get("project_info", "")
        project_name = "Professional Services Project"
        objectives = ["To be defined"]
        
        if project_info_text:
            # Try to extract project name and objectives
            lines = project_info_text.split('\n')
            for line in lines:
                if 'project' in line.lower() and 'name' in line.lower():
                    project_name = line.split(':', 1)[-1].strip()
                elif 'objective' in line.lower():
                    objectives = [line.split(':', 1)[-1].strip()]
            
            # If no structured format, use the whole text as project name
            if project_name == "Professional Services Project":
                project_name = project_info_text[:100]  # First 100 chars
        
        project_info = ProjectInfo(
            document_number=f"SOW-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            project_name=project_name,
            objectives=objectives
        )
        
        # Parse services
        services_type = project_data.get("services", "standard")
        services = [Service(
            name=f"{services_type.title()} Package",
            description="Professional services package",
            duration="As per timeline"
        )]
        
        # Parse deliverables
        deliverables_text = project_data.get("deliverables", "")
        deliverables = []
        if deliverables_text:
            deliv_lines = deliverables_text.split('\n')
            for i, line in enumerate(deliv_lines, 1):
                if line.strip():
                    deliverables.append(Deliverable(
                        id=i,
                        name=line.strip(),
                        description=line.strip(),
                        sprint_start=None,
                        sprint_end=None,
                        sprint_duration=None
                    ))
        
        # Parse timeline
        timeline_text = project_data.get("timeline", "")
        start_date = date.today()
        end_date = None
        total_sprints = 0
        sprint_duration = "2 weeks"
        
        if timeline_text:
            # Try to parse dates from timeline text
            import re
            date_matches = re.findall(r'(\d{4}-\d{2}-\d{2})', timeline_text)
            if len(date_matches) >= 2:
                try:
                    start_date = datetime.strptime(date_matches[0], '%Y-%m-%d').date()
                    end_date = datetime.strptime(date_matches[1], '%Y-%m-%d').date()
                except:
                    pass
            
            # Try to parse sprint info
            sprint_matches = re.findall(r'(\d+)\s*sprint', timeline_text.lower())
            if sprint_matches:
                try:
                    total_sprints = int(sprint_matches[0])
                except:
                    pass
        
        timeline = ProjectTimeline(
            start_date=start_date,
            end_date=end_date,
            total_sprints=total_sprints,
            sprint_duration=sprint_duration
        )
        
        # Parse resources
        resources_text = project_data.get("resources", "")
        resources = []
        if resources_text:
            resource_lines = resources_text.split('\\n')
            for line in resource_lines:
                if line.strip():
                    parts = line.split(' - ')
                    if len(parts) >= 2:
                        role = parts[0].strip()
                        count_text = parts[1].strip()
                        count = 1
                        try:
                            count = int(count_text.split()[0])
                        except:
                            pass
                        
                        resources.append(Resource(
                            role=role,
                            team="Development",
                            count=count,
                            allocation="100%"
                        ))
        
        # Parse contacts
        contacts_text = project_data.get("contacts", "")
        contractor_contact = Contact(
            name="Professional Services Inc.",
            company="Professional Services Inc.",
            address="123 Business St, City, State",
            phone="+1-555-0123",
            email="pm@company.com",
            role="Contractor"
        )
        
        client_contact = Contact(
            name="Client Organization",
            company="Client Organization",
            address="456 Client Ave, City, State",
            phone="+1-555-0456",
            email="client@company.com",
            role="Client"
        )
        
        # Parse budget
        budget_text = project_data.get("budget", "")
        milestones = []
        total_fee = 50000.0  # Default
        
        if budget_text:
            try:
                # Try to extract total amount
                import re
                amounts = re.findall(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', budget_text)
                if amounts:
                    total_fee = float(amounts[0].replace(',', ''))
            except:
                pass
            
            milestones.append(Milestone(
                id=1,
                name="Project Completion",
                fee=total_fee,
                description=budget_text[:100]
            ))
        
        # Create SOW context
        sow_context = SOWContext(
            project_info=project_info,
            services=services,
            deliverables=deliverables,
            timeline=timeline,
            resources=resources,
            contractor_contact=contractor_contact,
            client_contact=client_contact,
            milestones=milestones,
            total_fee=total_fee,
            estimated_expenses=0.0,
            assumptions=[
                "Client will provide timely feedback and approvals",
                "All necessary resources and access will be provided",
                "Project scope remains as defined in this SOW"
            ],
            terms=[
                "Changes to scope require written approval",
                "Payment terms are Net 30 days",
                "Intellectual property rights as per master agreement"
            ]
        )
        
        # Block until document generation is complete (including Gemini processing)
        from starlette.concurrency import run_in_threadpool
        import time
        
        def _generate_and_verify():
            """Generate document and ensure it exists before returning"""
            logger.info(f"🤖 Starting Gemini-powered document generation for session {session_id}")
            
            # This should call Gemini and render the doc
            output_path = document_service.generate_document(template_path, sow_context)
            original_filename = os.path.basename(output_path)
            
            # Rename file to include session ID for easier retrieval
            output_dir = os.path.dirname(output_path)
            session_filename = f"{session_id}_{original_filename}"
            session_output_path = os.path.join(output_dir, session_filename)
            
            # Rename the file
            import shutil
            shutil.move(output_path, session_output_path)
            
            # Verify file exists and has content
            if not os.path.isfile(session_output_path):
                raise RuntimeError(f"Document not found after generation: {session_output_path}")
            
            file_size = os.path.getsize(session_output_path)
            if file_size < 1000:  # Sanity check - SOW should be > 1KB
                raise RuntimeError(f"Generated document too small ({file_size} bytes), likely incomplete")
            
            logger.info(f"✅ Document verified: {session_filename} ({file_size} bytes)")
            return session_filename
        
        # Run generation in thread pool but await completion
        filename = await run_in_threadpool(_generate_and_verify)
        
        logger.info(f"✅ Direct SOW generation completed: {filename}")
        
        return {
            "success": True,
            "session_id": session_id,
            "filename": filename,
            "download_url": f"/api/download/{session_id}",
            "message": "SOW document generated successfully via direct API"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Direct SOW generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Direct generation failed: {str(e)}"
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
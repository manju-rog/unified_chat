"""FastAPI main application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional
import uuid
import os

from app.tools_absence import router as absence_router
from app.tools_sow import router as sow_router
from app.models import ChatResponse
from app.orchestrator import orchestrate

app = FastAPI(
    title="Gemini Orchestrator",
    description="AI-powered orchestrator for Absence Management and SOW Generation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(absence_router)
app.include_router(sow_router)

# ============================================================================
# Static File Serving (Subtask 8.3)
# ============================================================================

# Mount /files directory for DOCX downloads
# Ensure /tmp directory exists for generated SOW documents
files_directory = "/tmp"
if not os.path.exists(files_directory):
    os.makedirs(files_directory)

app.mount("/files", StaticFiles(directory=files_directory), name="files")

@app.get("/")
async def root():
    return {"message": "Gemini Orchestrator API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}


# ============================================================================
# Request Models
# ============================================================================

class OrchestratorRequest(BaseModel):
    """
    Request model for the /orchestrator endpoint.
    Requirements: 7.1, 7.5
    """
    text: str = Field(..., description="User message text")
    session_id: Optional[str] = Field(None, description="Optional session identifier")


# ============================================================================
# Orchestrator Endpoint (Subtask 8.2)
# ============================================================================

@app.post("/orchestrator", response_model=ChatResponse)
async def orchestrator_endpoint(request: OrchestratorRequest) -> ChatResponse:
    """
    Main orchestrator endpoint that processes user messages.
    
    Flow:
    1. Generate session_id if not provided
    2. Call orchestrate() function
    3. Return ChatResponse envelope
    
    Requirements: 7.1, 7.5
    
    Args:
        request: OrchestratorRequest with text and optional session_id
        
    Returns:
        ChatResponse: Structured response envelope
    """
    # Generate session_id if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    # Call orchestrate function
    response = await orchestrate(
        user_msg=request.text,
        session_id=session_id
    )
    
    return response

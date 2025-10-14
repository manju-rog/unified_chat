from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
from app.config import settings
from app.api import endpoints
from app.api.websocket import websocket_handler
from app.services.state_service import state_service

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{settings.LOGS_DIR}/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application"""
    logger.info("Starting SOW Generator API...")
    
    # Startup: Cleanup expired sessions
    state_service.cleanup_expired_sessions()
    
    yield
    
    # Shutdown: Cleanup
    logger.info("Shutting down SOW Generator API...")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Statement of Work (SOW) document generation system using agentic AI principles",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API router ONLY
app.include_router(endpoints.router, prefix="/api", tags=["SOW Generation"])


# DO NOT include websocket.router - we register it directly below

# Register WebSocket endpoint directly
@app.websocket("/api/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time conversation"""
    await websocket_handler(websocket, session_id)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "upload_template": "/api/upload-template",
            "create_session": "/api/create-session",
            "websocket": "/api/ws/{session_id}",
            "generate_document": "/api/generate-document/{session_id}",
            "download_document": "/api/download/{session_id}",
            "session_info": "/api/session/{session_id}"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

"""
🚀 ULTIMATE RAG SYSTEM v2.1 - FastAPI Backend
==============================================
Complete REST API for the most advanced free-tier RAG system!
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
import os
import shutil
from pathlib import Path

from .config import get_settings
from .services.rag_chain import UltimateRAGChain
from .models import (
    QueryRequest, QueryResponse,
    UploadDocumentRequest, UploadResponse,
    DocumentInfo, SystemStats, HealthResponse
)

# Initialize settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="The most advanced free-tier RAG system with 30+ file formats support!"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG chain (singleton)
rag_chain: Optional[UltimateRAGChain] = None


@app.on_event("startup")
async def startup_event():
    """Initialize RAG chain on startup"""
    global rag_chain

    print("\n" + "="*80)
    print(f"🚀 {settings.APP_NAME} STARTING UP...")
    print("="*80)

    try:
        rag_chain = UltimateRAGChain(settings)
        print("\n✅ RAG System ready to serve requests!")
        print("="*80 + "\n")
    except Exception as e:
        print(f"\n❌ Error initializing RAG system: {e}")
        print("="*80 + "\n")
        raise


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION,
        "components": {
            "api": "operational",
            "vector_store": "operational",
            "document_processor": "operational",
            "claude_api": "configured" if settings.ANTHROPIC_API_KEY else "not_configured"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return await root()


@app.post("/upload/files", response_model=UploadResponse)
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload and process multiple files
    """
    try:
        # Save uploaded files
        upload_dir = settings.UPLOAD_DIR
        upload_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []

        for file in files:
            # Save file
            file_path = upload_dir / file.filename
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            saved_paths.append(str(file_path))
            print(f"💾 Saved: {file.filename}")

        # Process files
        result = rag_chain.process_documents(file_paths=saved_paths)

        return UploadResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/folder", response_model=UploadResponse)
async def upload_folder(request: UploadDocumentRequest):
    """
    Process all documents in a folder
    """
    try:
        if not request.folder_path:
            raise HTTPException(status_code=400, detail="folder_path required")

        folder_path = Path(request.folder_path)

        if not folder_path.exists():
            raise HTTPException(status_code=404, detail=f"Folder not found: {request.folder_path}")

        # Process folder
        result = rag_chain.process_documents(folder_path=str(folder_path))

        return UploadResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Query the RAG system with a question
    """
    try:
        result = rag_chain.query(
            question=request.question,
            session_id=request.session_id,
            file_filters=request.file_filters,
            date_filter=request.date_filter,
            include_history=request.include_history
        )

        return QueryResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """
    List all indexed documents
    """
    try:
        documents = rag_chain.list_documents()
        return [DocumentInfo(**doc) for doc in documents]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/statistics", response_model=SystemStats)
async def get_statistics():
    """
    Get system statistics
    """
    try:
        stats = rag_chain.get_statistics()
        return SystemStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversation/{session_id}")
async def get_conversation_history(session_id: str):
    """
    Get conversation history for a session
    """
    try:
        history = rag_chain.get_conversation_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """
    Clear conversation history for a session
    """
    try:
        rag_chain.clear_conversation_history(session_id)
        return {"message": f"Cleared history for session: {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversation")
async def clear_all_conversations():
    """
    Clear all conversation history
    """
    try:
        rag_chain.clear_conversation_history()
        return {"message": "Cleared all conversation history"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/vector-store")
async def clear_vector_store():
    """
    Clear all documents from vector store
    WARNING: This deletes all indexed documents!
    """
    try:
        rag_chain.clear_vector_store()
        return {"message": "Cleared vector store"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_config():
    """
    Get current system configuration (safe subset)
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "model": settings.CLAUDE_MODEL,
        "max_context_tokens": settings.MAX_CONTEXT_TOKENS,
        "retrieval": {
            "initial_k": settings.INITIAL_RETRIEVAL_K,
            "rerank_k": settings.RERANK_TOP_K,
            "final_k": settings.FINAL_TOP_K
        },
        "chunking": {
            "parent_size": settings.PARENT_CHUNK_SIZE,
            "child_size": settings.CHILD_CHUNK_SIZE
        },
        "features": {
            "conversation_memory": settings.ENABLE_CONVERSATION_MEMORY,
            "semantic_cache": settings.ENABLE_SEMANTIC_CACHE,
            "reranking": settings.ENABLE_RERANKING,
            "parent_child_chunking": settings.ENABLE_PARENT_CHILD_CHUNKING,
            "advanced_metadata": settings.ENABLE_ADVANCED_METADATA
        },
        "supported_formats": settings.SUPPORTED_FORMATS,
        "total_features_enabled": settings.get_total_features_enabled()
    }


if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*80)
    print(f"🚀 Starting {settings.APP_NAME}")
    print("="*80)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

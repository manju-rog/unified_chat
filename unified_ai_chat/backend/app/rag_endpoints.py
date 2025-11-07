"""
RAG API Endpoints for Document Q&A
Add these to the existing main.py
"""

from fastapi import File, UploadFile, Form
from typing import List, Optional
import shutil
from pathlib import Path

# At the top of main.py, add:
# from .services.rag_chain import UltimateRAGChain

# Initialize RAG chain (add after app creation)
# rag_chain: Optional[UltimateRAGChain] = None

# @app.on_event("startup")
# async def init_rag():
#     global rag_chain
#     try:
#         rag_chain = UltimateRAGChain()
#         logger.info("RAG system initialized")
#     except Exception as e:
#         logger.warning(f"RAG system initialization failed: {e}")


# ===== RAG ENDPOINTS =====

@app.post("/api/rag/upload")
async def rag_upload_files(files: List[UploadFile] = File(...)):
    """Upload and process documents for RAG"""
    if not rag_chain:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    try:
        # Save uploaded files
        upload_dir = Path("./uploads/rag")
        upload_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []
        for file in files:
            file_path = upload_dir / file.filename
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            saved_paths.append(str(file_path))

        # Process files
        result = rag_chain.process_documents(file_paths=saved_paths)

        return {
            "success": True,
            "message": f"Processed {result['documents_processed']} documents",
            "chunks_created": result['chunks_created'],
            "documents": result['documents_processed']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/upload-folder")
async def rag_upload_folder(folder_path: str = Form(...)):
    """Process entire folder of documents"""
    if not rag_chain:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    try:
        folder = Path(folder_path)
        if not folder.exists():
            raise HTTPException(status_code=404, detail=f"Folder not found: {folder_path}")

        result = rag_chain.process_documents(folder_path=str(folder))

        return {
            "success": True,
            "message": f"Processed {result['documents_processed']} documents from folder",
            "chunks_created": result['chunks_created'],
            "documents": result['documents_processed'],
            "chunk_types": result.get('chunk_types', {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/query")
async def rag_query(
    question: str = Form(...),
    session_id: str = Form("default"),
    file_filters: Optional[List[str]] = Form(None)
):
    """Query documents using RAG"""
    if not rag_chain:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    try:
        result = rag_chain.query(
            question=question,
            session_id=session_id,
            file_filters=file_filters,
            include_history=True
        )

        return {
            "success": result['success'],
            "answer": result['answer'],
            "sources": result.get('sources', []),
            "confidence": result.get('confidence', 0.0),
            "files_used": result.get('files_used', []),
            "num_chunks": result.get('num_chunks_used', 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rag/documents")
async def rag_list_documents():
    """List all indexed documents"""
    if not rag_chain:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    try:
        docs = rag_chain.list_documents()
        return {
            "success": True,
            "documents": docs,
            "count": len(docs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rag/stats")
async def rag_statistics():
    """Get RAG system statistics"""
    if not rag_chain:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    try:
        stats = rag_chain.get_statistics()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/rag/clear")
async def rag_clear():
    """Clear all RAG documents"""
    if not rag_chain:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    try:
        rag_chain.clear_vector_store()
        return {
            "success": True,
            "message": "All documents cleared"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

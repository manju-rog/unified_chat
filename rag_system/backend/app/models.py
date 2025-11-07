"""
Pydantic models for API
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class UploadDocumentRequest(BaseModel):
    """Request to upload document(s)"""
    file_paths: Optional[List[str]] = Field(None, description="List of file paths")
    folder_path: Optional[str] = Field(None, description="Folder path to process")


class QueryRequest(BaseModel):
    """Request to query the RAG system"""
    question: str = Field(..., description="User's question")
    session_id: str = Field("default", description="Session ID for conversation memory")
    file_filters: Optional[List[str]] = Field(None, description="Filter by specific files")
    date_filter: Optional[Dict[str, str]] = Field(None, description="Filter by date (after/before)")
    include_history: bool = Field(True, description="Include conversation history")


class QueryResponse(BaseModel):
    """Response from query"""
    success: bool
    answer: str
    sources: List[Dict[str, Any]] = []
    confidence: float = 0.0
    num_chunks_used: int = 0
    files_used: List[str] = []
    tokens_used: Optional[Dict[str, int]] = None
    query_metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class UploadResponse(BaseModel):
    """Response from document upload"""
    success: bool
    chunks_created: int = 0
    chunks_added: int = 0
    documents_processed: int = 0
    chunk_types: Optional[Dict[str, int]] = None
    error: Optional[str] = None


class DocumentInfo(BaseModel):
    """Document information"""
    document_name: str
    file_path: str
    file_type: str
    file_size: int
    modified_date: str
    chunk_count: int


class SystemStats(BaseModel):
    """System statistics"""
    vector_store: Dict[str, Any]
    documents: Dict[str, Any]
    conversations: Dict[str, Any]
    settings: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    components: Dict[str, str]

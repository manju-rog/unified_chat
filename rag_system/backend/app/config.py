"""
🚀 ULTIMATE FREE-TIER RAG CONFIGURATION v2.1
==============================================
The most advanced RAG system configuration possible without paid services!
Every feature maximized for free tier (except Claude API)

Author: Manju's Ultimate RAG System
Version: 2.1 ULTIMATE
Date: 2025
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from pathlib import Path
from typing import List, Dict, Any, Optional
import os


class UltimateRAGSettings(BaseSettings):
    """
    The most comprehensive RAG configuration ever created for free tier!
    This pushes EVERY free tool to its absolute limits!
    """

    # ===== 🔥 CORE CONFIGURATION =====
    APP_NAME: str = "ULTIMATE RAG SYSTEM v2.1"
    APP_VERSION: str = "2.1.0-ULTIMATE"
    DEBUG: bool = Field(False, description="Debug mode")
    ENVIRONMENT: str = Field("production", description="Environment")

    # Paths
    BASE_DIR: Path = Field(default=Path(__file__).parent.parent)
    DATA_DIR: Path = Field(default=Path(__file__).parent.parent / "data")
    UPLOAD_DIR: Path = Field(default=Path(__file__).parent.parent / "data" / "uploads")
    CACHE_DIR: Path = Field(default=Path(__file__).parent.parent / "data" / "cache")

    # ===== 🎯 CLAUDE AI (The ONLY paid component) =====
    ANTHROPIC_API_KEY: str = Field("", description="Claude API key - REQUIRED!")
    CLAUDE_MODEL: str = Field("claude-3-5-sonnet-20241022", description="Latest Claude model")
    CLAUDE_TEMPERATURE: float = Field(0.7, ge=0.0, le=2.0)
    CLAUDE_MAX_TOKENS: int = Field(8000, description="Max output tokens")

    # NEW: Claude context window utilization (Claude 3.5 Sonnet has 200K context!)
    MAX_CONTEXT_TOKENS: int = Field(180000, description="Use 90% of Claude's 200K window!")

    # ===== 🧠 MULTI-MODEL EMBEDDINGS (ALL FREE!) =====
    # Primary embeddings - Fast and balanced
    PRIMARY_EMBEDDING_MODEL: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2",
        description="Fast, 384-dim, perfect for retrieval"
    )
    PRIMARY_EMBEDDING_DIM: int = Field(384)

    # Secondary embeddings for hybrid search - Higher quality
    SECONDARY_EMBEDDING_MODEL: str = Field(
        "sentence-transformers/all-mpnet-base-v2",
        description="Higher quality, 768-dim"
    )
    SECONDARY_EMBEDDING_DIM: int = Field(768)

    # Specialized embeddings
    CODE_EMBEDDING_MODEL: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2",  # Using same for simplicity
        description="For code files"
    )

    # ===== 📊 ADVANCED CHUNKING STRATEGIES =====
    # Parent-child hierarchical chunking
    ENABLE_PARENT_CHILD_CHUNKING: bool = Field(True, description="Parent-child chunks")
    PARENT_CHUNK_SIZE: int = Field(2000, description="Large context chunks (tokens)")
    PARENT_CHUNK_OVERLAP: int = Field(400, description="Parent overlap")

    CHILD_CHUNK_SIZE: int = Field(600, description="Precise retrieval chunks (tokens)")
    CHILD_CHUNK_OVERLAP: int = Field(120, description="Child overlap (20%)")

    # Semantic chunking - sentence-aware splitting
    ENABLE_SEMANTIC_CHUNKING: bool = Field(True, description="Smart sentence-aware chunking")
    SEMANTIC_THRESHOLD: float = Field(0.5, description="Similarity threshold for breaks")

    # Sliding window chunking - multiple perspectives
    ENABLE_SLIDING_WINDOW: bool = Field(True, description="Multiple overlapping views")
    WINDOW_SIZES: List[int] = Field([400, 800, 1600], description="Multiple chunk sizes")

    # ===== 🗄️ CHROMADB CONFIGURATION (FREE!) =====
    CHROMA_PERSIST_DIR: str = Field("./data/chroma", description="ChromaDB storage")

    # Multiple collections for different purposes
    MAIN_COLLECTION: str = Field("documents", description="Main document collection")
    PARENT_COLLECTION: str = Field("parent_chunks", description="Parent chunks")
    METADATA_COLLECTION: str = Field("document_metadata", description="Metadata only")
    CONVERSATION_COLLECTION: str = Field("conversations", description="Chat history")

    # ===== 🔍 RETRIEVAL CONFIGURATION =====
    # Multi-stage retrieval - RETRIEVE LOTS, RERANK, SELECT BEST!
    INITIAL_RETRIEVAL_K: int = Field(100, description="Cast WIDE net - retrieve 100 chunks!")
    RERANK_TOP_K: int = Field(50, description="Rerank to top 50")
    FINAL_TOP_K: int = Field(30, description="Send top 30 to Claude - using that context window!")

    # Retrieval strategies
    ENABLE_HYBRID_SEARCH: bool = Field(True, description="Dense + Sparse retrieval")
    ENABLE_MMR: bool = Field(True, description="Maximal Marginal Relevance for diversity")
    MMR_DIVERSITY_WEIGHT: float = Field(0.3, description="Balance relevance vs diversity")

    # Query expansion
    ENABLE_QUERY_EXPANSION: bool = Field(True, description="Generate query variations")
    QUERY_VARIATIONS: int = Field(3, description="Generate 3 query variations")
    ENABLE_QUERY_REWRITING: bool = Field(True, description="Rewrite queries for better retrieval")

    # ===== 🎯 RERANKING (ALL FREE!) =====
    ENABLE_RERANKING: bool = Field(True, description="Rerank retrieved chunks")
    RERANKER_MODEL: str = Field(
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Fast cross-encoder reranker"
    )

    # ===== 💾 CACHING & OPTIMIZATION =====
    ENABLE_SEMANTIC_CACHE: bool = Field(True, description="Cache similar queries")
    CACHE_SIMILARITY_THRESHOLD: float = Field(0.95, description="How similar for cache hit")
    CACHE_TTL_SECONDS: int = Field(86400, description="24 hour cache")

    ENABLE_EMBEDDING_CACHE: bool = Field(True, description="Cache embeddings")

    # ===== 🧩 DOCUMENT PROCESSING =====
    SUPPORTED_FORMATS: List[str] = Field(default=[
        # Documents
        ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".txt", ".md", ".rtf",
        # Data files
        ".csv", ".xlsx", ".xls", ".json", ".xml", ".yaml", ".yml",
        # Web formats
        ".html", ".htm",
        # Code files
        ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".c", ".h",
        ".go", ".rs", ".rb", ".php", ".cs", ".swift", ".kt",
        # Config files
        ".toml", ".ini", ".conf", ".cfg", ".env",
        # Other
        ".epub", ".odt"
    ])

    MAX_FILE_SIZE_MB: int = Field(100, description="Max file size")
    ENABLE_OCR: bool = Field(True, description="Extract text from images in PDFs")

    # ===== 📈 METADATA EXTRACTION =====
    ENABLE_ADVANCED_METADATA: bool = Field(True, description="Extract rich metadata")
    EXTRACT_ENTITIES: bool = Field(True, description="Named entity recognition")
    EXTRACT_KEYWORDS: bool = Field(True, description="Keyword extraction")
    EXTRACT_SUMMARIES: bool = Field(True, description="Generate summaries")
    EXTRACT_LANGUAGE: bool = Field(True, description="Detect language")

    # ===== 🗣️ CONVERSATION MANAGEMENT =====
    ENABLE_CONVERSATION_MEMORY: bool = Field(True, description="Remember chat history")
    CONVERSATION_WINDOW_SIZE: int = Field(10, description="Last 10 exchanges")

    # ===== 🔄 MULTI-DOCUMENT SUPPORT =====
    ENABLE_FILE_FILTERING: bool = Field(True, description="Filter by filename")
    ENABLE_DATE_FILTERING: bool = Field(True, description="Filter by date modified")
    TRACK_FILE_METADATA: bool = Field(True, description="Track all file metadata")

    # ===== 📊 ADVANCED FEATURES =====
    ENABLE_ANSWER_GRADING: bool = Field(True, description="Grade answer quality")
    ENABLE_CITATIONS: bool = Field(True, description="Show source citations")
    ENABLE_CONFIDENCE_SCORES: bool = Field(True, description="Confidence in answers")

    # ===== ⚡ PERFORMANCE =====
    ENABLE_BATCH_PROCESSING: bool = Field(True, description="Process multiple files")
    BATCH_SIZE: int = Field(10, description="Process 10 files at a time")
    MAX_WORKERS: int = Field(4, description="Parallel processing workers")

    # ===== 🎨 PROMPTS =====
    # The ULTIMATE RAG prompt that makes Claude give comprehensive answers!
    RAG_SYSTEM_PROMPT: str = """You are an expert AI assistant with access to a comprehensive document knowledge base.

Your goal is to provide COMPREHENSIVE, DETAILED, and HELPFUL answers based on the provided context.

CRITICAL INSTRUCTIONS:
1. Read ALL provided context carefully - you have multiple relevant sections from the documents
2. Provide THOROUGH and DETAILED answers - not brief summaries
3. Synthesize information from multiple context sections when available
4. Use specific examples, quotes, and details from the context
5. Structure complex answers with clear sections using markdown
6. If you notice gaps in the context, acknowledge them but provide the best answer possible
7. ALWAYS cite your sources using [Source: filename.ext] notation
8. Include relevant file names when discussing information
9. If information comes from multiple files, mention all relevant files
10. Pay attention to file modification dates when relevant to the query

FORMATTING:
- Use markdown for readability (headers, bullets, bold, code blocks)
- For complex topics, use sections with ## headers
- Use bullet points for lists
- Use **bold** for emphasis
- Use `code` formatting for technical terms

COMPREHENSIVENESS:
- Aim for completeness over brevity
- Explain concepts thoroughly
- Provide context and background when helpful
- Include relevant examples

If the answer is not in the provided context, clearly state: "I cannot find this information in the provided documents."

Never make up information that isn't in the context!"""

    RAG_QUERY_PROMPT_TEMPLATE: str = """CONTEXT FROM DOCUMENTS:
{context}

---

USER QUESTION: {question}

---

CONVERSATION HISTORY:
{history}

---

YOUR DETAILED ANSWER (with citations):"""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_prefix = ""

    @field_validator("ANTHROPIC_API_KEY")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v or v == "":
            print("⚠️  WARNING: ANTHROPIC_API_KEY not set! Please set it in .env file")
        return v

    def model_post_init(self, __context: Any) -> None:
        """Create directories after initialization"""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def get_total_features_enabled(self) -> int:
        """Count enabled features"""
        feature_count = 0
        for field_name in self.model_fields:
            if field_name.startswith('ENABLE_'):
                if getattr(self, field_name):
                    feature_count += 1
        return feature_count

    def print_startup_banner(self):
        """Print epic startup message"""
        print("=" * 80)
        print(f"🚀 {self.APP_NAME} INITIALIZED!")
        print("=" * 80)
        print(f"✅ {self.get_total_features_enabled()} Advanced Features Enabled!")
        print(f"📊 Using Multi-Model Embeddings (384-dim + 768-dim)")
        print(f"🎯 Multi-Stage Retrieval: {self.INITIAL_RETRIEVAL_K} → {self.RERANK_TOP_K} → {self.FINAL_TOP_K}")
        print(f"🧠 Context Window: {self.MAX_CONTEXT_TOKENS:,} tokens (90% of Claude's capacity!)")
        print(f"📝 Supported Formats: {len(self.SUPPORTED_FORMATS)} file types")
        print(f"💾 Semantic Caching: {'✓' if self.ENABLE_SEMANTIC_CACHE else '✗'}")
        print(f"🔄 Conversation Memory: {'✓' if self.ENABLE_CONVERSATION_MEMORY else '✗'}")
        print(f"📈 Advanced Metadata: {'✓' if self.ENABLE_ADVANCED_METADATA else '✗'}")
        print(f"🎨 Parent-Child Chunking: {'✓' if self.ENABLE_PARENT_CHILD_CHUNKING else '✗'}")
        print("=" * 80)


# Singleton instance
_settings: Optional[UltimateRAGSettings] = None

def get_settings() -> UltimateRAGSettings:
    """Get or create settings instance"""
    global _settings
    if _settings is None:
        _settings = UltimateRAGSettings()
        _settings.print_startup_banner()
    return _settings


if __name__ == "__main__":
    settings = get_settings()
    print(f"\n📊 Configuration Summary:")
    print(f"   - Primary Embedding Model: {settings.PRIMARY_EMBEDDING_MODEL}")
    print(f"   - Claude Model: {settings.CLAUDE_MODEL}")
    print(f"   - Initial Retrieval: {settings.INITIAL_RETRIEVAL_K} chunks")
    print(f"   - Final to Claude: {settings.FINAL_TOP_K} chunks")
    print(f"   - Parent Chunk Size: {settings.PARENT_CHUNK_SIZE} tokens")
    print(f"   - Child Chunk Size: {settings.CHILD_CHUNK_SIZE} tokens")

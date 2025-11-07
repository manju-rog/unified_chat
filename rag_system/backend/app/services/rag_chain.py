"""
🚀 ULTIMATE RAG CHAIN v2.1
==========================
Complete RAG pipeline with Claude 3.5 Sonnet
Features:
- Multi-stage retrieval with reranking
- Conversation memory
- Answer grading and confidence scoring
- Rich citations with file tracking
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import anthropic

from .document_processor import UltimateDocumentProcessor, DocumentChunk
from .vector_store import UltimateVectorStore
from ..config import get_settings


class UltimateRAGChain:
    """
    The ultimate RAG chain orchestrating all components
    """

    def __init__(self, settings=None):
        self.settings = settings or get_settings()

        print("🚀 Initializing Ultimate RAG Chain...")

        # Initialize components
        self.document_processor = UltimateDocumentProcessor(self.settings)
        self.vector_store = UltimateVectorStore(self.settings)

        # Initialize Claude client
        if not self.settings.ANTHROPIC_API_KEY:
            print("⚠️  WARNING: ANTHROPIC_API_KEY not set!")
            self.claude_client = None
        else:
            self.claude_client = anthropic.Anthropic(
                api_key=self.settings.ANTHROPIC_API_KEY
            )
            print(f"   ✓ Claude client initialized ({self.settings.CLAUDE_MODEL})")

        # Conversation memory (in-memory for now)
        self.conversations: Dict[str, List[Dict]] = {}

        print("✅ RAG Chain ready!")

    def process_documents(self, file_paths: List[str] = None, folder_path: str = None) -> Dict[str, Any]:
        """
        Process documents or entire folder
        """
        print("\n" + "="*80)
        print("📚 DOCUMENT PROCESSING PIPELINE")
        print("="*80)

        chunks = []

        if folder_path:
            # Process entire folder
            chunks = self.document_processor.process_folder(folder_path)

        elif file_paths:
            # Process individual files
            for file_path in file_paths:
                try:
                    file_chunks = self.document_processor.process_document(file_path)
                    chunks.extend(file_chunks)
                except Exception as e:
                    print(f"❌ Error processing {file_path}: {e}")
                    continue

        if not chunks:
            return {
                "success": False,
                "error": "No chunks created from documents",
                "chunks_created": 0
            }

        # Add to vector store
        num_added = self.vector_store.add_documents(chunks)

        result = {
            "success": True,
            "chunks_created": len(chunks),
            "chunks_added": num_added,
            "documents_processed": len(set(c.document_name for c in chunks)),
            "chunk_types": {
                "parent": len([c for c in chunks if c.chunk_type == "parent"]),
                "child": len([c for c in chunks if c.chunk_type == "child"]),
                "semantic": len([c for c in chunks if c.chunk_type == "semantic"]),
                "window": len([c for c in chunks if c.chunk_type == "window"])
            }
        }

        print("\n" + "="*80)
        print("✅ PROCESSING COMPLETE")
        print("="*80)
        print(f"📊 Documents: {result['documents_processed']}")
        print(f"📄 Total chunks: {result['chunks_created']}")
        print(f"💾 Added to vector store: {result['chunks_added']}")
        print(f"🎨 Chunk types: {result['chunk_types']}")
        print("="*80)

        return result

    def query(
        self,
        question: str,
        session_id: str = "default",
        file_filters: Optional[List[str]] = None,
        date_filter: Optional[Dict[str, str]] = None,
        include_history: bool = True
    ) -> Dict[str, Any]:
        """
        Query the RAG system with a question

        Args:
            question: User's question
            session_id: Session ID for conversation memory
            file_filters: Filter by specific file names
            date_filter: Filter by date modified
            include_history: Whether to include conversation history

        Returns:
            Complete answer with sources and metadata
        """
        print("\n" + "="*80)
        print(f"💬 QUERY: {question[:100]}...")
        print("="*80)

        if not self.claude_client:
            return {
                "success": False,
                "error": "Claude API key not configured",
                "answer": "Error: Claude API key not set. Please set ANTHROPIC_API_KEY in .env file"
            }

        # Get conversation history
        conversation_history = []
        if include_history and self.settings.ENABLE_CONVERSATION_MEMORY:
            conversation_history = self.conversations.get(session_id, [])
            conversation_history = conversation_history[-self.settings.CONVERSATION_WINDOW_SIZE:]

        # Retrieve relevant chunks
        print("\n🔍 Retrieving relevant information...")
        retrieval_result = self.vector_store.query(
            query_text=question,
            file_filters=file_filters,
            date_filter=date_filter,
            conversation_history=conversation_history
        )

        if not retrieval_result['chunks']:
            answer = "I couldn't find any relevant information in the documents to answer your question."
            return {
                "success": True,
                "answer": answer,
                "sources": [],
                "confidence": 0.0,
                "num_chunks_used": 0
            }

        # Build context from chunks
        print(f"\n📝 Building context from {len(retrieval_result['chunks'])} chunks...")
        context = self._build_context(retrieval_result['chunks'])

        print(f"   ✓ Context built: {len(context)} characters")
        print(f"   ✓ Tokens estimate: ~{len(context) // 4}")
        print(f"   ✓ Files referenced: {len(retrieval_result['files_used'])}")

        # Build conversation history string
        history_str = self._build_history_string(conversation_history)

        # Build the prompt
        prompt = self.settings.RAG_QUERY_PROMPT_TEMPLATE.format(
            context=context,
            question=question,
            history=history_str
        )

        # Query Claude
        print(f"\n🤖 Querying Claude ({self.settings.CLAUDE_MODEL})...")

        try:
            response = self.claude_client.messages.create(
                model=self.settings.CLAUDE_MODEL,
                max_tokens=self.settings.CLAUDE_MAX_TOKENS,
                temperature=self.settings.CLAUDE_TEMPERATURE,
                system=self.settings.RAG_SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            answer = response.content[0].text

            # Calculate token usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens

            print(f"   ✓ Answer generated ({output_tokens} tokens)")
            print(f"   ✓ Total tokens used: {total_tokens}")

        except Exception as e:
            print(f"   ❌ Claude API error: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": f"Error querying Claude: {e}"
            }

        # Grade answer quality (if enabled)
        confidence = 0.0
        if self.settings.ENABLE_CONFIDENCE_SCORES:
            confidence = self._calculate_confidence(
                question,
                answer,
                retrieval_result['chunks']
            )

        # Prepare result
        result = {
            "success": True,
            "answer": answer,
            "sources": retrieval_result['sources'],
            "confidence": confidence,
            "num_chunks_used": len(retrieval_result['chunks']),
            "files_used": retrieval_result['files_used'],
            "tokens_used": {
                "input": input_tokens,
                "output": output_tokens,
                "total": total_tokens
            },
            "query_metadata": {
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id
            }
        }

        # Store in conversation history
        if self.settings.ENABLE_CONVERSATION_MEMORY:
            self._update_conversation_history(session_id, question, answer)

        print("\n" + "="*80)
        print("✅ QUERY COMPLETE")
        print("="*80)
        print(f"📊 Confidence: {confidence:.2%}")
        print(f"📄 Chunks used: {result['num_chunks_used']}")
        print(f"📁 Files: {len(result['files_used'])}")
        print(f"🎯 Tokens: {total_tokens:,}")
        print("="*80)

        return result

    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Build context string from chunks
        Organized by document with metadata
        """
        # Group chunks by document
        docs_chunks = {}
        for chunk in chunks:
            doc_name = chunk['metadata']['document_name']
            if doc_name not in docs_chunks:
                docs_chunks[doc_name] = []
            docs_chunks[doc_name].append(chunk)

        # Build context string
        context_parts = []

        for doc_name, doc_chunks in docs_chunks.items():
            # Document header
            first_chunk = doc_chunks[0]
            metadata = first_chunk['metadata']

            doc_header = f"\n{'='*80}\n"
            doc_header += f"📄 SOURCE: {doc_name}\n"
            doc_header += f"   Type: {metadata['file_type']}\n"
            doc_header += f"   Modified: {metadata['modified_date']}\n"
            doc_header += f"   Chunks: {len(doc_chunks)}\n"
            doc_header += f"{'='*80}\n"

            context_parts.append(doc_header)

            # Add chunks
            for i, chunk in enumerate(doc_chunks, 1):
                is_parent = chunk.get('is_parent', False)
                chunk_type = "PARENT CONTEXT" if is_parent else "CHUNK"

                chunk_text = f"\n[{chunk_type} {i}]\n{chunk['content']}\n"
                context_parts.append(chunk_text)

        return "\n".join(context_parts)

    def _build_history_string(self, history: List[Dict]) -> str:
        """Build conversation history string"""
        if not history:
            return "No previous conversation."

        history_parts = []
        for exchange in history:
            history_parts.append(f"User: {exchange['question']}")
            history_parts.append(f"Assistant: {exchange['answer'][:200]}...")  # Truncate
            history_parts.append("")

        return "\n".join(history_parts)

    def _calculate_confidence(
        self,
        question: str,
        answer: str,
        chunks: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate confidence score for the answer
        Simple heuristic-based approach
        """
        confidence = 0.5  # Base confidence

        # Factor 1: Answer length (not too short, not too long)
        answer_words = len(answer.split())
        if 50 <= answer_words <= 500:
            confidence += 0.2
        elif answer_words > 20:
            confidence += 0.1

        # Factor 2: Multiple sources used
        num_sources = len(set(c['metadata']['document_name'] for c in chunks))
        if num_sources >= 3:
            confidence += 0.2
        elif num_sources >= 2:
            confidence += 0.1

        # Factor 3: Check if answer contains "I cannot find" or similar
        negative_phrases = ["i cannot find", "i couldn't find", "no information", "not in the", "don't know"]
        if any(phrase in answer.lower() for phrase in negative_phrases):
            confidence -= 0.3

        # Factor 4: Citations present (looking for [Source: patterns)
        if "[Source:" in answer or "Source:" in answer:
            confidence += 0.1

        # Clamp to [0, 1]
        confidence = max(0.0, min(1.0, confidence))

        return confidence

    def _update_conversation_history(self, session_id: str, question: str, answer: str):
        """Update conversation history for session"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        self.conversations[session_id].append({
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        })

        # Keep only last N exchanges
        max_history = self.settings.CONVERSATION_WINDOW_SIZE
        if len(self.conversations[session_id]) > max_history:
            self.conversations[session_id] = self.conversations[session_id][-max_history:]

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for session"""
        return self.conversations.get(session_id, [])

    def clear_conversation_history(self, session_id: str = None):
        """Clear conversation history"""
        if session_id:
            self.conversations.pop(session_id, None)
            print(f"✅ Cleared history for session: {session_id}")
        else:
            self.conversations.clear()
            print("✅ Cleared all conversation history")

    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        vector_stats = self.vector_store.get_statistics()
        documents = self.vector_store.list_documents()

        return {
            "vector_store": vector_stats,
            "documents": {
                "count": len(documents),
                "list": documents
            },
            "conversations": {
                "active_sessions": len(self.conversations),
                "total_exchanges": sum(len(h) for h in self.conversations.values())
            },
            "settings": {
                "model": self.settings.CLAUDE_MODEL,
                "max_context_tokens": self.settings.MAX_CONTEXT_TOKENS,
                "retrieval_k": self.settings.FINAL_TOP_K,
                "features_enabled": self.settings.get_total_features_enabled()
            }
        }

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all indexed documents"""
        return self.vector_store.list_documents()

    def clear_vector_store(self):
        """Clear all documents from vector store"""
        self.vector_store.clear_collection()
        print("✅ Cleared vector store")


if __name__ == "__main__":
    # Test RAG chain
    settings = get_settings()
    rag = UltimateRAGChain(settings)

    print("\n" + "="*80)
    print("🚀 Ultimate RAG Chain Ready!")
    print("="*80)
    print("\nSystem Statistics:")
    stats = rag.get_statistics()
    print(json.dumps(stats, indent=2))

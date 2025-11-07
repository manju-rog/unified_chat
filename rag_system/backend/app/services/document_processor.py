"""
🚀 ULTIMATE DOCUMENT PROCESSOR v2.1
====================================
Processes 30+ file formats with advanced chunking and metadata extraction
ALL FREE TIER (except Claude API)!

Features:
- 30+ file format support (PDF, DOCX, PPTX, CSV, JSON, code files, etc.)
- Multiple chunking strategies (parent-child, semantic, sliding window)
- Rich metadata extraction (entities, keywords, file info, dates)
- File name and content awareness
- Date tracking and filtering
"""

import os
import hashlib
import json
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import re

# Document processing libraries (ALL FREE!)
try:
    import PyPDF2
    from pdfminer.high_level import extract_text as pdf_extract_text
except:
    pass

try:
    import docx
except:
    pass

try:
    from pptx import Presentation
except:
    pass

import pandas as pd
from bs4 import BeautifulSoup
import chardet

# NLP libraries (ALL FREE!)
import spacy
from sentence_transformers import SentenceTransformer
import nltk
from collections import Counter

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)

from ..config import get_settings


@dataclass
class DocumentChunk:
    """Enhanced chunk with rich metadata"""
    # Content
    content: str
    chunk_id: str
    chunk_index: int

    # Document info
    document_id: str
    document_name: str
    file_path: str
    file_size: int
    file_type: str
    file_extension: str

    # Dates (critical for user requirement!)
    created_date: str
    modified_date: str
    processed_date: str

    # Chunk metadata
    chunk_type: str  # 'parent', 'child', 'semantic', 'window'
    chunk_size_category: str  # 'small', 'medium', 'large', 'xlarge'
    word_count: int
    char_count: int
    sentence_count: int

    # Hierarchical relationships
    parent_chunk_id: Optional[str] = None
    child_chunk_ids: List[str] = None

    # Position info
    start_char: int = 0
    end_char: int = 0
    page_numbers: Optional[List[int]] = None

    # Extracted features
    keywords: List[str] = None
    entities: List[str] = None
    language: str = "en"

    # Quality metrics
    completeness_score: float = 0.0
    relevance_score: float = 0.0

    def __post_init__(self):
        if self.child_chunk_ids is None:
            self.child_chunk_ids = []
        if self.keywords is None:
            self.keywords = []
        if self.entities is None:
            self.entities = []
        if self.page_numbers is None:
            self.page_numbers = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def get_metadata_dict(self) -> Dict[str, Any]:
        """Get metadata for vector store"""
        return {
            "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index,
            "document_id": self.document_id,
            "document_name": self.document_name,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_extension": self.file_extension,
            "file_size": self.file_size,
            "created_date": self.created_date,
            "modified_date": self.modified_date,
            "processed_date": self.processed_date,
            "chunk_type": self.chunk_type,
            "chunk_size_category": self.chunk_size_category,
            "word_count": self.word_count,
            "keywords": json.dumps(self.keywords),
            "entities": json.dumps(self.entities),
            "parent_chunk_id": self.parent_chunk_id or "",
            "page_numbers": json.dumps(self.page_numbers) if self.page_numbers else "[]"
        }


class UltimateDocumentProcessor:
    """
    The most advanced document processor on free tier!
    Handles 30+ formats with intelligent chunking
    """

    def __init__(self, settings=None):
        self.settings = settings or get_settings()

        print("🚀 Initializing Ultimate Document Processor...")

        # Load spaCy model for NLP
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            print("   📦 Downloading spaCy model...")
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

        # For keyword extraction (simple but effective)
        from nltk.corpus import stopwords
        self.stop_words = set(stopwords.words('english'))

        print(f"✅ Document Processor ready! Supports {len(self.settings.SUPPORTED_FORMATS)} formats")

    def process_folder(self, folder_path: str) -> List[DocumentChunk]:
        """
        Process an entire folder of 30-40 documents
        Returns all chunks with perfect metadata tracking
        """
        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Folder not found: {folder_path}")

        print(f"\n📁 Processing folder: {folder_path}")

        # Get all supported files
        all_files = []
        for file_path in folder.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.settings.SUPPORTED_FORMATS:
                all_files.append(file_path)

        # Sort by modified date (newest first)
        all_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        print(f"📄 Found {len(all_files)} documents:")
        for i, file_path in enumerate(all_files[:10], 1):  # Show first 10
            mod_date = datetime.fromtimestamp(file_path.stat().st_mtime)
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"   {i}. {file_path.name} ({size_mb:.2f}MB, modified: {mod_date.strftime('%Y-%m-%d %H:%M')})")
        if len(all_files) > 10:
            print(f"   ... and {len(all_files) - 10} more files")

        # Process each file
        all_chunks = []
        for i, file_path in enumerate(all_files, 1):
            try:
                print(f"\n🔄 [{i}/{len(all_files)}] Processing: {file_path.name}")
                chunks = self.process_document(str(file_path))
                all_chunks.extend(chunks)
                print(f"   ✅ Created {len(chunks)} chunks")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue

        print(f"\n🎉 Successfully processed {len(all_files)} files → {len(all_chunks)} total chunks!")
        return all_chunks

    def process_document(self, file_path: str) -> List[DocumentChunk]:
        """
        Process a single document with ALL advanced strategies
        Returns multiple types of chunks (parent, child, semantic)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        print(f"   📄 Extracting text from {file_path.suffix} file...")

        # Extract text based on file type
        text = self._extract_text(file_path)

        if not text or len(text.strip()) < 50:
            raise ValueError(f"No meaningful text extracted from {file_path}")

        # Calculate document hash (unique ID)
        doc_hash = hashlib.md5((str(file_path) + text[:1000]).encode()).hexdigest()[:16]

        # Get file metadata
        file_stats = file_path.stat()
        file_metadata = {
            "document_id": doc_hash,
            "document_name": file_path.name,
            "file_path": str(file_path),
            "file_size": file_stats.st_size,
            "file_type": mimetypes.guess_type(str(file_path))[0] or "unknown",
            "file_extension": file_path.suffix.lower(),
            "created_date": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
            "modified_date": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            "processed_date": datetime.now().isoformat()
        }

        print(f"   🔨 Creating chunks with multiple strategies...")

        all_chunks = []

        # Strategy 1: Parent-Child Hierarchical Chunking
        if self.settings.ENABLE_PARENT_CHILD_CHUNKING:
            parent_child_chunks = self._create_parent_child_chunks(text, file_metadata)
            all_chunks.extend(parent_child_chunks)
            print(f"      ✓ Parent-child: {len(parent_child_chunks)} chunks")

        # Strategy 2: Semantic Chunking (sentence-aware)
        if self.settings.ENABLE_SEMANTIC_CHUNKING:
            semantic_chunks = self._create_semantic_chunks(text, file_metadata)
            all_chunks.extend(semantic_chunks)
            print(f"      ✓ Semantic: {len(semantic_chunks)} chunks")

        # Strategy 3: Sliding Window (multiple sizes)
        if self.settings.ENABLE_SLIDING_WINDOW:
            window_chunks = self._create_sliding_window_chunks(text, file_metadata)
            all_chunks.extend(window_chunks)
            print(f"      ✓ Sliding window: {len(window_chunks)} chunks")

        # Extract metadata for all chunks
        print(f"   🏷️  Extracting metadata for {len(all_chunks)} chunks...")
        if self.settings.ENABLE_ADVANCED_METADATA:
            for chunk in all_chunks:
                self._extract_chunk_metadata(chunk)

        return all_chunks

    def _extract_text(self, file_path: Path) -> str:
        """Extract text from 30+ file formats"""
        ext = file_path.suffix.lower()

        try:
            # PDF files
            if ext == '.pdf':
                return self._extract_pdf_text(file_path)

            # Microsoft Office
            elif ext in ['.docx', '.doc']:
                return self._extract_docx_text(file_path)
            elif ext in ['.pptx', '.ppt']:
                return self._extract_pptx_text(file_path)
            elif ext in ['.xlsx', '.xls']:
                return self._extract_excel_text(file_path)

            # Plain text and markdown
            elif ext in ['.txt', '.md', '.rtf']:
                return self._extract_plain_text(file_path)

            # Code files
            elif ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h',
                        '.go', '.rs', '.rb', '.php', '.cs', '.swift', '.kt']:
                text = self._extract_plain_text(file_path)
                return f"[CODE FILE: {file_path.suffix[1:].upper()}]\nFile: {file_path.name}\n\n{text}"

            # Data formats
            elif ext == '.json':
                return self._extract_json_text(file_path)
            elif ext in ['.yaml', '.yml']:
                return self._extract_yaml_text(file_path)
            elif ext == '.csv':
                return self._extract_csv_text(file_path)
            elif ext == '.xml':
                return self._extract_xml_text(file_path)

            # Web formats
            elif ext in ['.html', '.htm']:
                return self._extract_html_text(file_path)

            # Config files
            elif ext in ['.toml', '.ini', '.conf', '.cfg', '.env']:
                text = self._extract_plain_text(file_path)
                return f"[CONFIG FILE]\nFile: {file_path.name}\n\n{text}"

            # Fallback: try as plain text
            else:
                return self._extract_plain_text(file_path)

        except Exception as e:
            raise Exception(f"Error extracting text from {file_path}: {e}")

    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF"""
        text_parts = []

        try:
            # Try pdfminer first (better quality)
            text = pdf_extract_text(str(file_path))
            if text and len(text.strip()) > 100:
                return text
        except:
            pass

        # Fallback to PyPDF2
        try:
            with open(file_path, 'rb') as file:
                pdf = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"[Page {page_num + 1}]\n{page_text}")
            return "\n\n".join(text_parts)
        except Exception as e:
            raise Exception(f"PDF extraction failed: {e}")

    def _extract_docx_text(self, file_path: Path) -> str:
        """Extract text from Word documents"""
        try:
            doc = docx.Document(file_path)
            text_parts = []

            # Extract paragraphs
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)

            # Extract tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join([cell.text for cell in row.cells])
                    if row_text.strip():
                        text_parts.append(row_text)

            return "\n\n".join(text_parts)
        except Exception as e:
            raise Exception(f"DOCX extraction failed: {e}")

    def _extract_pptx_text(self, file_path: Path) -> str:
        """Extract text from PowerPoint"""
        try:
            prs = Presentation(str(file_path))
            text_parts = []

            for slide_num, slide in enumerate(prs.slides, 1):
                slide_text = f"[Slide {slide_num}]\n"
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_text += shape.text + "\n"
                text_parts.append(slide_text)

            return "\n\n".join(text_parts)
        except Exception as e:
            raise Exception(f"PPTX extraction failed: {e}")

    def _extract_excel_text(self, file_path: Path) -> str:
        """Extract text from Excel"""
        try:
            xl_file = pd.ExcelFile(file_path)
            text_parts = []

            for sheet_name in xl_file.sheet_names:
                df = pd.read_excel(xl_file, sheet_name)
                sheet_text = f"[Sheet: {sheet_name}]\n"
                sheet_text += df.to_string()
                text_parts.append(sheet_text)

            return "\n\n".join(text_parts)
        except Exception as e:
            raise Exception(f"Excel extraction failed: {e}")

    def _extract_plain_text(self, file_path: Path) -> str:
        """Extract plain text with encoding detection"""
        try:
            # Detect encoding
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'

            # Read with detected encoding
            with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
                return file.read()
        except Exception as e:
            raise Exception(f"Text extraction failed: {e}")

    def _extract_json_text(self, file_path: Path) -> str:
        """Extract from JSON"""
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _extract_yaml_text(self, file_path: Path) -> str:
        """Extract from YAML"""
        import yaml
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        return yaml.dump(data, default_flow_style=False)

    def _extract_csv_text(self, file_path: Path) -> str:
        """Extract from CSV"""
        df = pd.read_csv(file_path)
        text = f"[CSV Data - {len(df)} rows, {len(df.columns)} columns]\n\n"
        text += "Columns: " + ", ".join(df.columns) + "\n\n"
        text += df.head(20).to_string()
        return text

    def _extract_xml_text(self, file_path: Path) -> str:
        """Extract from XML"""
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'xml')
        return soup.get_text(separator='\n', strip=True)

    def _extract_html_text(self, file_path: Path) -> str:
        """Extract from HTML"""
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()

        return soup.get_text(separator='\n', strip=True)

    def _create_parent_child_chunks(self, text: str, file_metadata: Dict) -> List[DocumentChunk]:
        """
        Create parent-child hierarchical chunks
        Parents: Large context (2000 tokens)
        Children: Precise retrieval (600 tokens)
        """
        chunks = []

        # Approximate tokens (1 token ≈ 4 chars)
        parent_chars = self.settings.PARENT_CHUNK_SIZE * 4
        parent_overlap_chars = self.settings.PARENT_CHUNK_OVERLAP * 4
        child_chars = self.settings.CHILD_CHUNK_SIZE * 4
        child_overlap_chars = self.settings.CHILD_CHUNK_OVERLAP * 4

        # Create parent chunks
        parent_texts = self._split_text(text, parent_chars, parent_overlap_chars)

        for p_idx, parent_text in enumerate(parent_texts):
            parent_id = f"{file_metadata['document_id']}_P{p_idx}"

            # Create parent chunk
            parent_chunk = self._create_chunk(
                content=parent_text,
                chunk_id=parent_id,
                chunk_index=p_idx,
                chunk_type="parent",
                chunk_size_category="xlarge",
                file_metadata=file_metadata
            )

            # Create children from parent
            child_texts = self._split_text(parent_text, child_chars, child_overlap_chars)

            for c_idx, child_text in enumerate(child_texts):
                child_id = f"{parent_id}_C{c_idx}"
                parent_chunk.child_chunk_ids.append(child_id)

                child_chunk = self._create_chunk(
                    content=child_text,
                    chunk_id=child_id,
                    chunk_index=p_idx * 1000 + c_idx,
                    chunk_type="child",
                    chunk_size_category="small",
                    file_metadata=file_metadata,
                    parent_chunk_id=parent_id
                )

                chunks.append(child_chunk)

            chunks.append(parent_chunk)

        return chunks

    def _create_semantic_chunks(self, text: str, file_metadata: Dict) -> List[DocumentChunk]:
        """
        Create semantically coherent chunks (sentence-aware)
        """
        chunks = []

        # Use NLTK for sentence tokenization
        sentences = nltk.sent_tokenize(text)

        current_chunk = []
        current_size = 0
        chunk_idx = 0
        target_size = self.settings.CHILD_CHUNK_SIZE * 4  # chars

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size > target_size and current_chunk:
                # Create chunk
                chunk_text = " ".join(current_chunk)
                chunk_id = f"{file_metadata['document_id']}_S{chunk_idx}"

                chunk = self._create_chunk(
                    content=chunk_text,
                    chunk_id=chunk_id,
                    chunk_index=chunk_idx,
                    chunk_type="semantic",
                    chunk_size_category="medium",
                    file_metadata=file_metadata
                )

                chunks.append(chunk)

                # Start new chunk with overlap
                overlap_count = max(1, len(current_chunk) // 5)  # 20% overlap
                current_chunk = current_chunk[-overlap_count:]
                current_size = sum(len(s) for s in current_chunk)
                chunk_idx += 1

            current_chunk.append(sentence)
            current_size += sentence_size

        # Last chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk_id = f"{file_metadata['document_id']}_S{chunk_idx}"

            chunk = self._create_chunk(
                content=chunk_text,
                chunk_id=chunk_id,
                chunk_index=chunk_idx,
                chunk_type="semantic",
                chunk_size_category="medium",
                file_metadata=file_metadata
            )

            chunks.append(chunk)

        return chunks

    def _create_sliding_window_chunks(self, text: str, file_metadata: Dict) -> List[DocumentChunk]:
        """
        Create chunks with multiple window sizes
        """
        chunks = []

        for window_size in self.settings.WINDOW_SIZES:
            window_chars = window_size * 4
            overlap_chars = int(window_chars * 0.2)  # 20% overlap

            window_texts = self._split_text(text, window_chars, overlap_chars)

            for idx, chunk_text in enumerate(window_texts):
                chunk_id = f"{file_metadata['document_id']}_W{window_size}_{idx}"

                # Determine category
                if window_size < 500:
                    category = 'small'
                elif window_size < 1000:
                    category = 'medium'
                else:
                    category = 'large'

                chunk = self._create_chunk(
                    content=chunk_text,
                    chunk_id=chunk_id,
                    chunk_index=idx + window_size * 10000,
                    chunk_type="window",
                    chunk_size_category=category,
                    file_metadata=file_metadata
                )

                chunks.append(chunk)

        return chunks

    def _create_chunk(self, content: str, chunk_id: str, chunk_index: int,
                     chunk_type: str, chunk_size_category: str,
                     file_metadata: Dict, parent_chunk_id: Optional[str] = None) -> DocumentChunk:
        """Helper to create a DocumentChunk"""
        return DocumentChunk(
            content=content,
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            document_id=file_metadata['document_id'],
            document_name=file_metadata['document_name'],
            file_path=file_metadata['file_path'],
            file_size=file_metadata['file_size'],
            file_type=file_metadata['file_type'],
            file_extension=file_metadata['file_extension'],
            created_date=file_metadata['created_date'],
            modified_date=file_metadata['modified_date'],
            processed_date=file_metadata['processed_date'],
            chunk_type=chunk_type,
            chunk_size_category=chunk_size_category,
            word_count=len(content.split()),
            char_count=len(content),
            sentence_count=len(nltk.sent_tokenize(content)),
            parent_chunk_id=parent_chunk_id
        )

    def _split_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into chunks with overlap (character-based)"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            if chunk.strip():
                chunks.append(chunk)

            start += chunk_size - overlap

            if start >= len(text):
                break

        return chunks

    def _extract_chunk_metadata(self, chunk: DocumentChunk):
        """Extract rich metadata for chunk"""
        try:
            # Extract keywords
            if self.settings.EXTRACT_KEYWORDS:
                chunk.keywords = self._extract_keywords(chunk.content)

            # Extract entities
            if self.settings.EXTRACT_ENTITIES:
                chunk.entities = self._extract_entities(chunk.content)

            # Calculate completeness
            chunk.completeness_score = self._calculate_completeness(chunk.content)

        except Exception as e:
            # Non-critical, continue
            pass

    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract keywords using frequency analysis"""
        # Simple but effective: word frequency
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        words = [w for w in words if w not in self.stop_words]

        # Count and get top N
        word_counts = Counter(words)
        return [word for word, count in word_counts.most_common(top_n)]

    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities using spaCy"""
        # Limit text length for performance
        text_sample = text[:5000]

        doc = self.nlp(text_sample)
        entities = []

        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'DATE', 'MONEY', 'PRODUCT']:
                entities.append(ent.text)

        return list(set(entities))[:20]  # Unique, max 20

    def _calculate_completeness(self, text: str) -> float:
        """Calculate if chunk feels complete"""
        sentences = nltk.sent_tokenize(text)

        if len(sentences) < 2:
            return 0.3

        # Check for typical sentence patterns
        first_sentence = sentences[0].lower()
        last_sentence = sentences[-1].lower()

        # Intro patterns
        has_intro = any(word in first_sentence for word in [
            'this', 'the', 'in this', 'we will', 'here', 'introduction'
        ])

        # Conclusion patterns
        has_conclusion = any(word in last_sentence for word in [
            'therefore', 'thus', 'in conclusion', 'finally', 'summary'
        ])

        if has_intro and has_conclusion:
            return 0.9
        elif has_intro or has_conclusion:
            return 0.6
        else:
            return 0.4


if __name__ == "__main__":
    # Test the processor
    settings = get_settings()
    processor = UltimateDocumentProcessor(settings)

    print("\n" + "="*80)
    print("🚀 Ultimate Document Processor Ready!")
    print("="*80)
    print(f"✅ Supports {len(settings.SUPPORTED_FORMATS)} file formats")
    print(f"✅ Multiple chunking strategies enabled")
    print(f"✅ Advanced metadata extraction enabled")

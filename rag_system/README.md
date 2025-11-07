# 🚀 Ultimate RAG System v2.1

**The Most Advanced Free-Tier RAG System Ever Built!**

A production-ready RAG (Retrieval-Augmented Generation) system that pushes every free tool to its absolute limits. The only paid component is the Claude API - everything else is 100% free!

## ✨ Features

### 🎯 Core Features
- **Multi-Stage Retrieval**: Retrieve 100 chunks → Rerank to 50 → Send top 30 to Claude
- **Parent-Child Chunking**: Small chunks for precision, large parents for context
- **Semantic Chunking**: Sentence-aware splitting that preserves meaning
- **Sliding Window**: Multiple chunk sizes for different perspectives
- **Cross-Encoder Reranking**: Advanced relevance scoring
- **Conversation Memory**: Full conversation history tracking
- **Semantic Caching**: Cache similar queries for speed
- **File & Date Filtering**: Filter by filename and modification date
- **Confidence Scoring**: Know how reliable each answer is

### 📄 Document Support (30+ Formats!)
- **Documents**: PDF, DOCX, PPTX, TXT, MD, RTF
- **Data**: CSV, XLSX, JSON, XML, YAML
- **Code**: PY, JS, TS, JSX, TSX, JAVA, CPP, GO, RS, and more
- **Web**: HTML, HTM
- **Config**: TOML, INI, CONF, ENV

### 🧠 Advanced Metadata Extraction
- **Named Entity Recognition**: Automatically extract people, organizations, locations
- **Keyword Extraction**: Identify key terms in each chunk
- **Language Detection**: Multi-language support
- **File Metadata**: Track filenames, sizes, dates, types
- **Quality Metrics**: Completeness and relevance scoring

### ⚡ Performance Optimizations
- **Batch Processing**: Process multiple files in parallel
- **Embedding Caching**: Cache embeddings for speed
- **Multi-Model Embeddings**: 384-dim for speed, 768-dim for quality
- **Efficient Chunking**: Multiple strategies working together

## 📋 Requirements

- **Python 3.9+**
- **Claude API Key** (from Anthropic) - **REQUIRED**
- **4GB+ RAM** (8GB+ recommended for large document sets)
- **~2GB disk space** for models and data

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or navigate to the rag_system directory
cd rag_system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Claude API key
nano .env  # or use any text editor
```

**REQUIRED**: Add your Claude API key:
```
ANTHROPIC_API_KEY=your_actual_key_here
```

Get your API key from: https://console.anthropic.com/

### 3. Start the System

**Terminal 1 - Backend:**
```bash
cd backend
python -m app.main
```

**Terminal 2 - Frontend:**
```bash
cd frontend
streamlit run app.py
```

The UI will open at: http://localhost:8501

## 📖 Usage

### Uploading Documents

**Method 1: Via UI**
1. Go to "Upload Documents" tab
2. Choose "Upload Files" or "Process Folder"
3. Select your files/folder
4. Click "Process"

**Method 2: Via API**
```python
import requests

# Upload files
files = [('files', open('document.pdf', 'rb'))]
response = requests.post('http://localhost:8000/upload/files', files=files)

# Or process entire folder
response = requests.post('http://localhost:8000/upload/folder',
    json={'folder_path': '/path/to/documents'})
```

### Querying Documents

**Via UI:**
1. Go to "Chat" tab
2. Type your question
3. Optionally filter by specific files
4. Get comprehensive answer with sources!

**Via API:**
```python
import requests

response = requests.post('http://localhost:8000/query', json={
    'question': 'What is the refund policy?',
    'session_id': 'user123',
    'include_history': True,
    'file_filters': ['policy.pdf']  # Optional
})

result = response.json()
print(result['answer'])
print(result['sources'])
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit Frontend                     │
│              (Beautiful UI for testing)                  │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────────────┐
│                   FastAPI Backend                        │
│              (RESTful API endpoints)                     │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                    RAG Chain                             │
│   (Orchestrates document processing and querying)        │
└──────┬───────────────┬──────────────────┬───────────────┘
       │               │                  │
┌──────▼──────┐ ┌─────▼─────┐  ┌────────▼────────┐
│  Document   │ │  Vector   │  │  Claude API      │
│  Processor  │ │  Store    │  │  (Anthropic)     │
│             │ │           │  │                  │
│ • 30+ formats│ │ • ChromaDB│  │ • Sonnet 3.5    │
│ • Chunking  │ │ • Multi-  │  │ • 200K context  │
│ • Metadata  │ │   stage   │  │                  │
│             │ │ • Rerank  │  │                  │
└─────────────┘ └───────────┘  └──────────────────┘
```

## 📊 How It Works

### Document Processing Pipeline

1. **Text Extraction**: Extract text from 30+ file formats
2. **Multi-Strategy Chunking**:
   - **Parent chunks** (2000 tokens): Large context
   - **Child chunks** (600 tokens): Precise retrieval
   - **Semantic chunks**: Sentence-aware
   - **Window chunks**: Multiple sizes
3. **Metadata Extraction**:
   - Named entities (people, organizations, etc.)
   - Keywords and key phrases
   - File metadata (name, type, date, size)
   - Quality metrics
4. **Embedding Generation**: Create vectors using sentence-transformers
5. **Vector Storage**: Store in ChromaDB with metadata

### Query Pipeline

1. **Query Expansion**: Generate variations of user question
2. **STAGE 1 - Wide Retrieval**: Retrieve 100 chunks from vector store
3. **STAGE 2 - Reranking**: Use cross-encoder to rerank to top 50
4. **STAGE 3 - Parent Retrieval**: Get parent chunks for context
5. **Final Selection**: Send top 30 chunks to Claude
6. **Context Building**: Organize chunks by document with metadata
7. **Claude Generation**: Generate comprehensive answer
8. **Answer Grading**: Calculate confidence score
9. **Source Citation**: Include file names and metadata

### Multi-Stage Retrieval Explained

```
User Query: "What is the refund policy?"
      │
      ▼
[Query Expansion]
  ├─ "What is the refund policy?"
  ├─ "what is the refund policy?"
  ├─ "refund policy"
  └─ "How do I get a refund?"
      │
      ▼
[STAGE 1: Wide Net - Retrieve 100 chunks]
  Vector similarity search across all documents
  → 100 potentially relevant chunks
      │
      ▼
[STAGE 2: Reranking - Top 50]
  Cross-encoder scores each chunk vs query
  → 50 most relevant chunks
      │
      ▼
[STAGE 3: Parent Retrieval - Top 30]
  For child chunks, fetch parent for context
  → 30 best chunks + their parents
      │
      ▼
[Send to Claude]
  Build context with ~25,000 tokens
  Claude generates comprehensive answer
      │
      ▼
[Answer with Citations]
  "The refund policy states... [Source: policy.pdf]"
```

## 🎯 Why This is Advanced

### 1. **Parent-Child Chunking**
Most RAG systems use fixed-size chunks. We use **hierarchical chunking**:
- Small child chunks (600 tokens) for precise retrieval
- Large parent chunks (2000 tokens) sent to Claude for context
- **Result**: Precision of small chunks + context of large chunks!

### 2. **Multi-Stage Retrieval with Reranking**
Most systems retrieve 5-10 chunks. We:
- Retrieve 100 chunks initially (cast wide net)
- Rerank using cross-encoder (ML model for relevance)
- Select top 30 for Claude
- **Result**: Much better retrieval quality!

### 3. **Massive Context Utilization**
- Claude 3.5 Sonnet has 200K context window
- We use 180K tokens (90%!)
- Most systems use <5% of context window
- **Result**: Claude sees WAY more information!

### 4. **Comprehensive Metadata**
Track everything:
- File names (know which file info came from)
- Modification dates (know freshness)
- Keywords and entities (better search)
- Quality scores (trust signals)

### 5. **Conversation Memory**
- Remember last 10 exchanges
- Context-aware follow-up questions
- Session management
- **Result**: Natural conversation flow!

## 🔧 Configuration

All configuration in `.env` file. Key settings:

### Retrieval Settings
```
INITIAL_RETRIEVAL_K=100    # How many chunks to retrieve initially
RERANK_TOP_K=50            # How many after reranking
FINAL_TOP_K=30             # How many to send to Claude
```

### Chunking Settings
```
PARENT_CHUNK_SIZE=2000     # Parent chunk size (tokens)
CHILD_CHUNK_SIZE=600       # Child chunk size (tokens)
PARENT_CHUNK_OVERLAP=400   # Overlap for parents
CHILD_CHUNK_OVERLAP=120    # Overlap for children
```

### Features
```
ENABLE_PARENT_CHILD_CHUNKING=true
ENABLE_SEMANTIC_CHUNKING=true
ENABLE_RERANKING=true
ENABLE_CONVERSATION_MEMORY=true
ENABLE_SEMANTIC_CACHE=true
```

## 📈 Performance Tips

### For Large Document Sets (40+ files)
- Increase `MAX_WORKERS=8` for parallel processing
- Enable all chunking strategies for better coverage
- Use file filtering to narrow searches

### For Speed
- Enable `ENABLE_SEMANTIC_CACHE=true` to cache queries
- Reduce `FINAL_TOP_K` to 20 if needed
- Use smaller embedding model

### For Quality
- Increase `FINAL_TOP_K` to 40+ (Claude can handle it!)
- Enable all metadata extraction
- Use query expansion

## 🎓 Technical Details

### Embedding Models (Both Free!)
- **Primary**: `all-MiniLM-L6-v2` (384-dim, fast, 80MB)
- **Secondary**: `all-mpnet-base-v2` (768-dim, quality, 420MB)

### Reranker Model (Free!)
- **Model**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Size**: 90MB
- **Speed**: ~1000 pairs/second on CPU

### Vector Store (Free!)
- **ChromaDB**: Persistent, local, no server needed
- **Storage**: Efficient on-disk storage
- **Search**: Fast HNSW algorithm

### NLP Models (All Free!)
- **spaCy**: `en_core_web_sm` for NER and tokenization
- **NLTK**: Sentence tokenization and stopwords

## 🐛 Troubleshooting

### "Cannot connect to backend"
```bash
# Make sure backend is running
cd backend
python -m app.main
```

### "ANTHROPIC_API_KEY not set"
```bash
# Add your key to .env file
echo "ANTHROPIC_API_KEY=your_key_here" >> .env
```

### "spaCy model not found"
```bash
# Download the model
python -m spacy download en_core_web_sm
```

### "Out of memory"
- Reduce `FINAL_TOP_K`
- Reduce `INITIAL_RETRIEVAL_K`
- Process fewer files at once

## 📝 API Documentation

Full API docs available at: http://localhost:8000/docs (when backend is running)

### Key Endpoints

- `POST /upload/files` - Upload multiple files
- `POST /upload/folder` - Process entire folder
- `POST /query` - Query with a question
- `GET /documents` - List indexed documents
- `GET /statistics` - System statistics
- `DELETE /vector-store` - Clear all documents

## 🎯 Use Cases

- **Customer Support**: Query product manuals, policies
- **Research**: Search through papers and reports
- **Code Documentation**: Search code repos and docs
- **Legal**: Query contracts and agreements
- **Education**: Search textbooks and course materials
- **Business Intelligence**: Query reports and data

## 💰 Cost Analysis

### Free Components (100% of system):
- ChromaDB: FREE
- Sentence Transformers: FREE
- Document processing libraries: FREE
- spaCy & NLTK: FREE
- FastAPI: FREE
- Streamlit: FREE
- All ML models: FREE

### Paid Component (Only Cost):
- **Claude API**: ~$3 per million input tokens, ~$15 per million output tokens
- **Typical query**: 25K input + 1K output = ~$0.08 per query
- **Monthly (1000 queries)**: ~$80

## 🚀 Deployment

### Local Development
Already covered above! Just run backend + frontend.

### Docker (Coming Soon)
```bash
docker-compose up
```

### Cloud Deployment
Can be deployed to:
- **Railway**: Easy one-click deploy
- **Heroku**: Free tier available
- **AWS/GCP**: Full control
- **DigitalOcean**: Simple VPS

## 🤝 Contributing

This is a proof-of-concept of what's possible with free-tier tools. Feel free to:
- Add more file format support
- Improve chunking strategies
- Add more metadata extraction
- Optimize performance
- Add new features

## 📄 License

MIT License - Use freely!

## 🙏 Acknowledgments

Built with amazing open-source tools:
- Anthropic Claude API
- ChromaDB
- Sentence Transformers
- spaCy
- FastAPI
- Streamlit

---

**Built with ❤️ to prove that advanced RAG doesn't need expensive tools!**

🚀 **The most advanced free-tier RAG system in existence!**

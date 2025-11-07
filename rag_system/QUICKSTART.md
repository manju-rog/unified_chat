# 🚀 Quick Start Guide - Ultimate RAG System v2.1

Get up and running in 5 minutes!

## Prerequisites
- Python 3.9 or higher
- Claude API key from https://console.anthropic.com/

## Installation

```bash
# 1. Navigate to directory
cd rag_system

# 2. Run setup script (installs everything)
./setup.sh

# 3. Add your Claude API key to .env
nano .env  # Add: ANTHROPIC_API_KEY=your_key_here
```

## Start the System

```bash
# Start both backend and frontend
./start.sh
```

The system will open at: **http://localhost:8501**

## First Steps

### 1. Upload Documents
- Click "Upload Documents" tab
- Choose "Process Folder"
- Enter your folder path (e.g., `/path/to/your/docs`)
- Click "Process Folder"
- Wait for processing to complete

### 2. Ask Questions
- Go to "Chat" tab
- Type your question
- Get comprehensive answer with sources!

## Example Use Case

**Scenario**: You have 30 PDF files about company policies

```bash
# 1. Upload the folder
Go to Upload Documents → Process Folder → /path/to/policies/ → Process

# 2. Ask questions
"What is the vacation policy?"
"How do I submit an expense report?"
"What are the work from home guidelines?"
```

The system will:
1. Search across all 30 PDFs
2. Find the most relevant sections
3. Combine information from multiple files
4. Give you a comprehensive answer with citations
5. Show which files the answer came from

## Advanced Features

### File Filtering
```
In Chat → Advanced Filters → Select specific files
Only searches those files
```

### Conversation Memory
```
The system remembers your conversation
Ask follow-up questions naturally
"Tell me more about that"
"What about remote work?"
```

### View Statistics
```
Analytics tab → See:
- How many documents indexed
- How many chunks created
- System configuration
```

## Troubleshooting

### Backend won't start?
```bash
# Check if port 8000 is available
lsof -i :8000

# Start manually
cd backend
python -m app.main
```

### Frontend won't start?
```bash
# Check if port 8501 is available
lsof -i :8501

# Start manually
cd frontend
streamlit run app.py
```

### "Claude API error"?
```bash
# Check your API key in .env
cat .env | grep ANTHROPIC_API_KEY

# Make sure it's set correctly
```

## Manual Start (Alternative)

If `./start.sh` doesn't work:

**Terminal 1 - Backend:**
```bash
cd backend
source ../venv/bin/activate  # On Windows: ..\venv\Scripts\activate
python -m app.main
```

**Terminal 2 - Frontend:**
```bash
cd frontend
source ../venv/bin/activate  # On Windows: ..\venv\Scripts\activate
streamlit run app.py
```

## What Makes This System Special?

1. **Handles 30-40 files effortlessly** - Upload entire folders
2. **Knows filenames and context** - Tracks which file each answer comes from
3. **Date-aware** - Knows when files were modified
4. **Multi-stage retrieval** - Retrieves 100 chunks, reranks, sends top 30 to Claude
5. **Parent-child chunks** - Small chunks for search, large chunks for context
6. **Conversation memory** - Remembers your chat history
7. **All free tier!** - Only pay for Claude API

## API Usage (For Developers)

```python
import requests

# Upload documents
response = requests.post('http://localhost:8000/upload/folder',
    json={'folder_path': '/path/to/docs'})

# Query
response = requests.post('http://localhost:8000/query',
    json={
        'question': 'What is the refund policy?',
        'session_id': 'user123'
    })

print(response.json()['answer'])
```

## Next Steps

1. Upload your documents
2. Start asking questions
3. Explore advanced features
4. Check out the full README.md for details

## Need Help?

- Check README.md for detailed documentation
- API docs: http://localhost:8000/docs
- Configuration: Edit .env file

---

**That's it! You now have the most advanced free-tier RAG system running!** 🚀

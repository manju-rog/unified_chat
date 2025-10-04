# 🤖 Unified AI Chat Interface

A single, intelligent chat interface that seamlessly handles both **Absence Management** and **SOW Generation** using Gemini AI for intent classification and natural language understanding.

## ✨ Features

### 🎯 Intelligent Intent Detection
- Automatically understands whether you want to manage absences or generate SOWs
- No need to switch between applications
- Context-aware conversations

### 💬 Natural Language Processing
- Talk naturally - no rigid commands
- AI extracts relevant information from your messages
- Maintains conversation context

### 📊 Dual Application Support

#### 1. Absence Management
- Mark employees absent/present/vacation
- Query absence records
- View attendance reports
- All through natural conversation

#### 2. SOW Generation
- Create professional Statement of Work documents
- Step-by-step guided process
- AI-powered content generation
- Download ready-to-use documents

### 🔄 Session Management
- Persistent conversation history
- Context maintained across messages
- Seamless switching between tasks

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+** with pip
2. **Node.js 18+** with npm
3. **Gemini API Key** from [Google AI Studio](https://makersuite.google.com/app/apikey)
4. **Running Absence Management Backend** (Spring Boot on port 8080)

### Installation

#### 1. Backend Setup (FastAPI Orchestrator)

```bash
cd unified_ai_chat/backend

# Install Python dependencies
pip install -r requirements.txt

# Create .env file with Gemini + downstream service settings
cat > .env <<'EOF'
GEMINI_API_KEY=your-gemini-api-key-here
ABSENCE_API_URL=http://localhost:8080/api
SOW_PROJECT_PATH=../../sow_gen_ai
SOW_TEMPLATE_PATH="../../sow_gen_ai/G-COP SOW v1.0_CLEAN.docx"
EOF

# Start FastAPI orchestrator
uvicorn app.main:app --reload --port 8000
```

Backend will run on: `http://localhost:8000`

#### 2. Frontend Setup

```bash
cd unified_ai_chat/frontend

# Install dependencies
npm install

# Create .env file pointing to the FastAPI backend
cat > .env <<'EOF'
REACT_APP_API_URL=http://localhost:8000/api
EOF

# Start the React app
npm start
```

Frontend will open at: `http://localhost:3000`

### 3. Start Required Services

Make sure these are running:

```bash
# Terminal 1: Absence Management Backend (Spring Boot)
cd ai_absence-ai_absence_mi/backend/absence-management
./mvnw spring-boot:run

# Terminal 2: Unified Chat Backend (FastAPI)
cd unified_ai_chat/backend
uvicorn app.main:app --reload --port 8000

# Terminal 3: Unified Chat Frontend (React)
cd unified_ai_chat/frontend
npm start
```

### Configuration Reference

The FastAPI orchestrator reads the following settings from `.env` (or the environment):

- `GEMINI_API_KEY` – required Google Gemini key.
- `GEMINI_MODEL` – override to use a different Gemini model (default `models/gemini-1.5-pro-latest`).
- `ABSENCE_API_URL` – base URL of the Spring Boot absence management API (`http://localhost:8080/api`).
- `SOW_PROJECT_PATH` – path to the `sow_gen_ai` project used for document generation.
- `SOW_TEMPLATE_PATH` – absolute path to the default SOW template.
- `SOW_OUTPUT_DIR` – where generated DOCX files are stored (`backend/generated_docs` by default).
- `SESSION_HISTORY_LIMIT` – number of recent turns shared with Gemini (default 10).
- `SESSION_EXPIRY_MINUTES` – minutes of inactivity before session cleanup (default 60).

## 💡 Usage Examples

### Absence Management

**Mark someone absent:**
```
You: "Mark Manju absent today"
AI: ✅ Got it! I've marked Manju as Absent for October 3, 2025.
```

**Query absences:**
```
You: "Who was absent yesterday?"
AI: Here's who was absent on October 2, 2025:
    - John (Absent)
    - Sarah (Vacation)
```

**Natural variations work too:**
```
You: "Manju won't be in today"
AI: I understand - marking Manju as absent for today!
```

### SOW Generation

**Start SOW creation:**
```
You: "I need to create a Statement of Work"
AI: Great! Let's create a SOW document. Tell me about your project:
    - Project Name
    - Project ID
    - Main Objectives
```

**Continue conversation:**
```
You: "It's a cloud migration project for ABC Corp, 
      migrating 50 applications to AWS"
AI: Perfect! I've noted the project details.
    Next, what services will be provided?
```

**Complete and download:**
```
AI: ✅ Your SOW document is ready!
    [Download Button]
```

### Mixed Conversations

The AI intelligently switches context:

```
You: "Mark John absent today"
AI: ✅ Marked John as absent for October 3, 2025.

You: "Also, I need to create a SOW for a new project"
AI: Sure! Let's start the SOW. Tell me about your project...

You: "Wait, who else is absent today?"
AI: Let me check the absences for today...
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   React Frontend                            │
│  - UnifiedChat.jsx                                         │
│  - Conversational UI + download controls                   │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/JSON
┌─────────────────────────────────────────────────────────────┐
│            FastAPI Orchestrator (backend/app)               │
│  - main.py: /api/chat, health, document download           │
│  - gemini_client.py: system prompt + Gemini tools          │
│  - services/absence.py: Spring Boot adapter                │
│  - services/sow.py: ConversationalSOWGenerator bridge      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Spring Boot Absence API  │  sow_gen_ai Python toolkit      │
└─────────────────────────────────────────────────────────────┘
```

## 📡 API Endpoints

- `POST /api/chat` – Send a user message (optionally with `session_id`) and receive the assistant reply + action metadata.
- `GET /api/health` – Lightweight health and configuration check.
- `GET /api/sow/documents/{sessionId}/{filename}` – Download SOW documents generated in a chat session.

## 🎨 UI Highlights

- Welcome message with quick actions for common absence and SOW tasks.
- Automatic scrolling, typing indicator, and contextual download button injection.
- Error banner when the backend call fails.

## 🧪 Verification

1. Start the Spring Boot absence backend (`./mvnw spring-boot:run`).
2. Launch the FastAPI orchestrator (`uvicorn app.main:app --reload --port 8000`).
3. Run the React dev server (`npm start`).
4. Chat flows to verify:
   - “Mark Jane absent tomorrow” → absence update confirmation.
   - “Show this week's absences” → formatted report.
   - “Create a SOW document for …” → multi-step flow ending with download link.

If you update code, you can sanity-check the backend with `python -m compileall app` and hit `/api/health` to confirm configuration.

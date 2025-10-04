# 🚀 Start Gemini Orchestrator

## Quick Start (2 Terminals)

### Terminal 1: Start Backend
```bash
cd gemini-orchestrator/backend
uvicorn app.main:app --reload --port 8000
```

Wait until you see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Terminal 2: Start Frontend
```bash
cd gemini-orchestrator/frontend
npm run dev
```

Wait until you see:
```
  ▲ Next.js 14.x.x
  - Local:        http://localhost:3000
  - Ready in X.Xs
```

### Open Browser
Navigate to: **http://localhost:3000**

---

## What You'll See

### 1. Chat Interface
- Clean, modern chat UI
- Mode indicator at top (IDLE/ABSENCE/SOW)
- Message input at bottom
- Real-time responses from Gemini AI

### 2. Try These Commands

#### Absence Management
```
mark manju absent today because of sick leave
```
Expected: Tool execution, confirmation message

```
is john absent today?
```
Expected: Status check response

```
mark sarah present today
```
Expected: Presence confirmation

#### SOW Generation
```
generate sow for Predictive Maintenance System
```
Expected: Multi-turn conversation to collect info

The AI will ask you for:
- Oracle representative details
- Billing contact
- Services to be provided
- Timeline
- Deliverables

Then it will generate a DOCX file with download link.

#### Out-of-Scope (Should Refuse)
```
what's the weather?
```
Expected: Polite refusal message

```
tell me a joke
```
Expected: Explanation of capabilities

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (localhost:3000)                  │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Next.js Chat Interface                      │    │
│  │  • Message display                                  │    │
│  │  • Mode indicator                                   │    │
│  │  • Tool result cards                                │    │
│  └────────────────────────────────────────────────────┘    │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTP POST /api/chat
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (localhost:8000)                │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Orchestrator                           │    │
│  │  1. Domain Router → IDLE/ABSENCE/SOW               │    │
│  │  2. Session Manager → State & History              │    │
│  │  3. Gemini Service → AI Processing                 │    │
│  │  4. Tool Executor → Action Execution               │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────┐  ┌──────────────────┐                │
│  │ Absence Tools   │  │   SOW Tools      │                │
│  │ • mark_absent   │  │ • start_sow      │                │
│  │ • mark_present  │  │ • update_sow     │                │
│  │ • get_status    │  │ • generate_sow   │                │
│  └─────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                   Google Gemini API
                   (AI Processing)
```

---

## Features You'll Experience

### ✓ Intelligent Domain Routing
The system automatically detects whether you're talking about:
- Absence management (keywords: absent, present, leave, sick)
- SOW generation (keywords: sow, statement of work, generate, document)
- Out-of-scope (everything else → polite refusal)

### ✓ Session State Management
- Your conversation is tracked across messages
- Mode persists (if you're in SOW mode, follow-up questions stay in SOW)
- Information is collected incrementally
- Session ID stored in browser localStorage

### ✓ Tool Execution
- When Gemini decides an action is needed, it calls a tool
- Tools execute via validated REST endpoints
- Results are returned to the UI
- Confirmation cards show what happened

### ✓ Multi-Turn Conversations
For SOW generation, the AI will:
1. Start a SOW session
2. Ask for missing information one piece at a time
3. Collect all required fields
4. Generate the document
5. Provide download link

---

## Troubleshooting

### Backend won't start
- Check if port 8000 is already in use: `lsof -i :8000`
- Verify `.env` file exists with `GEMINI_API_KEY`
- Check Python dependencies: `pip install -r requirements.txt`

### Frontend won't start
- Check if port 3000 is already in use: `lsof -i :3000`
- Verify node_modules installed: `npm install`
- Check `.env.local` has `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`

### "Connection failed" errors
- Make sure backend is running first
- Check backend health: `curl http://localhost:8000/health`
- Look at backend logs for errors

### Gemini API errors
- Verify your API key is valid
- Check you have API quota remaining
- Look for rate limit messages in backend logs

---

## API Endpoints (for testing)

### Health Check
```bash
curl http://localhost:8000/health
```

### Orchestrator (main endpoint)
```bash
curl -X POST http://localhost:8000/orchestrator \
  -H "Content-Type: application/json" \
  -d '{"text": "mark john absent today", "session_id": "test123"}'
```

### Absence - Mark Absent
```bash
curl -X POST http://localhost:8000/absence/mark_absent \
  -H "Content-Type: application/json" \
  -d '{"employee_id": "john", "date": "2025-10-03", "reason": "sick"}'
```

### Absence - Check Status
```bash
curl http://localhost:8000/absence/status/john?date=2025-10-03
```

### API Documentation
Open in browser: http://localhost:8000/docs

---

## Logs and Debugging

### View Backend Logs
The backend will show:
- Incoming requests
- Domain routing decisions
- Gemini API calls and responses
- Tool executions
- Session state updates

### View Frontend Logs
The frontend will show:
- User messages sent
- API responses received
- State updates
- Rendering events

### Check Browser Console
Open DevTools (F12) to see:
- Network requests to `/api/chat`
- Frontend state changes
- Any JavaScript errors

---

## Example Session Flow

```
You: hi
AI: Hello! I can help you with Absence Management and SOW Generation.

You: mark manju absent today because of sick leave
AI: [Executes mark_absent tool]
    I've marked manju as absent on 2025-10-03 for sick leave.
    [Shows green confirmation card]

You: generate sow for Predictive Maintenance
AI: [Enters SOW mode]
    I'll help you create a SOW for Predictive Maintenance.
    Who is the Oracle representative?

You: John Doe, john@oracle.com, 555-1234
AI: Got it. Who is the billing contact?

You: Jane Smith, jane@client.com
AI: Perfect. What services will be provided?

You: AI model development and deployment
AI: Great. What's the timeline?

You: 6 months
AI: And what are the key deliverables?

You: Trained model, API, documentation
AI: [Executes generate_sow tool]
    All information collected! Generating your SOW document...
    Download: http://localhost:8000/files/sow_abc123.docx
    [Shows download link card]
```

---

## Stop the Servers

Press `Ctrl+C` in each terminal window to stop the servers gracefully.

---

## Next Steps

1. **Start both servers** (see Quick Start above)
2. **Open http://localhost:3000** in your browser
3. **Try the example commands** to see the system in action
4. **Explore the API docs** at http://localhost:8000/docs
5. **Check the logs** to understand the flow

---

## 🎉 Enjoy Your Gemini Orchestrator!

The system is fully integrated and ready to use. All tests pass, all components are wired together, and the AI is ready to help with Absence Management and SOW Generation.

**Have fun exploring!** 🚀

# 🚀 System is Running!

Both services are now live and ready for testing with your real Gemini API key.

## Services Status

✅ **Spring Boot Absence Service**
- URL: http://localhost:8080
- PID: Check with `ps aux | grep spring-boot`
- Log: `spring-boot.log`

✅ **FastAPI Orchestrator**
- URL: http://localhost:8000
- PID: Check with `ps aux | grep uvicorn`
- Log: `fastapi.log`

✅ **React Frontend**
- URL: http://localhost:3000
- PID: Check with `ps aux | grep react-scripts`
- Log: `react.log`

## Quick Test Commands

### 1. Test Absence Management

```bash
# Who is absent today?
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-1", "message": "Who is absent today?"}'

# Mark someone absent
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-2", "message": "Mark Shreyas absent today"}'

# Query by date
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-3", "message": "Show me absences for this week"}'
```

### 2. Test SOW Generation (8-Step Flow)

```bash
# Step 1: Start SOW
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "sow-1", "message": "Create a SOW for a mobile app project"}'

# Step 2: Services
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "sow-1", "message": "iOS and Android development, API integration"}'

# Step 3: Deliverables
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "sow-1", "message": "Mobile apps, backend API, documentation"}'

# Step 4: Timeline
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "sow-1", "message": "6 months, starting next month"}'

# Step 5: Resources
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "sow-1", "message": "2 mobile developers, 1 backend developer, 1 QA"}'

# Step 6: Contacts
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "sow-1", "message": "John Smith, john@company.com"}'

# Step 7: Budget
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "sow-1", "message": "$150,000 total budget"}'

# Step 8: Finalize (generates DOCX)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "sow-1", "message": "finalize"}'
```

The final response will include a `download_url` like:
```
/api/sow/documents/sow-1/Generated_SOW_20251004_193000.docx
```

Download it with:
```bash
curl -O http://localhost:8000/api/sow/documents/sow-1/Generated_SOW_20251004_193000.docx
```

## Health Check

```bash
curl http://localhost:8000/api/health
```

## Stop the System

```bash
# Kill Spring Boot
pkill -f "spring-boot:run"

# Kill FastAPI
pkill -f "uvicorn app.main:app"

# Kill React Frontend
pkill -f "react-scripts start"
```

Or use CTRL+C in the terminals where they're running.

## Logs

View real-time logs:
```bash
# Spring Boot
tail -f spring-boot.log

# FastAPI
tail -f fastapi.log

# React Frontend
tail -f react.log
```

## Environment

- Gemini API Key: Loaded from `sow_gen_ai/.env`
- Database: SQLite at `ai_absence-ai_absence_mi/abscent.db`
- SOW Template: `sow_gen_ai/G-COP SOW v1.0_CLEAN.docx`
- Output Directory: `sow_gen_ai/out/`

## What's Working

✅ Database-backed absence management (mark, query, list)
✅ Full 8-step SOW generation workflow
✅ DOCX document generation with proper formatting
✅ Session management across conversations
✅ **Gemini 2.0 Flash** AI integration with structured function calling
✅ **Employee context** in every request for smart name matching
✅ **Typo handling** - "gansh" → "Did you mean Ganesh?"
✅ **Clear date formatting** - Shows WHO was absent on WHICH date
✅ **Detailed reports** - Month/range queries show day-by-day breakdown
✅ CORS enabled for frontend integration

## Next Steps

1. Test with your React UI at `unified_ai_chat/frontend`
2. Try complex queries like "Who was absent last week?"
3. Generate a complete SOW document end-to-end
4. Verify the downloaded DOCX has proper formatting

Enjoy! 🎉

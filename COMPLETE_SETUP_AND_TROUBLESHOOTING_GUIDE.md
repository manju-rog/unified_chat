# Complete Setup and Troubleshooting Guide

## 🤖 For AI Assistants (Kiro, Claude, ChatGPT, etc.)

**If you're an AI assistant helping with this project, READ THIS FIRST:**

### Quick Context Check
Before making any changes, verify:
1. **What services exist:** Run `ls -la` in project root to see directories
2. **What's currently running:** Run `lsof -i :8010,8002,8001,3001` to check active services
3. **Current configuration:** Check these files for port numbers:
   - `unified_ai_chat/backend/app/main.py` (line ~1293) - Should be port 8002
   - `new_sow/run_backend_8002.py` (line 11) - Should be port 8002
   - `unified_ai_chat/backend/run_server.py` (line 8) - Should be port 8001
   - `unified_ai_chat/frontend/package.json` (line 8) - Should be PORT=3001

### Critical Rules for AI Assistants
1. **NEVER change port 8002 to 8000** - new_sow runs on 8002, NOT 8000
2. **NEVER suggest using use_sow** - We use `new_sow` (not use_sow)
3. **NEVER add Claude/Anthropic** - System uses Gemini only
4. **ALWAYS check what's running first** before starting services
5. **ALWAYS verify .env files exist** before starting backends

### How to Help Users Start the System

**Step 1: Check Current State**
```bash
# See what's running
lsof -i :8010,8002,8001,3001

# If nothing is running, proceed to Step 2
# If services are running, ask user if they want to restart
```

**Step 2: Verify Prerequisites**
```bash
# Check if required files exist
ls -la new_sow/.env                          # Must exist with GEMINI_API_KEY
ls -la unified_ai_chat/backend/.env          # Must exist with GEMINI_API_KEY
ls -la new_sow/sample_sow_template.docx      # Must exist
ls -la ai_absence-ai_absence_mi/backend/absence-management/mvnw  # Must exist
```

**Step 3: Start Services Using Kiro's controlBashProcess**
```javascript
// Start in this order:
1. controlBashProcess("start", "ai_absence-ai_absence_mi/backend/absence-management", "./mvnw spring-boot:run")
2. controlBashProcess("start", "new_sow", "python run_backend_8002.py")
3. controlBashProcess("start", "unified_ai_chat/backend", "python run_server.py")
4. controlBashProcess("start", "unified_ai_chat/frontend", "npm start")
```

**Step 4: Verify Services Started**
```bash
# Wait 10-15 seconds, then check:
curl http://localhost:8010/api/ai/employees  # Should return JSON
curl http://localhost:8002/health            # Should return {"status":"healthy"}
curl http://localhost:8001/api/health        # Should return health status
curl http://localhost:3001                   # Should return HTML
```

### Common User Requests and How to Handle Them

**User says: "Start all services"**
→ Use the script: `./unified_ai_chat/start_all_different_ports.sh`
→ OR start each service individually as shown in Step 3 above

**User says: "It's not working" or "I'm getting errors"**
→ Ask: "What error message are you seeing?"
→ Check logs: `tail -f /tmp/*-backend-*.log`
→ Check if services are running: `lsof -i :8010,8002,8001,3001`

**User says: "Port 8000 error"**
→ This means unified backend is trying to connect to wrong port
→ Check `unified_ai_chat/backend/app/main.py` line ~1293
→ Should be: `new_sow_url = "http://localhost:8002/api/generate-direct"`
→ NOT: `new_sow_url = "http://localhost:8000/api/generate-direct"`

**User says: "Gemini error" or "Data extraction failed"**
→ Check if GEMINI_API_KEY is set in `.env` files
→ Verify key is valid: `curl "https://generativelanguage.googleapis.com/v1/models?key=<KEY>"`
→ Check new_sow logs for detailed error

**User says: "Template not found"**
→ Check: `ls -la new_sow/sample_sow_template.docx`
→ If missing: `cp new_sow/templates/doc_*.docx new_sow/sample_sow_template.docx`

### What NOT to Do
❌ Don't suggest changing ports without checking current configuration
❌ Don't suggest using `use_sow` - we use `new_sow`
❌ Don't add Claude/Anthropic imports - system uses Gemini only
❌ Don't start services without checking if they're already running
❌ Don't modify code without understanding the full context

### File Structure Reference
```
project/
├── ai_absence-ai_absence_mi/backend/absence-management/  # Port 8010
├── new_sow/                                              # Port 8002
│   ├── run_backend_8002.py
│   ├── .env (GEMINI_API_KEY)
│   └── sample_sow_template.docx
├── unified_ai_chat/
│   ├── backend/                                          # Port 8001
│   │   ├── run_server.py
│   │   ├── .env (GEMINI_API_KEY)
│   │   └── app/main.py (line ~1293: port 8002 config)
│   └── frontend/                                         # Port 3001
│       └── package.json (PORT=3001)
└── COMPLETE_SETUP_AND_TROUBLESHOOTING_GUIDE.md (this file)
```

---

## System Overview

This unified AI chat system integrates three main components:
1. **Absence Management Service** (Port 8010) - Java Spring Boot
2. **new_sow Backend** (Port 8002) - Python FastAPI for SOW generation
3. **Unified AI Chat** (Port 8001 backend, Port 3001 frontend) - React + Python orchestrator

All services use **Gemini AI** (no Claude/Anthropic).

---

## Problems We Encountered and Solutions

### Problem 1: Wrong Port Configuration
**Issue:** Unified chat backend was trying to connect to new_sow on port 8000, but new_sow runs on port 8002.

**Error Message:**
```
Cannot connect to host localhost:8000 ssl:default [Errno 61] Connect call failed
```

**Solution:**
Changed hardcoded port in `unified_ai_chat/backend/app/main.py`:
```python
# OLD (WRONG):
new_sow_url = "http://localhost:8000/api/generate-direct"

# NEW (CORRECT):
new_sow_url = "http://localhost:8002/api/generate-direct"
```

**Files Modified:**
- `unified_ai_chat/backend/app/main.py` (line ~1293)
- `unified_ai_chat/backend/test_full_sow_generation.py` (lines 84, 91)

---

### Problem 2: Gemini Function Calling Error
**Issue:** new_sow's data extraction was failing because Gemini sometimes returns text instead of function calls, causing IndexError.

**Error Message:**
```
IndexError: list index out of range
function_call = response.candidates[0].content.parts[0].function_call
```

**Root Cause:** 
The code assumed Gemini would always return a function call, but sometimes it returns empty parts or text responses.

**Solution:**
Added proper error handling in `new_sow/app/agents/data_collector_v2.py`:
```python
# Check if response has parts
if not response.candidates[0].content.parts:
    logger.error("No parts in Gemini response")
    return False

# Check if first part has function_call
first_part = response.candidates[0].content.parts[0]
if not hasattr(first_part, 'function_call') or not first_part.function_call:
    logger.error("No function_call in response")
    return False
```

**Files Modified:**
- `new_sow/app/agents/data_collector_v2.py` (lines ~420-440)

---

## Complete Startup Guide

### Prerequisites Check

```bash
# Check Java (required for Absence Management)
java -version
# Should show Java 11 or higher

# Check Python (required for backends)
python3 --version
# Should show Python 3.8 or higher

# Check Node.js (required for frontend)
node --version
npm --version
# Should show Node 14 or higher
```

---

### Step 1: Start Absence Management Service (Port 8010)

```bash
cd ai_absence-ai_absence_mi/backend/absence-management
./mvnw spring-boot:run
```

**Verification:**
```bash
curl http://localhost:8010/api/ai/employees
# Should return JSON with employee list
```

**Expected Output:**
```json
{"success":true,"message":"Employees retrieved successfully","data":[...]}
```

---

### Step 2: Start new_sow Backend (Port 8002)

```bash
cd new_sow
python run_backend_8002.py
```

**Verification:**
```bash
curl http://localhost:8002/health
# Should return: {"status":"healthy"}

curl http://localhost:8002/
# Should return API info with version
```

**Expected Output:**
```json
{
  "application": "SOW Generator API",
  "version": "1.0.0",
  "status": "running"
}
```

**Important Files to Check:**
- `new_sow/.env` - Must contain valid `GEMINI_API_KEY`
- `new_sow/sample_sow_template.docx` - Template file must exist

---

### Step 3: Start Unified Chat Backend (Port 8001)

```bash
cd unified_ai_chat/backend
python run_server.py
```

**Verification:**
```bash
curl http://localhost:8001/api/health
# Should return health status with service URLs
```

**Expected Output:**
```json
{
  "status": "ok",
  "time": "2025-10-30T...",
  "absence_api": "http://localhost:8010/api",
  "sow_template": "..."
}
```

**Important Files to Check:**
- `unified_ai_chat/backend/.env` - Should contain `GEMINI_API_KEY`
- Verify it connects to port 8002 (not 8000)

---

### Step 4: Start Unified Chat Frontend (Port 3001)

```bash
cd unified_ai_chat/frontend
npm start
```

**Note:** The frontend is configured to run on port 3001 (see `package.json`):
```json
"scripts": {
  "start": "PORT=3001 react-scripts start"
}
```

**Verification:**
Open browser to: http://localhost:3001

**Expected:** React app loads with chat interface

---

## Quick Start Script

Use the provided startup script:

```bash
cd unified_ai_chat
./start_all_different_ports.sh
```

This script will:
1. Check prerequisites (Java, Python, npm)
2. Check if ports are available
3. Start all services in order
4. Wait for each service to be ready
5. Open browser automatically

---

## Stopping All Services

### Option 1: Use Stop Script
```bash
cd unified_ai_chat
./stop_all_different_ports.sh
```

### Option 2: Manual Stop
```bash
# Find processes by port
lsof -ti:8010 | xargs kill  # Absence Management
lsof -ti:8002 | xargs kill  # new_sow
lsof -ti:8001 | xargs kill  # Unified Backend
lsof -ti:3001 | xargs kill  # Frontend
```

### Option 3: Kill by PID files
```bash
kill $(cat /tmp/absence-backend-8010.pid)
kill $(cat /tmp/use-sow-backend-8002.pid)
kill $(cat /tmp/unified-backend-8001.pid)
kill $(cat /tmp/unified-frontend-3001.pid)
```

---

## Port Configuration Summary

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| Absence Management | 8010 | HTTP | Employee absence tracking |
| new_sow Backend | 8002 | HTTP | SOW document generation |
| Unified Chat Backend | 8001 | HTTP | Main orchestrator |
| Unified Chat Frontend | 3001 | HTTP | React UI |

**Critical:** Unified chat backend MUST connect to port 8002 for new_sow.

---

## Configuration Files to Verify

### 1. new_sow/.env
```bash
GEMINI_API_KEY=AIzaSy...  # Must be valid
GEMINI_MODEL=gemini-2.5-flash
DEBUG=True
```

### 2. unified_ai_chat/backend/.env
```bash
GEMINI_API_KEY=AIzaSy...  # Must be valid (can be same as new_sow)
```

### 3. unified_ai_chat/frontend/.env
```bash
REACT_APP_API_URL=http://localhost:8001
```

### 4. unified_ai_chat/frontend/package.json
```json
"scripts": {
  "start": "PORT=3001 react-scripts start"
}
```

---

## Testing the System

### Test 1: Absence Management
```bash
# Mark someone absent
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test123",
    "message": "Mark Manju absent today"
  }'
```

### Test 2: SOW Generation (Direct API)
```bash
cd new_sow
python test_complete_sow.py
```

**Expected:** Document generated in `new_sow/output/`

### Test 3: Full Integration via UI
1. Open http://localhost:3001
2. Type: "I want to create a SOW"
3. Follow the wizard through 7 steps
4. Click "Generate SOW Document"
5. Document should be generated and downloadable

---

## Common Issues and Solutions

### Issue: "Port already in use"
**Solution:**
```bash
# Find what's using the port
lsof -i :8002

# Kill the process
kill -9 <PID>
```

### Issue: "Cannot connect to new_sow"
**Check:**
1. Is new_sow running? `curl http://localhost:8002/health`
2. Is unified backend pointing to port 8002? Check `unified_ai_chat/backend/app/main.py` line ~1293
3. Restart unified backend after fixing

### Issue: "Gemini API error"
**Check:**
1. Is API key valid? Test with: `curl https://generativelanguage.googleapis.com/v1/models?key=YOUR_KEY`
2. Is key in `.env` files?
3. Did you restart services after adding key?

### Issue: "Data extraction failed"
**Check:**
1. new_sow logs: `tail -f /tmp/use-sow-backend-8002.log`
2. Look for "No function_call in response" - means Gemini returned text instead
3. Usually resolves on retry

### Issue: "Template not found"
**Check:**
```bash
# Verify template exists
ls -la new_sow/sample_sow_template.docx

# If missing, copy from templates folder
cp new_sow/templates/doc_*.docx new_sow/sample_sow_template.docx
```

---

## Log Files Location

All services write logs to `/tmp/`:

```bash
# View logs in real-time
tail -f /tmp/absence-backend-8010.log
tail -f /tmp/use-sow-backend-8002.log
tail -f /tmp/unified-backend-8001.log
tail -f /tmp/unified-frontend-3001.log
```

---

## Architecture Flow

```
User Browser (http://localhost:3001)
    ↓
React Frontend (Port 3001)
    ↓ HTTP POST /api/chat
Unified Chat Backend (Port 8001)
    ↓
    ├─→ Absence Management (Port 8010) - for absence queries
    │   └─→ Returns employee data
    │
    └─→ new_sow Backend (Port 8002) - for SOW generation
        └─→ Gemini AI (function calling)
            └─→ Generates .docx document
                └─→ Saved to new_sow/output/
                    └─→ Copied to generated_docs_sow/
```

---

## Key Code Locations

### Port Configuration
- `unified_ai_chat/backend/app/main.py` line ~1293
- `unified_ai_chat/backend/run_server.py` line 8
- `new_sow/run_backend_8002.py` line 11
- `unified_ai_chat/frontend/package.json` line 8

### Gemini Integration
- `new_sow/app/agents/data_collector_v2.py` - Function calling
- `unified_ai_chat/backend/app/gemini_client.py` - Unified chat Gemini client

### SOW Generation
- `new_sow/app/api/direct_generation.py` - Direct API endpoint
- `unified_ai_chat/backend/app/services/new_sow_adapter.py` - Integration adapter

---

## Success Indicators

When everything is working correctly, you should see:

1. **Absence Management (8010):**
   ```
   Started AbsenceManagementApplication in X.XXX seconds
   ```

2. **new_sow (8002):**
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8002
   Starting SOW Generator API...
   Application startup complete.
   ```

3. **Unified Backend (8001):**
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8001
   📁 SOW output directory: .../generated_docs_sow
   🔑 Gemini API Key loaded: Yes (length: 39)
   Application startup complete.
   ```

4. **Frontend (3001):**
   ```
   Compiled successfully!
   You can now view unified-ai-chat in the browser.
   Local: http://localhost:3001
   ```

---

## Final Checklist

Before using the system, verify:

- [ ] All 4 services are running (check with `lsof -i :8010,8002,8001,3001`)
- [ ] Gemini API keys are configured in both `.env` files
- [ ] Template file exists: `new_sow/sample_sow_template.docx`
- [ ] Unified backend connects to port 8002 (not 8000)
- [ ] Frontend opens at http://localhost:3001
- [ ] Health endpoints respond:
  - [ ] http://localhost:8010/api/ai/employees
  - [ ] http://localhost:8002/health
  - [ ] http://localhost:8001/api/health
  - [ ] http://localhost:3001

---

## Quick Reference Commands

```bash
# Start all services
cd unified_ai_chat && ./start_all_different_ports.sh

# Stop all services
cd unified_ai_chat && ./stop_all_different_ports.sh

# Check what's running
lsof -i :8010,8002,8001,3001

# View logs
tail -f /tmp/*-backend-*.log

# Test new_sow directly
cd new_sow && python test_complete_sow.py

# Restart just unified backend (after config changes)
kill $(cat /tmp/unified-backend-8001.pid)
cd unified_ai_chat/backend && python run_server.py &
```

---

## Support and Debugging

If issues persist:

1. **Check all logs** in `/tmp/` directory
2. **Verify Gemini API key** is valid and has quota
3. **Ensure ports are not blocked** by firewall
4. **Restart all services** in order (Absence → new_sow → Unified → Frontend)
5. **Clear browser cache** if frontend behaves oddly
6. **Check network connectivity** if API calls fail

---

## Document Generation Output

Generated SOW documents are saved to:
- **Primary:** `new_sow/output/SOW_*.docx`
- **Copy:** `generated_docs_sow/SOW_*.docx`

File naming format: `SOW_<ProjectName>_doc_<timestamp>_<hash>.docx`

---

## 🎯 Quick Start for New Developers/AI Assistants

### First Time Setup Checklist

1. **Clone/Open Project**
   ```bash
   cd /path/to/project
   ls -la  # Verify you see: ai_absence-ai_absence_mi, new_sow, unified_ai_chat
   ```

2. **Check Environment Files**
   ```bash
   # Check if .env files exist
   cat new_sow/.env | grep GEMINI_API_KEY
   cat unified_ai_chat/backend/.env | grep GEMINI_API_KEY
   
   # If missing, create them:
   echo "GEMINI_API_KEY=your_key_here" > new_sow/.env
   echo "GEMINI_MODEL=gemini-2.5-flash" >> new_sow/.env
   echo "DEBUG=True" >> new_sow/.env
   
   echo "GEMINI_API_KEY=your_key_here" > unified_ai_chat/backend/.env
   ```

3. **Verify Template File**
   ```bash
   ls -la new_sow/sample_sow_template.docx
   # If missing, copy from templates folder
   ```

4. **Install Dependencies**
   ```bash
   # Python dependencies for new_sow
   cd new_sow
   pip install -r requirements.txt
   
   # Python dependencies for unified_ai_chat backend
   cd ../unified_ai_chat/backend
   pip install -r requirements.txt
   
   # Node dependencies for frontend
   cd ../frontend
   npm install
   ```

5. **Start Services**
   ```bash
   cd ../../unified_ai_chat
   ./start_all_different_ports.sh
   ```

6. **Verify Everything Works**
   - Open http://localhost:3001
   - Try: "Mark Manju absent today"
   - Try: "I want to create a SOW"

---

## 🔍 Debugging Guide for AI Assistants

### When User Reports "Not Working"

**Step 1: Gather Information**
```bash
# What's running?
lsof -i :8010,8002,8001,3001

# Check logs
tail -n 50 /tmp/absence-backend-8010.log
tail -n 50 /tmp/use-sow-backend-8002.log
tail -n 50 /tmp/unified-backend-8001.log
tail -n 50 /tmp/unified-frontend-3001.log
```

**Step 2: Identify the Problem**
- **No services running?** → Start them
- **Port conflict?** → Kill conflicting process
- **Connection refused?** → Check if target service is running
- **500 error?** → Check backend logs for stack trace
- **Gemini error?** → Check API key and quota

**Step 3: Apply Solution**
- Restart affected service
- Fix configuration
- Update environment variables
- Clear caches if needed

### Error Pattern Recognition

| Error Message | Likely Cause | Solution |
|--------------|--------------|----------|
| `Cannot connect to host localhost:8000` | Wrong port in config | Change to 8002 in main.py |
| `IndexError: list index out of range` | Gemini response parsing | Already fixed in data_collector_v2.py |
| `Package not found at 'templates/...'` | Wrong template path | Use `sample_sow_template.docx` |
| `No module named 'app.services.document_service'` | Import error (harmless) | Ignore - use_sow not needed |
| `Data extraction failed` | Gemini function call issue | Check logs, retry usually works |
| `Port already in use` | Service already running | Kill existing or reuse |

---

## 📝 For AI Code Assistants: Code Modification Guidelines

### Safe to Modify
✅ Business logic in service files
✅ UI components in frontend/src
✅ Prompt templates in data_collector_v2.py
✅ Error messages and logging
✅ Validation logic

### Dangerous to Modify (Ask First)
⚠️ Port numbers (must stay: 8010, 8002, 8001, 3001)
⚠️ API endpoint paths (/api/generate-direct, /api/chat)
⚠️ Gemini model configuration
⚠️ File paths for templates and output
⚠️ Session management logic

### Never Modify Without Explicit Request
❌ Service startup scripts (run_server.py, run_backend_8002.py)
❌ Package.json port configuration
❌ CORS settings
❌ Environment variable names
❌ Database connection strings (if any)

---

## 🚨 Emergency Recovery

### If Everything is Broken

1. **Stop All Services**
   ```bash
   killall -9 java python node
   # Or use the stop script
   cd unified_ai_chat && ./stop_all_different_ports.sh
   ```

2. **Clean Up**
   ```bash
   rm -f /tmp/*-backend-*.log
   rm -f /tmp/*-backend-*.pid
   ```

3. **Verify Configuration**
   ```bash
   # Check port 8002 (not 8000) in main.py
   grep -n "localhost:800" unified_ai_chat/backend/app/main.py
   # Should only show 8001, 8002, 8010 - NOT 8000
   ```

4. **Restart Fresh**
   ```bash
   cd unified_ai_chat
   ./start_all_different_ports.sh
   ```

5. **Test Each Service Individually**
   ```bash
   curl http://localhost:8010/api/ai/employees
   curl http://localhost:8002/health
   curl http://localhost:8001/api/health
   curl http://localhost:3001
   ```

---

## 📚 Additional Resources

### Understanding the Data Flow

**Absence Management Flow:**
```
User: "Mark Manju absent today"
  → Frontend (3001) sends to Backend (8001)
  → Backend calls Gemini to parse intent
  → Backend calls Absence API (8010)
  → Absence API updates database
  → Response flows back to user
```

**SOW Generation Flow:**
```
User: "I want to create a SOW"
  → Frontend (3001) starts wizard
  → User fills 7 steps (project, services, deliverables, etc.)
  → User clicks "Generate"
  → Backend (8001) sends data to new_sow (8002)
  → new_sow calls Gemini for data extraction
  → new_sow generates .docx document
  → Document saved to new_sow/output/
  → Copy saved to generated_docs_sow/
  → Download link sent to frontend
```

### Key Integration Points

1. **unified_ai_chat/backend/app/main.py** (line ~1293)
   - Calls new_sow API
   - MUST use port 8002

2. **new_sow/app/api/direct_generation.py**
   - Receives generation requests
   - Processes with Gemini
   - Returns document info

3. **unified_ai_chat/backend/app/services/new_sow_adapter.py**
   - Converts unified_chat format to new_sow format
   - Handles API communication

---

**Last Updated:** October 30, 2025
**System Version:** Unified AI Chat v1.0 with new_sow integration
**AI Model:** Gemini 2.5 Flash

---

## 📞 Support Information

**For AI Assistants:**
- Always read this guide before making changes
- Check current state before suggesting solutions
- Verify changes don't break port configuration
- Test after modifications

**For Developers:**
- Keep this guide updated when making architectural changes
- Document new issues and solutions
- Update port numbers if changed
- Add new services to the startup script

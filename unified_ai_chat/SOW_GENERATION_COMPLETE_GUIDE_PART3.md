# 📘 SOW GENERATION COMPLETE GUIDE - PART 3

## Continuation from Part 2...

---

## 🔧 TROUBLESHOOTING & TIPS {#troubleshooting}

### Common Issues and Solutions

#### Issue 1: "new_sow application is not running on port 8002"

**Symptoms:**
```
❌ new_sow generation failed: new_sow application is not running on port 8002
🔄 Falling back to direct document generation...
```

**Cause:**
- new_sow application is not started
- new_sow is running on a different port
- Network connectivity issue

**Solution:**
```bash
# 1. Check if new_sow is running
curl http://localhost:8002/health

# 2. If not running, start new_sow
cd new_sow
python -m uvicorn app.main:app --reload --port 8002

# 3. Verify it's running
curl http://localhost:8002/health
# Should return: {"status": "healthy"}
```

---

#### Issue 2: "Gemini API Key not found"

**Symptoms:**
```
🔑 Gemini API Key loaded: No (length: 0)
❌ Error: Gemini API key not configured
```

**Cause:**
- GEMINI_API_KEY environment variable not set
- .env file not loaded

**Solution:**
```bash
# 1. Create .env file in project root
echo "GEMINI_API_KEY=your_api_key_here" > .env

# 2. Or export in terminal
export GEMINI_API_KEY="your_api_key_here"

# 3. Restart both applications
# Terminal 1:
cd unified_ai_chat/backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2:
cd new_sow
python -m uvicorn app.main:app --reload --port 8002
```

---

#### Issue 3: "Template file not found"

**Symptoms:**
```
❌ Template file not found: /path/to/sample_sow_template.docx
🔄 Using fallback document generation
```

**Cause:**
- Template file missing or in wrong location
- Path calculation error

**Solution:**
```bash
# 1. Check if template exists
ls -la sample_sow_template.docx

# 2. If missing, create or download template
# Template should be in project root

# 3. Verify path in code
# File: new_sow_adapter.py, line ~20
project_root = Path(__file__).resolve().parents[4]
self.template_path = str(project_root / "sample_sow_template.docx")
```

---

#### Issue 4: "Silent update not working in resource builder"

**Symptoms:**
- Clicking +/- buttons adds chat messages instead of silently updating

**Cause:**
- Frontend not handling `silent_update` flag correctly

**Solution:**
```javascript
// File: UnifiedChat.jsx
// Check if response has silent_update flag
if (data.silent_update) {
  // Don't add bot message, just update state
  setResourceBuilderData(data.current_resources);
  return;
}

// Otherwise, add bot message as usual
const botMessage = {
  text: data.response,
  sender: 'bot',
  ...
};
setMessages(prev => [...prev, botMessage]);
```

---

#### Issue 5: "Contact selection not working"

**Symptoms:**
- Clicking contact button doesn't populate input field
- Contact data not saved correctly

**Cause:**
- `populate_input` not set correctly in button
- Backend not parsing contact format

**Solution:**
```python
# Backend: Ensure full contact text in populate_input
{
  "id": "contact_mufg",
  "label": "MUFG Bank (Client)",
  "populate_input": "CONTACT: MUFG Bank | Contact Person: John Doe (Senior Manager, IT Department) | Email: john.doe@mufg.com | Phone: +1-555-0123 | Address: 1251 Avenue of the Americas, New York, NY 10020",
  "style": "primary"
}

# Backend: Parse contact text correctly
if txt.startswith("CONTACT:"):
    # Extract organization name
    org_name = txt.split("|")[0].replace("CONTACT:", "").strip()
    # Find contact in database
    selected_contact = find_contact_by_name(org_name)
```

---

#### Issue 6: "Document generation timeout"

**Symptoms:**
```
❌ new_sow API call error: Timeout after 60 seconds
```

**Cause:**
- Gemini API taking too long
- Network latency
- Large document processing

**Solution:**
```python
# Increase timeout in new_sow_adapter.py
async with session.post(
    f"{self.api_url}/generate-direct",
    json=payload,
    timeout=120  # Increase from 60 to 120 seconds
) as response:
    ...
```

---

#### Issue 7: "CORS error in browser console"

**Symptoms:**
```
Access to fetch at 'http://localhost:8000/api/chat' from origin 
'http://localhost:3000' has been blocked by CORS policy
```

**Cause:**
- CORS middleware not configured correctly
- Frontend URL not in allowed origins

**Solution:**
```python
# File: main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:3000",  # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Debugging Tips

#### Enable Detailed Logging

```python
# File: main.py or any service file
import logging

# Set to DEBUG level for detailed logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

**Example Debug Output:**
```
2024-10-30 10:30:45 - app.main - INFO - 📨 Received message: Create a new SOW
2024-10-30 10:30:45 - app.main - INFO - 🔑 Session ID: session_abc123
2024-10-30 10:30:45 - app.services.intent_classifier - DEBUG - Checking SOW keywords...
2024-10-30 10:30:45 - app.services.intent_classifier - INFO - ✅ SOW intent detected (keyword: sow)
2024-10-30 10:30:45 - app.services.sow_direct - DEBUG - Starting SOW collection
2024-10-30 10:30:45 - app.services.sow_direct - DEBUG - Current stage: project_info
```

---

#### Inspect Session State

```python
# Add debug endpoint to main.py
@app.get("/api/debug/session/{session_id}")
async def debug_session(session_id: str):
    """Debug endpoint to inspect session state"""
    state = get_session_state(session_id)
    return {
        "session_id": session_id,
        "stage": state.stage,
        "data": state.data,
        "created_at": state.created_at
    }
```

**Usage:**
```bash
# Check session state
curl http://localhost:8000/api/debug/session/session_abc123

# Response:
{
  "session_id": "session_abc123",
  "stage": "resources",
  "data": {
    "project_info": "Mobile e-commerce app...",
    "services": "SERVICES: Discovery & Planning...",
    "deliverables": "iOS app, Android app...",
    "timeline": "6 months starting January 2025"
  },
  "created_at": "2024-10-30T10:30:00Z"
}
```

---

#### Test Individual Components

**Test Intent Classification:**
```python
# test_intent.py
import asyncio
from app.services.intent_classifier import classify_intent

async def test():
    result = await classify_intent("Create a new SOW", "test_session")
    print(f"Intent: {result['intent']}")
    # Expected: Intent: sow_generation

asyncio.run(test())
```

**Test new_sow Health:**
```bash
# Test if new_sow is reachable
curl -v http://localhost:8002/health

# Expected response:
HTTP/1.1 200 OK
{"status": "healthy", "version": "1.0.0"}
```

**Test Document Generation:**
```python
# test_generation.py
import asyncio
from app.services.new_sow_adapter import new_sow_adapter

async def test():
    test_data = {
        "project_info": "Test project",
        "services": "Standard services",
        "deliverables": "Test deliverables",
        "timeline": "3 months",
        "resources": [{"role": "Developer", "count": 1}],
        "contacts": {"name": "Test Client", "email": "test@example.com"},
        "budget": "$10,000"
    }
    
    result = await new_sow_adapter.generate_sow_document(test_data, "test_session")
    print(f"Success: {result['success']}")
    print(f"Filename: {result.get('filename')}")

asyncio.run(test())
```

---

### Performance Optimization

#### 1. Cache Contact Data

```python
# File: sow_direct.py
class SowAdapter:
    def __init__(self):
        # Cache contacts on initialization
        self._contacts_cache = None
    
    def _get_contact_options(self):
        if self._contacts_cache is None:
            # Load from file only once
            self._contacts_cache = self._read_contacts()
        return self._contacts_cache
```

#### 2. Async Processing

```python
# Use async/await for all I/O operations
async def process_message(message: str):
    # Parallel processing
    intent_task = classify_intent(message)
    session_task = load_session(session_id)
    
    # Wait for both
    intent, session = await asyncio.gather(intent_task, session_task)
```

#### 3. Connection Pooling

```python
# File: new_sow_adapter.py
class NewSowAdapter:
    def __init__(self):
        # Reuse HTTP session
        self._session = None
    
    async def _get_session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session
```

---

## 📊 DATA STRUCTURES REFERENCE

### SowState Object

```python
class SowState:
    """Represents the current state of SOW collection"""
    
    stage: str  # Current stage: "project_info", "services", etc.
    data: Dict[str, Any]  # Collected data
    created_at: datetime  # When collection started
    updated_at: datetime  # Last update time
    
    # Example:
    {
        "stage": "resources",
        "data": {
            "project_info": "Mobile e-commerce app...",
            "services": "SERVICES: Discovery & Planning...",
            "deliverables": "iOS app, Android app...",
            "timeline": "6 months starting January 2025",
            "resources": [
                {"role": "Developer", "count": 2},
                {"role": "Tester", "count": 1}
            ]
        },
        "created_at": "2024-10-30T10:30:00Z",
        "updated_at": "2024-10-30T10:35:00Z"
    }
```

### ChatRequest Object

```python
class ChatRequest(BaseModel):
    """Request from frontend to backend"""
    
    message: str  # User's message
    session_id: str  # Unique session identifier
    
    # Example:
    {
        "message": "Create a new SOW for mobile app",
        "session_id": "session_abc123"
    }
```

### ChatResponse Object

```python
class ChatResponse(BaseModel):
    """Response from backend to frontend"""
    
    response: str  # Bot's message
    intent: str = None  # Detected intent
    confirmation_buttons: List[Dict] = None  # Buttons to show
    show_resource_builder: bool = False  # Show resource UI
    resource_roles: List[str] = None  # Available roles
    current_resources: List[Dict] = None  # Current resources
    silent_update: bool = False  # Don't add chat message
    download_url: str = None  # Document download link
    filename: str = None  # Generated filename
    
    # Example:
    {
        "response": "✅ Project Info captured! Step 2: Services...",
        "intent": "sow_generation",
        "confirmation_buttons": [
            {
                "id": "sow_service_standard",
                "label": "📦 Standard Package",
                "populate_input": "SERVICES: Discovery & Planning...",
                "style": "primary"
            }
        ]
    }
```

### Resource Object

```python
class Resource:
    """Represents a team resource"""
    
    role: str  # Role name (e.g., "Developer")
    count: int  # Number of people
    
    # Example:
    {
        "role": "Developer",
        "count": 2
    }
```

### Contact Object

```python
class Contact:
    """Represents a client/contractor contact"""
    
    id: str  # Unique identifier
    name: str  # Organization name
    type: str  # "client" or "contractor"
    contact_person: str  # Contact person name
    designation: str  # Job title
    department: str  # Department
    email: str  # Email address
    phone: str  # Phone number
    address: str  # Physical address
    
    # Example:
    {
        "id": "contact_mufg",
        "name": "MUFG Bank",
        "type": "client",
        "contact_person": "John Doe",
        "designation": "Senior Manager",
        "department": "IT Department",
        "email": "john.doe@mufg.com",
        "phone": "+1-555-0123",
        "address": "1251 Avenue of the Americas, New York, NY 10020"
    }
```

---

## 🎓 KEY CONCEPTS FOR BEGINNERS

### 1. What is an API?

**API (Application Programming Interface)** is a way for programs to talk to each other.

**Example:**
```
Frontend (React) wants to send a message
         ↓
Makes HTTP POST request to API
         ↓
Backend (FastAPI) receives request
         ↓
Processes the message
         ↓
Sends response back
         ↓
Frontend displays response
```

**Real Code:**
```javascript
// Frontend makes API call
fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  body: JSON.stringify({message: "Hello"})
})

// Backend receives and responds
@app.post("/api/chat")
async def chat(request):
    return {"response": "Hi there!"}
```

---

### 2. What is Async/Await?

**Async/await** allows programs to do multiple things at once without waiting.

**Without Async (Slow):**
```python
# Wait for each operation to finish
result1 = call_api_1()  # Takes 2 seconds
result2 = call_api_2()  # Takes 2 seconds
# Total: 4 seconds
```

**With Async (Fast):**
```python
# Start both at the same time
result1, result2 = await asyncio.gather(
    call_api_1(),  # Takes 2 seconds
    call_api_2()   # Takes 2 seconds
)
# Total: 2 seconds (parallel execution)
```

---

### 3. What is State Management?

**State** is the current condition of your application.

**Example:**
```python
# Initial state
state = {
    "stage": "project_info",
    "data": {}
}

# User provides project info
state = {
    "stage": "services",  # Stage changed
    "data": {
        "project_info": "Mobile app"  # Data added
    }
}

# User selects services
state = {
    "stage": "deliverables",  # Stage changed again
    "data": {
        "project_info": "Mobile app",
        "services": "Standard Package"  # More data added
    }
}
```

---

### 4. What is a Session?

**Session** keeps track of a user's conversation.

**Example:**
```
User A (session_abc123):
  - Stage: resources
  - Data: {project_info: "...", services: "..."}

User B (session_xyz789):
  - Stage: deliverables
  - Data: {project_info: "...", services: "..."}

Each user has their own session, so they don't interfere with each other.
```

---

### 5. What is Template Rendering?

**Template rendering** fills in placeholders with actual data.

**Template:**
```
Hello {{ name }}, your order #{{ order_id }} is ready!
Total: ${{ total }}
```

**Data:**
```python
{
    "name": "John",
    "order_id": "12345",
    "total": "99.99"
}
```

**Result:**
```
Hello John, your order #12345 is ready!
Total: $99.99
```

**In SOW Generation:**
```
Template: "Project Name: {{ project_name }}"
Data: {"project_name": "Mobile e-commerce app"}
Result: "Project Name: Mobile e-commerce app"
```

---

## 📝 COMPLETE FILE REFERENCE

### Frontend Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| `UnifiedChat.jsx` | Main chat interface | `handleSendMessage()`, `renderMessage()`, `renderResourceBuilder()` |
| `UnifiedChat.css` | Styling | Button styles, chat layout, resource builder UI |

### Backend Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| `main.py` | FastAPI server | `chat()` endpoint, CORS setup |
| `intent_classifier.py` | Detect user intent | `classify_intent()` |
| `sow_direct.py` | SOW data collection | `start()`, `process()`, `finalize()` |
| `new_sow_adapter.py` | Integration with new_sow | `generate_sow_document()`, `_call_new_sow_generation()` |
| `document_service.py` | Fallback generation | `generate()` |
| `contacts_data.json` | Contact database | N/A (data file) |

### new_sow Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| `direct_generation.py` | API endpoint | `generate_direct()` |
| `orchestrator.py` | AI coordination | `process_and_generate()`, `_create_enhancement_prompt()` |
| `sow_models.py` | Data structures | Model definitions |

---

## 🎯 SUMMARY

### What We Learned

1. **SOW Generation Flow:**
   - User types message → Intent classification → 7-stage collection → new_sow generation → Document download

2. **Key Components:**
   - Frontend: React chat interface
   - Backend: FastAPI server with 7-stage collector
   - new_sow: AI-powered document generator

3. **Data Flow:**
   - Structured data (unified_chat) → String format (adapter) → AI enhancement (new_sow) → Professional document

4. **Integration:**
   - HTTP communication between applications
   - Health checks and error handling
   - Fallback mechanisms

### Best Practices

1. **Always validate user input** before moving to next stage
2. **Use async/await** for I/O operations
3. **Implement health checks** for external services
4. **Provide fallback options** when services fail
5. **Log everything** for debugging
6. **Use clear variable names** for maintainability
7. **Handle errors gracefully** with user-friendly messages

### Next Steps

1. **Extend functionality:**
   - Add more service types
   - Support multiple templates
   - Add document preview

2. **Improve UX:**
   - Add progress indicators
   - Support editing previous stages
   - Add document history

3. **Enhance AI:**
   - Fine-tune Gemini prompts
   - Add industry-specific templates
   - Support multiple languages

---

## 📚 ADDITIONAL RESOURCES

### Documentation
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- Gemini AI: https://ai.google.dev/
- python-docx: https://python-docx.readthedocs.io/
- docxtpl: https://docxtpl.readthedocs.io/

### Tutorials
- Async Python: https://realpython.com/async-io-python/
- REST APIs: https://restfulapi.net/
- State Management: https://react.dev/learn/managing-state

---

## 🎉 CONCLUSION

You now have a complete understanding of how SOW generation works in Unified AI Chat!

**Key Takeaways:**
- ✅ 7-stage conversational data collection
- ✅ Integration between unified_ai_chat and new_sow
- ✅ AI-powered content enhancement with Gemini
- ✅ Professional document generation with templates
- ✅ Error handling and fallback mechanisms

**Remember:**
- Start simple, add complexity gradually
- Test each component independently
- Log everything for debugging
- Handle errors gracefully
- Keep user experience smooth

Happy coding! 🚀

---

**Document Version:** 1.0  
**Last Updated:** October 30, 2024  
**Author:** AI Assistant  
**For:** Unified AI Chat SOW Generation System

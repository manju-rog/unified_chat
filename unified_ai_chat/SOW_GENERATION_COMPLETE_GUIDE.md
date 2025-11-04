# 📘 COMPLETE SOW GENERATION GUIDE - UNIFIED AI CHAT

## 🎯 What This Document Covers

This is a **complete, step-by-step guide** for beginners that explains:
- How SOW (Statement of Work) generation works in Unified AI Chat
- Every single file involved and what it does
- The complete flow from user typing to document generation
- All the code with explanations
- Real examples with actual data

---

## 📚 TABLE OF CONTENTS

1. [Overview - What is SOW Generation?](#overview)
2. [Architecture - How Everything Connects](#architecture)
3. [The 7 Stages of Data Collection](#stages)
4. [Complete Code Walkthrough](#code-walkthrough)
5. [Step-by-Step Flow Example](#flow-example)
6. [Integration with new_sow Application](#integration)
7. [Document Generation Process](#document-generation)
8. [Troubleshooting & Tips](#troubleshooting)

---

## 📖 OVERVIEW - What is SOW Generation? {#overview}

### What is a Statement of Work (SOW)?

A **Statement of Work (SOW)** is a professional business document that defines:
- What work will be done in a project
- Who will do the work (team members)
- When it will be completed (timeline)
- How much it will cost (budget)
- Who the client is (contact information)

### How Does Unified AI Chat Generate SOWs?

Unified AI Chat uses a **conversational approach** to collect information:

```
User types: "Create a new SOW for mobile app development"
         ↓
System collects info through 7 stages (like a conversation)
         ↓
System sends data to new_sow application
         ↓
new_sow uses AI (Gemini) to enhance the content
         ↓
Professional Word document (.docx) is generated
         ↓
User downloads the document
```

### Why Two Applications?

1. **unified_ai_chat** = Collects information through conversation
2. **new_sow** = Generates professional documents with AI enhancement

This separation makes the system:
- More maintainable (each app has one job)
- More flexible (can use new_sow independently)
- More powerful (new_sow has specialized AI prompts)

---

## 🏗️ ARCHITECTURE - How Everything Connects {#architecture}

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    USER'S BROWSER                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         React Frontend (UnifiedChat.jsx)             │  │
│  │  - Chat interface                                    │  │
│  │  - Buttons for user interaction                      │  │
│  │  - Resource builder UI                               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↕ HTTP (Port 3000)
┌─────────────────────────────────────────────────────────────┐
│              UNIFIED_AI_CHAT BACKEND (Port 8000)            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  main.py - FastAPI Server                           │  │
│  │  - Handles /api/chat endpoint                        │  │
│  │  - Routes messages to correct service                │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  intent_classifier.py                                │  │
│  │  - Detects if user wants SOW                         │  │
│  │  - Returns intent: "sow_generation"                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  sow_direct.py - SowAdapter                          │  │
│  │  - Manages 7 stages of data collection              │  │
│  │  - Stores user responses                             │  │
│  │  - Calls new_sow_adapter when ready                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  new_sow_adapter.py - NewSowAdapter                  │  │
│  │  - Converts data to new_sow format                   │  │
│  │  - Makes HTTP call to new_sow API                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↕ HTTP (Port 8002)
┌─────────────────────────────────────────────────────────────┐
│                NEW_SOW APPLICATION (Port 8002)              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  direct_generation.py                                │  │
│  │  - Receives raw data                                 │  │
│  │  - Calls Gemini AI for enhancement                   │  │
│  │  - Generates Word document                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  orchestrator.py                                     │  │
│  │  - Coordinates AI agents                             │  │
│  │  - Enhances content with Gemini                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Document Generation                                 │  │
│  │  - Uses template (sample_sow_template.docx)          │  │
│  │  - Fills in all sections                             │  │
│  │  - Saves to new_sow/output/                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↓
                  📄 SOW_ProjectName_20241030.docx
```

### File Structure

```
project_root/
├── unified_ai_chat/
│   ├── frontend/
│   │   └── src/
│   │       └── UnifiedChat.jsx          # React UI
│   └── backend/
│       └── app/
│           ├── main.py                  # FastAPI server
│           ├── services/
│           │   ├── intent_classifier.py # Detects SOW intent
│           │   ├── sow_direct.py        # 7-stage collector
│           │   └── new_sow_adapter.py   # Calls new_sow
│           └── sow_components/
│               ├── document_service.py  # Fallback generator
│               └── contacts_data.json   # Contact database
├── new_sow/
│   ├── app/
│   │   ├── api/
│   │   │   └── direct_generation.py    # API endpoint
│   │   ├── agents/
│   │   │   └── orchestrator.py         # AI coordinator
│   │   └── models/
│   │       └── sow_models.py           # Data structures
│   └── output/                         # Generated docs
└── generated_docs_sow/                 # Final output folder
```

---

## 🎯 THE 7 STAGES OF DATA COLLECTION {#stages}

### Overview

The SOW generation process collects information in **7 sequential stages**:

| Stage | What It Collects | Example |
|-------|-----------------|---------|
| 1. Project Info | Project description, goals, scope | "Mobile app for e-commerce with payment integration" |
| 2. Services | Type of services (Standard/Custom) | "Standard Package" or "Custom Services" |
| 3. Deliverables | What will be delivered | "iOS app, Android app, Admin panel, API documentation" |
| 4. Timeline | Project schedule and milestones | "6 months, starting Jan 2025" |
| 5. Resources | Team members needed | "2 Developers, 1 Tester, 1 Project Manager" |
| 6. Contacts | Client information | "MUFG Bank, John Doe, john@mufg.com" |
| 7. Budget | Project cost | "$150,000 USD" |

### Stage Flow Diagram

```
START
  ↓
[Stage 1: Project Info]
  User types: "Mobile app development project"
  System stores: project_info = "Mobile app development project"
  ↓
[Stage 2: Services]
  System shows: [Standard Package] [Custom Services] buttons
  User clicks: Standard Package
  System stores: services = "SERVICES: Discovery & Planning (3 weeks)..."
  ↓
[Stage 3: Deliverables]
  User types: "iOS app, Android app, Admin panel"
  System stores: deliverables = "iOS app, Android app, Admin panel"
  ↓
[Stage 4: Timeline]
  User types: "6 months starting January 2025"
  System stores: timeline = "6 months starting January 2025"
  ↓
[Stage 5: Resources]
  System shows: Resource builder with +/- buttons
  User clicks: +Developer, +Developer, +Tester, +Project Manager
  System stores: resources = [{role:"Developer",count:2}, {role:"Tester",count:1}, ...]
  ↓
[Stage 6: Contacts]
  System shows: Contact dropdown
  User selects: "MUFG Bank"
  System stores: contacts = {name:"MUFG Bank", email:"...", ...}
  ↓
[Stage 7: Budget]
  User types: "$150,000 USD"
  System stores: budget = "$150,000 USD"
  ↓
[Generation Ready]
  System shows: [Generate SOW Document] button
  User clicks button
  ↓
SEND TO NEW_SOW
```

---


## 💻 COMPLETE CODE WALKTHROUGH {#code-walkthrough}

### Part 1: Frontend - UnifiedChat.jsx

#### What This File Does
- Displays the chat interface
- Shows buttons for user interaction
- Sends messages to backend
- Displays responses from backend

#### Key Code Sections

**1. Sending a Message to Backend**

```javascript
// Location: UnifiedChat.jsx, line ~150
const handleSendMessage = async () => {
  // Get user's message from input
  const userMessage = inputMessage.trim();
  
  // Create message object
  const newMessage = {
    text: userMessage,
    sender: 'user',
    timestamp: new Date().toISOString()
  };
  
  // Add to chat display
  setMessages(prev => [...prev, newMessage]);
  
  // Send to backend
  const response = await fetch('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: userMessage,
      session_id: sessionId
    })
  });
  
  // Get response
  const data = await response.json();
  
  // Display bot's response
  const botMessage = {
    text: data.response,
    sender: 'bot',
    timestamp: new Date().toISOString()
  };
  setMessages(prev => [...prev, botMessage]);
};
```

**Explanation:**
1. Gets text from input field
2. Creates a message object with text, sender, and timestamp
3. Adds message to chat (so user sees it immediately)
4. Sends HTTP POST request to backend at `http://localhost:8000/api/chat`
5. Waits for response from backend
6. Displays bot's response in chat

**2. Rendering Confirmation Buttons**

```javascript
// Location: UnifiedChat.jsx, line ~250
{message.confirmation_buttons && (
  <div className="confirmation-buttons">
    {message.confirmation_buttons.map((button, idx) => (
      <button
        key={idx}
        className={`confirmation-btn ${button.style || 'primary'}`}
        onClick={() => {
          // When button clicked, populate input with button's text
          if (button.populate_input) {
            setInputMessage(button.populate_input);
          }
        }}
      >
        {button.label}
      </button>
    ))}
  </div>
)}
```

**Explanation:**
- Checks if message has `confirmation_buttons` array
- For each button, creates a clickable button element
- When clicked, puts button's text into input field
- User can then send that text or modify it

**Example:**
```javascript
// Backend sends this:
{
  message: "Choose service type:",
  confirmation_buttons: [
    {
      id: "sow_service_standard",
      label: "📦 Standard Package",
      populate_input: "SERVICES: Discovery & Planning (3 weeks)...",
      style: "primary"
    }
  ]
}

// Frontend displays:
[📦 Standard Package] button
// When clicked, input field shows: "SERVICES: Discovery & Planning (3 weeks)..."
```

**3. Resource Builder UI**

```javascript
// Location: UnifiedChat.jsx, line ~300
{message.show_resource_builder && (
  <div className="resource-builder">
    <h4>Team Resources</h4>
    
    {/* Display current resources */}
    <div className="current-resources">
      {message.current_resources?.map((resource, idx) => (
        <div key={idx} className="resource-item">
          <span>{resource.role}: {resource.count}</span>
          <button onClick={() => handleResourceChange(resource.role, -1)}>-</button>
          <button onClick={() => handleResourceChange(resource.role, 1)}>+</button>
        </div>
      ))}
    </div>
    
    {/* Add new resource buttons */}
    <div className="add-resource-buttons">
      {message.resource_roles?.map((role, idx) => (
        <button 
          key={idx}
          onClick={() => handleResourceChange(role, 1)}
        >
          + {role}
        </button>
      ))}
    </div>
    
    {/* Next button */}
    <button onClick={() => handleSendMessage('next')}>
      Continue to Next Step
    </button>
  </div>
)}
```

**Explanation:**
- Shows current team members with +/- buttons
- Shows buttons to add new roles
- When user clicks +, sends message like "+:Developer"
- When user clicks -, sends message like "-:Developer"
- Backend updates the count and sends back updated list

---

### Part 2: Backend Entry Point - main.py

#### What This File Does
- Runs the FastAPI web server
- Receives HTTP requests from frontend
- Routes requests to appropriate services
- Sends responses back to frontend

#### Key Code Sections

**1. Server Setup**

```python
# Location: main.py, line ~1
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Create FastAPI app
app = FastAPI(title="Unified AI Chat API")

# Enable CORS (allows frontend to call backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

**Explanation:**
- Creates FastAPI application
- Adds CORS middleware so React (port 3000) can call API (port 8000)
- Sets up logging to see what's happening

**2. Chat Endpoint**

```python
# Location: main.py, line ~50
class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    intent: str = None
    confirmation_buttons: list = None
    show_resource_builder: bool = False
    # ... other fields

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint - receives user messages and returns responses
    """
    logger.info(f"📨 Received message: {request.message}")
    logger.info(f"🔑 Session ID: {request.session_id}")
    
    # Step 1: Classify intent (what does user want?)
    intent_result = await classify_intent(request.message, request.session_id)
    intent = intent_result.get("intent")
    
    logger.info(f"🎯 Detected intent: {intent}")
    
    # Step 2: Route to appropriate service
    if intent == "sow_generation":
        # Handle SOW generation
        response = await handle_sow_generation(request.message, request.session_id)
    elif intent == "absence_management":
        # Handle absence management
        response = await handle_absence(request.message, request.session_id)
    else:
        # General chat
        response = {"response": "I can help with SOW generation or absence management."}
    
    return response
```

**Explanation:**
1. Receives POST request with user's message and session_id
2. Calls `classify_intent()` to determine what user wants
3. Routes to appropriate handler based on intent
4. Returns response to frontend

**Example Flow:**
```
User types: "Create a new SOW"
         ↓
POST /api/chat
{
  "message": "Create a new SOW",
  "session_id": "abc123"
}
         ↓
classify_intent() returns: "sow_generation"
         ↓
handle_sow_generation() is called
         ↓
Returns: {
  "response": "Let's create a SOW! Tell me about the project...",
  "intent": "sow_generation"
}
```

---

### Part 3: Intent Classification - intent_classifier.py

#### What This File Does
- Analyzes user's message
- Determines what the user wants to do
- Returns intent type (sow_generation, absence_management, etc.)

#### Key Code Sections

**1. Intent Detection**

```python
# Location: intent_classifier.py, line ~20
async def classify_intent(message: str, session_id: str) -> dict:
    """
    Classify user intent from message
    
    Returns:
        dict with 'intent' key: 'sow_generation', 'absence_management', or 'general'
    """
    message_lower = message.lower()
    
    # Check for SOW keywords
    sow_keywords = [
        'sow', 'statement of work', 'create sow', 'generate sow',
        'new sow', 'project document', 'work statement'
    ]
    
    for keyword in sow_keywords:
        if keyword in message_lower:
            logger.info(f"✅ SOW intent detected (keyword: {keyword})")
            return {"intent": "sow_generation"}
    
    # Check for absence keywords
    absence_keywords = [
        'absent', 'absence', 'leave', 'mark absent', 'not coming',
        'sick leave', 'vacation', 'time off'
    ]
    
    for keyword in absence_keywords:
        if keyword in message_lower:
            logger.info(f"✅ Absence intent detected (keyword: {keyword})")
            return {"intent": "absence_management"}
    
    # Default to general
    logger.info("ℹ️ General intent (no specific keywords)")
    return {"intent": "general"}
```

**Explanation:**
- Converts message to lowercase for easier matching
- Checks if message contains SOW-related keywords
- Checks if message contains absence-related keywords
- Returns the detected intent

**Examples:**
```python
classify_intent("Create a new SOW for mobile app", "session123")
# Returns: {"intent": "sow_generation"}

classify_intent("Mark John absent today", "session123")
# Returns: {"intent": "absence_management"}

classify_intent("Hello, how are you?", "session123")
# Returns: {"intent": "general"}
```

---

### Part 4: SOW Data Collection - sow_direct.py (SowAdapter)

#### What This File Does
- Manages the 7 stages of SOW data collection
- Stores user responses in memory
- Validates user input
- Calls new_sow_adapter when all data is collected

#### Key Code Sections

**1. SowAdapter Class Initialization**

```python
# Location: sow_direct.py, line ~15
class SowAdapter:
    """Blind intake across 7 stages. AI (Gemini) is called once in finalize()."""
    
    def __init__(self, out_root: Path):
        # Setup output directory
        project_root = Path(__file__).resolve().parents[3]
        self.out_root = project_root / "generated_docs_sow"
        self.out_root.mkdir(parents=True, exist_ok=True)
        
        # Initialize document service (fallback)
        self.doc_service = DocumentService(out_dir=self.out_root)
        
        # Initialize Gemini client
        import os
        api_key = os.getenv("GEMINI_API_KEY")
        self.gemini = GeminiClient(api_key=api_key)
```

**Explanation:**
- Sets up output folder for generated documents
- Creates DocumentService for fallback generation
- Initializes Gemini AI client with API key from environment

**2. Starting SOW Collection**

```python
# Location: sow_direct.py, line ~35
def start(self) -> Tuple[str, Dict[str, Any]]:
    """
    Start SOW collection process
    
    Returns:
        Tuple of (question_text, response_dict)
    """
    return self._question_for("project_info"), {
        "tips": "We'll collect details first (no AI yet). Type 'exit' anytime to cancel."
    }
```

**Explanation:**
- Called when SOW generation starts
- Returns first question (about project info)
- Provides helpful tip to user

**3. Processing User Responses - Stage 1 (Project Info)**

```python
# Location: sow_direct.py, line ~45
def process(self, state: SowState, user_message: str) -> Tuple[SowState, Dict[str, Any]]:
    """
    Process user message based on current stage
    
    Args:
        state: Current SOW state (contains stage and collected data)
        user_message: User's message
    
    Returns:
        Tuple of (updated_state, response_dict)
    """
    txt = (user_message or "").strip()
    resp: Dict[str, Any] = {}
    
    # STAGE 1: PROJECT INFO
    if state.stage == "project_info":
        # Store user's project description
        state.data["project_info"] = txt
        
        # Move to next stage
        state.stage = "services"
        
        # Prepare response with buttons
        resp["message"] = "✅ **Project Info captured!**\n\n**Step 2: Services**\nChoose the type of services for this SOW:"
        resp["confirmation_buttons"] = [
            {
                "id": "sow_service_standard",
                "label": "📦 Standard Package",
                "populate_input": "SERVICES: Discovery & Planning (3 weeks), Data Migration (4 weeks), Application Development (8 weeks), Testing & QA (2 weeks), Deployment & Go-Live (1 week)",
                "style": "primary"
            },
            {
                "id": "sow_service_custom",
                "label": "🛠️ Custom Services",
                "populate_input": "Custom Services (to be defined based on project requirements)",
                "style": "secondary"
            }
        ]
        
        return state, resp
```

**Explanation:**
1. Gets user's message and trims whitespace
2. Checks current stage (project_info)
3. Stores user's response in `state.data["project_info"]`
4. Updates stage to "services"
5. Creates response with confirmation message and buttons
6. Returns updated state and response

**Example Flow:**
```
User types: "Mobile app for e-commerce with payment integration"
         ↓
state.stage = "project_info"
         ↓
Store: state.data["project_info"] = "Mobile app for e-commerce..."
         ↓
Update: state.stage = "services"
         ↓
Return: {
  "message": "✅ Project Info captured! Step 2: Services...",
  "confirmation_buttons": [
    {label: "📦 Standard Package", ...},
    {label: "🛠️ Custom Services", ...}
  ]
}
```

**4. Processing Stage 2 (Services)**

```python
# Location: sow_direct.py, line ~75
if state.stage == "services":
    # Handle both full text and short format
    if txt.startswith("SERVICES:"):
        # Full standard package text
        state.data["services"] = txt
        service_type = "Standard Package"
    elif txt.startswith("Custom Services"):
        # Full custom services text
        state.data["services"] = txt
        service_type = "Custom Services"
    elif txt.lower() == "standard":
        # Short format - expand to full
        state.data["services"] = "SERVICES: Discovery & Planning (3 weeks), Data Migration (4 weeks), Application Development (8 weeks), Testing & QA (2 weeks), Deployment & Go-Live (1 week)"
        service_type = "Standard Package"
    elif txt.lower() == "custom":
        # Short format - expand to full
        state.data["services"] = "Custom Services (to be defined based on project requirements)"
        service_type = "Custom Services"
    else:
        # Invalid input - show buttons again
        resp["message"] = "Please select one of the service options:"
        resp["confirmation_buttons"] = [...]
        return state, resp
    
    # Move to next stage
    state.stage = "deliverables"
    resp["message"] = f"✅ **{service_type} selected!**\n\n**Services Details:**\n{state.data['services']}\n\n**Step 3: Deliverables**\nNow tell me about the specific deliverables for this project:"
    
    return state, resp
```

**Explanation:**
- Handles multiple input formats (full text, short keywords)
- Validates input and shows buttons again if invalid
- Stores service selection
- Moves to deliverables stage

**5. Processing Stage 5 (Resources) - Complex Example**

```python
# Location: sow_direct.py, line ~150
if state.stage == "resources":
    # Initialize resources list if not exists
    data = state.data.setdefault("resources", [])
    
    # Helper function to update resource count
    def set_count(role: str, delta: int):
        # Find existing resource
        for r in data:
            if r["role"].lower() == role.lower():
                r["count"] = max(0, r["count"] + delta)
                if r["count"] == 0:
                    data.remove(r)  # Remove if count reaches 0
                return
        # Add new resource if delta is positive
        if delta > 0:
            data.append({"role": role, "count": delta})
    
    # Handle add command: "+:Developer"
    if txt.startswith("+:") or txt.startswith("add:"):
        role = txt.split(":", 1)[1].strip()
        set_count(role, 1)
        
        # Silent update - don't add new message
        resp["silent_update"] = True
        resp["show_resource_builder"] = True
        resp["resource_roles"] = ["Developer", "DevOps", "Tester", "QA Engineer", "Business Analyst", "Project Manager"]
        resp["current_resources"] = data
        return state, resp
    
    # Handle remove command: "-:Developer"
    elif txt.startswith("-:"):
        role = txt.split(":", 1)[1].strip()
        set_count(role, -1)
        
        # Silent update
        resp["silent_update"] = True
        resp["show_resource_builder"] = True
        resp["resource_roles"] = [...]
        resp["current_resources"] = data
        return state, resp
    
    # Handle next command
    elif txt.lower() == "next" or txt.startswith("Add these resources:"):
        state.stage = "contacts"
        resp["message"] = "✅ **Resources selected!**\n\n**Step 6: Contacts**\nSelect a contact:"
        
        # Load contacts and create buttons
        contacts = self._get_contact_options()
        resp["confirmation_buttons"] = [
            {
                "id": contact["id"],
                "label": contact["label"],
                "populate_input": contact["value"],
                "style": "primary"
            }
            for contact in contacts[:5]
        ]
        return state, resp
```

**Explanation:**
- Manages a list of resources (team members)
- Handles add (+:Role) and remove (-:Role) commands
- Uses "silent_update" to update UI without adding chat message
- When user says "next", moves to contacts stage

**Example Flow:**
```
User clicks: +Developer button
         ↓
Frontend sends: "+:Developer"
         ↓
Backend: set_count("Developer", 1)
         ↓
data = [{"role": "Developer", "count": 1}]
         ↓
Return: {
  "silent_update": true,
  "show_resource_builder": true,
  "current_resources": [{"role": "Developer", "count": 1}]
}
         ↓
Frontend updates UI (no new chat message)

User clicks: +Developer again
         ↓
data = [{"role": "Developer", "count": 2}]

User clicks: +Tester
         ↓
data = [
  {"role": "Developer", "count": 2},
  {"role": "Tester", "count": 1}
]

User clicks: Next
         ↓
Move to contacts stage
```

**6. Finalizing and Generating Document**

```python
# Location: sow_direct.py, line ~300
def finalize(self, state: SowState, session_id: str) -> Dict[str, Any]:
    """
    Generate final SOW document using new_sow application
    """
    print(f"🎯 GENERATING SOW VIA NEW_SOW APPLICATION...")
    
    try:
        # Import the new_sow adapter
        from .new_sow_adapter import new_sow_adapter
        
        # Call new_sow application via adapter
        import asyncio
        
        # Create event loop and run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                new_sow_adapter.generate_sow_document(state.data, session_id)
            )
        finally:
            loop.close()
        
        if result["success"]:
            print(f"✅ new_sow generation completed: {result['filename']}")
            
            return {
                "message": f"✅ **SOW Generated Successfully!**\n\nYour professional Statement of Work document has been created.\n\n📄 **Document Details:**\n- Project: {state.data.get('project_info', 'N/A')}\n- Total Value: {state.data.get('budget', 'N/A')}\n- Timeline: {state.data.get('timeline', 'N/A')}\n\n**Document is ready for download!**",
                "download_url": result['download_url'],
                "filename": result['filename']
            }
        else:
            raise Exception(f"new_sow generation failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ new_sow generation failed: {e}")
        # Fallback to direct generation
        return self._fallback_generation(state, session_id)
```

**Explanation:**
1. Called when all 7 stages are complete
2. Imports new_sow_adapter
3. Creates async event loop (needed for HTTP calls)
4. Calls `new_sow_adapter.generate_sow_document()` with collected data
5. If successful, returns success message with download link
6. If fails, falls back to direct generation

---


### Part 5: Integration with new_sow - new_sow_adapter.py

#### What This File Does
- Converts unified_chat data format to new_sow format
- Makes HTTP calls to new_sow application
- Handles errors and retries
- Copies generated documents to final location

#### Key Code Sections

**1. NewSowAdapter Class**

```python
# Location: new_sow_adapter.py, line ~15
class NewSowAdapter:
    """Adapter to convert unified_chat data to new_sow format and generate documents"""
    
    def __init__(self, new_sow_base_url: str = "http://localhost:8002"):
        self.base_url = new_sow_base_url
        self.api_url = f"{self.base_url}/api"
        
        # Find template path
        project_root = Path(__file__).resolve().parents[4]
        self.template_path = str(project_root / "sample_sow_template.docx")
```

**Explanation:**
- Sets new_sow base URL (default: http://localhost:8002)
- Constructs API URL
- Finds template file path

**2. Main Generation Method**

```python
# Location: new_sow_adapter.py, line ~30
async def generate_sow_document(self, unified_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """
    Generate SOW document using new_sow application
    
    Args:
        unified_data: Data collected from unified_chat (7 stages)
        session_id: Session identifier
        
    Returns:
        Dict with success status, filename, and download info
    """
    try:
        logger.info(f"🎯 Converting unified_chat data to new_sow format for session {session_id}")
        
        # Step 1: Check if new_sow is running
        if not await self._check_new_sow_health():
            raise Exception("new_sow application is not running on port 8002")
        
        # Step 2: Convert data format
        raw_responses = self._convert_to_raw_responses(unified_data)
        
        # Step 3: Call new_sow API
        result = await self._call_new_sow_generation(raw_responses, session_id)
        
        # Step 4: Copy file to final location
        if result["success"]:
            logger.info(f"✅ SOW document generated successfully: {result['filename']}")
            self._copy_to_generated_docs_sow_sync(result['filename'], session_id)
            
            return {
                "success": True,
                "filename": result["filename"],
                "download_url": f"/api/sow/download/{result['filename']}",
                "message": "SOW document generated successfully"
            }
        else:
            raise Exception(f"new_sow generation failed: {result.get('error')}")
        
    except Exception as e:
        logger.error(f"❌ new_sow generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"SOW generation failed: {str(e)}"
        }
```

**Explanation:**
1. Checks if new_sow application is running
2. Converts unified_chat data to new_sow format
3. Makes HTTP call to new_sow API
4. Copies generated file to final location
5. Returns success/failure result

**3. Health Check**

```python
# Location: new_sow_adapter.py, line ~80
async def _check_new_sow_health(self) -> bool:
    """Check if new_sow application is running"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/health", timeout=5) as response:
                if response.status == 200:
                    logger.info("✅ new_sow application is running and healthy")
                    return True
                else:
                    logger.error(f"❌ new_sow health check failed: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"❌ new_sow health check error: {e}")
        return False
```

**Explanation:**
- Makes HTTP GET request to new_sow's /health endpoint
- Returns True if new_sow is running, False otherwise
- Has 5-second timeout to avoid hanging

**Example:**
```
GET http://localhost:8002/health
         ↓
Response: 200 OK
         ↓
Return: True (new_sow is running)
```

**4. Calling new_sow API**

```python
# Location: new_sow_adapter.py, line ~100
async def _call_new_sow_generation(self, raw_responses: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """Call new_sow direct generation API"""
    try:
        logger.info(f"📤 Calling new_sow direct generation API...")
        logger.info(f"   new_sow will process data with Gemini using its own prompts")
        
        # Prepare request payload
        payload = {
            "template_path": self.template_path,
            "project_data": raw_responses,  # Raw string responses
            "session_id": session_id
        }
        
        # Make HTTP POST request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/generate-direct",
                json=payload,
                timeout=60  # Allow time for Gemini processing
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ new_sow generation successful: {result.get('filename')}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ new_sow API error ({response.status}): {error_text}")
                    return {
                        "success": False,
                        "error": f"new_sow API returned {response.status}: {error_text}"
                    }
                
    except Exception as e:
        logger.error(f"❌ new_sow API call error: {e}")
        return {"success": False, "error": str(e)}
```

**Explanation:**
1. Prepares payload with template path, project data, and session ID
2. Makes HTTP POST to new_sow's /api/generate-direct endpoint
3. Waits up to 60 seconds for response (Gemini processing takes time)
4. Returns result or error

**Example HTTP Request:**
```http
POST http://localhost:8002/api/generate-direct
Content-Type: application/json

{
  "template_path": "/path/to/sample_sow_template.docx",
  "project_data": {
    "project_info": "Mobile app for e-commerce",
    "services": "SERVICES: Discovery & Planning (3 weeks)...",
    "deliverables": "iOS app, Android app, Admin panel",
    "timeline": "6 months starting January 2025",
    "resources": "Developer: 2 person(s), Tester: 1 person(s)",
    "contacts": "Client: MUFG Bank, Contact: John Doe...",
    "budget": "$150,000 USD"
  },
  "session_id": "abc123"
}
```

**5. Data Format Conversion**

```python
# Location: new_sow_adapter.py, line ~150
def _convert_to_raw_responses(self, unified_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert unified_chat data to new_sow raw_responses format
    """
    
    # Format project info (already a string)
    project_info_str = unified_data.get("project_info", "")
    
    # Format services (already a string)
    services_str = unified_data.get("services", "")
    
    # Format deliverables (already a string)
    deliverables_str = unified_data.get("deliverables", "")
    
    # Format timeline (already a string)
    timeline_str = unified_data.get("timeline", "")
    
    # Format resources (convert list to string)
    resources_list = unified_data.get("resources", [])
    resources_str = ", ".join([
        f"{r.get('role', 'Team Member')}: {r.get('count', 1)} person(s)" 
        for r in resources_list
    ])
    
    # Format contacts (convert dict to string)
    contacts_dict = unified_data.get("contacts", {})
    contacts_str = f"Client: {contacts_dict.get('name', 'N/A')}, Contact: {contacts_dict.get('contact_person', 'N/A')}, Email: {contacts_dict.get('email', 'N/A')}, Phone: {contacts_dict.get('phone', 'N/A')}, Address: {contacts_dict.get('address', 'N/A')}"
    
    # Format budget (already a string)
    budget_str = unified_data.get("budget", "")
    
    # Create raw_responses dict
    raw_responses = {
        "project_info": project_info_str,
        "services": services_str,
        "deliverables": deliverables_str,
        "timeline": timeline_str,
        "resources": resources_str,
        "contacts": contacts_str,
        "budget": budget_str
    }
    
    logger.info(f"✅ Converted unified_chat data to new_sow raw_responses format")
    return raw_responses
```

**Explanation:**
- Converts unified_chat's structured data to new_sow's string format
- Resources: list → comma-separated string
- Contacts: dict → formatted string
- Other fields: already strings, just pass through

**Example Conversion:**
```python
# Input (unified_chat format):
{
  "project_info": "Mobile app for e-commerce",
  "resources": [
    {"role": "Developer", "count": 2},
    {"role": "Tester", "count": 1}
  ],
  "contacts": {
    "name": "MUFG Bank",
    "contact_person": "John Doe",
    "email": "john@mufg.com",
    "phone": "+1-555-1234",
    "address": "123 Main St"
  }
}

# Output (new_sow format):
{
  "project_info": "Mobile app for e-commerce",
  "resources": "Developer: 2 person(s), Tester: 1 person(s)",
  "contacts": "Client: MUFG Bank, Contact: John Doe, Email: john@mufg.com, Phone: +1-555-1234, Address: 123 Main St"
}
```

**6. Copying Generated File**

```python
# Location: new_sow_adapter.py, line ~200
def _copy_to_generated_docs_sow_sync(self, filename: str, session_id: str):
    """Copy generated document from new_sow/output to generated_docs_sow"""
    try:
        import shutil
        project_root = Path(__file__).resolve().parents[4]
        
        # Source: new_sow/output/
        source = project_root / "new_sow" / "output" / filename
        
        # Destination: generated_docs_sow/
        dest_dir = project_root / "generated_docs_sow"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filename
        
        if source.exists():
            shutil.copy2(source, dest)
            logger.info(f"✅ Copied document to generated_docs_sow: {filename}")
        else:
            logger.warning(f"⚠️ Source file not found: {source}")
    except Exception as e:
        logger.error(f"❌ Error copying document: {e}")
```

**Explanation:**
- Finds source file in new_sow/output/
- Creates destination folder if needed
- Copies file to generated_docs_sow/
- Logs success or error

---

## 🔄 STEP-BY-STEP FLOW EXAMPLE {#flow-example}

### Complete Example: "Create SOW for Mobile App Project"

Let's trace a complete SOW generation from start to finish with actual data.

#### Initial Request

**User Action:**
```
User types in chat: "Create a new SOW for mobile app development"
User clicks: Send button
```

**Frontend (UnifiedChat.jsx):**
```javascript
// Line ~150
handleSendMessage() {
  const userMessage = "Create a new SOW for mobile app development";
  
  // Add to chat display
  setMessages([...messages, {
    text: userMessage,
    sender: 'user',
    timestamp: '2024-10-30T10:00:00Z'
  }]);
  
  // Send to backend
  fetch('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      message: userMessage,
      session_id: 'session_abc123'
    })
  });
}
```

**HTTP Request:**
```http
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "message": "Create a new SOW for mobile app development",
  "session_id": "session_abc123"
}
```

---

#### Backend Processing - Intent Classification

**Backend (main.py):**
```python
# Line ~50
@app.post("/api/chat")
async def chat(request: ChatRequest):
    logger.info(f"📨 Received: Create a new SOW for mobile app development")
    logger.info(f"🔑 Session: session_abc123")
    
    # Classify intent
    intent_result = await classify_intent(
        "Create a new SOW for mobile app development",
        "session_abc123"
    )
    # Returns: {"intent": "sow_generation"}
    
    logger.info(f"🎯 Intent: sow_generation")
    
    # Route to SOW handler
    response = await handle_sow_generation(
        "Create a new SOW for mobile app development",
        "session_abc123"
    )
    
    return response
```

**Intent Classifier (intent_classifier.py):**
```python
# Line ~20
async def classify_intent(message, session_id):
    message_lower = "create a new sow for mobile app development"
    
    sow_keywords = ['sow', 'statement of work', 'create sow', ...]
    
    # Check: 'sow' in message_lower → True!
    logger.info("✅ SOW intent detected (keyword: sow)")
    return {"intent": "sow_generation"}
```

---

#### Stage 1: Project Info

**SOW Handler (sow_direct.py):**
```python
# First call - start()
def start():
    return "Project Info: briefly describe project, goal, and scope.", {
        "tips": "We'll collect details first. Type 'exit' anytime to cancel."
    }
```

**HTTP Response to Frontend:**
```json
{
  "response": "Let's create a professional Statement of Work!\n\n**Step 1: Project Information**\nProject Info: briefly describe project, goal, and scope.",
  "intent": "sow_generation",
  "tips": "We'll collect details first. Type 'exit' anytime to cancel."
}
```

**Frontend Display:**
```
Bot: Let's create a professional Statement of Work!

**Step 1: Project Information**
Project Info: briefly describe project, goal, and scope.

💡 We'll collect details first. Type 'exit' anytime to cancel.
```

**User Types:**
```
"Mobile e-commerce app with payment gateway integration, user authentication, product catalog, and shopping cart functionality"
```

**Backend Processing:**
```python
# process() method
if state.stage == "project_info":
    # Store response
    state.data["project_info"] = "Mobile e-commerce app with payment gateway integration, user authentication, product catalog, and shopping cart functionality"
    
    # Move to next stage
    state.stage = "services"
    
    # Return response
    return state, {
        "message": "✅ **Project Info captured!**\n\n**Step 2: Services**\nChoose the type of services for this SOW:",
        "confirmation_buttons": [
            {
                "id": "sow_service_standard",
                "label": "📦 Standard Package",
                "populate_input": "SERVICES: Discovery & Planning (3 weeks), Data Migration (4 weeks), Application Development (8 weeks), Testing & QA (2 weeks), Deployment & Go-Live (1 week)",
                "style": "primary"
            },
            {
                "id": "sow_service_custom",
                "label": "🛠️ Custom Services",
                "populate_input": "Custom Services (to be defined based on project requirements)",
                "style": "secondary"
            }
        ]
    }
```

**Frontend Display:**
```
Bot: ✅ **Project Info captured!**

**Step 2: Services**
Choose the type of services for this SOW:

[📦 Standard Package]  [🛠️ Custom Services]
```

---

#### Stage 2: Services

**User Action:**
```
User clicks: [📦 Standard Package] button
```

**Frontend:**
```javascript
// Button click handler
onClick={() => {
  setInputMessage("SERVICES: Discovery & Planning (3 weeks), Data Migration (4 weeks), Application Development (8 weeks), Testing & QA (2 weeks), Deployment & Go-Live (1 week)");
  // User sees this in input field and can send it
}}
```

**User Sends Message:**
```
"SERVICES: Discovery & Planning (3 weeks), Data Migration (4 weeks), Application Development (8 weeks), Testing & QA (2 weeks), Deployment & Go-Live (1 week)"
```

**Backend Processing:**
```python
if state.stage == "services":
    txt = "SERVICES: Discovery & Planning (3 weeks)..."
    
    if txt.startswith("SERVICES:"):
        state.data["services"] = txt
        service_type = "Standard Package"
    
    state.stage = "deliverables"
    
    return state, {
        "message": "✅ **Standard Package selected!**\n\n**Services Details:**\nSERVICES: Discovery & Planning (3 weeks), Data Migration (4 weeks), Application Development (8 weeks), Testing & QA (2 weeks), Deployment & Go-Live (1 week)\n\n**Step 3: Deliverables**\nNow tell me about the specific deliverables for this project:"
    }
```

---

#### Stage 3: Deliverables

**User Types:**
```
"iOS mobile app, Android mobile app, Admin web dashboard, REST API backend, User documentation, Deployment guide"
```

**Backend Processing:**
```python
if state.stage == "deliverables":
    state.data["deliverables"] = "iOS mobile app, Android mobile app, Admin web dashboard, REST API backend, User documentation, Deployment guide"
    
    state.stage = "timeline"
    
    return state, {
        "message": "✅ **Deliverables captured!**\n\n**Step 4: Timeline**\nProvide the project timeline (milestones, dates, duration):"
    }
```

---

#### Stage 4: Timeline

**User Types:**
```
"6 months project starting January 15, 2025. Phase 1: Planning (3 weeks), Phase 2: Development (16 weeks), Phase 3: Testing (3 weeks), Phase 4: Deployment (2 weeks)"
```

**Backend Processing:**
```python
if state.stage == "timeline":
    state.data["timeline"] = "6 months project starting January 15, 2025. Phase 1: Planning (3 weeks), Phase 2: Development (16 weeks), Phase 3: Testing (3 weeks), Phase 4: Deployment (2 weeks)"
    
    state.stage = "resources"
    
    return state, {
        "message": "✅ **Timeline captured!**\n\n**Step 5: Resources**\nSelect team members using the + and - buttons below:",
        "show_resource_builder": True,
        "resource_roles": ["Developer", "DevOps", "Tester", "QA Engineer", "Business Analyst", "Project Manager"],
        "current_resources": []
    }
```

**Frontend Display:**
```
Bot: ✅ **Timeline captured!**

**Step 5: Resources**
Select team members using the + and - buttons below:

Team Resources:
(empty)

Add Resources:
[+ Developer] [+ DevOps] [+ Tester] [+ QA Engineer] [+ Business Analyst] [+ Project Manager]

[Continue to Next Step]
```

---

#### Stage 5: Resources (Interactive)

**User Interactions:**

**Click 1: +Developer**
```
Frontend sends: "+:Developer"
Backend: set_count("Developer", 1)
State: resources = [{"role": "Developer", "count": 1}]
Response: {
  "silent_update": true,
  "current_resources": [{"role": "Developer", "count": 1}]
}
Frontend updates UI (no new message)
```

**Click 2: +Developer (again)**
```
Frontend sends: "+:Developer"
Backend: set_count("Developer", 1)
State: resources = [{"role": "Developer", "count": 2}]
Response: {"silent_update": true, "current_resources": [...]}
```

**Click 3: +Tester**
```
Frontend sends: "+:Tester"
Backend: set_count("Tester", 1)
State: resources = [
  {"role": "Developer", "count": 2},
  {"role": "Tester", "count": 1}
]
```

**Click 4: +QA Engineer**
```
State: resources = [
  {"role": "Developer", "count": 2},
  {"role": "Tester", "count": 1},
  {"role": "QA Engineer", "count": 1}
]
```

**Click 5: +Project Manager**
```
State: resources = [
  {"role": "Developer", "count": 2},
  {"role": "Tester", "count": 1},
  {"role": "QA Engineer", "count": 1},
  {"role": "Project Manager", "count": 1}
]
```

**Frontend Display:**
```
Team Resources:
Developer: 2  [-] [+]
Tester: 1  [-] [+]
QA Engineer: 1  [-] [+]
Project Manager: 1  [-] [+]
```

**User Clicks: [Continue to Next Step]**
```
Frontend sends: "next"
Backend: Move to contacts stage
```

---

#### Stage 6: Contacts

**Backend Processing:**
```python
elif txt.lower() == "next":
    state.stage = "contacts"
    
    # Load contacts from database
    contacts = self._get_contact_options()
    # Returns list of contacts from contacts_data.json
    
    return state, {
        "message": "✅ **Resources selected!**\n\n**Step 6: Contacts**\nSelect a contact:",
        "confirmation_buttons": [
            {
                "id": "contact_mufg",
                "label": "MUFG Bank (Client)",
                "populate_input": "CONTACT: MUFG Bank | Contact Person: John Doe (Senior Manager, IT Department) | Email: john.doe@mufg.com | Phone: +1-555-0123 | Address: 1251 Avenue of the Americas, New York, NY 10020",
                "style": "primary"
            },
            {
                "id": "contact_toyota",
                "label": "Toyota Motor Corporation (Client)",
                "populate_input": "CONTACT: Toyota Motor Corporation | Contact Person: ...",
                "style": "primary"
            },
            # ... more contacts
        ]
    }
```

**Frontend Display:**
```
Bot: ✅ **Resources selected!**

**Step 6: Contacts**
Select a contact:

[MUFG Bank (Client)]
[Toyota Motor Corporation (Client)]
[Sony Corporation (Client)]
[Rakuten Group (Client)]
[SoftBank Group (Client)]
```

**User Clicks: [MUFG Bank (Client)]**
```
Frontend: Input field populated with full contact text
User sends: "CONTACT: MUFG Bank | Contact Person: John Doe (Senior Manager, IT Department) | Email: john.doe@mufg.com | Phone: +1-555-0123 | Address: 1251 Avenue of the Americas, New York, NY 10020"
```

**Backend Processing:**
```python
if state.stage == "contacts":
    txt = "CONTACT: MUFG Bank | Contact Person: John Doe..."
    
    # Parse contact
    if txt.startswith("CONTACT:"):
        org_name = "MUFG Bank"
        selected_contact = find_contact_by_name(org_name)
        
        state.data["contacts"] = {
            "name": "MUFG Bank",
            "email": "john.doe@mufg.com",
            "phone": "+1-555-0123",
            "address": "1251 Avenue of the Americas, New York, NY 10020",
            "contact_person": "John Doe",
            "designation": "Senior Manager",
            "department": "IT Department"
        }
        
        state.stage = "budget"
        
        return state, {
            "message": "✅ **Contact selected: MUFG Bank**\n\n**Contact Details:**\n• **Organization**: MUFG Bank\n• **Contact Person**: John Doe\n• **Designation**: Senior Manager\n• **Department**: IT Department\n• **Email**: john.doe@mufg.com\n• **Phone**: +1-555-0123\n• **Address**: 1251 Avenue of the Americas, New York, NY 10020\n\n**Step 7: Budget**\nFinally, provide the budget details for this project:"
        }
```

---

#### Stage 7: Budget

**User Types:**
```
"$150,000 USD - Fixed price contract with milestone-based payments: 30% on kickoff, 40% on development completion, 30% on final delivery"
```

**Backend Processing:**
```python
if state.stage == "budget":
    state.data["budget"] = "$150,000 USD - Fixed price contract with milestone-based payments: 30% on kickoff, 40% on development completion, 30% on final delivery"
    
    return state, {
        "message": "✅ **Budget captured!**\n\n🎉 **All information collected successfully!**\n\nReady to generate your professional SOW document?",
        "confirmation_buttons": [
            {
                "id": "sow_generate",
                "label": "📄 Generate SOW Document",
                "populate_input": "generate_sow",
                "style": "primary"
            }
        ]
    }
```

**Frontend Display:**
```
Bot: ✅ **Budget captured!**

🎉 **All information collected successfully!**

Ready to generate your professional SOW document?

[📄 Generate SOW Document]
```

---

#### Document Generation

**User Clicks: [📄 Generate SOW Document]**

**Backend - finalize() method:**
```python
def finalize(state: SowState, session_id: str):
    print("🎯 GENERATING SOW VIA NEW_SOW APPLICATION...")
    
    # Collected data:
    collected_data = {
        "project_info": "Mobile e-commerce app with payment gateway integration...",
        "services": "SERVICES: Discovery & Planning (3 weeks)...",
        "deliverables": "iOS mobile app, Android mobile app...",
        "timeline": "6 months project starting January 15, 2025...",
        "resources": [
            {"role": "Developer", "count": 2},
            {"role": "Tester", "count": 1},
            {"role": "QA Engineer", "count": 1},
            {"role": "Project Manager", "count": 1}
        ],
        "contacts": {
            "name": "MUFG Bank",
            "email": "john.doe@mufg.com",
            ...
        },
        "budget": "$150,000 USD - Fixed price contract..."
    }
    
    # Call new_sow adapter
    from .new_sow_adapter import new_sow_adapter
    
    result = await new_sow_adapter.generate_sow_document(
        collected_data,
        "session_abc123"
    )
```

**new_sow_adapter.py:**
```python
async def generate_sow_document(unified_data, session_id):
    # Step 1: Health check
    is_healthy = await self._check_new_sow_health()
    # GET http://localhost:8002/health → 200 OK
    
    # Step 2: Convert data
    raw_responses = self._convert_to_raw_responses(unified_data)
    # Converts:
    # resources: [{"role":"Developer","count":2},...] 
    #         → "Developer: 2 person(s), Tester: 1 person(s), ..."
    # contacts: {"name":"MUFG Bank",...}
    #         → "Client: MUFG Bank, Contact: John Doe, ..."
    
    # Step 3: Call new_sow API
    result = await self._call_new_sow_generation(raw_responses, session_id)
```

**HTTP Request to new_sow:**
```http
POST http://localhost:8002/api/generate-direct
Content-Type: application/json

{
  "template_path": "/path/to/sample_sow_template.docx",
  "project_data": {
    "project_info": "Mobile e-commerce app with payment gateway integration, user authentication, product catalog, and shopping cart functionality",
    "services": "SERVICES: Discovery & Planning (3 weeks), Data Migration (4 weeks), Application Development (8 weeks), Testing & QA (2 weeks), Deployment & Go-Live (1 week)",
    "deliverables": "iOS mobile app, Android mobile app, Admin web dashboard, REST API backend, User documentation, Deployment guide",
    "timeline": "6 months project starting January 15, 2025. Phase 1: Planning (3 weeks), Phase 2: Development (16 weeks), Phase 3: Testing (3 weeks), Phase 4: Deployment (2 weeks)",
    "resources": "Developer: 2 person(s), Tester: 1 person(s), QA Engineer: 1 person(s), Project Manager: 1 person(s)",
    "contacts": "Client: MUFG Bank, Contact: John Doe, Email: john.doe@mufg.com, Phone: +1-555-0123, Address: 1251 Avenue of the Americas, New York, NY 10020",
    "budget": "$150,000 USD - Fixed price contract with milestone-based payments: 30% on kickoff, 40% on development completion, 30% on final delivery"
  },
  "session_id": "session_abc123"
}
```

---


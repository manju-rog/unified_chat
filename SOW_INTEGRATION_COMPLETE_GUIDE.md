# 🎯 COMPLETE SOW INTEGRATION GUIDE
## Unified Chat Frontend ↔️ new_sow Backend

> **For Complete Beginners**: This guide explains EVERY step of how the SOW generation works, from user clicking a button to getting a downloadable document.

---

## 📊 VISUAL FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER'S BROWSER                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  UnifiedChat.jsx (React Component)                            │  │
│  │  - User types: "I want to create SOW"                         │  │
│  │  - Displays chat messages                                     │  │
│  │  - Shows buttons and forms                                    │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              ↓ HTTP POST                             │
│                    http://localhost:8001/api/chat                    │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   UNIFIED BACKEND (Port 8001)                        │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  main.py - /api/chat endpoint                                 │  │
│  │  - Receives user message                                      │  │
│  │  - Detects "SOW" keywords                                     │  │
│  │  - Switches to SOW mode                                       │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              ↓                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  gemini_client.py                                             │  │
│  │  - Sends message to Google Gemini AI                          │  │
│  │  - Gets AI response                                           │  │
│  │  - Collects: Project Info, Services, Timeline, etc.          │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              ↓                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  When user clicks "Generate SOW Document"                     │  │
│  │  - Calls: POST http://localhost:8002/api/generate-direct     │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                               ↓ HTTP POST
                    http://localhost:8002/api/generate-direct
┌─────────────────────────────────────────────────────────────────────┐
│                    NEW_SOW BACKEND (Port 8002)                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  direct_generation.py                                         │  │
│  │  - Receives all collected data                                │  │
│  │  - Calls Gemini AI to extract structured data                │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              ↓                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  data_collector_v2.py                                         │  │
│  │  - Uses Gemini Function Calling                               │  │
│  │  - Extracts: document_number, project_name, services, etc.   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              ↓                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  document_generator.py                                        │  │
│  │  - Fills Word template with data                              │  │
│  │  - Saves to: new_sow/output/SOW_xxx.docx                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                               ↓ Returns filename
┌─────────────────────────────────────────────────────────────────────┐
│                   UNIFIED BACKEND (Port 8001)                        │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  main.py - handle_generate_sow()                              │  │
│  │  - Copies file from new_sow/output to generated_docs_sow/    │  │
│  │  - Triggers browser download                                  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                               ↓ File download
┌─────────────────────────────────────────────────────────────────────┐
│                         USER'S BROWSER                               │
│  📥 Downloads: SOW_Document_20251105_103945.docx                    │
└─────────────────────────────────────────────────────────────────────┘
```

---


## 🔢 STEP-BY-STEP CODE BREAKDOWN

### STEP 1: User Starts SOW Creation (Frontend)

**File**: `unified_ai_chat/frontend/src/UnifiedChat.jsx`

```javascript
// User types: "I want to create SOW"
const handleSendMessage = async () => {
  // This function runs when user presses Enter or clicks Send
  
  const response = await fetch('http://localhost:8001/api/chat', {
    method: 'POST',  // Sending data TO the server
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: userInput,        // "I want to create SOW"
      session_id: sessionId      // Unique ID for this conversation
    })
  });
  
  const data = await response.json();
  // data = { response: "Great! Let's create your SOW...", theme: "sow" }
  
  if (data.theme === 'sow') {
    setCurrentTheme('sow');  // Changes UI to blue theme
  }
}
```

**What happens here?**
- User types message
- JavaScript sends HTTP POST request to backend
- Backend responds with AI message and theme
- UI updates to show SOW mode

---

### STEP 2: Backend Detects SOW Request (Unified Backend)

**File**: `unified_ai_chat/backend/app/main.py`

```python
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    # This function receives the user's message
    
    user_message = request.message  # "I want to create SOW"
    session_id = request.session_id
    
    # Check if user wants to create SOW
    sow_keywords = ["sow", "statement of work", "create sow"]
    
    if any(keyword in user_message.lower() for keyword in sow_keywords):
        # User wants SOW!
        
        # Store in session that we're in SOW mode
        sessions[session_id] = {
            "mode": "sow",
            "stage": "project_info",  # First question
            "collected_data": {}
        }
        
        # Send to Gemini AI to get response
        ai_response = await gemini_client.send_message(
            user_message,
            session_id,
            mode="sow"
        )
        
        return {
            "response": ai_response,
            "theme": "sow",  # Tell frontend to switch theme
            "session_id": session_id
        }
```

**What happens here?**
- Backend receives message
- Checks if message contains SOW keywords
- Switches session to SOW mode
- Sends to Gemini AI for intelligent response
- Returns response + theme to frontend

---

### STEP 3: Gemini AI Asks Questions (Unified Backend)

**File**: `unified_ai_chat/backend/app/gemini_client.py`

```python
async def send_message(self, message: str, session_id: str, mode: str):
    # This function talks to Google Gemini AI
    
    if mode == "sow":
        # Build conversation history
        history = self._build_sow_history(session_id)
        
        # Create chat with Gemini
        chat = self.model.start_chat(history=history)
        
        # Send user's message to Gemini
        response = chat.send_message(message)
        
        # Gemini responds with next question
        # Example: "Great! Please provide project information..."
        
        return response.text
```

**What happens here?**
- Sends user message to Google Gemini AI
- Gemini understands context and asks next question
- Returns AI response to main.py
- main.py sends it back to frontend

---

### STEP 4: User Fills Out Information (Frontend)

**File**: `unified_ai_chat/frontend/src/components/SowControls.jsx`

```javascript
// User sees buttons and forms for each stage

// STAGE 1: Project Info
<textarea 
  placeholder="Describe your project..."
  onChange={(e) => setProjectInfo(e.target.value)}
/>

// STAGE 2: Services
<button onClick={() => handleServiceSelection('standard')}>
  Standard Package
</button>

// STAGE 3: Timeline
<TimelineBuilder 
  onTimelineSubmit={(timeline) => {
    // timeline = { startDate: "2025-01-02", endDate: "2025-09-30", ... }
    sendMessage(`TIMELINE: Start ${timeline.startDate}, End ${timeline.endDate}...`);
  }}
/>

// STAGE 4: Resources
<div className="resource-counter">
  <button onClick={() => setDevelopers(developers + 1)}>+</button>
  <span>{developers}</span>
  <button onClick={() => setDevelopers(developers - 1)}>-</button>
</div>
```

**What happens here?**
- User sees forms and buttons for each stage
- Each input is collected
- When user clicks "Next" or submits, data is sent to backend
- Backend stores the data in session

---


### STEP 5: User Clicks "Generate SOW Document" (Frontend)

**File**: `unified_ai_chat/frontend/src/components/SowControls.jsx`

```javascript
const handleGenerateSOW = async () => {
  // User clicked the big "Generate SOW Document" button!
  
  // Send special message to backend
  await sendMessage("generate_sow");
  
  // This triggers the document generation process
}
```

**What happens here?**
- User clicks button
- Frontend sends "generate_sow" message to backend
- Backend recognizes this as trigger to generate document

---

### STEP 6: Backend Prepares Data for new_sow (Unified Backend)

**File**: `unified_ai_chat/backend/app/main.py`

```python
async def handle_generate_sow(session_id: str):
    # This function is called when user wants to generate document
    
    # Get all collected data from session
    session = sessions[session_id]
    collected_data = session["collected_data"]
    
    # collected_data looks like:
    # {
    #   "project_info": "Document Number: GB-16796941, Design and Development...",
    #   "services": "SERVICES: Discovery & Planning (3 weeks)...",
    #   "deliverables": "Design Review, Development, Testing...",
    #   "timeline": "TIMELINE: Start 2025-01-02, End 2025-09-30...",
    #   "resources": "3 Developers, 1 Tester, 1 Business Analyst...",
    #   "contacts": "CONTACT: MUFG Bank | Contact Person: Hiroshi Tanaka...",
    #   "budget": "$235,000.00"
    # }
    
    # Prepare request for new_sow service
    request_data = {
        "session_id": session_id,
        "template_path": "templates/SOW_Template.docx",
        "project_data": collected_data
    }
    
    # Call new_sow service
    response = requests.post(
        "http://localhost:8002/api/generate-direct",
        json=request_data
    )
    
    # response = { "success": True, "filename": "SOW_xxx.docx" }
    
    if response.status_code == 200:
        result = response.json()
        filename = result["filename"]
        
        # Copy file from new_sow/output to unified_ai_chat/generated_docs_sow
        source = f"../new_sow/output/{filename}"
        destination = f"generated_docs_sow/{filename}"
        shutil.copy(source, destination)
        
        # Return success message
        return {
            "success": True,
            "filename": filename,
            "download_url": f"/api/download-sow/{filename}"
        }
```

**What happens here?**
- Backend collects all data from session
- Formats it into structure new_sow expects
- Makes HTTP POST request to new_sow service (port 8002)
- Waits for new_sow to generate document
- Copies generated file to download folder
- Returns download URL to frontend

---

### STEP 7: new_sow Receives Request (new_sow Backend)

**File**: `new_sow/app/api/direct_generation.py`

```python
@router.post("/generate-direct")
async def generate_direct(request: DirectGenerationRequest):
    # This function receives the generation request
    
    # request contains:
    # - session_id: "abc123"
    # - template_path: "templates/SOW_Template.docx"
    # - project_data: { all the collected information }
    
    logger.info(f"📥 Received request for session: {request.session_id}")
    
    # Create a new session in new_sow
    orchestrator = OrchestratorAgent()
    session = orchestrator.initialize_session(
        session_id=request.session_id,
        template_id="direct_gen",
        template_path=request.template_path
    )
    
    # Store the raw responses
    session.raw_responses = {
        "project_info": request.project_data.get("project_info", ""),
        "services": request.project_data.get("services", ""),
        "deliverables": request.project_data.get("deliverables", ""),
        "timeline": request.project_data.get("timeline", ""),
        "resources": request.project_data.get("resources", ""),
        "contacts": request.project_data.get("contacts", ""),
        "budget": request.project_data.get("budget", "")
    }
    
    # Now extract structured data using Gemini AI
    logger.info("🤖 Calling Gemini to extract structured data...")
    success = await orchestrator.data_collector._extract_all_data_with_function_calling(session)
    
    if not success:
        raise HTTPException(status_code=500, detail="Data extraction failed")
    
    # Generate the Word document
    logger.info("📄 Generating Word document...")
    output_path = await orchestrator.generate_document(request.session_id)
    
    # Return success
    filename = os.path.basename(output_path)
    return {
        "success": True,
        "filename": filename,
        "message": "SOW document generated successfully"
    }
```

**What happens here?**
- new_sow receives all the collected data
- Creates a session to track this generation
- Stores raw text responses
- Calls data_collector to extract structured data
- Generates Word document
- Returns filename

---


### STEP 8: Gemini Extracts Structured Data (new_sow Backend)

**File**: `new_sow/app/agents/data_collector_v2.py`

```python
async def _extract_all_data_with_function_calling(self, session_data):
    # This is the MAGIC function that converts text to structured data
    
    # Build conversation from raw responses
    conversation = self._build_complete_conversation(session_data.raw_responses)
    
    # conversation looks like:
    # """
    # Stage: PROJECT_INFO
    # Question: Please provide project information
    # User Response: Document Number: GB-16796941, Design and Development...
    # 
    # Stage: SERVICES
    # Question: What services do you need?
    # User Response: SERVICES: Discovery & Planning (3 weeks)...
    # 
    # ... (all stages)
    # """
    
    # Create enhanced prompt for Gemini
    enhanced_prompt = f"""
    Extract complete SOW data from this conversation:
    
    {conversation}
    
    CRITICAL INSTRUCTIONS:
    - Extract document_number from text like "Document Number: GB-16796941"
    - Extract project_name from the description
    - Parse services into structured list
    - Parse timeline dates (start_date, end_date)
    - Extract resources with counts
    - Parse contact information
    - Extract budget amount
    
    Use the extract_sow_data function to return structured data.
    """
    
    # Call Gemini with function calling
    response = self.model.generate_content(
        enhanced_prompt,
        tool_config={'function_calling_config': 'AUTO'}
    )
    
    # Gemini returns structured data using the function schema
    function_call = response.candidates[0].content.parts[0].function_call
    extracted_data = dict(function_call.args)
    
    # extracted_data now looks like:
    # {
    #   "document_number": "GB-16796941",
    #   "project_name": "OPF to G-COP Data Extraction Implementation",
    #   "services": [
    #     {"name": "Discovery & Planning", "description": "...", "duration": "3 weeks"},
    #     {"name": "Data Migration", "description": "...", "duration": "4 weeks"}
    #   ],
    #   "deliverables": [
    #     {"name": "Design Document", "description": "...", "sprint_start": 1, "sprint_end": 2}
    #   ],
    #   "start_date": "2025-01-02",
    #   "end_date": "2025-09-30",
    #   "total_sprints": 5,
    #   "resources": [
    #     {"role": "Developer", "count": 3, "allocation": "Full-time"}
    #   ],
    #   "client_contact": {
    #     "name": "Hiroshi Tanaka",
    #     "company": "MUFG Bank",
    #     "email": "corporate@mufg.com"
    #   },
    #   "estimated_expenses": 235000.00
    # }
    
    # Populate session context with structured data
    self._populate_context_from_dict(session_data, extracted_data)
    
    return True  # Success!
```

**What happens here?**
- Takes all raw text responses
- Builds a conversation string
- Sends to Gemini AI with special instructions
- Gemini uses "function calling" to return structured JSON data
- Data is validated and stored in session
- Now we have clean, structured data ready for document generation

**🤔 What is "Function Calling"?**

Function calling is a special Gemini AI feature where you define a schema (structure) and Gemini returns data in that exact format.

```python
# We define the schema:
{
  "document_number": STRING,
  "project_name": STRING,
  "services": ARRAY of OBJECTS,
  "deliverables": ARRAY of OBJECTS,
  ...
}

# Gemini reads the text and returns:
{
  "document_number": "GB-16796941",
  "project_name": "OPF to G-COP Implementation",
  "services": [...]
}
```

It's like telling Gemini: "Here's the format I need, please extract the data and give it to me in this exact structure."

---

### STEP 9: Generate Word Document (new_sow Backend)

**File**: `new_sow/app/services/document_generator.py`

```python
async def generate_document(self, session_id: str):
    # This function creates the actual Word document
    
    # Get session data
    session = state_service.get_session(session_id)
    sow_context = session.sow_context
    
    # Load Word template
    doc = Document(session.template_path)
    # doc is now a Word document object we can modify
    
    # Replace placeholders in template
    # Template has: {{document_number}}, {{project_name}}, etc.
    
    for paragraph in doc.paragraphs:
        # Replace {{document_number}} with actual value
        if "{{document_number}}" in paragraph.text:
            paragraph.text = paragraph.text.replace(
                "{{document_number}}", 
                sow_context.project_info.document_number
            )
        
        # Replace {{project_name}}
        if "{{project_name}}" in paragraph.text:
            paragraph.text = paragraph.text.replace(
                "{{project_name}}", 
                sow_context.project_info.project_name
            )
    
    # Add services table
    services_table = doc.add_table(rows=1, cols=3)
    services_table.style = 'Light Grid Accent 1'
    
    # Add header row
    header_cells = services_table.rows[0].cells
    header_cells[0].text = 'Service'
    header_cells[1].text = 'Description'
    header_cells[2].text = 'Duration'
    
    # Add each service as a row
    for service in sow_context.services:
        row_cells = services_table.add_row().cells
        row_cells[0].text = service.name
        row_cells[1].text = service.description
        row_cells[2].text = service.duration
    
    # Add deliverables, timeline, resources, contacts, budget...
    # (Similar process for each section)
    
    # Save document
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"SOW_Document_{timestamp}.docx"
    output_path = f"output/{filename}"
    
    doc.save(output_path)
    
    logger.info(f"✅ Document saved: {output_path}")
    
    return output_path
```

**What happens here?**
- Loads Word template file
- Replaces placeholders ({{document_number}}, etc.) with actual data
- Creates tables for services, deliverables, resources
- Formats everything nicely
- Saves as new Word document
- Returns file path

---


### STEP 10: File Download (Unified Backend → Frontend)

**File**: `unified_ai_chat/backend/app/main.py`

```python
@app.get("/api/download-sow/{filename}")
async def download_sow(filename: str):
    # This endpoint serves the file for download
    
    file_path = f"generated_docs_sow/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Return file as download
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
```

**File**: `unified_ai_chat/frontend/src/UnifiedChat.jsx`

```javascript
// When backend returns success with download URL
if (response.download_url) {
  // Automatically trigger download in browser
  const link = document.createElement('a');
  link.href = `http://localhost:8001${response.download_url}`;
  link.download = response.filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  // User sees: "📥 Downloading SOW_Document_20251105_103945.docx"
}
```

**What happens here?**
- Backend provides download endpoint
- Frontend creates invisible link
- Clicks it automatically
- Browser downloads file
- User gets Word document!

---

## 📦 DATA STRUCTURE EXAMPLES

### Example 1: Raw Collected Data (from Unified Chat)

```json
{
  "project_info": "Document Number: GB-16796941, Design and Development / Test / Post-Go-live support for OPF to G-COP Data Extraction, Compression, and transfer Implementation. Oracle will cover the following activities: Design Review & Feedback, Development of Applications, File Transfer mechanism, Quality Assurance, Connectivity, SIT, Functional, Non-Functional (Performance, HA & DR), TDM Coordination, Pre-Go Live Support, Go Live Support, Post Go Live Support",
  
  "services": "SERVICES: Discovery & Planning (3 weeks), Data Migration (4 weeks), Application Development (8 weeks), Testing & QA (2 weeks), Deployment & Go-Live (1 week)",
  
  "deliverables": "Design and Development / Test / Post-Go-live support for OPF to G-COP Data Extraction, Compression, and transfer Implementation. Oracle will cover the following activities: Design Review & Feedback, Development of Applications, File Transfer mechanism, Quality Assurance, Connectivity, SIT, Functional, Non-Functional (Performance, HA & DR), TDM Coordination, Pre-Go Live Support, Go Live Support, Post Go Live Support",
  
  "timeline": "TIMELINE: Start 2025-01-02, End 2025-09-30, 5 sprints of 2 weeks each",
  
  "resources": "Add these resources: 3 Developers, 1 Tester, 1 Business Analyst, 1 DevOps, 1 Project Manager",
  
  "contacts": "CONTACT: MUFG Bank | Contact Person: Hiroshi Tanaka (Senior Vice President, Corporate Banking Division) | Email: corporate@mufg.com | Phone: +81-3-3240-1111 | Address: 2-7-1 Marunouchi, Chiyoda-ku, Tokyo 100-8388, Japan",
  
  "budget": "$235,000.00"
}
```

### Example 2: Structured Data (after Gemini extraction)

```json
{
  "document_number": "GB-16796941",
  "project_name": "OPF to G-COP Data Extraction, Compression, and Transfer Implementation",
  
  "objectives": [
    "Design Review & Feedback",
    "Development of Applications and File Transfer mechanism",
    "Quality Assurance (Connectivity, SIT, Functional, Non-Functional)",
    "TDM Coordination",
    "Pre-Go Live, Go Live, and Post Go Live Support"
  ],
  
  "services": [
    {
      "name": "Discovery & Planning",
      "description": "Initial project planning and requirements gathering",
      "duration": "3 weeks"
    },
    {
      "name": "Data Migration",
      "description": "Data extraction and migration activities",
      "duration": "4 weeks"
    },
    {
      "name": "Application Development",
      "description": "Core application development and file transfer mechanism",
      "duration": "8 weeks"
    },
    {
      "name": "Testing & QA",
      "description": "Comprehensive testing including SIT, functional, and non-functional",
      "duration": "2 weeks"
    },
    {
      "name": "Deployment & Go-Live",
      "description": "Production deployment and go-live support",
      "duration": "1 week"
    }
  ],
  
  "deliverables": [
    {
      "name": "Design Review Document",
      "description": "Comprehensive design review and feedback documentation",
      "sprint_start": 1,
      "sprint_end": 1,
      "sprint_duration": 1
    },
    {
      "name": "Application Development",
      "description": "Core applications and file transfer mechanism",
      "sprint_start": 2,
      "sprint_end": 4,
      "sprint_duration": 3
    },
    {
      "name": "Quality Assurance Package",
      "description": "Complete QA including connectivity, SIT, functional, and non-functional testing",
      "sprint_start": 4,
      "sprint_end": 5,
      "sprint_duration": 2
    },
    {
      "name": "Go-Live Support Package",
      "description": "Pre-Go Live, Go Live, and Post Go Live support",
      "sprint_start": 5,
      "sprint_end": 5,
      "sprint_duration": 1
    }
  ],
  
  "start_date": "2025-01-02",
  "end_date": "2025-09-30",
  "total_sprints": 5,
  "sprint_duration": "2 weeks",
  
  "resources": [
    {
      "role": "Developer",
      "team": "Development",
      "count": 3,
      "allocation": "Full-time"
    },
    {
      "role": "Tester",
      "team": "Quality Assurance",
      "count": 1,
      "allocation": "Full-time"
    },
    {
      "role": "Business Analyst",
      "team": "Analysis",
      "count": 1,
      "allocation": "Full-time"
    },
    {
      "role": "DevOps",
      "team": "Operations",
      "count": 1,
      "allocation": "Full-time"
    },
    {
      "role": "Project Manager",
      "team": "Management",
      "count": 1,
      "allocation": "Full-time"
    }
  ],
  
  "client_contact": {
    "name": "Hiroshi Tanaka",
    "company": "MUFG Bank",
    "address": "2-7-1 Marunouchi, Chiyoda-ku, Tokyo 100-8388, Japan",
    "phone": "+81-3-3240-1111",
    "email": "corporate@mufg.com",
    "role": "Senior Vice President, Corporate Banking Division"
  },
  
  "contractor_contact": {
    "name": "Oracle Representative",
    "company": "Oracle Corporation",
    "address": "Oracle Parkway, Redwood City, CA",
    "phone": "+1-650-506-7000",
    "email": "contact@oracle.com",
    "role": "Service Provider"
  },
  
  "milestones": [
    {
      "name": "Discovery & Planning Complete",
      "fee": 47000.00,
      "description": "Completion of initial planning phase"
    },
    {
      "name": "Development Complete",
      "fee": 94000.00,
      "description": "All application development finished"
    },
    {
      "name": "Testing Complete",
      "fee": 47000.00,
      "description": "All QA activities completed"
    },
    {
      "name": "Go-Live",
      "fee": 47000.00,
      "description": "Successful production deployment"
    }
  ],
  
  "estimated_expenses": 235000.00
}
```

---


## 🔍 DETAILED CODE TRACING

### Trace 1: User Message Flow

```
1. User types in browser: "I want to create SOW"
   ↓
2. UnifiedChat.jsx → handleSendMessage()
   ↓
3. fetch('http://localhost:8001/api/chat', { message: "I want to create SOW" })
   ↓
4. unified_ai_chat/backend/app/main.py → @app.post("/api/chat")
   ↓
5. Check: if "sow" in message.lower() → YES!
   ↓
6. sessions[session_id] = { mode: "sow", stage: "project_info" }
   ↓
7. gemini_client.send_message(message, session_id, mode="sow")
   ↓
8. Gemini AI responds: "Great! Let's create your SOW. Please provide project information..."
   ↓
9. Return { response: "Great! Let's...", theme: "sow" }
   ↓
10. UnifiedChat.jsx receives response
   ↓
11. setCurrentTheme('sow') → UI turns blue
   ↓
12. Display AI message in chat
```

### Trace 2: Generate SOW Flow

```
1. User clicks "Generate SOW Document" button
   ↓
2. SowControls.jsx → handleGenerateSOW()
   ↓
3. sendMessage("generate_sow")
   ↓
4. fetch('http://localhost:8001/api/chat', { message: "generate_sow" })
   ↓
5. unified_ai_chat/backend/app/main.py → @app.post("/api/chat")
   ↓
6. Check: if message == "generate_sow" → YES!
   ↓
7. handle_generate_sow(session_id)
   ↓
8. Collect all data from sessions[session_id]["collected_data"]
   ↓
9. requests.post('http://localhost:8002/api/generate-direct', {
      session_id: session_id,
      template_path: "templates/SOW_Template.docx",
      project_data: collected_data
   })
   ↓
10. new_sow/app/api/direct_generation.py → @router.post("/generate-direct")
   ↓
11. orchestrator.initialize_session(session_id, template_path)
   ↓
12. session.raw_responses = project_data
   ↓
13. orchestrator.data_collector._extract_all_data_with_function_calling(session)
   ↓
14. new_sow/app/agents/data_collector_v2.py → _extract_all_data_with_function_calling()
   ↓
15. Build conversation string from raw_responses
   ↓
16. Create enhanced_prompt with instructions
   ↓
17. self.model.generate_content(enhanced_prompt, tool_config='AUTO')
   ↓
18. Gemini AI processes and returns structured data via function calling
   ↓
19. extracted_data = dict(function_call.args)
   ↓
20. _populate_context_from_dict(session_data, extracted_data)
   ↓
21. Return True (success)
   ↓
22. Back to direct_generation.py
   ↓
23. orchestrator.generate_document(session_id)
   ↓
24. new_sow/app/services/document_generator.py → generate_document()
   ↓
25. Load Word template: doc = Document(template_path)
   ↓
26. Replace placeholders: {{document_number}} → "GB-16796941"
   ↓
27. Add tables for services, deliverables, resources
   ↓
28. doc.save("output/SOW_Document_20251105_103945.docx")
   ↓
29. Return filename
   ↓
30. Back to unified_ai_chat/backend/app/main.py
   ↓
31. shutil.copy("../new_sow/output/SOW_xxx.docx", "generated_docs_sow/SOW_xxx.docx")
   ↓
32. Return { success: True, filename: "SOW_xxx.docx", download_url: "/api/download-sow/SOW_xxx.docx" }
   ↓
33. UnifiedChat.jsx receives response
   ↓
34. Create download link and click it
   ↓
35. Browser downloads file
   ↓
36. User has Word document! 🎉
```

---

## 🎨 UI STATE CHANGES

### Theme Switching

```javascript
// Initial state (default theme)
currentTheme = 'default'
// UI: Purple/pink gradient

// User says "I want to create SOW"
// Backend returns: { theme: 'sow' }
setCurrentTheme('sow')
// UI: Blue gradient

// User says "Who is absent today?"
// Backend returns: { theme: 'absence' }
setCurrentTheme('absence')
// UI: Green gradient
```

### SOW Controls Visibility

```javascript
// When theme is 'sow' and stage is 'services'
{currentTheme === 'sow' && sowStage === 'services' && (
  <div className="service-selection">
    <button>Standard Package</button>
    <button>Custom Services</button>
  </div>
)}

// When theme is 'sow' and stage is 'timeline'
{currentTheme === 'sow' && sowStage === 'timeline' && (
  <TimelineBuilder onTimelineSubmit={handleTimelineSubmit} />
)}

// When theme is 'sow' and stage is 'completed'
{currentTheme === 'sow' && sowStage === 'completed' && (
  <button className="generate-button" onClick={handleGenerateSOW}>
    Generate SOW Document
  </button>
)}
```

---

## 🔧 CONFIGURATION FILES

### Port Configuration

```
unified_ai_chat/frontend:     Port 3001 (React dev server)
unified_ai_chat/backend:      Port 8001 (FastAPI)
new_sow:                      Port 8002 (FastAPI)
absence-management:           Port 8010 (Spring Boot)
```

### Environment Variables

**unified_ai_chat/backend/.env**
```bash
GEMINI_API_KEY=your_gemini_api_key_here
NEW_SOW_API_URL=http://localhost:8002
ABSENCE_API_URL=http://localhost:8010
```

**new_sow/.env**
```bash
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-pro
```

---

## 🚀 STARTING THE SYSTEM

### Option 1: Start All Services

```bash
# From project root
cd unified_ai_chat
./start_all_different_ports.sh
```

This starts:
1. Absence Management (port 8010)
2. new_sow backend (port 8002)
3. Unified backend (port 8001)
4. Unified frontend (port 3001)

### Option 2: Start Individually

```bash
# Terminal 1: Absence Management
cd ai_absence-ai_absence_mi/backend/absence-management
./mvnw spring-boot:run

# Terminal 2: new_sow
cd new_sow
python run_backend_8002.py

# Terminal 3: Unified Backend
cd unified_ai_chat/backend
python run_server.py

# Terminal 4: Unified Frontend
cd unified_ai_chat/frontend
npm start
```

---

## 🐛 DEBUGGING TIPS

### Check if Services are Running

```bash
# Check ports
lsof -i :3001  # Frontend
lsof -i :8001  # Unified backend
lsof -i :8002  # new_sow
lsof -i :8010  # Absence management

# Test endpoints
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8010/api/health
```

### View Logs

```bash
# Unified backend logs
tail -f unified_ai_chat/backend/logs/app.log

# new_sow logs
tail -f new_sow/logs/app.log

# Frontend console
# Open browser DevTools → Console tab
```

### Common Issues

**Issue 1: "Connection refused" error**
- Solution: Make sure all services are running
- Check: `lsof -i :8001` and `lsof -i :8002`

**Issue 2: "MALFORMED_FUNCTION_CALL" error**
- Solution: Check Gemini API key is valid
- Check: Data format being sent to Gemini

**Issue 3: File not found error**
- Solution: Check file paths in code
- Verify: `new_sow/output/` directory exists
- Verify: `unified_ai_chat/generated_docs_sow/` directory exists

**Issue 4: Document not downloading**
- Solution: Check browser console for errors
- Verify: File was copied to `generated_docs_sow/`
- Check: Download endpoint returns 200 status

---

## 📚 KEY CONCEPTS FOR BEGINNERS

### What is HTTP POST?

```javascript
// Sending data TO the server
fetch('http://localhost:8001/api/chat', {
  method: 'POST',  // We're sending data
  body: JSON.stringify({ message: "Hello" })
})
```

### What is JSON?

```javascript
// JavaScript Object Notation - a way to structure data
{
  "name": "John",
  "age": 30,
  "hobbies": ["reading", "coding"]
}
```

### What is async/await?

```javascript
// Wait for something to finish before continuing
async function getData() {
  const response = await fetch('http://api.com/data');
  // Wait here until fetch completes
  const data = await response.json();
  // Wait here until json parsing completes
  return data;
}
```

### What is a Session?

```python
# A way to remember information about a user
sessions = {
  "user123": {
    "mode": "sow",
    "collected_data": {...}
  }
}

# Later, we can retrieve this user's data
user_data = sessions["user123"]
```

### What is an API Endpoint?

```python
# A URL that does something when you call it
@app.post("/api/chat")  # This is an endpoint
async def chat_endpoint(request):
    # Do something
    return response
```

When you call `http://localhost:8001/api/chat`, this function runs!

---

## 🎯 SUMMARY

**The Complete Flow in Simple Terms:**

1. **User talks to chatbot** → Frontend sends message to unified backend
2. **Backend detects SOW request** → Switches to SOW mode
3. **AI asks questions** → User fills out forms
4. **User clicks Generate** → Backend sends all data to new_sow
5. **new_sow uses Gemini AI** → Converts text to structured data
6. **Document generator** → Creates Word document from template
7. **File is copied** → From new_sow to unified chat folder
8. **Browser downloads** → User gets the document!

**Key Technologies:**
- **React**: Frontend UI framework
- **FastAPI**: Python web framework for backends
- **Gemini AI**: Google's AI for understanding and extracting data
- **python-docx**: Library for creating Word documents
- **HTTP/REST**: How services communicate

**Why Two Backends?**
- **Unified Backend (8001)**: Handles chat, coordinates everything
- **new_sow Backend (8002)**: Specialized in SOW generation only
- This separation makes the code cleaner and easier to maintain

---

## 📖 FURTHER READING

- **React Tutorial**: https://react.dev/learn
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Gemini AI Function Calling**: https://ai.google.dev/docs/function_calling
- **python-docx Guide**: https://python-docx.readthedocs.io/

---

**Created**: November 5, 2025  
**Last Updated**: November 5, 2025  
**Version**: 1.0


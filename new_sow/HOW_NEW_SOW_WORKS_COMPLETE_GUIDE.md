# 📚 How new_sow Works - Complete Beginner's Guide

## 🎯 What is new_sow?

**new_sow** is an AI-powered application that helps you create professional Statement of Work (SOW) documents through a conversational interface. Think of it as a smart assistant that asks you questions, collects information, and generates a polished document.

---

## 🏗️ The Big Picture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐      ┌──────────────┐
│   You talk  │ ───> │  new_sow     │ ───> │   Gemini    │ ───> │  Beautiful   │
│   to bot    │      │  collects    │      │   enhances  │      │  SOW         │
│             │      │  answers     │      │   content   │      │  Document    │
└─────────────┘      └──────────────┘      └─────────────┘      └──────────────┘
```

### The Process (Simple Version)
1. **You start** a conversation
2. **Bot asks** 7 questions (project info, services, deliverables, etc.)
3. **You answer** each question
4. **Gemini AI** processes your answers and makes them professional
5. **Document** is generated from a template

---

## 📁 Project Structure

```
new_sow/
├── app/
│   ├── agents/              # The "brains" - AI agents
│   │   ├── orchestrator.py      # Main coordinator
│   │   └── data_collector_v2.py # Collects & processes data
│   ├── api/                 # How you talk to the app
│   │   ├── endpoints.py         # REST API routes
│   │   ├── websocket.py         # Real-time chat
│   │   └── direct_generation.py # Direct document generation
│   ├── models/              # Data structures
│   │   └── sow_models.py        # All data models
│   ├── services/            # Helper services
│   │   ├── document_service.py  # Creates documents
│   │   ├── state_service.py     # Remembers conversations
│   │   └── contacts_service.py  # Manages contacts
│   ├── utils/               # Utilities
│   │   └── prompts.py           # Gemini prompts
│   ├── config.py            # Settings
│   └── main.py              # Application entry point
├── templates/               # Word document templates
├── output/                  # Generated documents
├── logs/                    # Application logs
└── sample_sow_template.docx # Default template
```

---

## 🚀 How to Start the Application

### Step 1: Setup Environment
```bash
cd new_sow
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure API Key
Create a `.env` file:
```
GEMINI_API_KEY=your_actual_api_key_here
```

### Step 3: Start the Server
```bash
python -m uvicorn app.main:app --reload --port 8002
```

The app is now running at `http://localhost:8002`

---

## 🔄 The Complete Flow (Step by Step)

Let me explain EXACTLY what happens when you use new_sow...


### 🎬 Part 1: Starting a Session

#### What Happens:
```python
# File: app/main.py
# When you start the app, FastAPI initializes everything
```

**Step 1.1: Application Starts**
- FastAPI loads all routes and services
- Creates directories (templates/, output/, logs/)
- Validates configuration (checks API key, etc.)

**Step 1.2: You Create a Session**
```
POST /api/create-session
{
  "template_id": "optional_template_id"
}
```

**What happens inside:**
```python
# File: app/services/state_service.py
def create_session(session_id, template_id, template_path):
    session = SessionData(
        session_id=session_id,
        template_id=template_id,
        template_path=template_path,
        current_stage=ConversationStage.INITIAL,
        raw_responses={},
        sow_context=SOWContext()
    )
    # Store in memory
    self._sessions[session_id] = session
    return session
```

**Result:** You get a `session_id` (like "abc123") that tracks your conversation.

---

### 🎬 Part 2: The Conversation (7 Stages)

#### The 7 Stages:
1. **INITIAL** - Welcome message
2. **PROJECT_INFO** - Document number, project name, objectives
3. **SERVICES** - What work will be done
4. **DELIVERABLES** - What will be delivered
5. **TIMELINE** - Start date, end date, sprints
6. **RESOURCES** - Team members needed
7. **CONTACTS** - Client and contractor information
8. **BUDGET** - Milestones and fees
9. **COMPLETED** - All done!

#### How Each Stage Works:

**Stage Flow:**
```
You: "SOW-2025-001, Cloud Migration, reduce costs"
  ↓
Bot stores your answer
  ↓
Bot moves to next stage
  ↓
Bot asks next question
```

**The Code (Simplified):**
```python
# File: app/agents/data_collector_v2.py
async def process_user_input(session_data, user_message):
    # 1. Get current stage
    current_stage = session_data.current_stage
    
    # 2. Store your answer
    session_data.raw_responses[current_stage.value] = user_message
    
    # 3. Move to next stage
    next_stage = self._determine_next_stage(current_stage)
    session_data.current_stage = next_stage
    
    # 4. Get next question
    next_question = self.prompts.STAGE_QUESTIONS[next_stage.value]
    
    return next_question, session_data
```

---

### 🎬 Part 3: Data Collection Complete

After you answer all 7 questions, something special happens...

**The Trigger:**
```python
if next_stage == ConversationStage.COMPLETED:
    # Time to process everything!
    success = await self._extract_all_data_with_function_calling(session_data)
```

This is where the magic happens! Let's dive deep...

---

## 🧠 The AI Processing (Most Important Part!)

### What is "Function Calling"?

**Simple Explanation:**
Instead of asking Gemini to write text, we ask it to fill out a form with specific fields.

**Example:**
```
❌ Bad way: "Gemini, tell me about the project"
   Result: "The project is about cloud migration and..."

✅ Good way: "Gemini, extract data and call extract_sow_data function"
   Result: {
     "document_number": "SOW-2025-001",
     "project_name": "Cloud Migration",
     "objectives": ["reduce costs", "improve scalability"]
   }
```

### The Function Schema

**What we tell Gemini:**
```python
# File: app/agents/data_collector_v2.py
self.sow_function = genai.protos.Tool(
    function_declarations=[
        genai.protos.FunctionDeclaration(
            name="extract_sow_data",
            description="Extract complete Statement of Work data",
            parameters={
                "document_number": "string",
                "project_name": "string",
                "objectives": "array of strings",
                "services": "array of objects",
                "deliverables": "array of objects",
                # ... and more
            }
        )
    ]
)
```

**Translation:** "Hey Gemini, I need you to extract data and organize it exactly like this structure."

---

### The Extraction Process (Step by Step)

**Step 1: Build the Conversation**
```python
def _build_complete_conversation(raw_responses):
    conversation = ""
    for stage, answer in raw_responses.items():
        conversation += f"""
        Stage: {stage}
        Question: {question_for_stage}
        Your Answer: {answer}
        """
    return conversation
```

**Example Output:**
```
Stage: PROJECT_INFO
Question: Please provide document number, project name, and objectives
Your Answer: SOW-2025-001, Cloud Migration, reduce costs by 40%

Stage: SERVICES
Question: Tell me about the services
Your Answer: standard

Stage: DELIVERABLES
Question: List the deliverables
Your Answer: 1. Architecture Design, 2. Migrated Code, 3. Test Plan
...
```

**Step 2: Create the Prompt**
```python
enhanced_prompt = f"""
Extract complete SOW data from this conversation:

{conversation}

CRITICAL INSTRUCTIONS:
- Extract ONLY what the user provided
- Use YYYY-MM-DD format for dates
- Return structured JSON
- Be precise and accurate

Use the extract_sow_data function to return all information.
"""
```

**Step 3: Call Gemini**
```python
response = self.model.generate_content(
    enhanced_prompt,
    tool_config={'function_calling_config': 'AUTO'}
)
```

**What Gemini Does:**
1. Reads the entire conversation
2. Understands the context
3. Extracts structured data
4. Calls the `extract_sow_data` function with the data
5. Returns JSON

**Step 4: Get the Result**
```python
function_call = response.candidates[0].content.parts[0].function_call
extracted_data = dict(function_call.args)
```

**Example Result:**
```json
{
  "document_number": "SOW-2025-001",
  "project_name": "Cloud Migration Project",
  "objectives": [
    "Reduce infrastructure costs by 40%",
    "Improve scalability",
    "Enhance security posture"
  ],
  "services": [
    {
      "name": "Discovery & Planning",
      "description": "Initial assessment and planning",
      "duration": "3 weeks"
    }
  ],
  "deliverables": [
    {
      "name": "Architecture Design",
      "description": "Detailed AWS architecture with diagrams",
      "sprint_start": 1,
      "sprint_end": 2
    }
  ],
  "start_date": "2025-02-01",
  "end_date": "2025-07-31",
  "total_sprints": 12,
  "resources": [...],
  "milestones": [...]
}
```

---

## 📝 Data Models (What Gets Stored)

### The Main Container: SOWContext
```python
# File: app/models/sow_models.py
class SOWContext:
    project_info: ProjectInfo          # Document number, name, objectives
    services: List[Service]            # What work will be done
    deliverables: List[Deliverable]    # What will be delivered
    timeline: ProjectTimeline          # Dates and sprints
    resources: List[Resource]          # Team members
    contractor_contact: Contact        # Your company info
    client_contact: Contact            # Client company info
    milestones: List[Milestone]        # Payment milestones
    total_fee: float                   # Total project cost
    estimated_expenses: float          # Additional expenses
    assumptions: List[str]             # Project assumptions
    terms: List[str]                   # Terms and conditions
```

### Example: ProjectInfo
```python
class ProjectInfo:
    document_number: str  # "SOW-2025-001"
    project_name: str     # "Cloud Migration Project"
    objectives: List[str] # ["reduce costs", "improve scalability"]
```

### Example: Service
```python
class Service:
    name: str         # "Discovery & Planning"
    description: str  # "Initial assessment and planning activities"
    duration: str     # "3 weeks"
```

### Example: Deliverable
```python
class Deliverable:
    id: int              # 1
    name: str            # "Architecture Design"
    description: str     # "Detailed AWS architecture with diagrams"
    sprint_start: int    # 1
    sprint_end: int      # 2
    sprint_duration: int # 2
```

---

## 🎨 Document Generation

After Gemini extracts all the data, it's time to create the document!

### Step 1: Prepare the Context
```python
# File: app/services/document_service.py
def prepare_context(sow_context):
    context = {
        "document_number": sow_context.project_info.document_number,
        "project_name": sow_context.project_info.project_name,
        "objectives": sow_context.project_info.objectives,
        "services": [s.model_dump() for s in sow_context.services],
        "deliverables": [d.model_dump() for d in sow_context.deliverables],
        "start_date": sow_context.timeline.start_date.strftime("%B %d, %Y"),
        "end_date": sow_context.timeline.end_date.strftime("%B %d, %Y"),
        # ... and more
    }
    return context
```

**Example Context:**
```python
{
    "document_number": "SOW-2025-001",
    "project_name": "Cloud Migration Project",
    "start_date": "February 01, 2025",
    "end_date": "July 31, 2025",
    "services": [
        {"name": "Discovery & Planning", "description": "...", "duration": "3 weeks"}
    ]
}
```

### Step 2: Load the Template
```python
from docxtpl import DocxTemplate

doc = DocxTemplate("sample_sow_template.docx")
```

**What's in the Template?**
A Word document with placeholders like:
```
Document Number: {{ document_number }}
Project Name: {{ project_name }}

Services:
{% for service in services %}
- {{ service.name }}: {{ service.description }}
{% endfor %}
```

### Step 3: Render the Document
```python
doc.render(context)
```

**What happens:**
- `{{ document_number }}` → "SOW-2025-001"
- `{{ project_name }}` → "Cloud Migration Project"
- The loop creates a list of all services

### Step 4: Save the Document
```python
output_path = "output/SOW_Cloud_Migration_20251028.docx"
doc.save(output_path)
```

**Result:** A beautiful, professional SOW document!

---

## 🔌 API Endpoints

### 1. Create Session
```
POST /api/create-session
```
**Purpose:** Start a new conversation
**Returns:** `session_id`

### 2. WebSocket Chat
```
WS /api/ws/{session_id}
```
**Purpose:** Real-time conversation
**How it works:**
- You send: `{"message": "SOW-2025-001, Cloud Migration"}`
- Bot replies: `{"message": "Great! Now tell me about services...", "stage": "services"}`

### 3. Generate Document
```
POST /api/generate-document/{session_id}
```
**Purpose:** Create the final document
**Returns:** Path to generated document

### 4. Download Document
```
GET /api/download/{session_id}
```
**Purpose:** Download the generated document
**Returns:** DOCX file

### 5. Direct Generation (Advanced)
```
POST /api/generate-direct
{
  "template_path": "path/to/template.docx",
  "project_data": {
    "project_info": "...",
    "services": "...",
    ...
  },
  "session_id": "abc123"
}
```
**Purpose:** Generate document without conversation
**Use case:** When another app (like unified_ai_chat) collects data

---

## 🎯 The Prompts (How Gemini Knows What to Do)

### Location: `app/utils/prompts.py`

### 1. STAGE_QUESTIONS
```python
STAGE_QUESTIONS = {
    "project_info": "Please provide document number, project name, and objectives",
    "services": "Tell me about the services...",
    "deliverables": "List the deliverables...",
    # ... for each stage
}
```
**Purpose:** Questions the bot asks you

### 2. DATA_EXTRACTION_PROMPT
```python
DATA_EXTRACTION_PROMPT = """
Extract structured information from the user's response.

Stage: {stage}
User Response: "{user_message}"

Instructions:
- Extract ONLY what the user provided
- Use YYYY-MM-DD format for dates
- Return valid JSON

Expected Format:
{expected_structure}
"""
```
**Purpose:** Tells Gemini how to extract data from your answers

### 3. VALIDATION_PROMPT
```python
VALIDATION_PROMPT = """
Validate the extracted data for completeness.

Checks:
1. All required fields present
2. Data types correct
3. Dates logical
4. Numbers positive
"""
```
**Purpose:** Ensures data quality

---

## 🔄 Complete Example (End to End)

Let's trace a complete example from start to finish...


### 📖 Complete Example: Creating a Cloud Migration SOW

#### Step 1: Start Session
```bash
curl -X POST http://localhost:8002/api/create-session
```

**Response:**
```json
{
  "session_id": "abc123",
  "message": "Session created successfully"
}
```

**What happened internally:**
```python
# state_service.py creates a new SessionData object
session = SessionData(
    session_id="abc123",
    current_stage=ConversationStage.INITIAL,
    raw_responses={},
    sow_context=SOWContext()
)
```

---

#### Step 2: Connect via WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8002/api/ws/abc123');
```

**Bot sends welcome:**
```json
{
  "role": "assistant",
  "message": "Hello! I'll help you create a SOW. First, upload your template...",
  "stage": "initial",
  "progress": 0.0
}
```

---

#### Step 3: Answer Project Info
**You send:**
```json
{
  "message": "SOW-2025-001, Cloud Migration Project, objectives: reduce costs by 40%, improve scalability, enhance security"
}
```

**What happens:**
```python
# 1. orchestrator.py receives message
bot_response = await orchestrator.handle_message("abc123", user_message)

# 2. data_collector_v2.py processes it
session_data.raw_responses["project_info"] = user_message
session_data.current_stage = ConversationStage.SERVICES

# 3. Bot asks next question
next_question = prompts.STAGE_QUESTIONS["services"]
```

**Bot responds:**
```json
{
  "role": "assistant",
  "message": "Great! Now tell me about the services. Type 'standard' for standard package or 'custom' for custom services.",
  "stage": "services",
  "progress": 14.3
}
```

---

#### Step 4: Select Services
**You send:**
```json
{
  "message": "standard"
}
```

**What happens:**
```python
# Special handling for "standard"
if user_message.lower() == "standard":
    # Auto-populate with standard services
    for standard_service in STANDARD_SERVICES:
        service = Service(
            name=standard_service["name"],
            description=standard_service["description"],
            duration=standard_service["duration"]
        )
        session_data.sow_context.services.append(service)
    
    # Move to next stage
    session_data.current_stage = ConversationStage.DELIVERABLES
```

**Bot responds:**
```json
{
  "role": "assistant",
  "message": "✅ Standard services package applied! Now let's define deliverables...",
  "stage": "deliverables",
  "progress": 28.6
}
```

---

#### Step 5: List Deliverables
**You send:**
```json
{
  "message": "1. Architecture Design Document\n2. Migrated Application Code\n3. Infrastructure as Code\n4. Test Plan & Results"
}
```

**What happens:**
```python
# Store the response
session_data.raw_responses["deliverables"] = user_message

# Move to next stage
session_data.current_stage = ConversationStage.TIMELINE
```

**Bot responds:**
```json
{
  "role": "assistant",
  "message": "Perfect! Now for the timeline. Provide start date, end date, and number of sprints.",
  "stage": "timeline",
  "progress": 42.9
}
```

---

#### Step 6: Provide Timeline
**You send:**
```json
{
  "message": "Start: 2025-02-01, End: 2025-07-31, 12 sprints, 2 weeks each"
}
```

---

#### Step 7: List Resources
**You send:**
```json
{
  "message": "Cloud Architect: 1, Senior Developer: 2, DevOps Engineer: 2, QA Engineer: 1, Project Manager: 1"
}
```

---

#### Step 8: Provide Contacts
**You send:**
```json
{
  "message": "MUFG Bank"
}
```

**What happens:**
```python
# contacts_service.py looks up the company
client_contact = contacts_service.get_client_contact("MUFG Bank")

# Returns full contact details from database
{
  "name": "John Smith",
  "company": "MUFG Bank",
  "address": "1251 Avenue of the Americas, New York, NY 10020",
  "phone": "+1 (212) 555-0100",
  "email": "john.smith@mufg.com",
  "role": "VP of Technology"
}
```

---

#### Step 9: Provide Budget
**You send:**
```json
{
  "message": "Milestone 1: Architecture - $80,000\nMilestone 2: Migration - $150,000\nMilestone 3: Testing - $70,000\nTotal: $300,000"
}
```

**Bot responds:**
```json
{
  "role": "assistant",
  "message": "Perfect! All information collected. Processing with Gemini AI...",
  "stage": "completed",
  "progress": 100.0
}
```

---

#### Step 10: Gemini Processing (The Magic!)

**What happens now:**
```python
# 1. Build complete conversation
conversation = """
Stage: PROJECT_INFO
Answer: SOW-2025-001, Cloud Migration Project, objectives: reduce costs...

Stage: SERVICES
Answer: standard

Stage: DELIVERABLES
Answer: 1. Architecture Design Document...

Stage: TIMELINE
Answer: Start: 2025-02-01, End: 2025-07-31, 12 sprints...

Stage: RESOURCES
Answer: Cloud Architect: 1, Senior Developer: 2...

Stage: CONTACTS
Answer: MUFG Bank

Stage: BUDGET
Answer: Milestone 1: Architecture - $80,000...
"""

# 2. Create enhanced prompt
prompt = f"""
Extract complete SOW data from this conversation:

{conversation}

CRITICAL INSTRUCTIONS:
- Extract ONLY what the user provided
- Use YYYY-MM-DD format for dates
- For deliverables, allocate sprints intelligently
- Return structured JSON

Use the extract_sow_data function.
"""

# 3. Call Gemini with function calling
response = model.generate_content(
    prompt,
    tool_config={'function_calling_config': 'AUTO'}
)

# 4. Get structured data
extracted_data = dict(response.candidates[0].content.parts[0].function_call.args)
```

**Gemini returns:**
```json
{
  "document_number": "SOW-2025-001",
  "project_name": "Cloud Migration Project",
  "objectives": [
    "Reduce infrastructure costs by 40%",
    "Improve scalability",
    "Enhance security posture"
  ],
  "services": [
    {
      "name": "Discovery & Planning",
      "description": "Initial project assessment, requirements gathering, stakeholder interviews, and comprehensive project planning. This phase establishes the foundation for successful project execution through detailed analysis and strategic planning activities.",
      "duration": "3 weeks"
    },
    {
      "name": "Data Migration",
      "description": "Complete data migration services including data mapping, transformation, validation, and migration execution. Ensures data integrity and completeness throughout the migration process with comprehensive testing and validation.",
      "duration": "4 weeks"
    }
    // ... more services
  ],
  "deliverables": [
    {
      "name": "Architecture Design Document",
      "description": "Detailed AWS architecture design document including system diagrams, component specifications, security architecture, and deployment strategy. Provides comprehensive blueprint for the migration project.",
      "sprint_start": 1,
      "sprint_end": 2,
      "sprint_duration": 2
    },
    {
      "name": "Migrated Application Code",
      "description": "Fully refactored and optimized application code migrated to AWS cloud infrastructure. Includes all necessary modifications for cloud-native operation, performance optimization, and scalability improvements.",
      "sprint_start": 3,
      "sprint_end": 8,
      "sprint_duration": 6
    }
    // ... more deliverables
  ],
  "start_date": "2025-02-01",
  "end_date": "2025-07-31",
  "total_sprints": 12,
  "sprint_duration": "2 weeks",
  "resources": [
    {
      "role": "Cloud Architect",
      "team": "Architecture",
      "count": 1,
      "allocation": "Full-time"
    },
    {
      "role": "Senior Developer",
      "team": "Development",
      "count": 2,
      "allocation": "Full-time"
    }
    // ... more resources
  ],
  "contractor_contact": {
    "name": "Jane Doe",
    "company": "Tech Solutions Inc.",
    "address": "123 Tech Street, San Francisco, CA 94105",
    "phone": "+1 (415) 555-0200",
    "email": "jane.doe@techsolutions.com",
    "role": "Senior Project Manager"
  },
  "client_contact": {
    "name": "John Smith",
    "company": "MUFG Bank",
    "address": "1251 Avenue of the Americas, New York, NY 10020",
    "phone": "+1 (212) 555-0100",
    "email": "john.smith@mufg.com",
    "role": "VP of Technology"
  },
  "milestones": [
    {
      "name": "Architecture Design Completion",
      "fee": 80000.00,
      "description": "Upon completion of architecture design and approval"
    },
    {
      "name": "Migration Completion",
      "fee": 150000.00,
      "description": "Upon successful migration of all applications"
    },
    {
      "name": "Testing and Go-Live",
      "fee": 70000.00,
      "description": "Upon completion of testing and production deployment"
    }
  ],
  "estimated_expenses": 15000.00
}
```

**Notice what Gemini did:**
- ✅ Extracted all data accurately
- ✅ Enhanced descriptions to be professional
- ✅ Allocated sprints intelligently (deliverable 1: sprints 1-2, deliverable 2: sprints 3-8)
- ✅ Looked up contact details for MUFG Bank
- ✅ Parsed budget into structured milestones
- ✅ Converted dates to YYYY-MM-DD format

---

#### Step 11: Populate SOWContext

**What happens:**
```python
# File: app/agents/data_collector_v2.py
def _populate_context_from_dict(session_data, extracted_data):
    # Project Info
    session_data.sow_context.project_info = ProjectInfo(
        document_number=extracted_data["document_number"],
        project_name=extracted_data["project_name"],
        objectives=extracted_data["objectives"]
    )
    
    # Services (already populated from standard package)
    # Skip if already populated
    
    # Deliverables
    for idx, deliv in enumerate(extracted_data["deliverables"], 1):
        deliverable = Deliverable(
            id=idx,
            name=deliv["name"],
            description=deliv["description"],
            sprint_start=deliv["sprint_start"],
            sprint_end=deliv["sprint_end"],
            sprint_duration=deliv["sprint_duration"]
        )
        session_data.sow_context.deliverables.append(deliverable)
    
    # Timeline
    session_data.sow_context.timeline = ProjectTimeline(
        start_date=datetime.strptime(extracted_data["start_date"], "%Y-%m-%d").date(),
        end_date=datetime.strptime(extracted_data["end_date"], "%Y-%m-%d").date(),
        total_sprints=extracted_data["total_sprints"],
        sprint_duration=extracted_data["sprint_duration"]
    )
    
    # Resources, Contacts, Milestones...
    # (similar process for each)
```

**Result:** `session_data.sow_context` now contains all structured data!

---

#### Step 12: Generate Document

**You call:**
```bash
curl -X POST http://localhost:8002/api/generate-document/abc123
```

**What happens:**
```python
# File: app/agents/orchestrator.py
async def generate_document(session_id):
    # 1. Get session data
    session_data = state_service.get_session(session_id)
    
    # 2. Generate document
    output_path = document_service.generate_document(
        template_path=session_data.template_path,
        sow_context=session_data.sow_context
    )
    
    return output_path
```

**Inside document_service.generate_document:**
```python
# 1. Load template
doc = DocxTemplate("sample_sow_template.docx")

# 2. Prepare context
context = {
    "document_number": "SOW-2025-001",
    "project_name": "Cloud Migration Project",
    "objectives": ["Reduce costs by 40%", "Improve scalability", "Enhance security"],
    "services": [
        {
            "name": "Discovery & Planning",
            "description": "Initial project assessment...",
            "duration": "3 weeks"
        }
    ],
    "deliverables": [
        {
            "id": 1,
            "name": "Architecture Design Document",
            "description": "Detailed AWS architecture...",
            "sprint_start": 1,
            "sprint_end": 2
        }
    ],
    "start_date": "February 01, 2025",
    "end_date": "July 31, 2025",
    "total_sprints": 12,
    "resources": [...],
    "contractor_name": "Jane Doe",
    "contractor_company": "Tech Solutions Inc.",
    "client_name": "John Smith",
    "client_company": "MUFG Bank",
    "milestones": [...],
    "total_fee": "$300,000.00",
    "current_date": "October 28, 2025"
}

# 3. Render template
doc.render(context)

# 4. Save document
output_path = "output/SOW_Cloud_Migration_Project_20251028_143022.docx"
doc.save(output_path)
```

**Result:** Professional SOW document created!

---

#### Step 13: Download Document

**You call:**
```bash
curl -X GET http://localhost:8002/api/download/abc123 --output my_sow.docx
```

**What happens:**
```python
# File: app/api/endpoints.py
@router.get("/download/{session_id}")
async def download_document(session_id: str):
    session = state_service.get_session(session_id)
    output_path = session.output_path
    
    return FileResponse(
        path=output_path,
        filename=os.path.basename(output_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
```

**Result:** You get your beautiful SOW document!

---

## 🎯 Key Concepts Explained

### 1. Session Management

**What is a session?**
A session is like a conversation thread. It remembers:
- What stage you're at
- All your answers
- The extracted data
- The generated document path

**Why sessions?**
- Multiple users can use the app simultaneously
- Each user has their own conversation
- Data doesn't get mixed up

**How long do sessions last?**
- Default: 1 hour (3600 seconds)
- Configurable in `config.py`
- Expired sessions are automatically cleaned up

---

### 2. Conversation Stages

**Why stages?**
- Organizes the conversation
- Ensures all information is collected
- Tracks progress (14%, 28%, 42%, etc.)

**Stage Flow:**
```
INITIAL → PROJECT_INFO → SERVICES → DELIVERABLES → 
TIMELINE → RESOURCES → CONTACTS → BUDGET → COMPLETED
```

**Can you skip stages?**
No, you must go through all stages in order. This ensures completeness.

---

### 3. Function Calling vs Regular Prompts

**Regular Prompt (Old Way):**
```
Prompt: "Extract the project name from: SOW-2025-001, Cloud Migration"
Response: "The project name is Cloud Migration"
```
Problem: You get text, not structured data.

**Function Calling (New Way):**
```
Prompt: "Extract data and call extract_sow_data function"
Response: {
  "document_number": "SOW-2025-001",
  "project_name": "Cloud Migration"
}
```
Benefit: You get structured, parseable data!

---

### 4. Standard vs Custom Services

**Standard Services:**
- Pre-defined package
- 5 services (Discovery, Migration, Development, Testing, Deployment)
- Just type "standard"
- Saves time

**Custom Services:**
- You define your own
- Flexible for unique projects
- Type "custom" then provide details

---

### 5. Sprint Allocation

**What are sprints?**
- Time periods (usually 2 weeks)
- Used in Agile project management
- Deliverables are assigned to sprints

**Example:**
```
Total sprints: 12 (24 weeks)

Deliverable 1: Architecture Design
- Sprint 1-2 (weeks 1-4)

Deliverable 2: Application Migration
- Sprint 3-8 (weeks 5-16)

Deliverable 3: Testing
- Sprint 9-11 (weeks 17-22)

Deliverable 4: Deployment
- Sprint 12 (weeks 23-24)
```

**Parallel Work:**
Multiple deliverables can overlap!
```
Deliverable A: Sprints 3-8
Deliverable B: Sprints 4-10  ← Overlaps with A (sprints 4-8)
```

---

### 6. Contact Lookup

**How it works:**
```python
# You say: "MUFG Bank"
# System looks up in contacts_data.json
# Finds full details:
{
  "name": "John Smith",
  "company": "MUFG Bank",
  "address": "1251 Avenue of the Americas...",
  "phone": "+1 (212) 555-0100",
  "email": "john.smith@mufg.com"
}
```

**Benefits:**
- Saves typing
- Ensures accuracy
- Consistent formatting

**What if not found?**
- You provide full details manually
- System uses what you provide

---

## 🔧 Configuration & Customization

### Environment Variables (.env file)

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional (with defaults)
GEMINI_MODEL=gemini-2.5-flash
DEBUG=True
SESSION_TIMEOUT=3600
MAX_FILE_SIZE=10485760
```

### Customizing Prompts

**File:** `app/utils/prompts.py`

**Example: Change a question**
```python
STAGE_QUESTIONS = {
    "project_info": "Tell me about your project (number, name, goals)",
    # Change to:
    "project_info": "What's your project about? Include SOW number, name, and main objectives.",
}
```

### Adding New Contacts

**File:** `contacts_data.json`

```json
{
  "contacts": [
    {
      "id": "mufg_bank",
      "name": "MUFG Bank",
      "type": "client",
      "company": "MUFG Bank",
      "contact_person": "John Smith",
      "designation": "VP of Technology",
      "email": "john.smith@mufg.com",
      "phone": "+1 (212) 555-0100",
      "address": "1251 Avenue of the Americas, New York, NY 10020"
    }
  ]
}
```

### Customizing the Template

**File:** `sample_sow_template.docx`

**Placeholders you can use:**
```
{{ document_number }}
{{ project_name }}
{{ current_date }}

{% for objective in objectives %}
- {{ objective }}
{% endfor %}

{% for service in services %}
{{ service.name }}: {{ service.description }}
{% endfor %}
```

**Jinja2 Syntax:**
- `{{ variable }}` - Insert value
- `{% for item in list %}` - Loop
- `{% if condition %}` - Conditional

---

## 🐛 Debugging & Logs

### Log Files

**Location:** `new_sow/logs/`

**Main log:** `app.log`
```
2025-10-28 14:30:22 - INFO - Session created: abc123
2025-10-28 14:30:25 - INFO - Stored response for stage: project_info
2025-10-28 14:30:25 - INFO - Advanced from project_info to services
```

**Session logs:** `session_abc123_timestamp.log`
- Detailed conversation history
- Gemini API calls
- Data extraction results

### Common Issues & Solutions

**Issue 1: "GEMINI_API_KEY not configured"**
```
Solution: Create .env file with your API key
```

**Issue 2: "Session not found"**
```
Solution: Session expired (1 hour timeout). Start a new session.
```

**Issue 3: "Template not found"**
```
Solution: Ensure sample_sow_template.docx exists in project root
```

**Issue 4: "Data extraction failed"**
```
Solution: Check logs for Gemini API errors. May need to retry.
```

---

## 📊 Performance & Scalability

### Current Implementation
- **Storage:** In-memory (Python dictionary)
- **Concurrent users:** Limited by memory
- **Session persistence:** Lost on restart

### Production Recommendations
- **Use Redis** for session storage
- **Add database** for document history
- **Implement queue** for document generation
- **Add caching** for Gemini responses

---

## 🎓 Learning Path

### Beginner
1. ✅ Read this guide
2. ✅ Run the application
3. ✅ Create a simple SOW
4. ✅ Examine the generated document

### Intermediate
1. ✅ Modify prompts in `prompts.py`
2. ✅ Add custom contacts
3. ✅ Customize the template
4. ✅ Read the logs to understand flow

### Advanced
1. ✅ Add new conversation stages
2. ✅ Implement Redis storage
3. ✅ Add new data models
4. ✅ Create custom Gemini functions

---

## 🎉 Summary

### The Complete Flow (One More Time)

```
1. START SESSION
   ↓
2. CONVERSATION (7 stages)
   - You answer questions
   - Bot stores answers
   ↓
3. GEMINI PROCESSING
   - Builds conversation
   - Calls Gemini with function calling
   - Extracts structured data
   - Enhances descriptions
   ↓
4. DATA POPULATION
   - Creates ProjectInfo, Services, Deliverables, etc.
   - Looks up contacts
   - Validates data
   ↓
5. DOCUMENT GENERATION
   - Loads template
   - Prepares context
   - Renders document
   - Saves to output/
   ↓
6. DOWNLOAD
   - You get your professional SOW!
```

### Key Files to Remember

```
app/main.py                    # Application entry point
app/agents/orchestrator.py     # Main coordinator
app/agents/data_collector_v2.py # Data collection & Gemini processing
app/services/document_service.py # Document generation
app/services/state_service.py  # Session management
app/utils/prompts.py           # Gemini prompts
app/models/sow_models.py       # Data structures
app/config.py                  # Configuration
```

### The Magic Ingredients

1. **FastAPI** - Web framework
2. **Gemini AI** - Data extraction & enhancement
3. **Function Calling** - Structured data extraction
4. **docxtpl** - Template rendering
5. **Pydantic** - Data validation

---

## 🚀 Next Steps

1. **Try it yourself** - Create a SOW
2. **Customize prompts** - Make it your own
3. **Add contacts** - Build your contact database
4. **Modify template** - Match your company's style
5. **Integrate** - Connect with other apps (like unified_ai_chat)

---

## 📚 Additional Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Gemini API:** https://ai.google.dev/docs
- **docxtpl:** https://docxtpl.readthedocs.io/
- **Pydantic:** https://docs.pydantic.dev/

---

## ❓ FAQ

**Q: Can I use a different AI model?**
A: Yes, modify `GEMINI_MODEL` in config.py. Options: gemini-1.5-pro, gemini-1.5-flash

**Q: How do I add more stages?**
A: Add to `ConversationStage` enum in `sow_models.py` and update `data_collector_v2.py`

**Q: Can I skip the conversation and generate directly?**
A: Yes! Use the `/api/generate-direct` endpoint

**Q: How do I backup sessions?**
A: Implement Redis or database storage (currently in-memory only)

**Q: Can I use my own template?**
A: Yes! Upload via `/api/upload-template` or specify path in session creation

---

**🎉 Congratulations! You now understand how new_sow works from start to finish!**

If you have questions, check the logs in `new_sow/logs/` or review this guide again. Happy SOW generating! 📄✨

# new_sow Architecture - Visual Guide

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER / CLIENT                            │
│                    (Browser, API Client, etc.)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP/WebSocket
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI APPLICATION                         │
│                         (app/main.py)                            │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   REST API   │  │  WebSocket   │  │    Direct    │          │
│  │  Endpoints   │  │   Handler    │  │  Generation  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         └──────────────────┼──────────────────┘                   │
│                            ↓                                      │
│                   ┌────────────────┐                             │
│                   │  Orchestrator  │                             │
│                   │     Agent      │                             │
│                   └────────┬───────┘                             │
│                            │                                      │
│         ┌──────────────────┼──────────────────┐                 │
│         ↓                  ↓                   ↓                  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │    Data     │  │    State     │  │   Document   │           │
│  │  Collector  │  │   Service    │  │   Service    │           │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                  │                    │
└─────────┼─────────────────┼──────────────────┼───────────────────┘
          │                 │                  │
          ↓                 ↓                  ↓
┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
│   Gemini AI     │  │   Session    │  │   Template   │
│  (Function      │  │   Storage    │  │   (DOCX)     │
│   Calling)      │  │  (In-Memory) │  │              │
└─────────────────┘  └──────────────┘  └──────────────┘
```

---

## 🔄 Data Flow Diagram

### Conversation Flow

```
┌──────────┐
│  START   │
└────┬─────┘
     │
     ↓
┌─────────────────────┐
│  Create Session     │ ← state_service.create_session()
│  session_id: abc123 │
└────┬────────────────┘
     │
     ↓
┌─────────────────────┐
│  Stage 1:           │
│  PROJECT_INFO       │ ← prompts.STAGE_QUESTIONS["project_info"]
└────┬────────────────┘
     │
     ↓ User answers
┌─────────────────────┐
│  Store Response     │ ← raw_responses["project_info"] = answer
└────┬────────────────┘
     │
     ↓
┌─────────────────────┐
│  Stage 2:           │
│  SERVICES           │ ← prompts.STAGE_QUESTIONS["services"]
└────┬────────────────┘
     │
     ↓ User answers
┌─────────────────────┐
│  Store Response     │ ← raw_responses["services"] = answer
└────┬────────────────┘
     │
     ↓
     ... (repeat for all 7 stages)
     │
     ↓
┌─────────────────────┐
│  Stage 8:           │
│  COMPLETED          │
└────┬────────────────┘
     │
     ↓
┌─────────────────────────────────────────┐
│  Gemini Processing                      │
│  1. Build conversation                  │
│  2. Call Gemini with function calling   │
│  3. Extract structured data             │
│  4. Populate SOWContext                 │
└────┬────────────────────────────────────┘
     │
     ↓
┌─────────────────────┐
│  Generate Document  │ ← document_service.generate_document()
└────┬────────────────┘
     │
     ↓
┌─────────────────────┐
│  Download Document  │
└────┬────────────────┘
     │
     ↓
┌──────────┐
│   END    │
└──────────┘
```

---

## 🧠 Gemini Processing Flow

```
┌────────────────────────────────────────────────────────────┐
│  INPUT: Raw Responses from All Stages                     │
│                                                            │
│  {                                                         │
│    "project_info": "SOW-2025-001, Cloud Migration...",   │
│    "services": "standard",                                │
│    "deliverables": "1. Architecture Design...",           │
│    "timeline": "Start: 2025-02-01...",                    │
│    "resources": "Cloud Architect: 1...",                  │
│    "contacts": "MUFG Bank",                               │
│    "budget": "Milestone 1: $80,000..."                    │
│  }                                                         │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  STEP 1: Build Complete Conversation                      │
│                                                            │
│  Stage: PROJECT_INFO                                       │
│  Question: Please provide document number...               │
│  Answer: SOW-2025-001, Cloud Migration...                 │
│                                                            │
│  Stage: SERVICES                                           │
│  Question: Tell me about services...                       │
│  Answer: standard                                          │
│  ...                                                       │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  STEP 2: Create Enhanced Prompt                           │
│                                                            │
│  "Extract complete SOW data from this conversation:       │
│                                                            │
│  [conversation text]                                       │
│                                                            │
│  CRITICAL INSTRUCTIONS:                                    │
│  - Extract ONLY what user provided                         │
│  - Use YYYY-MM-DD for dates                                │
│  - Allocate sprints intelligently                          │
│  - Return structured JSON                                  │
│                                                            │
│  Use the extract_sow_data function."                       │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  STEP 3: Call Gemini API                                  │
│                                                            │
│  model.generate_content(                                   │
│      prompt,                                               │
│      tool_config={'function_calling_config': 'AUTO'}       │
│  )                                                         │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  GEMINI PROCESSES:                                         │
│  1. Reads entire conversation                              │
│  2. Understands context                                    │
│  3. Extracts data for each field                           │
│  4. Enhances descriptions                                  │
│  5. Allocates sprints intelligently                        │
│  6. Formats dates correctly                                │
│  7. Structures everything as JSON                          │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  STEP 4: Gemini Calls extract_sow_data Function           │
│                                                            │
│  function_call = {                                         │
│    name: "extract_sow_data",                               │
│    args: {                                                 │
│      "document_number": "SOW-2025-001",                    │
│      "project_name": "Cloud Migration Project",            │
│      "objectives": [                                       │
│        "Reduce infrastructure costs by 40%",               │
│        "Improve scalability",                              │
│        "Enhance security posture"                          │
│      ],                                                    │
│      "services": [                                         │
│        {                                                   │
│          "name": "Discovery & Planning",                   │
│          "description": "Initial project assessment...",   │
│          "duration": "3 weeks"                             │
│        },                                                  │
│        ...                                                 │
│      ],                                                    │
│      "deliverables": [...],                                │
│      "start_date": "2025-02-01",                           │
│      "end_date": "2025-07-31",                             │
│      ...                                                   │
│    }                                                       │
│  }                                                         │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  STEP 5: Extract Data from Function Call                  │
│                                                            │
│  extracted_data = dict(function_call.args)                 │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  STEP 6: Populate SOWContext                               │
│                                                            │
│  session_data.sow_context.project_info = ProjectInfo(...)  │
│  session_data.sow_context.services = [Service(...), ...]   │
│  session_data.sow_context.deliverables = [...]             │
│  session_data.sow_context.timeline = ProjectTimeline(...)  │
│  ...                                                       │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  OUTPUT: Fully Populated SOWContext                        │
│                                                            │
│  Ready for document generation!                            │
└────────────────────────────────────────────────────────────┘
```

---

## 📄 Document Generation Flow

```
┌────────────────────────────────────────────────────────────┐
│  INPUT: SOWContext (Structured Data)                       │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  STEP 1: Prepare Context Dictionary                       │
│                                                            │
│  context = {                                               │
│    "document_number": "SOW-2025-001",                      │
│    "project_name": "Cloud Migration Project",              │
│    "start_date": "February 01, 2025",                      │
│    "services": [                                           │
│      {"name": "...", "description": "...", "duration": ""}│
│    ],                                                      │
│    ...                                                     │
│  }                                                         │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  STEP 2: Load Template                                    │
│                                                            │
│  doc = DocxTemplate("sample_sow_template.docx")            │
│                                                            │
│  Template contains placeholders:                           │
│  - {{ document_number }}                                   │
│  - {{ project_name }}                                      │
│  - {% for service in services %}                           │
│      {{ service.name }}                                    │
│    {% endfor %}                                            │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  STEP 3: Render Template with Context                     │
│                                                            │
│  doc.render(context)                                       │
│                                                            │
│  Jinja2 replaces all placeholders:                         │
│  {{ document_number }} → "SOW-2025-001"                    │
│  {{ project_name }} → "Cloud Migration Project"            │
│  Loops create lists of services, deliverables, etc.        │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  STEP 4: Generate Filename                                │
│                                                            │
│  filename = "SOW_Cloud_Migration_Project_20251028.docx"    │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  STEP 5: Save Document                                    │
│                                                            │
│  output_path = "output/SOW_Cloud_Migration_Project..."     │
│  doc.save(output_path)                                     │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  OUTPUT: Professional SOW Document (DOCX)                 │
└────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Data Models Hierarchy

```
SessionData
├── session_id: str
├── template_id: str
├── template_path: str
├── current_stage: ConversationStage
├── raw_responses: Dict[str, str]
│   ├── "project_info": "SOW-2025-001..."
│   ├── "services": "standard"
│   ├── "deliverables": "1. Architecture..."
│   ├── "timeline": "Start: 2025-02-01..."
│   ├── "resources": "Cloud Architect: 1..."
│   ├── "contacts": "MUFG Bank"
│   └── "budget": "Milestone 1: $80,000..."
├── sow_context: SOWContext
│   ├── project_info: ProjectInfo
│   │   ├── document_number: str
│   │   ├── project_name: str
│   │   └── objectives: List[str]
│   ├── services: List[Service]
│   │   └── Service
│   │       ├── name: str
│   │       ├── description: str
│   │       └── duration: str
│   ├── deliverables: List[Deliverable]
│   │   └── Deliverable
│   │       ├── id: int
│   │       ├── name: str
│   │       ├── description: str
│   │       ├── sprint_start: int
│   │       ├── sprint_end: int
│   │       └── sprint_duration: int
│   ├── timeline: ProjectTimeline
│   │   ├── start_date: date
│   │   ├── end_date: date
│   │   ├── total_sprints: int
│   │   └── sprint_duration: str
│   ├── resources: List[Resource]
│   │   └── Resource
│   │       ├── role: str
│   │       ├── team: str
│   │       ├── count: int
│   │       └── allocation: str
│   ├── contractor_contact: Contact
│   │   ├── name: str
│   │   ├── company: str
│   │   ├── address: str
│   │   ├── phone: str
│   │   ├── email: str
│   │   └── role: str
│   ├── client_contact: Contact
│   ├── milestones: List[Milestone]
│   │   └── Milestone
│   │       ├── id: int
│   │       ├── name: str
│   │       ├── fee: float
│   │       └── description: str
│   ├── total_fee: float
│   ├── estimated_expenses: float
│   ├── assumptions: List[str]
│   └── terms: List[str]
├── conversation_history: List[Dict]
├── is_completed: bool
├── created_at: datetime
└── updated_at: datetime
```

---

## 🔌 API Endpoints Map

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
│                   http://localhost:8002                     │
└─────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ↓                    ↓                    ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  REST API    │    │  WebSocket   │    │   Direct     │
│  Endpoints   │    │              │    │  Generation  │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
        │                    │                    │
┌───────┴────────┐  ┌────────┴────────┐  ┌───────┴────────┐
│ POST           │  │ WS              │  │ POST           │
│ /api/          │  │ /api/ws/        │  │ /api/          │
│ create-session │  │ {session_id}    │  │ generate-direct│
└────────────────┘  └─────────────────┘  └────────────────┘
        │                    │                    │
┌───────┴────────┐  ┌────────┴────────┐          │
│ POST           │  │ Real-time       │          │
│ /api/          │  │ conversation    │          │
│ upload-template│  │ with bot        │          │
└────────────────┘  └─────────────────┘          │
        │                                         │
┌───────┴────────┐                                │
│ POST           │                                │
│ /api/          │                                │
│ generate-      │                                │
│ document/      │                                │
│ {session_id}   │                                │
└────────────────┘                                │
        │                                         │
┌───────┴────────┐                                │
│ GET            │                                │
│ /api/download/ │                                │
│ {session_id}   │                                │
└────────────────┘                                │
        │                                         │
┌───────┴────────┐                                │
│ GET            │                                │
│ /api/session/  │                                │
│ {session_id}   │                                │
└────────────────┘                                │
                                                  │
                                         ┌────────┴────────┐
                                         │ Bypasses        │
                                         │ conversation    │
                                         │ Generates       │
                                         │ directly from   │
                                         │ provided data   │
                                         └─────────────────┘
```

---

## 🎯 Component Responsibilities

```
┌─────────────────────────────────────────────────────────────┐
│  main.py                                                    │
│  • Application entry point                                  │
│  • Initializes FastAPI                                      │
│  • Registers routes                                         │
│  • Configures CORS                                          │
│  • Sets up logging                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  orchestrator.py                                            │
│  • Main coordinator                                         │
│  • Handles incoming messages                                │
│  • Delegates to data_collector                              │
│  • Triggers document generation                             │
│  • Manages conversation flow                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  data_collector_v2.py                                       │
│  • Collects user responses                                  │
│  • Advances conversation stages                             │
│  • Calls Gemini for data extraction                         │
│  • Populates SOWContext                                     │
│  • Validates data                                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  state_service.py                                           │
│  • Manages sessions (in-memory)                             │
│  • Creates/reads/updates/deletes sessions                   │
│  • Tracks conversation history                              │
│  • Handles session expiration                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  document_service.py                                        │
│  • Loads DOCX templates                                     │
│  • Prepares context for rendering                           │
│  • Renders templates with data                              │
│  • Saves generated documents                                │
│  • Validates templates                                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  prompts.py                                                 │
│  • Stores all Gemini prompts                                │
│  • Stage questions                                          │
│  • Data extraction prompts                                  │
│  • Validation prompts                                       │
│  • Expected JSON structures                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  sow_models.py                                              │
│  • Defines all data structures                              │
│  • Pydantic models for validation                           │
│  • SessionData, SOWContext, ProjectInfo, etc.               │
│  • Enums for stages and types                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  config.py                                                  │
│  • Application configuration                                │
│  • Environment variables                                    │
│  • Directory setup                                          │
│  • API keys and settings                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Visual Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    new_sow Application                      │
│                                                             │
│  YOU → CONVERSATION → GEMINI → DOCUMENT                     │
│                                                             │
│  1. Answer 7 questions                                      │
│  2. Gemini extracts & enhances data                         │
│  3. Template renders with data                              │
│  4. Professional SOW generated                              │
│                                                             │
│  Simple. Powerful. AI-driven.                               │
└─────────────────────────────────────────────────────────────┘
```

---

**For detailed explanations, see: HOW_NEW_SOW_WORKS_COMPLETE_GUIDE.md**

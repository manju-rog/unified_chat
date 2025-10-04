# 🏗️ Unified AI Chat - Architecture Documentation

## System Overview

The Unified AI Chat is an intelligent orchestration layer that sits between a single chat UI and two distinct applications (Absence Management and SOW Generation), using Gemini AI to understand user intent and route requests appropriately.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                              │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    React Chat UI                              │ │
│  │  - Modern conversational interface                            │ │
│  │  - Real-time message updates                                  │ │
│  │  - Session management                                         │ │
│  │  - Material Design components                                 │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              ↓ HTTP/REST                            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                              │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │              Unified Chat Backend (Flask)                     │ │
│  │                                                               │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │         Intent Classification Engine                    │ │ │
│  │  │         (Powered by Gemini AI)                          │ │ │
│  │  │                                                         │ │ │
│  │  │  • Analyzes user message                               │ │ │
│  │  │  • Understands context from history                    │ │ │
│  │  │  • Classifies intent with confidence                   │ │ │
│  │  │  • Extracts entities (names, dates, etc.)              │ │ │
│  │  │  • Falls back to regex if AI unavailable               │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  │                              ↓                                │ │
│  │  ┌──────────────────────┐    ┌──────────────────────────┐   │ │
│  │  │  AbsenceHandler      │    │  SOWHandler              │   │ │
│  │  │                      │    │                          │   │ │
│  │  │  • Mark absence      │    │  • Start generation      │   │ │
│  │  │  • Query records     │    │  • Collect data          │   │ │
│  │  │  • Extract details   │    │  • Generate document     │   │ │
│  │  │  • Call Spring API   │    │  • Manage workflow       │   │ │
│  │  └──────────────────────┘    └──────────────────────────┘   │ │
│  │                              ↓                                │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │         Session Management                              │ │ │
│  │  │  • In-memory session storage                            │ │ │
│  │  │  • Conversation history                                 │ │ │
│  │  │  • Context preservation                                 │ │ │
│  │  │  • State machine for SOW workflow                       │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                    ↓                              ↓
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│    APPLICATION LAYER 1          │  │    APPLICATION LAYER 2          │
│                                 │  │                                 │
│  ┌───────────────────────────┐ │  │  ┌───────────────────────────┐ │
│  │  Absence Management       │ │  │  │  SOW Generator            │ │
│  │  (Spring Boot)            │ │  │  │  (Python Modules)         │ │
│  │                           │ │  │  │                           │ │
│  │  • REST API endpoints     │ │  │  │  • Template matching      │ │
│  │  • AI chat integration    │ │  │  │  • Content generation     │ │
│  │  • Employee management    │ │  │  │  • Document formatting    │ │
│  │  • Absence tracking       │ │  │  │  • AI-powered extraction  │ │
│  │  • Query processing       │ │  │  │                           │ │
│  └───────────────────────────┘ │  │  └───────────────────────────┘ │
│              ↓                  │  │              ↓                  │
│  ┌───────────────────────────┐ │  │  ┌───────────────────────────┐ │
│  │  SQLite Database          │ │  │  │  DOCX Templates           │ │
│  │  • Employees              │ │  │  │  • G-COP SOW v1.0         │ │
│  │  • Absence records        │ │  │  │  • Custom templates       │ │
│  └───────────────────────────┘ │  │  └───────────────────────────┘ │
└─────────────────────────────────┘  └─────────────────────────────────┘
```

## Component Details

### 1. React Chat UI

**Location:** `unified_ai_chat/frontend/src/UnifiedChat.jsx`

**Responsibilities:**
- Render modern chat interface
- Handle user input
- Display messages with proper formatting
- Manage local UI state
- Show typing indicators
- Display download buttons for SOW documents

**Key Features:**
- Material Design icons
- Smooth animations
- Responsive layout
- Quick action buttons
- Session status indicator
- Error handling with user-friendly messages

**State Management:**
```javascript
{
  messages: [],           // Array of message objects
  inputValue: '',         // Current input text
  isLoading: false,       // Loading state
  sessionId: null,        // Backend session ID
  error: null            // Error message if any
}
```

### 2. Intent Classification Engine

**Location:** `unified_ai_chat/backend/unified_chat_server.py` → `IntentClassifier`

**How It Works:**

1. **Receives user message** and conversation history
2. **Constructs AI prompt** with context and intent definitions
3. **Calls Gemini AI** to analyze and classify
4. **Returns structured result:**
   ```json
   {
     "intent": "absence_mark",
     "confidence": 0.95,
     "entities": {
       "employee_name": "Manju",
       "date": "2025-10-03",
       "status": "A"
     },
     "reasoning": "User wants to mark employee absent"
   }
   ```

**Supported Intents:**

| Intent | Trigger Examples | Handler |
|--------|-----------------|---------|
| `greeting` | "Hi", "Hello", "Hey there" | Direct response |
| `absence_mark` | "Mark X absent", "X won't be in" | AbsenceHandler |
| `absence_query` | "Who was absent?", "Show absences" | AbsenceHandler |
| `sow_generate` | "Create SOW", "Generate document" | SOWHandler |
| `sow_continue` | Responses during SOW flow | SOWHandler |
| `general` | Out of scope questions | Polite decline |

**Fallback Mechanism:**
If Gemini AI is unavailable or fails, the system uses regex-based classification:
```python
def _fallback_classification(message: str):
    # Keyword matching
    if 'mark' in message or 'absent' in message:
        return {'intent': 'absence_mark', ...}
    # ... more patterns
```

### 3. Absence Handler

**Location:** `unified_ai_chat/backend/unified_chat_server.py` → `AbsenceHandler`

**Methods:**

#### `mark_absence(message, session)`
1. Extracts employee name, dates, and status using AI
2. Validates extracted information
3. Calls Spring Boot API: `POST /api/ai/chat`
4. Returns formatted response

**Flow:**
```
User: "Mark Manju absent today"
  ↓
Extract: {name: "Manju", date: "2025-10-03", status: "A"}
  ↓
Call: POST http://localhost:8080/api/ai/chat
  ↓
Response: "✅ Marked Manju as absent for October 3, 2025"
```

#### `query_absence(message, session)`
1. Forwards query to Spring Boot API
2. Receives structured absence data
3. Formats response for user

### 4. SOW Handler

**Location:** `unified_ai_chat/backend/unified_chat_server.py` → `SOWHandler`

**State Machine:**

```
[START] → project_basics → services → deliverables → timeline → budget → [GENERATE]
```

**Methods:**

#### `start_sow_generation(session)`
- Initializes SOW workflow
- Sets state to 'project_basics'
- Returns first prompt

#### `continue_sow_generation(message, session)`
- Processes user input based on current step
- Stores data in session context
- Advances to next step
- Returns next prompt

**Session Context:**
```python
{
  'sow_state': 'started',
  'sow_step': 'services',
  'sow_data': {
    'project_basics': "...",
    'services': "...",
    'deliverables': "...",
    'timeline': "...",
    'budget': "..."
  }
}
```

#### `_generate_document(session)`
- Imports SOW generator modules
- Feeds collected data to generator
- Creates DOCX document
- Returns download URL

### 5. Session Management

**Data Structure:**
```python
@dataclass
class ChatSession:
    session_id: str
    messages: List[Message]
    context: Dict[str, Any]
    created_at: str
    last_activity: str
```

**Storage:**
- Currently: In-memory dictionary
- Production: Redis or database recommended

**Lifecycle:**
1. Created on first message
2. Updated with each interaction
3. Expires after inactivity (configurable)

## Data Flow Examples

### Example 1: Mark Absence

```
┌──────────┐
│   User   │ "Mark Manju absent today"
└────┬─────┘
     │
     ↓ POST /api/chat
┌────────────────┐
│  Flask Server  │
└────┬───────────┘
     │
     ↓ classify_intent()
┌────────────────┐
│  Gemini AI     │ → intent: "absence_mark"
└────┬───────────┘      entities: {name: "Manju", ...}
     │
     ↓ AbsenceHandler.mark_absence()
┌────────────────┐
│  Extract       │ → {employeeName: "Manju", 
│  Details       │    dates: ["2025-10-03"],
└────┬───────────┘    status: "A"}
     │
     ↓ POST /api/ai/chat
┌────────────────┐
│  Spring Boot   │ → Processes with Gemini
│  API           │ → Marks absence in DB
└────┬───────────┘ → Returns success
     │
     ↓ Response
┌────────────────┐
│  Flask Server  │ → Formats response
└────┬───────────┘
     │
     ↓ JSON response
┌────────────────┐
│  React UI      │ → Displays: "✅ Marked Manju..."
└────────────────┘
```

### Example 2: SOW Generation

```
┌──────────┐
│   User   │ "Create a SOW"
└────┬─────┘
     │
     ↓ POST /api/chat
┌────────────────┐
│  Flask Server  │
└────┬───────────┘
     │
     ↓ classify_intent()
┌────────────────┐
│  Gemini AI     │ → intent: "sow_generate"
└────┬───────────┘
     │
     ↓ SOWHandler.start_sow_generation()
┌────────────────┐
│  Initialize    │ → Set state: 'project_basics'
│  Workflow      │ → Store in session
└────┬───────────┘
     │
     ↓ Response
┌────────────────┐
│  React UI      │ → "Tell me about your project..."
└────┬───────────┘
     │
     ↓ User responds
┌────────────────┐
│  Flask Server  │ → intent: "sow_continue"
└────┬───────────┘
     │
     ↓ SOWHandler.continue_sow_generation()
┌────────────────┐
│  Process       │ → Store data
│  Response      │ → Advance to 'services'
└────┬───────────┘ → Return next prompt
     │
     ↓ ... continues through all steps ...
     │
     ↓ Final step
┌────────────────┐
│  Generate      │ → Import SOW modules
│  Document      │ → Create DOCX
└────┬───────────┘ → Return download URL
     │
     ↓ Response
┌────────────────┐
│  React UI      │ → Shows download button
└────────────────┘
```

## API Specifications

### POST /api/chat

**Request:**
```json
{
  "message": "string (required)",
  "session_id": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "response": "string",
  "session_id": "string",
  "intent": "string",
  "action_type": "string",
  "action_data": {},
  "download_url": "string (optional)"
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad request (empty message)
- `500` - Server error

### GET /api/session/{session_id}/history

**Response:**
```json
{
  "success": true,
  "messages": [
    {
      "role": "user|assistant|system",
      "content": "string",
      "timestamp": "ISO 8601",
      "metadata": {}
    }
  ],
  "context": {}
}
```

### GET /api/health

**Response:**
```json
{
  "success": true,
  "status": "healthy",
  "gemini_configured": true,
  "active_sessions": 5
}
```

## Security Considerations

### Current Implementation
- No authentication (internal use)
- CORS enabled for all origins
- Sessions stored in memory
- No rate limiting

### Production Recommendations
1. **Authentication:** Add JWT or OAuth
2. **Authorization:** Role-based access control
3. **Rate Limiting:** Prevent abuse
4. **Session Storage:** Use Redis with encryption
5. **CORS:** Restrict to specific origins
6. **Input Validation:** Sanitize all inputs
7. **API Keys:** Secure storage (not in code)
8. **Logging:** Audit trail for all actions

## Performance Considerations

### Current Bottlenecks
1. **Gemini API calls:** ~1-3 seconds per request
2. **Spring Boot API:** Network latency
3. **In-memory sessions:** Limited scalability

### Optimization Strategies
1. **Caching:** Cache common intents and responses
2. **Async Processing:** Use async/await for API calls
3. **Connection Pooling:** Reuse HTTP connections
4. **Load Balancing:** Multiple backend instances
5. **CDN:** Serve static frontend assets
6. **Database:** Index frequently queried fields

## Scalability

### Current Limits
- **Sessions:** Limited by server memory
- **Concurrent Users:** ~100-200 (single instance)
- **API Rate Limits:** Gemini API quotas

### Scaling Strategy

**Horizontal Scaling:**
```
┌─────────────┐
│ Load        │
│ Balancer    │
└──────┬──────┘
       │
   ┌───┴───┬───────┬───────┐
   │       │       │       │
┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──┐
│ App │ │ App │ │ App │ │ App │
│  1  │ │  2  │ │  3  │ │  4  │
└──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘
   │       │       │       │
   └───┬───┴───────┴───────┘
       │
   ┌───▼────┐
   │ Redis  │ ← Shared session storage
   └────────┘
```

## Monitoring & Logging

### Key Metrics
- Request latency
- Intent classification accuracy
- API success/failure rates
- Active sessions count
- Error rates by type

### Logging Strategy
```python
logger.info(f"Intent classified: {intent} (confidence: {confidence})")
logger.error(f"API call failed: {error}", exc_info=True)
logger.warning(f"Low confidence classification: {confidence}")
```

### Recommended Tools
- **Application:** Sentry for error tracking
- **Infrastructure:** Prometheus + Grafana
- **Logs:** ELK Stack (Elasticsearch, Logstash, Kibana)

## Testing Strategy

### Unit Tests
- Intent classification logic
- Handler methods
- Session management
- Entity extraction

### Integration Tests
- End-to-end conversation flows
- API integration with Spring Boot
- SOW generation workflow
- Error handling scenarios

### Load Tests
- Concurrent user simulation
- API rate limit testing
- Memory usage under load

## Deployment

### Development
```bash
# Backend
cd unified_ai_chat/backend
python unified_chat_server.py

# Frontend
cd unified_ai_chat/frontend
npm start
```

### Production (Docker)
```dockerfile
# Backend Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5002", "unified_chat_server:app"]

# Frontend Dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html
```

### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5002:5002"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - redis
  
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

## Future Enhancements

### Phase 1 (Short-term)
- [ ] Persistent session storage (Redis)
- [ ] User authentication
- [ ] Conversation export
- [ ] Advanced error recovery

### Phase 2 (Medium-term)
- [ ] Voice input/output
- [ ] File attachments
- [ ] Multi-language support
- [ ] Analytics dashboard

### Phase 3 (Long-term)
- [ ] Mobile app
- [ ] WebSocket real-time updates
- [ ] AI model fine-tuning
- [ ] Custom integrations API

---

**Architecture Version:** 1.0  
**Last Updated:** October 3, 2025  
**Maintained By:** Development Team

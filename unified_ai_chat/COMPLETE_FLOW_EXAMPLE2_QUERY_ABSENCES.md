# 🔍 Complete Flow Example 2: "Show September absences"

## 📋 Overview

This document traces **EVERY SINGLE STEP** when a user types "Show September absences" - from input to displaying a formatted table of absence data.

**User Input:** `Show September absences`

**Expected Result:** Table showing all absences in September 2025

**Time:** ~2-3 seconds total

---

## 🎬 Step-by-Step Flow

### Step 1: User Types and Sends

**Location:** Frontend - `UnifiedChat.jsx`

**User types:** `Show September absences`

**Presses Enter → triggers:**
```javascript
const handleKeyDown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSendMessage();
  }
};
```

---

### Step 2: Frontend Sends Request

**Location:** Frontend - `UnifiedChat.jsx` line ~150

**Code:**
```javascript
const handleSendMessage = async () => {
  const message = 'Show September absences';
  
  // Add user message to chat
  const userMessage = {
    id: 1730123456789,
    role: 'user',
    content: 'Show September absences',
    timestamp: '2025-10-28T10:35:00.000Z'
  };
  setMessages(prev => [...prev, userMessage]);
  
  setIsLoading(true);
  
  // Send to backend
  const response = await fetch('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: 'Show September absences',
      mode: 'unified',
      session_id: 'abc123'
    })
  });
  
  const data = await response.json();
  // ... handle response
};
```

**HTTP Request:**
```http
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "message": "Show September absences",
  "mode": "unified",
  "session_id": "abc123"
}
```

---

### Step 3: Backend Receives Request

**Location:** Backend - `main.py` line ~300

**Code:**
```python
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, session: SessionState = Depends(get_session)):
    logger.info("Processing chat message for session %s", session.session_id)
    
    user_message = request.message.strip()  # "Show September absences"
    session.add_message("user", user_message)
    
    lowered = user_message.lower()  # "show september absences"
    
    # ... continues to Gemini
```

**Console Output:**
```
INFO: Processing chat message for session abc123
INFO: User message: "Show September absences"
```

---

### Step 4: Build Context for Gemini

**Location:** Backend - `main.py` line ~400

**Code:**
```python
# Build context
context_parts = []

# Add employee directory
employees = await absence_adapter.get_employees()
employee_entries = [
    f"{emp.get('name')}|{emp.get('id')}|{emp.get('department')}"
    for emp in employees
    if emp.get("name")
]
context_parts.append("EMPLOYEE_DIRECTORY: " + "; ".join(employee_entries))

# Add current date
from datetime import datetime
today = datetime.now().strftime("%Y-%m-%d")  # "2025-10-28"
day_name = datetime.now().strftime("%A")  # "Monday"
current_year = datetime.now().year  # 2025
current_month = datetime.now().strftime("%B")  # "October"

context_parts.append(f"TODAY'S DATE: {today} ({day_name})")

full_context = " | ".join(context_parts)
```

**Context:**
```
EMPLOYEE_DIRECTORY: Manju|1|Engineering; Ganesh|2|HR; Shreyas|3|Sales; Suhas|4|Marketing; Anushri|5|Finance | TODAY'S DATE: 2025-10-28 (Monday)
```

---

### Step 5: Send to Gemini

**Location:** Backend - `gemini_client.py` line ~100

**Code:**
```python
def generate(self, session, user_message, context):
    messages = []
    
    # Combine context and message
    full_message = f"{context}\n\nUser request: {user_message}"
    messages.append({"role": "user", "parts": [full_message]})
    
    # Call Gemini
    response = self._model.generate_content(
        messages,
        tool_config={"function_calling_config": {"mode": "AUTO"}},
    )
    
    return response
```

**What Gemini Receives:**
```
System Instruction:
"You are the Unified Operations AI Assistant. Today's date is 2025-10-28 (Monday). 
Current year is 2025. Current month is October.

**CRITICAL DATE RULES:**
- TODAY is 2025-10-28 (Monday)
- CURRENT YEAR is 2025 - ALWAYS use this year unless user explicitly mentions a different year
- CURRENT MONTH is October
- When user says 'September absences' or any month name WITHOUT a year, use year=2025
- NEVER assume year 2024 or any past year - ALWAYS use 2025 unless explicitly stated otherwise

**Absence Management — use `absence_chat`:**
- action='query_absence' with `time_period`, `date`, `date_range`, or (`month`, `year`).
..."

User Message:
"EMPLOYEE_DIRECTORY: Manju|1|Engineering; ... | TODAY'S DATE: 2025-10-28 (Monday)

User request: Show September absences"
```

**Gemini's Thinking:**
```
💭 Analyzing: "Show September absences"
   - Action: query_absence
   - Month: September
   - Year: 2025 (current year - not specified by user)
   - Query type: byMonth
   
   Decision: Call absence_chat with month="September" and year=2025
```

---

### Step 6: Gemini Returns Function Call

**Gemini Response:**
```json
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "function_call": {
              "name": "absence_chat",
              "args": {
                "action": "query_absence",
                "query_type": "all_absent",
                "month": "September",
                "year": 2025
              }
            }
          }
        ]
      },
      "finish_reason": "STOP"
    }
  ]
}
```

**Console Output:**
```
🔍 GEMINI RESPONSE DEBUG:
📊 Candidate finish reason: STOP
🧩 Response parts count: 1
  Part 1:
    🛠️ FUNCTION CALL: absence_chat
    📋 Raw Args: {'action': 'query_absence', 'query_type': 'all_absent', 'month': 'September', 'year': 2025}
    ✅ Parsed Args: {'action': 'query_absence', 'query_type': 'all_absent', 'month': 'September', 'year': 2025}
🎯 FINAL PARSED RESULT:
  Tool calls: 1
    - absence_chat: {'action': 'query_absence', 'query_type': 'all_absent', 'month': 'September', 'year': 2025}
  Text: ''
  Thinking: 'Calling absence_chat → Action: query_absence'
```

---

### Step 7: Parse Gemini Response

**Location:** Backend - `gemini_client.py` line ~200

**Code:**
```python
def parse_response(self, response):
    candidate = response.candidates[0]
    parts = candidate.content.parts
    tool_calls = []
    
    for part in parts:
        if getattr(part, "function_call", None):
            func_call = part.function_call
            tool_calls.append(ToolCall(
                name=func_call.name,
                arguments=dict(func_call.args)
            ))
    
    return {
        "tool_calls": tool_calls,
        "text": "",
        "thinking": "Calling absence_chat → Action: query_absence"
    }
```

**Result:**
```python
{
    "tool_calls": [
        ToolCall(
            name="absence_chat",
            arguments={
                "action": "query_absence",
                "query_type": "all_absent",
                "month": "September",
                "year": 2025
            }
        )
    ],
    "text": "",
    "thinking": "Calling absence_chat → Action: query_absence"
}
```

---

### Step 8: Handle absence_chat Tool Call

**Location:** Backend - `main.py` line ~600

**Code:**
```python
async def _handle_gemini_absence_call(session, tool_call, user_message):
    args = tool_call.arguments
    action = args.get("action")  # "query_absence"
    
    if action == "query_absence":
        query_type = args.get("query_type", "all_absent")  # "all_absent"
        month = args.get("month")  # "September"
        year = args.get("year", datetime.now().year)  # 2025
        
        logger.info(f"Query absence - month: {month}, year: {year}")
        
        # Check for month FIRST
        if month:
            # Convert month name to number
            month_num = _month_name_to_number(month)  # 9
            month_str = f"{int(year)}-{month_num:02d}"  # "2025-09"
            
            logger.info(f"Querying month: {month_str}")
            
            # Call absence adapter
            result = await absence_adapter.query_absence(
                query_type="byMonth",
                month=month_str
            )
        
        # Add response message
        session.add_message("assistant", result.get("message"))
        
        # Pass details to action_data for frontend rendering
        action_data = {"theme": "absence"}
        if result.get("details"):
            action_data.update(result["details"])
        
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message"),
            action_type="absence_query_result",
            action_data=action_data
        )
```

**Helper Function:**
```python
def _month_name_to_number(month_name: str) -> int:
    """Convert month name to number"""
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12
    }
    return months.get(month_name.lower(), 1)
```

**Result:**
```python
month_num = 9
month_str = "2025-09"
```

---

### Step 9: Query Absence API

**Location:** Backend - `services/absence.py` line ~200

**Code:**
```python
async def query_absence(self, query_type: str, month: str = None, **kwargs):
    try:
        # Build query parameters
        params = {"query_type": query_type}  # "byMonth"
        
        if month:
            params["month"] = month  # "2025-09"
        
        # Call absence API
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/absence/query",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Format response
                    return self._format_absence_query_response(data, query_type, month)
                else:
                    error = await response.text()
                    return {
                        "success": False,
                        "message": f"❌ Query failed: {error}"
                    }
    except Exception as e:
        logger.error(f"Error querying absence: {e}")
        return {
            "success": False,
            "message": f"❌ Error: {str(e)}"
        }
```

**API Request:**
```http
GET http://localhost:8010/api/absence/query?query_type=byMonth&month=2025-09
```

**API Response:**
```json
{
  "success": true,
  "data": {
    "month": "2025-09",
    "absences": [
      {
        "employee_id": 1,
        "employee_name": "Manju",
        "dates": ["2025-09-05", "2025-09-12", "2025-09-19"],
        "status": "A",
        "reasons": ["Sick leave", "Personal", "Medical appointment"]
      },
      {
        "employee_id": 2,
        "employee_name": "Ganesh",
        "dates": ["2025-09-08", "2025-09-15"],
        "status": "A",
        "reasons": ["Family emergency", "Personal"]
      },
      {
        "employee_id": 4,
        "employee_name": "Suhas",
        "dates": ["2025-09-20", "2025-09-21", "2025-09-22", "2025-09-23", "2025-09-24"],
        "status": "V",
        "reasons": ["Vacation", "Vacation", "Vacation", "Vacation", "Vacation"]
      }
    ],
    "totals": {
      "absent": 5,
      "vacation": 5,
      "total_days": 10
    }
  }
}
```

---

### Step 10: Format Response

**Location:** Backend - `services/absence.py` line ~300

**Code:**
```python
def _format_absence_query_response(self, data, query_type, month):
    absences = data.get("data", {}).get("absences", [])
    totals = data.get("data", {}).get("totals", {})
    
    if not absences:
        return {
            "success": True,
            "message": f"📊 No absences found for {month}",
            "details": None
        }
    
    # Build message
    message_parts = [f"📊 **ABSENCE REPORT FOR {month.upper()}**\n"]
    
    # Group by employee
    employee_absences = []
    for absence in absences:
        employee_absences.append({
            "name": absence["employee_name"],
            "status": "Absent" if absence["status"] == "A" else "Vacation",
            "dates": absence["dates"]
        })
    
    # Build text summary
    for emp in employee_absences:
        message_parts.append(f"• **{emp['name']}** - {emp['status']}: {len(emp['dates'])} days")
    
    message_parts.append(f"\n**Total:** {totals.get('absent', 0)} absences, {totals.get('vacation', 0)} vacation days")
    
    message = "\n".join(message_parts)
    
    # Prepare details for frontend rendering
    details = {
        "display_type": "absence_breakdown",
        "start": f"{month}-01",
        "end": f"{month}-30",
        "employee_absences": employee_absences,
        "totals": totals
    }
    
    return {
        "success": True,
        "message": message,
        "details": details
    }
```

**Formatted Result:**
```python
{
    "success": True,
    "message": "📊 **ABSENCE REPORT FOR 2025-09**\n\n• **Manju** - Absent: 3 days\n• **Ganesh** - Absent: 2 days\n• **Suhas** - Vacation: 5 days\n\n**Total:** 5 absences, 5 vacation days",
    "details": {
        "display_type": "absence_breakdown",
        "start": "2025-09-01",
        "end": "2025-09-30",
        "employee_absences": [
            {
                "name": "Manju",
                "status": "Absent",
                "dates": ["2025-09-05", "2025-09-12", "2025-09-19"]
            },
            {
                "name": "Ganesh",
                "status": "Absent",
                "dates": ["2025-09-08", "2025-09-15"]
            },
            {
                "name": "Suhas",
                "status": "Vacation",
                "dates": ["2025-09-20", "2025-09-21", "2025-09-22", "2025-09-23", "2025-09-24"]
            }
        ],
        "totals": {
            "absent": 5,
            "vacation": 5,
            "total_days": 10
        }
    }
}
```

---

### Step 11: Return Response to Frontend

**HTTP Response:**
```json
{
  "session_id": "abc123",
  "response": "📊 **ABSENCE REPORT FOR 2025-09**\n\n• **Manju** - Absent: 3 days\n• **Ganesh** - Absent: 2 days\n• **Suhas** - Vacation: 5 days\n\n**Total:** 5 absences, 5 vacation days",
  "action_type": "absence_query_result",
  "action_data": {
    "theme": "absence",
    "display_type": "absence_breakdown",
    "start": "2025-09-01",
    "end": "2025-09-30",
    "employee_absences": [
      {
        "name": "Manju",
        "status": "Absent",
        "dates": ["2025-09-05", "2025-09-12", "2025-09-19"]
      },
      {
        "name": "Ganesh",
        "status": "Absent",
        "dates": ["2025-09-08", "2025-09-15"]
      },
      {
        "name": "Suhas",
        "status": "Vacation",
        "dates": ["2025-09-20", "2025-09-21", "2025-09-22", "2025-09-23", "2025-09-24"]
      }
    ],
    "totals": {
      "absent": 5,
      "vacation": 5,
      "total_days": 10
    }
  },
  "thinking": "Calling absence_chat → Action: query_absence"
}
```

---

### Step 12: Frontend Receives Response

**Location:** Frontend - `UnifiedChat.jsx` line ~200

**Code:**
```javascript
const data = await response.json();

// Create assistant message
const assistantMessage = {
  id: Date.now() + 1,
  role: 'assistant',
  content: data.response,
  timestamp: new Date().toISOString(),
  metadata: {
    actionType: "absence_query_result",
    actionData: data.action_data,
    thinking: "Calling absence_chat → Action: query_absence"
  }
};

// Add to messages
setMessages(prev => [...prev, assistantMessage]);

// Update theme
setCurrentMode('absence');

// Stop loading
setIsLoading(false);
```

---

### Step 13: Render Absence Breakdown

**Location:** Frontend - `UnifiedChat.jsx` line ~700

**Code:**
```javascript
const renderMessage = (message) => {
  // Check if this is an absence breakdown
  if (message.metadata?.actionData?.display_type === 'absence_breakdown') {
    return (
      <div key={message.id} className="message assistant">
        <div className="message-avatar">
          <span className="material-icons">smart_toy</span>
        </div>
        <div className="message-content">
          {renderAbsenceBreakdown(message.metadata.actionData)}
          <div className="message-time">
            {formatTime(message.timestamp)}
          </div>
        </div>
      </div>
    );
  }
  // ... other rendering logic
};
```

**Calls:**
```javascript
renderAbsenceBreakdown({
  display_type: "absence_breakdown",
  start: "2025-09-01",
  end: "2025-09-30",
  employee_absences: [...],
  totals: {...}
})
```

---

### Step 14: Render Absence Table

**Location:** Frontend - `UnifiedChat.jsx` line ~750

**Code:**
```javascript
const renderAbsenceBreakdown = (data) => {
  const { start, end, employee_absences, totals } = data;
  
  // Parse month/year
  const startDate = new Date(start);
  const monthYear = startDate.toLocaleDateString('en-US', { 
    month: 'long', 
    year: 'numeric' 
  }).toUpperCase();  // "SEPTEMBER 2025"
  
  return (
    <div className="absence-breakdown-card">
      <div className="breakdown-header">
        <h3>ABSENCE BREAKDOWN</h3>
        <div className="breakdown-period">{monthYear}</div>
      </div>
      
      <div className="breakdown-table">
        <div className="breakdown-table-header">
          <div className="col-name">NAME</div>
          <div className="col-status">STATUS</div>
          <div className="col-dates">DATES</div>
        </div>
        
        <div className="breakdown-table-body">
          {employee_absences.map((emp, index) => (
            <div key={index} className="breakdown-row">
              <div className="col-name">
                <span className="employee-name">{emp.name}</span>
              </div>
              <div className="col-status">
                <span className={`status-badge ${emp.status.toLowerCase()}`}>
                  {emp.status}
                </span>
              </div>
              <div className="col-dates">
                <div className="date-pills">
                  {emp.dates.map((date, idx) => {
                    const d = new Date(date);
                    const formatted = d.toLocaleDateString('en-US', { 
                      month: 'short', 
                      day: 'numeric' 
                    });
                    return (
                      <span key={idx} className="date-pill">
                        {formatted}
                      </span>
                    );
                  })}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="breakdown-footer">
        <div className="total-stat">
          <span className="stat-label">Total Absences:</span>
          <span className="stat-value">{totals.absent}</span>
        </div>
        <div className="total-stat">
          <span className="stat-label">Total Vacations:</span>
          <span className="stat-value">{totals.vacation}</span>
        </div>
      </div>
    </div>
  );
};
```

---

### Step 15: Display Final Result

**What User Sees:**

```
┌─────────────────────────────────────────────────────────────────┐
│ 👤 You                                          10:35 AM        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Show September absences                                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ 🤖 AI Assistant                                 10:35 AM        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 💭 Calling absence_chat → Action: query_absence             │ │
│ │                                                              │ │
│ │ ╔═══════════════════════════════════════════════════════╗   │ │
│ │ ║         ABSENCE BREAKDOWN                             ║   │ │
│ │ ║         SEPTEMBER 2025                                ║   │ │
│ │ ╠═══════════════════════════════════════════════════════╣   │ │
│ │ ║ NAME      │ STATUS   │ DATES                          ║   │ │
│ │ ╠═══════════════════════════════════════════════════════╣   │ │
│ │ ║ Manju     │ Absent   │ [Sep 5] [Sep 12] [Sep 19]     ║   │ │
│ │ ║ Ganesh    │ Absent   │ [Sep 8] [Sep 15]              ║   │ │
│ │ ║ Suhas     │ Vacation │ [Sep 20] [Sep 21] [Sep 22]    ║   │ │
│ │ ║           │          │ [Sep 23] [Sep 24]             ║   │ │
│ │ ╠═══════════════════════════════════════════════════════╣   │ │
│ │ ║ Total Absences: 5    │    Total Vacations: 5         ║   │ │
│ │ ╚═══════════════════════════════════════════════════════╝   │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Complete Timeline

```
0.0s  - User presses Enter
0.1s  - Frontend sends HTTP request
0.2s  - Backend receives request
0.3s  - Backend builds context (employee directory + date)
0.4s  - Backend calls Gemini API
1.2s  - Gemini processes and returns function call
1.3s  - Backend parses Gemini response
1.4s  - Backend handles absence_chat tool
1.5s  - Backend converts "September" to "2025-09"
1.6s  - Backend calls absence API
1.8s  - Absence API queries database
2.0s  - Absence API returns data
2.1s  - Backend formats response
2.2s  - Backend returns to frontend
2.3s  - Frontend renders absence breakdown table
2.4s  - User sees formatted table
```

**Total Time:** ~2.4 seconds

---

## 🎯 Data Transformations

### Input → Month String
```
"Show September absences"
    ↓
month = "September"
year = 2025 (current year)
    ↓
month_num = 9
    ↓
month_str = "2025-09"
```

### API Data → Frontend Display
```
API Response:
{
  "absences": [
    {
      "employee_name": "Manju",
      "dates": ["2025-09-05", "2025-09-12", "2025-09-19"],
      "status": "A"
    }
  ]
}
    ↓
Formatted:
{
  "employee_absences": [
    {
      "name": "Manju",
      "status": "Absent",
      "dates": ["2025-09-05", "2025-09-12", "2025-09-19"]
    }
  ]
}
    ↓
Rendered:
┌─────────┬─────────┬──────────────────────────┐
│ Manju   │ Absent  │ [Sep 5] [Sep 12] [Sep 19]│
└─────────┴─────────┴──────────────────────────┘
```

---

## 🎯 Summary

### What Happened:
1. ✅ User typed "Show September absences"
2. ✅ Frontend sent to backend
3. ✅ Backend added context (employee directory + current date)
4. ✅ Backend sent to Gemini
5. ✅ Gemini called absence_chat with month="September", year=2025
6. ✅ Backend converted to "2025-09"
7. ✅ Backend queried absence API
8. ✅ Backend formatted response with breakdown data
9. ✅ Frontend rendered formatted table
10. ✅ User sees beautiful absence breakdown

### Files Involved:
- `frontend/src/UnifiedChat.jsx` - UI and rendering
- `backend/app/main.py` - Main logic
- `backend/app/gemini_client.py` - Gemini integration
- `backend/app/services/absence.py` - Absence API calls

### API Calls Made:
1. POST `/api/chat` - Main request
2. GET `/absence/query?query_type=byMonth&month=2025-09` - Query absences

### Key Features Demonstrated:
- ✅ Natural language understanding ("September" → "2025-09")
- ✅ Automatic year inference (2025 from current date)
- ✅ Gemini function calling
- ✅ Data formatting and transformation
- ✅ Beautiful table rendering
- ✅ Thinking process display

---

## 🎓 Key Learnings

### 1. Date Handling
- User says "September" without year
- Gemini uses current year (2025)
- Backend converts month name to number
- API receives "2025-09" format

### 2. Data Flow
```
User Input (natural language)
    ↓
Gemini (understands intent)
    ↓
Backend (processes and queries)
    ↓
API (returns raw data)
    ↓
Backend (formats for display)
    ↓
Frontend (renders beautifully)
```

### 3. Response Structure
- Text message for screen readers
- Structured data for visual display
- Both sent together
- Frontend chooses how to render

---

**🎉 You now understand the complete flow for both marking absences and querying absence data!**

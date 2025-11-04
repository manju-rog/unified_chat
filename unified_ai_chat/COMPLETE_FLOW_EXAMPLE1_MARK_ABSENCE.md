# 🔍 Complete Flow Example 1: "Mark Manju absent today"

## 📋 Overview

This document traces **EVERY SINGLE STEP** when a user types "Mark Manju absent today" - from the moment they press Enter to the final response displayed.

**User Input:** `Mark Manju absent today`

**Expected Result:** Manju is marked as absent for today's date

**Time:** ~2-3 seconds total

---

## 🎬 Step-by-Step Flow

### Step 1: User Types and Presses Enter

**Location:** Frontend - `UnifiedChat.jsx`

**What happens:**
```javascript
// User types in input field
<textarea
  value={inputValue}  // "Mark Manju absent today"
  onChange={(e) => setInputValue(e.target.value)}
  onKeyDown={handleKeyDown}  // ← Triggered when Enter is pressed
/>
```

**When Enter is pressed:**
```javascript
const handleKeyDown = useCallback((e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSendMessage();  // ← Calls this function
  }
}, [handleSendMessage]);
```

---

### Step 2: handleSendMessage() Executes

**Location:** Frontend - `UnifiedChat.jsx` line ~150

**Code:**
```javascript
const handleSendMessage = useCallback(async () => {
  const message = inputValue.trim();  // "Mark Manju absent today"
  if (!message || isLoading) return;
  
  // 1. Clear input
  setInputValue('');
  
  // 2. Add user message to chat immediately
  const userMessage = {
    id: Date.now(),  // e.g., 1730123456789
    role: 'user',
    content: 'Mark Manju absent today',
    timestamp: new Date().toISOString()  // "2025-10-28T10:30:00.000Z"
  };
  setMessages(prev => [...prev, userMessage]);
  
  // 3. Show loading indicator
  setIsLoading(true);
  
  // 4. Send to backend
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: 'Mark Manju absent today',
      mode: 'unified',  // Current mode
      session_id: 'abc123'  // Session ID (if exists)
    })
  });
  
  // ... continues
}, [inputValue, isLoading, sessionId, API_BASE_URL, currentMode]);
```

**What you see:**
- Input field clears immediately
- Your message appears in chat (blue bubble on right)
- Loading indicator appears (spinning icon)

---

### Step 3: HTTP Request Sent

**Request Details:**

```http
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "message": "Mark Manju absent today",
  "mode": "unified",
  "session_id": "abc123"
}
```

**Network Tab (Browser DevTools):**
```
Request URL: http://localhost:8000/api/chat
Request Method: POST
Status Code: 200 OK
```

---

### Step 4: Backend Receives Request

**Location:** Backend - `main.py` line ~300

**Code:**
```python
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    session: SessionState = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> ChatResponse:
    logger.info("Processing chat message for session %s", session.session_id)
    
    # Extract message
    user_message = request.message.strip()  # "Mark Manju absent today"
    
    # Add to session history
    session.add_message("user", user_message)
    
    # Convert to lowercase for checking
    lowered = user_message.lower()  # "mark manju absent today"
    
    # ... continues
```

**Console Output:**
```
INFO: Processing chat message for session abc123
INFO: User message: "Mark Manju absent today"
```

---

### Step 5: Send to Gemini AI

**Location:** Backend - `main.py` line ~400

**Code:**
```python
# Build context for Gemini
context_parts = []

# Add employee directory
try:
    employees = await absence_adapter.get_employees()
    employee_entries = [
        f"{emp.get('name')}|{emp.get('id')}|{emp.get('department')}"
        for emp in employees
        if emp.get("name")
    ]
    if employee_entries:
        context_parts.append(
            "EMPLOYEE_DIRECTORY: "
            + "; ".join(employee_entries)
        )
except Exception as e:
    logger.warning(f"Could not fetch employees: {e}")

# Add current date
from datetime import datetime
today = datetime.now().strftime("%Y-%m-%d")
day_name = datetime.now().strftime("%A")
context_parts.append(f"TODAY'S DATE: {today} ({day_name})")

full_context = " | ".join(context_parts)

# Call Gemini
gemini_response = gemini_client.generate(session, user_message, full_context)
```

**Context sent to Gemini:**
```
EMPLOYEE_DIRECTORY: Manju|1|Engineering; Ganesh|2|HR; Shreyas|3|Sales; Suhas|4|Marketing; Anushri|5|Finance | TODAY'S DATE: 2025-10-28 (Monday)

User request: Mark Manju absent today
```

---

### Step 6: Gemini Processes Request

**Location:** Backend - `gemini_client.py` line ~100

**Code:**
```python
def generate(self, session: SessionState, user_message: str, context: Optional[str] = None):
    try:
        # Build messages for Gemini
        messages = []
        
        # Add context
        if context:
            full_message = f"{context}\n\nUser request: {user_message}"
        else:
            full_message = user_message
        
        messages.append({"role": "user", "parts": [full_message]})
        
        # Call Gemini API
        response = self._model.generate_content(
            messages,
            tool_config={"function_calling_config": {"mode": "AUTO"}},
        )
        
        return response
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        raise
```

**What Gemini Sees:**
```
System Instruction:
"You are the Unified Operations AI Assistant. Today's date is 2025-10-28 (Monday). 
Always respond by calling one of the registered tools.

**Absence Management — use `absence_chat`:**
- action='mark_absence' with `employee_name`, `status` (A/P/V), optional `reason`, and `date`.
..."

User Message:
"EMPLOYEE_DIRECTORY: Manju|1|Engineering; Ganesh|2|HR; ... | TODAY'S DATE: 2025-10-28 (Monday)

User request: Mark Manju absent today"
```

**Gemini's Thinking Process:**
```
💭 Analyzing: "Mark Manju absent today"
   - Action: mark_absence
   - Employee: Manju (found in directory)
   - Status: A (absent)
   - Date: today (2025-10-28)
   - Reason: Not provided
   
   Decision: Call absence_chat tool
```

---

### Step 7: Gemini Returns Function Call

**Gemini's Response:**
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
                "action": "mark_absence",
                "employee_name": "Manju",
                "status": "A",
                "date": "today",
                "reason": ""
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
    📋 Raw Args: {'action': 'mark_absence', 'employee_name': 'Manju', 'status': 'A', 'date': 'today', 'reason': ''}
    ✅ Parsed Args: {'action': 'mark_absence', 'employee_name': 'Manju', 'status': 'A', 'date': 'today', 'reason': ''}
🎯 FINAL PARSED RESULT:
  Tool calls: 1
    - absence_chat: {'action': 'mark_absence', 'employee_name': 'Manju', 'status': 'A', 'date': 'today', 'reason': ''}
  Text: ''
  Thinking: 'Calling absence_chat → Action: mark_absence'
```

---

### Step 8: Parse Gemini Response

**Location:** Backend - `gemini_client.py` line ~200

**Code:**
```python
def parse_response(self, response: Any) -> Dict[str, Any]:
    if not response.candidates:
        raise RuntimeError("Gemini returned no candidates")
    
    candidate = response.candidates[0]
    parts = candidate.content.parts
    tool_calls = []
    
    for part in parts:
        if getattr(part, "function_call", None):
            func_call = part.function_call
            name = func_call.name  # "absence_chat"
            args = dict(func_call.args)  # Convert to dict
            
            tool_calls.append(ToolCall(name=name, arguments=args))
    
    return {
        "tool_calls": tool_calls,
        "text": "",
        "thinking": "Calling absence_chat → Action: mark_absence"
    }
```

**Parsed Result:**
```python
{
    "tool_calls": [
        ToolCall(
            name="absence_chat",
            arguments={
                "action": "mark_absence",
                "employee_name": "Manju",
                "status": "A",
                "date": "today",
                "reason": ""
            }
        )
    ],
    "text": "",
    "thinking": "Calling absence_chat → Action: mark_absence"
}
```

---

### Step 9: Handle absence_chat Tool Call

**Location:** Backend - `main.py` line ~500

**Code:**
```python
# Check if Gemini returned tool calls
if parsed_response["tool_calls"]:
    tool_call = parsed_response["tool_calls"][0]
    
    if tool_call.name == "absence_chat":
        response = await _handle_gemini_absence_call(session, tool_call, user_message)
        response.thinking = thinking
        return response
```

**Calls:**
```python
await _handle_gemini_absence_call(
    session=session,
    tool_call=ToolCall(name="absence_chat", arguments={...}),
    user_message="Mark Manju absent today"
)
```

---

### Step 10: Process Absence Marking

**Location:** Backend - `main.py` line ~600

**Code:**
```python
async def _handle_gemini_absence_call(session: SessionState, tool_call: ToolCall, user_message: str):
    args = tool_call.arguments
    action = args.get("action")  # "mark_absence"
    
    if action == "mark_absence":
        employee_name = args.get("employee_name", "").strip()  # "Manju"
        status = args.get("status", "A")  # "A"
        date_str = args.get("date", "today")  # "today"
        reason = args.get("reason", "")  # ""
        
        # Get employees list
        employees = await absence_adapter.get_employees()
        
        # Find matching employee
        matches = _find_employee_matches(employee_name, employees)
        
        if not matches:
            return ChatResponse(
                session_id=session.session_id,
                response=f"I couldn't find '{employee_name}'.",
                action_type="employee_not_found"
            )
        
        if len(matches) > 1:
            # Multiple matches - ask for clarification
            options = [
                DisambiguationOption(
                    id=f"emp_{emp['id']}",
                    label=emp['name'],
                    value=emp['name']
                ) for emp in matches
            ]
            return ChatResponse(
                session_id=session.session_id,
                response=f"Multiple employees found for '{employee_name}'. Please select:",
                action_type="disambiguation_required",
                disambiguation_options=options
            )
        
        # Single match found
        matched_employee = matches[0]  # {'id': 1, 'name': 'Manju', 'department': 'Engineering'}
        
        # Normalize date
        normalized_date = _normalize_date_str(date_str)  # "2025-10-28"
        
        # Check if reason is needed
        if not reason:
            # Ask for reason
            session.metadata["pending_action"] = {
                "type": "ask_reason",
                "data": {
                    "employee_name": matched_employee["name"],
                    "status": status,
                    "dates": [normalized_date],
                    "reason": ""
                }
            }
            return ChatResponse(
                session_id=session.session_id,
                response=f"Would you like to add a reason for marking {matched_employee['name']} as absent?",
                action_type="reason_confirmation",
                confirmation_buttons=[
                    ConfirmationButton(id="reason_yes", label="Yes, add reason", value="yes", style="primary"),
                    ConfirmationButton(id="reason_no", label="No, skip", value="no", style="secondary")
                ]
            )
        
        # Execute marking (if reason provided or skipped)
        result = await absence_adapter.mark_absence(
            employee_name=matched_employee["name"],
            status=status,
            dates=[normalized_date],
            reason=reason
        )
        
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Absence marked successfully"),
            action_type="absence_marked"
        )
```

**In this case (no reason provided):**
```python
# Returns confirmation request
return ChatResponse(
    session_id="abc123",
    response="Would you like to add a reason for marking Manju as absent?",
    action_type="reason_confirmation",
    confirmation_buttons=[
        {"id": "reason_yes", "label": "Yes, add reason", "value": "yes"},
        {"id": "reason_no", "label": "No, skip", "value": "no"}
    ]
)
```

---

### Step 11: Return Response to Frontend

**HTTP Response:**
```json
{
  "session_id": "abc123",
  "response": "Would you like to add a reason for marking Manju as absent?",
  "action_type": "reason_confirmation",
  "action_data": {
    "theme": "absence"
  },
  "confirmation_buttons": [
    {
      "id": "reason_yes",
      "label": "Yes, add reason",
      "value": "yes",
      "style": "primary"
    },
    {
      "id": "reason_no",
      "label": "No, skip",
      "value": "no",
      "style": "secondary"
    }
  ],
  "thinking": "Calling absence_chat → Action: mark_absence"
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
  content: "Would you like to add a reason for marking Manju as absent?",
  timestamp: new Date().toISOString(),
  metadata: {
    actionType: "reason_confirmation",
    actionData: { theme: "absence" },
    confirmationButtons: [
      { id: "reason_yes", label: "Yes, add reason", value: "yes", style: "primary" },
      { id: "reason_no", label: "No, skip", value: "no", style: "secondary" }
    ],
    thinking: "Calling absence_chat → Action: mark_absence"
  }
};

// Add to messages
setMessages(prev => [...prev, assistantMessage]);

// Set active buttons
setLastActiveButtonMessageId(assistantMessage.id);

// Update theme
setCurrentMode('absence');

// Stop loading
setIsLoading(false);
```

---

### Step 13: Display Response

**What User Sees:**

```
┌─────────────────────────────────────────────────────────┐
│ 👤 You                                    10:30 AM      │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Mark Manju absent today                             │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ 🤖 AI Assistant                           10:30 AM      │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 💭 Calling absence_chat → Action: mark_absence      │ │
│ │                                                      │ │
│ │ Would you like to add a reason for marking Manju    │ │
│ │ as absent?                                           │ │
│ │                                                      │ │
│ │ ┌──────────────────┐  ┌──────────────────┐         │ │
│ │ │ ✓ Yes, add reason│  │ ✗ No, skip       │         │ │
│ │ └──────────────────┘  └──────────────────┘         │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

### Step 14: User Clicks "No, skip"

**Location:** Frontend - `UnifiedChat.jsx` line ~450

**Code:**
```javascript
const handleConfirmationClick = async (buttonValue) => {
  // User clicked "No, skip" button
  // buttonValue = "no"
  
  setInputValue('no');
  
  // Send message
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: 'no',
      session_id: sessionId
    })
  });
  
  const data = await response.json();
  // ... handle response
};
```

**Request:**
```json
{
  "message": "no",
  "session_id": "abc123"
}
```

---

### Step 15: Backend Handles "No" Response

**Location:** Backend - `main.py` line ~800

**Code:**
```python
# Check for pending action
pending_action = session.metadata.get("pending_action")

if pending_action and pending_action.get("type") == "ask_reason":
    if lowered in {"no", "n", "nope", "not now"}:
        # User said no to adding reason
        pending_action["data"]["reason"] = "Not provided"
        pending_action["type"] = "mark_absence"
        return await _execute_pending_action(session, pending_action)
```

**Executes:**
```python
await _execute_pending_action(
    session=session,
    pending_action={
        "type": "mark_absence",
        "data": {
            "employee_name": "Manju",
            "status": "A",
            "dates": ["2025-10-28"],
            "reason": "Not provided"
        }
    }
)
```

---

### Step 16: Execute Absence Marking

**Location:** Backend - `main.py` line ~900

**Code:**
```python
async def _execute_pending_action(session, pending_action):
    action_type = pending_action.get("type")
    data = pending_action.get("data", {})
    
    if action_type == "mark_absence":
        employee_name = data.get("employee_name")  # "Manju"
        status = data.get("status", "A")  # "A"
        dates = data.get("dates", [])  # ["2025-10-28"]
        reason = data.get("reason", "")  # "Not provided"
        
        # Call absence adapter
        result = await absence_adapter.mark_absence(
            employee_name,
            dates,
            status,
            reason
        )
        
        # Clear pending action
        session.metadata.pop("pending_action", None)
        
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message"),
            action_type="absence_marked"
        )
```

---

### Step 17: Call Absence API

**Location:** Backend - `services/absence.py` line ~100

**Code:**
```python
async def mark_absence(self, employee_name: str, dates: List[str], status: str, reason: str):
    try:
        # Prepare payload
        payload = {
            "employee_name": employee_name,  # "Manju"
            "dates": dates,  # ["2025-10-28"]
            "status": status,  # "A"
            "reason": reason  # "Not provided"
        }
        
        # Call absence API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/absence/mark",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "message": f"✅ Marked {employee_name} as absent for {dates[0]}"
                    }
                else:
                    error = await response.text()
                    return {
                        "success": False,
                        "message": f"❌ Failed to mark absence: {error}"
                    }
    except Exception as e:
        logger.error(f"Error marking absence: {e}")
        return {
            "success": False,
            "message": f"❌ Error: {str(e)}"
        }
```

**API Request:**
```http
POST http://localhost:8010/api/absence/mark
Content-Type: application/json

{
  "employee_name": "Manju",
  "dates": ["2025-10-28"],
  "status": "A",
  "reason": "Not provided"
}
```

**API Response:**
```json
{
  "success": true,
  "message": "Absence marked successfully",
  "data": {
    "employee_id": 1,
    "employee_name": "Manju",
    "date": "2025-10-28",
    "status": "A",
    "reason": "Not provided"
  }
}
```

---

### Step 18: Return Final Response

**HTTP Response to Frontend:**
```json
{
  "session_id": "abc123",
  "response": "✅ Marked Manju as absent for 2025-10-28",
  "action_type": "absence_marked",
  "action_data": {
    "theme": "absence"
  }
}
```

---

### Step 19: Display Final Result

**What User Sees:**

```
┌─────────────────────────────────────────────────────────┐
│ 👤 You                                    10:30 AM      │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Mark Manju absent today                             │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ 🤖 AI Assistant                           10:30 AM      │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Would you like to add a reason for marking Manju    │ │
│ │ as absent?                                           │ │
│ │ [Yes, add reason] [No, skip]                        │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ 👤 You                                    10:30 AM      │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ no                                                   │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ 🤖 AI Assistant                           10:30 AM      │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ✅ Marked Manju as absent for 2025-10-28            │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Complete Timeline

```
0.0s  - User presses Enter
0.1s  - Frontend sends HTTP request
0.2s  - Backend receives request
0.3s  - Backend calls Gemini API
1.0s  - Gemini processes and returns function call
1.1s  - Backend parses Gemini response
1.2s  - Backend handles absence_chat tool
1.3s  - Backend returns confirmation request
1.4s  - Frontend displays confirmation buttons
---
5.0s  - User clicks "No, skip"
5.1s  - Frontend sends "no" message
5.2s  - Backend executes pending action
5.3s  - Backend calls absence API
5.5s  - Absence API marks absence
5.6s  - Backend returns success message
5.7s  - Frontend displays success message
```

**Total Time:** ~5.7 seconds (including user interaction time)

---

## 🎯 Summary

### What Happened:
1. ✅ User typed "Mark Manju absent today"
2. ✅ Frontend sent to backend
3. ✅ Backend sent to Gemini
4. ✅ Gemini called absence_chat tool
5. ✅ Backend asked for reason confirmation
6. ✅ User clicked "No, skip"
7. ✅ Backend marked absence via API
8. ✅ Success message displayed

### Files Involved:
- `frontend/src/UnifiedChat.jsx` - UI and HTTP requests
- `backend/app/main.py` - Main endpoint and logic
- `backend/app/gemini_client.py` - Gemini integration
- `backend/app/services/absence.py` - Absence API calls

### API Calls Made:
1. POST `/api/chat` (mark request)
2. POST `/api/chat` (no response)
3. POST `/absence/mark` (actual marking)

---

**Continue to COMPLETE_FLOW_EXAMPLE2_QUERY_ABSENCES.md for the "Show September absences" example!**

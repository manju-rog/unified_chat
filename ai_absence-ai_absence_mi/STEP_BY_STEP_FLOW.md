# 🎯 Step-by-Step Flow: "Mark Manju absent today"

## What Happens When You Press Send

### Step 1: User Types and Clicks Send
**What happens:** You type "Mark Manju absent today" in the chat box and click the send button.

**Function Called:** `handleSendMessage()`
**Parameters:** 
- `inputValue = "Mark Manju absent today"`
- `conversationId = "conv_1724678400000_abc123def"`

**What the function does:**
1. Gets your message: `const message = inputValue.trim()`
2. Validates it's not empty: `if (!message || isLoading) return`
3. Clears the input box: `setInputValue('')`
4. Adds your message to chat: `addUserMessage(message)`
5. Shows loading spinner: `setLoading(true)`

**Output:** Message is ready to send to backend

---

### Step 2: Frontend Sends HTTP Request
**What happens:** The frontend sends your message to the backend server.

**Function Called:** `callBackendAI(message, conversationId)`
**Parameters:**
- `message = "Mark Manju absent today"`
- `conversationId = "conv_1724678400000_abc123def"`

**HTTP Request Sent:**
```json
POST http://localhost:8080/api/ai/chat
Content-Type: application/json

{
  "message": "Mark Manju absent today",
  "conversationId": "conv_1724678400000_abc123def"
}
```

**Output:** HTTP request is sent to backend

---

### Step 3: Backend Receives Request
**What happens:** The backend server receives your request and starts processing it.

**Function Called:** `AIController.chat()`
**Parameters:**
- `request.getMessage() = "Mark Manju absent today"`
- `request.getConversationId() = "conv_1724678400000_abc123def"`

**What the function does:**
1. Logs the request: `logger.info("Chat request - Message length: 25, ConversationId: conv_1724678400000_abc123def")`
2. Validates message exists: `if (request.getMessage() == null || request.getMessage().trim().isEmpty())`
3. Validates message length: `if (message.length() > 10000)`
4. Cleans the message: `String message = request.getMessage().trim()`
5. Ensures conversation ID: `final String conversationId = request.getConversationId().trim()`

**Output:** Validated request is passed to AI service

---

### Step 4: AI Service Starts Processing
**What happens:** The AI service coordinates the entire process.

**Function Called:** `AIService.processChatMessage()`
**Parameters:**
- `message = "Mark Manju absent today"`
- `conversationId = "conv_1724678400000_abc123def"`

**What the function does:**
1. Gets conversation context: `context = conversationContextService.getContext(conversationId)`
2. Adds user message to history: `conversationContextService.addUserMessage(conversationId, message)`
3. Loads all employees: `employees = employeeService.getAllEmployees()`
4. Gets employee names: `employeeNames = ["Manju", "Shreyas", "Ganesh"]`
5. Builds system prompt: `systemPrompt = geminiAPIService.buildSystemPrompt(employeeNames)`

**Employee Data Loaded:**
```json
[
  {"id": 1, "name": "Manju", "department": "Engineering"},
  {"id": 2, "name": "Shreyas", "department": "Marketing"},
  {"id": 3, "name": "Ganesh", "department": "Sales"}
]
```

**Output:** Context is prepared for AI call

---

### Step 5: System Prompt is Built
**What happens:** The system creates instructions for the AI with employee context.

**Function Called:** `GeminiAPIService.buildSystemPrompt()`
**Parameters:** `employeeNames = ["Manju", "Shreyas", "Ganesh"]`

**System Prompt Created:**
```
You are an AI assistant for absence management. You help users mark employee attendance and query absence information.

Available employees:
- Manju (ID: 1, Department: Engineering)
- Shreyas (ID: 2, Department: Marketing)  
- Ganesh (ID: 3, Department: Sales)

Current date: 2025-08-26

IMPORTANT: For ANY attendance marking request (mark, set, put someone absent/present/vacation), you MUST use the markAbsence function. Never respond with text for these operations.

For ANY query request (who was absent, show absences, check attendance), you MUST use the queryAbsence function.

Use exact employee names from the list above.
```

**Output:** Complete system prompt with employee context

---

### Step 6: Request Sent to Gemini AI
**What happens:** The system sends your message with context to Google's Gemini AI.

**Function Called:** `GeminiAPIService.callGeminiAPI()`
**Parameters:**
- `systemPrompt = [full prompt from step 5]`
- `userInput = "Mark Manju absent today"`
- `conversationHistory = []` (empty for new conversation)

**Request Sent to Gemini:**
```json
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_API_KEY
Content-Type: application/json

{
  "contents": [{
    "parts": [{
      "text": "You are an AI assistant for absence management...\nAvailable employees: Manju, Shreyas, Ganesh...\nCurrent date: 2025-08-26\n\nUser request: Mark Manju absent today"
    }]
  }],
  "tools": [{
    "functionDeclarations": [{
      "name": "markAbsence",
      "description": "REQUIRED: Use this function for ANY request to mark, set, or change employee attendance status",
      "parameters": {
        "type": "object",
        "properties": {
          "employeeName": {"type": "string", "description": "Full name of the employee"},
          "dates": {"type": "array", "items": {"type": "string"}, "description": "Array of dates in YYYY-MM-DD format"},
          "status": {"type": "string", "enum": ["P", "A", "V"], "description": "P=Present, A=Absent, V=Vacation"}
        },
        "required": ["employeeName", "dates", "status"]
      }
    }]
  }],
  "generationConfig": {
    "temperature": 0.1,
    "topK": 20,
    "topP": 0.7,
    "maxOutputTokens": 1000
  },
  "toolConfig": {
    "functionCallingConfig": {
      "mode": "ANY"
    }
  }
}
```

**Output:** Request is sent to Gemini AI

---

### Step 7: Gemini AI Processes and Responds
**What happens:** Gemini AI understands your request and decides to call the markAbsence function.

**AI Analysis:**
1. Identifies intent: "Mark" + "absent" = attendance marking operation
2. Extracts employee: "Manju" (matches available employee)
3. Extracts date: "today" = current date = "2025-08-26"
4. Extracts status: "absent" = "A"
5. Decides to use markAbsence function instead of text response

**Response from Gemini:**
```json
{
  "candidates": [{
    "content": {
      "parts": [{
        "functionCall": {
          "name": "markAbsence",
          "args": {
            "employeeName": "Manju",
            "dates": ["2025-08-26"],
            "status": "A"
          }
        }
      }]
    },
    "finishReason": "STOP"
  }]
}
```

**Output:** Function call with extracted parameters

---

### Step 8: Backend Processes Function Call
**What happens:** The backend receives the AI's function call and extracts the parameters.

**Function Called:** `AIService.processGeminiResponse()`
**Parameters:** `geminiResponse` containing the function call

**What the function does:**
1. Detects function call: `if (geminiResponse.isFunctionCall())`
2. Gets function name: `functionName = "markAbsence"`
3. Gets function args: `functionArgs = {"employeeName": "Manju", "dates": ["2025-08-26"], "status": "A"}`
4. Routes to executor: `return executeAbsenceAction(functionArgs, context, employees)`

**Output:** Function call is routed to absence action executor

---

### Step 9: Execute Absence Action
**What happens:** The system validates the parameters and prepares to mark the absence.

**Function Called:** `AIService.executeAbsenceAction()`
**Parameters:**
- `functionArgs = {"employeeName": "Manju", "dates": ["2025-08-26"], "status": "A"}`
- `context = conversation context`
- `employees = [list of all employees]`

**What the function does:**
1. Extracts employee name: `employeeName = "Manju"`
2. Extracts status: `status = "A"`
3. Extracts dates: `dates = [LocalDate.of(2025, 8, 26)]`
4. Finds employee: `employee = employees.stream().filter(emp -> emp.getName().equalsIgnoreCase("Manju")).findFirst()`
5. Found: `Employee{id=1, name="Manju", department="Engineering"}`

**Output:** Employee found, ready to mark absence

---

### Step 10: Mark Absence in Database
**What happens:** The system creates an absence record in the database.

**Function Called:** `AbsenceService.markAbsenceFromAI()`
**Parameters:**
- `employeeId = 1`
- `dates = [LocalDate.of(2025, 8, 26)]`
- `status = "A"`
- `reason = "Marked by AI Assistant"`

**What the function does:**
1. Finds employee: `employee = employeeRepository.findById(1)` → Returns Manju
2. Loops through dates: `for (LocalDate date : dates)` → Processes 2025-08-26
3. Checks existing record: `existingRecord = absenceRecordRepository.findByEmployeeIdAndAbsenceDate(1, 2025-08-26)` → None found
4. Creates new record: `record = new AbsenceRecord()`
5. Sets properties:
   - `record.setEmployee(employee)` → Manju
   - `record.setAbsenceDate(date)` → 2025-08-26
   - `record.setAbsenceType(AbsenceRecord.AbsenceType.A)` → Absent
   - `record.setReason("Marked by AI Assistant")`
   - `record.setStatus(AbsenceRecord.AbsenceStatus.APPROVED)`
6. Saves to database: `absenceRecordRepository.save(record)`

**SQL Executed:**
```sql
INSERT INTO absence_records (
  employee_id, 
  absence_date, 
  absence_type, 
  reason, 
  status, 
  created_at, 
  updated_at
) VALUES (
  1, 
  '2025-08-26', 
  'A', 
  'Marked by AI Assistant', 
  'APPROVED', 
  '2025-08-26 10:30:00', 
  '2025-08-26 10:30:00'
);
```

**Output:** Absence record saved in database

---

### Step 11: Build Success Response
**What happens:** The system creates a success message to send back to the frontend.

**Function Called:** `AIService.executeAbsenceAction()` (continuation)

**What the function does:**
1. Converts status to text: `statusText = "Absent"` (from "A")
2. Formats date: `dateText = "August 26, 2025"` (from 2025-08-26)
3. Builds message: `responseText = "✅ Got it! I've marked Manju as Absent for August 26, 2025."`
4. Creates action data:
```json
{
  "employeeName": "Manju",
  "employeeId": 1,
  "dates": ["2025-08-26"],
  "status": "A"
}
```
5. Saves to conversation: `conversationContextService.addAssistantMessage(conversationId, responseText)`

**Response Created:**
```json
{
  "success": true,
  "response": "✅ Got it! I've marked Manju as Absent for August 26, 2025.",
  "actionType": "markAbsence",
  "actionData": {
    "employeeName": "Manju",
    "employeeId": 1,
    "dates": ["2025-08-26"],
    "status": "A"
  },
  "conversationId": "conv_1724678400000_abc123def"
}
```

**Output:** Success response ready to send

---

### Step 12: Send Response to Frontend
**What happens:** The backend sends the success response back to the frontend.

**HTTP Response Sent:**
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "response": "✅ Got it! I've marked Manju as Absent for August 26, 2025.",
  "actionType": "markAbsence",
  "actionData": {
    "employeeName": "Manju",
    "employeeId": 1,
    "dates": ["2025-08-26"],
    "status": "A"
  },
  "conversationId": "conv_1724678400000_abc123def"
}
```

**Output:** Response received by frontend

---

### Step 13: Frontend Processes Response
**What happens:** The frontend receives the response and processes it.

**Function Called:** `Chatbot.handleSendMessage()` (continuation)

**What the function does:**
1. Receives response: `backendResponse = await callBackendAI(message, conversationId)`
2. Checks success: `if (!backendResponse.success)` → Success = true, continues
3. Checks action type: `if (backendResponse.actionType === 'markAbsence')` → True
4. Extracts action data: `actionData = backendResponse.actionData`
5. Creates AI response:
```javascript
const aiResponse = {
  action: 'markAbsence',
  args: {
    employeeName: "Manju",
    employeeId: 1,
    dates: ["2025-08-26"],
    status: "A"
  }
}
```
6. Sends to ActionBus: `executeCommand(aiResponse)`
7. Shows AI message: `addAiMessage("✅ Got it! I've marked Manju as Absent for August 26, 2025.")`
8. Shows system message: `addSystemMessage("Action executed: Manju → Absent (2025-08-26)", 'success')`

**Output:** UI updates triggered

---

### Step 14: ActionBus Updates Grid
**What happens:** The ActionBusHandler receives the command and updates the visual grid.

**Function Called:** `ActionBusHandler useEffect`
**Parameters:** `pendingCommand = {action: 'markAbsence', args: {employeeId: 1, dates: ["2025-08-26"], status: "A"}}`

**What the function does:**
1. Detects command: `if (pendingCommand?.action === 'markAbsence')`
2. Extracts data: `const { employeeId, dates, status } = pendingCommand.args`
3. Updates each date:
   - `cellKey = "1-2025-08-26"` (employee 1, date 2025-08-26)
   - `handleStatusChange("1-2025-08-26", "A", 1, "2025-08-26")`
4. Schedules auto-save: `setTimeout(() => handleSaveChanges(), 100)`
5. Clears command: `clearCommand()`

**Grid Update:**
- Cell "1-2025-08-26" changes from "P" (green) to "A" (red)
- Manju's cell for today now shows red background with "A"

**Output:** Visual grid updated

---

### Step 15: Auto-Save Changes
**What happens:** The system automatically saves the changes to ensure persistence.

**Function Called:** `grid_memory.handleSaveChanges()`

**What the function does:**
1. Prepares changes:
```javascript
const changes = [{
  employeeId: 1,
  absenceDate: "2025-08-26",
  absenceType: "A",
  reason: "Updated via AI Assistant"
}]
```
2. Sends to backend: `await api.absences.bulkUpdate(changes)`
3. Clears unsaved changes: `setHasChanges(false)`
4. Shows success notification

**HTTP Request Sent:**
```json
PUT http://localhost:8080/api/absences/bulk-update
Content-Type: application/json

[{
  "employeeId": 1,
  "absenceDate": "2025-08-26",
  "absenceType": "A",
  "reason": "Updated via AI Assistant"
}]
```

**Output:** Changes saved and confirmed

---

## Final Result

**What you see:**
1. **Chat Interface:**
   - Your message: "Mark Manju absent today"
   - AI response: "✅ Got it! I've marked Manju as Absent for August 26, 2025."
   - System message: "Action executed: Manju → Absent (2025-08-26)"

2. **Grid Interface:**
   - Manju's cell for today (Aug 26) is now red with "A"
   - Changed from green "P" to red "A"

3. **Database:**
   - New record in absence_records table
   - Employee: Manju (ID: 1)
   - Date: 2025-08-26
   - Type: A (Absent)
   - Status: APPROVED

**Total time:** ~2-3 seconds from send to completion
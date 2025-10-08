# 🚀 Complete End-to-End Flow Guide: Frontend ↔ Backend ↔ Database ↔ AI

## 📋 Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Data Flow Diagrams](#data-flow-diagrams)
3. [Frontend Components](#frontend-components)
4. [Backend Services](#backend-services)
5. [Database Layer](#database-layer)
6. [AI Integration](#ai-integration)
7. [Function Calling Mechanism](#function-calling-mechanism)
8. [Complete Code Flow Examples](#complete-code-flow-examples)
9. [Testing & Verification](#testing--verification)

---

## 🏗️ System Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FRONTEND      │    │    BACKEND      │    │    DATABASE     │    │   AI SERVICE    │
│   (React)       │    │  (Spring Boot)  │    │   (SQLite)      │    │   (Gemini)      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Grid UI       │◄──►│ • REST APIs     │◄──►│ • Employee      │    │ • Function      │
│ • Chatbot       │    │ • AI Controller │    │ • AbsenceRecord │◄──►│   Calling       │
│ • Action Bus    │    │ • Services      │    │ • Repositories  │    │ • Context       │
│ • State Mgmt    │    │ • Data Layer    │    │ • Transactions  │    │ • NLP           │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🔄 Key Integration Points:
- **Frontend ↔ Backend**: REST API calls (`/api/employees`, `/api/absences/bulk-update`, `/api/ai/chat`)
- **Backend ↔ Database**: JPA/Hibernate with SQLite
- **Backend ↔ AI**: Gemini API with function calling
- **AI ↔ Database**: Through backend services (AbsenceService, EmployeeService)

---

## 📊 Data Flow Diagrams

### 1. 🎯 AI Action Flow (User → AI → Database → UI)
```
User Input: "Mark Manju absent today"
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (React)                                                │
│ ┌─────────────────┐                                             │
│ │ Chatbot.jsx     │ → Captures user input                       │
│ │ - handleSubmit  │ → Sends to backend                          │
│ └─────────────────┘                                             │
└─────────────────────────────────────────────────────────────────┘
    ↓ POST /api/ai/chat
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND (Spring Boot)                                           │
│ ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐ │
│ │ AIController    │ → │ AIService       │ → │ GeminiAPIService│ │
│ │ - chat()        │   │ - processChat() │   │ - callGemini()  │ │
│ └─────────────────┘   └─────────────────┘   └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
    ↓ Function Call: markAbsence
┌─────────────────────────────────────────────────────────────────┐
│ AI SERVICE (Gemini)                                             │
│ ┌─────────────────┐                                             │
│ │ Function Call   │ → Parses: employeeName="Manju"             │
│ │ - markAbsence   │          dates=["2025-08-26"]              │
│ │                 │          status="A"                        │
│ └─────────────────┘                                             │
└─────────────────────────────────────────────────────────────────┘
    ↓ Returns structured data
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND (Spring Boot)                                           │
│ ┌─────────────────┐   ┌─────────────────┐                       │
│ │ AIService       │ → │ AbsenceService  │                       │
│ │ - executeAction │   │ - markAbsence   │                       │
│ │                 │   │   FromAI()      │                       │
│ └─────────────────┘   └─────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
    ↓ @Transactional
┌─────────────────────────────────────────────────────────────────┐
│ DATABASE (SQLite)                                               │
│ ┌─────────────────┐   ┌─────────────────┐                       │
│ │ AbsenceRecord   │ ← │ Employee        │                       │
│ │ Repository      │   │ Repository      │                       │
│ │ - save()        │   │ - findById()    │                       │
│ └─────────────────┘   └─────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
    ↓ Success response
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (React)                                                │
│ ┌─────────────────┐   ┌─────────────────┐                       │
│ │ ActionBusHandler│ → │ AbsencesPage    │                       │
│ │ - refreshData() │   │ - updateGrid()  │                       │
│ └─────────────────┘   └─────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

### 2. 🖱️ Manual Grid Action Flow (User → UI → Database)
```
User clicks cell in grid
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (React)                                                │
│ ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐ │
│ │ OneDayCell.jsx  │ → │ AbsencesPage    │ → │ grid_memory.js  │ │
│ │ - handleClick() │   │ - handleStatus  │   │ - handleSave    │ │
│ │                 │   │   Change()      │   │   Changes()     │ │
│ └─────────────────┘   └─────────────────┘   └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
    ↓ PUT /api/absences/bulk-update
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND (Spring Boot)                                           │
│ ┌─────────────────┐   ┌─────────────────┐                       │
│ │ AbsenceController│ → │ AbsenceService  │                       │
│ │ - bulkUpdate()  │   │ - bulkUpdate    │                       │
│ │                 │   │   Absences()    │                       │
│ └─────────────────┘   └─────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
    ↓ @Transactional
┌─────────────────────────────────────────────────────────────────┐
│ DATABASE (SQLite)                                               │
│ ┌─────────────────┐                                             │
│ │ absence_records │ ← INSERT/UPDATE records                     │
│ │ employees       │                                             │
│ └─────────────────┘                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Frontend Components

### 📁 File Structure
```
frontend/src/
├── components/
│   ├── ActionBusHandler.jsx     # 🚌 Processes AI commands
│   └── Chatbot/
│       ├── Chatbot.jsx          # 💬 AI chat interface
│       └── AbsenceQueryPopup.jsx # 📊 Query results display
├── pages/Absences/
│   ├── AbsencesPage.jsx         # 📅 Main grid page
│   ├── parts/
│   │   ├── GridTable.jsx        # 📋 Table container
│   │   ├── OneEmployeeRow.jsx   # 👤 Employee row
│   │   └── OneDayCell.jsx       # 📱 Individual cell
│   └── save_and_changes/
│       ├── grid_memory.js       # 💾 Data persistence
│       └── save_actions.js      # ⚡ User actions
├── memory/
│   ├── data_memory.js           # 🗄️ Global state
│   └── chatbot_memory.js        # 🤖 Chat state
└── services/
    └── api.js                   # 🌐 Backend API calls
```

### 🔑 Key Components Explained

#### 1. **OneDayCell.jsx** - The Heart of the Grid
```javascript
// Cell ID Generation: employeeId-isoString (e.g., "1-2025-08-26")
const cellKey = makeKey(employeeId, isoString);
const status = absenceData[cellKey] || 'P'; // Default to Present

// Status Cycling: P → A → V → P
const getNextStatus = (currentStatus) => {
  const statusOrder = ['P', 'A', 'V'];
  const currentIndex = statusOrder.indexOf(currentStatus);
  return statusOrder[(currentIndex + 1) % statusOrder.length];
};

// Click Handler
const handleCellClick = () => {
  const nextStatus = getNextStatus(status);
  onStatusChange(cellKey, nextStatus, employeeId, isoString);
};
```

#### 2. **ActionBusHandler.jsx** - AI Command Processor
```javascript
// Listens for AI commands and executes them
useEffect(() => {
  if (pendingCommand?.action === 'markAbsence') {
    const { employeeId, dates, status } = pendingCommand.args;
    
    // Update UI immediately
    dates.forEach(date => {
      const cellKey = `${employeeId}-${date}`;
      handleStatusChange(cellKey, status, employeeId, date);
    });
    
    // Auto-save to backend
    setTimeout(() => handleSaveChanges(), 100);
    clearCommand();
  }
}, [pendingCommand]);
```

#### 3. **grid_memory.js** - Data Persistence Layer
```javascript
// Load data from backend
const loadAbsenceData = useCallback(async () => {
  const employees = await api.employees.getAll();
  
  // Convert to grid format: {employeeId-date: status}
  const newAbsenceData = {};
  employees.forEach(employee => {
    employee.absenceRecords?.forEach(record => {
      const cellKey = `${employee.id}-${record.absenceDate}`;
      newAbsenceData[cellKey] = record.absenceType;
    });
  });
  
  setAbsenceData(newAbsenceData);
}, []);

// Save changes to backend
const handleSaveChanges = useCallback(async () => {
  const changes = recentChanges.map(change => ({
    employeeId: change.employeeId,
    absenceDate: change.date,
    absenceType: change.newStatus,
    reason: 'Updated via grid'
  }));
  
  await api.absences.bulkUpdate(changes);
  setHasChanges(false);
  setRecentChanges([]);
}, [recentChanges]);
```

---

## ⚙️ Backend Services

### 📁 File Structure
```
backend/src/main/java/com/companyname/absence_management/
├── controllers/
│   ├── AIController.java           # 🤖 AI chat endpoint
│   ├── EmployeeController.java     # 👥 Employee CRUD
│   └── AbsenceController.java      # 📅 Absence operations
├── services/
│   ├── AIService.java              # 🧠 AI logic coordinator
│   ├── GeminiAPIService.java       # 🔗 Gemini API client
│   ├── AbsenceService.java         # 📊 Absence business logic
│   └── EmployeeService.java        # 👤 Employee business logic
├── model/
│   ├── Employee.java               # 👤 Employee entity
│   └── AbsenceRecord.java          # 📅 Absence entity
├── repository/
│   ├── EmployeeRepository.java     # 👥 Employee data access
│   └── AbsenceRecordRepository.java # 📅 Absence data access
└── dto/
    ├── ChatRequestDTO.java         # 💬 Chat input
    ├── ChatResponseDTO.java        # 💬 Chat output
    └── AbsenceChangeDTO.java       # 📊 Bulk update format
```

### 🔑 Key Services Explained

#### 1. **AIController.java** - Entry Point for AI
```java
@PostMapping("/chat")
public ResponseEntity<ChatResponseDTO> chat(@RequestBody ChatRequestDTO request) {
    // Validate input
    if (request.getMessage() == null || request.getMessage().trim().isEmpty()) {
        return ResponseEntity.badRequest()
            .body(ChatResponseDTO.error("Message cannot be empty", request.getConversationId()));
    }
    
    // Process with AI service
    Mono<ChatResponseDTO> responseMono = aiService.processUserMessage(
        request.getMessage(), 
        request.getConversationId()
    );
    
    // Return response
    ChatResponseDTO response = responseMono.block();
    return ResponseEntity.ok(response);
}
```

#### 2. **AIService.java** - AI Logic Coordinator
```java
public Mono<ChatResponseDTO> processUserMessage(String message, String conversationId) {
    // Get conversation context
    ConversationContext context = conversationContextService.getOrCreateContext(conversationId);
    
    // Add user message to history
    conversationContextService.addUserMessage(conversationId, message);
    
    // Load employee data for context
    List<Employee> employees = employeeService.getAllEmployees();
    
    // Call Gemini API with function calling
    return geminiAPIService.generateResponse(message, context, employees)
        .flatMap(geminiResponse -> processGeminiResponse(geminiResponse, context, employees));
}

private Mono<ChatResponseDTO> executeAbsenceAction(JsonNode functionArgs, 
                                                  ConversationContext context, 
                                                  List<Employee> employees) {
    // Extract parameters
    String employeeName = functionArgs.get("employeeName").asText();
    String status = functionArgs.get("status").asText();
    List<LocalDate> dates = parseDates(functionArgs.get("dates"));
    
    // Find employee
    Employee employee = findEmployeeByName(employeeName, employees);
    
    // Execute absence marking
    absenceService.markAbsenceFromAI(employee.getId(), dates, status, "Marked by AI Assistant");
    
    // Return success response
    return Mono.just(ChatResponseDTO.success(
        "✅ Got it! I've marked " + employee.getName() + " as " + getStatusText(status),
        "markAbsence",
        createActionData(employee, dates, status),
        context.getConversationId()
    ));
}
```

#### 3. **AbsenceService.java** - Business Logic
```java
@Transactional
public void markAbsenceFromAI(Long employeeId, List<LocalDate> dates, String status, String reason) {
    Employee employee = employeeRepository.findById(employeeId)
        .orElseThrow(() -> new EmployeeNotFoundException(employeeId));

    for (LocalDate date : dates) {
        // Check for existing record
        Optional<AbsenceRecord> existingRecord = 
            absenceRecordRepository.findByEmployeeIdAndAbsenceDate(employeeId, date);

        if ("P".equalsIgnoreCase(status)) {
            // Present = delete absence record
            existingRecord.ifPresent(absenceRecordRepository::delete);
        } else {
            // Create or update absence record
            AbsenceRecord record = existingRecord.orElse(new AbsenceRecord());
            record.setEmployee(employee);
            record.setAbsenceDate(date);
            record.setAbsenceType(AbsenceRecord.AbsenceType.valueOf(status.toUpperCase()));
            record.setReason(reason);
            record.setStatus(AbsenceRecord.AbsenceStatus.APPROVED);
            
            absenceRecordRepository.save(record);
        }
    }
}

@Transactional
public void bulkUpdateAbsences(List<AbsenceChangeDTO> changes) {
    for (AbsenceChangeDTO dto : changes) {
        Employee employee = employeeRepository.findById(dto.getEmployeeId())
            .orElseThrow(() -> new EmployeeNotFoundException(dto.getEmployeeId()));

        LocalDate absenceDate = LocalDate.parse(dto.getAbsenceDate());
        
        Optional<AbsenceRecord> existingRecord = 
            absenceRecordRepository.findByEmployeeIdAndAbsenceDate(employee.getId(), absenceDate);

        if ("P".equalsIgnoreCase(dto.getAbsenceType())) {
            existingRecord.ifPresent(absenceRecordRepository::delete);
        } else {
            AbsenceRecord record = existingRecord.orElse(new AbsenceRecord());
            record.setEmployee(employee);
            record.setAbsenceDate(absenceDate);
            record.setAbsenceType(AbsenceRecord.AbsenceType.valueOf(dto.getAbsenceType().toUpperCase()));
            record.setReason(dto.getReason() != null ? dto.getReason() : "Updated via grid");
            record.setStatus(AbsenceRecord.AbsenceStatus.APPROVED);
            
            absenceRecordRepository.save(record);
        }
    }
}
```

---

## 🗄️ Database Layer

### 📊 Entity Relationships
```sql
-- Employee Table
CREATE TABLE employees (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    department VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Absence Records Table
CREATE TABLE absence_records (
    id BIGINT PRIMARY KEY,
    employee_id BIGINT NOT NULL,
    absence_date DATE NOT NULL,
    absence_type VARCHAR(255) CHECK (absence_type IN ('P','A','V')),
    reason VARCHAR(500),
    status VARCHAR(255) CHECK (status IN ('PENDING','APPROVED','REJECTED')),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

-- Indexes for performance
CREATE INDEX idx_absence_records_employee_id ON absence_records(employee_id);
CREATE INDEX idx_absence_records_date ON absence_records(absence_date);
```

### 🔗 JPA Entity Mapping
```java
@Entity
@Table(name = "employees")
public class Employee {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String name;
    
    @OneToMany(mappedBy = "employee", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<AbsenceRecord> absenceRecords = new ArrayList<>();
}

@Entity
@Table(name = "absence_records")
public class AbsenceRecord {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "employee_id", nullable = false)
    private Employee employee;
    
    @Column(name = "absence_date", nullable = false)
    private LocalDate absenceDate;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "absence_type", nullable = false)
    private AbsenceType absenceType;
    
    public enum AbsenceType { P, A, V }
    public enum AbsenceStatus { PENDING, APPROVED, REJECTED }
}
```

---

## 🤖 AI Integration

### 🧠 Gemini Function Calling Setup
```java
@Service
public class GeminiAPIService {
    
    // Function definitions for Gemini
    private final String FUNCTION_DEFINITIONS = """
    {
      "function_declarations": [
        {
          "name": "markAbsence",
          "description": "Mark employee attendance status for specific dates",
          "parameters": {
            "type": "object",
            "properties": {
              "employeeName": {
                "type": "string",
                "description": "Name of the employee"
              },
              "dates": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Dates in YYYY-MM-DD format"
              },
              "status": {
                "type": "string",
                "enum": ["P", "A", "V"],
                "description": "P=Present, A=Absent, V=Vacation"
              }
            },
            "required": ["employeeName", "dates", "status"]
          }
        }
      ]
    }
    """;
    
    public Mono<GeminiResponse> generateResponse(String message, 
                                               ConversationContext context, 
                                               List<Employee> employees) {
        // Build context with employee list
        String employeeContext = buildEmployeeContext(employees);
        String conversationHistory = buildConversationHistory(context);
        
        // Create request with function calling
        GeminiRequest request = GeminiRequest.builder()
            .contents(List.of(
                GeminiContent.builder()
                    .parts(List.of(
                        GeminiPart.text(SYSTEM_PROMPT + employeeContext + conversationHistory),
                        GeminiPart.text("User: " + message)
                    ))
                    .build()
            ))
            .tools(List.of(
                GeminiTool.builder()
                    .functionDeclarations(parseFunctionDeclarations(FUNCTION_DEFINITIONS))
                    .build()
            ))
            .build();
        
        // Call Gemini API
        return webClient.post()
            .uri(GEMINI_API_URL)
            .header("x-goog-api-key", apiKey)
            .bodyValue(request)
            .retrieve()
            .bodyToMono(GeminiResponse.class);
    }
}
```

### 🎯 Function Call Processing
```java
// In AIService.java
private Mono<ChatResponseDTO> processGeminiResponse(GeminiResponse geminiResponse, 
                                                   ConversationContext context, 
                                                   List<Employee> employees) {
    if (geminiResponse.getCandidates().isEmpty()) {
        return Mono.just(ChatResponseDTO.error("No response from AI", context.getConversationId()));
    }
    
    GeminiCandidate candidate = geminiResponse.getCandidates().get(0);
    GeminiContent content = candidate.getContent();
    
    // Check for function calls
    for (GeminiPart part : content.getParts()) {
        if (part.getFunctionCall() != null) {
            GeminiFunctionCall functionCall = part.getFunctionCall();
            String functionName = functionCall.getName();
            JsonNode functionArgs = functionCall.getArgs();
            
            if ("markAbsence".equals(functionName)) {
                return executeAbsenceAction(functionArgs, context, employees);
            } else if ("queryAbsence".equals(functionName)) {
                return executeQueryAction(functionArgs, context, employees);
            }
        }
    }
    
    // Handle regular text response
    return handleTextResponse(content, context);
}
```

---

## ⚡ Function Calling Mechanism

### 🔄 Complete Function Call Flow

#### 1. **User Input Processing**
```
User: "Mark Manju absent today"
    ↓
Frontend: POST /api/ai/chat
    ↓
AIController.chat() → AIService.processUserMessage()
```

#### 2. **Context Building**
```java
// Build employee context for AI
String employeeContext = """
Available employees:
- Manju (ID: 1, Department: Engineering)
- Shreyas (ID: 2, Department: Marketing)
- Ganesh (ID: 3, Department: Sales)

Current date: 2025-08-26
""";

// Add conversation history
String conversationHistory = context.getMessages().stream()
    .map(msg -> msg.getRole() + ": " + msg.getContent())
    .collect(Collectors.joining("\n"));
```

#### 3. **Gemini API Call with Functions**
```json
{
  "contents": [{
    "parts": [{
      "text": "System: You are an AI assistant for absence management...\nUser: Mark Manju absent today"
    }]
  }],
  "tools": [{
    "function_declarations": [{
      "name": "markAbsence",
      "description": "Mark employee attendance status",
      "parameters": {
        "type": "object",
        "properties": {
          "employeeName": {"type": "string"},
          "dates": {"type": "array", "items": {"type": "string"}},
          "status": {"type": "string", "enum": ["P", "A", "V"]}
        }
      }
    }]
  }]
}
```

#### 4. **Gemini Response with Function Call**
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
    }
  }]
}
```

#### 5. **Function Execution**
```java
// Extract function parameters
String employeeName = functionArgs.get("employeeName").asText(); // "Manju"
String status = functionArgs.get("status").asText(); // "A"
List<LocalDate> dates = parseDates(functionArgs.get("dates")); // [2025-08-26]

// Find employee
Employee employee = employees.stream()
    .filter(emp -> emp.getName().equalsIgnoreCase(employeeName))
    .findFirst()
    .orElseThrow(() -> new EmployeeNotFoundException(employeeName));

// Execute business logic
absenceService.markAbsenceFromAI(employee.getId(), dates, status, "Marked by AI Assistant");
```

#### 6. **Database Transaction**
```java
@Transactional
public void markAbsenceFromAI(Long employeeId, List<LocalDate> dates, String status, String reason) {
    for (LocalDate date : dates) {
        // Find existing record
        Optional<AbsenceRecord> existing = absenceRecordRepository
            .findByEmployeeIdAndAbsenceDate(employeeId, date);
        
        if ("P".equals(status)) {
            // Present = delete absence record
            existing.ifPresent(absenceRecordRepository::delete);
        } else {
            // Create/update absence record
            AbsenceRecord record = existing.orElse(new AbsenceRecord());
            record.setEmployee(employeeRepository.findById(employeeId).get());
            record.setAbsenceDate(date);
            record.setAbsenceType(AbsenceRecord.AbsenceType.valueOf(status));
            record.setReason(reason);
            record.setStatus(AbsenceRecord.AbsenceStatus.APPROVED);
            
            absenceRecordRepository.save(record); // SQL INSERT/UPDATE
        }
    }
} // Transaction commits here
```

#### 7. **Response Generation**
```java
// Create success response
ChatResponseDTO response = ChatResponseDTO.success(
    "✅ Got it! I've marked Manju as absent for August 26, 2025.",
    "markAbsence",
    Map.of(
        "employeeName", "Manju",
        "employeeId", 1L,
        "dates", List.of("2025-08-26"),
        "status", "A"
    ),
    conversationId
);

return ResponseEntity.ok(response);
```

#### 8. **Frontend Processing**
```javascript
// Chatbot receives response
const response = await api.post('/api/ai/chat', { message, conversationId });

if (response.success && response.actionType === 'markAbsence') {
    // Add to action bus for UI update
    executeCommand({
        action: 'markAbsence',
        args: response.actionData
    });
    
    // Show success message
    addMessage({
        text: response.response,
        sender: 'assistant',
        timestamp: new Date().toISOString()
    });
}
```

#### 9. **UI Update via Action Bus**
```javascript
// ActionBusHandler processes the command
useEffect(() => {
    if (pendingCommand?.action === 'markAbsence') {
        const { employeeId, dates, status } = pendingCommand.args;
        
        // Update grid cells immediately
        dates.forEach(date => {
            const cellKey = `${employeeId}-${date}`;
            handleStatusChange(cellKey, status, employeeId, date);
        });
        
        // Auto-save to ensure persistence
        setTimeout(() => handleSaveChanges(), 100);
        
        clearCommand();
    }
}, [pendingCommand]);
```

---

## 🧪 Complete Code Flow Examples

### Example 1: AI Absence Marking
```
INPUT: "Mark Manju absent today"
OUTPUT: Database record + UI update + Success message
```

**Step-by-step trace:**
1. **Frontend**: `Chatbot.jsx` → `handleSubmit()` → `POST /api/ai/chat`
2. **Backend**: `AIController.chat()` → `AIService.processUserMessage()`
3. **AI**: `GeminiAPIService.generateResponse()` → Function call returned
4. **Processing**: `AIService.executeAbsenceAction()` → `AbsenceService.markAbsenceFromAI()`
5. **Database**: `AbsenceRecordRepository.save()` → SQLite INSERT
6. **Response**: Success JSON returned to frontend
7. **UI Update**: `ActionBusHandler` → `AbsencesPage` → Grid cell updated
8. **Persistence**: Auto-save via `grid_memory.js` → `PUT /api/absences/bulk-update`

### Example 2: Manual Grid Update
```
INPUT: User clicks cell (Shreyas, Aug 27) → Changes P to A
OUTPUT: Database record + UI update
```

**Step-by-step trace:**
1. **Frontend**: `OneDayCell.jsx` → `handleCellClick()` → `onStatusChange()`
2. **State**: `AbsencesPage.jsx` → `handleStatusChange()` → Updates `absenceData`
3. **Changes**: Added to `recentChanges` array
4. **Save**: User clicks "Save Changes" → `grid_memory.js` → `handleSaveChanges()`
5. **API**: `PUT /api/absences/bulk-update` with changes array
6. **Backend**: `AbsenceController.bulkUpdate()` → `AbsenceService.bulkUpdateAbsences()`
7. **Database**: `AbsenceRecordRepository.save()` → SQLite INSERT/UPDATE
8. **UI**: Changes cleared, success notification shown

### Example 3: Data Loading
```
INPUT: Page load or refresh
OUTPUT: Grid populated with current absence data
```

**Step-by-step trace:**
1. **Frontend**: `AbsencesPage.jsx` → `useEffect()` → `loadAbsenceData()`
2. **API**: `GET /api/employees` → Returns employees with nested absence records
3. **Backend**: `EmployeeController.getAllEmployees()` → `EmployeeService.getAllEmployees()`
4. **Database**: `EmployeeRepository.findAll()` → SQLite SELECT with JOIN
5. **Processing**: `grid_memory.js` converts records to grid format `{employeeId-date: status}`
6. **UI**: `GridTable.jsx` → `OneEmployeeRow.jsx` → `OneDayCell.jsx` renders cells
7. **Display**: Each cell shows P/A/V based on `absenceData[cellKey]`

---

## ✅ Testing & Verification

### 🧪 Test Scenarios

#### 1. **End-to-End AI Test**
```bash
# Test AI absence marking
curl -X POST http://localhost:8080/api/ai/chat \
-H "Content-Type: application/json" \
-d '{"message": "Mark John absent today", "conversationId": "test123"}'

# Verify database
sqlite3 backend/absence-management/abscent.db \
"SELECT e.name, ar.absence_date, ar.absence_type 
 FROM absence_records ar 
 JOIN employees e ON ar.employee_id = e.id 
 WHERE e.name = 'John'"
```

#### 2. **Frontend Integration Test**
```javascript
// Test grid save functionality
const testChanges = [
    {
        employeeId: 1,
        absenceDate: "2025-08-26",
        absenceType: "A",
        reason: "Test absence"
    }
];

const response = await api.absences.bulkUpdate(testChanges);
console.log('Save result:', response);
```

#### 3. **Database Consistency Test**
```sql
-- Check data integrity
SELECT 
    e.name,
    COUNT(ar.id) as absence_count,
    ar.absence_type,
    ar.absence_date
FROM employees e
LEFT JOIN absence_records ar ON e.id = ar.employee_id
GROUP BY e.id, ar.absence_type
ORDER BY e.name;
```

### 🔍 Debugging Tools

#### 1. **Backend Logs**
```java
// Enable debug logging in application.properties
logging.level.com.companyname.absence_management=DEBUG
logging.level.org.springframework.web=DEBUG
logging.level.org.hibernate.SQL=DEBUG
```

#### 2. **Frontend Console**
```javascript
// Enable API request logging
console.log('🌐 API Request:', method, url, data);
console.log('✅ API Success:', response);
console.log('❌ API Error:', error);
```

#### 3. **Database Monitoring**
```bash
# Watch database changes in real-time
watch -n 1 'sqlite3 backend/absence-management/abscent.db "SELECT COUNT(*) FROM absence_records"'
```

---

## 🎯 Summary

This system demonstrates a complete **AI-powered absence management** solution with:

### ✨ **Key Features:**
- **🤖 Natural Language Processing**: "Mark Manju absent today" → Database update
- **⚡ Real-time UI Updates**: Changes reflect immediately in grid
- **💾 Persistent Storage**: All actions saved to SQLite database
- **🔄 Bidirectional Sync**: AI actions ↔ Manual grid changes
- **📱 Responsive Interface**: Click cells to cycle P → A → V
- **🚌 Action Bus Pattern**: Decoupled AI commands from UI updates

### 🏗️ **Architecture Highlights:**
- **Frontend**: React with hooks-based state management
- **Backend**: Spring Boot with JPA/Hibernate
- **Database**: SQLite with proper indexing
- **AI**: Gemini with function calling
- **Integration**: RESTful APIs with JSON payloads

### 🔗 **Data Flow:**
1. **User Input** → Frontend captures
2. **API Call** → Backend processes
3. **AI Processing** → Gemini function calling
4. **Business Logic** → Service layer execution
5. **Database Update** → JPA transaction
6. **Response** → Success/error handling
7. **UI Update** → Real-time grid refresh
8. **Persistence** → Auto-save mechanism


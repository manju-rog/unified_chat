# 🔢 Numbered Flow Diagram: "Mark Manju absent on August 16th"

```
User Input: "Mark Manju absent on August 16th"
↓

┌─────────────────────────────────────────────────────────────┐
│ FRONTEND (React)                                            │
│ ┌─────────────────┐                                         │
│ │ 1. Chatbot.jsx  │ → Captures user input                   │
│ │ - handleSubmit  │ → Sends to backend                      │
│ └─────────────────┘                                         │
└─────────────────────────────────────────────────────────────┘
↓ POST /api/ai/chat

┌─────────────────────────────────────────────────────────────┐
│ BACKEND (Spring Boot)                                       │
│ ┌─────────────────┐   ┌─────────────────┐   ┌─────────────┐ │
│ │ 2. AIController │ → │ 3. AIService    │ → │ 4. GeminiAPI│ │
│ │ - chat()        │   │ - processChat() │   │ Service     │ │
│ │                 │   │                 │   │ - callGem() │ │
│ └─────────────────┘   └─────────────────┘   └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
↓ Function Call: markAbsence

┌─────────────────────────────────────────────────────────────┐
│ AI SERVICE (Gemini)                                         │
│ ┌─────────────────┐                                         │
│ │ 5. Function Call│ → Parses: employeeName="Manju"         │
│ │ - markAbsence   │          dates=["2025-08-16"]          │
│ │                 │          status="A"                    │
│ └─────────────────┘                                         │
└─────────────────────────────────────────────────────────────┘
↓ Returns structured data

┌─────────────────────────────────────────────────────────────┐
│ BACKEND (Spring Boot)                                       │
│ ┌─────────────────┐   ┌─────────────────┐                   │
│ │ 6. AIService    │ → │ 7. AbsenceServ  │                   │
│ │ - executeAction │   │ - markAbsence   │                   │
│ │                 │   │   FromAI()      │                   │
│ └─────────────────┘   └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
↓ @Transactional

┌─────────────────────────────────────────────────────────────┐
│ DATABASE (SQLite)                                           │
│ ┌─────────────────┐   ┌─────────────────┐                   │
│ │ 8. AbsenceRec   │ ← │ 9. Employee     │                   │
│ │ Repository      │   │ Repository      │                   │
│ │ - save()        │   │ - findById()    │                   │
│ └─────────────────┘   └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
↓ Success response

┌─────────────────────────────────────────────────────────────┐
│ FRONTEND (React)                                            │
│ ┌─────────────────┐   ┌─────────────────┐                   │
│ │ 10. ActionBus   │ → │ 11. AbsencePage │                   │
│ │ Handler         │   │ - updateGrid()  │                   │
│ │ - refreshData() │   │                 │                   │
│ └─────────────────┘   └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Component Numbering Reference

**Frontend Components:**
1. Chatbot.jsx - handleSubmit
10. ActionBusHandler - refreshData()  
11. AbsencesPage - updateGrid()

**Backend Components:**
2. AIController - chat()
3. AIService - processChat()
4. GeminiAPIService - callGemini()
6. AIService - executeAction
7. AbsenceService - markAbsenceFromAI()

**AI Service:**
5. Function Call - markAbsence

**Database Components:**
8. AbsenceRecordRepository - save()
9. EmployeeRepository - findById()

---

## 📋 Quick Reference Map

| Number | Component | Function | Layer |
|--------|-----------|----------|-------|
| 1 | Chatbot.jsx | handleSubmit | Frontend |
| 2 | AIController | chat() | Backend |
| 3 | AIService | processChat() | Backend |
| 4 | GeminiAPIService | callGemini() | Backend |
| 5 | Gemini AI | markAbsence | External |
| 6 | AIService | executeAction | Backend |
| 7 | AbsenceService | markAbsenceFromAI() | Backend |
| 8 | AbsenceRecordRepository | save() | Database |
| 9 | EmployeeRepository | findById() | Database |
| 10 | ActionBusHandler | refreshData() | Frontend |
| 11 | AbsencesPage | updateGrid() | Frontend |
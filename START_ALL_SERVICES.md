# Complete System Startup Guide

## 🚀 Start All Services Separately

### 1. Absence Management Service (Port 8010)
```bash
cd ai_absence-ai_absence_mi/backend/absence-management
./mvnw spring-boot:run
```
**Status:** ✅ Available at http://localhost:8010

### 2. use_sow Backend (Port 8002)
```bash
cd use_sow
python run_backend_8002.py
```
**Status:** 🔄 Available at http://localhost:8002

### 3. use_sow Frontend (Port 8003) - Optional
```bash
cd use_sow
python run_frontend_8003.py
```
**Status:** 🔄 Available at http://localhost:8003

### 4. Unified AI Chat Backend (Port 8001)
```bash
cd unified_ai_chat/backend
python run_server.py
```
**Status:** ✅ Available at http://localhost:8001

### 5. Unified AI Chat Frontend (Port 3000)
```bash
cd unified_ai_chat/frontend
npm start
```
**Status:** ✅ Available at http://localhost:3000

## 🎯 Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Complete System Architecture                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │ Unified Chat UI │    │   use_sow UI    │    │ Absence Mgmt│ │
│  │   Port 3000     │    │   Port 8003     │    │  Port 8010  │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
│           │                       │                     │       │
│  ┌─────────────────┐    ┌─────────────────┐             │       │
│  │ Unified Chat    │    │   use_sow       │             │       │
│  │ Backend         │────│   Backend       │─────────────┘       │
│  │   Port 8001     │    │   Port 8002     │                     │
│  └─────────────────┘    └─────────────────┘                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🔗 Integration Flow

1. **User interacts with Unified Chat UI** (Port 3000)
2. **Unified Chat Backend** (Port 8001) handles conversation
3. **For SOW generation:** Calls use_sow Backend (Port 8002)
4. **For absence management:** Calls Absence Service (Port 8010)
5. **Documents generated** by use_sow with full Gemini AI processing
6. **Results delivered** through Unified Chat interface

## ✅ Verification

After starting all services, verify:

- [ ] Absence Management: http://localhost:8010/api/ai/employees
- [ ] use_sow Backend: http://localhost:8002/
- [ ] use_sow Frontend: http://localhost:8003/ (optional)
- [ ] Unified Chat Backend: http://localhost:8001/api/chat
- [ ] Unified Chat Frontend: http://localhost:3000/

## 🎯 Benefits

- **Separate Concerns:** Each service runs independently
- **Easy Debugging:** Can test each service separately
- **Scalable:** Services can be deployed on different servers
- **Maintainable:** Clear separation of responsibilities
- **Proven Quality:** use_sow generates documents with full AI processing
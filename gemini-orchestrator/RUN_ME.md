# 🎯 RUN THE GEMINI ORCHESTRATOR

## ⚡ Quick Commands

### Open Terminal 1 and run:
```bash
cd ~/Desktop/project/gemini-orchestrator/backend
uvicorn app.main:app --reload --port 8000
```

### Open Terminal 2 and run:
```bash
cd ~/Desktop/project/gemini-orchestrator/frontend
npm run dev
```

### Open Browser:
```
http://localhost:3000
```

---

## ✅ What You Should See

### Terminal 1 (Backend):
```
INFO:     Will watch for changes in these directories: ['/Users/manju/Desktop/project/gemini-orchestrator/backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Terminal 2 (Frontend):
```
  ▲ Next.js 14.x.x
  - Local:        http://localhost:3000
  - Environments: .env.local

 ✓ Ready in 2.3s
```

### Browser:
- Clean chat interface
- "Gemini Orchestrator" header
- Mode indicator showing "IDLE"
- Message input box at bottom
- Welcome message with capabilities

---

## 🎮 Try These Commands

### 1. Absence Management
```
mark manju absent today because of sick leave
```

### 2. Check Status
```
is john absent today?
```

### 3. SOW Generation
```
generate sow for Predictive Maintenance System
```
(Then answer the questions it asks)

### 4. Out of Scope
```
what's the weather?
```
(Should politely refuse)

---

## 🛑 To Stop

Press `Ctrl+C` in both terminal windows

---

## 📚 More Info

- **Full Demo Guide**: See `DEMO_GUIDE.md`
- **Startup Guide**: See `START_HERE.md`
- **Integration Report**: See `INTEGRATION_COMPLETE.md`
- **API Docs**: http://localhost:8000/docs (after starting backend)

---

## 🎉 That's It!

The system is fully integrated and ready to use. Enjoy! 🚀

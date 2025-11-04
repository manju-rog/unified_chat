# 🚀 Unified AI Chat System - README FIRST

## Welcome!

You've received the **Unified AI Chat System** - an integrated platform for absence management and SOW (Statement of Work) document generation powered by Google Gemini AI.

---

## ⚡ Quick Start (5 Minutes)

### 1. Extract the Package
```bash
unzip unified-ai-chat-system.zip
cd unified-ai-chat-system
```

### 2. Get Your Gemini API Key
1. Visit: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIzaSy...`)

### 3. Configure API Keys
```bash
# Edit these files and add your API key:
nano new_sow/.env
nano unified_ai_chat/backend/.env

# Replace YOUR_API_KEY_HERE with your actual key
```

### 4. Run Installation Script
```bash
chmod +x fresh_install.sh
./fresh_install.sh
```

### 5. Start All Services
```bash
cd unified_ai_chat
./start_all_different_ports.sh
```

### 6. Open Application
Open your browser to: **http://localhost:3001**

---

## 📚 Documentation

This package includes comprehensive documentation:

1. **README_FIRST.md** (this file) - Quick start guide
2. **DEPLOYMENT_PACKAGE_GUIDE.md** - Detailed installation and troubleshooting
3. **COMPLETE_SETUP_AND_TROUBLESHOOTING_GUIDE.md** - Complete system documentation

**Read these files in order if you encounter any issues.**

---

## 🎯 What This System Does

### Absence Management
- Mark employees as absent, present, or on vacation
- Query absences by date, date range, or month
- Check employee status
- Natural language interface: "Mark John absent today"

### SOW Generation
- Create professional Statement of Work documents
- 7-step wizard: Project info, Services, Deliverables, Timeline, Resources, Contacts, Budget
- AI-powered data extraction and document generation
- Download as Word (.docx) format

---

## 🔧 System Requirements

### Software Prerequisites
- **Java 11+** (for Absence Management service)
- **Python 3.8+** (for backend services)
- **Node.js 14+** (for frontend)
- **npm** (comes with Node.js)

### Hardware Requirements
- **RAM:** 4GB minimum, 8GB recommended
- **Disk Space:** 2GB for installation
- **Network:** Internet connection for Gemini API calls

### Operating Systems
- ✅ macOS (tested on macOS 10.15+)
- ✅ Linux (tested on Ubuntu 20.04+)
- ✅ Windows 10/11 (with WSL recommended)

---

## 🌐 Service Ports

The system runs 4 services on different ports:

| Service | Port | URL |
|---------|------|-----|
| Absence Management | 8010 | http://localhost:8010 |
| new_sow Backend | 8002 | http://localhost:8002 |
| Unified Chat Backend | 8001 | http://localhost:8001 |
| Frontend (React) | 3001 | http://localhost:3001 |

**Make sure these ports are available before starting.**

---

## ✅ Verification Checklist

After installation, verify:

- [ ] All 4 services are running: `lsof -i :8010,8002,8001,3001`
- [ ] Health endpoints respond:
  - [ ] http://localhost:8010/api/ai/employees
  - [ ] http://localhost:8002/health
  - [ ] http://localhost:8001/api/health
  - [ ] http://localhost:3001
- [ ] Frontend loads in browser
- [ ] You can interact with the chat interface

---

## 🚨 Common Issues

### "Port already in use"
```bash
# Kill processes on the ports
lsof -ti:8010 | xargs kill -9
lsof -ti:8002 | xargs kill -9
lsof -ti:8001 | xargs kill -9
lsof -ti:3001 | xargs kill -9
```

### "GEMINI_API_KEY not found"
```bash
# Verify .env files exist and contain your key
cat new_sow/.env
cat unified_ai_chat/backend/.env
```

### "Module not found" errors
```bash
# Reinstall dependencies
./fresh_install.sh
```

### Services won't start
```bash
# Check logs
tail -f /tmp/*-backend-*.log
```

---

## 📖 Usage Examples

### Example 1: Mark Absence
```
You: Mark John absent today
System: ✅ John has been marked absent for 2025-10-30
```

### Example 2: Query Absences
```
You: Who is absent this week?
System: 📊 Absences this week:
- John (2025-10-30)
- Sarah (2025-10-31)
```

### Example 3: Generate SOW
```
You: I want to create a SOW
System: [Starts 7-step wizard]
1. Project Info
2. Services
3. Deliverables
4. Timeline
5. Resources
6. Contacts
7. Budget
[After completion]
System: ✅ SOW Generated! [Download button]
```

---

## 🛑 Stopping Services

### Using Script
```bash
cd unified_ai_chat
./stop_all_different_ports.sh
```

### Manual Stop
```bash
# Kill all services
killall -9 java python node
```

---

## 📁 Project Structure

```
unified-ai-chat-system/
├── ai_absence-ai_absence_mi/     # Absence Management (Java Spring Boot)
├── new_sow/                       # SOW Generation Backend (Python FastAPI)
├── unified_ai_chat/               # Main Application
│   ├── backend/                   # Orchestrator Backend (Python FastAPI)
│   └── frontend/                  # React Frontend
├── README_FIRST.md                # This file
├── DEPLOYMENT_PACKAGE_GUIDE.md    # Detailed installation guide
├── COMPLETE_SETUP_AND_TROUBLESHOOTING_GUIDE.md  # Full documentation
└── fresh_install.sh               # Automated installation script
```

---

## 🔐 Security Notes

- **API Keys:** Keep your Gemini API keys secure. Don't commit them to version control.
- **Ports:** The system runs on localhost by default. For production, configure proper security.
- **Data:** Generated documents are saved locally. Ensure proper backup procedures.

---

## 🆘 Getting Help

1. **Check Documentation:**
   - Read `DEPLOYMENT_PACKAGE_GUIDE.md` for detailed troubleshooting
   - Read `COMPLETE_SETUP_AND_TROUBLESHOOTING_GUIDE.md` for complete system info

2. **Check Logs:**
   ```bash
   tail -f /tmp/absence-backend-8010.log
   tail -f /tmp/use-sow-backend-8002.log
   tail -f /tmp/unified-backend-8001.log
   tail -f /tmp/unified-frontend-3001.log
   ```

3. **Verify Configuration:**
   - Check API keys in `.env` files
   - Verify ports are not in use
   - Ensure all dependencies are installed

4. **Try Fresh Installation:**
   ```bash
   ./fresh_install.sh
   ```

---

## 🎉 Success!

If you see this in your browser at http://localhost:3001, you're ready to go:

```
╔════════════════════════════════════════╗
║   Unified AI Chat                      ║
║   How can I help you today?            ║
╚════════════════════════════════════════╝
```

Try saying:
- "Mark someone absent"
- "Who is absent today?"
- "I want to create a SOW"

---

## 📞 Support

For issues or questions:
1. Check the documentation files
2. Review the troubleshooting sections
3. Verify all prerequisites are installed
4. Check service logs for errors

---

**Version:** 1.0  
**Last Updated:** October 30, 2025  
**AI Model:** Google Gemini 2.5 Flash  
**License:** [Your License Here]

---

## 🙏 Thank You!

Thank you for using the Unified AI Chat System. We hope it serves you well!

**Happy chatting! 🚀**

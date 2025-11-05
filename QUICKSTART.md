# ⚡ QUICK START GUIDE

Get the Unified AI Chat System running in 5 minutes!

## 🎯 For First-Time Users (Fresh Clone from GitHub)

### Step 1: Clone the Repository

```bash
git clone https://github.com/manju-rog/unified_chat.git
cd unified_chat
```

### Step 2: Get Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your API key (starts with `AIzaSy...`)

### Step 3: Run the Setup Script

```bash
chmod +x setup_and_start.sh
./setup_and_start.sh
```

The script will:
- ✅ Check if you have Java, Python, and Node.js installed
- ✅ Create `.env` files for you
- ✅ Install all dependencies
- ✅ Start all services automatically

### Step 4: Configure API Keys

When prompted, edit these files and add your API key:

**File 1: `new_sow/.env`**
```bash
GEMINI_API_KEY=AIzaSy_your_actual_key_here
GEMINI_MODEL=gemini-1.5-pro
DEBUG=True
```

**File 2: `unified_ai_chat/backend/.env`**
```bash
GEMINI_API_KEY=AIzaSy_your_actual_key_here
NEW_SOW_API_URL=http://localhost:8002
ABSENCE_API_URL=http://localhost:8010
```

### Step 5: Restart Services

```bash
cd unified_ai_chat
./stop_all_different_ports.sh
./start_all_different_ports.sh
```

### Step 6: Open the Application

```
http://localhost:3001
```

---

## 🔄 For Returning Users

### Start All Services

```bash
cd unified_ai_chat
./start_all_different_ports.sh
```

### Stop All Services

```bash
cd unified_ai_chat
./stop_all_different_ports.sh
```

---

## 🎮 Try These Commands

Once the application is running, try:

### SOW Generation
- "I want to create a SOW"
- "Create statement of work"
- "Generate SOW document"

### Absence Management
- "Who is absent today?"
- "Show me absences"
- "Mark John as absent"

### General Chat
- "Hello"
- "What can you do?"
- "Help me"

---

## 🚨 Common Issues

### Issue: "Port already in use"

**Solution:**
```bash
# Find what's using the port
lsof -i :3001  # or :8001, :8002, :8010

# Kill it
kill -9 <PID>
```

### Issue: "Java not found"

**Solution (macOS):**
```bash
brew install openjdk@11
```

**Solution (Ubuntu):**
```bash
sudo apt install openjdk-11-jdk
```

### Issue: "Python not found"

**Solution (macOS):**
```bash
brew install python@3.11
```

**Solution (Ubuntu):**
```bash
sudo apt install python3 python3-pip
```

### Issue: "Node not found"

**Solution (macOS):**
```bash
brew install node
```

**Solution (Ubuntu):**
```bash
sudo apt install nodejs npm
```

### Issue: "API key not working"

**Checklist:**
- ✅ Key starts with `AIzaSy`
- ✅ Key is in both `.env` files
- ✅ No extra spaces or quotes around the key
- ✅ Gemini API is enabled in Google Cloud Console

---

## 📊 Service Status Check

### Check if services are running:

```bash
# Check ports
lsof -i :3001  # Frontend
lsof -i :8001  # Unified Backend
lsof -i :8002  # new_sow
lsof -i :8010  # Absence Management

# Test endpoints
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8010/api/health
```

### View logs:

```bash
# Unified backend logs
tail -f unified_ai_chat/backend/logs/app.log

# new_sow logs
tail -f new_sow/logs/app.log

# Frontend console
# Open browser DevTools → Console tab
```

---

## 🎯 What Each Service Does

| Service | Port | Purpose |
|---------|------|---------|
| **Frontend** | 3001 | User interface (React) |
| **Unified Backend** | 8001 | Main orchestrator, routes requests |
| **new_sow** | 8002 | Generates SOW documents |
| **Absence Management** | 8010 | Tracks employee absences |

---

## 📚 Need More Help?

- [Complete Setup Guide](COMPLETE_SETUP_AND_TROUBLESHOOTING_GUIDE.md)
- [SOW Integration Guide](SOW_INTEGRATION_COMPLETE_GUIDE.md)
- [Full README](README.md)

---

## 🎉 You're All Set!

Open http://localhost:3001 and start chatting!

Try: "I want to create a SOW" or "Who is absent today?"


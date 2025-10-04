# 🚀 Quick Start Guide - Unified AI Chat

Get up and running in 5 minutes!

## Step 1: Prerequisites Check ✅

Make sure you have:
- [ ] Python 3.8+ installed
- [ ] Node.js 14+ installed
- [ ] Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- [ ] Absence Management backend running on port 8080

## Step 2: Start Absence Management Backend 🏃

```bash
# Terminal 1
cd ai_absence-ai_absence_mi/backend/absence-management
./mvnw spring-boot:run
```

Wait for: `Started AbsenceManagementApplication`

## Step 3: Setup Unified Chat Backend 🔧

```bash
# Terminal 2
cd unified_ai_chat/backend

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your Gemini API key
nano .env  # or use your favorite editor
```

Add your API key:
```
GEMINI_API_KEY=your-actual-api-key-here
```

## Step 4: Start Unified Chat Backend 🚀

```bash
# Still in Terminal 2
python unified_chat_server.py
```

You should see:
```
🚀 Unified AI Chat Server starting...
📍 Absence API: http://localhost:8080/api
📍 SOW Generator: ../../sow_gen_ai
🤖 Gemini AI: Configured
 * Running on http://0.0.0.0:5002
```

## Step 5: Setup Frontend 🎨

```bash
# Terminal 3
cd unified_ai_chat/frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env
```

## Step 6: Start Frontend 🌐

```bash
# Still in Terminal 3
npm start
```

Browser will open automatically at `http://localhost:3000`

## Step 7: Test It! 🎉

Try these commands in the chat:

### Test Absence Management:
```
Mark Manju absent today
```

### Test SOW Generation:
```
I need to create a SOW document
```

### Test Query:
```
Who was absent yesterday?
```

## Troubleshooting 🔧

### Backend won't start?
```bash
# Check if port is in use
lsof -i :5002

# Kill process if needed
kill -9 <PID>
```

### Frontend won't connect?
```bash
# Test backend health
curl http://localhost:5002/api/health
```

### Absence API not working?
```bash
# Test Spring Boot
curl http://localhost:8080/api/employees
```

## What's Running? 📊

After setup, you should have:

| Service | Port | URL |
|---------|------|-----|
| Absence Backend | 8080 | http://localhost:8080 |
| Unified Backend | 5002 | http://localhost:5002 |
| React Frontend | 3000 | http://localhost:3000 |

## Next Steps 📚

- Read the full [README.md](README.md) for detailed documentation
- Explore the [Architecture](#) section
- Try different conversation flows
- Customize the UI in `UnifiedChat.css`

## Need Help? 🆘

Check the logs:
- **Backend logs**: Terminal 2 output
- **Frontend logs**: Browser console (F12)
- **Spring Boot logs**: Terminal 1 output

---

**You're all set! Start chatting with your AI assistant! 🎉**

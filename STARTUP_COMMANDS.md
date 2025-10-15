# 🚀 **Complete Startup Commands for Enhanced SOW System**

## **NEW PORTS CONFIGURATION:**
- **Backend**: Port 8001 (changed from 8000)
- **Frontend**: Port 3001 (changed from 3000)

## **Step 1: Kill All Existing Processes**

```bash
# Kill all Python/Node processes
pkill -f "python.*run_server.py" || true
pkill -f "npm start" || true  
pkill -f "uvicorn" || true
pkill -f "node.*react-scripts" || true

# Kill processes on all possible ports
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:3001 | xargs kill -9 2>/dev/null || true
lsof -ti:5002 | xargs kill -9 2>/dev/null || true

# Wait for processes to terminate
sleep 3
```

## **Step 2: Start Backend (Terminal 1)**

```bash
# Navigate to backend directory
cd unified_ai_chat/backend

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server on port 8001
python run_server.py
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## **Step 3: Start Frontend (Terminal 2 - New Terminal)**

```bash
# Navigate to frontend directory
cd unified_ai_chat/frontend

# Install dependencies (if needed)
npm install

# Start React development server on port 3001
npm start
```

**Expected Output:**
```
Compiled successfully!

You can now view unified-ai-chat in the browser.

  Local:            http://localhost:3001
  On Your Network:  http://192.168.x.x:3001
```

## **Step 4: Verify Everything is Working**

### **Test Backend API:**
```bash
curl http://localhost:8001/api/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "time": "2024-10-14T12:47:18.123456",
  "absence_api": "http://localhost:8080/api",
  "sow_template": "../../sow_gen_ai"
}
```

### **Test Gemini API Integration:**
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent" \
-H 'Content-Type: application/json' \
-H 'X-goog-api-key: AIzaSyD_mxuXtvtnK5d3d9LaWT__1fG0a8shppE' \
-X POST \
-d '{"contents": [{"parts": [{"text": "Generate a brief SOW summary"}]}]}'
```

## **Step 5: Access the Application**

- **Frontend**: http://localhost:3001 ⭐ (NEW PORT)
- **Backend API**: http://localhost:8001 ⭐ (NEW PORT)
- **API Documentation**: http://localhost:8001/docs ⭐ (NEW PORT)

## **Step 6: Test the Enhanced SOW System**

1. **Open Browser**: Go to http://localhost:3000
2. **Start SOW**: Click "Create a SOW" button
3. **Follow Enhanced Flow**:
   - **Project Info**: Type project description
   - **Services**: Click "📦 Standard Package" or "🛠️ Custom Services"
   - **Deliverables**: Type deliverables
   - **Timeline**: Type timeline
   - **Resources**: Use +/- buttons for roles (Developer, DevOps, Tester, Quality Analyst, BA, Project Manager)
   - **Contacts**: Select from dropdown (MUFG Bank auto-fills details)
   - **Budget**: Type budget
   - **Generate**: Click "📄 Generate SOW Document"

## **🎯 Key Features to Test**

✅ **Service Selection Buttons** - Beautiful in-chat buttons
✅ **Resource Builder** - Interactive +/- controls for 6 roles
✅ **MUFG Bank Contact** - Dropdown with auto-fill functionality
✅ **Gemini AI Integration** - Real AI-generated SOW content
✅ **Document Download** - Professional DOCX generation

## **🛑 To Stop All Services**

```bash
# Kill backend
pkill -f "python.*run_server.py"

# Kill frontend  
pkill -f "npm start"

# Or use Ctrl+C in each terminal
```

## **🔧 Environment Variables**

The system is configured with:
- **GEMINI_API_KEY**: `AIzaSyD_mxuXtvtnK5d3d9LaWT__1fG0a8shppE`
- **Backend Port**: 8000
- **Frontend Port**: 3000

## **🧪 Quick Test Commands**

```bash
# Test enhanced SOW system
python test_enhanced_sow_ui.py

# Test basic integration
python test_sow_integration.py
```

## **🎉 You're Ready!**

The enhanced SOW system is now running with:
- Real Gemini AI integration
- Beautiful in-chat UI elements
- MUFG Bank contact with auto-fill
- Professional document generation
- Interactive resource builder

**Start with the commands above and enjoy the enhanced SOW experience!**
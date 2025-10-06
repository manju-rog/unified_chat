# 🤖 AI Absence and SOW System

A sophisticated AI-powered platform with **color-coded workflows** for **Employee Absence Management** and **Statement of Work (SOW) Generation**, featuring an elegant monochrome glassmorphism design.

![Status](https://img.shields.io/badge/status-production--ready-green)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![React](https://img.shields.io/badge/react-18.2-blue)
![Gemini](https://img.shields.io/badge/gemini-2.0--flash-purple)

## ✨ Features

### 🎯 Conversational AI
- **Context-aware conversations** - Remembers previous messages
- **Smart name matching** - Handles typos and partial names
- **Disambiguation UI** - Beautiful buttons when multiple employees match
- **Yes/no responses** - Natural follow-up conversations

### 📊 Absence Management
- Mark employees as absent/present/vacation
- Query absence records by date, range, or month
- View detailed reports with dates and names
- Real-time database integration

### 📄 SOW Generation
- 8-step guided workflow
- Professional DOCX document generation
- Template-based formatting
- Downloadable documents

## 🏗️ Architecture

```
┌─────────────────┐
│  React Frontend │ (Port 3000)
│   Beautiful UI  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ FastAPI Backend │ (Port 8000)
│ Gemini 2.0 AI   │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│ Spring │ │  SOW   │
│  Boot  │ │ Engine │
│ (8080) │ │        │
└────────┘ └────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Java 17+ (for Spring Boot)
- Google Gemini API Key

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd project
```

### 2. Set Up Environment Variables
```bash
# Create .env file in sow_gen_ai/
echo "GEMINI_API_KEY=your_api_key_here" > sow_gen_ai/.env

# Create .env file in unified_ai_chat/frontend/
echo "REACT_APP_API_URL=http://localhost:8000/api" > unified_ai_chat/frontend/.env
```

### 3. Install Dependencies

**Backend:**
```bash
cd unified_ai_chat/backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd unified_ai_chat/frontend
npm install
```

### 4. Start All Services

**Option A: Manual Start**
```bash
# Terminal 1: Spring Boot
cd ai_absence-ai_absence_mi/backend/absence-management
./mvnw spring-boot:run

# Terminal 2: FastAPI
cd unified_ai_chat/backend
uvicorn app.main:app --port 8000

# Terminal 3: React
cd unified_ai_chat/frontend
npm start
```

**Option B: Background Start**
```bash
chmod +x start_all_services.sh
./start_all_services.sh
```

### 5. Access the Application
- **Frontend UI**: http://localhost:3000
- **FastAPI Docs**: http://localhost:8000/docs
- **Spring Boot API**: http://localhost:8080

## 📖 Usage Examples

### Absence Management
```
You: "Who is absent today?"
AI: "📅 Absence Report for 2025-10-04:
     🚫 Absent: Manju - No reason provided"

You: "Mark gansh absent today"
AI: "Did you mean Ganesh?"
You: "yes"
AI: "✅ Marked Ganesh as absent for 2025-10-04"

You: "Show me September absences"
AI: "📊 Absence Report: 2025-09-01 to 2025-09-30
     📅 2025-09-08:
       🚫 Absent: Manju
       🏖️ Vacation: Ganesh
     ..."
```

### SOW Generation
```
You: "Create a SOW for mobile app development"
AI: "Let's create your SOW. What services will be provided?"
You: "iOS and Android development, API integration"
AI: "Great! What are the key deliverables?"
... (8-step workflow)
AI: "✅ Your SOW is ready! [Download Button]"
```

## 🎨 Key Features Explained

### 1. Conversational Context
The system remembers your conversation:
- Handles "yes/no" responses
- Maintains context across messages
- Smart clarification requests

### 2. Disambiguation Buttons
When multiple employees match:
```
AI: "I found 3 employees matching 'suhas'. Please select one:"
   [Button: Suhas TS (Development)]
   [Button: Suhas B (QA)]
   [Button: Suhas P (Management)]
```
Click any button to proceed!

### 3. Smart Date Handling
- "today" → Current date
- "yesterday" → Previous day
- "september" → September 2025
- "this week" → Current week range

### 4. Beautiful UI
- Gradient buttons with animations
- Real-time typing indicators
- Message history
- Download buttons for documents

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Google Gemini 2.0 Flash** - AI model
- **Spring Boot** - Absence management service
- **SQLite** - Database
- **Python-docx** - Document generation

### Frontend
- **React 18** - UI framework
- **CSS3** - Styling with gradients & animations
- **Material Icons** - Icon library

## 📁 Project Structure

```
project/
├── unified_ai_chat/           # Main orchestrator
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py       # FastAPI app
│   │   │   ├── gemini_client.py
│   │   │   ├── models/
│   │   │   └── services/
│   │   └── requirements.txt
│   └── frontend/
│       ├── src/
│       │   ├── UnifiedChat.jsx
│       │   └── UnifiedChat.css
│       └── package.json
├── ai_absence-ai_absence_mi/  # Spring Boot service
│   └── backend/absence-management/
├── sow_gen_ai/                # SOW generation
│   ├── .env                   # API keys here!
│   └── G-COP SOW v1.0_CLEAN.docx
└── README.md
```

## 🔧 Configuration

### Environment Variables

**sow_gen_ai/.env:**
```env
GEMINI_API_KEY=your_gemini_api_key
```

**unified_ai_chat/frontend/.env:**
```env
REACT_APP_API_URL=http://localhost:8000/api
```

### Backend Settings
Edit `unified_ai_chat/backend/app/config.py`:
- `gemini_model`: AI model name
- `absence_api_base`: Spring Boot URL
- `session_expiry_minutes`: Session timeout

## 🧪 Testing

### Manual Testing
```bash
# Test absence query
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test1", "message": "who is absent today?"}'

# Test with typo
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test2", "message": "mark gansh absent today"}'
```

### Run Test Script
```bash
chmod +x test_improvements.sh
./test_improvements.sh
```

## 📚 Documentation

- **[IMPROVEMENTS_APPLIED.md](IMPROVEMENTS_APPLIED.md)** - Recent improvements
- **[CONVERSATIONAL_CONTEXT_FEATURES.md](CONVERSATIONAL_CONTEXT_FEATURES.md)** - Context features
- **[SYSTEM_RUNNING.md](SYSTEM_RUNNING.md)** - Deployment guide
- **[unified_ai_chat/ARCHITECTURE.md](unified_ai_chat/ARCHITECTURE.md)** - System architecture

## 🐛 Troubleshooting

### Services won't start
```bash
# Check if ports are in use
lsof -i :3000  # React
lsof -i :8000  # FastAPI
lsof -i :8080  # Spring Boot

# Kill processes if needed
pkill -f "react-scripts"
pkill -f "uvicorn"
pkill -f "spring-boot"
```

### Gemini API errors
- Check your API key in `sow_gen_ai/.env`
- Verify model name: `gemini-2.0-flash-exp`
- Check API quota/limits

### Database issues
```bash
# Reset database
rm ai_absence-ai_absence_mi/abscent.db
# Restart Spring Boot to recreate
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

[Your License Here]

## 👥 Authors

- Your Name - Initial work

## 🙏 Acknowledgments

- Google Gemini AI
- FastAPI framework
- React community
- Spring Boot team

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check documentation files
- Review logs: `spring-boot.log`, `fastapi.log`, `react.log`

---

**Built with ❤️ using Google Gemini 2.0 Flash**

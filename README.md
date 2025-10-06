# 🤖 AI Absence and SOW System

AI-powered platform for **Employee Absence Management** and **Statement of Work Generation** with color-coded workflows.

## ✨ Features

- **🔵 Absence Management**: Track employee attendance with blue-themed interface
- **🔴 SOW Generation**: Create professional documents with red-themed workflow  
- **⚫ Unified Interface**: Clean monochrome glassmorphism design
- **🎯 Smart AI**: Natural language processing with Google Gemini

## 🚀 Quick Start

### Prerequisites
- Java 11+, Python 3.8+, Node.js 14+
- Gemini API Key from Google AI Studio

### Setup
```bash
# 1. Clone repository
git clone https://github.com/manju-rog/unified_chat.git
cd unified_chat

# 2. Add API key
echo "GEMINI_API_KEY=your_key_here" > unified_ai_chat/backend/.env

# 3. Start all services
cd unified_ai_chat && ./start_all.sh

# 4. Open browser
open http://localhost:3000
```

## 🎯 Usage

### Absence Management
- "Who is absent today?"
- "Mark John as absent"
- "Show September absences"

### SOW Generation
- "Create a SOW"
- Follow red-themed guided workflow
- Download generated document

## 🏗️ Architecture

```
React Frontend (3000) → FastAPI Backend (5002) → Gemini AI
                              ↓
                      Spring Boot API (8080)
```

## 📁 Structure

```
unified_chat/
├── unified_ai_chat/          # Main application
│   ├── backend/              # FastAPI + Gemini
│   ├── frontend/             # React UI
│   └── start_all.sh          # Startup script
├── ai_absence-ai_absence_mi/ # Spring Boot service
├── sow_gen_ai/               # SOW generation engine
└── README.md
```

## 🔧 Configuration

**Backend (.env):**
```env
GEMINI_API_KEY=your_api_key_here
ABSENCE_API_URL=http://localhost:8080/api
SOW_GENERATOR_PATH=../../sow_gen_ai
```

## 🎨 UI Features

- **Color-coded modes**: Red (SOW), Blue (Absence), Monochrome (Unified)
- **Dynamic expansion**: Interface grows with conversation
- **Glassmorphism design**: Modern blur effects and transparency
- **Responsive layout**: Works on all devices

---

**Built with Google Gemini AI**
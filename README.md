# 🤖 Unified AI Chat System

A comprehensive AI-powered chat system with SOW (Statement of Work) generation, absence management, and multi-service integration.

## ✨ Features

- 🎯 **Multi-Service AI Chat**: Intelligent routing between different services
- � **SSOW Generation**: Automated Statement of Work document creation with Word templates
- 👥 **Absence Management**: Employee absence tracking and reporting
- 🎨 **Dynamic UI Themes**: Context-aware interface that adapts to the current service
- 🔄 **Real-time Updates**: WebSocket support for live interactions
- � **uTimeline Builder**: Visual project timeline creation
- 🤖 **Gemini AI Integration**: Powered by Google's Gemini AI for intelligent responses

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│                    Port: 3001                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Unified Backend (FastAPI)                       │
│                    Port: 8001                                │
│  - Chat orchestration                                        │
│  - Service routing                                           │
│  - Session management                                        │
└─────────────────────────────────────────────────────────────┘
                    ↓               ↓
        ┌───────────────┐   ┌──────────────────┐
        │   new_sow     │   │    Absence       │
        │   Backend     │   │   Management     │
        │   Port: 8002  │   │   Port: 8010     │
        │   (FastAPI)   │   │  (Spring Boot)   │
        └───────────────┘   └──────────────────┘
```

## 🚀 Quick Start (One Command)

```bash
# Clone the repository
git clone https://github.com/manju-rog/unified_chat.git
cd unified_chat

# Run the setup and start script
chmod +x setup_and_start.sh
./setup_and_start.sh
```

This script will:
1. ✅ Check prerequisites (Java, Python, Node.js)
2. ✅ Create environment files
3. ✅ Install all dependencies
4. ✅ Start all services
5. ✅ Open the application in your browser

## 📋 Prerequisites

Before running the setup script, ensure you have:

- **Java 11+** (for absence management service)
- **Python 3.8+** (for backend services)
- **Node.js 14+** and **npm** (for frontend)
- **Gemini API Key** (get from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Installing Prerequisites

**macOS:**
```bash
brew install openjdk@11 python@3.11 node
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install openjdk-11-jdk python3 python3-pip nodejs npm
```

**Windows:**
- Install Java from [Oracle](https://www.oracle.com/java/technologies/downloads/)
- Install Python from [python.org](https://www.python.org/downloads/)
- Install Node.js from [nodejs.org](https://nodejs.org/)

## ⚙️ Manual Setup

If you prefer to set up manually:

### 1. Configure API Keys

Create `.env` files with your Gemini API key:

**new_sow/.env:**
```bash
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-pro
DEBUG=True
```

**unified_ai_chat/backend/.env:**
```bash
GEMINI_API_KEY=your_gemini_api_key_here
NEW_SOW_API_URL=http://localhost:8002
ABSENCE_API_URL=http://localhost:8010
```

### 2. Install Dependencies

```bash
# Python dependencies for new_sow
cd new_sow
pip install -r requirements.txt
cd ..

# Python dependencies for unified backend
cd unified_ai_chat/backend
pip install -r requirements.txt
cd ../..

# Node.js dependencies for frontend
cd unified_ai_chat/frontend
npm install
cd ../..
```

### 3. Start Services

**Option A: Start all services at once**
```bash
cd unified_ai_chat
./start_all_different_ports.sh
```

**Option B: Start services individually**
```bash
# Terminal 1: Absence Management
cd ai_absence-ai_absence_mi/backend/absence-management
./mvnw spring-boot:run

# Terminal 2: new_sow Backend
cd new_sow
python run_backend_8002.py

# Terminal 3: Unified Backend
cd unified_ai_chat/backend
python run_server.py

# Terminal 4: Frontend
cd unified_ai_chat/frontend
npm start
```

### 4. Access the Application

Open your browser and navigate to:
```
http://localhost:3001
```

## 🎯 Usage

### Creating a Statement of Work (SOW)

1. Type: "I want to create a SOW" or "Create statement of work"
2. Follow the guided conversation:
   - Provide project information
   - Select services (Standard or Custom)
   - Define deliverables
   - Set timeline using the visual builder
   - Add resources
   - Select contacts
   - Enter budget
3. Click "Generate SOW Document"
4. Download your professional Word document

### Checking Absences

1. Type: "Who is absent today?" or "Show me absences"
2. Get instant reports on employee absences
3. View department breakdowns and statistics

## 📁 Project Structure

```
unified_chat/
├── unified_ai_chat/          # Main application
│   ├── frontend/             # React frontend (Port 3001)
│   ├── backend/              # FastAPI backend (Port 8001)
│   ├── start_all_different_ports.sh
│   └── stop_all_different_ports.sh
├── new_sow/                  # SOW generation service
│   ├── app/                  # FastAPI application (Port 8002)
│   ├── templates/            # Word templates
│   ├── output/               # Generated documents
│   └── requirements.txt
├── ai_absence-ai_absence_mi/ # Absence management
│   └── backend/              # Spring Boot service (Port 8010)
├── setup_and_start.sh        # One-command setup
├── fresh_install.sh          # Installation only
└── README.md                 # This file
```

## 🔧 Configuration

### Port Configuration

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3001 | React development server |
| Unified Backend | 8001 | Main FastAPI orchestrator |
| new_sow Backend | 8002 | SOW generation service |
| Absence Management | 8010 | Spring Boot service |

### Environment Variables

**new_sow/.env:**
- `GEMINI_API_KEY`: Your Google Gemini API key
- `GEMINI_MODEL`: Model to use (default: gemini-1.5-pro)
- `DEBUG`: Enable debug logging (True/False)

**unified_ai_chat/backend/.env:**
- `GEMINI_API_KEY`: Your Google Gemini API key
- `NEW_SOW_API_URL`: URL for new_sow service
- `ABSENCE_API_URL`: URL for absence management service

## 🛠️ Troubleshooting

### Port Already in Use

```bash
# Check what's using a port
lsof -i :3001  # or :8001, :8002, :8010

# Kill the process
kill -9 <PID>
```

### Services Not Starting

```bash
# Stop all services
cd unified_ai_chat
./stop_all_different_ports.sh

# Check logs
tail -f unified_ai_chat/backend/logs/app.log
tail -f new_sow/logs/app.log
```

### API Key Issues

Make sure your Gemini API key:
- Starts with `AIzaSy`
- Is configured in both `.env` files
- Has the Gemini API enabled in Google Cloud Console

### Dependencies Issues

```bash
# Reinstall Python dependencies
pip install --upgrade -r requirements.txt

# Reinstall Node dependencies
cd unified_ai_chat/frontend
rm -rf node_modules package-lock.json
npm install
```

## 📚 Documentation

- [Complete Setup Guide](COMPLETE_SETUP_AND_TROUBLESHOOTING_GUIDE.md)
- [SOW Integration Guide](SOW_INTEGRATION_COMPLETE_GUIDE.md)
- [Deployment Guide](DEPLOYMENT_PACKAGE_GUIDE.md)
- [Packaging Instructions](PACKAGING_INSTRUCTIONS.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Gemini AI for intelligent conversation handling
- FastAPI for the robust backend framework
- React for the dynamic frontend
- Spring Boot for absence management service

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check the [troubleshooting guide](COMPLETE_SETUP_AND_TROUBLESHOOTING_GUIDE.md)
- Review the [integration documentation](SOW_INTEGRATION_COMPLETE_GUIDE.md)

---

**Made with ❤️ by the Unified AI Chat Team**


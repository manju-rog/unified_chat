# 🚀 AI Absence and SOW - Complete Setup Guide

## 📋 **Prerequisites**

Before cloning, ensure you have:

- **Java 11+** (for Spring Boot absence service)
- **Python 3.8+** (for unified backend)
- **Node.js 14+** (for React frontend)
- **npm** (comes with Node.js)
- **Gemini API Key** (from Google AI Studio)

## 🔧 **Quick Setup (5 Minutes)**

### **1. Clone Repository**
```bash
git clone https://github.com/manju-rog/unified_chat.git
cd unified_chat
```

### **2. Configure API Key**
```bash
# Edit the backend .env file
nano unified_ai_chat/backend/.env

# Add your Gemini API key:
GEMINI_API_KEY=your_gemini_api_key_here
```

### **3. Start All Services**
```bash
cd unified_ai_chat
chmod +x start_all.sh
./start_all.sh
```

### **4. Access Application**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5002
- **Absence Service**: http://localhost:8080

## 📁 **Manual Setup (If Needed)**

### **Backend Setup**
```bash
cd unified_ai_chat/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install python-docx openpyxl  # Additional dependencies

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Start backend
python run_server.py
```

### **Frontend Setup**
```bash
cd unified_ai_chat/frontend

# Install dependencies
npm install

# Start frontend
npm start
```

### **Absence Management Service**
```bash
cd ai_absence-ai_absence_mi/backend/absence-management

# Start Spring Boot service
./mvnw spring-boot:run
```

## 🎯 **Features Overview**

### **🔴 SOW Generation Mode**
- Red-themed interface for document creation
- Step-by-step requirements gathering
- Professional SOW document generation
- Exit SOW button always available

### **🔵 Absence Management Mode**
- Blue-themed interface for HR operations
- Employee absence tracking
- Vacation management
- Detailed absence reports with clear date visibility

### **⚫ Unified Mode**
- Clean monochrome design
- Access to both SOW and absence features
- Smart mode detection and switching

## 🛠️ **Configuration Files**

### **Backend (.env)**
```env
# Gemini AI Configuration
GEMINI_API_KEY=your_api_key_here

# Absence Management API
ABSENCE_API_URL=http://localhost:8080/api

# SOW Generator Path
SOW_GENERATOR_PATH=../../sow_gen_ai
```

### **Frontend (.env)**
```env
REACT_APP_API_URL=http://localhost:5002/api
```

## 🔍 **Troubleshooting**

### **Port Conflicts**
If ports are in use:
```bash
# Check what's using ports
lsof -ti:3000  # Frontend
lsof -ti:5002  # Backend
lsof -ti:8080  # Absence service

# Kill processes if needed
kill $(lsof -ti:3000)
```

### **Missing Dependencies**
```bash
# Backend missing modules
pip install python-docx openpyxl google-generativeai

# Frontend issues
cd unified_ai_chat/frontend
rm -rf node_modules package-lock.json
npm install
```

### **Java Issues**
```bash
# Check Java version
java -version

# Install Java 11+ if needed (macOS)
brew install openjdk@11
```

## 📱 **Usage Examples**

### **Absence Management**
- "Who is absent today?"
- "Mark John as absent"
- "Show September absences"
- "Check vacation days"

### **SOW Generation**
- "Create a SOW"
- "I need a statement of work"
- Follow the red-themed workflow
- Download generated document

## 🎨 **UI Features**

- **Dynamic Expansion**: UI grows with conversation
- **Color-Coded Modes**: Visual feedback for different functions
- **Glassmorphism Design**: Modern, professional appearance
- **Responsive Layout**: Works on all screen sizes
- **High Contrast**: Clear visibility for all elements

## 📊 **System Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │ Spring Boot API │
│   (Port 3000)   │◄──►│   (Port 5002)    │◄──►│   (Port 8080)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Gemini AI API  │
                       │  (Tool Calling)  │
                       └──────────────────┘
```

## 🚀 **Production Deployment**

For production deployment:

1. **Environment Variables**: Set production API keys
2. **Build Frontend**: `npm run build`
3. **Docker**: Use provided Dockerfiles
4. **Reverse Proxy**: Configure nginx/Apache
5. **SSL**: Enable HTTPS for security

## 📞 **Support**

If you encounter issues:

1. Check the logs in `/tmp/` directory
2. Verify all prerequisites are installed
3. Ensure API key is correctly configured
4. Check port availability

---

**🎉 You're ready to use the AI Absence and SOW system! The interface will automatically detect your needs and provide the appropriate color-coded workflow.**
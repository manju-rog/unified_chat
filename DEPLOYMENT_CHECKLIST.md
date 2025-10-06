# ✅ Deployment Checklist - AI Absence and SOW System

## 🎯 **Pre-Deployment Verification**

### **📋 Prerequisites Check**
- [ ] Java 11+ installed (`java -version`)
- [ ] Python 3.8+ installed (`python3 --version`)
- [ ] Node.js 14+ installed (`node --version`)
- [ ] npm installed (`npm --version`)
- [ ] Git installed (`git --version`)

### **🔑 API Configuration**
- [ ] Gemini API key obtained from Google AI Studio
- [ ] API key added to `unified_ai_chat/backend/.env`
- [ ] Environment files properly configured

### **📁 File Structure Verification**
```
unified_chat/
├── unified_ai_chat/
│   ├── backend/
│   │   ├── .env ✅ (with GEMINI_API_KEY)
│   │   ├── requirements.txt ✅
│   │   └── run_server.py ✅
│   ├── frontend/
│   │   ├── package.json ✅
│   │   └── src/ ✅
│   └── start_all.sh ✅ (executable)
├── ai_absence-ai_absence_mi/ ✅
├── sow_gen_ai/ ✅
└── SETUP_GUIDE.md ✅
```

## 🚀 **Deployment Steps**

### **Step 1: Clone Repository**
```bash
git clone https://github.com/manju-rog/unified_chat.git
cd unified_chat
```
- [ ] Repository cloned successfully
- [ ] All files present

### **Step 2: Configure Environment**
```bash
# Add Gemini API key
echo "GEMINI_API_KEY=your_actual_key_here" > unified_ai_chat/backend/.env
```
- [ ] API key configured
- [ ] .env file created

### **Step 3: Install Dependencies**
```bash
# Backend dependencies
cd unified_ai_chat/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install python-docx openpyxl
cd ../..

# Frontend dependencies  
cd unified_ai_chat/frontend
npm install
cd ../..
```
- [ ] Backend virtual environment created
- [ ] Python dependencies installed
- [ ] Additional packages (docx, openpyxl) installed
- [ ] Frontend dependencies installed

### **Step 4: Start Services**
```bash
cd unified_ai_chat
chmod +x start_all.sh
./start_all.sh
```
- [ ] Start script executable
- [ ] All services starting without errors
- [ ] Ports 3000, 5002, 8080 available

## 🔍 **Verification Tests**

### **Service Health Checks**
```bash
# Check backend health
curl http://localhost:5002/api/health
# Expected: {"status":"ok","time":"..."}

# Check frontend loading
curl http://localhost:3000
# Expected: HTML with React app

# Check absence service
curl http://localhost:8080/api/employees
# Expected: JSON array of employees
```
- [ ] Backend health endpoint responding
- [ ] Frontend serving React app
- [ ] Absence service API responding

### **Feature Testing**

#### **Absence Management**
- [ ] Open http://localhost:3000
- [ ] Type: "Who is absent today?"
- [ ] Verify blue theme activation
- [ ] Check absence report display
- [ ] Test employee name disambiguation

#### **SOW Generation**
- [ ] Type: "Create a SOW"
- [ ] Verify SOW initiation suggestion
- [ ] Click "Generate SOW" button
- [ ] Verify red theme activation
- [ ] Test "Exit SOW" functionality
- [ ] Complete SOW workflow

#### **UI Features**
- [ ] Monochrome glassmorphism design loads
- [ ] Dynamic expansion works (horizontal + vertical)
- [ ] Color themes switch properly (Red/Blue/Monochrome)
- [ ] Date pills in absence reports are clearly visible
- [ ] All buttons and interactions work smoothly

## 🎨 **UI Verification Checklist**

### **Visual Elements**
- [ ] Title displays: "AI ABSENCE AND SOW"
- [ ] Subtitle is readable and properly aligned
- [ ] Hero section centers correctly
- [ ] Chat card has glassmorphism effects
- [ ] Message bubbles display properly

### **Color Themes**
- [ ] **Unified Mode**: Clean monochrome (white/black/gray)
- [ ] **SOW Mode**: Red theme with red buttons and accents
- [ ] **Absence Mode**: Blue theme with blue buttons and accents
- [ ] Mode transitions are smooth

### **Interactive Elements**
- [ ] Send button works and shows loading state
- [ ] Quick action chips are clickable
- [ ] Confirmation buttons (Yes/No) work
- [ ] SOW initiation buttons appear correctly
- [ ] Exit SOW buttons work in SOW mode only

## 🐛 **Common Issues & Solutions**

### **Port Conflicts**
```bash
# If ports are in use:
lsof -ti:3000 | xargs kill  # Frontend
lsof -ti:5002 | xargs kill  # Backend  
lsof -ti:8080 | xargs kill  # Absence service
```

### **Missing Dependencies**
```bash
# Backend missing modules:
pip install python-docx openpyxl google-generativeai

# Frontend issues:
rm -rf node_modules package-lock.json
npm install
```

### **API Key Issues**
- [ ] Verify API key is valid
- [ ] Check .env file location and format
- [ ] Ensure no extra spaces or quotes around key

### **Java/Spring Boot Issues**
```bash
# Check Java version
java -version

# If Java missing (macOS):
brew install openjdk@11

# If Spring Boot fails:
cd ai_absence-ai_absence_mi/backend/absence-management
./mvnw clean install
./mvnw spring-boot:run
```

## 📊 **Performance Verification**

### **Load Times**
- [ ] Frontend loads in < 3 seconds
- [ ] Backend responds in < 1 second
- [ ] AI responses arrive in < 5 seconds
- [ ] File downloads work properly

### **Memory Usage**
- [ ] Backend uses < 500MB RAM
- [ ] Frontend uses reasonable browser memory
- [ ] No memory leaks during extended use

## 🔒 **Security Checklist**

- [ ] API key not exposed in frontend
- [ ] CORS properly configured
- [ ] No sensitive data in logs
- [ ] Environment files not committed to git

## 📝 **Documentation Verification**

- [ ] SETUP_GUIDE.md is comprehensive
- [ ] README.md reflects current features
- [ ] All example commands work
- [ ] Screenshots/demos are current

## 🎉 **Final Deployment Confirmation**

### **User Acceptance Test**
1. [ ] New user can clone and setup in < 10 minutes
2. [ ] All features work without technical knowledge
3. [ ] Error messages are helpful and clear
4. [ ] UI is intuitive and responsive
5. [ ] Both absence and SOW workflows complete successfully

### **Production Readiness**
- [ ] All services start automatically
- [ ] System handles errors gracefully
- [ ] Logs are informative but not verbose
- [ ] Performance is acceptable under normal load

---

## ✅ **Deployment Complete!**

When all items are checked:
- [ ] System is ready for production use
- [ ] Documentation is complete and accurate
- [ ] All features tested and working
- [ ] Repository is clean and well-organized

**🎯 The AI Absence and SOW system is now ready for deployment and use!**
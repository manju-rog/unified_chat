# Deployment Package Guide - Zip, Transfer, and Run

## 📦 For Package Recipients: Quick Start

**You received a zip file of this project. Here's how to get it running in 5 minutes.**

---

## Step 1: Extract the Package

```bash
# Extract the zip file
unzip unified-ai-chat-system.zip
cd unified-ai-chat-system

# Verify extraction
ls -la
# You should see: ai_absence-ai_absence_mi, new_sow, unified_ai_chat, *.md files
```

---

## Step 2: Prerequisites Installation

### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Java (for Absence Management)
brew install openjdk@11
sudo ln -sfn /opt/homebrew/opt/openjdk@11/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-11.jdk

# Install Python
brew install python@3.11

# Install Node.js
brew install node

# Verify installations
java -version    # Should show Java 11+
python3 --version # Should show Python 3.8+
node --version   # Should show Node 14+
npm --version
```

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Java
sudo apt install openjdk-11-jdk -y

# Install Python
sudo apt install python3 python3-pip python3-venv -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Verify installations
java -version
python3 --version
node --version
npm --version
```

### Windows

1. **Install Java:**
   - Download from: https://adoptium.net/
   - Install Java 11 or higher
   - Add to PATH

2. **Install Python:**
   - Download from: https://www.python.org/downloads/
   - Install Python 3.8 or higher
   - Check "Add Python to PATH" during installation

3. **Install Node.js:**
   - Download from: https://nodejs.org/
   - Install LTS version
   - Restart terminal after installation

4. **Verify installations:**
   ```cmd
   java -version
   python --version
   node --version
   npm --version
   ```

---

## Step 3: Configure API Keys

**CRITICAL: You must add your Gemini API key before running.**

### Get Gemini API Key

1. Go to: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIzaSy...`)

### Add API Key to Configuration Files

```bash
# Configure new_sow backend
cat > new_sow/.env << 'EOF'
GEMINI_API_KEY=YOUR_API_KEY_HERE
GEMINI_MODEL=gemini-2.5-flash
DEBUG=True
EOF

# Configure unified_ai_chat backend
cat > unified_ai_chat/backend/.env << 'EOF'
GEMINI_API_KEY=YOUR_API_KEY_HERE
EOF

# Replace YOUR_API_KEY_HERE with your actual key
# On macOS/Linux:
sed -i '' 's/YOUR_API_KEY_HERE/AIzaSy.../g' new_sow/.env
sed -i '' 's/YOUR_API_KEY_HERE/AIzaSy.../g' unified_ai_chat/backend/.env

# On Linux (without macOS):
sed -i 's/YOUR_API_KEY_HERE/AIzaSy.../g' new_sow/.env
sed -i 's/YOUR_API_KEY_HERE/AIzaSy.../g' unified_ai_chat/backend/.env
```

**Or manually edit the files:**
```bash
# Edit with your preferred editor
nano new_sow/.env
nano unified_ai_chat/backend/.env

# Replace YOUR_API_KEY_HERE with your actual Gemini API key
```

---

## Step 4: Install Dependencies

### Install Python Dependencies

```bash
# Install new_sow dependencies
cd new_sow
python3 -m pip install -r requirements.txt
cd ..

# Install unified_ai_chat backend dependencies
cd unified_ai_chat/backend
python3 -m pip install -r requirements.txt
cd ../..
```

### Install Node.js Dependencies

```bash
# Install frontend dependencies
cd unified_ai_chat/frontend
npm install
cd ../..
```

### Verify Maven Wrapper (for Absence Management)

```bash
# Make Maven wrapper executable
chmod +x ai_absence-ai_absence_mi/backend/absence-management/mvnw

# Test Maven
cd ai_absence-ai_absence_mi/backend/absence-management
./mvnw --version
cd ../../..
```

---

## Step 5: Verify Template File

```bash
# Check if template exists
ls -la new_sow/sample_sow_template.docx

# If missing, copy from templates folder
if [ ! -f "new_sow/sample_sow_template.docx" ]; then
    cp new_sow/templates/doc_*.docx new_sow/sample_sow_template.docx 2>/dev/null || \
    echo "⚠️  Warning: Template file not found. SOW generation may fail."
fi
```

---

## Step 6: Start All Services

### Option A: Automated Script (Recommended)

```bash
cd unified_ai_chat
chmod +x start_all_different_ports.sh
./start_all_different_ports.sh
```

The script will:
- Check prerequisites
- Start all 4 services
- Wait for each to be ready
- Open browser automatically

### Option B: Manual Start (if script fails)

**Terminal 1 - Absence Management (Port 8010):**
```bash
cd ai_absence-ai_absence_mi/backend/absence-management
./mvnw spring-boot:run
```

**Terminal 2 - new_sow Backend (Port 8002):**
```bash
cd new_sow
python3 run_backend_8002.py
```

**Terminal 3 - Unified Chat Backend (Port 8001):**
```bash
cd unified_ai_chat/backend
python3 run_server.py
```

**Terminal 4 - Frontend (Port 3001):**
```bash
cd unified_ai_chat/frontend
npm start
```

---

## Step 7: Verify Everything Works

### Check Services are Running

```bash
# Check all ports
lsof -i :8010,8002,8001,3001

# Or check individually
curl http://localhost:8010/api/ai/employees  # Should return JSON
curl http://localhost:8002/health            # Should return {"status":"healthy"}
curl http://localhost:8001/api/health        # Should return health status
curl http://localhost:3001                   # Should return HTML
```

### Open the Application

Open your browser to: **http://localhost:3001**

### Test Basic Functionality

1. **Test Absence Management:**
   - Type: "Mark Manju absent today"
   - Should mark absence successfully

2. **Test SOW Generation:**
   - Type: "I want to create a SOW"
   - Follow the 7-step wizard
   - Click "Generate SOW Document"
   - Document should be generated

---

## 🚨 Troubleshooting After Extraction

### Issue: "Command not found" errors

**Solution:**
```bash
# Make scripts executable
chmod +x unified_ai_chat/start_all_different_ports.sh
chmod +x unified_ai_chat/stop_all_different_ports.sh
chmod +x ai_absence-ai_absence_mi/backend/absence-management/mvnw
```

### Issue: "Port already in use"

**Solution:**
```bash
# Find and kill processes using the ports
lsof -ti:8010 | xargs kill -9
lsof -ti:8002 | xargs kill -9
lsof -ti:8001 | xargs kill -9
lsof -ti:3001 | xargs kill -9

# Then restart services
```

### Issue: "Module not found" or "Package not found"

**Solution:**
```bash
# Reinstall Python dependencies
cd new_sow
pip3 install -r requirements.txt --force-reinstall

cd ../unified_ai_chat/backend
pip3 install -r requirements.txt --force-reinstall

# Reinstall Node dependencies
cd ../frontend
rm -rf node_modules package-lock.json
npm install
```

### Issue: "GEMINI_API_KEY not found"

**Solution:**
```bash
# Verify .env files exist and have content
cat new_sow/.env
cat unified_ai_chat/backend/.env

# If empty or missing, recreate them (see Step 3)
```

### Issue: "Template not found"

**Solution:**
```bash
# Check template location
ls -la new_sow/sample_sow_template.docx

# If missing, check templates folder
ls -la new_sow/templates/

# Copy any template file
cp new_sow/templates/doc_*.docx new_sow/sample_sow_template.docx
```

### Issue: Maven build fails

**Solution:**
```bash
# Clean Maven cache and rebuild
cd ai_absence-ai_absence_mi/backend/absence-management
./mvnw clean
./mvnw spring-boot:run
```

---

## 📋 Pre-Deployment Checklist (For Package Creator)

**Before zipping the project, ensure:**

### Files to Include
- [ ] All source code directories
- [ ] `COMPLETE_SETUP_AND_TROUBLESHOOTING_GUIDE.md`
- [ ] `DEPLOYMENT_PACKAGE_GUIDE.md` (this file)
- [ ] `START_ALL_SERVICES.md`
- [ ] Startup scripts (`start_all_different_ports.sh`, `stop_all_different_ports.sh`)
- [ ] `requirements.txt` files
- [ ] `package.json` files
- [ ] Template files in `new_sow/templates/`
- [ ] Sample template: `new_sow/sample_sow_template.docx`

### Files to Exclude (Add to .gitignore or remove before zipping)
- [ ] `node_modules/` folders
- [ ] `venv/` or virtual environment folders
- [ ] `.env` files with actual API keys (include `.env.example` instead)
- [ ] `__pycache__/` folders
- [ ] `.DS_Store` files
- [ ] `target/` folders (Maven build output)
- [ ] `build/` folders
- [ ] Generated documents in `output/` folders
- [ ] Log files in `/tmp/`
- [ ] `.pid` files

### Create .env.example Files

```bash
# Create example env files (without real keys)
cat > new_sow/.env.example << 'EOF'
GEMINI_API_KEY=YOUR_API_KEY_HERE
GEMINI_MODEL=gemini-2.5-flash
DEBUG=True
EOF

cat > unified_ai_chat/backend/.env.example << 'EOF'
GEMINI_API_KEY=YOUR_API_KEY_HERE
EOF
```

### Zip Command

```bash
# From project parent directory
zip -r unified-ai-chat-system.zip unified-ai-chat-system/ \
  -x "*/node_modules/*" \
  -x "*/venv/*" \
  -x "*/__pycache__/*" \
  -x "*/.DS_Store" \
  -x "*/target/*" \
  -x "*/build/*" \
  -x "*/output/*" \
  -x "*/.env" \
  -x "*.log" \
  -x "*.pid"
```

---

## 🔄 Clean Installation Script

**Save this as `fresh_install.sh` in the extracted folder:**

```bash
#!/bin/bash

echo "🚀 Fresh Installation Script for Unified AI Chat System"
echo "========================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check prerequisites
echo "📋 Checking prerequisites..."
command -v java >/dev/null 2>&1 || { echo -e "${RED}❌ Java not found${NC}"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}❌ Python3 not found${NC}"; exit 1; }
command -v node >/dev/null 2>&1 || { echo -e "${RED}❌ Node.js not found${NC}"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo -e "${RED}❌ npm not found${NC}"; exit 1; }
echo -e "${GREEN}✅ All prerequisites found${NC}"
echo ""

# Check API keys
echo "🔑 Checking API keys..."
if [ ! -f "new_sow/.env" ] || ! grep -q "AIzaSy" new_sow/.env; then
    echo -e "${RED}❌ Gemini API key not configured in new_sow/.env${NC}"
    echo "Please edit new_sow/.env and add your GEMINI_API_KEY"
    exit 1
fi
if [ ! -f "unified_ai_chat/backend/.env" ] || ! grep -q "AIzaSy" unified_ai_chat/backend/.env; then
    echo -e "${RED}❌ Gemini API key not configured in unified_ai_chat/backend/.env${NC}"
    echo "Please edit unified_ai_chat/backend/.env and add your GEMINI_API_KEY"
    exit 1
fi
echo -e "${GREEN}✅ API keys configured${NC}"
echo ""

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x unified_ai_chat/start_all_different_ports.sh
chmod +x unified_ai_chat/stop_all_different_ports.sh
chmod +x ai_absence-ai_absence_mi/backend/absence-management/mvnw
echo -e "${GREEN}✅ Scripts are executable${NC}"
echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd new_sow
python3 -m pip install -q -r requirements.txt
cd ..
cd unified_ai_chat/backend
python3 -m pip install -q -r requirements.txt
cd ../..
echo -e "${GREEN}✅ Python dependencies installed${NC}"
echo ""

# Install Node dependencies
echo "📦 Installing Node.js dependencies..."
cd unified_ai_chat/frontend
npm install --silent
cd ../..
echo -e "${GREEN}✅ Node.js dependencies installed${NC}"
echo ""

# Check template
echo "📄 Checking template file..."
if [ ! -f "new_sow/sample_sow_template.docx" ]; then
    echo -e "${YELLOW}⚠️  Template not found, copying from templates folder...${NC}"
    cp new_sow/templates/doc_*.docx new_sow/sample_sow_template.docx 2>/dev/null || \
    echo -e "${RED}❌ Could not find template file${NC}"
fi
echo -e "${GREEN}✅ Template file ready${NC}"
echo ""

echo "========================================================"
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo "To start all services, run:"
echo "  cd unified_ai_chat"
echo "  ./start_all_different_ports.sh"
echo ""
echo "Or start services manually in separate terminals:"
echo "  Terminal 1: cd ai_absence-ai_absence_mi/backend/absence-management && ./mvnw spring-boot:run"
echo "  Terminal 2: cd new_sow && python3 run_backend_8002.py"
echo "  Terminal 3: cd unified_ai_chat/backend && python3 run_server.py"
echo "  Terminal 4: cd unified_ai_chat/frontend && npm start"
echo ""
echo "Then open: http://localhost:3001"
echo "========================================================"
```

**Make it executable and run:**
```bash
chmod +x fresh_install.sh
./fresh_install.sh
```

---

## 📝 Quick Reference Card

**Save this for quick access:**

```
╔════════════════════════════════════════════════════════════╗
║        UNIFIED AI CHAT SYSTEM - QUICK REFERENCE           ║
╠════════════════════════════════════════════════════════════╣
║ SERVICES:                                                  ║
║  • Absence Management:  http://localhost:8010              ║
║  • new_sow Backend:     http://localhost:8002              ║
║  • Unified Backend:     http://localhost:8001              ║
║  • Frontend:            http://localhost:3001              ║
╠════════════════════════════════════════════════════════════╣
║ START ALL:                                                 ║
║  cd unified_ai_chat && ./start_all_different_ports.sh      ║
╠════════════════════════════════════════════════════════════╣
║ STOP ALL:                                                  ║
║  cd unified_ai_chat && ./stop_all_different_ports.sh       ║
╠════════════════════════════════════════════════════════════╣
║ CHECK STATUS:                                              ║
║  lsof -i :8010,8002,8001,3001                              ║
╠════════════════════════════════════════════════════════════╣
║ VIEW LOGS:                                                 ║
║  tail -f /tmp/*-backend-*.log                              ║
╠════════════════════════════════════════════════════════════╣
║ CONFIGURATION FILES:                                       ║
║  • new_sow/.env                                            ║
║  • unified_ai_chat/backend/.env                            ║
╠════════════════════════════════════════════════════════════╣
║ HELP:                                                      ║
║  • COMPLETE_SETUP_AND_TROUBLESHOOTING_GUIDE.md             ║
║  • DEPLOYMENT_PACKAGE_GUIDE.md                             ║
╚════════════════════════════════════════════════════════════╝
```

---

## 🎯 Success Criteria

**Your installation is successful when:**

1. ✅ All 4 services start without errors
2. ✅ All health endpoints respond:
   - http://localhost:8010/api/ai/employees
   - http://localhost:8002/health
   - http://localhost:8001/api/health
   - http://localhost:3001
3. ✅ Frontend loads in browser
4. ✅ You can mark an absence
5. ✅ You can generate a SOW document

---

## 📞 Support

**If you encounter issues:**

1. Check `COMPLETE_SETUP_AND_TROUBLESHOOTING_GUIDE.md` for detailed troubleshooting
2. Verify all prerequisites are installed
3. Ensure API keys are configured correctly
4. Check logs in `/tmp/` directory
5. Try the fresh installation script

**Common Issues:**
- Port conflicts → Kill existing processes
- Missing dependencies → Run fresh_install.sh
- API key errors → Verify .env files
- Template errors → Check sample_sow_template.docx exists

---

**Package Version:** 1.0
**Last Updated:** October 30, 2025
**Tested On:** macOS, Linux (Ubuntu), Windows 10/11

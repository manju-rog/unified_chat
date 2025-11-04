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
command -v java >/dev/null 2>&1 || { echo -e "${RED}❌ Java not found. Please install Java 11+${NC}"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}❌ Python3 not found. Please install Python 3.8+${NC}"; exit 1; }
command -v node >/dev/null 2>&1 || { echo -e "${RED}❌ Node.js not found. Please install Node 14+${NC}"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo -e "${RED}❌ npm not found. Please install npm${NC}"; exit 1; }
echo -e "${GREEN}✅ All prerequisites found${NC}"
echo ""

# Check API keys
echo "🔑 Checking API keys..."
if [ ! -f "new_sow/.env" ]; then
    echo -e "${YELLOW}⚠️  Creating new_sow/.env from example...${NC}"
    if [ -f "new_sow/.env.example" ]; then
        cp new_sow/.env.example new_sow/.env
    else
        cat > new_sow/.env << 'EOF'
GEMINI_API_KEY=YOUR_API_KEY_HERE
GEMINI_MODEL=gemini-2.5-flash
DEBUG=True
EOF
    fi
    echo -e "${RED}❌ Please edit new_sow/.env and add your GEMINI_API_KEY${NC}"
    exit 1
fi

if ! grep -q "AIzaSy" new_sow/.env; then
    echo -e "${RED}❌ Gemini API key not configured in new_sow/.env${NC}"
    echo "Please edit new_sow/.env and replace YOUR_API_KEY_HERE with your actual key"
    exit 1
fi

if [ ! -f "unified_ai_chat/backend/.env" ]; then
    echo -e "${YELLOW}⚠️  Creating unified_ai_chat/backend/.env from example...${NC}"
    if [ -f "unified_ai_chat/backend/.env.example" ]; then
        cp unified_ai_chat/backend/.env.example unified_ai_chat/backend/.env
    else
        cat > unified_ai_chat/backend/.env << 'EOF'
GEMINI_API_KEY=YOUR_API_KEY_HERE
EOF
    fi
    echo -e "${RED}❌ Please edit unified_ai_chat/backend/.env and add your GEMINI_API_KEY${NC}"
    exit 1
fi

if ! grep -q "AIzaSy" unified_ai_chat/backend/.env; then
    echo -e "${RED}❌ Gemini API key not configured in unified_ai_chat/backend/.env${NC}"
    echo "Please edit unified_ai_chat/backend/.env and replace YOUR_API_KEY_HERE with your actual key"
    exit 1
fi

echo -e "${GREEN}✅ API keys configured${NC}"
echo ""

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x unified_ai_chat/start_all_different_ports.sh 2>/dev/null
chmod +x unified_ai_chat/stop_all_different_ports.sh 2>/dev/null
chmod +x ai_absence-ai_absence_mi/backend/absence-management/mvnw 2>/dev/null
echo -e "${GREEN}✅ Scripts are executable${NC}"
echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies for new_sow..."
cd new_sow
python3 -m pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to install new_sow dependencies${NC}"
    exit 1
fi
cd ..

echo "📦 Installing Python dependencies for unified_ai_chat..."
cd unified_ai_chat/backend
python3 -m pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to install unified_ai_chat dependencies${NC}"
    exit 1
fi
cd ../..
echo -e "${GREEN}✅ Python dependencies installed${NC}"
echo ""

# Install Node dependencies
echo "📦 Installing Node.js dependencies (this may take a few minutes)..."
cd unified_ai_chat/frontend
npm install --silent
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to install Node.js dependencies${NC}"
    exit 1
fi
cd ../..
echo -e "${GREEN}✅ Node.js dependencies installed${NC}"
echo ""

# Check template
echo "📄 Checking template file..."
if [ ! -f "new_sow/sample_sow_template.docx" ]; then
    echo -e "${YELLOW}⚠️  Template not found, copying from templates folder...${NC}"
    cp new_sow/templates/doc_*.docx new_sow/sample_sow_template.docx 2>/dev/null
    if [ ! -f "new_sow/sample_sow_template.docx" ]; then
        echo -e "${RED}❌ Could not find template file. SOW generation may fail.${NC}"
    else
        echo -e "${GREEN}✅ Template file copied${NC}"
    fi
else
    echo -e "${GREEN}✅ Template file exists${NC}"
fi
echo ""

echo "========================================================"
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo "To start all services, run:"
echo -e "${YELLOW}  cd unified_ai_chat${NC}"
echo -e "${YELLOW}  ./start_all_different_ports.sh${NC}"
echo ""
echo "Or start services manually in separate terminals:"
echo "  Terminal 1: cd ai_absence-ai_absence_mi/backend/absence-management && ./mvnw spring-boot:run"
echo "  Terminal 2: cd new_sow && python3 run_backend_8002.py"
echo "  Terminal 3: cd unified_ai_chat/backend && python3 run_server.py"
echo "  Terminal 4: cd unified_ai_chat/frontend && npm start"
echo ""
echo "Then open: ${GREEN}http://localhost:3001${NC}"
echo "========================================================"

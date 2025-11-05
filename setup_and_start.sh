#!/bin/bash

# ============================================================================
# UNIFIED AI CHAT SYSTEM - ONE-COMMAND SETUP & START
# ============================================================================
# This script:
# 1. Checks prerequisites (Java, Python, Node.js)
# 2. Creates .env files from examples
# 3. Installs all dependencies
# 4. Starts all services
# ============================================================================

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   🚀 UNIFIED AI CHAT SYSTEM - SETUP & START                   ║"
echo "║   Complete installation and startup script                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# STEP 1: CHECK PREREQUISITES
# ============================================================================
echo -e "${BLUE}📋 STEP 1: Checking prerequisites...${NC}"

check_command() {
    if command -v $1 >/dev/null 2>&1; then
        echo -e "${GREEN}  ✅ $1 found${NC}"
        return 0
    else
        echo -e "${RED}  ❌ $1 not found${NC}"
        return 1
    fi
}

MISSING_DEPS=0

check_command java || MISSING_DEPS=1
check_command python3 || MISSING_DEPS=1
check_command node || MISSING_DEPS=1
check_command npm || MISSING_DEPS=1

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo -e "${RED}❌ Missing prerequisites. Please install:${NC}"
    echo "  - Java 11+ (for absence management)"
    echo "  - Python 3.8+ (for backends)"
    echo "  - Node.js 14+ and npm (for frontend)"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites found!${NC}"
echo ""

# ============================================================================
# STEP 2: SETUP ENVIRONMENT FILES
# ============================================================================
echo -e "${BLUE}📋 STEP 2: Setting up environment files...${NC}"

# Function to setup .env file
setup_env_file() {
    local env_file=$1
    local example_file=$2
    
    if [ -f "$env_file" ]; then
        echo -e "${GREEN}  ✅ $env_file already exists${NC}"
        
        # Check if API key is configured
        if grep -q "YOUR_API_KEY_HERE" "$env_file" 2>/dev/null; then
            echo -e "${YELLOW}  ⚠️  API key not configured in $env_file${NC}"
            echo -e "${YELLOW}     Please edit this file and add your Gemini API key${NC}"
        elif grep -q "AIzaSy" "$env_file" 2>/dev/null; then
            echo -e "${GREEN}  ✅ API key configured${NC}"
        fi
    else
        if [ -f "$example_file" ]; then
            cp "$example_file" "$env_file"
            echo -e "${YELLOW}  ⚠️  Created $env_file from example${NC}"
            echo -e "${YELLOW}     Please edit this file and add your Gemini API key${NC}"
        else
            echo -e "${RED}  ❌ Neither $env_file nor $example_file found${NC}"
        fi
    fi
}

setup_env_file "new_sow/.env" "new_sow/.env.example"
setup_env_file "unified_ai_chat/backend/.env" "unified_ai_chat/backend/.env.example"

echo ""

# ============================================================================
# STEP 3: MAKE SCRIPTS EXECUTABLE
# ============================================================================
echo -e "${BLUE}📋 STEP 3: Making scripts executable...${NC}"

chmod +x unified_ai_chat/start_all_different_ports.sh 2>/dev/null || true
chmod +x unified_ai_chat/stop_all_different_ports.sh 2>/dev/null || true
chmod +x ai_absence-ai_absence_mi/backend/absence-management/mvnw 2>/dev/null || true
chmod +x fresh_install.sh 2>/dev/null || true
chmod +x setup_and_start.sh 2>/dev/null || true

echo -e "${GREEN}✅ Scripts are executable${NC}"
echo ""

# ============================================================================
# STEP 4: CREATE REQUIRED DIRECTORIES
# ============================================================================
echo -e "${BLUE}📋 STEP 4: Creating required directories...${NC}"

mkdir -p new_sow/output
mkdir -p new_sow/logs
mkdir -p unified_ai_chat/backend/logs
mkdir -p unified_ai_chat/generated_docs_sow

echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# ============================================================================
# STEP 5: INSTALL PYTHON DEPENDENCIES
# ============================================================================
echo -e "${BLUE}📋 STEP 5: Installing Python dependencies...${NC}"

echo "  📦 Installing new_sow dependencies..."
cd new_sow
python3 -m pip install --upgrade pip -q
python3 -m pip install -r requirements.txt -q
if [ $? -ne 0 ]; then
    echo -e "${RED}  ❌ Failed to install new_sow dependencies${NC}"
    exit 1
fi
cd ..
echo -e "${GREEN}  ✅ new_sow dependencies installed${NC}"

echo "  📦 Installing unified_ai_chat backend dependencies..."
cd unified_ai_chat/backend
python3 -m pip install -r requirements.txt -q
if [ $? -ne 0 ]; then
    echo -e "${RED}  ❌ Failed to install unified_ai_chat dependencies${NC}"
    exit 1
fi
cd ../..
echo -e "${GREEN}  ✅ unified_ai_chat backend dependencies installed${NC}"
echo ""

# ============================================================================
# STEP 6: INSTALL NODE.JS DEPENDENCIES
# ============================================================================
echo -e "${BLUE}📋 STEP 6: Installing Node.js dependencies...${NC}"
echo "  (This may take a few minutes)"

cd unified_ai_chat/frontend
npm install --silent
if [ $? -ne 0 ]; then
    echo -e "${RED}  ❌ Failed to install Node.js dependencies${NC}"
    exit 1
fi
cd ../..
echo -e "${GREEN}✅ Node.js dependencies installed${NC}"
echo ""

# ============================================================================
# STEP 7: VERIFY TEMPLATE FILES
# ============================================================================
echo -e "${BLUE}📋 STEP 7: Verifying template files...${NC}"

if [ -f "new_sow/sample_sow_template.docx" ]; then
    echo -e "${GREEN}✅ SOW template found${NC}"
elif [ -f "new_sow/templates/SOW_Template.docx" ]; then
    cp new_sow/templates/SOW_Template.docx new_sow/sample_sow_template.docx
    echo -e "${GREEN}✅ SOW template copied${NC}"
else
    echo -e "${YELLOW}⚠️  SOW template not found (generation may fail)${NC}"
fi
echo ""

# ============================================================================
# STEP 8: CHECK API KEYS BEFORE STARTING
# ============================================================================
echo -e "${BLUE}📋 STEP 8: Verifying API keys...${NC}"

API_KEY_MISSING=0

if ! grep -q "AIzaSy" new_sow/.env 2>/dev/null; then
    echo -e "${RED}  ❌ Gemini API key not configured in new_sow/.env${NC}"
    API_KEY_MISSING=1
fi

if ! grep -q "AIzaSy" unified_ai_chat/backend/.env 2>/dev/null; then
    echo -e "${RED}  ❌ Gemini API key not configured in unified_ai_chat/backend/.env${NC}"
    API_KEY_MISSING=1
fi

if [ $API_KEY_MISSING -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  ⚠️  API KEYS NOT CONFIGURED                                  ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Please configure your Gemini API keys in:"
    echo "  1. new_sow/.env"
    echo "  2. unified_ai_chat/backend/.env"
    echo ""
    echo "Get your API key from: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to exit and configure keys..."
fi

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""

# ============================================================================
# STEP 9: START ALL SERVICES
# ============================================================================
echo -e "${BLUE}📋 STEP 9: Starting all services...${NC}"
echo ""

cd unified_ai_chat
./start_all_different_ports.sh


#!/bin/bash

echo "📦 Creating Deployment Package for Unified AI Chat System"
echo "=========================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Package name
PACKAGE_NAME="unified-ai-chat-system"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_FILE="${PACKAGE_NAME}_${TIMESTAMP}.zip"

echo "📋 Pre-packaging checklist..."

# Check if we're in the right directory
if [ ! -d "unified_ai_chat" ] || [ ! -d "new_sow" ] || [ ! -d "ai_absence-ai_absence_mi" ]; then
    echo -e "${RED}❌ Error: Must run from project root directory${NC}"
    echo "Expected directories: unified_ai_chat, new_sow, ai_absence-ai_absence_mi"
    exit 1
fi

# Create .env.example files if they don't exist
echo "🔧 Creating .env.example files..."
if [ ! -f "new_sow/.env.example" ]; then
    cat > new_sow/.env.example << 'EOF'
GEMINI_API_KEY=YOUR_API_KEY_HERE
GEMINI_MODEL=gemini-2.5-flash
DEBUG=True
EOF
    echo -e "${GREEN}✅ Created new_sow/.env.example${NC}"
fi

if [ ! -f "unified_ai_chat/backend/.env.example" ]; then
    cat > unified_ai_chat/backend/.env.example << 'EOF'
GEMINI_API_KEY=YOUR_API_KEY_HERE
EOF
    echo -e "${GREEN}✅ Created unified_ai_chat/backend/.env.example${NC}"
fi

# Check if documentation exists
echo "📚 Checking documentation files..."
if [ ! -f "README_FIRST.md" ]; then
    echo -e "${YELLOW}⚠️  README_FIRST.md not found${NC}"
fi
if [ ! -f "DEPLOYMENT_PACKAGE_GUIDE.md" ]; then
    echo -e "${YELLOW}⚠️  DEPLOYMENT_PACKAGE_GUIDE.md not found${NC}"
fi
if [ ! -f "COMPLETE_SETUP_AND_TROUBLESHOOTING_GUIDE.md" ]; then
    echo -e "${YELLOW}⚠️  COMPLETE_SETUP_AND_TROUBLESHOOTING_GUIDE.md not found${NC}"
fi

# Check if template exists
echo "📄 Checking template file..."
if [ ! -f "new_sow/sample_sow_template.docx" ]; then
    echo -e "${YELLOW}⚠️  Template file not found, copying from templates...${NC}"
    cp new_sow/templates/doc_*.docx new_sow/sample_sow_template.docx 2>/dev/null
    if [ -f "new_sow/sample_sow_template.docx" ]; then
        echo -e "${GREEN}✅ Template file copied${NC}"
    else
        echo -e "${RED}❌ Warning: Template file not found${NC}"
    fi
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x unified_ai_chat/start_all_different_ports.sh 2>/dev/null
chmod +x unified_ai_chat/stop_all_different_ports.sh 2>/dev/null
chmod +x fresh_install.sh 2>/dev/null
chmod +x ai_absence-ai_absence_mi/backend/absence-management/mvnw 2>/dev/null

echo ""
echo "📦 Creating zip package..."
echo "Excluding: node_modules, venv, __pycache__, .DS_Store, target, build, output, .env (with keys), logs"
echo ""

# Create the zip file
zip -r "$PACKAGE_FILE" . \
  -x "*/node_modules/*" \
  -x "*/venv/*" \
  -x "*/__pycache__/*" \
  -x "*/.DS_Store" \
  -x "*/target/*" \
  -x "*/build/*" \
  -x "*/output/*.docx" \
  -x "*/generated_docs_sow/*.docx" \
  -x "*/.env" \
  -x "*.log" \
  -x "*.pid" \
  -x "*/.git/*" \
  -x "*/.idea/*" \
  -x "*/.vscode/*" \
  -x "*/dist/*" \
  -x "*/.pytest_cache/*" \
  -x "*/.coverage" \
  -x "*/htmlcov/*" \
  -x "*.pyc" \
  -x "*.pyo" \
  -x "*.class" \
  -x "*.jar" \
  -x "*/package-lock.json" \
  -q

if [ $? -eq 0 ]; then
    FILE_SIZE=$(du -h "$PACKAGE_FILE" | cut -f1)
    echo ""
    echo "=========================================================="
    echo -e "${GREEN}✅ Package created successfully!${NC}"
    echo ""
    echo "📦 Package: $PACKAGE_FILE"
    echo "📊 Size: $FILE_SIZE"
    echo ""
    echo "📋 Package includes:"
    echo "  ✓ All source code"
    echo "  ✓ Documentation files"
    echo "  ✓ Installation scripts"
    echo "  ✓ Template files"
    echo "  ✓ .env.example files (without real API keys)"
    echo ""
    echo "📋 Package excludes:"
    echo "  ✗ node_modules (will be installed by recipient)"
    echo "  ✗ venv (will be created by recipient)"
    echo "  ✗ .env files with real API keys"
    echo "  ✗ Build artifacts and logs"
    echo "  ✗ Generated documents"
    echo ""
    echo "📤 Next steps:"
    echo "  1. Test the package by extracting it in a new location"
    echo "  2. Run fresh_install.sh to verify installation works"
    echo "  3. Share the package with recipients"
    echo ""
    echo "📝 Recipients should:"
    echo "  1. Extract the zip file"
    echo "  2. Read README_FIRST.md"
    echo "  3. Get Gemini API key from https://makersuite.google.com/app/apikey"
    echo "  4. Run ./fresh_install.sh"
    echo "  5. Start services with ./unified_ai_chat/start_all_different_ports.sh"
    echo "=========================================================="
else
    echo -e "${RED}❌ Failed to create package${NC}"
    exit 1
fi

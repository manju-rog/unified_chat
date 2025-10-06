#!/bin/bash

# 🚀 AI Absence & SOW - Production Build Script
# This script creates production-ready builds for all components

set -e

echo "🚀 Starting production build process..."
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create deployment directory
echo -e "${BLUE}📁 Creating deployment directory...${NC}"
mkdir -p deploy/dist
mkdir -p deploy/dist/backend
mkdir -p deploy/dist/frontend
mkdir -p deploy/dist/absence-service
mkdir -p deploy/dist/sow-engine
mkdir -p deploy/dist/configs

echo -e "${GREEN}✅ Deployment directory created${NC}"

# Build Spring Boot JAR
echo -e "${BLUE}🔨 Building Spring Boot JAR file...${NC}"
cd ai_absence-ai_absence_mi/backend/absence-management

# Clean and build
./mvnw clean package -DskipTests

# Copy JAR to deployment
cp target/*.jar ../../../deploy/dist/absence-service/absence-management.jar

echo -e "${GREEN}✅ Spring Boot JAR created: absence-management.jar${NC}"

cd ../../..

# Build React Frontend
echo -e "${BLUE}🔨 Building React production bundle...${NC}"
cd unified_ai_chat/frontend

# Install dependencies and build
npm install
npm run build

# Copy build to deployment
cp -r build/* ../../deploy/dist/frontend/

echo -e "${GREEN}✅ React build completed${NC}"

cd ../..

# Package Python Backend
echo -e "${BLUE}🔨 Packaging Python FastAPI backend...${NC}"
cd unified_ai_chat/backend

# Create requirements with versions
pip freeze > requirements-prod.txt

# Copy backend files
cp -r app ../../deploy/dist/backend/
cp requirements-prod.txt ../../deploy/dist/backend/
cp run_server.py ../../deploy/dist/backend/
cp .env.example ../../deploy/dist/backend/.env

echo -e "${GREEN}✅ Python backend packaged${NC}"

cd ../..

# Copy SOW Engine
echo -e "${BLUE}🔨 Copying SOW generation engine...${NC}"
cp -r sow_gen_ai/* deploy/dist/sow-engine/

echo -e "${GREEN}✅ SOW engine copied${NC}"

# Create deployment info
echo -e "${BLUE}📋 Creating deployment information...${NC}"
cat > deploy/dist/BUILD_INFO.txt << EOF
AI Absence & SOW System - Production Build
==========================================

Build Date: $(date)
Build Version: 1.0.0
Git Commit: $(git rev-parse --short HEAD 2>/dev/null || echo "N/A")

Components:
- Spring Boot JAR: absence-management.jar
- React Build: frontend/ directory
- FastAPI Backend: backend/ directory  
- SOW Engine: sow-engine/ directory

Deployment Instructions:
1. Upload dist/ directory to server
2. Run deploy/install.sh on server
3. Configure environment variables
4. Start services with deploy/start-services.sh

EOF

echo -e "${GREEN}✅ Build information created${NC}"

# Create checksums for integrity
echo -e "${BLUE}🔐 Creating file checksums...${NC}"
cd deploy/dist
find . -type f -exec sha256sum {} \; > CHECKSUMS.txt
cd ../..

echo -e "${GREEN}✅ Checksums created${NC}"

# Create deployment package
echo -e "${BLUE}📦 Creating deployment package...${NC}"
cd deploy
tar -czf ai-absence-sow-deployment.tar.gz dist/
cd ..

echo -e "${GREEN}✅ Deployment package created: deploy/ai-absence-sow-deployment.tar.gz${NC}"

# Display build summary
echo ""
echo -e "${GREEN}🎉 BUILD COMPLETED SUCCESSFULLY!${NC}"
echo "========================================"
echo -e "${YELLOW}📦 Deployment Package:${NC} deploy/ai-absence-sow-deployment.tar.gz"
echo -e "${YELLOW}📁 Package Size:${NC} $(du -h deploy/ai-absence-sow-deployment.tar.gz | cut -f1)"
echo ""
echo -e "${BLUE}📋 Package Contents:${NC}"
echo "  ├── absence-service/absence-management.jar"
echo "  ├── backend/ (FastAPI application)"
echo "  ├── frontend/ (React build)"
echo "  ├── sow-engine/ (Document generation)"
echo "  ├── configs/ (Configuration templates)"
echo "  └── BUILD_INFO.txt"
echo ""
echo -e "${GREEN}🚀 Ready for deployment to Oracle Cloud!${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Upload ai-absence-sow-deployment.tar.gz to your Oracle Cloud VM"
echo "2. Run the deployment script on the server"
echo "3. Configure your domain and SSL"
echo ""
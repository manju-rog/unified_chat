#!/bin/bash

# Unified AI Chat - Start All Services
# This script starts all required services for the unified chat system

set -e

echo "🚀 Starting Unified AI Chat System..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    echo -e "${YELLOW}Waiting for $name to start...${NC}"
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $name is ready!${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    echo -e "${RED}✗ $name failed to start${NC}"
    return 1
}

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v java &> /dev/null; then
    echo -e "${RED}✗ Java not found. Please install Java 11 or higher.${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm not found. Please install Node.js 14 or higher.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Check if ports are available
echo -e "${BLUE}Checking ports...${NC}"

if check_port 8080; then
    echo -e "${YELLOW}⚠ Port 8080 is already in use (Absence Management)${NC}"
    echo -e "${YELLOW}  Assuming service is already running...${NC}"
else
    echo -e "${GREEN}✓ Port 8080 is available${NC}"
fi

if check_port 5002; then
    echo -e "${RED}✗ Port 5002 is already in use (Unified Backend)${NC}"
    echo -e "${YELLOW}  Please stop the existing service or change the port${NC}"
    exit 1
fi

if check_port 3000; then
    echo -e "${RED}✗ Port 3000 is already in use (React Frontend)${NC}"
    echo -e "${YELLOW}  Please stop the existing service or change the port${NC}"
    exit 1
fi

echo ""

# Start Absence Management Backend (if not running)
if ! check_port 8080; then
    echo -e "${BLUE}Starting Absence Management Backend...${NC}"
    cd ../ai_absence-ai_absence_mi/backend/absence-management
    ./mvnw spring-boot:run > /tmp/absence-backend.log 2>&1 &
    ABSENCE_PID=$!
    echo $ABSENCE_PID > /tmp/absence-backend.pid
    cd - > /dev/null
    
    wait_for_service "http://localhost:8080/api/employees" "Absence Management Backend"
else
    echo -e "${GREEN}✓ Absence Management Backend already running${NC}"
fi

echo ""

# Start Unified Chat Backend
echo -e "${BLUE}Starting Unified Chat Backend...${NC}"
cd backend

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating from example...${NC}"
    cp .env.example .env
    echo -e "${RED}✗ Please edit backend/.env and add your GEMINI_API_KEY${NC}"
    exit 1
fi

# Check if dependencies are installed
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

python run_server.py > /tmp/unified-backend.log 2>&1 &
UNIFIED_PID=$!
echo $UNIFIED_PID > /tmp/unified-backend.pid
cd - > /dev/null

wait_for_service "http://localhost:5002/api/health" "Unified Chat Backend"

echo ""

# Start React Frontend
echo -e "${BLUE}Starting React Frontend...${NC}"
cd frontend

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env from example...${NC}"
    cp .env.example .env
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing npm dependencies...${NC}"
    npm install
fi

npm start > /tmp/unified-frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > /tmp/unified-frontend.pid
cd - > /dev/null

wait_for_service "http://localhost:3000" "React Frontend"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ All services started successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Services running:${NC}"
echo -e "  • Absence Management: ${GREEN}http://localhost:8080${NC}"
echo -e "  • Unified Backend:    ${GREEN}http://localhost:5002${NC}"
echo -e "  • React Frontend:     ${GREEN}http://localhost:3000${NC}"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo -e "  • Absence Backend:  tail -f /tmp/absence-backend.log"
echo -e "  • Unified Backend:  tail -f /tmp/unified-backend.log"
echo -e "  • React Frontend:   tail -f /tmp/unified-frontend.log"
echo ""
echo -e "${BLUE}To stop all services:${NC}"
echo -e "  ./stop_all.sh"
echo ""
echo -e "${GREEN}Opening browser...${NC}"
sleep 3
open http://localhost:3000 || xdg-open http://localhost:3000 || echo "Please open http://localhost:3000 in your browser"

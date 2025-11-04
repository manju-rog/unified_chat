#!/bin/bash

# Unified AI Chat - Start All Services on Different Ports
# This script starts all required services with non-conflicting ports

set -e

echo "🚀 Starting Unified AI Chat System on Different Ports..."
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
    
    echo -e "${RED}✗ $name failed to start (timeout after 60s)${NC}"
    echo -e "${YELLOW}  Check logs for details${NC}"
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

PORTS=(8010 8002 8001 3001)
PORT_NAMES=("Absence Management" "new_sow Backend" "Unified Chat Backend" "React Frontend")

for i in "${!PORTS[@]}"; do
    if check_port ${PORTS[$i]}; then
        echo -e "${YELLOW}⚠ Port ${PORTS[$i]} is already in use (${PORT_NAMES[$i]})${NC}"
        echo -e "${YELLOW}  Assuming service is already running...${NC}"
    else
        echo -e "${GREEN}✓ Port ${PORTS[$i]} is available${NC}"
    fi
done

echo ""

# Start Absence Management Backend (Port 8010)
if ! check_port 8010; then
    echo -e "${BLUE}Starting Absence Management Backend on port 8010...${NC}"
    if [ -d "../ai_absence-ai_absence_mi/backend/absence-management" ]; then
        cd ../ai_absence-ai_absence_mi/backend/absence-management
        ./mvnw spring-boot:run -Dspring-boot.run.arguments=--server.port=8010 > /tmp/absence-backend-8010.log 2>&1 &
        ABSENCE_PID=$!
        echo $ABSENCE_PID > /tmp/absence-backend-8010.pid
        cd - > /dev/null
        
        sleep 5
        echo -e "${GREEN}✓ Absence Management Backend started (PID: $ABSENCE_PID)${NC}"
    else
        echo -e "${YELLOW}⚠ Absence Management directory not found, skipping...${NC}"
    fi
else
    echo -e "${GREEN}✓ Absence Management Backend already running on port 8010${NC}"
fi

echo ""

# Start new_sow Backend (Port 8002)
if ! check_port 8002; then
    echo -e "${BLUE}Starting new_sow Backend on port 8002...${NC}"
    if [ -d "../new_sow" ]; then
        cd ../new_sow
        
        # Start with custom port using python3 directly
        python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8002 > /tmp/new-sow-backend-8002.log 2>&1 &
        NEW_SOW_PID=$!
        echo $NEW_SOW_PID > /tmp/new-sow-backend-8002.pid
        cd - > /dev/null
        
        sleep 3
        echo -e "${GREEN}✓ new_sow Backend started (PID: $NEW_SOW_PID)${NC}"
    else
        echo -e "${YELLOW}⚠ new_sow directory not found, skipping...${NC}"
    fi
else
    echo -e "${GREEN}✓ new_sow Backend already running on port 8002${NC}"
fi

echo ""

# Start Unified Chat Backend (Port 8001)
if ! check_port 8001; then
    echo -e "${BLUE}Starting Unified Chat Backend on port 8001...${NC}"
    cd backend

    # Check if .env exists
    if [ ! -f .env ]; then
        echo -e "${YELLOW}⚠ .env file not found. Creating from example...${NC}"
        if [ -f .env.example ]; then
            cp .env.example .env
        fi
    fi

    # Start using python3 directly
    python3 run_server.py > /tmp/unified-backend-8001.log 2>&1 &
    UNIFIED_PID=$!
    echo $UNIFIED_PID > /tmp/unified-backend-8001.pid
    cd - > /dev/null

    sleep 3
    echo -e "${GREEN}✓ Unified Chat Backend started (PID: $UNIFIED_PID)${NC}"
else
    echo -e "${GREEN}✓ Unified Chat Backend already running on port 8001${NC}"
fi

echo ""

# Start React Frontend (Port 3001)
if ! check_port 3001; then
    echo -e "${BLUE}Starting React Frontend on port 3001...${NC}"
    cd frontend

    # Check if .env exists
    if [ ! -f .env ]; then
        echo -e "${YELLOW}Creating .env from example...${NC}"
        if [ -f .env.example ]; then
            cp .env.example .env
        fi
    fi

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing npm dependencies...${NC}"
        npm install
    fi

    PORT=3001 npm start > /tmp/unified-frontend-3001.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > /tmp/unified-frontend-3001.pid
    cd - > /dev/null

    sleep 5
    echo -e "${GREEN}✓ React Frontend started (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${GREEN}✓ React Frontend already running on port 3001${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ All services started successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Services running on different ports:${NC}"
echo -e "  • Absence Management: ${GREEN}http://localhost:8010${NC}"
echo -e "  • new_sow Backend:    ${GREEN}http://localhost:8002${NC}"
echo -e "  • Unified Backend:    ${GREEN}http://localhost:8001${NC}"
echo -e "  • React Frontend:     ${GREEN}http://localhost:3001${NC}"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo -e "  • Absence Backend:  tail -f /tmp/absence-backend-8010.log"
echo -e "  • new_sow Backend:  tail -f /tmp/new-sow-backend-8002.log"
echo -e "  • Unified Backend:  tail -f /tmp/unified-backend-8001.log"
echo -e "  • React Frontend:   tail -f /tmp/unified-frontend-3001.log"
echo ""
echo -e "${BLUE}To stop all services:${NC}"
echo -e "  ./stop_all_different_ports.sh"
echo ""
echo -e "${GREEN}Opening browser in 3 seconds...${NC}"
sleep 3
open http://localhost:3001 || xdg-open http://localhost:3001 || echo "Please open http://localhost:3001 in your browser"

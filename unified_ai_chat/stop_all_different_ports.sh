#!/bin/bash

# Unified AI Chat - Stop All Services on Different Ports

echo "🛑 Stopping Unified AI Chat System..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to stop service by PID file
stop_service() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping $service_name (PID: $PID)...${NC}"
            kill $PID
            sleep 2
            if ps -p $PID > /dev/null 2>&1; then
                echo -e "${RED}Force stopping $service_name...${NC}"
                kill -9 $PID
            fi
            echo -e "${GREEN}✓ $service_name stopped${NC}"
        else
            echo -e "${YELLOW}⚠ $service_name not running${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠ $service_name PID file not found${NC}"
    fi
}

# Function to stop by port
stop_by_port() {
    local port=$1
    local service_name=$2
    
    PID=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo -e "${YELLOW}Stopping $service_name on port $port (PID: $PID)...${NC}"
        kill $PID 2>/dev/null
        sleep 2
        if lsof -ti:$port > /dev/null 2>&1; then
            echo -e "${RED}Force stopping $service_name...${NC}"
            kill -9 $PID 2>/dev/null
        fi
        echo -e "${GREEN}✓ $service_name stopped${NC}"
    else
        echo -e "${YELLOW}⚠ No process found on port $port${NC}"
    fi
}

# Stop services by PID files
stop_service "/tmp/unified-frontend-3001.pid" "React Frontend"
stop_service "/tmp/unified-backend-8001.pid" "Unified Chat Backend"
stop_service "/tmp/new-sow-backend-8002.pid" "new_sow Backend"
stop_service "/tmp/absence-backend-8010.pid" "Absence Management Backend"

echo ""
echo -e "${YELLOW}Checking for any remaining processes on ports...${NC}"

# Stop any remaining processes on the ports
stop_by_port 3001 "React Frontend"
stop_by_port 8001 "Unified Chat Backend"
stop_by_port 8002 "new_sow Backend"
stop_by_port 8010 "Absence Management Backend"

# Clean up log files (optional)
echo ""
echo -e "${YELLOW}Cleaning up log files...${NC}"
rm -f /tmp/absence-backend-8010.log
rm -f /tmp/new-sow-backend-8002.log
rm -f /tmp/unified-backend-8001.log
rm -f /tmp/unified-frontend-3001.log

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ All services stopped${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"

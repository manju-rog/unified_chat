#!/bin/bash

# Unified AI Chat - Stop All Services

echo "🛑 Stopping Unified AI Chat System..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to stop service by PID file
stop_service() {
    local pid_file=$1
    local name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping $name (PID: $pid)...${NC}"
            kill $pid
            sleep 2
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${RED}Force killing $name...${NC}"
                kill -9 $pid
            fi
            echo -e "${GREEN}✓ $name stopped${NC}"
        else
            echo -e "${YELLOW}⚠ $name not running${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠ No PID file for $name${NC}"
    fi
}

# Stop services
stop_service "/tmp/unified-frontend.pid" "React Frontend"
stop_service "/tmp/unified-backend.pid" "Unified Chat Backend"
stop_service "/tmp/absence-backend.pid" "Absence Management Backend"

# Clean up log files
echo ""
echo -e "${YELLOW}Cleaning up log files...${NC}"
rm -f /tmp/absence-backend.log
rm -f /tmp/unified-backend.log
rm -f /tmp/unified-frontend.log

echo ""
echo -e "${GREEN}✓ All services stopped${NC}"

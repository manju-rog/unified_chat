#!/bin/bash

# Gemini Orchestrator - Start All Services
# This script starts both backend and frontend servers

echo "=========================================="
echo "Starting Gemini Orchestrator"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend .env exists
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}Warning: backend/.env not found${NC}"
    echo "Please create backend/.env with your GEMINI_API_KEY"
    exit 1
fi

# Check if frontend .env.local exists
if [ ! -f "frontend/.env.local" ]; then
    echo -e "${YELLOW}Creating frontend/.env.local...${NC}"
    echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:8000" > frontend/.env.local
fi

echo -e "${BLUE}Starting Backend Server...${NC}"
echo "Location: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""

# Start backend in background
cd backend
uvicorn app.main:app --reload --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend started successfully${NC}"
else
    echo -e "${YELLOW}⚠ Backend may still be starting...${NC}"
fi

echo ""
echo -e "${BLUE}Starting Frontend Server...${NC}"
echo "Location: http://localhost:3000"
echo ""

# Start frontend in background
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "Waiting for frontend to start..."
sleep 5

echo ""
echo "=========================================="
echo -e "${GREEN}Gemini Orchestrator Started!${NC}"
echo "=========================================="
echo ""
echo "Access Points:"
echo "  • Frontend UI:  http://localhost:3000"
echo "  • Backend API:  http://localhost:8000"
echo "  • API Docs:     http://localhost:8000/docs"
echo ""
echo "Process IDs:"
echo "  • Backend:  $BACKEND_PID"
echo "  • Frontend: $FRONTEND_PID"
echo ""
echo "Logs:"
echo "  • Backend:  tail -f backend.log"
echo "  • Frontend: tail -f frontend.log"
echo ""
echo "To stop all services:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo -e "${YELLOW}Press Ctrl+C to view logs, or open http://localhost:3000 in your browser${NC}"
echo ""

# Save PIDs to file for easy cleanup
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

# Follow logs
tail -f backend.log frontend.log

#!/bin/bash

echo "🚀 Starting All Services..."
echo ""

# Start Spring Boot
echo "1️⃣  Starting Spring Boot Absence Service (port 8080)..."
cd ai_absence-ai_absence_mi/backend/absence-management
./mvnw spring-boot:run > ../../../spring-boot.log 2>&1 &
SPRING_PID=$!
cd ../../..
echo "   ✓ Started (PID: $SPRING_PID)"
echo "   Waiting 30 seconds for initialization..."
sleep 30

# Start FastAPI
echo ""
echo "2️⃣  Starting FastAPI Orchestrator (port 8000)..."
cd unified_ai_chat/backend
uvicorn app.main:app --port 8000 > ../../fastapi.log 2>&1 &
FASTAPI_PID=$!
cd ../..
echo "   ✓ Started (PID: $FASTAPI_PID)"
sleep 3

# Start React Frontend
echo ""
echo "3️⃣  Starting React Frontend (port 3000)..."
cd unified_ai_chat/frontend
npm start > ../../react.log 2>&1 &
REACT_PID=$!
cd ../..
echo "   ✓ Started (PID: $REACT_PID)"
echo "   Waiting 10 seconds for React to compile..."
sleep 10

echo ""
echo "=========================================="
echo "✅ ALL SERVICES RUNNING!"
echo "=========================================="
echo ""
echo "🌐 Open in browser: http://localhost:3000"
echo ""
echo "Services:"
echo "  • React Frontend:    http://localhost:3000"
echo "  • FastAPI Backend:   http://localhost:8000"
echo "  • Spring Boot API:   http://localhost:8080"
echo ""
echo "Logs:"
echo "  • Spring Boot: tail -f spring-boot.log"
echo "  • FastAPI:     tail -f fastapi.log"
echo "  • React:       tail -f react.log"
echo ""
echo "To stop all services:"
echo "  pkill -f 'spring-boot:run'"
echo "  pkill -f 'uvicorn app.main:app'"
echo "  pkill -f 'react-scripts start'"
echo ""
echo "PIDs: $SPRING_PID $FASTAPI_PID $REACT_PID" > .service_pids
echo "PIDs saved to .service_pids"
echo ""

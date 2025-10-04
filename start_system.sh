#!/bin/bash

echo "🚀 Starting the Unified AI Chat System..."
echo ""
echo "Step 1: Starting Spring Boot Absence Service..."
echo "----------------------------------------"

# Start Spring Boot in background
cd ai_absence-ai_absence_mi/backend/absence-management
./mvnw spring-boot:run > ../../../spring-boot.log 2>&1 &
SPRING_PID=$!
cd ../../..

echo "✓ Spring Boot started (PID: $SPRING_PID)"
echo "  Waiting 30 seconds for Spring Boot to initialize..."
sleep 30

echo ""
echo "Step 2: Starting FastAPI Orchestrator..."
echo "----------------------------------------"

# Start FastAPI
cd unified_ai_chat/backend
uvicorn app.main:app --port 8000 > ../../fastapi.log 2>&1 &
FASTAPI_PID=$!
cd ../..

echo "✓ FastAPI started (PID: $FASTAPI_PID)"
echo ""
echo "=========================================="
echo "✅ SYSTEM READY!"
echo "=========================================="
echo ""
echo "FastAPI Orchestrator: http://localhost:8000"
echo "Spring Boot Service:  http://localhost:8080"
echo ""
echo "Logs:"
echo "  - Spring Boot: spring-boot.log"
echo "  - FastAPI:     fastapi.log"
echo ""
echo "To stop the system:"
echo "  kill $SPRING_PID $FASTAPI_PID"
echo ""
echo "PIDs saved to .system_pids"
echo "$SPRING_PID $FASTAPI_PID" > .system_pids

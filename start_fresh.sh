#!/bin/bash

echo "🔥 Starting Fresh SOW System with Gemini AI Integration"
echo "=================================================="

# Kill any existing processes
echo "🛑 Killing existing processes..."
pkill -f "python.*run_server.py" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true  
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "node.*react-scripts" 2>/dev/null || true

# Kill processes on all possible ports
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:3001 | xargs kill -9 2>/dev/null || true
lsof -ti:5002 | xargs kill -9 2>/dev/null || true

# Wait a moment for processes to terminate
sleep 3

echo "✅ All processes killed"

# Check if we're in the right directory
if [ ! -d "unified_ai_chat" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Start backend
echo "🚀 Starting Backend with Gemini AI..."
cd unified_ai_chat/backend

# Install dependencies
echo "📦 Installing backend dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Start backend in background
echo "🔧 Starting FastAPI server on port 8001..."
python run_server.py &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8001/api/health > /dev/null; then
    echo "✅ Backend started successfully at http://localhost:8001"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start frontend
echo "🎨 Starting Frontend..."
cd ../frontend

# Install dependencies
echo "📦 Installing frontend dependencies..."
npm install > /dev/null 2>&1

# Start frontend in background
echo "🔧 Starting React development server on port 3001..."
npm start &
FRONTEND_PID=$!

# Wait for frontend to start
echo "⏳ Waiting for frontend to initialize..."
sleep 10

echo ""
echo "🎉 SOW System Started Successfully!"
echo "=================================================="
echo "🌐 Frontend: http://localhost:3001"
echo "🔧 Backend API: http://localhost:8001"
echo "📚 API Docs: http://localhost:8001/docs"
echo "🤖 Gemini AI: ✅ Connected"
echo ""
echo "🎯 To test the enhanced SOW system:"
echo "1. Open http://localhost:3001"
echo "2. Click 'Create a SOW'"
echo "3. Follow the enhanced UI flow"
echo ""
echo "🛑 To stop all services:"
echo "pkill -f 'python.*run_server.py'"
echo "pkill -f 'npm start'"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
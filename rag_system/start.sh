#!/bin/bash

# 🚀 Ultimate RAG System v2.1 - Startup Script
# Starts both backend and frontend

echo "================================="
echo "🚀 Ultimate RAG System v2.1"
echo "================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo "✅ Please edit .env and add your ANTHROPIC_API_KEY"
    echo "Then run this script again."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo ""
echo "Starting backend server..."
echo "Backend will run on: http://localhost:8000"
echo ""

# Start backend in background
cd backend
python -m app.main &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

echo ""
echo "Starting frontend UI..."
echo "Frontend will run on: http://localhost:8501"
echo ""

# Start frontend
cd ../frontend
streamlit run app.py &
FRONTEND_PID=$!

echo ""
echo "================================="
echo "✅ System Started!"
echo "================================="
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:8501"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both services"
echo "================================="

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait

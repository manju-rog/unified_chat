#!/bin/bash
cd backend
echo "Starting Gemini Orchestrator Backend..."
echo "API: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo ""
uvicorn app.main:app --reload --port 8000

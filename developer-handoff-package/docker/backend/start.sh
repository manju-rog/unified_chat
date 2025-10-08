#!/bin/bash

# 🚀 FastAPI Backend Startup Script
# Production-ready Gunicorn configuration

set -e

echo "🚀 Starting AI Absence & SOW Backend..."

# Wait for dependencies (if needed)
echo "⏳ Checking dependencies..."

# Start Gunicorn with optimized settings
exec gunicorn app.main:app \
    --bind 0.0.0.0:5002 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 300 \
    --keep-alive 5 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance
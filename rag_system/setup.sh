#!/bin/bash

# 🚀 Ultimate RAG System v2.1 - Setup Script
# Installs all dependencies and downloads models

echo "================================="
echo "🚀 Ultimate RAG System v2.1"
echo "   Setup & Installation"
echo "================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "📦 Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt

# Download spaCy model
echo ""
echo "📦 Downloading spaCy English model..."
python -m spacy download en_core_web_sm

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY"
    echo "   Get your API key from: https://console.anthropic.com/"
else
    echo ""
    echo "✅ .env file already exists"
fi

# Create data directories
echo ""
echo "📁 Creating data directories..."
mkdir -p backend/data/chroma
mkdir -p backend/data/uploads
mkdir -p backend/data/cache
echo "✅ Directories created"

echo ""
echo "================================="
echo "✅ Setup Complete!"
echo "================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your ANTHROPIC_API_KEY"
echo "2. Run: ./start.sh"
echo ""
echo "Or start manually:"
echo "  Terminal 1: cd backend && python -m app.main"
echo "  Terminal 2: cd frontend && streamlit run app.py"
echo ""
echo "================================="

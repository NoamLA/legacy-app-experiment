#!/bin/bash

echo "🚀 Starting Legacy Interview App Backend with Virtual Environment..."

# Check if virtual environment exists
if [ ! -d "legacy-venv" ]; then
    echo "❌ Virtual environment not found. Run 'python setup.py' first."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source legacy-venv/bin/activate

# Check if we're in the virtual environment
if [ "$VIRTUAL_ENV" != "" ]; then
    echo "✅ Virtual environment activated: $(basename $VIRTUAL_ENV)"
else
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Change to backend directory
if [ -d "backend" ]; then
    cd backend
    echo "📁 Changed to backend directory"
else
    echo "❌ Backend directory not found"
    exit 1
fi

# Load environment variables from .env file
if [ -f "../.env" ]; then
    echo "📄 Loading environment variables from .env"
    export $(grep -v '^#' ../.env | xargs)
else
    echo "⚠️  .env file not found - some features may not work"
fi

# Set environment variables
export AGNO_TELEMETRY=false

# Verify OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY not found in environment variables"
    echo "Please check your .env file contains: OPENAI_API_KEY=your_key_here"
    exit 1
else
    echo "✅ OpenAI API key loaded successfully"
fi

# Start the FastAPI server
echo "📡 Starting FastAPI server on http://localhost:8000"
echo "📖 API docs will be available at http://localhost:8000/docs"
echo "🛑 Press Ctrl+C to stop the server"

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

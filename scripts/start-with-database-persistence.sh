#!/bin/bash
# Start Legacy Interview App with PostgreSQL persistence enabled

echo "🚀 Starting Legacy Interview App with Database Persistence..."

# Check if PostgreSQL is running on port 5433
if ! pg_isready -h localhost -p 5433 >/dev/null 2>&1; then
    echo "❌ PostgreSQL is not running on port 5433. Please start it first."
    echo "   Check your PostgreSQL installation and ensure it's running on port 5433"
    exit 1
fi

echo "✅ PostgreSQL is running on port 5433"

# Set environment variables for database mode
export USE_DATABASE=true
export DATABASE_URL="postgresql://legacy_user:legacy_pass@localhost:5433/legacy_interview_dev"
export LEGACY_ENV=development

# Load additional environment variables if .env.development exists
if [ -f .env.development ]; then
    echo "📝 Loading environment from .env.development"
    export $(cat .env.development | grep -v '^#' | xargs)
fi

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set. AI features will not work."
    echo "   Please set your OpenAI API key in .env.development"
fi

echo "🗄️ Database persistence: ENABLED"
echo "🔧 Database URL: postgresql://legacy_user:***@localhost:5433/legacy_interview_dev"
echo "🌐 Backend will be available at: http://localhost:8000"
echo ""

# Activate virtual environment and start backend
source legacy-venv/bin/activate
python backend/main.py

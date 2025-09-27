#!/bin/bash
# Start Legacy Interview App with PostgreSQL Database

echo "🚀 Starting Legacy Interview App with Database..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env.development exists
if [ ! -f .env.development ]; then
    echo "📝 Creating .env.development from template..."
    cp env-template.txt .env.development
    echo "⚠️  Please update OPENAI_API_KEY in .env.development"
fi

# Start PostgreSQL database
echo "🗄️ Starting PostgreSQL database..."
docker-compose up -d postgres

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
timeout=60
while [ $timeout -gt 0 ]; do
    if docker-compose exec -T postgres pg_isready -U legacy_user -d legacy_interview_dev >/dev/null 2>&1; then
        echo "✅ Database is ready!"
        break
    fi
    sleep 2
    timeout=$((timeout - 2))
done

if [ $timeout -le 0 ]; then
    echo "❌ Database failed to start within 60 seconds"
    exit 1
fi

# Load environment variables
if [ -f .env.development ]; then
    export $(cat .env.development | grep -v '^#' | xargs)
fi

# Start the backend application
echo "🔧 Starting backend application..."
echo "📋 Database connection: postgresql://legacy_user:***@localhost:5432/legacy_interview_dev"
echo "🌐 Backend will be available at: http://localhost:8000"
echo ""

# Activate virtual environment and start backend
source legacy-venv/bin/activate
python backend/main.py

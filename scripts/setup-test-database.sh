#!/bin/bash
# Setup Test Database Infrastructure
# Creates isolated PostgreSQL instances for testing

set -e

echo "🐳 Setting up test database infrastructure..."

# Navigate to project root
cd "$(dirname "$0")/.."

# Stop any existing test containers
echo "🛑 Stopping existing test containers..."
docker-compose -f docker/docker-compose.test.yml down --volumes --remove-orphans 2>/dev/null || true

# Start test databases
echo "🚀 Starting test PostgreSQL databases..."
docker-compose -f docker/docker-compose.test.yml up -d

# Wait for databases to be ready
echo "⏳ Waiting for test databases to be ready..."

# Wait for basic test database
echo "   Waiting for basic test database (port 5434)..."
timeout 30 bash -c 'until docker-compose -f docker/docker-compose.test.yml exec test-postgres pg_isready -U legacy_test_user -d legacy_interview_test; do sleep 1; done'

# Wait for full-featured test database
echo "   Waiting for full-featured test database (port 5435)..."
timeout 30 bash -c 'until docker-compose -f docker/docker-compose.test.yml exec test-postgres-with-extensions pg_isready -U legacy_test_user -d legacy_interview_test_full; do sleep 1; done'

echo "✅ Test databases are ready!"

# Test connections
echo "🔍 Testing database connections..."

# Test basic database
PGPASSWORD=legacy_test_pass psql -h localhost -p 5434 -U legacy_test_user -d legacy_interview_test -c "SELECT 'Basic test DB connected' as status;" || {
    echo "❌ Failed to connect to basic test database"
    exit 1
}

# Test full-featured database
PGPASSWORD=legacy_test_pass psql -h localhost -p 5435 -U legacy_test_user -d legacy_interview_test_full -c "SELECT 'Full test DB connected' as status;" || {
    echo "❌ Failed to connect to full-featured test database"
    exit 1
}

echo ""
echo "🎯 Test Database Setup Complete!"
echo ""
echo "Available test databases:"
echo "  📋 Basic Test DB:     localhost:5434 (legacy_interview_test)"
echo "  🚀 Full-Featured DB:  localhost:5435 (legacy_interview_test_full)"
echo ""
echo "Environment variables for testing:"
echo "  export TEST_DB_HOST=localhost"
echo "  export TEST_DB_PORT=5434"
echo "  export TEST_DB_NAME=legacy_interview_test"
echo "  export TEST_DB_USER=legacy_test_user"
echo "  export TEST_DB_PASS=legacy_test_pass"
echo ""
echo "To run tests:"
echo "  pytest tests/ -v --tb=short"
echo ""
echo "To stop test databases:"
echo "  docker-compose -f docker/docker-compose.test.yml down --volumes"

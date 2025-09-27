#!/bin/bash
# Run Real Database Integration Tests
# Sets up PostgreSQL test database and runs comprehensive integration tests

set -e

echo "🧪 Running Real Database Integration Tests"
echo "========================================"

# Navigate to project root
cd "$(dirname "$0")/.."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed"
    echo "   Please install Docker to run database integration tests"
    exit 1
fi

# Check if pytest is available
if ! python -m pytest --version &> /dev/null; then
    echo "❌ pytest is not available"
    echo "   Please install pytest: pip install pytest"
    exit 1
fi

# Set up test database
echo "🐳 Setting up test database..."
./scripts/setup-test-database.sh

# Wait a moment for database to be fully ready
echo "⏳ Waiting for database to be fully ready..."
sleep 5

# Set environment variables for testing
export LEGACY_ENV=test
export USE_POSTGRES=true
export USE_DATABASE=true
export TEST_DB_HOST=localhost
export TEST_DB_PORT=5434
export TEST_DB_NAME=legacy_interview_test
export TEST_DB_USER=legacy_test_user
export TEST_DB_PASS=legacy_test_pass

# Activate virtual environment if available
if [ -f "legacy-venv/bin/activate" ]; then
    echo "🔧 Activating virtual environment..."
    source legacy-venv/bin/activate
fi

# Run database integration tests
echo ""
echo "🧪 Running Real Database Integration Tests..."
echo ""

# Run tests with specific configuration
python -m pytest \
    tests/backend/test_database/test_real_database_integration.py \
    tests/backend/test_agents/test_real_agent_integration.py \
    -v \
    --tb=short \
    --confcutdir=tests \
    -p no:warnings \
    --color=yes \
    -m "database and integration" \
    --durations=10

test_exit_code=$?

echo ""
echo "📊 Test Results Summary:"
echo "========================"

if [ $test_exit_code -eq 0 ]; then
    echo "✅ All real database integration tests passed!"
    echo ""
    echo "🎯 What was tested:"
    echo "  • Real PostgreSQL database operations"
    echo "  • Project CRUD with actual database persistence"
    echo "  • Interview responses and themes storage"
    echo "  • Agent session management with PostgresDb"
    echo "  • Multi-agent workflow integration"
    echo "  • Database performance and constraints"
    echo "  • Memory persistence across agent interactions"
    echo "  • Session isolation between projects"
    echo ""
else
    echo "❌ Some tests failed (exit code: $test_exit_code)"
    echo ""
    echo "💡 Troubleshooting tips:"
    echo "  • Check if test database is running: docker ps"
    echo "  • Verify database connection: psql -h localhost -p 5434 -U legacy_test_user -d legacy_interview_test"
    echo "  • Check test logs above for specific errors"
    echo "  • Restart test database: ./scripts/setup-test-database.sh"
    echo ""
fi

# Optional: Run unit tests as well for comparison
read -p "🤔 Run unit tests for comparison? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🧪 Running Unit Tests for Comparison..."
    echo ""
    
    python -m pytest \
        tests/backend/test_database/test_config.py \
        tests/backend/test_agents/test_planner_agent.py \
        tests/backend/test_agents/test_prober_agent.py \
        -v \
        --tb=short \
        -m "unit" \
        --color=yes
fi

# Clean up test database
echo ""
echo "🧹 Cleaning up test database..."
docker-compose -f docker/docker-compose.test.yml down --volumes --remove-orphans

echo ""
echo "✨ Real database integration testing complete!"
echo ""

exit $test_exit_code

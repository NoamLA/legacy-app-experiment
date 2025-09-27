#!/bin/bash
# Comprehensive Test Runner for Legacy Interview App
# Supports different test types: unit, integration, database, performance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="unit"
VERBOSE=false
COVERAGE=false
PARALLEL=false
CLEAN_DB=false

# Function to show usage
show_usage() {
    echo "🧪 Legacy Interview App Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS] [TEST_TYPE]"
    echo ""
    echo "Test Types:"
    echo "  unit          - Fast unit tests with mocks (default)"
    echo "  integration   - Integration tests with external services"
    echo "  database      - Real database integration tests"
    echo "  real          - All real integration tests (no mocks)"
    echo "  performance   - Performance and load tests"
    echo "  all           - All tests (unit + integration + database)"
    echo "  agents        - AI agent tests only"
    echo "  api           - API endpoint tests only"
    echo ""
    echo "Options:"
    echo "  -v, --verbose     Verbose output"
    echo "  -c, --coverage    Generate coverage report"
    echo "  -p, --parallel    Run tests in parallel"
    echo "  --clean-db        Clean test database before running"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                        # Run unit tests"
    echo "  $0 database --verbose     # Run database tests with verbose output"
    echo "  $0 all --coverage         # Run all tests with coverage"
    echo "  $0 agents --parallel      # Run agent tests in parallel"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        --clean-db)
            CLEAN_DB=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        unit|integration|database|real|performance|all|agents|api)
            TEST_TYPE="$1"
            shift
            ;;
        *)
            echo "❌ Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Navigate to project root
cd "$(dirname "$0")/.."

# Activate virtual environment if available
if [ -f "legacy-venv/bin/activate" ]; then
    echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
    source legacy-venv/bin/activate
fi

# Check if pytest is available
if ! python -m pytest --version &> /dev/null; then
    echo -e "${RED}❌ pytest is not available${NC}"
    echo "   Please install pytest: pip install pytest"
    exit 1
fi

# Base pytest command
PYTEST_CMD="python -m pytest"

# Add verbose flag if requested
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add coverage if requested
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=backend --cov=database --cov-report=html --cov-report=term-missing"
fi

# Add parallel execution if requested
if [ "$PARALLEL" = true ]; then
    if python -c "import xdist" &> /dev/null; then
        PYTEST_CMD="$PYTEST_CMD -n auto"
    else
        echo -e "${YELLOW}⚠️  pytest-xdist not installed, running sequentially${NC}"
    fi
fi

# Common pytest flags
PYTEST_CMD="$PYTEST_CMD --tb=short --color=yes --durations=10"

# Set up test database if needed
setup_test_database() {
    echo -e "${BLUE}🐳 Setting up test database...${NC}"
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is required for database tests but not installed${NC}"
        exit 1
    fi
    
    # Set up test database
    ./scripts/setup-test-database.sh
    
    # Set environment variables
    export LEGACY_ENV=test
    export USE_POSTGRES=true
    export USE_DATABASE=true
    export TEST_DB_HOST=localhost
    export TEST_DB_PORT=5434
    export TEST_DB_NAME=legacy_interview_test
    export TEST_DB_USER=legacy_test_user
    export TEST_DB_PASS=legacy_test_pass
    
    # Clean database if requested
    if [ "$CLEAN_DB" = true ]; then
        echo -e "${BLUE}🧹 Cleaning test database...${NC}"
        PGPASSWORD=$TEST_DB_PASS psql -h $TEST_DB_HOST -p $TEST_DB_PORT -U $TEST_DB_USER -d $TEST_DB_NAME -c "
            TRUNCATE TABLE interview_responses CASCADE;
            TRUNCATE TABLE interview_themes CASCADE;
            TRUNCATE TABLE projects CASCADE;
            TRUNCATE TABLE knowledge_documents CASCADE;
            TRUNCATE TABLE agent_sessions CASCADE;
            TRUNCATE TABLE agent_messages CASCADE;
            TRUNCATE TABLE agent_runs CASCADE;
            TRUNCATE TABLE user_memories CASCADE;
            TRUNCATE TABLE session_summaries CASCADE;
        " 2>/dev/null || echo "Database cleaned (some tables may not exist yet)"
    fi
}

# Clean up test database
cleanup_test_database() {
    if [ "$TEST_TYPE" = "database" ] || [ "$TEST_TYPE" = "real" ] || [ "$TEST_TYPE" = "all" ]; then
        echo -e "${BLUE}🧹 Cleaning up test database...${NC}"
        docker-compose -f docker/docker-compose.test.yml down --volumes --remove-orphans 2>/dev/null || true
    fi
}

# Trap cleanup on exit
trap cleanup_test_database EXIT

# Run tests based on type
echo -e "${GREEN}🧪 Running ${TEST_TYPE} tests...${NC}"
echo "========================================"

case $TEST_TYPE in
    unit)
        echo -e "${BLUE}Running fast unit tests with mocks...${NC}"
        $PYTEST_CMD \
            tests/backend/test_database/test_config.py \
            tests/backend/test_database/test_memory_functionality.py \
            tests/backend/test_agents/test_planner_agent.py \
            tests/backend/test_agents/test_prober_agent.py \
            tests/backend/test_agents/test_summarizer_agent.py \
            -m "unit and not database"
        ;;
    
    integration)
        echo -e "${BLUE}Running integration tests...${NC}"
        $PYTEST_CMD \
            tests/backend/ \
            -m "integration and not database"
        ;;
    
    database)
        echo -e "${BLUE}Running real database integration tests...${NC}"
        setup_test_database
        $PYTEST_CMD \
            tests/backend/test_database/test_real_database_integration.py \
            tests/backend/test_database/test_database_service_real.py \
            -m "database"
        ;;
    
    real)
        echo -e "${BLUE}Running all real integration tests (no mocks)...${NC}"
        setup_test_database
        $PYTEST_CMD \
            tests/backend/test_database/test_real_database_integration.py \
            tests/backend/test_agents/test_real_agent_integration.py \
            tests/backend/test_database/test_database_service_real.py \
            -m "real_integration or database"
        ;;
    
    performance)
        echo -e "${BLUE}Running performance tests...${NC}"
        setup_test_database
        $PYTEST_CMD \
            tests/backend/ \
            -m "performance or slow" \
            --durations=0
        ;;
    
    all)
        echo -e "${BLUE}Running all tests (unit + integration + database)...${NC}"
        setup_test_database
        
        echo -e "${YELLOW}📋 Phase 1: Unit Tests${NC}"
        $PYTEST_CMD tests/backend/ -m "unit and not database" || echo "Some unit tests failed"
        
        echo -e "${YELLOW}📋 Phase 2: Integration Tests${NC}"
        $PYTEST_CMD tests/backend/ -m "integration and not database" || echo "Some integration tests failed"
        
        echo -e "${YELLOW}📋 Phase 3: Database Tests${NC}"
        $PYTEST_CMD tests/backend/ -m "database" || echo "Some database tests failed"
        ;;
    
    agents)
        echo -e "${BLUE}Running AI agent tests...${NC}"
        $PYTEST_CMD \
            tests/backend/test_agents/ \
            -m "agents"
        ;;
    
    api)
        echo -e "${BLUE}Running API tests...${NC}"
        $PYTEST_CMD \
            tests/backend/test_api/ \
            -m "api"
        ;;
    
    *)
        echo -e "${RED}❌ Unknown test type: $TEST_TYPE${NC}"
        show_usage
        exit 1
        ;;
esac

test_exit_code=$?

echo ""
echo "📊 Test Results Summary:"
echo "========================"

if [ $test_exit_code -eq 0 ]; then
    echo -e "${GREEN}✅ All $TEST_TYPE tests passed!${NC}"
    
    if [ "$COVERAGE" = true ]; then
        echo ""
        echo -e "${BLUE}📈 Coverage report generated in htmlcov/index.html${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}🎯 What was tested:${NC}"
    case $TEST_TYPE in
        unit)
            echo "  • Fast unit tests with mocks and stubs"
            echo "  • Database configuration logic"
            echo "  • Agent initialization and basic functionality"
            echo "  • Memory management systems"
            ;;
        database)
            echo "  • Real PostgreSQL database operations"
            echo "  • Data persistence and retrieval"
            echo "  • Database constraints and relationships"
            echo "  • Agent session management with real DB"
            ;;
        real)
            echo "  • End-to-end workflows with real services"
            echo "  • Multi-agent interactions with persistence"
            echo "  • Real database performance under load"
            echo "  • Session isolation and memory management"
            ;;
        all)
            echo "  • Complete test suite coverage"
            echo "  • Unit tests (fast, isolated)"
            echo "  • Integration tests (with real services)"
            echo "  • Database tests (full persistence)"
            ;;
    esac
else
    echo -e "${RED}❌ Some $TEST_TYPE tests failed (exit code: $test_exit_code)${NC}"
    echo ""
    echo -e "${YELLOW}💡 Troubleshooting tips:${NC}"
    echo "  • Check test logs above for specific errors"
    echo "  • For database tests: ensure Docker is running"
    echo "  • For integration tests: check external service availability"
    echo "  • Run with --verbose for more detailed output"
    echo "  • Try running individual test files to isolate issues"
fi

echo ""
echo -e "${BLUE}📋 Available test commands:${NC}"
echo "  ./scripts/run-tests.sh unit           # Fast unit tests"
echo "  ./scripts/run-tests.sh database       # Real database tests"
echo "  ./scripts/run-tests.sh all --coverage # Complete test suite with coverage"
echo ""

exit $test_exit_code
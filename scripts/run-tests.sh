#!/bin/bash
# Test runner script for Legacy Interview App

set -e  # Exit on any error

echo "🧪 Legacy Interview App Test Suite"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment not detected. Activating legacy-venv...${NC}"
    source legacy-venv/bin/activate
fi

# Set test environment
export LEGACY_ENV=ci
export TESTING=true

echo -e "${BLUE}🌍 Environment: $LEGACY_ENV${NC}"
echo -e "${BLUE}📁 Working Directory: $(pwd)${NC}"

# Function to run specific test categories
run_tests() {
    local test_type=$1
    local test_path=$2
    local description=$3
    
    echo ""
    echo -e "${BLUE}🔬 Running $description...${NC}"
    echo "----------------------------------------"
    
    if pytest "$test_path" -m "$test_type" --tb=short -v; then
        echo -e "${GREEN}✅ $description passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ $description failed!${NC}"
        return 1
    fi
}

# Parse command line arguments
case "${1:-all}" in
    "unit")
        echo -e "${YELLOW}Running unit tests only...${NC}"
        run_tests "unit" "tests/" "Unit Tests"
        ;;
    "integration") 
        echo -e "${YELLOW}Running integration tests only...${NC}"
        run_tests "integration" "tests/" "Integration Tests"
        ;;
    "agents")
        echo -e "${YELLOW}Running agent tests only...${NC}"
        run_tests "agents" "tests/backend/test_agents/" "Agent Tests"
        ;;
    "database")
        echo -e "${YELLOW}Running database tests only...${NC}"
        run_tests "database" "tests/backend/test_database/" "Database Tests"
        ;;
    "fast")
        echo -e "${YELLOW}Running fast tests only (unit tests, no slow/integration)...${NC}"
        if pytest tests/ -m "not slow and not integration" --tb=short -v; then
            echo -e "${GREEN}✅ Fast tests passed!${NC}"
        else
            echo -e "${RED}❌ Fast tests failed!${NC}"
            exit 1
        fi
        ;;
    "coverage")
        echo -e "${YELLOW}Running tests with coverage report...${NC}"
        if pytest tests/ --cov=backend --cov=database --cov-report=html --cov-report=term-missing --tb=short -v; then
            echo -e "${GREEN}✅ Tests with coverage completed!${NC}"
            echo -e "${BLUE}📊 Coverage report generated in htmlcov/index.html${NC}"
        else
            echo -e "${RED}❌ Tests with coverage failed!${NC}"
            exit 1
        fi
        ;;
    "all"|"")
        echo -e "${YELLOW}Running all tests...${NC}"
        
        # Run unit tests first (fast)
        if ! run_tests "unit" "tests/" "Unit Tests"; then
            exit 1
        fi
        
        # Run integration tests (slower)
        if ! run_tests "integration" "tests/" "Integration Tests"; then
            echo -e "${YELLOW}⚠️  Integration tests failed, but continuing...${NC}"
        fi
        
        echo ""
        echo -e "${GREEN}🎉 All tests completed!${NC}"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [test_type]"
        echo ""
        echo "Test types:"
        echo "  all         - Run all tests (default)"
        echo "  unit        - Run unit tests only"
        echo "  integration - Run integration tests only"
        echo "  agents      - Run agent tests only"
        echo "  database    - Run database tests only"
        echo "  fast        - Run fast tests only (no slow/integration)"
        echo "  coverage    - Run tests with coverage report"
        echo "  help        - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 unit"
        echo "  $0 agents"
        echo "  $0 coverage"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Unknown test type: $1${NC}"
        echo "Use '$0 help' for available options"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}📋 Test Summary Complete${NC}"

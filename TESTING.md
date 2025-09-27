# Testing Guide - Legacy Interview App

## 🧪 **Testing Overview**

The Legacy Interview App includes a comprehensive test suite covering:
- **Question Generation**: Tests for AI-powered interview question creation
- **Memory & Database**: Tests for session management and data persistence
- **Multi-Environment**: Tests for CI/Test/Production database separation
- **Agent Functionality**: Tests for all AI agents (Planner, Prober, Summarizer, Simulator)
- **Real Database Integration**: Tests using actual PostgreSQL database for realistic scenarios
- **Performance Testing**: Tests for database performance under realistic loads

## 🏗️ **Test Structure**

```
tests/
├── backend/
│   ├── conftest.py              # Pytest configuration & fixtures
│   ├── conftest_real_db.py      # Real database test configuration
│   ├── test_agents/             # AI agent tests
│   │   ├── test_planner_agent.py      # Question generation tests (mocked)
│   │   ├── test_prober_agent.py       # Follow-up question tests (mocked)
│   │   ├── test_summarizer_agent.py   # Summarization tests (mocked)
│   │   └── test_real_agent_integration.py # Real agent integration tests
│   └── test_database/           # Database & memory tests
│       ├── test_config.py             # Multi-environment config tests
│       ├── test_memory_functionality.py # Session management tests
│       ├── test_real_database_integration.py # Real PostgreSQL tests
│       └── test_database_service_real.py # Database service integration tests
├── frontend/                    # React component tests (future)
└── integration/                 # End-to-end tests (future)
```

## 🎯 **Test Categories**

### **Unit Tests** (`-m unit`)
- Fast, isolated tests
- Mock external dependencies (OpenAI, database)
- Test individual functions and classes
- **Runtime**: < 1 minute

### **Integration Tests** (`-m integration`)
- Test component interactions
- May require database setup
- Test real agent interactions
- **Runtime**: 1-5 minutes

### **Database Tests** (`-m database`)
- Use real PostgreSQL database
- Test actual data persistence
- Test database constraints and relationships
- **Runtime**: 2-10 minutes

### **Real Integration Tests** (`-m real_integration`)
- No mocks - use actual services
- End-to-end workflows with real database
- Multi-agent interactions with persistence
- **Runtime**: 5-15 minutes

### **Performance Tests** (`-m performance`)
- Database performance under load
- Large dataset handling
- Concurrent operation testing
- **Runtime**: 5+ minutes

### **Slow Tests** (`-m slow`)
- Require OpenAI API calls
- Full end-to-end workflows
- Real database operations
- **Runtime**: 5+ minutes

## 🚀 **Running Tests**

### **Quick Start**
```bash
# Install dependencies first
./scripts/install-dependencies.sh

# Run fast unit tests (mocked, no external dependencies)
./scripts/run-tests.sh unit

# Run all tests including real database integration
./scripts/run-tests.sh all
```

### **Specific Test Types**
```bash
# Unit tests only (fastest, mocked)
./scripts/run-tests.sh unit

# Real database integration tests
./scripts/run-tests.sh database

# All real integration tests (no mocks)
./scripts/run-tests.sh real

# Performance tests
./scripts/run-tests.sh performance

# Agent tests only
./scripts/run-tests.sh agents

# All tests with coverage report
./scripts/run-tests.sh all --coverage

# Verbose output
./scripts/run-tests.sh database --verbose

# Parallel execution
./scripts/run-tests.sh unit --parallel
```

### **Database Test Setup**
```bash
# Set up PostgreSQL test database (Docker required)
./scripts/setup-test-database.sh

# Run database tests with clean database
./scripts/run-tests.sh database --clean-db

# Run comprehensive real database tests
./scripts/run-real-database-tests.sh
```

### **Manual Pytest Commands**
```bash
# Activate virtual environment first
source legacy-venv/bin/activate

# Run specific test files
pytest tests/backend/test_agents/test_planner_agent.py -v

# Run unit tests only (fast, mocked)
pytest tests/ -m "unit and not database" -v

# Run real database integration tests
pytest tests/ -m "database" -v

# Run all real integration tests (no mocks)
pytest tests/ -m "real_integration or database" -v

# Run performance tests
pytest tests/ -m "performance" -v --durations=0

# Run with coverage
pytest tests/ --cov=backend --cov=database --cov-report=html

# Run specific test methods
pytest tests/backend/test_database/test_real_database_integration.py::TestRealDatabaseIntegration::test_project_crud_operations -v

# Skip database tests if Docker not available
SKIP_DB_TESTS=true pytest tests/ -v
```

## 🔧 **Test Configuration**

### **Environment Variables**

**Unit Tests** (use mocks, no database):
```bash
LEGACY_ENV=ci          # Uses ci_ table prefix
TESTING=true           # Enables test mode
```

**Database Tests** (use real PostgreSQL):
```bash
LEGACY_ENV=test        # Test environment
USE_POSTGRES=true      # Enable PostgreSQL
USE_DATABASE=true      # Enable database operations
TEST_DB_HOST=localhost # Test database host
TEST_DB_PORT=5434      # Test database port (Docker)
TEST_DB_NAME=legacy_interview_test
TEST_DB_USER=legacy_test_user
TEST_DB_PASS=legacy_test_pass
```

**Skip Database Tests**:
```bash
SKIP_DB_TESTS=true     # Skip all database tests
```

### **Pytest Configuration** (`pytest.ini`)
- Test discovery patterns
- Marker definitions
- Output formatting
- Warning filters

### **Test Fixtures**

**`conftest.py`** (Unit tests):
- Mock database configuration
- Sample data for testing
- Mock OpenAI responses
- In-memory session management

**`conftest_real_db.py`** (Database tests):
- Real PostgreSQL database setup
- Docker container management
- Database cleaning between tests
- Real database session management

## 📊 **Test Coverage**

### **Question Generation Tests**
- ✅ Seed question generation with valid/invalid JSON
- ✅ Structured question parsing
- ✅ Theme identification
- ✅ Session management consistency
- ✅ Question quality validation
- ✅ End-to-end integration with OpenAI API

### **Memory & Database Tests**

**Unit Tests** (mocked):
- ✅ Multi-environment configuration
- ✅ Database connection management
- ✅ Session isolation between projects
- ✅ Memory persistence across calls
- ✅ Conversation summary retrieval
- ✅ Error handling and graceful degradation

**Real Database Tests**:
- ✅ Actual PostgreSQL database operations
- ✅ Project CRUD with real persistence
- ✅ Interview responses and themes storage
- ✅ Database constraints and relationships
- ✅ Multi-project data handling
- ✅ Performance under realistic loads
- ✅ Agent session persistence with PostgresDb

### **Agent Functionality Tests**

**Unit Tests** (mocked):
- ✅ **PlannerAgent**: Question generation and theme identification
- ✅ **ProberAgent**: Follow-up question generation and style adaptation
- ✅ **SummarizerAgent**: Timeline narratives and memorable quote extraction
- ✅ **SubjectSimulatorAgent**: Memory management and character consistency

**Real Integration Tests**:
- ✅ **Multi-agent workflows** with real database persistence
- ✅ **Session continuity** across multiple agent interactions
- ✅ **Memory persistence** with actual PostgresDb storage
- ✅ **Project isolation** with separate database sessions
- ✅ **Performance testing** with concurrent agent operations

## 🐛 **Debugging Tests**

### **Verbose Output**
```bash
pytest tests/ -v -s  # Show print statements
```

### **Failed Test Details**
```bash
pytest tests/ --tb=long  # Detailed tracebacks
```

### **Run Single Test**
```bash
pytest tests/backend/test_agents/test_planner_agent.py::TestPlannerAgent::test_generate_seed_questions_success -v -s
```

### **Debug with PDB**
```bash
pytest tests/ --pdb  # Drop into debugger on failure
```

## 🔑 **API Key Requirements**

### **Unit Tests**
- ❌ **No API key needed** - Uses mocks

### **Integration Tests**
- ✅ **OpenAI API key required** - Set `OPENAI_API_KEY` in `.env`
- Tests are automatically skipped if API key is missing

### **Slow Tests**
- ✅ **OpenAI API key required** - Real API calls for end-to-end testing

## 📈 **Test Metrics**

### **Current Coverage**
- **Agents**: ~95% test coverage (unit + integration)
- **Database Config**: ~90% test coverage
- **Memory Functions**: ~85% test coverage
- **Real Database Integration**: ~80% coverage
- **Agent Integration**: ~75% coverage

### **Performance Benchmarks**
- **Unit Tests**: ~30 seconds (mocked, fast)
- **Database Tests**: ~2-5 minutes (real PostgreSQL)
- **Real Integration Tests**: ~5-10 minutes (full workflow)
- **Performance Tests**: ~5-15 minutes (load testing)
- **Full Suite**: ~10-20 minutes (all test types)

## 🎯 **Best Practices**

### **Writing Tests**
1. **Use descriptive test names** that explain what's being tested
2. **Mock external dependencies** for unit tests
3. **Use fixtures** for common test data
4. **Test both success and failure cases**
5. **Include edge cases** and error conditions

### **Running Tests**
1. **Run fast tests frequently** during development
2. **Run full suite before commits**
3. **Use coverage reports** to identify gaps
4. **Test in CI environment** before production

### **Debugging**
1. **Use verbose output** to see detailed results
2. **Run single tests** to isolate issues
3. **Check logs and print statements**
4. **Verify environment variables** are set correctly

## 🚨 **Common Issues**

### **Missing Dependencies**
```bash
# Solution: Install test dependencies
pip install -r requirements.txt
```

### **Database Connection Errors**

**Unit Tests**:
```bash
# Solution: Ensure test environment is set
export LEGACY_ENV=ci
```

**Database Tests**:
```bash
# Solution: Set up test database
./scripts/setup-test-database.sh

# Or set environment variables manually
export TEST_DB_HOST=localhost
export TEST_DB_PORT=5434
export TEST_DB_NAME=legacy_interview_test
export TEST_DB_USER=legacy_test_user
export TEST_DB_PASS=legacy_test_pass
```

### **OpenAI API Errors**
```bash
# Solution: Set API key or skip integration tests
export OPENAI_API_KEY=your_key_here
# OR run without integration tests:
./scripts/run-tests.sh unit
```

### **Import Errors**
```bash
# Solution: Activate virtual environment
source legacy-venv/bin/activate
```

### **Docker Issues** (for database tests)
```bash
# Solution: Ensure Docker is running
docker --version

# Restart Docker if needed
sudo service docker restart  # Linux
# Or restart Docker Desktop on macOS/Windows

# Clean up test containers
docker-compose -f docker/docker-compose.test.yml down --volumes
```

### **Test Database Issues**
```bash
# Solution: Reset test database
./scripts/setup-test-database.sh

# Or manually clean test database
PGPASSWORD=legacy_test_pass psql -h localhost -p 5434 -U legacy_test_user -d legacy_interview_test -c "
  TRUNCATE TABLE projects CASCADE;
  TRUNCATE TABLE agent_sessions CASCADE;
"

# Skip database tests if Docker unavailable
SKIP_DB_TESTS=true ./scripts/run-tests.sh unit
```

---
**📅 Last Updated:** September 27, 2025

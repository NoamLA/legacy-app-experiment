# Testing Guide - Legacy Interview App

## 🧪 **Testing Overview**

The Legacy Interview App includes a comprehensive test suite covering:
- **Question Generation**: Tests for AI-powered interview question creation
- **Memory & Database**: Tests for session management and data persistence
- **Multi-Environment**: Tests for CI/Test/Production database separation
- **Agent Functionality**: Tests for all AI agents (Planner, Prober, Summarizer, Simulator)

## 🏗️ **Test Structure**

```
tests/
├── backend/
│   ├── conftest.py              # Pytest configuration & fixtures
│   ├── test_agents/             # AI agent tests
│   │   ├── test_planner_agent.py      # Question generation tests
│   │   ├── test_prober_agent.py       # Follow-up question tests
│   │   └── test_summarizer_agent.py   # Summarization tests
│   └── test_database/           # Database & memory tests
│       ├── test_config.py             # Multi-environment config tests
│       └── test_memory_functionality.py # Session management tests
├── frontend/                    # React component tests (future)
└── integration/                 # End-to-end tests (future)
```

## 🎯 **Test Categories**

### **Unit Tests** (`-m unit`)
- Fast, isolated tests
- Mock external dependencies
- Test individual functions and classes
- **Runtime**: < 1 minute

### **Integration Tests** (`-m integration`)
- Test component interactions
- May require database setup
- Test real agent interactions
- **Runtime**: 1-5 minutes

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

# Run all fast tests
./scripts/run-tests.sh fast

# Run all tests
./scripts/run-tests.sh
```

### **Specific Test Types**
```bash
# Unit tests only (fastest)
./scripts/run-tests.sh unit

# Agent tests only
./scripts/run-tests.sh agents

# Database tests only
./scripts/run-tests.sh database

# Integration tests
./scripts/run-tests.sh integration

# Tests with coverage report
./scripts/run-tests.sh coverage
```

### **Manual Pytest Commands**
```bash
# Activate virtual environment first
source legacy-venv/bin/activate

# Run specific test files
pytest tests/backend/test_agents/test_planner_agent.py -v

# Run with specific markers
pytest tests/ -m "unit and not slow" -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Run specific test methods
pytest tests/backend/test_agents/test_planner_agent.py::TestPlannerAgent::test_generate_seed_questions_success -v
```

## 🔧 **Test Configuration**

### **Environment Variables**
Tests automatically use the CI environment:
```bash
LEGACY_ENV=ci          # Uses ci_ table prefix
TESTING=true           # Enables test mode
```

### **Pytest Configuration** (`pytest.ini`)
- Test discovery patterns
- Marker definitions
- Output formatting
- Warning filters

### **Test Fixtures** (`conftest.py`)
- Database configuration for tests
- Sample data for testing
- Mock configurations
- Session management

## 📊 **Test Coverage**

### **Question Generation Tests**
- ✅ Seed question generation with valid/invalid JSON
- ✅ Structured question parsing
- ✅ Theme identification
- ✅ Session management consistency
- ✅ Question quality validation
- ✅ End-to-end integration with OpenAI API

### **Memory & Database Tests**
- ✅ Multi-environment configuration
- ✅ Database connection management
- ✅ Session isolation between projects
- ✅ Memory persistence across calls
- ✅ Conversation summary retrieval
- ✅ Error handling and graceful degradation

### **Agent Functionality Tests**
- ✅ **PlannerAgent**: Question generation and theme identification
- ✅ **ProberAgent**: Follow-up question generation and style adaptation
- ✅ **SummarizerAgent**: Timeline narratives and memorable quote extraction
- ✅ **SubjectSimulatorAgent**: Memory management and character consistency

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
- **Agents**: ~95% test coverage
- **Database Config**: ~90% test coverage
- **Memory Functions**: ~85% test coverage

### **Performance Benchmarks**
- **Unit Tests**: ~30 seconds
- **Integration Tests**: ~2-3 minutes (with API calls)
- **Full Suite**: ~5 minutes

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
```bash
# Solution: Ensure test environment is set
export LEGACY_ENV=ci
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
---
**📅 Last Updated:** September 27, 2025

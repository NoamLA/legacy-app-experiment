# Legacy Interview App - Project Structure

## 📁 Current Repository Organization

```
legacy/
├── 🏗️ PROJECT FILES
│   ├── README.md                    # Main project documentation
│   ├── SETUP.md                     # Setup instructions
│   ├── PROJECT_STRUCTURE.md         # This file
│   ├── requirements.txt             # Python dependencies
│   ├── package.json                 # Node.js dependencies
│   └── setup.py                     # Automated setup script
│
├── 🌍 ENVIRONMENT CONFIG
│   ├── env-template.txt             # Environment variables template
│   ├── env-setup.md                 # Environment setup guide
│   ├── .env                         # Local environment (gitignored)
│   ├── .env.ci                      # CI environment
│   ├── .env.test                    # Test environment
│   ├── .env.production              # Production environment
│   └── .env.development             # Development environment
│
├── 🗄️ DATABASE
│   ├── database/
│   │   ├── config.py                # Multi-env database configuration
│   │   ├── schema.sql               # Original schema (legacy)
│   │   ├── schema_multi_env.sql     # Multi-environment schema
│   │   ├── setup.py                 # Single environment setup
│   │   └── env_setup.py             # Multi-environment setup
│   └── migrations/                  # Database migrations (to be created)
│
├── 🖥️ BACKEND (FastAPI + Agno)
│   └── backend/
│       ├── __init__.py
│       ├── main.py                  # FastAPI application entry point
│       ├── database_models.py       # SQLAlchemy models
│       ├── agents/                  # Agno AI agents
│       │   ├── __init__.py
│       │   ├── planner_agent.py     # Question generation agent
│       │   ├── prober_agent.py      # Follow-up questions agent
│       │   ├── summarizer_agent.py  # Interview summarization agent
│       │   └── subject_simulator_agent.py # Testing simulator agent
│       ├── api/                     # API routes (to be created)
│       ├── services/                # Business logic (to be created)
│       └── utils/                   # Utility functions (to be created)
│
├── 🌐 FRONTEND (React)
│   ├── public/
│   │   ├── index.html
│   │   └── manifest.json
│   ├── src/
│   │   ├── index.js                 # React entry point
│   │   ├── App.js                   # Main App component
│   │   ├── App.css
│   │   ├── index.css
│   │   ├── components/              # Reusable React components
│   │   │   └── Header.js
│   │   └── pages/                   # Page components
│   │       ├── HomePage.js
│   │       ├── ProjectCreate.js
│   │       ├── ProjectDashboard.js
│   │       └── InterviewFlow.js
│   ├── package.json
│   ├── postcss.config.js
│   └── tailwind.config.js
│
├── 🧪 TESTS
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── conftest.py              # Pytest configuration (unit tests)
│   │   ├── conftest_real_db.py      # Real database test configuration
│   │   ├── test_agents/             # Agent testing
│   │   │   ├── test_planner_agent.py        # Unit tests (mocked)
│   │   │   ├── test_prober_agent.py         # Unit tests (mocked)
│   │   │   ├── test_summarizer_agent.py     # Unit tests (mocked)
│   │   │   └── test_real_agent_integration.py # Real integration tests
│   │   ├── test_database/           # Database testing
│   │   │   ├── test_config.py               # Unit tests (mocked)
│   │   │   ├── test_memory_functionality.py # Unit tests (mocked)
│   │   │   ├── test_real_database_integration.py # Real PostgreSQL tests
│   │   │   └── test_database_service_real.py # Database service integration
│   │   └── test_api/                # API endpoint testing (future)
│   ├── frontend/
│   │   └── __tests__/               # React component tests
│   └── integration/                 # End-to-end tests
│
├── 🚀 DEPLOYMENT & SCRIPTS
│   ├── scripts/                     # Utility scripts
│   │   ├── start-backend.py
│   │   ├── start-frontend.sh
│   │   ├── start-with-venv.sh
│   │   ├── run-tests.sh             # Comprehensive test runner
│   │   ├── run-real-database-tests.sh # Real database test runner
│   │   ├── setup-test-database.sh   # Docker PostgreSQL setup
│   │   └── install-dependencies.sh
│   ├── docker/                      # Docker configurations
│   │   └── docker-compose.test.yml  # Test database setup
│   └── .github/                     # GitHub Actions (to be created)
│       └── workflows/
│
├── 📚 DOCUMENTATION
│   ├── docs/                        # Additional documentation (to be created)
│   │   ├── api.md                   # API documentation
│   │   ├── agents.md                # Agent documentation
│   │   └── database.md              # Database documentation
│   └── .cursor/                     # Cursor IDE rules
│       └── rules/
│
└── 🔧 DEVELOPMENT
    ├── legacy-venv/                 # Python virtual environment
    ├── node_modules/                # Node.js dependencies
    ├── activate-venv.sh             # Virtual environment activation
    └── __pycache__/                 # Python cache files
```

## ✅ **Completed Improvements**

### 1. **✅ Scripts Organization**
- ✅ Moved all startup scripts to `scripts/` directory
- ✅ Created `scripts/run-tests.sh` for comprehensive testing

### 2. **✅ Testing Structure**
- ✅ Created comprehensive test suite with pytest
- ✅ Separated unit, integration, database, and performance tests with markers
- ✅ Added test configuration with `pytest.ini`
- ✅ Created unit tests with mocks for all agents
- ✅ Created real database integration tests using Docker PostgreSQL
- ✅ Created performance tests for database operations
- ✅ Added multi-agent integration tests with real persistence
- ✅ Created comprehensive test runners (`run-tests.sh`, `run-real-database-tests.sh`)
- ✅ Added Docker-based test database setup (`docker-compose.test.yml`)
- ✅ Added testing dependencies to `requirements.txt`

### 3. **✅ Multi-Environment Database**
- ✅ Created environment-specific database configuration
- ✅ Added CI/Test/Production database separation
- ✅ Created multi-environment schema and setup scripts

## 🎯 **Remaining Improvements**

### 1. **Backend Structure** (Future)
- Split `main.py` into separate API route modules  
- Create `services/` for business logic
- Add `utils/` for shared utilities

### 2. **Documentation** (Future)
- API documentation with OpenAPI/Swagger
- Agent behavior documentation  
- Database schema documentation

### 3. **Deployment** (Future)
- Docker configurations for different environments
- GitHub Actions for CI/CD
- Environment-specific deployment scripts

## 🧪 **Testing Commands**

```bash
# Run different test types
./scripts/run-tests.sh unit          # Fast unit tests (mocked)
./scripts/run-tests.sh database      # Real PostgreSQL database tests
./scripts/run-tests.sh real          # All real integration tests (no mocks)
./scripts/run-tests.sh performance   # Performance and load tests
./scripts/run-tests.sh all           # Complete test suite
./scripts/run-tests.sh agents        # Agent tests only

# Test options
./scripts/run-tests.sh database --verbose    # Verbose output
./scripts/run-tests.sh all --coverage        # With coverage report
./scripts/run-tests.sh unit --parallel       # Parallel execution
./scripts/run-tests.sh database --clean-db   # Clean database before tests

# Database test setup
./scripts/setup-test-database.sh             # Set up Docker PostgreSQL
./scripts/run-real-database-tests.sh         # Comprehensive database tests

# Manual pytest commands
pytest tests/ -m "unit and not database"     # Unit tests only
pytest tests/ -m "database"                  # Database tests only
pytest tests/ -m "real_integration"          # Real integration tests
pytest tests/ -m "performance"               # Performance tests
pytest tests/ --cov=backend --cov=database  # With coverage
```

---
**📅 Last Updated:** October 1, 2025

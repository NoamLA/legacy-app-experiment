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
├── 🧪 TESTS (to be created)
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── test_agents/             # Agent testing
│   │   ├── test_database/           # Database testing
│   │   ├── test_api/                # API endpoint testing
│   │   └── conftest.py              # Pytest configuration
│   ├── frontend/
│   │   └── __tests__/               # React component tests
│   └── integration/                 # End-to-end tests
│
├── 🚀 DEPLOYMENT & SCRIPTS
│   ├── scripts/                     # Utility scripts (to be created)
│   │   ├── start-backend.py
│   │   ├── start-frontend.sh
│   │   └── start-with-venv.sh
│   ├── docker/                      # Docker configurations (to be created)
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
- ✅ Separated unit, integration, and slow tests with markers
- ✅ Added test configuration with `pytest.ini`
- ✅ Created tests for question generation (`test_planner_agent.py`)
- ✅ Created tests for follow-up questions (`test_prober_agent.py`) 
- ✅ Created tests for summarization (`test_summarizer_agent.py`)
- ✅ Created tests for database/memory functionality (`test_config.py`, `test_memory_functionality.py`)
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
# Run all tests
./scripts/run-tests.sh

# Run specific test types
./scripts/run-tests.sh unit          # Fast unit tests only
./scripts/run-tests.sh integration   # Integration tests only
./scripts/run-tests.sh agents        # Agent tests only
./scripts/run-tests.sh database      # Database tests only
./scripts/run-tests.sh fast          # Fast tests (no slow/integration)
./scripts/run-tests.sh coverage      # Tests with coverage report

# Manual pytest commands
pytest tests/ -m unit                # Unit tests
pytest tests/ -m "not slow"          # Exclude slow tests
pytest tests/backend/test_agents/    # Agent tests only
pytest tests/ --cov=backend         # With coverage
```

---
**📅 Last Updated:** September 27, 2025

"""
Pytest configuration for real database integration tests
Sets up PostgreSQL test database and manages test environment
"""
import pytest
import os
import sys
import subprocess
import time
import psycopg2
from pathlib import Path

# Add backend and database to path
backend_path = Path(__file__).parent.parent / "backend"
database_path = Path(__file__).parent.parent / "database"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(database_path))

from config import DatabaseConfig, DatabaseManager

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "database: Tests that require real PostgreSQL database"
    )
    config.addinivalue_line(
        "markers", "real_integration: Integration tests with real services"
    )

def pytest_collection_modifyitems(config, items):
    """Auto-mark database tests"""
    for item in items:
        if "test_real_database" in item.nodeid or "test_real_agent" in item.nodeid:
            item.add_marker(pytest.mark.database)
            item.add_marker(pytest.mark.real_integration)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Set up test database infrastructure for the entire test session"""
    print("\n🐳 Setting up test database infrastructure...")
    
    # Set test environment variables
    os.environ.update({
        "LEGACY_ENV": "test",
        "USE_POSTGRES": "true",
        "USE_DATABASE": "true",
        "TEST_DB_HOST": "localhost",
        "TEST_DB_PORT": "5434",
        "TEST_DB_NAME": "legacy_interview_test",
        "TEST_DB_USER": "legacy_test_user",
        "TEST_DB_PASS": "legacy_test_pass"
    })
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("Docker not available - skipping real database tests")
    
    # Start test database
    project_root = Path(__file__).parent.parent
    compose_file = project_root / "docker" / "docker-compose.test.yml"
    
    if not compose_file.exists():
        pytest.skip("Test database configuration not found")
    
    try:
        # Stop any existing test containers
        subprocess.run([
            "docker-compose", "-f", str(compose_file), "down", "--volumes"
        ], cwd=project_root, capture_output=True)
        
        # Start test database
        result = subprocess.run([
            "docker-compose", "-f", str(compose_file), "up", "-d", "test-postgres"
        ], cwd=project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            pytest.skip(f"Failed to start test database: {result.stderr}")
        
        # Wait for database to be ready
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    port=5434,
                    database="legacy_interview_test",
                    user="legacy_test_user",
                    password="legacy_test_pass"
                )
                conn.close()
                print("✅ Test database is ready!")
                break
            except psycopg2.Error:
                if attempt == max_attempts - 1:
                    pytest.skip("Test database failed to become ready")
                time.sleep(1)
        
        yield
        
        # Cleanup: Stop test containers
        subprocess.run([
            "docker-compose", "-f", str(compose_file), "down", "--volumes"
        ], cwd=project_root, capture_output=True)
        
    except Exception as e:
        pytest.skip(f"Failed to set up test database: {e}")

@pytest.fixture(scope="session")
def test_database_config():
    """Provide test database configuration"""
    config = DatabaseConfig(environment="test")
    config.host = "localhost"
    config.port = "5434"
    config.database = "legacy_interview_test"
    config.username = "legacy_test_user"
    config.password = "legacy_test_pass"
    return config

@pytest.fixture(scope="session")
def test_database_manager(test_database_config):
    """Provide test database manager"""
    return DatabaseManager(test_database_config)

@pytest.fixture(scope="function")
def clean_test_database(test_database_manager):
    """Clean test database before each test"""
    with test_database_manager.get_session() as session:
        # Clean all tables
        tables = [
            "interview_responses",
            "interview_themes", 
            "projects",
            "knowledge_documents",
            "agent_sessions",
            "agent_messages",
            "agent_runs",
            "user_memories",
            "session_summaries"
        ]
        
        for table in tables:
            try:
                session.execute(f"TRUNCATE TABLE {table} CASCADE")
            except Exception:
                pass  # Table might not exist yet
        
        session.commit()
        
        yield session
        
        # Clean up after test
        for table in tables:
            try:
                session.execute(f"TRUNCATE TABLE {table} CASCADE")
            except Exception:
                pass
        
        session.commit()

def pytest_runtest_setup(item):
    """Skip database tests if database is not available"""
    if "database" in item.keywords:
        # Check if we should skip database tests
        if os.getenv("SKIP_DB_TESTS", "").lower() == "true":
            pytest.skip("Database tests skipped by SKIP_DB_TESTS environment variable")
        
        # Check if test database is accessible
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5434,
                database="legacy_interview_test",
                user="legacy_test_user",
                password="legacy_test_pass",
                connect_timeout=5
            )
            conn.close()
        except psycopg2.Error:
            pytest.skip("Test database not accessible - run './scripts/setup-test-database.sh' first")

# Sample data fixtures for real database tests
@pytest.fixture
def sample_project_data():
    """Sample project data for database tests"""
    return {
        "name": "Real Database Test Project",
        "subject_info": {
            "name": "Maria Gonzalez",
            "age": 79,
            "relation": "grandmother",
            "background": "Born in Spain, lived in Mexico, immigrated to US in 1960s",
            "language": "English"
        },
        "interview_mode": "family",
        "language": "en",
        "status": "created"
    }

@pytest.fixture
def sample_interview_responses():
    """Sample interview responses for testing"""
    return [
        {
            "question": "Tell me about your childhood in Spain",
            "answer": "I grew up in a small village in Andalusia. My father was a farmer and we had olive trees.",
            "question_type": "seed"
        },
        {
            "question": "What was it like moving to Mexico?",
            "answer": "It was a big change. The culture was different but the language was familiar.",
            "question_type": "seed"
        },
        {
            "question": "How did you meet your husband?",
            "answer": "We met at a church dance in Mexico City. He was so handsome and kind.",
            "question_type": "followup"
        }
    ]

@pytest.fixture
def sample_themes():
    """Sample themes for testing"""
    return [
        {
            "name": "Immigration Journey",
            "description": "Stories about moving from Spain to Mexico to US",
            "questions": [
                "What was the hardest part about leaving Spain?",
                "How did you adapt to life in Mexico?",
                "What made you decide to come to America?"
            ],
            "suggested_interviewer": "family member"
        },
        {
            "name": "Family Life",
            "description": "Stories about marriage, children, and family traditions",
            "questions": [
                "Tell me about your wedding day",
                "What traditions did you keep from Spain?",
                "How did you raise your children?"
            ],
            "suggested_interviewer": "close family member"
        }
    ]

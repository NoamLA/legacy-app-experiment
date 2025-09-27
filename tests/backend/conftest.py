"""
Pytest configuration for Legacy Interview App backend tests
"""
import pytest
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Add database to path
database_path = Path(__file__).parent.parent.parent / "database"
sys.path.insert(0, str(database_path))

from database.config import DatabaseConfig, DatabaseManager, Environment
from backend.database_models import Base
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def test_env():
    """Set up test environment"""
    os.environ["LEGACY_ENV"] = "ci"  # Use CI environment for tests
    yield
    # Cleanup
    os.environ.pop("LEGACY_ENV", None)

@pytest.fixture(scope="session")
def test_db_config(test_env):
    """Create test database configuration"""
    return DatabaseConfig(environment="ci")

@pytest.fixture(scope="session")
def test_db_manager(test_db_config):
    """Create test database manager"""
    return DatabaseManager(test_db_config)

@pytest.fixture(scope="function")
def test_db_session(test_db_manager):
    """Create a test database session with rollback"""
    with test_db_manager.get_session() as session:
        # Start a transaction
        transaction = session.begin()
        
        yield session
        
        # Rollback transaction to clean up
        transaction.rollback()

@pytest.fixture(scope="session")
def sample_subject_info():
    """Sample subject information for testing"""
    return {
        "name": "Rose Martinez",
        "age": 82,
        "relation": "grandmother",
        "background": "Born in Mexico, immigrated to California in the 1960s. Raised 5 children while working as a seamstress.",
        "language": "English",
        "interview_mode": "family"
    }

@pytest.fixture(scope="session")
def sample_responses():
    """Sample interview responses for testing"""
    return [
        {
            "question": "Tell me about where you were born and what it was like growing up there.",
            "answer": "I was born in a small village in Jalisco, Mexico. It was very different from here - we had dirt roads and my family grew corn and beans. Life was simple but we were happy."
        },
        {
            "question": "What is your earliest childhood memory?",
            "answer": "I remember helping my mother make tortillas when I was maybe 4 years old. She would let me pat the dough, and I felt so important helping her feed the family."
        },
        {
            "question": "Who were the most important people in your early life?",
            "answer": "My grandmother, she taught me everything about cooking and taking care of a family. And my father, he worked so hard in the fields but always had time to tell us stories at night."
        }
    ]

@pytest.fixture(scope="session")
def mock_openai_response():
    """Mock OpenAI response for testing"""
    class MockResponse:
        def __init__(self, content):
            self.content = content
    
    return MockResponse

# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow

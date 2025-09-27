"""
Tests for Database Configuration and Multi-Environment Setup
"""
import pytest
import os
import tempfile
from unittest.mock import patch, Mock
import sys
from pathlib import Path

# Add database to path
database_path = Path(__file__).parent.parent.parent.parent / "database"
sys.path.insert(0, str(database_path))

from config import DatabaseConfig, DatabaseManager, Environment

class TestDatabaseConfig:
    """Test suite for DatabaseConfig"""
    
    @pytest.mark.unit
    def test_environment_detection(self):
        """Test that environment is correctly detected from env vars"""
        # Test CI environment
        with patch.dict(os.environ, {"LEGACY_ENV": "ci"}):
            config = DatabaseConfig()
            assert config.environment == Environment.CI
            assert config.database == "legacy_interview_ci"
            assert config.table_prefix == "ci_"
            
        # Test TEST environment  
        with patch.dict(os.environ, {"LEGACY_ENV": "test"}):
            config = DatabaseConfig()
            assert config.environment == Environment.TEST
            assert config.database == "legacy_interview_test"
            assert config.table_prefix == "test_"
            
        # Test PRODUCTION environment
        with patch.dict(os.environ, {"LEGACY_ENV": "production"}):
            config = DatabaseConfig()
            assert config.environment == Environment.PRODUCTION
            assert config.database == "legacy_interview_prod"
            assert config.table_prefix == ""
            
    @pytest.mark.unit
    def test_default_environment(self):
        """Test default environment when LEGACY_ENV is not set"""
        with patch.dict(os.environ, {}, clear=True):
            config = DatabaseConfig()
            assert config.environment == Environment.TEST  # Default should be test
            
    @pytest.mark.unit
    def test_database_url_generation(self):
        """Test that database URLs are generated correctly"""
        with patch.dict(os.environ, {
            "LEGACY_ENV": "test",
            "DB_HOST": "testhost",
            "DB_PORT": "5433", 
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass",
            "DB_BASE_NAME": "testdb"
        }):
            config = DatabaseConfig()
            expected_url = "postgresql+psycopg://testuser:testpass@testhost:5433/testdb_test?sslmode=prefer"
            assert config.url == expected_url
            
    @pytest.mark.unit
    def test_environment_specific_pool_sizes(self):
        """Test that pool sizes are environment-specific"""
        # CI should have minimal pool
        with patch.dict(os.environ, {"LEGACY_ENV": "ci"}):
            config = DatabaseConfig()
            assert config.pool_size == 2
            assert config.max_overflow == 2
            
        # Production should have large pool
        with patch.dict(os.environ, {"LEGACY_ENV": "production"}):
            config = DatabaseConfig()
            assert config.pool_size == 20
            assert config.max_overflow == 50
            
    @pytest.mark.unit
    def test_table_name_prefixing(self):
        """Test that table names are correctly prefixed"""
        with patch.dict(os.environ, {"LEGACY_ENV": "ci"}):
            config = DatabaseConfig()
            assert config.get_table_name("projects") == "ci_projects"
            assert config.get_table_name("agent_sessions") == "ci_agent_sessions"
            
        with patch.dict(os.environ, {"LEGACY_ENV": "production"}):
            config = DatabaseConfig()
            assert config.get_table_name("projects") == "projects"  # No prefix
            
    @pytest.mark.unit
    def test_environment_info(self):
        """Test environment info dictionary"""
        with patch.dict(os.environ, {"LEGACY_ENV": "test"}):
            config = DatabaseConfig()
            info = config.get_environment_info()
            
            assert info["environment"] == Environment.TEST
            assert info["database"] == "legacy_interview_test"
            assert info["table_prefix"] == "test_"
            assert info["is_test"] == True
            assert info["is_production"] == False

class TestDatabaseManager:
    """Test suite for DatabaseManager"""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock database config for testing"""
        config = Mock()
        # Use PostgreSQL URL for testing to match production behavior
        config.url = "postgresql+psycopg://test:test@localhost:5432/test_db"
        config.agno_url = "postgresql+psycopg://test:test@localhost:5432/test_db"
        config.pool_size = 2
        config.max_overflow = 2
        config.pool_timeout = 30
        config.pool_recycle = 3600
        config.get_table_name = lambda x: f"test_{x}"
        return config
        
    @pytest.mark.unit
    def test_database_manager_initialization(self, mock_config):
        """Test DatabaseManager initialization"""
        manager = DatabaseManager(mock_config)
        assert manager.config == mock_config
        assert manager._engine is None  # Should be lazy-loaded
        
    @pytest.mark.unit
    @patch('config.create_engine')
    def test_engine_creation(self, mock_create_engine, mock_config):
        """Test that SQLAlchemy engine is created correctly"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        manager = DatabaseManager(mock_config)
        engine = manager.engine
        
        assert engine is mock_engine
        assert manager._engine is engine  # Should be cached
        
        # Verify create_engine was called with correct parameters
        mock_create_engine.assert_called_once_with(
            mock_config.url,
            pool_size=mock_config.pool_size,
            max_overflow=mock_config.max_overflow,
            pool_timeout=mock_config.pool_timeout,
            pool_recycle=mock_config.pool_recycle,
            pool_pre_ping=True,
            echo=False
        )
        
        # Second access should return same engine
        engine2 = manager.engine
        assert engine is engine2
        
    @pytest.mark.unit
    @patch('config.create_engine')
    @patch('config.sessionmaker')
    def test_session_factory_creation(self, mock_sessionmaker, mock_create_engine, mock_config):
        """Test that session factory is created correctly"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        mock_factory = Mock()
        mock_sessionmaker.return_value = mock_factory
        
        manager = DatabaseManager(mock_config)
        factory = manager.session_factory
        
        assert factory is mock_factory
        assert manager._session_factory is factory  # Should be cached
        
        # Verify sessionmaker was called with the engine
        mock_sessionmaker.assert_called_once_with(bind=mock_engine)
        
    @pytest.mark.unit
    @patch('config.PostgresDb')
    def test_agno_db_creation(self, mock_postgres_db, mock_config):
        """Test that Agno PostgresDb is created with correct table names"""
        manager = DatabaseManager(mock_config)
        agno_db = manager.agno_db
        
        # Verify PostgresDb was called with environment-specific table names
        mock_postgres_db.assert_called_once_with(
            db_url=mock_config.agno_url,
            session_table="test_agent_sessions",
            run_table="test_agent_runs",
            message_table="test_agent_messages",
            memory_table="test_user_memories",
            summary_table="test_session_summaries"
        )
        
    @pytest.mark.unit
    @patch('config.create_engine')
    @patch('config.sessionmaker')
    def test_session_context_manager(self, mock_sessionmaker, mock_create_engine, mock_config):
        """Test database session context manager"""
        # Mock engine and session
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        mock_session = Mock()
        mock_session.is_active = True
        mock_session_factory = Mock(return_value=mock_session)
        mock_sessionmaker.return_value = mock_session_factory
        
        manager = DatabaseManager(mock_config)
        
        with manager.get_session() as session:
            assert session is not None
            
        # Verify session lifecycle methods were called
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        
    @pytest.mark.unit
    @patch('config.create_engine')
    def test_connection_test_success(self, mock_create_engine, mock_config):
        """Test successful database connection test"""
        # Mock successful engine creation and connection
        mock_engine = Mock()
        mock_connection = Mock()
        mock_context_manager = Mock()
        mock_context_manager.__enter__ = Mock(return_value=mock_connection)
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_context_manager
        
        # Mock the execute result to return scalar() == 1
        mock_result = Mock()
        mock_result.scalar.return_value = 1
        mock_connection.execute.return_value = mock_result
        
        mock_create_engine.return_value = mock_engine
        
        manager = DatabaseManager(mock_config)
        assert manager.test_connection() == True
        
    @pytest.mark.unit
    def test_connection_test_failure(self):
        """Test database connection test failure"""
        config = Mock()
        config.url = "postgresql://invalid:invalid@nonexistent:5432/invalid"
        config.pool_size = 1
        config.max_overflow = 1
        config.pool_timeout = 1
        config.pool_recycle = 3600
        
        manager = DatabaseManager(config)
        
        # Should fail with invalid connection string
        assert manager.test_connection() == False
        
    @pytest.mark.unit
    def test_check_extensions_no_postgres(self, mock_config):
        """Test extension check with non-PostgreSQL database"""
        manager = DatabaseManager(mock_config)
        extensions = manager.check_extensions()
        
        # Should return False for all extensions with SQLite
        assert extensions['uuid-ossp'] == False
        assert extensions['pgvector'] == False
        assert extensions['pg_trgm'] == False

class TestEnvironmentIntegration:
    """Integration tests for multi-environment functionality"""
    
    @pytest.mark.integration
    def test_environment_switching(self):
        """Test switching between environments"""
        environments = ["ci", "test", "production", "development"]
        
        for env in environments:
            with patch.dict(os.environ, {"LEGACY_ENV": env}):
                config = DatabaseConfig()
                manager = DatabaseManager(config)
                
                # Verify environment-specific configuration
                assert config.environment.value == env
                
                if env == "ci":
                    assert config.table_prefix == "ci_"
                    assert config.pool_size == 2
                elif env == "test":
                    assert config.table_prefix == "test_"
                    assert config.pool_size == 5
                elif env == "production":
                    assert config.table_prefix == ""
                    assert config.pool_size == 20
                elif env == "development":
                    assert config.table_prefix == "dev_"
                    assert config.pool_size == 10
                    
    @pytest.mark.integration
    def test_agno_integration(self):
        """Test integration with Agno PostgresDb"""
        with patch.dict(os.environ, {"LEGACY_ENV": "ci"}):
            config = DatabaseConfig()
            
            # Test that Agno table names are correctly prefixed
            expected_tables = {
                "session_table": "ci_agent_sessions",
                "run_table": "ci_agent_runs", 
                "message_table": "ci_agent_messages",
                "memory_table": "ci_user_memories",
                "summary_table": "ci_session_summaries"
            }
            
            with patch('config.PostgresDb') as mock_postgres:
                manager = DatabaseManager(config)
                agno_db = manager.agno_db
                
                # Verify correct table names were passed
                call_kwargs = mock_postgres.call_args[1]
                for table_type, expected_name in expected_tables.items():
                    assert call_kwargs[table_type] == expected_name

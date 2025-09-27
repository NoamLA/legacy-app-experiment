"""
Database configuration and connection management for Legacy Interview App
Multi-environment setup: CI/Test/Production
Optimized for Agno PostgresDb integration and RAG capabilities
"""
import os
from typing import Optional, Literal
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from agno.db.postgres import PostgresDb
from contextlib import contextmanager
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Environment(str, Enum):
    """Application environment types"""
    CI = "ci"
    TEST = "test" 
    PRODUCTION = "production"
    DEVELOPMENT = "development"  # Local development

class DatabaseConfig:
    """Multi-environment database configuration management"""
    
    def __init__(self, environment: Optional[str] = None):
        # Determine environment
        self.environment = Environment(environment or os.getenv("LEGACY_ENV", "test"))
        logger.info(f"🌍 Database environment: {self.environment}")
        
        # Base configuration
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.username = os.getenv("DB_USER", "legacy_user")
        self.password = os.getenv("DB_PASSWORD", "legacy_pass")
        self.ssl_mode = os.getenv("DB_SSL_MODE", "prefer")
        
        # Environment-specific database names
        self.database = self._get_database_name()
        
        # Environment-specific table prefixes
        self.table_prefix = self._get_table_prefix()
        
        # Environment-specific connection pool settings
        self.pool_size = self._get_pool_size()
        self.max_overflow = self._get_max_overflow()
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    
    def _get_database_name(self) -> str:
        """Get environment-specific database name"""
        base_name = os.getenv("DB_BASE_NAME", "legacy_interview")
        
        if self.environment == Environment.CI:
            return f"{base_name}_ci"
        elif self.environment == Environment.TEST:
            return f"{base_name}_test"
        elif self.environment == Environment.PRODUCTION:
            return f"{base_name}_prod"
        else:  # DEVELOPMENT
            return f"{base_name}_dev"
    
    def _get_table_prefix(self) -> str:
        """Get environment-specific table prefix"""
        if self.environment == Environment.CI:
            return "ci_"
        elif self.environment == Environment.TEST:
            return "test_"
        elif self.environment == Environment.PRODUCTION:
            return ""  # No prefix for production
        else:  # DEVELOPMENT
            return "dev_"
    
    def _get_pool_size(self) -> int:
        """Get environment-specific pool size"""
        if self.environment == Environment.CI:
            return int(os.getenv("DB_POOL_SIZE", "2"))  # Minimal for CI
        elif self.environment == Environment.TEST:
            return int(os.getenv("DB_POOL_SIZE", "5"))  # Small for testing
        elif self.environment == Environment.PRODUCTION:
            return int(os.getenv("DB_POOL_SIZE", "20"))  # Large for production
        else:  # DEVELOPMENT
            return int(os.getenv("DB_POOL_SIZE", "10"))  # Medium for dev
    
    def _get_max_overflow(self) -> int:
        """Get environment-specific max overflow"""
        if self.environment == Environment.CI:
            return int(os.getenv("DB_MAX_OVERFLOW", "2"))
        elif self.environment == Environment.TEST:
            return int(os.getenv("DB_MAX_OVERFLOW", "10"))
        elif self.environment == Environment.PRODUCTION:
            return int(os.getenv("DB_MAX_OVERFLOW", "50"))
        else:  # DEVELOPMENT
            return int(os.getenv("DB_MAX_OVERFLOW", "20"))
    
    def get_table_name(self, base_table_name: str) -> str:
        """Get prefixed table name for environment"""
        return f"{self.table_prefix}{base_table_name}"
    
    @property
    def url(self) -> str:
        """Get the database URL for SQLAlchemy"""
        return f"postgresql+psycopg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"
    
    @property
    def agno_url(self) -> str:
        """Get the database URL formatted for Agno PostgresDb"""
        return self.url
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_test(self) -> bool:
        """Check if running in test environment (including CI)"""
        return self.environment in [Environment.CI, Environment.TEST]
    
    def get_environment_info(self) -> dict:
        """Get comprehensive environment information"""
        return {
            "environment": self.environment,
            "database": self.database,
            "table_prefix": self.table_prefix,
            "host": self.host,
            "port": self.port,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "is_production": self.is_production,
            "is_test": self.is_test
        }

class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._engine = None
        self._session_factory = None
        self._agno_db = None
    
    @property
    def engine(self):
        """Get or create SQLAlchemy engine with connection pooling"""
        if self._engine is None:
            self._engine = create_engine(
                self.config.url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=True,  # Verify connections before use
                echo=os.getenv("DB_ECHO", "false").lower() == "true"
            )
        return self._engine
    
    @property
    def session_factory(self):
        """Get or create session factory"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory
    
    @property
    def agno_db(self) -> PostgresDb:
        """Get or create Agno PostgresDb instance with environment-specific table names"""
        if self._agno_db is None:
            self._agno_db = PostgresDb(
                db_url=self.config.agno_url,
                # Environment-specific Agno table configurations
                session_table=self.config.get_table_name("agent_sessions"),
                run_table=self.config.get_table_name("agent_runs"),
                message_table=self.config.get_table_name("agent_messages"),
                memory_table=self.config.get_table_name("user_memories"),
                summary_table=self.config.get_table_name("session_summaries")
            )
        return self._agno_db
    
    @contextmanager
    def get_session(self):
        """Get a database session with automatic cleanup"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def check_extensions(self) -> dict:
        """Check if required PostgreSQL extensions are installed"""
        extensions = {
            'uuid-ossp': False,
            'pgvector': False,
            'pg_trgm': False
        }
        
        try:
            with self.engine.connect() as conn:
                for ext in extensions.keys():
                    result = conn.execute(
                        text("SELECT 1 FROM pg_extension WHERE extname = :ext"),
                        {"ext": ext}
                    )
                    extensions[ext] = result.scalar() is not None
        except Exception as e:
            logger.error(f"Failed to check extensions: {e}")
        
        return extensions
    
    def initialize_schema(self, schema_file: str = "database/schema.sql"):
        """Initialize database schema from SQL file"""
        try:
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            with self.engine.connect() as conn:
                # Execute schema in a transaction
                trans = conn.begin()
                try:
                    # Split by semicolon and execute each statement
                    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
                    for statement in statements:
                        if statement:
                            conn.execute(text(statement))
                    trans.commit()
                    logger.info("Database schema initialized successfully")
                    return True
                except Exception as e:
                    trans.rollback()
                    logger.error(f"Schema initialization failed: {e}")
                    raise
        except FileNotFoundError:
            logger.error(f"Schema file not found: {schema_file}")
            return False
        except Exception as e:
            logger.error(f"Schema initialization error: {e}")
            return False

# Global database manager instance
db_manager = DatabaseManager()

def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    return db_manager

def get_agno_db() -> PostgresDb:
    """Get Agno PostgresDb instance for agent session management"""
    return db_manager.agno_db

# Health check functions
def check_database_health() -> dict:
    """Comprehensive database health check"""
    health = {
        'connection': False,
        'extensions': {},
        'tables': {},
        'performance': {}
    }
    
    try:
        # Test connection
        health['connection'] = db_manager.test_connection()
        
        # Check extensions
        health['extensions'] = db_manager.check_extensions()
        
        # Check critical tables exist
        with db_manager.engine.connect() as conn:
            tables_to_check = [
                'projects', 'interview_responses', 'interview_themes',
                'agent_sessions', 'agent_messages', 'user_memories'
            ]
            
            for table in tables_to_check:
                result = conn.execute(
                    text("SELECT 1 FROM information_schema.tables WHERE table_name = :table"),
                    {"table": table}
                )
                health['tables'][table] = result.scalar() is not None
        
        # Basic performance check
        with db_manager.engine.connect() as conn:
            import time
            start = time.time()
            conn.execute(text("SELECT COUNT(*) FROM projects"))
            health['performance']['query_time_ms'] = (time.time() - start) * 1000
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health['error'] = str(e)
    
    return health

if __name__ == "__main__":
    # Test the database configuration
    print("Testing database configuration...")
    
    config = DatabaseConfig()
    print(f"Database URL: {config.url}")
    
    manager = DatabaseManager(config)
    
    if manager.test_connection():
        print("✅ Database connection successful")
        
        extensions = manager.check_extensions()
        print("Extensions status:")
        for ext, installed in extensions.items():
            status = "✅" if installed else "❌"
            print(f"  {status} {ext}")
    else:
        print("❌ Database connection failed")
    
    # Health check
    health = check_database_health()
    print(f"\nHealth check: {health}")

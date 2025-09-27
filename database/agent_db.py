"""
Smart Agent Database Configuration
Automatically chooses the right database based on environment:
- Development/Testing: InMemoryDb (fast, no persistence)
- Production: PostgresDb (persistent, scalable)

This file implements the decision made in September 2025 to use:
- InMemoryDb for development (current setup)
- PostgresDb for production (migration required)
"""
import os
from agno.db.in_memory import InMemoryDb
from agno.db.postgres import PostgresDb
from database.config import DatabaseManager, DatabaseConfig

def get_agent_db():
    """
    Returns appropriate database for current environment.
    
    Environment Logic:
    - production: PostgresDb (persistent, multi-user, scalable)
    - ci/test/development: InMemoryDb (fast, temporary, single-user)
    
    Returns:
        Database instance appropriate for current environment
    """
    env = os.getenv("LEGACY_ENV", "test")
    
    if env == "production":
        # Production: Use PostgreSQL for persistence and scalability
        print(f"🗄️ Using PostgresDb for {env} environment")
        config = DatabaseConfig(environment=env)
        manager = DatabaseManager(config)
        return manager.agno_db
    else:
        # Development/Testing: Use InMemoryDb for speed and simplicity
        print(f"💾 Using InMemoryDb for {env} environment")
        return InMemoryDb()

def get_agent_db_info():
    """Get information about current database configuration"""
    env = os.getenv("LEGACY_ENV", "test")
    db = get_agent_db()
    
    return {
        "environment": env,
        "database_type": type(db).__name__,
        "is_production": env == "production",
        "persistence": env == "production",
        "multi_user": env == "production"
    }

# For backwards compatibility and easy testing
def create_development_db():
    """Explicitly create InMemoryDb for development"""
    return InMemoryDb()

def create_production_db():
    """Explicitly create PostgresDb for production"""
    config = DatabaseConfig(environment="production")
    manager = DatabaseManager(config)
    return manager.agno_db

if __name__ == "__main__":
    # Test the configuration
    print("🔍 Agent Database Configuration Test")
    print("=" * 40)
    
    info = get_agent_db_info()
    for key, value in info.items():
        print(f"{key}: {value}")
    
    print(f"\nCurrent database: {type(get_agent_db()).__name__}")
    
    # Test different environments
    print("\n🧪 Environment Testing:")
    for test_env in ["ci", "test", "development", "production"]:
        original_env = os.getenv("LEGACY_ENV")
        os.environ["LEGACY_ENV"] = test_env
        
        db = get_agent_db()
        print(f"{test_env}: {type(db).__name__}")
        
        # Restore original environment
        if original_env:
            os.environ["LEGACY_ENV"] = original_env
        else:
            os.environ.pop("LEGACY_ENV", None)

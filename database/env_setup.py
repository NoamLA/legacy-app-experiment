"""
Multi-environment database setup for Legacy Interview App
Handles CI/Test/Production database initialization and management
"""
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from database.config import DatabaseManager, DatabaseConfig, Environment, check_database_health
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EnvironmentManager:
    """Manages multi-environment database setup"""
    
    def __init__(self):
        self.environments = [Environment.CI, Environment.TEST, Environment.PRODUCTION, Environment.DEVELOPMENT]
    
    def create_all_databases(self) -> bool:
        """Create databases for all environments"""
        print("🗄️ Creating databases for all environments...")
        
        success = True
        for env in self.environments:
            if not self._create_database_for_env(env):
                success = False
        
        return success
    
    def _create_database_for_env(self, env: Environment) -> bool:
        """Create database for specific environment"""
        config = DatabaseConfig(environment=env.value)
        
        print(f"📦 Creating database: {config.database}")
        
        try:
            # Connect to default postgres database to create our database
            default_config = DatabaseConfig(environment=env.value)
            default_config.database = "postgres"  # Connect to default database
            
            manager = DatabaseManager(default_config)
            
            with manager.engine.connect() as conn:
                # Close any existing connections to the database
                conn.execute(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity 
                    WHERE datname = '{config.database}' AND pid <> pg_backend_pid()
                """)
                
                # Create database if it doesn't exist
                result = conn.execute(f"""
                    SELECT 1 FROM pg_database WHERE datname = '{config.database}'
                """)
                
                if not result.scalar():
                    conn.execute(f"CREATE DATABASE {config.database}")
                    print(f"✅ Created database: {config.database}")
                else:
                    print(f"📄 Database already exists: {config.database}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create database {config.database}: {e}")
            return False
    
    def initialize_all_schemas(self) -> bool:
        """Initialize schemas for all environments"""
        print("🏗️ Initializing schemas for all environments...")
        
        success = True
        for env in self.environments:
            if not self._initialize_schema_for_env(env):
                success = False
        
        return success
    
    def _initialize_schema_for_env(self, env: Environment) -> bool:
        """Initialize schema for specific environment"""
        config = DatabaseConfig(environment=env.value)
        manager = DatabaseManager(config)
        
        print(f"🔧 Initializing schema for {env.value}: {config.database}")
        
        try:
            if not manager.test_connection():
                print(f"❌ Cannot connect to {config.database}")
                return False
            
            # Initialize schema using multi-environment schema file
            schema_path = Path(__file__).parent / "schema_multi_env.sql"
            if schema_path.exists():
                success = manager.initialize_schema(str(schema_path))
                if success:
                    print(f"✅ Schema initialized for {env.value}")
                    return True
                else:
                    print(f"❌ Failed to initialize schema for {env.value}")
                    return False
            else:
                print(f"❌ Schema file not found: {schema_path}")
                return False
                
        except Exception as e:
            print(f"❌ Schema initialization failed for {env.value}: {e}")
            return False
    
    def health_check_all_environments(self) -> Dict[str, Dict[str, Any]]:
        """Run health check on all environments"""
        print("🏥 Running health checks on all environments...")
        
        results = {}
        
        for env in self.environments:
            config = DatabaseConfig(environment=env.value)
            print(f"\n🔍 Checking {env.value} environment ({config.database})...")
            
            # Temporarily set environment for health check
            original_env = os.getenv("LEGACY_ENV")
            os.environ["LEGACY_ENV"] = env.value
            
            try:
                health = check_database_health()
                results[env.value] = health
                
                # Print summary
                status = "✅" if health.get('connection') else "❌"
                print(f"{status} {env.value}: Connection = {health.get('connection')}")
                
                if health.get('tables'):
                    table_count = sum(1 for exists in health['tables'].values() if exists)
                    total_tables = len(health['tables'])
                    print(f"  📊 Tables: {table_count}/{total_tables}")
                
                if health.get('performance'):
                    query_time = health['performance'].get('query_time_ms', 0)
                    print(f"  ⚡ Query time: {query_time:.2f}ms")
                    
            except Exception as e:
                results[env.value] = {'error': str(e), 'connection': False}
                print(f"❌ {env.value}: Health check failed - {e}")
            
            finally:
                # Restore original environment
                if original_env:
                    os.environ["LEGACY_ENV"] = original_env
                else:
                    os.environ.pop("LEGACY_ENV", None)
        
        return results
    
    def cleanup_environment(self, env: Environment) -> bool:
        """Clean up specific environment"""
        config = DatabaseConfig(environment=env.value)
        
        print(f"🧹 Cleaning up {env.value} environment...")
        
        try:
            manager = DatabaseManager(config)
            
            with manager.engine.connect() as conn:
                # Use the cleanup function from our schema
                conn.execute(f"SELECT cleanup_environment_tables('{config.table_prefix}')")
                print(f"✅ Cleaned up {env.value} environment")
                return True
                
        except Exception as e:
            print(f"❌ Failed to cleanup {env.value}: {e}")
            return False
    
    def get_environment_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all environments"""
        status = {}
        
        for env in self.environments:
            config = DatabaseConfig(environment=env.value)
            manager = DatabaseManager(config)
            
            env_status = {
                'database': config.database,
                'table_prefix': config.table_prefix,
                'connection': False,
                'table_count': 0,
                'environment_info': config.get_environment_info()
            }
            
            try:
                env_status['connection'] = manager.test_connection()
                
                if env_status['connection']:
                    with manager.engine.connect() as conn:
                        result = conn.execute(f"""
                            SELECT table_count FROM get_environment_info('{config.table_prefix}')
                        """)
                        row = result.fetchone()
                        if row:
                            env_status['table_count'] = row[0]
                            
            except Exception as e:
                env_status['error'] = str(e)
            
            status[env.value] = env_status
        
        return status

def create_environment_specific_env_files():
    """Create environment-specific .env files"""
    print("📄 Creating environment-specific .env files...")
    
    base_path = Path(__file__).parent.parent
    
    env_configs = {
        'ci': {
            'LEGACY_ENV': 'ci',
            'DB_POOL_SIZE': '2',
            'DB_MAX_OVERFLOW': '2',
            'DB_ECHO': 'false'
        },
        'test': {
            'LEGACY_ENV': 'test',
            'DB_POOL_SIZE': '5',
            'DB_MAX_OVERFLOW': '10',
            'DB_ECHO': 'false'
        },
        'production': {
            'LEGACY_ENV': 'production',
            'DB_POOL_SIZE': '20',
            'DB_MAX_OVERFLOW': '50',
            'DB_ECHO': 'false'
        },
        'development': {
            'LEGACY_ENV': 'development',
            'DB_POOL_SIZE': '10',
            'DB_MAX_OVERFLOW': '20',
            'DB_ECHO': 'true'
        }
    }
    
    for env_name, config in env_configs.items():
        env_file = base_path / f".env.{env_name}"
        
        env_content = f"""# Legacy Interview App - {env_name.upper()} Environment

# Environment Configuration
LEGACY_ENV={config['LEGACY_ENV']}

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_BASE_NAME=legacy_interview
DB_USER=legacy_user
DB_PASSWORD=legacy_pass
DB_SSL_MODE=prefer

# Database Connection Pool
DB_POOL_SIZE={config['DB_POOL_SIZE']}
DB_MAX_OVERFLOW={config['DB_MAX_OVERFLOW']}
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Debug settings
DB_ECHO={config['DB_ECHO']}

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# FastAPI settings
SECRET_KEY=your_secret_key_here
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Created {env_file}")

def main():
    """Main multi-environment setup function"""
    print("🚀 Legacy Interview App Multi-Environment Database Setup")
    print("=" * 60)
    
    # Create environment-specific .env files
    create_environment_specific_env_files()
    
    # Initialize environment manager
    env_manager = EnvironmentManager()
    
    # Step 1: Create all databases
    if not env_manager.create_all_databases():
        print("❌ Failed to create all databases")
        return False
    
    # Step 2: Initialize all schemas
    if not env_manager.initialize_all_schemas():
        print("❌ Failed to initialize all schemas")
        return False
    
    # Step 3: Run health checks
    health_results = env_manager.health_check_all_environments()
    
    # Step 4: Show environment status
    print("\n📊 Environment Status Summary:")
    print("=" * 40)
    
    status = env_manager.get_environment_status()
    for env_name, env_status in status.items():
        connection_status = "✅" if env_status['connection'] else "❌"
        print(f"{connection_status} {env_name.upper()}")
        print(f"  Database: {env_status['database']}")
        print(f"  Tables: {env_status['table_count']}")
        print(f"  Prefix: '{env_status['table_prefix']}'")
        
        if 'error' in env_status:
            print(f"  Error: {env_status['error']}")
        print()
    
    print("🎉 Multi-environment database setup completed!")
    print("\nNext steps:")
    print("1. Update .env files with actual API keys")
    print("2. Set LEGACY_ENV environment variable:")
    print("   - export LEGACY_ENV=test    # For testing (default)")
    print("   - export LEGACY_ENV=ci      # For CI/CD")
    print("   - export LEGACY_ENV=production  # For production")
    print("3. Run 'python backend/main.py' to start the application")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

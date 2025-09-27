"""
Database setup and initialization script for Legacy Interview App
"""
import os
import sys
import subprocess
import time
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from database.config import DatabaseManager, DatabaseConfig, check_database_health
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_postgresql_installed():
    """Check if PostgreSQL is installed"""
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PostgreSQL found: {result.stdout.strip()}")
            return True
        else:
            print("❌ PostgreSQL not found")
            return False
    except FileNotFoundError:
        print("❌ PostgreSQL not installed or not in PATH")
        return False

def check_docker_available():
    """Check if Docker is available for running PostgreSQL container"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker found: {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker not found")
            return False
    except FileNotFoundError:
        print("❌ Docker not installed or not in PATH")
        return False

def start_postgres_container():
    """Start PostgreSQL container with pgvector extension"""
    print("🐳 Starting PostgreSQL container with pgvector...")
    
    container_name = "legacy-postgres"
    
    # Check if container already exists
    result = subprocess.run(
        ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
        capture_output=True, text=True
    )
    
    if container_name in result.stdout:
        print(f"📦 Container {container_name} already exists")
        # Start if not running
        subprocess.run(['docker', 'start', container_name])
    else:
        # Create and start new container
        cmd = [
            'docker', 'run', '-d',
            '--name', container_name,
            '-e', 'POSTGRES_DB=legacy_interview',
            '-e', 'POSTGRES_USER=legacy_user',
            '-e', 'POSTGRES_PASSWORD=legacy_pass',
            '-e', 'PGDATA=/var/lib/postgresql/data/pgdata',
            '-v', 'legacy_pgdata:/var/lib/postgresql/data',
            '-p', '5432:5432',
            'agnohq/pgvector:16'  # Agno's PostgreSQL + pgvector image
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PostgreSQL container started: {result.stdout.strip()}")
        else:
            print(f"❌ Failed to start container: {result.stderr}")
            return False
    
    # Wait for PostgreSQL to be ready
    print("⏳ Waiting for PostgreSQL to be ready...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            config = DatabaseConfig()
            manager = DatabaseManager(config)
            if manager.test_connection():
                print("✅ PostgreSQL is ready!")
                return True
        except Exception:
            pass
        time.sleep(1)
    
    print("❌ PostgreSQL failed to start within 30 seconds")
    return False

def create_env_file():
    """Create .env file with database configuration"""
    env_path = Path(__file__).parent.parent / ".env"
    
    if env_path.exists():
        print("📄 .env file already exists")
        return
    
    env_content = """# Legacy Interview App Environment Variables

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=legacy_interview
DB_USER=legacy_user
DB_PASSWORD=legacy_pass
DB_SSL_MODE=prefer

# Database Connection Pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Debug settings
DB_ECHO=false

# OpenAI API Key (add your key here)
OPENAI_API_KEY=your_openai_api_key_here

# FastAPI settings
SECRET_KEY=your_secret_key_here
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Created .env file at {env_path}")
    print("⚠️  Please update the .env file with your actual API keys!")

def initialize_database():
    """Initialize database schema and tables"""
    print("🗄️  Initializing database schema...")
    
    try:
        config = DatabaseConfig()
        manager = DatabaseManager(config)
        
        # Test connection first
        if not manager.test_connection():
            print("❌ Cannot connect to database")
            return False
        
        # Check extensions
        extensions = manager.check_extensions()
        print("📦 Extension status:")
        for ext, installed in extensions.items():
            status = "✅" if installed else "❌"
            print(f"   {status} {ext}")
        
        # Initialize schema
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            success = manager.initialize_schema(str(schema_path))
            if success:
                print("✅ Database schema initialized successfully")
                return True
            else:
                print("❌ Failed to initialize database schema")
                return False
        else:
            print(f"❌ Schema file not found: {schema_path}")
            return False
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def run_health_check():
    """Run comprehensive database health check"""
    print("🏥 Running database health check...")
    
    health = check_database_health()
    
    print(f"Connection: {'✅' if health['connection'] else '❌'}")
    
    if health.get('extensions'):
        print("Extensions:")
        for ext, installed in health['extensions'].items():
            status = "✅" if installed else "❌"
            print(f"  {status} {ext}")
    
    if health.get('tables'):
        print("Tables:")
        for table, exists in health['tables'].items():
            status = "✅" if exists else "❌"
            print(f"  {status} {table}")
    
    if health.get('performance'):
        query_time = health['performance'].get('query_time_ms', 0)
        print(f"Query performance: {query_time:.2f}ms")
    
    if health.get('error'):
        print(f"❌ Health check error: {health['error']}")
        return False
    
    return health['connection']

def main():
    """Main setup function"""
    print("🚀 Legacy Interview App Database Setup")
    print("=" * 50)
    
    # Step 1: Create .env file
    create_env_file()
    
    # Step 2: Check if PostgreSQL is available
    postgres_available = check_postgresql_installed()
    docker_available = check_docker_available()
    
    if not postgres_available and not docker_available:
        print("❌ Neither PostgreSQL nor Docker is available")
        print("Please install PostgreSQL or Docker to continue")
        return False
    
    # Step 3: Start PostgreSQL (container if no local installation)
    if not postgres_available and docker_available:
        if not start_postgres_container():
            return False
    
    # Step 4: Initialize database
    if not initialize_database():
        return False
    
    # Step 5: Run health check
    if not run_health_check():
        return False
    
    print("\n🎉 Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Update your .env file with actual API keys")
    print("2. Run 'python backend/main.py' to start the application")
    print("3. The app will now use PostgreSQL for persistent storage")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

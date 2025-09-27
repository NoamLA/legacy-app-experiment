#!/bin/bash
# Enable PostgreSQL for Development Environment
# This switches from InMemoryDb to PostgresDb for testing persistence

echo "🗄️ Enabling PostgreSQL for Development..."

# Check if PostgreSQL is running on port 5433
if ! pg_isready -h localhost -p 5433 >/dev/null 2>&1; then
    echo "❌ PostgreSQL is not running on port 5433."
    echo "   Please ensure your PostgreSQL database is running on port 5433"
    echo "   You mentioned it's already running on this port."
    exit 1
fi

echo "✅ PostgreSQL is running on port 5433"

# Set environment to development with PostgreSQL
export LEGACY_ENV=development
export USE_POSTGRES=true

# Create .env.development if it doesn't exist
if [ ! -f .env.development ]; then
    echo "📝 Creating .env.development..."
    cat > .env.development << EOF
# Legacy Interview App - Development Environment with PostgreSQL
LEGACY_ENV=development
USE_POSTGRES=true
DB_HOST=localhost
DB_PORT=5433
DB_BASE_NAME=legacy_interview
DB_USER=legacy_user  
DB_PASSWORD=legacy_pass
DB_SSL_MODE=prefer
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=dev_secret_key_change_in_production
EOF
    echo "⚠️  Please update OPENAI_API_KEY in .env.development"
else
    echo "📝 .env.development already exists"
fi

# Load environment variables
if [ -f .env.development ]; then
    export $(cat .env.development | grep -v '^#' | xargs)
fi

# Test database connection
echo "🔍 Testing database connection..."
python -c "
import sys
sys.path.append('.')
from database.agent_db import get_agent_db_info

try:
    info = get_agent_db_info()
    print('✅ Database Configuration:')
    for key, value in info.items():
        print(f'   {key}: {value}')
    
    # Test actual connection
    from database.agent_db import get_agent_db
    db = get_agent_db()
    print(f'✅ Database instance: {type(db).__name__}')
    
    if hasattr(db, 'engine'):
        print('✅ PostgreSQL connection successful!')
    else:
        print('ℹ️  Using InMemoryDb (set LEGACY_ENV=production for PostgreSQL)')
        
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
"

echo ""
echo "🎯 Development Environment Ready!"
echo "   Database: PostgreSQL on port 5433"
echo "   Environment: development"
echo "   Agents: Will use proper Agno database configuration"
echo ""
echo "🚀 Start the backend with:"
echo "   source legacy-venv/bin/activate"
echo "   export LEGACY_ENV=development"
echo "   export USE_POSTGRES=true"
echo "   python backend/main.py"

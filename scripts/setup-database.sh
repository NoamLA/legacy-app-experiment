#!/bin/bash
# Database Setup Script for Legacy Interview App
# Creates PostgreSQL database and user for development

echo "🗄️ Setting up Legacy Interview App Database..."

# Database configuration
DB_NAME="legacy_interview_dev"
DB_USER="legacy_user"
DB_PASSWORD="legacy_pass"

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first:"
    echo "   brew services start postgresql"
    echo "   # OR"
    echo "   pg_ctl -D /usr/local/var/postgres start"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Create user if it doesn't exist
echo "👤 Creating database user..."
psql -h localhost -p 5432 -U postgres -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';" 2>/dev/null || {
    echo "ℹ️  User ${DB_USER} already exists or couldn't create (this is usually fine)"
}

# Grant privileges
psql -h localhost -p 5432 -U postgres -c "ALTER USER ${DB_USER} CREATEDB;" 2>/dev/null || {
    echo "ℹ️  Could not grant CREATEDB to ${DB_USER} (this might be fine)"
}

# Create database if it doesn't exist
echo "🗄️ Creating database..."
psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};" 2>/dev/null || {
    echo "ℹ️  Database ${DB_NAME} already exists (this is fine)"
}

# Grant all privileges
psql -h localhost -p 5432 -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};" 2>/dev/null

echo "✅ Database setup complete!"
echo ""
echo "📋 Database Details:"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   Database: ${DB_NAME}"
echo "   User: ${DB_USER}"
echo "   Password: ${DB_PASSWORD}"
echo ""
echo "🔧 Next steps:"
echo "1. Copy env-template.txt to .env.development"
echo "2. Update OPENAI_API_KEY in .env.development"
echo "3. Run the application with: python backend/main.py"

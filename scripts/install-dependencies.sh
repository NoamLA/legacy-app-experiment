#!/bin/bash
# Dependency installation script for Legacy Interview App

set -e  # Exit on any error

echo "📦 Legacy Interview App - Dependency Installation"
echo "==============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [[ ! -f "requirements.txt" ]]; then
    echo -e "${RED}❌ requirements.txt not found. Please run this script from the project root.${NC}"
    exit 1
fi

# Check if virtual environment exists
if [[ ! -d "legacy-venv" ]]; then
    echo -e "${YELLOW}📁 Creating Python virtual environment...${NC}"
    python3 -m venv legacy-venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🔄 Activating virtual environment...${NC}"
source legacy-venv/bin/activate

# Upgrade pip
echo -e "${BLUE}⬆️  Upgrading pip...${NC}"
pip install --upgrade pip

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt

echo -e "${GREEN}✅ Python dependencies installed${NC}"

# Check if Node.js is available for frontend
if command -v node &> /dev/null; then
    echo -e "${BLUE}📦 Installing Node.js dependencies...${NC}"
    npm install
    echo -e "${GREEN}✅ Node.js dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  Node.js not found. Frontend dependencies not installed.${NC}"
    echo -e "${YELLOW}    Install Node.js to run the React frontend.${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Dependency installation completed!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Copy env-template.txt to .env and update with your API keys"
echo "2. Set up the database: python database/env_setup.py"
echo "3. Run tests: ./scripts/run-tests.sh"
echo "4. Start backend: ./scripts/start-backend.py"
echo "5. Start frontend: ./scripts/start-frontend.sh"

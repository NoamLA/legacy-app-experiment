#!/bin/bash

# Helper script to activate the virtual environment
# Usage: source activate-venv.sh

if [ ! -d "legacy-venv" ]; then
    echo "❌ Virtual environment not found. Run 'python setup.py' first."
    return 1
fi

echo "📦 Activating virtual environment..."
source legacy-venv/bin/activate

if [ "$VIRTUAL_ENV" != "" ]; then
    echo "✅ Virtual environment activated: $(basename $VIRTUAL_ENV)"
    echo "💡 To deactivate, run: deactivate"
else
    echo "❌ Failed to activate virtual environment"
    return 1
fi

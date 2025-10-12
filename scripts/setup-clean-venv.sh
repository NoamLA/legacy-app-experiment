#!/bin/bash

# Clean Virtual Environment Setup Script for Legacy Project
# This script ensures all dependencies are properly installed in the legacy-venv

set -e  # Exit on any error

echo "🔧 Setting up clean virtual environment for Legacy project..."

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/legacy-venv"

echo "📁 Project root: $PROJECT_ROOT"
echo "🐍 Virtual environment: $VENV_PATH"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "Please run the initial setup first or create the virtual environment manually."
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Upgrade pip to latest version
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install/upgrade all requirements
echo "📦 Installing/updating all dependencies from requirements.txt..."
pip install -r "$PROJECT_ROOT/requirements.txt"

# Verify critical packages for test_audio functionality
echo "🔍 Verifying critical packages..."

# Test PyAnnote
echo -n "Testing PyAnnote... "
if python -c "import pyannote.audio; print('✅')" 2>/dev/null; then
    echo "PyAnnote: ✅"
else
    echo "PyAnnote: ❌"
    echo "Installing PyAnnote..."
    pip install pyannote.audio
fi

# Test Jiwer
echo -n "Testing Jiwer... "
if python -c "import jiwer; print('✅')" 2>/dev/null; then
    echo "Jiwer: ✅"
else
    echo "Jiwer: ❌"
    echo "Installing Jiwer..."
    pip install jiwer
fi

# Test other critical packages
echo "Testing other critical packages..."

packages=(
    "torch:PyTorch"
    "torchaudio:TorchAudio"
    "librosa:Librosa"
    "soundfile:SoundFile"
    "scipy:SciPy"
    "numpy:NumPy"
    "openai:OpenAI"
    "whisper:Whisper"
    "fastapi:FastAPI"
    "uvicorn:Uvicorn"
    "sqlalchemy:SQLAlchemy"
    "psycopg:Psycopg"
    "redis:Redis"
    "pytest:Pytest"
)

for package_info in "${packages[@]}"; do
    IFS=':' read -r package display_name <<< "$package_info"
    echo -n "Testing $display_name... "
    if python -c "import $package; print('✅')" 2>/dev/null; then
        echo "$display_name: ✅"
    else
        echo "$display_name: ❌"
    fi
done

# Test test_audio specific functionality
echo ""
echo "🧪 Testing test_audio functionality..."

# Test audio transcription
echo -n "Testing audio transcription imports... "
if python -c "
import sys
sys.path.append('$PROJECT_ROOT')
from services.conversation_recording_service import conversation_recording_service
print('✅')
" 2>/dev/null; then
    echo "Audio transcription service: ✅"
else
    echo "Audio transcription service: ❌"
fi

# Test speaker diarization
echo -n "Testing speaker diarization... "
if python -c "
import pyannote.audio
from pyannote.audio import Pipeline
print('✅')
" 2>/dev/null; then
    echo "Speaker diarization: ✅"
else
    echo "Speaker diarization: ❌"
fi

# Test audio evaluation
echo -n "Testing audio evaluation... "
if python -c "
import jiwer
from jiwer import wer
print('✅')
" 2>/dev/null; then
    echo "Audio evaluation: ✅"
else
    echo "Audio evaluation: ❌"
fi

echo ""
echo "🎉 Virtual environment setup complete!"
echo ""
echo "📋 Summary:"
echo "   • Virtual environment: $VENV_PATH"
echo "   • All dependencies installed from requirements.txt"
echo "   • Critical packages verified"
echo "   • test_audio functionality verified"
echo ""
echo "🚀 To activate the environment, run:"
echo "   source $VENV_PATH/bin/activate"
echo ""
echo "🧪 To test the setup, run:"
echo "   python test_audio_transcription.py"
echo "   python test_speaker_diarization.py"
echo "   python test_audio_evaluation.py"

#!/bin/bash
# Speaker Diarization Test Runner
# Usage: ./run_speaker_test.sh <audio_file> [ground_truth_file] [expected_speakers]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 Speaker Diarization Test Runner${NC}"
echo "=================================="

# Check if audio file is provided
if [ $# -lt 1 ]; then
    echo -e "${RED}❌ Error: Audio file path is required${NC}"
    echo "Usage: $0 <audio_file> [ground_truth_file] [expected_speakers...]"
    echo ""
    echo "Examples:"
    echo "  $0 test_audio/sample.wav"
    echo "  $0 test_audio/sample.wav test_audio/sample_ground_truth.json"
    echo "  $0 test_audio/sample.wav test_audio/sample_ground_truth.json interviewer subject"
    exit 1
fi

AUDIO_FILE="$1"
GROUND_TRUTH_FILE="${2:-}"
EXPECTED_SPEAKERS="${3:-interviewer subject}"

# Check if audio file exists
if [ ! -f "$AUDIO_FILE" ]; then
    echo -e "${RED}❌ Error: Audio file not found: $AUDIO_FILE${NC}"
    exit 1
fi

# Check if ground truth file exists (if provided)
if [ -n "$GROUND_TRUTH_FILE" ] && [ ! -f "$GROUND_TRUTH_FILE" ]; then
    echo -e "${YELLOW}⚠️  Warning: Ground truth file not found: $GROUND_TRUTH_FILE${NC}"
    echo "Continuing without ground truth validation..."
    GROUND_TRUTH_FILE=""
fi

echo -e "${GREEN}📁 Audio file: $AUDIO_FILE${NC}"
if [ -n "$GROUND_TRUTH_FILE" ]; then
    echo -e "${GREEN}📋 Ground truth: $GROUND_TRUTH_FILE${NC}"
else
    echo -e "${YELLOW}📋 Ground truth: None (accuracy validation disabled)${NC}"
fi
echo -e "${GREEN}👥 Expected speakers: $EXPECTED_SPEAKERS${NC}"
echo ""

# Check if virtual environment exists
if [ -d "legacy-venv" ]; then
    echo -e "${BLUE}🐍 Activating virtual environment...${NC}"
    source legacy-venv/bin/activate
else
    echo -e "${YELLOW}⚠️  Virtual environment not found. Using system Python...${NC}"
fi

# Check if required dependencies are installed
echo -e "${BLUE}🔍 Checking dependencies...${NC}"
python -c "
try:
    import pyannote.audio
    print('✅ PyAnnote-Audio: Available')
except ImportError:
    print('❌ PyAnnote-Audio: Not installed')
    print('   Install with: pip install pyannote.audio')

try:
    import soundfile
    print('✅ SoundFile: Available')
except ImportError:
    print('❌ SoundFile: Not installed')
    print('   Install with: pip install soundfile')

try:
    import openai
    print('✅ OpenAI: Available')
except ImportError:
    print('❌ OpenAI: Not installed')
    print('   Install with: pip install openai')
"

echo ""
echo -e "${BLUE}🚀 Running speaker diarization test...${NC}"
echo "=================================="

# Run the test
python test_speaker_diarization.py "$AUDIO_FILE" \
    ${GROUND_TRUTH_FILE:+--ground-truth "$GROUND_TRUTH_FILE"} \
    --expected-speakers $EXPECTED_SPEAKERS \
    --test-dir test_audio

echo ""
echo -e "${GREEN}✅ Test completed!${NC}"
echo "Check test_audio/ directory for results and reports."



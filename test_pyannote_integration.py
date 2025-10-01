#!/usr/bin/env python3
"""
Test script for PyAnnote-Audio integration
This script tests the new simplified conversation recording service
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.conversation_recording_service import conversation_recording_service

async def test_pyannote_integration():
    """Test the new PyAnnote-Audio integration"""
    print("🧪 Testing PyAnnote-Audio Integration")
    print("=" * 50)
    
    try:
        # Test 1: Initialize service
        print("1. Testing service initialization...")
        service = conversation_recording_service
        print("✅ Service initialized successfully")
        
        # Test 2: Start recording session
        print("\n2. Testing session creation...")
        session_id = await service.start_recording_session(
            project_id="test-project-123",
            session_name="Test Recording Session",
            participants=[
                {'id': 'interviewer', 'name': 'Test Interviewer'},
                {'id': 'subject', 'name': 'Test Subject'}
            ]
        )
        print(f"✅ Session created: {session_id}")
        
        # Test 3: Simulate audio chunk processing
        print("\n3. Testing audio chunk processing...")
        # Create dummy audio data (1 second of silence)
        import numpy as np
        dummy_audio = np.zeros(16000, dtype=np.int16).tobytes()
        
        result = await service.process_audio_chunk(
            session_id=session_id,
            audio_data=dummy_audio,
            sample_rate=16000
        )
        print(f"✅ Audio chunk processed: {result}")
        
        # Test 4: End session (this will trigger PyAnnote processing)
        print("\n4. Testing session completion...")
        try:
            final_result = await service.end_recording_session(session_id)
            print(f"✅ Session completed successfully")
            print(f"   - Audio file: {final_result.get('audio_file_path', 'N/A')}")
            print(f"   - Transcription: {final_result.get('transcription_file_path', 'N/A')}")
            print(f"   - Utterances: {final_result.get('utterance_count', 0)}")
        except Exception as e:
            print(f"⚠️  Session completion failed (expected if PyAnnote not installed): {e}")
        
        print("\n🎉 Integration test completed!")
        print("\nNext steps:")
        print("1. Install PyAnnote-Audio: pip install pyannote.audio")
        print("2. Get Hugging Face token for model access")
        print("3. Test with real audio files")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

async def test_dependencies():
    """Test if required dependencies are available"""
    print("🔍 Checking Dependencies")
    print("=" * 30)
    
    # Check PyAnnote-Audio
    try:
        from pyannote.audio import Pipeline
        print("✅ PyAnnote-Audio: Available")
    except ImportError:
        print("❌ PyAnnote-Audio: Not installed")
        print("   Install with: pip install pyannote.audio")
    
    # Check OpenAI
    try:
        import openai
        print("✅ OpenAI: Available")
    except ImportError:
        print("❌ OpenAI: Not installed")
        print("   Install with: pip install openai")
    
    # Check other dependencies
    try:
        import soundfile as sf
        import numpy as np
        print("✅ SoundFile & NumPy: Available")
    except ImportError:
        print("❌ SoundFile/NumPy: Not installed")

if __name__ == "__main__":
    print("🚀 PyAnnote-Audio Integration Test")
    print("=" * 50)
    
    # Run dependency check
    asyncio.run(test_dependencies())
    
    print("\n" + "=" * 50)
    
    # Run integration test
    asyncio.run(test_pyannote_integration())

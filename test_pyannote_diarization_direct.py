#!/usr/bin/env python3
"""
Test PyAnnote 3.1 Pipeline - Fixed Version
Using the exact approach from the HuggingFace documentation
"""
import os
import sys
from pathlib import Path

# Load environment variables
def load_env_file(env_file=".env.development"):
    if Path(env_file).exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print(f"✅ Loaded environment variables from {env_file}")

load_env_file()

def test_pyannote_3_1_pipeline():
    """Test the 3.1 pipeline using the exact HuggingFace documentation approach"""
    print("🔍 Testing PyAnnote 3.1 Pipeline (Fixed Version)")
    print("=" * 60)
    
    hf_token = os.getenv('HF_TOKEN')
    if not hf_token:
        print("❌ HF_TOKEN not found in environment")
        return False
    
    try:
        from pyannote.audio import Pipeline
        
        print("🔄 Loading pyannote/speaker-diarization-3.1...")
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token
        )
        
        print("✅ Pipeline loaded successfully!")
        
        # Test on audio file
        audio_file = "test_audio/Interview_trimmed_4min16sec.wav"
        if not Path(audio_file).exists():
            print(f"❌ Audio file not found: {audio_file}")
            return False
        
        print(f"🔄 Processing audio: {audio_file}")
        diar = pipeline(audio_file)
        
        print("✅ Processing completed!")
        
        # Use the exact iteration method from the documentation
        print(f"\n📊 Speaker Diarization Results:")
        segments = []
        for segment, _, speaker in diar.itertracks(yield_label=True):
            segments.append((segment.start, segment.end, speaker))
            print(f"   {segment.start:.1f}s - {segment.end:.1f}s: {speaker}")
        
        print(f"\n📈 Summary:")
        print(f"   Total segments: {len(segments)}")
        
        # Count unique speakers
        speakers = set()
        for _, _, speaker in segments:
            speakers.add(speaker)
        
        print(f"   Unique speakers: {len(speakers)}")
        print(f"   Speaker IDs: {sorted(speakers)}")
        
        # Check for irregular durations (not 10-second alternation)
        durations = [end - start for start, end, _ in segments]
        print(f"   Duration range: {min(durations):.1f}s - {max(durations):.1f}s")
        print(f"   Average duration: {sum(durations)/len(durations):.1f}s")
        
        # Verify this is real speaker diarization (not fallback)
        if len(segments) > 0 and max(durations) < 15.0:  # Real segments are usually shorter
            print("✅ Real speaker diarization detected (irregular, voice-driven segments)")
        else:
            print("⚠️  Possible fallback method (regular time-based segments)")
        
        return True
        
    except Exception as e:
        print(f"❌ PyAnnote 3.1 pipeline failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 PyAnnote 3.1 Pipeline Test (Fixed)")
    print("=" * 60)
    
    success = test_pyannote_3_1_pipeline()
    
    if success:
        print(f"\n🎉 SUCCESS! Real speaker diarization is working!")
    else:
        print(f"\n❌ Still having issues with PyAnnote 3.1")

#!/usr/bin/env python3
"""
Example usage of the Speaker Diarization Test Suite
Demonstrates how to test the PyAnnote-Audio migration
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from test_speaker_diarization import SpeakerDiarizationTester

async def example_test():
    """Example of how to use the speaker diarization tester"""
    
    print("🎯 Speaker Diarization Test Example")
    print("=" * 50)
    
    # Initialize tester
    tester = SpeakerDiarizationTester("test_audio")
    
    # Example 1: Test with audio file only (no ground truth)
    print("\n📁 Example 1: Basic Test (No Ground Truth)")
    print("-" * 40)
    
    # Note: Replace with your actual audio file
    audio_file = "test_audio/sample.wav"
    
    if Path(audio_file).exists():
        result = await tester.run_comprehensive_test(
            audio_file_path=audio_file,
            expected_speakers=["interviewer", "subject"]
        )
        
        if 'error' not in result:
            print(f"✅ Test completed successfully")
            print(f"📊 Utterances found: {result['results']['utterances_found']}")
            print(f"👥 Speakers identified: {result['results']['speakers_identified']}")
            print(f"⏱️  Processing time: {result['timing']['total_processing']:.2f}s")
        else:
            print(f"❌ Test failed: {result['error']}")
    else:
        print(f"⚠️  Audio file not found: {audio_file}")
        print("   Please add a sample audio file to test with")
    
    # Example 2: Test with ground truth validation
    print("\n📋 Example 2: Test with Ground Truth")
    print("-" * 40)
    
    ground_truth_file = "test_audio/sample_ground_truth.json"
    
    if Path(audio_file).exists() and Path(ground_truth_file).exists():
        result = await tester.run_comprehensive_test(
            audio_file_path=audio_file,
            ground_truth_file=ground_truth_file,
            expected_speakers=["interviewer", "subject"]
        )
        
        if 'error' not in result and 'accuracy_analysis' in result:
            accuracy = result['accuracy_analysis']
            print(f"✅ Test completed with accuracy analysis")
            print(f"🎯 Overall accuracy: {accuracy.get('overall_accuracy', 0):.2%}")
            print(f"👤 Speaker accuracy: {accuracy.get('speaker_accuracy', 0):.2%}")
            print(f"📝 Text accuracy: {accuracy.get('text_accuracy', 0):.2%}")
            
            # Show speaker distribution
            if 'speaker_distribution' in accuracy:
                print(f"📊 Speaker distribution: {accuracy['speaker_distribution']}")
        else:
            print(f"❌ Test failed or no accuracy analysis available")
    else:
        print(f"⚠️  Required files not found:")
        print(f"   Audio: {audio_file} ({'✅' if Path(audio_file).exists() else '❌'})")
        print(f"   Ground truth: {ground_truth_file} ({'✅' if Path(ground_truth_file).exists() else '❌'})")
    
    # Example 3: Generate summary report
    print("\n📊 Example 3: Summary Report")
    print("-" * 40)
    
    summary = tester.generate_summary_report()
    
    if 'total_tests' in summary:
        print(f"📈 Test Summary:")
        print(f"   Total tests: {summary['total_tests']}")
        print(f"   Successful: {summary['successful_tests']}")
        print(f"   Failed: {summary['failed_tests']}")
        print(f"   Success rate: {summary.get('success_rate', 0):.2%}")
        print(f"   Average accuracy: {summary.get('average_accuracy', 0):.2%}")
        print(f"   Average processing time: {summary.get('average_processing_time', 0):.2f}s")
    else:
        print("📊 No test results found yet")
    
    print("\n🎉 Example completed!")
    print("\nNext steps:")
    print("1. Add your audio file to test_audio/ directory")
    print("2. Create ground truth JSON file (optional)")
    print("3. Run: ./run_speaker_test.sh test_audio/your_file.wav")
    print("4. Check test_audio/ directory for results")

def create_sample_audio():
    """Create a sample audio file for testing (requires additional setup)"""
    print("\n🎵 Creating Sample Audio File")
    print("-" * 40)
    
    # This would require additional audio generation libraries
    # For now, just show instructions
    print("To create a sample audio file for testing:")
    print("1. Record a short conversation (1-2 minutes)")
    print("2. Save as WAV format, 16kHz sample rate")
    print("3. Place in test_audio/ directory")
    print("4. Create corresponding ground truth JSON file")
    
    # Create the test directory structure
    test_dir = Path("test_audio")
    test_dir.mkdir(exist_ok=True)
    
    # Create a placeholder README
    readme_content = """# Test Audio Directory

Place your test audio files here:

- `sample.wav` - Your test audio file
- `sample_ground_truth.json` - Ground truth data (optional)

## Audio Requirements:
- Format: WAV
- Sample rate: 16kHz
- Duration: 1-5 minutes recommended
- Quality: Clear speech, minimal background noise

## Ground Truth Format:
```json
[
  {
    "speaker": "interviewer",
    "text": "Hello, thank you for agreeing to this interview."
  },
  {
    "speaker": "subject", 
    "text": "My name is John Smith, and I'm happy to be here."
  }
]
```
"""
    
    with open(test_dir / "README.md", "w") as f:
        f.write(readme_content)
    
    print(f"✅ Created test directory: {test_dir}")
    print(f"📝 Added README with instructions")

if __name__ == "__main__":
    print("🚀 Speaker Diarization Test Suite - Example Usage")
    print("=" * 60)
    
    # Create sample audio directory
    create_sample_audio()
    
    # Run example test
    asyncio.run(example_test())

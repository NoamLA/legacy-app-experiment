# 🎯 Speaker Diarization Testing Suite

## Overview

This comprehensive test suite validates the PyAnnote-Audio migration with real audio files, ground truth validation, and performance benchmarking.

## ✨ Key Features

### 🎯 **Comprehensive Testing**
- **Real Audio Processing**: Tests with actual audio files
- **Ground Truth Validation**: Compares results against known speaker segments
- **Performance Timing**: Measures processing speed and efficiency
- **Accuracy Analysis**: Calculates speaker identification and timing accuracy
- **Speaker Mapping**: Maps detected speakers to expected roles (interviewer/subject)

### 📊 **Detailed Analysis**
- **Speaker Distribution**: Analyzes how speakers are distributed
- **Timing Accuracy**: Compares detected segments with ground truth
- **Processing Performance**: Measures setup, processing, and cleanup times
- **Separation Quality**: Evaluates speaker separation effectiveness

### 🔧 **Easy Integration**
- **Automated Testing**: Simple command-line interface
- **Batch Processing**: Test multiple files with different configurations
- **Result Storage**: Saves detailed test results and reports
- **Summary Reports**: Generates comprehensive test summaries

## 🚀 Quick Start

### **1. Basic Test (No Ground Truth)**
```bash
./run_speaker_test.sh test_audio/sample.wav
```

### **2. Complete Evaluation with Metrics**
```bash
python test_audio_transcription_evaluation.py
```

### **3. Comprehensive Speaker Diarization**
```bash
python test_speaker_diarization_comprehensive.py
```

### **4. Direct PyAnnote Testing**
```bash
python test_pyannote_diarization_direct.py
```

## 📋 Ground Truth Format

Create a JSON file with speaker segments (speaker and text only):

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

## 📊 Test Results

### **Generated Files**
- `test_results_<test_id>.json` - Detailed test results
- `test_summary.json` - Summary of all tests
- `complete_audio.wav` - Processed audio file
- `transcription.json` - Full transcription with speaker separation

### **Key Metrics**
- **Utterances Found**: Number of speech segments detected
- **Speakers Identified**: Number of unique speakers
- **Processing Time**: Total time for diarization
- **Speaker Accuracy**: How well speakers were identified
- **Text Accuracy**: How well transcribed text matches ground truth
- **Overall Accuracy**: Combined accuracy score

### **Sample Output**
```
🚀 Audio Transcription Evaluation
==================================================
✅ PyAnnote-Audio pipeline loaded
✅ OpenAI client initialized
📊 Ground truth: 23 segments
👥 Detected 2 speakers
📝 Transcribed 38 segments
🎯 Diarization Error Rate (DER): 223.177
🎯 Jaccard Error Rate (JER): 0.983
📝 Word Error Rate (WER): 0.075
✅ Generated 38 utterances with speaker assignments
```

## 🔧 Advanced Usage

### **Batch Testing**
```bash
# Test multiple files
for audio_file in test_audio/*.wav; do
    ./run_speaker_test.sh "$audio_file"
done
```

### **Custom Analysis**
```python
from test_speaker_diarization import SpeakerDiarizationTester

tester = SpeakerDiarizationTester("test_audio")
result = await tester.run_comprehensive_test(
    audio_file_path="sample.wav",
    ground_truth_file="sample_ground_truth.json",
    expected_speakers=["interviewer", "subject"]
)
```

### **Integration with Summarizer**
The test automatically prepares results for the summarizer model:

```json
{
  "session_id": "test-session-123",
  "project_id": "test-project-diarization",
  "speakers": ["interviewer", "subject"],
  "utterances": [
    {
      "speaker_id": "interviewer",
      "speaker_name": "Interviewer",
      "text": "Hello, thank you for agreeing to this interview.",
      "start_time": "00:00",
      "end_time": "00:03",
      "confidence": "0.95"
    }
  ],
  "ready_for_summarization": true
}
```

## 📈 Performance Benchmarks

### **Expected Performance**
- **Processing Time**: 2-5 seconds for 1-minute audio
- **Speaker Accuracy**: 85-95% with clear audio
- **Timing Accuracy**: 80-90% with good ground truth
- **Memory Usage**: ~100-200MB for typical audio files

### **Optimization Tips**
- Use 16kHz sample rate for optimal performance
- Ensure clear audio with minimal background noise
- Provide accurate ground truth for better validation
- Use GPU acceleration for faster processing

## 🐛 Troubleshooting

### **Common Issues**

#### **1. PyAnnote-Audio Not Available**
```bash
pip install pyannote.audio torch torchaudio
```

#### **2. Audio File Format Issues**
- Ensure audio is in WAV format
- Use 16kHz sample rate for best results
- Check file permissions and accessibility

#### **3. Ground Truth Format Errors**
- Verify JSON format is correct
- Check that start/end times are numeric
- Ensure speaker names match expected speakers

#### **4. Memory Issues**
- Use shorter audio files for testing
- Close other applications to free memory
- Consider using smaller PyAnnote models

### **Debug Mode**
```bash
# Enable verbose logging
export PYTHONPATH=$PWD/backend:$PYTHONPATH
python test_speaker_diarization.py test_audio/sample.wav --verbose
```

## 📚 Integration with Summarizer

The test results are automatically formatted for the summarizer model:

### **Speaker Separation**
- **Interviewer**: Questions and prompts
- **Subject**: Answers and responses
- **Clear Attribution**: Each utterance tagged with speaker

### **Ready for Processing**
```python
# Use test results with summarizer
from backend.agents.summarizer_agent import SummarizerAgent

summarizer = SummarizerAgent()
result = summarizer.create_timeline_narrative(
    conversation_data=test_results['updated_recording']
)
```

## 🎯 Test Scenarios

### **1. Basic Speaker Separation**
- Test with 2 speakers (interviewer/subject)
- No ground truth required
- Focus on speaker identification accuracy

### **2. Timing Validation**
- Test with ground truth timing
- Validate segment boundaries
- Measure timing accuracy

### **3. Multi-Speaker Scenarios**
- Test with 3+ speakers
- Validate speaker clustering
- Check for speaker confusion

### **4. Performance Testing**
- Test with long audio files
- Measure processing time
- Monitor memory usage

## 📊 Expected Results

### **High Quality Audio**
- **Speaker Accuracy**: 90-95%
- **Timing Accuracy**: 85-90%
- **Processing Time**: 2-3 seconds per minute

### **Challenging Audio**
- **Speaker Accuracy**: 70-85%
- **Timing Accuracy**: 70-80%
- **Processing Time**: 3-5 seconds per minute

### **Poor Quality Audio**
- **Speaker Accuracy**: 50-70%
- **Timing Accuracy**: 60-75%
- **Processing Time**: 4-6 seconds per minute

## 🔄 Continuous Integration

### **Automated Testing**
```bash
# Add to CI pipeline
./run_speaker_test.sh test_audio/ci_test.wav test_audio/ci_ground_truth.json
```

### **Performance Monitoring**
```bash
# Monitor processing time
time ./run_speaker_test.sh test_audio/performance_test.wav
```

## 📝 Best Practices

### **1. Audio Quality**
- Use clear, high-quality audio
- Minimize background noise
- Ensure consistent volume levels

### **2. Ground Truth**
- Provide accurate timing information
- Use consistent speaker labels
- Include all speech segments

### **3. Testing Strategy**
- Test with various audio lengths
- Use different speaker combinations
- Validate with multiple audio sources

### **4. Result Analysis**
- Review accuracy metrics
- Check for systematic errors
- Validate speaker mapping

---

**📅 Last Updated:** October 12, 2025

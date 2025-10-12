#!/usr/bin/env python3
"""
Audio Transcription Evaluation Script
Implements proper workflow: diarize → transcribe once → align by overlap → evaluate
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.development')

# PyAnnote-Audio for speaker diarization
try:
    from pyannote.audio import Pipeline
    from pyannote.core import Annotation, Segment
    from pyannote.metrics.diarization import DiarizationErrorRate, JaccardErrorRate
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    print("❌ pyannote.audio not available")

# OpenAI Whisper for transcription
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("❌ openai not available")

# WER computation
try:
    from jiwer import wer
    JIWER_AVAILABLE = True
except ImportError:
    JIWER_AVAILABLE = False
    print("❌ jiwer not available - install with: pip install jiwer")

logger = logging.getLogger(__name__)

class AudioEvaluationService:
    """Proper audio evaluation service with correct workflow"""
    
    def __init__(self):
        self.diarization_pipeline = None
        self.openai_client = None
        
        # Initialize PyAnnote pipeline
        if PYANNOTE_AVAILABLE:
            try:
                hf_token = os.getenv('HF_TOKEN')
                if not hf_token:
                    raise ValueError("HF_TOKEN not found in environment")
                
                self.diarization_pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=hf_token
                )
                print("✅ PyAnnote-Audio pipeline loaded")
            except Exception as e:
                print(f"❌ Failed to load PyAnnote pipeline: {e}")
                self.diarization_pipeline = None
        
        # Initialize OpenAI client
        if OPENAI_AVAILABLE:
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                self.openai_client = openai.OpenAI(api_key=openai_key)
                print("✅ OpenAI client initialized")
            else:
                print("❌ OPENAI_API_KEY not found")
    
    def transcribe_full_audio(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Transcribe audio once and return time-stamped segments
        Returns: [{'start': float, 'end': float, 'text': str}, ...]
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not available")
        
        print(f"🎙️ Transcribing audio: {audio_path}")
        
        with open(audio_path, 'rb') as f:
            transcript = self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json"
            )
        
        # Extract segments with timestamps
        segments = []
        if hasattr(transcript, 'segments') and transcript.segments:
            for seg in transcript.segments:
                segments.append({
                    'start': float(seg.start),
                    'end': float(seg.end),
                    'text': seg.text
                })
        else:
            # Fallback: use full text with estimated duration
            duration = getattr(transcript, 'duration', 300.0)  # Default 5 minutes
            segments.append({
                'start': 0.0,
                'end': float(duration),
                'text': transcript.text
            })
        
        print(f"📝 Transcribed {len(segments)} segments")
        return segments
    
    def run_diarization(self, audio_path: str) -> Annotation:
        """Run speaker diarization and return Annotation object"""
        if not self.diarization_pipeline:
            raise ValueError("PyAnnote pipeline not available")
        
        print(f"🎯 Running speaker diarization: {audio_path}")
        diarization = self.diarization_pipeline(audio_path)
        print(f"👥 Detected {len(diarization.labels())} speakers")
        return diarization
    
    def assign_speakers_to_segments(self, diarization: Annotation, asr_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Assign speakers to ASR segments by maximum time overlap
        """
        print(f"🔗 Assigning speakers to {len(asr_segments)} ASR segments")
        
        utterances = []
        for i, seg in enumerate(asr_segments):
            asr_segment = Segment(seg["start"], seg["end"])
            
            # Find speaker with maximum overlap
            best_speaker = None
            best_overlap = 0.0
            
            # Get all speakers and their segments
            for speaker in diarization.labels():
                timeline = diarization.label_timeline(speaker)
                overlap_duration = 0.0
                for speaker_segment in timeline:
                    intersection = speaker_segment & asr_segment
                    if intersection:
                        overlap_duration += intersection.duration
                
                if overlap_duration > best_overlap:
                    best_speaker = speaker
                    best_overlap = overlap_duration
            
            # Create utterance record
            utterance = {
                'id': str(uuid.uuid4()),
                'speaker_id': best_speaker if best_speaker else "UNKNOWN",
                'speaker_name': self._get_speaker_name(best_speaker),
                'start_time': f"{int(seg['start']//60):02d}:{int(seg['start']%60):02d}",
                'end_time': f"{int(seg['end']//60):02d}:{int(seg['end']%60):02d}",
                'duration': int((seg["end"] - seg["start"]) * 1000),
                'timestamp': datetime.now().isoformat(),
                'text': seg["text"],
                'confidence': '0.95'
            }
            
            utterances.append(utterance)
            
            if i < 5:  # Show first 5 for debugging
                print(f"   Segment {i+1}: {best_speaker} ({best_overlap:.2f}s overlap): {seg['text'][:50]}...")
        
        return utterances
    
    def _get_speaker_name(self, speaker_id: str) -> str:
        """Map speaker ID to human-readable name"""
        if not speaker_id or speaker_id == "UNKNOWN":
            return "Unknown"
        
        # Simple mapping - could be enhanced
        speaker_map = {
            "SPEAKER_00": "Speaker 1",
            "SPEAKER_01": "Speaker 2",
            "SPEAKER_02": "Speaker 3",
        }
        return speaker_map.get(speaker_id, f"Speaker {speaker_id}")
    
    def export_rttm(self, diarization: Annotation, output_path: str):
        """Export diarization results to RTTM format"""
        print(f"💾 Exporting RTTM to: {output_path}")
        with open(output_path, 'w') as f:
            diarization.write_rttm(f)
    
    def json_to_annotation(self, ground_truth: Dict[str, Any]) -> Annotation:
        """Convert ground truth JSON to PyAnnote Annotation"""
        annotation = Annotation()
        
        for segment in ground_truth.get('segments', []):
            start = segment.get('start_time', 0.0)
            end = segment.get('end_time', start + 1.0)
            speaker = segment.get('speaker', 'UNKNOWN')
            
            # Convert time strings to seconds if needed
            if isinstance(start, str):
                start = self._time_to_seconds(start)
            if isinstance(end, str):
                end = self._time_to_seconds(end)
            
            annotation[Segment(start, end)] = speaker
        
        return annotation
    
    def _time_to_seconds(self, time_str: str) -> float:
        """Convert MM:SS or HH:MM:SS to seconds"""
        parts = time_str.split(':')
        if len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            return float(time_str)
    
    def compute_diarization_metrics(self, predicted: Annotation, reference: Annotation) -> Dict[str, float]:
        """Compute DER and JER metrics"""
        if not PYANNOTE_AVAILABLE:
            return {"DER": -1.0, "JER": -1.0}
        
        der_metric = DiarizationErrorRate()
        jer_metric = JaccardErrorRate()
        
        der_score = float(der_metric(reference, predicted))
        jer_score = float(jer_metric(reference, predicted))
        
        return {
            "DER": der_score,
            "JER": jer_score
        }
    
    def compute_wer_metrics(self, reference_texts: List[str], hypothesis_texts: List[str]) -> Dict[str, float]:
        """Compute Word Error Rate"""
        if not JIWER_AVAILABLE:
            return {"WER": -1.0}
        
        ref_text = " ".join(reference_texts)
        hyp_text = " ".join(hypothesis_texts)
        
        wer_score = float(wer(ref_text, hyp_text))
        
        return {
            "WER": wer_score
        }

async def run_evaluation():
    """Run complete audio evaluation workflow"""
    print("🚀 Audio Transcription Evaluation")
    print("=" * 50)
    
    # Check environment
    if not PYANNOTE_AVAILABLE:
        print("❌ PyAnnote-Audio not available")
        return
    
    if not OPENAI_AVAILABLE:
        print("❌ OpenAI not available")
        return
    
    # Initialize service
    service = AudioEvaluationService()
    
    # File paths
    audio_file = "test_audio/Interview_trimmed_4min16sec.wav"
    ground_truth_file = "test_audio/sample_ground_truth.json"
    
    if not Path(audio_file).exists():
        print(f"❌ Audio file not found: {audio_file}")
        return
    
    if not Path(ground_truth_file).exists():
        print(f"❌ Ground truth file not found: {ground_truth_file}")
        return
    
    try:
        # Load ground truth
        print("\n📋 Loading ground truth...")
        with open(ground_truth_file, 'r') as f:
            ground_truth = json.load(f)
        
        print(f"📊 Ground truth: {len(ground_truth['segments'])} segments")
        
        # Step 1: Run diarization
        print("\n🎯 Step 1: Speaker Diarization")
        diarization = service.run_diarization(audio_file)
        
        # Export RTTM
        rttm_path = "test_audio/predicted_diarization.rttm"
        service.export_rttm(diarization, rttm_path)
        
        # Step 2: Transcribe audio once
        print("\n🎙️ Step 2: Audio Transcription")
        asr_segments = service.transcribe_full_audio(audio_file)
        
        # Step 3: Assign speakers to segments
        print("\n🔗 Step 3: Speaker Assignment")
        utterances = service.assign_speakers_to_segments(diarization, asr_segments)
        
        print(f"✅ Generated {len(utterances)} utterances with speaker assignments")
        
        # Step 4: Evaluation
        print("\n📊 Step 4: Evaluation Metrics")
        
        # Convert ground truth to Annotation
        gt_annotation = service.json_to_annotation(ground_truth)
        
        # Compute diarization metrics
        diar_metrics = service.compute_diarization_metrics(diarization, gt_annotation)
        print(f"🎯 Diarization Error Rate (DER): {diar_metrics['DER']:.3f}")
        print(f"🎯 Jaccard Error Rate (JER): {diar_metrics['JER']:.3f}")
        
        # Compute WER if jiwer is available
        wer_metrics = {}
        if JIWER_AVAILABLE:
            # Extract reference texts from ground truth
            ref_texts = [seg.get('text', '') for seg in ground_truth['segments']]
            # Extract hypothesis texts from utterances
            hyp_texts = [utt['text'] for utt in utterances]
            
            wer_metrics = service.compute_wer_metrics(ref_texts, hyp_texts)
            print(f"📝 Word Error Rate (WER): {wer_metrics['WER']:.3f}")
        
        # Save results
        metrics = diar_metrics.copy()
        metrics.update(wer_metrics)
        
        results = {
            'audio_file': audio_file,
            'ground_truth_file': ground_truth_file,
            'utterances': utterances,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
        
        results_path = "test_audio/evaluation_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_path}")
        print(f"📄 RTTM exported to: {rttm_path}")
        
        # Show sample results
        print(f"\n📋 Sample Results (first 5 utterances):")
        for i, utt in enumerate(utterances[:5]):
            print(f"   {i+1}. {utt['speaker_name']}: {utt['text'][:80]}...")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_evaluation())

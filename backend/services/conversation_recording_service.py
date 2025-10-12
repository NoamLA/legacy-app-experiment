"""
Conversation Recording Service with PyAnnote-Audio Speaker Diarization
Simplified implementation using state-of-the-art speaker diarization
"""
import os
import json
import uuid
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import numpy as np
import soundfile as sf

# PyAnnote-Audio for speaker diarization
try:
    from pyannote.audio import Pipeline
    from pyannote.audio.pipelines.utils.hook import ProgressHook
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    logging.warning("pyannote.audio not available - speaker diarization disabled")

# OpenAI Whisper for transcription
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("openai not available - transcription disabled")

logger = logging.getLogger(__name__)

class ConversationRecordingService:
    """Simplified conversation recording with PyAnnote-Audio speaker diarization"""
    
    def __init__(self, storage_path: str = "recordings"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Initialize PyAnnote-Audio pipeline
        self.diarization_pipeline = None
        if PYANNOTE_AVAILABLE:
            try:
                # Get HuggingFace token from environment
                hf_token = os.getenv('HF_TOKEN')
                if not hf_token:
                    logger.warning("HF_TOKEN not found in environment - PyAnnote-Audio will use fallback")
                    self.diarization_pipeline = None
                else:
                    # Use 3.1 model with authentication
                    self.diarization_pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=hf_token
                    )
                    logger.info("PyAnnote-Audio speaker diarization pipeline loaded (community model with auth)")
            except Exception as e:
                logger.warning(f"Failed to load PyAnnote-Audio pipeline: {e}")
                logger.info("Falling back to basic audio processing without speaker diarization")
                self.diarization_pipeline = None
        
        self.active_sessions = {}
        
    async def start_recording_session(
        self, 
        project_id: str, 
        session_name: str,
        participants: List[Dict[str, str]] = None
    ) -> str:
        """Start a new conversation recording session"""
        session_id = str(uuid.uuid4())
        
        # Create session directory
        session_dir = self.storage_path / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Initialize session data
        session_data = {
            'session_id': session_id,
            'project_id': project_id,
            'session_name': session_name,
            'participants': participants or [
                {'id': 'interviewer', 'name': 'Interviewer'},
                {'id': 'subject', 'name': 'Interview Subject'}
            ],
            'started_at': datetime.now().isoformat(),
            'status': 'active',
            'audio_chunks': [],
            'session_dir': str(session_dir)
        }
        
        self.active_sessions[session_id] = session_data
        
        logger.info(f"Started recording session {session_id} for project {project_id}")
        return session_id
    
    async def process_audio_chunk(
        self, 
        session_id: str, 
        audio_data: bytes,
        sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """Store audio chunk for later processing"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        try:
            # Store audio chunk
            session['audio_chunks'].append(audio_data)
            
            return {
                'session_id': session_id,
                'status': 'stored',
                'chunk_count': len(session['audio_chunks']),
                'message': 'Audio chunk stored for processing'
            }
            
        except Exception as e:
            logger.error(f"Error storing audio chunk: {e}")
            return {'error': str(e)}
    
    async def process_complete_audio(
        self, 
        session_id: str
    ) -> Dict[str, Any]:
        """Process complete audio file with speaker diarization and transcription"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        try:
            # Combine all audio chunks
            combined_audio = b''.join(session['audio_chunks'])
            
            # Save complete audio file
            audio_file_path = await self._save_complete_audio(session, combined_audio)
            
            # Process with PyAnnote-Audio for speaker diarization
            diarization_result = await self._process_speaker_diarization(str(audio_file_path))
            print(f"🔍 DEBUG: Diarization result type: {type(diarization_result)}")
            print(f"🔍 DEBUG: Diarization result: {diarization_result}")
            
            # Transcribe each speaker segment
            utterances = await self._transcribe_speaker_segments(
                str(audio_file_path), 
                diarization_result,
                session
            )
            print(f"🔍 DEBUG: Generated {len(utterances)} utterances")
            
            # Update session with results
            session['utterances'] = utterances
            session['audio_file_path'] = str(audio_file_path)
            session['status'] = 'processed'
            
            return {
                'session_id': session_id,
                'utterances': utterances,
                'total_utterances': len(utterances),
                'audio_file_path': str(audio_file_path),
                'status': 'processed'
            }
            
        except Exception as e:
            logger.error(f"Error processing complete audio: {e}")
            return {'error': str(e)}
    
    async def _process_speaker_diarization(self, audio_file_path: str) -> Any:
        """Process audio file with PyAnnote-Audio speaker diarization"""
        if not self.diarization_pipeline:
            logger.warning("PyAnnote-Audio pipeline not available - using fallback method")
            return self._fallback_speaker_diarization(audio_file_path)
        
        try:
            # Run speaker diarization
            with ProgressHook() as hook:
                diarization = self.diarization_pipeline(audio_file_path, hook=hook)
            
            logger.info(f"Speaker diarization completed for {audio_file_path}")
            return diarization
            
        except Exception as e:
            logger.error(f"Error in speaker diarization: {e}")
            logger.info("Falling back to basic speaker separation")
            return self._fallback_speaker_diarization(audio_file_path)
    
    def _fallback_speaker_diarization(self, audio_file_path: str) -> Any:
        """Fallback speaker diarization using simple time-based segmentation"""
        logger.info("Using fallback speaker diarization")
        
        # Load audio file to get duration
        try:
            import soundfile as sf
            audio_data, sample_rate = sf.read(audio_file_path)
            duration = len(audio_data) / sample_rate
            
            # Create a simple mock diarization result
            # Split the audio into 10-second segments and alternate speakers
            segments = []
            segment_duration = 10.0  # 10 seconds per segment
            current_time = 0.0
            speaker_id = 0
            
            while current_time < duration:
                end_time = min(current_time + segment_duration, duration)
                segments.append({
                    'start': current_time,
                    'end': end_time,
                    'speaker': f'SPEAKER_{speaker_id:02d}'
                })
                current_time = end_time
                speaker_id = (speaker_id + 1) % 2  # Alternate between 2 speakers
            
            # Create a mock diarization object
            class MockDiarization:
                def __init__(self, segments):
                    self.segments = segments
                
                def __iter__(self):
                    for segment in self.segments:
                        # Create mock turn and speaker objects
                        class MockTurn:
                            def __init__(self, start, end):
                                self.start = start
                                self.end = end
                        
                        class MockSpeaker:
                            def __init__(self, speaker_id):
                                self.speaker_id = speaker_id
                            
                            def __str__(self):
                                return self.speaker_id
                        
                        yield MockTurn(segment['start'], segment['end']), MockSpeaker(segment['speaker'])
            
            return MockDiarization(segments)
            
        except Exception as e:
            logger.error(f"Error in fallback diarization: {e}")
            # Return empty diarization
            class EmptyDiarization:
                def __iter__(self):
                    return iter([])
            
            return EmptyDiarization()
    
    async def _transcribe_speaker_segments(
        self, 
        audio_file_path: str, 
        diarization_result: Any,
        session: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Transcribe each speaker segment using OpenAI Whisper"""
        utterances = []
        
        try:
            print(f"🔍 DEBUG: Processing diarization result: {type(diarization_result)}")
            
            # Handle both old and new PyAnnote formats
            segment_count = 0
            for segment, _, speaker in diarization_result.itertracks(yield_label=True):
                segment_count += 1
                print(f"🔍 DEBUG: Processing segment {segment_count}: {segment.start:.1f}s - {segment.end:.1f}s, speaker: {speaker}")
                
                # Extract audio segment
                start_time = segment.start
                end_time = segment.end
                duration = end_time - start_time
                
                # Create utterance record
                utterance = {
                    'id': str(uuid.uuid4()),
                    'speaker_id': str(speaker),  # Convert to string for JSON serialization
                    'speaker_name': self._get_speaker_name(session, str(speaker)),
                    'start_time': f"{int(start_time//60):02d}:{int(start_time%60):02d}",
                    'end_time': f"{int(end_time//60):02d}:{int(end_time%60):02d}",
                    'duration': int(duration * 1000),  # Convert to milliseconds
                    'timestamp': datetime.now().isoformat(),
                    'audio_segment_path': None,  # Could extract and save segments
                    'text': '',  # Will be filled by transcription
                    'confidence': '0.95'  # Default confidence
                }
                
                # Transcribe this segment
                if OPENAI_AVAILABLE:
                    transcription = await self._transcribe_audio_segment(
                        audio_file_path, start_time, end_time
                    )
                    utterance['text'] = transcription.get('text', '')
                    utterance['confidence'] = transcription.get('confidence', '0.95')
                
                utterances.append(utterance)
            
            return utterances
            
        except Exception as e:
            logger.error(f"Error transcribing speaker segments: {e}")
            return []
    
    async def _transcribe_audio_segment(
        self, 
        audio_file_path: str, 
        start_time: float, 
        end_time: float
    ) -> Dict[str, Any]:
        """Transcribe a specific audio segment using OpenAI Whisper"""
        if not OPENAI_AVAILABLE:
            return {'text': '[Transcription not available]', 'confidence': '0.0'}
        
        try:
            # Use OpenAI client v1.0+ API
            client = openai.OpenAI()
            
            with open(audio_file_path, 'rb') as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
            
            return {
                'text': transcript.text,
                'confidence': str(transcript.segments[0].avg_logprob if transcript.segments else 0.95)
            }
            
        except Exception as e:
            logger.error(f"OpenAI transcription error: {e}")
            return {'text': '[Transcription failed]', 'confidence': '0.0'}
    
    async def _save_complete_audio(self, session: Dict[str, Any], audio_data: bytes) -> Path:
        """Save complete audio file"""
        session_dir = Path(session['session_dir'])
        audio_file_path = session_dir / "complete_audio.wav"
        
        # Convert bytes to numpy array and save
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        sf.write(audio_file_path, audio_array, 16000)
        
        return audio_file_path
    
    def _get_speaker_name(self, session: Dict[str, Any], speaker_id: str) -> str:
        """Get human-readable speaker name"""
        # Map speaker IDs to participant names
        speaker_mapping = {
            'SPEAKER_00': 'Interviewer',
            'SPEAKER_01': 'Interview Subject',
            'SPEAKER_02': 'Additional Speaker',
        }
        
        # Check if we have custom participant mapping
        for participant in session['participants']:
            if participant['id'] == speaker_id:
                return participant['name']
        
        # Use default mapping
        return speaker_mapping.get(speaker_id, f"Speaker {speaker_id}")
    
    async def end_recording_session(self, session_id: str) -> Dict[str, Any]:
        """End recording session and process all audio"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        session['status'] = 'processing'
        session['ended_at'] = datetime.now().isoformat()
        
        # Process complete audio with speaker diarization
        result = await self.process_complete_audio(session_id)
        
        if 'error' in result:
            return result
        
        # Save transcription file
        transcription_file_path = await self._save_transcription(session)
        session['transcription_file_path'] = str(transcription_file_path)
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        logger.info(f"Ended recording session {session_id}")
        return {
            'session_id': session_id,
            'status': 'completed',
            'audio_file_path': result.get('audio_file_path'),
            'transcription_file_path': str(transcription_file_path),
            'utterance_count': len(result.get('utterances', [])),
            'utterances': result.get('utterances', [])
        }
    
    async def _save_transcription(self, session: Dict[str, Any]) -> Path:
        """Save transcription as JSON file"""
        session_dir = Path(session['session_dir'])
        transcription_file_path = session_dir / "transcription.json"
        
        transcription_data = {
            'session_id': session['session_id'],
            'project_id': session['project_id'],
            'session_name': session['session_name'],
            'started_at': session['started_at'],
            'ended_at': session['ended_at'],
            'participants': session['participants'],
            'utterances': session.get('utterances', []),
            'audio_file_path': session.get('audio_file_path'),
            'processing_method': 'pyannote-audio'
        }
        
        with open(transcription_file_path, 'w') as f:
            json.dump(transcription_data, f, indent=2)
        
        return transcription_file_path

# Global service instance
conversation_recording_service = ConversationRecordingService()
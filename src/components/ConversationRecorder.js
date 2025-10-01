import React, { useState, useRef, useEffect } from 'react';
import { 
  MicrophoneIcon, 
  StopIcon, 
  PlayIcon, 
  PauseIcon,
  SpeakerWaveIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';

const ConversationRecorder = ({ projectId, onRecordingComplete }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [sessionId, setSessionId] = useState(null);
  const [utterances, setUtterances] = useState([]);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [participants, setParticipants] = useState([
    { id: 'interviewer', name: 'Interviewer' },
    { id: 'subject', name: 'Interview Subject' }
  ]);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);

  // Initialize audio context and analyser for real-time audio processing
  useEffect(() => {
    if (isRecording && !audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 2048;
      dataArrayRef.current = new Uint8Array(analyserRef.current.frequencyBinCount);
    }
  }, [isRecording]);

  // Start recording session
  const startRecording = async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        } 
      });
      
      streamRef.current = stream;
      
      // Connect audio stream to analyser for real-time processing
      if (audioContextRef.current) {
        const source = audioContextRef.current.createMediaStreamSource(stream);
        source.connect(analyserRef.current);
      }

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Handle data available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          processAudioChunk(event.data);
        }
      };

      // Start recording
      mediaRecorder.start(1000); // Collect data every 1 second
      setIsRecording(true);
      
      // Start timer
      intervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

      // Start conversation session
      await startConversationSession();

    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Failed to start recording. Please check microphone permissions.');
    }
  };

  // Start conversation session on backend
  const startConversationSession = async () => {
    try {
      const response = await fetch('/conversation/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: projectId,
          session_name: `Interview Session ${new Date().toLocaleString()}`,
          participants: participants
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
      } else {
        throw new Error('Failed to start conversation session');
      }
    } catch (error) {
      console.error('Error starting conversation session:', error);
    }
  };

  // Process audio chunk for speaker separation
  const processAudioChunk = async (audioBlob) => {
    if (!sessionId) return;

    try {
      // Convert blob to base64
      const arrayBuffer = await audioBlob.arrayBuffer();
      const base64Audio = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));

      // Send to backend for processing
      const response = await fetch('/conversation/audio-chunk', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          audio_data: base64Audio,
          sample_rate: 16000
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Update utterances with new speaker-separated data
        if (data.utterances && data.utterances.length > 0) {
          setUtterances(prev => [...prev, ...data.utterances]);
          
          // Auto-transcribe new utterances
          for (const utterance of data.utterances) {
            await transcribeUtterance(utterance.id);
          }
        }
      }
    } catch (error) {
      console.error('Error processing audio chunk:', error);
    }
  };

  // Transcribe utterance
  const transcribeUtterance = async (utteranceId) => {
    if (!sessionId) return;

    try {
      const response = await fetch('/conversation/transcribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          utterance_id: utteranceId,
          transcription_service: 'openai'
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Update utterance with transcription
        setUtterances(prev => 
          prev.map(utterance => 
            utterance.id === utteranceId 
              ? { ...utterance, text: data.text, confidence: data.confidence }
              : utterance
          )
        );
      }
    } catch (error) {
      console.error('Error transcribing utterance:', error);
    }
  };

  // Stop recording
  const stopRecording = async () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      
      // Stop all tracks
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      
      // Stop timer
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      
      setIsRecording(false);
      setIsPaused(false);
      
      // End conversation session
      if (sessionId) {
        await endConversationSession();
      }
    }
  };

  // End conversation session
  const endConversationSession = async () => {
    try {
      const response = await fetch(`/conversation/end/${sessionId}`, {
        method: 'POST',
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Conversation session ended:', data);
        
        if (onRecordingComplete) {
          onRecordingComplete({
            sessionId,
            utterances,
            audioFile: data.audio_file_path,
            transcriptionFile: data.transcription_file_path
          });
        }
      }
    } catch (error) {
      console.error('Error ending conversation session:', error);
    }
  };

  // Toggle pause/resume
  const togglePause = () => {
    if (isPaused) {
      // Resume recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'paused') {
        mediaRecorderRef.current.resume();
      }
      setIsPaused(false);
    } else {
      // Pause recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.pause();
      }
      setIsPaused(true);
    }
  };

  // Format time display
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Get real-time audio level for visualization
  const getAudioLevel = () => {
    if (!analyserRef.current || !dataArrayRef.current) return 0;
    
    analyserRef.current.getByteFrequencyData(dataArrayRef.current);
    const average = dataArrayRef.current.reduce((a, b) => a + b) / dataArrayRef.current.length;
    return average / 255; // Normalize to 0-1
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-gray-900">
          Conversation Recording
        </h3>
        <div className="flex items-center space-x-2">
          <div className="text-sm text-gray-500">
            {formatTime(recordingTime)}
          </div>
          {isRecording && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-red-600">Recording</span>
            </div>
          )}
        </div>
      </div>

      {/* Recording Controls */}
      <div className="flex items-center justify-center space-x-4 mb-6">
        {!isRecording ? (
          <button
            onClick={startRecording}
            className="flex items-center space-x-2 bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg transition-colors"
          >
            <MicrophoneIcon className="w-5 h-5" />
            <span>Start Recording</span>
          </button>
        ) : (
          <>
            <button
              onClick={togglePause}
              className="flex items-center space-x-2 bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              {isPaused ? (
                <>
                  <PlayIcon className="w-4 h-4" />
                  <span>Resume</span>
                </>
              ) : (
                <>
                  <PauseIcon className="w-4 h-4" />
                  <span>Pause</span>
                </>
              )}
            </button>
            
            <button
              onClick={stopRecording}
              className="flex items-center space-x-2 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <StopIcon className="w-4 h-4" />
              <span>Stop</span>
            </button>
          </>
        )}
      </div>

      {/* Audio Level Visualization */}
      {isRecording && (
        <div className="mb-6">
          <div className="text-sm text-gray-600 mb-2">Audio Level</div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-green-500 h-2 rounded-full transition-all duration-100"
              style={{ width: `${getAudioLevel() * 100}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Live Transcript */}
      <div className="mb-6">
        <div className="flex items-center space-x-2 mb-3">
          <DocumentTextIcon className="w-5 h-5 text-gray-600" />
          <h4 className="text-lg font-medium text-gray-900">Live Transcript</h4>
        </div>
        
        <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
          {utterances.length === 0 ? (
            <p className="text-gray-500 italic">No speech detected yet...</p>
          ) : (
            <div className="space-y-3">
              {utterances.map((utterance, index) => (
                <div key={utterance.id || index} className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                      utterance.speaker_id === 'interviewer' 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {utterance.speaker_name?.charAt(0) || '?'}
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-medium text-gray-900">
                        {utterance.speaker_name || 'Unknown Speaker'}
                      </span>
                      <span className="text-xs text-gray-500">
                        {utterance.start_time} - {utterance.end_time}
                      </span>
                      {utterance.confidence && (
                        <span className="text-xs text-gray-400">
                          ({Math.round(parseFloat(utterance.confidence) * 100)}%)
                        </span>
                      )}
                    </div>
                    <p className="text-gray-700">
                      {utterance.text || '[Transcribing...]'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Participants */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Participants</h4>
        <div className="flex space-x-4">
          {participants.map((participant) => (
            <div key={participant.id} className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                participant.id === 'interviewer' ? 'bg-blue-500' : 'bg-green-500'
              }`}></div>
              <span className="text-sm text-gray-600">{participant.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Session Info */}
      {sessionId && (
        <div className="text-xs text-gray-500">
          Session ID: {sessionId}
        </div>
      )}
    </div>
  );
};

export default ConversationRecorder;

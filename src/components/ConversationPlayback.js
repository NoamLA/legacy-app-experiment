import React, { useState, useEffect } from 'react';
import { 
  PlayIcon, 
  PauseIcon, 
  StopIcon,
  SpeakerWaveIcon,
  DocumentTextIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const ConversationPlayback = ({ sessionId, projectId }) => {
  const [transcript, setTranscript] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [selectedSpeaker, setSelectedSpeaker] = useState(null);
  const [filteredUtterances, setFilteredUtterances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const audioRef = useRef(null);
  const intervalRef = useRef(null);

  // Load conversation transcript
  useEffect(() => {
    loadTranscript();
  }, [sessionId]);

  // Update filtered utterances when speaker filter changes
  useEffect(() => {
    if (transcript) {
      const filtered = selectedSpeaker 
        ? transcript.transcript.filter(utterance => utterance.speaker === selectedSpeaker)
        : transcript.transcript;
      setFilteredUtterances(filtered);
    }
  }, [transcript, selectedSpeaker]);

  const loadTranscript = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/conversation/session/${sessionId}/transcript`);
      
      if (response.ok) {
        const data = await response.json();
        setTranscript(data);
        setDuration(parseTimeToSeconds(data.duration));
      } else {
        throw new Error('Failed to load transcript');
      }
    } catch (error) {
      console.error('Error loading transcript:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  // Parse time string (HH:MM:SS) to seconds
  const parseTimeToSeconds = (timeStr) => {
    const parts = timeStr.split(':');
    return parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2]);
  };

  // Format seconds to time string
  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Play/pause audio
  const togglePlayback = () => {
    if (isPlaying) {
      pauseAudio();
    } else {
      playAudio();
    }
  };

  const playAudio = () => {
    if (audioRef.current) {
      audioRef.current.play();
      setIsPlaying(true);
      
      // Update current time
      intervalRef.current = setInterval(() => {
        if (audioRef.current) {
          setCurrentTime(audioRef.current.currentTime);
        }
      }, 100);
    }
  };

  const pauseAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
      
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }
  };

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
      setCurrentTime(0);
      
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }
  };

  // Seek to specific time
  const seekToTime = (time) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  // Get current utterance based on time
  const getCurrentUtterance = () => {
    if (!transcript) return null;
    
    return transcript.transcript.find(utterance => {
      const startTime = parseTimeToSeconds(utterance.timestamp);
      const endTime = startTime + (utterance.duration || 5); // Default 5 seconds if no duration
      return currentTime >= startTime && currentTime <= endTime;
    });
  };

  // Get unique speakers
  const getSpeakers = () => {
    if (!transcript) return [];
    return [...new Set(transcript.transcript.map(utterance => utterance.speaker))];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-600">Loading conversation...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="text-red-800">Error: {error}</div>
      </div>
    );
  }

  if (!transcript) {
    return (
      <div className="text-gray-600">No conversation data available</div>
    );
  }

  const currentUtterance = getCurrentUtterance();
  const speakers = getSpeakers();

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-gray-900">
          Conversation Playback
        </h3>
        <div className="text-sm text-gray-500">
          {transcript.participants?.join(', ')}
        </div>
      </div>

      {/* Audio Controls */}
      <div className="mb-6">
        <div className="flex items-center space-x-4 mb-4">
          <button
            onClick={togglePlayback}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            {isPlaying ? (
              <>
                <PauseIcon className="w-4 h-4" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <PlayIcon className="w-4 h-4" />
                <span>Play</span>
              </>
            )}
          </button>
          
          <button
            onClick={stopAudio}
            className="flex items-center space-x-2 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <StopIcon className="w-4 h-4" />
            <span>Stop</span>
          </button>
        </div>

        {/* Progress Bar */}
        <div className="mb-2">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <ClockIcon className="w-4 h-4" />
            <span>{formatTime(currentTime)} / {formatTime(duration)}</span>
          </div>
          <div 
            className="w-full bg-gray-200 rounded-full h-2 cursor-pointer"
            onClick={(e) => {
              const rect = e.currentTarget.getBoundingClientRect();
              const clickX = e.clientX - rect.left;
              const percentage = clickX / rect.width;
              seekToTime(percentage * duration);
            }}
          >
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-100"
              style={{ width: `${(currentTime / duration) * 100}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Speaker Filter */}
      <div className="mb-6">
        <div className="flex items-center space-x-2 mb-3">
          <SpeakerWaveIcon className="w-5 h-5 text-gray-600" />
          <span className="text-sm font-medium text-gray-900">Filter by Speaker</span>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setSelectedSpeaker(null)}
            className={`px-3 py-1 rounded-full text-sm ${
              selectedSpeaker === null 
                ? 'bg-blue-100 text-blue-800' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            All Speakers
          </button>
          {speakers.map((speaker) => (
            <button
              key={speaker}
              onClick={() => setSelectedSpeaker(speaker)}
              className={`px-3 py-1 rounded-full text-sm ${
                selectedSpeaker === speaker 
                  ? 'bg-blue-100 text-blue-800' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {speaker}
            </button>
          ))}
        </div>
      </div>

      {/* Current Utterance Highlight */}
      {currentUtterance && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
            <span className="font-medium text-blue-900">Currently Playing</span>
          </div>
          <div className="text-blue-800">
            <strong>{currentUtterance.speaker}:</strong> {currentUtterance.text}
          </div>
        </div>
      )}

      {/* Transcript */}
      <div className="mb-4">
        <div className="flex items-center space-x-2 mb-3">
          <DocumentTextIcon className="w-5 h-5 text-gray-600" />
          <h4 className="text-lg font-medium text-gray-900">Transcript</h4>
          <span className="text-sm text-gray-500">
            ({filteredUtterances.length} utterances)
          </span>
        </div>
        
        <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
          <div className="space-y-3">
            {filteredUtterances.map((utterance, index) => {
              const isCurrent = currentUtterance && currentUtterance.speaker === utterance.speaker && 
                               currentUtterance.text === utterance.text;
              
              return (
                <div 
                  key={index} 
                  className={`flex items-start space-x-3 p-3 rounded-lg cursor-pointer transition-colors ${
                    isCurrent 
                      ? 'bg-blue-100 border border-blue-200' 
                      : 'hover:bg-gray-100'
                  }`}
                  onClick={() => {
                    const startTime = parseTimeToSeconds(utterance.timestamp);
                    seekToTime(startTime);
                  }}
                >
                  <div className="flex-shrink-0">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                      utterance.speaker === 'Interviewer' 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {utterance.speaker?.charAt(0) || '?'}
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-medium text-gray-900">
                        {utterance.speaker}
                      </span>
                      <span className="text-xs text-gray-500">
                        {utterance.timestamp}
                      </span>
                      {utterance.confidence && (
                        <span className="text-xs text-gray-400">
                          ({Math.round(parseFloat(utterance.confidence) * 100)}%)
                        </span>
                      )}
                    </div>
                    <p className="text-gray-700">
                      {utterance.text}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Hidden audio element for playback */}
      <audio
        ref={audioRef}
        onEnded={() => {
          setIsPlaying(false);
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
          }
        }}
        onLoadedMetadata={() => {
          setDuration(audioRef.current.duration);
        }}
      />
    </div>
  );
};

export default ConversationPlayback;

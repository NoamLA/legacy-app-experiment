import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ConversationRecorder from '../components/ConversationRecorder';
import ConversationPlayback from '../components/ConversationPlayback';
import { 
  MicrophoneIcon, 
  PlayIcon, 
  DocumentTextIcon,
  ClockIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline';

const ConversationManager = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState('record');
  const [conversationSessions, setConversationSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load conversation sessions on component mount
  useEffect(() => {
    loadConversationSessions();
  }, [projectId]);

  const loadConversationSessions = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/conversation/sessions/${projectId}`);
      
      if (response.ok) {
        const data = await response.json();
        setConversationSessions(data.sessions || []);
      } else {
        throw new Error('Failed to load conversation sessions');
      }
    } catch (error) {
      console.error('Error loading conversation sessions:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRecordingComplete = (recordingData) => {
    console.log('Recording completed:', recordingData);
    // Reload sessions to include the new recording
    loadConversationSessions();
    // Switch to playback tab
    setActiveTab('playback');
    setSelectedSession(recordingData.sessionId);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (startTime, endTime) => {
    if (!startTime || !endTime) return 'Unknown';
    
    const start = new Date(startTime);
    const end = new Date(endTime);
    const durationMs = end - start;
    const minutes = Math.floor(durationMs / 60000);
    const seconds = Math.floor((durationMs % 60000) / 1000);
    
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-lg text-gray-600">Loading conversation sessions...</div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Conversation Manager</h1>
            <p className="text-gray-600 mt-2">
              Record and manage conversations with automatic speaker separation
            </p>
          </div>
          <button
            onClick={() => navigate(`/project/${projectId}`)}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Back to Project
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="text-red-800">Error: {error}</div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('record')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'record'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <MicrophoneIcon className="w-5 h-5 inline mr-2" />
              Record Conversation
            </button>
            
            <button
              onClick={() => setActiveTab('playback')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'playback'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <PlayIcon className="w-5 h-5 inline mr-2" />
              Playback & Transcripts
            </button>
            
            <button
              onClick={() => setActiveTab('sessions')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'sessions'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <DocumentTextIcon className="w-5 h-5 inline mr-2" />
              All Sessions
            </button>
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'record' && (
        <div className="space-y-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-lg font-medium text-blue-900 mb-2">
              🎙️ Start Recording
            </h3>
            <p className="text-blue-800">
              Click "Start Recording" to begin capturing audio with automatic speaker separation. 
              The system will identify different speakers and transcribe the conversation in real-time.
            </p>
          </div>
          
          <ConversationRecorder 
            projectId={projectId}
            onRecordingComplete={handleRecordingComplete}
          />
        </div>
      )}

      {activeTab === 'playback' && (
        <div className="space-y-6">
          {selectedSession ? (
            <ConversationPlayback 
              sessionId={selectedSession}
              projectId={projectId}
            />
          ) : (
            <div className="text-center py-12">
              <PlayIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Select a Session to Play
              </h3>
              <p className="text-gray-600 mb-4">
                Choose a conversation session from the list below to view the transcript and playback audio.
              </p>
              <button
                onClick={() => setActiveTab('sessions')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                View All Sessions
              </button>
            </div>
          )}
        </div>
      )}

      {activeTab === 'sessions' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">
              Conversation Sessions ({conversationSessions.length})
            </h3>
            <button
              onClick={loadConversationSessions}
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              Refresh
            </button>
          </div>

          {conversationSessions.length === 0 ? (
            <div className="text-center py-12">
              <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No Conversation Sessions
              </h3>
              <p className="text-gray-600 mb-4">
                Start recording a conversation to see it appear here.
              </p>
              <button
                onClick={() => setActiveTab('record')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Start Recording
              </button>
            </div>
          ) : (
            <div className="grid gap-4">
              {conversationSessions.map((session) => (
                <div 
                  key={session.id}
                  className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => {
                    setSelectedSession(session.id);
                    setActiveTab('playback');
                  }}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <DocumentTextIcon className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="text-lg font-medium text-gray-900">
                          {session.session_name}
                        </h4>
                        <p className="text-sm text-gray-600">
                          {formatDate(session.started_at)}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(session.status)}`}>
                        {session.status}
                      </span>
                      <div className="text-right">
                        <div className="flex items-center space-x-1 text-sm text-gray-600">
                          <ClockIcon className="w-4 h-4" />
                          <span>{formatDuration(session.started_at, session.ended_at)}</span>
                        </div>
                        <div className="flex items-center space-x-1 text-sm text-gray-600">
                          <UserGroupIcon className="w-4 h-4" />
                          <span>{session.utterance_count || 0} utterances</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <div className="flex items-center space-x-1">
                      <UserGroupIcon className="w-4 h-4" />
                      <span>{session.participants?.join(', ') || 'Unknown participants'}</span>
                    </div>
                    {session.ended_at && (
                      <div className="flex items-center space-x-1">
                        <ClockIcon className="w-4 h-4" />
                        <span>Ended: {formatDate(session.ended_at)}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ConversationManager;

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeftIcon, 
  PlayIcon, 
  CheckCircleIcon, 
  ClockIcon,
  UserIcon,
  ComputerDesktopIcon,
  EyeIcon,
  XMarkIcon,
  MicrophoneIcon
} from '@heroicons/react/24/outline';

const ProjectDashboard = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [responses, setResponses] = useState([]);
  const [themes, setThemes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showPreview, setShowPreview] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  useEffect(() => {
    fetchProject();
    fetchResponses();
  }, [projectId]);

  const fetchProject = async () => {
    try {
      const response = await fetch(`/projects/${projectId}`);
      if (response.ok) {
        const projectData = await response.json();
        setProject(projectData);
        setThemes(projectData.themes || []);
      }
    } catch (error) {
      console.error('Error fetching project:', error);
    }
  };

  const fetchResponses = async () => {
    try {
      const response = await fetch(`/projects/${projectId}/responses`);
      if (response.ok) {
        const data = await response.json();
        setResponses(data.responses || []);
      }
    } catch (error) {
      console.error('Error fetching responses:', error);
    } finally {
      setLoading(false);
    }
  };

  const startSeedQuestions = () => {
    navigate(`/interview/${projectId}?phase=seed`);
  };

  const identifyThemes = async () => {
    try {
      const response = await fetch(`/projects/${projectId}/identify-themes`, {
        method: 'POST'
      });
      if (response.ok) {
        const data = await response.json();
        setThemes(data.themes);
        await fetchProject(); // Refresh project data
      }
    } catch (error) {
      console.error('Error identifying themes:', error);
    }
  };

  const startThemeInterview = (themeId) => {
    navigate(`/interview/${projectId}?phase=theme&themeId=${themeId}`);
  };

  const previewThemeQuestions = async (themeId) => {
    setLoadingPreview(true);
    try {
      const response = await fetch(`/projects/${projectId}/themes/${themeId}/preview`);
      if (response.ok) {
        const data = await response.json();
        setPreviewData(data);
        setShowPreview(true);
      } else {
        console.error('Failed to fetch theme preview');
      }
    } catch (error) {
      console.error('Error fetching theme preview:', error);
    } finally {
      setLoadingPreview(false);
    }
  };

  const closePreview = () => {
    setShowPreview(false);
    setPreviewData(null);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-64">
        <div className="text-lg text-gray-600">Loading project...</div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-16">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Project Not Found</h2>
        <Link to="/" className="btn-primary">Back to Home</Link>
      </div>
    );
  }

  const seedResponses = responses.filter(r => r.question_type === 'seed');
  const canIdentifyThemes = seedResponses.length >= 5 && themes.length === 0;
  const hasThemes = themes.length > 0;

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeftIcon className="w-5 h-5 mr-2" />
          Back to Home
        </button>
        
        <div className="interview-card">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {project.name}
              </h1>
              <div className="text-gray-600 space-y-1">
                <p><strong>Subject:</strong> {project.subject_info.name}</p>
                <p><strong>Relationship:</strong> {project.subject_info.relation}</p>
                <p><strong>Mode:</strong> {project.interview_mode}</p>
                <p><strong>Status:</strong> 
                  <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${
                    project.status === 'completed' ? 'bg-green-100 text-green-800' :
                    project.status === 'themes_identified' ? 'bg-blue-100 text-blue-800' :
                    project.status === 'seed_questions' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {project.status.replace('_', ' ')}
                  </span>
                </p>
              </div>
            </div>
            
            <div className="text-right">
              <div className="text-2xl font-bold text-blue-600">{responses.length}</div>
              <div className="text-sm text-gray-600">Total Responses</div>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Flow */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Interview Progress</h2>
        
        <div className="grid md:grid-cols-3 gap-4">
          {/* Phase 1: Seed Questions */}
          <div className={`interview-card ${
            project.status === 'seed_questions' || responses.length > 0 ? 'border-blue-500' : ''
          }`}>
            <div className="flex items-center mb-3">
              {seedResponses.length > 0 ? (
                <CheckCircleIcon className="w-6 h-6 text-green-600 mr-2" />
              ) : (
                <ClockIcon className="w-6 h-6 text-gray-400 mr-2" />
              )}
              <h3 className="font-semibold">Phase 1: Seed Questions</h3>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Build rapport with warm-up questions
            </p>
            <div className="text-sm text-gray-500 mb-4">
              {seedResponses.length} responses collected
            </div>
            {seedResponses.length === 0 ? (
              <button onClick={startSeedQuestions} className="btn-primary w-full">
                <PlayIcon className="w-4 h-4 mr-2 inline" />
                Start Interview
              </button>
            ) : (
              <button 
                onClick={startSeedQuestions} 
                className="btn-secondary w-full"
              >
                Continue Questions
              </button>
            )}
          </div>

          {/* Phase 2: Theme Identification */}
          <div className={`interview-card ${
            hasThemes ? 'border-blue-500' : canIdentifyThemes ? 'border-yellow-500' : ''
          }`}>
            <div className="flex items-center mb-3">
              {hasThemes ? (
                <CheckCircleIcon className="w-6 h-6 text-green-600 mr-2" />
              ) : canIdentifyThemes ? (
                <ClockIcon className="w-6 h-6 text-yellow-600 mr-2" />
              ) : (
                <ClockIcon className="w-6 h-6 text-gray-400 mr-2" />
              )}
              <h3 className="font-semibold">Phase 2: Identify Themes</h3>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              AI analyzes responses to find key themes
            </p>
            <div className="text-sm text-gray-500 mb-4">
              {themes.length} themes identified
            </div>
            {canIdentifyThemes ? (
              <button onClick={identifyThemes} className="btn-primary w-full">
                Identify Themes
              </button>
            ) : hasThemes ? (
              <div className="text-sm text-green-600">✓ Themes Ready</div>
            ) : (
              <div className="text-sm text-gray-500">
                Need {Math.max(0, 5 - seedResponses.length)} more responses
              </div>
            )}
          </div>

          {/* Phase 3: Deep Dive */}
          <div className={`interview-card ${
            hasThemes ? 'border-blue-500' : ''
          }`}>
            <div className="flex items-center mb-3">
              <ClockIcon className="w-6 h-6 text-gray-400 mr-2" />
              <h3 className="font-semibold">Phase 3: Deep Dive</h3>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Explore themes with detailed questions
            </p>
            <div className="text-sm text-gray-500 mb-4">
              Ready when themes are identified
            </div>
            {hasThemes ? (
              <div className="text-sm text-blue-600">Ready to explore themes</div>
            ) : (
              <div className="text-sm text-gray-500">Waiting for themes</div>
            )}
          </div>
        </div>
      </div>

      {/* Conversation Recording Section */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Conversation Recording</h2>
        
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                <MicrophoneIcon className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Record Conversations with Speaker Separation
                </h3>
                <p className="text-sm text-gray-600">
                  Capture natural conversations with automatic speaker identification and real-time transcription
                </p>
              </div>
            </div>
          </div>
          
          <div className="grid md:grid-cols-2 gap-4 mb-4">
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <h4 className="font-medium text-gray-900 mb-2">🎙️ Real-time Recording</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Automatic speaker separation</li>
                <li>• Live transcription</li>
                <li>• Voice activity detection</li>
                <li>• Audio quality optimization</li>
              </ul>
            </div>
            
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <h4 className="font-medium text-gray-900 mb-2">📝 Smart Transcription</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Speaker identification</li>
                <li>• Confidence scoring</li>
                <li>• Timestamp tracking</li>
                <li>• Export capabilities</li>
              </ul>
            </div>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={() => navigate(`/project/${projectId}/conversations`)}
              className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg transition-colors flex items-center space-x-2"
            >
              <MicrophoneIcon className="w-5 h-5" />
              <span>Manage Conversations</span>
            </button>
            
            <button
              onClick={() => navigate(`/project/${projectId}/conversations?tab=record`)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition-colors flex items-center space-x-2"
            >
              <PlayIcon className="w-5 h-5" />
              <span>Start Recording</span>
            </button>
          </div>
        </div>
      </div>

      {/* Themes Section */}
      {hasThemes && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Interview Themes</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {themes.map((theme, index) => (
              <div key={theme.id || index} className="theme-card">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-gray-900">{theme.name}</h3>
                  <div className="flex items-center text-sm text-gray-600">
                    {theme.suggested_interviewer === 'AI' ? (
                      <ComputerDesktopIcon className="w-4 h-4 mr-1" />
                    ) : (
                      <UserIcon className="w-4 h-4 mr-1" />
                    )}
                    {theme.suggested_interviewer}
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-4">{theme.description}</p>
                <div className="text-xs text-gray-500 mb-3">
                  {theme.questions?.length || 0} questions prepared
                </div>
                <div className="flex space-x-2">
                  <button 
                    onClick={() => previewThemeQuestions(theme.id)}
                    className="btn-secondary flex-1 text-sm"
                    disabled={loadingPreview}
                  >
                    <EyeIcon className="w-4 h-4 mr-2 inline" />
                    Preview Questions
                  </button>
                  <button 
                    onClick={() => startThemeInterview(theme.id)}
                    className="btn-primary flex-1 text-sm"
                  >
                    <PlayIcon className="w-4 h-4 mr-2 inline" />
                    Start Interview
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Responses */}
      {responses.length > 0 && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Responses</h2>
          <div className="space-y-4">
            {responses.slice(-3).reverse().map((response, index) => (
              <div key={response.id || index} className="interview-card">
                <div className="question-bubble">
                  <div className="font-medium text-gray-900 mb-1">Question:</div>
                  <div className="text-gray-700">{response.question}</div>
                </div>
                <div className="response-bubble">
                  <div className="font-medium text-gray-900 mb-1">Response:</div>
                  <div className="text-gray-700">{response.answer}</div>
                </div>
                <div className="text-xs text-gray-500 mt-2">
                  {new Date(response.timestamp).toLocaleDateString()} • 
                  {response.question_type} question
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Theme Preview Modal */}
      {showPreview && previewData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{previewData.name}</h2>
                <p className="text-sm text-gray-600 mt-1">{previewData.description}</p>
                <div className="flex items-center mt-2 text-sm text-gray-500">
                  <span className="font-medium">{previewData.total_questions} questions</span>
                  {previewData.custom && (
                    <span className="ml-3 px-2 py-1 bg-purple-100 text-purple-800 rounded-full text-xs">
                      Custom Theme
                    </span>
                  )}
                  <div className="ml-3 flex items-center">
                    {previewData.suggested_interviewer === 'AI' ? (
                      <ComputerDesktopIcon className="w-4 h-4 mr-1" />
                    ) : (
                      <UserIcon className="w-4 h-4 mr-1" />
                    )}
                    <span>Suggested: {previewData.suggested_interviewer}</span>
                  </div>
                </div>
              </div>
              <button
                onClick={closePreview}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>

            {/* Assignment Information */}
            {(previewData.assigned_participants?.length > 0 || previewData.self_assigned_participants?.length > 0) && (
              <div className="px-6 py-4 bg-blue-50 border-b">
                <h3 className="font-medium text-blue-900 mb-2">Assignment Status</h3>
                <div className="text-sm space-y-1">
                  {previewData.assigned_participants?.length > 0 && (
                    <div>
                      <span className="font-medium text-blue-800">Assigned to: </span>
                      {previewData.assigned_participants.map(p => p.name).join(', ')}
                    </div>
                  )}
                  {previewData.self_assigned_participants?.length > 0 && (
                    <div>
                      <span className="font-medium text-blue-800">Self-assigned: </span>
                      {previewData.self_assigned_participants.map(p => p.name).join(', ')}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Questions List */}
            <div className="flex-1 overflow-y-auto p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Interview Questions</h3>
              <div className="space-y-4">
                {previewData.questions?.map((question, index) => (
                  <div key={index} className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-sm font-medium">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <p className="text-gray-900">{question}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between p-6 border-t bg-gray-50">
              <div className="text-sm text-gray-600">
                {previewData.total_questions} questions • Estimated time: {Math.ceil(previewData.total_questions * 2)} minutes
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={closePreview}
                  className="btn-secondary"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    closePreview();
                    startThemeInterview(previewData.theme_id);
                  }}
                  className="btn-primary"
                >
                  <PlayIcon className="w-4 h-4 mr-2 inline" />
                  Start Interview
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectDashboard;

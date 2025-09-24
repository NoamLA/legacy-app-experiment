import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeftIcon, 
  PlayIcon, 
  CheckCircleIcon, 
  ClockIcon,
  UserIcon,
  ComputerDesktopIcon
} from '@heroicons/react/24/outline';

const ProjectDashboard = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [responses, setResponses] = useState([]);
  const [themes, setThemes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProject();
    fetchResponses();
  }, [projectId]);

  const fetchProject = async () => {
    try {
      const response = await fetch(`/api/projects/${projectId}`);
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
      const response = await fetch(`/api/projects/${projectId}/responses`);
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
      const response = await fetch(`/api/projects/${projectId}/identify-themes`, {
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
                <button 
                  onClick={() => startThemeInterview(theme.id)}
                  className="btn-primary w-full text-sm"
                >
                  <PlayIcon className="w-4 h-4 mr-2 inline" />
                  Explore Theme
                </button>
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
    </div>
  );
};

export default ProjectDashboard;

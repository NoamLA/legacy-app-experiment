import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeftIcon, 
  ArrowRightIcon, 
  MicrophoneIcon,
  StopIcon 
} from '@heroicons/react/24/outline';

const InterviewFlow = () => {
  const { projectId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const phase = searchParams.get('phase') || 'seed';
  const themeId = searchParams.get('themeId');
  
  const [project, setProject] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [responses, setResponses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isGeneratingResponse, setIsGeneratingResponse] = useState(false);

  useEffect(() => {
    fetchProject();
  }, [projectId]);

  useEffect(() => {
    fetchQuestions();
  }, [projectId, phase, themeId]);

  const fetchProject = async () => {
    try {
      const response = await fetch(`/projects/${projectId}`);
      if (response.ok) {
        const projectData = await response.json();
        setProject(projectData);
      }
    } catch (error) {
      console.error('Error fetching project:', error);
    }
  };

  const fetchQuestions = async () => {
    try {
      let endpoint = `/projects/${projectId}/seed-questions`;
      
      if (phase === 'theme' && themeId) {
        endpoint = `/projects/${projectId}/themes/${themeId}/questions`;
      }
      
      const response = await fetch(endpoint);
      if (response.ok) {
        const data = await response.json();
        console.log('API Response:', data); // Debug log
        setQuestions(data.questions || []);
      } else {
        console.error('API Error:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error fetching questions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSubmit = async () => {
    if (!currentAnswer.trim()) return;
    
    setSubmitting(true);
    
    try {
      const response = await fetch('/responses', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: projectId,
          question: questions[currentQuestionIndex],
          answer: currentAnswer,
          question_type: phase === 'seed' ? 'seed' : 'theme',
          theme_id: themeId
        }),
      });

      if (response.ok) {
        const responseData = await response.json();
        setResponses(prev => [...prev, responseData]);
        
        // Move to next question or show completion
        if (currentQuestionIndex < questions.length - 1) {
          setCurrentQuestionIndex(prev => prev + 1);
          setCurrentAnswer('');
        } else {
          // Interview phase complete
          navigate(`/project/${projectId}`);
        }
      }
    } catch (error) {
      console.error('Error submitting response:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSkipQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      setCurrentAnswer('');
    } else {
      navigate(`/project/${projectId}`);
    }
  };

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
      setCurrentAnswer('');
    }
  };

  // Mock voice recording functionality
  const toggleRecording = () => {
    setIsRecording(!isRecording);
    // In a real app, this would integrate with speech-to-text
    if (!isRecording) {
      // Start recording
      setTimeout(() => {
        setCurrentAnswer(prev => prev + " [Voice input simulated]");
        setIsRecording(false);
      }, 2000);
    }
  };

  // Generate AI response for testing
  const generateAgentResponse = async () => {
    if (!currentQuestion) return;
    
    setIsGeneratingResponse(true);
    
    try {
      const response = await fetch('/simulator/generate-response', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: projectId,
          question: currentQuestion,
          context: {
            phase: phase,
            theme_id: themeId,
            timestamp: new Date().toISOString()
          }
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentAnswer(data.generated_answer);
      } else {
        console.error('Failed to generate agent response');
      }
    } catch (error) {
      console.error('Error generating agent response:', error);
    } finally {
      setIsGeneratingResponse(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-64">
        <div className="text-lg text-gray-600">Loading interview questions...</div>
      </div>
    );
  }

  if (!questions.length) {
    return (
      <div className="text-center py-16">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">No Questions Available</h2>
        <button 
          onClick={() => navigate(`/project/${projectId}`)}
          className="btn-primary"
        >
          Back to Project
        </button>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / questions.length) * 100;

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate(`/project/${projectId}`)}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeftIcon className="w-5 h-5 mr-2" />
          Back to Project
        </button>
        
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {phase === 'seed' ? 'Getting to Know You' : 'Deep Dive Interview'}
          </h1>
          <p className="text-gray-600 mb-4">
            {phase === 'seed' 
              ? 'Let\'s start with some warm-up questions to build rapport'
              : `Exploring the theme in depth`
            }
          </p>
          
          {/* Progress Bar */}
          <div className="progress-bar mb-2">
            <div 
              className="progress-fill"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <div className="text-sm text-gray-600">
            Question {currentQuestionIndex + 1} of {questions.length}
          </div>
        </div>
      </div>

      {/* Question Card */}
      <div className="interview-card mb-8">
        <div className="question-bubble text-lg">
          {currentQuestion}
        </div>

        {/* Answer Input */}
        <div className="space-y-4">
          <div>
            <label htmlFor="answer" className="block text-sm font-medium text-gray-700 mb-2">
              Your Response
            </label>
            <textarea
              id="answer"
              value={currentAnswer}
              onChange={(e) => setCurrentAnswer(e.target.value)}
              placeholder="Share your thoughts, memories, and stories..."
              rows="6"
              className="textarea-field"
            />
          </div>

          {/* Voice Recording and Agent Response Buttons */}
          <div className="flex justify-center space-x-4">
            <button
              onClick={toggleRecording}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                isRecording 
                  ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                  : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
              }`}
            >
              {isRecording ? (
                <>
                  <StopIcon className="w-5 h-5" />
                  <span>Stop Recording</span>
                </>
              ) : (
                <>
                  <MicrophoneIcon className="w-5 h-5" />
                  <span>Record Voice</span>
                </>
              )}
            </button>

            {/* Agent Answer Button - For Testing */}
            <button
              onClick={generateAgentResponse}
              disabled={isGeneratingResponse}
              className="flex items-center space-x-2 px-4 py-2 bg-purple-100 text-purple-700 hover:bg-purple-200 rounded-lg transition-colors disabled:opacity-50"
            >
              {isGeneratingResponse ? (
                <>
                  <div className="w-5 h-5 border-2 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
                  <span>Generating...</span>
                </>
              ) : (
                <>
                  <span className="w-5 h-5 flex items-center justify-center">🤖</span>
                  <span>Agent Answer</span>
                </>
              )}
            </button>
          </div>

          {isRecording && (
            <div className="text-center">
              <div className="inline-flex items-center space-x-2 text-red-600">
                <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse"></div>
                <span className="text-sm">Recording... speak naturally</span>
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between items-center mt-8 pt-6 border-t">
          <button
            onClick={handlePreviousQuestion}
            disabled={currentQuestionIndex === 0}
            className={`flex items-center space-x-2 ${
              currentQuestionIndex === 0 
                ? 'text-gray-400 cursor-not-allowed' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <ArrowLeftIcon className="w-5 h-5" />
            <span>Previous</span>
          </button>

          <div className="flex space-x-3">
            <button
              onClick={handleSkipQuestion}
              className="btn-secondary"
            >
              Skip Question
            </button>
            
            <button
              onClick={handleAnswerSubmit}
              disabled={submitting || !currentAnswer.trim()}
              className="btn-primary flex items-center space-x-2"
            >
              <span>
                {submitting ? 'Saving...' : 
                 currentQuestionIndex === questions.length - 1 ? 'Complete' : 'Next Question'}
              </span>
              {!submitting && <ArrowRightIcon className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Testing Mode Indicator */}
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
        <h3 className="font-medium text-purple-900 mb-2">🧪 Testing Mode Active</h3>
        <p className="text-sm text-purple-800">
          Use the <strong>"Agent Answer"</strong> button to generate authentic AI responses for testing the complete interview flow.
          The AI will simulate realistic human answers based on the project's character profile.
        </p>
      </div>

      {/* Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 mb-2">💡 Interview Tips</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Take your time - there's no rush</li>
          <li>• Share specific stories and details</li>
          <li>• It's okay to skip questions that don't resonate</li>
          <li>• Use the voice recorder if you prefer speaking</li>
          <li>• <strong>Testing:</strong> Click "Agent Answer" to simulate responses</li>
        </ul>
      </div>
    </div>
  );
};

export default InterviewFlow;

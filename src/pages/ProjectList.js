import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  ArrowLeftIcon, 
  PlayIcon, 
  ClockIcon,
  CheckCircleIcon,
  UserIcon,
  CalendarIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline';

const ProjectList = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      // Since there's no list endpoint, we'll need to get projects from the database
      // For now, let's create a mock implementation that we can replace with real API
      const response = await fetch('/api/projects/list');
      
      if (response.ok) {
        const data = await response.json();
        setProjects(data.projects || []);
      } else {
        // Fallback: try to get projects from localStorage or show empty state
        const savedProjects = localStorage.getItem('legacy_projects');
        if (savedProjects) {
          setProjects(JSON.parse(savedProjects));
        } else {
          setProjects([]);
        }
      }
    } catch (error) {
      console.error('Error fetching projects:', error);
      setError('Failed to load projects');
      // Try localStorage fallback
      const savedProjects = localStorage.getItem('legacy_projects');
      if (savedProjects) {
        setProjects(JSON.parse(savedProjects));
      }
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'themes_identified':
        return 'bg-blue-100 text-blue-800';
      case 'seed_questions':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-600" />;
      case 'themes_identified':
        return <ChatBubbleLeftRightIcon className="w-5 h-5 text-blue-600" />;
      case 'seed_questions':
        return <ClockIcon className="w-5 h-5 text-yellow-600" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-600" />;
    }
  };

  const getNextAction = (project) => {
    switch (project.status) {
      case 'created':
        return {
          text: 'Start Interview',
          action: () => navigate(`/interview/${project.id}?phase=seed`),
          className: 'btn-primary'
        };
      case 'seed_questions':
        return {
          text: 'Continue Questions',
          action: () => navigate(`/interview/${project.id}?phase=seed`),
          className: 'btn-primary'
        };
      case 'themes_identified':
        return {
          text: 'Explore Themes',
          action: () => navigate(`/project/${project.id}`),
          className: 'btn-primary'
        };
      case 'completed':
        return {
          text: 'View Results',
          action: () => navigate(`/project/${project.id}`),
          className: 'btn-secondary'
        };
      default:
        return {
          text: 'Continue',
          action: () => navigate(`/project/${project.id}`),
          className: 'btn-primary'
        };
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-center items-center min-h-64">
          <div className="text-lg text-gray-600">Loading your projects...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeftIcon className="w-5 h-5 mr-2" />
          Back to Home
        </button>
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Your Interview Projects
            </h1>
            <p className="text-gray-600">
              Continue working on your family legacy interviews
            </p>
          </div>
          
          <Link to="/create-project" className="btn-primary">
            <PlayIcon className="w-5 h-5 mr-2 inline" />
            New Project
          </Link>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="interview-card border-red-200 bg-red-50 mb-6">
          <div className="text-red-800 font-medium mb-2">Error Loading Projects</div>
          <div className="text-red-600 text-sm">{error}</div>
          <button 
            onClick={fetchProjects}
            className="mt-3 btn-secondary text-sm"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Empty State */}
      {projects.length === 0 && !error && (
        <div className="text-center py-16">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <ChatBubbleLeftRightIcon className="w-8 h-8 text-gray-400" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">No Projects Yet</h2>
          <p className="text-gray-600 mb-8 max-w-md mx-auto">
            Start your first legacy interview project to preserve precious family memories and stories.
          </p>
          <Link to="/create-project" className="btn-primary text-lg px-8 py-3">
            Create Your First Project
          </Link>
        </div>
      )}

      {/* Projects Grid */}
      {projects.length > 0 && (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => {
            const nextAction = getNextAction(project);
            
            return (
              <div key={project.id} className="interview-card hover:shadow-xl transition-all duration-200">
                {/* Project Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1 line-clamp-2">
                      {project.name}
                    </h3>
                    <div className="flex items-center text-sm text-gray-600">
                      <UserIcon className="w-4 h-4 mr-1" />
                      {project.subject_info?.name || project.subject_name}
                    </div>
                  </div>
                  
                  <div className="flex items-center ml-3">
                    {getStatusIcon(project.status)}
                  </div>
                </div>

                {/* Project Details */}
                <div className="space-y-2 mb-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Status:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
                      {project.status.replace('_', ' ')}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Relationship:</span>
                    <span className="text-gray-900 font-medium">
                      {project.subject_info?.relation || project.relation}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Mode:</span>
                    <span className="text-gray-900 capitalize">
                      {project.interview_mode}
                    </span>
                  </div>
                  
                  {project.created_at && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Created:</span>
                      <div className="flex items-center text-gray-900">
                        <CalendarIcon className="w-4 h-4 mr-1" />
                        {formatDate(project.created_at)}
                      </div>
                    </div>
                  )}
                </div>

                {/* Progress Indicator */}
                <div className="mb-4">
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-gray-600">Progress</span>
                    <span className="text-gray-900 font-medium">
                      {project.responses?.length || 0} responses
                    </span>
                  </div>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill"
                      style={{
                        width: `${Math.min(100, ((project.responses?.length || 0) / 10) * 100)}%`
                      }}
                    />
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex space-x-2">
                  <button
                    onClick={nextAction.action}
                    className={`${nextAction.className} flex-1 text-sm`}
                  >
                    <PlayIcon className="w-4 h-4 mr-2 inline" />
                    {nextAction.text}
                  </button>
                  
                  <button
                    onClick={() => navigate(`/project/${project.id}`)}
                    className="btn-secondary text-sm px-3"
                    title="View Dashboard"
                  >
                    Dashboard
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Quick Stats */}
      {projects.length > 0 && (
        <div className="mt-12 grid md:grid-cols-4 gap-4">
          <div className="interview-card text-center">
            <div className="text-2xl font-bold text-blue-600 mb-1">
              {projects.length}
            </div>
            <div className="text-sm text-gray-600">Total Projects</div>
          </div>
          
          <div className="interview-card text-center">
            <div className="text-2xl font-bold text-green-600 mb-1">
              {projects.filter(p => p.status === 'completed').length}
            </div>
            <div className="text-sm text-gray-600">Completed</div>
          </div>
          
          <div className="interview-card text-center">
            <div className="text-2xl font-bold text-yellow-600 mb-1">
              {projects.filter(p => p.status === 'seed_questions' || p.status === 'themes_identified').length}
            </div>
            <div className="text-sm text-gray-600">In Progress</div>
          </div>
          
          <div className="interview-card text-center">
            <div className="text-2xl font-bold text-gray-600 mb-1">
              {projects.reduce((total, p) => total + (p.responses?.length || 0), 0)}
            </div>
            <div className="text-sm text-gray-600">Total Responses</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectList;

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

const ProjectCreate = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    subject_name: '',
    subject_age: '',
    relation: '',
    background: '',
    interview_mode: 'self',
    language: 'en'
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await fetch('/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          subject_age: formData.subject_age ? parseInt(formData.subject_age) : null
        }),
      });

      if (response.ok) {
        const project = await response.json();
        navigate(`/project/${project.id}`);
      } else {
        console.error('Failed to create project');
        // Handle error
      }
    } catch (error) {
      console.error('Error creating project:', error);
      // Handle error
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeftIcon className="w-5 h-5 mr-2" />
          Back to Home
        </button>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Create New Interview Project
        </h1>
        <p className="text-gray-600">
          Set up a new legacy interview project to start capturing precious memories.
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="interview-card">
        <div className="space-y-6">
          {/* Project Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              Project Name
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="e.g., Grandma Sarah's Stories"
              className="input-field"
              required
            />
            <p className="text-sm text-gray-500 mt-1">
              Give your project a memorable name
            </p>
          </div>

          {/* Subject Information */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">About the Interview Subject</h3>
            
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="subject_name" className="block text-sm font-medium text-gray-700 mb-2">
                  Subject's Name
                </label>
                <input
                  type="text"
                  id="subject_name"
                  name="subject_name"
                  value={formData.subject_name}
                  onChange={handleInputChange}
                  placeholder="Full name"
                  className="input-field"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="subject_age" className="block text-sm font-medium text-gray-700 mb-2">
                  Age (Optional)
                </label>
                <input
                  type="number"
                  id="subject_age"
                  name="subject_age"
                  value={formData.subject_age}
                  onChange={handleInputChange}
                  placeholder="Age"
                  className="input-field"
                  min="1"
                  max="120"
                />
              </div>
            </div>

            <div className="mt-4">
              <label htmlFor="relation" className="block text-sm font-medium text-gray-700 mb-2">
                Relationship to You
              </label>
              <select
                id="relation"
                name="relation"
                value={formData.relation}
                onChange={handleInputChange}
                className="input-field"
                required
              >
                <option value="">Select relationship</option>
                <option value="grandmother">Grandmother</option>
                <option value="grandfather">Grandfather</option>
                <option value="mother">Mother</option>
                <option value="father">Father</option>
                <option value="aunt">Aunt</option>
                <option value="uncle">Uncle</option>
                <option value="family_friend">Family Friend</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="mt-4">
              <label htmlFor="background" className="block text-sm font-medium text-gray-700 mb-2">
                Background Information (Optional)
              </label>
              <textarea
                id="background"
                name="background"
                value={formData.background}
                onChange={handleInputChange}
                placeholder="Any important context about their life, interests, or experiences..."
                rows="3"
                className="textarea-field"
              />
            </div>
          </div>

          {/* Interview Mode */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Interview Mode</h3>
            
            <div className="space-y-3">
              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="radio"
                  name="interview_mode"
                  value="self"
                  checked={formData.interview_mode === 'self'}
                  onChange={handleInputChange}
                  className="mt-1"
                />
                <div>
                  <div className="font-medium text-gray-900">Self Interview</div>
                  <div className="text-sm text-gray-600">AI interviewer leads all conversations</div>
                </div>
              </label>
              
              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="radio"
                  name="interview_mode"
                  value="family"
                  checked={formData.interview_mode === 'family'}
                  onChange={handleInputChange}
                  className="mt-1"
                />
                <div>
                  <div className="font-medium text-gray-900">Family-led</div>
                  <div className="text-sm text-gray-600">Assign questions to family members</div>
                </div>
              </label>
              
              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="radio"
                  name="interview_mode"
                  value="hybrid"
                  checked={formData.interview_mode === 'hybrid'}
                  onChange={handleInputChange}
                  className="mt-1"
                />
                <div>
                  <div className="font-medium text-gray-900">Hybrid</div>
                  <div className="text-sm text-gray-600">Mix of AI and family member interviews</div>
                </div>
              </label>
            </div>
          </div>

          {/* Language */}
          <div className="border-t pt-6">
            <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-2">
              Interview Language
            </label>
            <select
              id="language"
              name="language"
              value={formData.language}
              onChange={handleInputChange}
              className="input-field"
            >
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
              <option value="it">Italian</option>
              <option value="pt">Portuguese</option>
            </select>
          </div>
        </div>

        {/* Submit Button */}
        <div className="mt-8 pt-6 border-t">
          <button
            type="submit"
            disabled={isSubmitting}
            className="btn-primary w-full text-lg py-3"
          >
            {isSubmitting ? 'Creating Project...' : 'Create Project & Start Interview'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ProjectCreate;

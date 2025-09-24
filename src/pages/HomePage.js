import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRightIcon, UserGroupIcon, MicrophoneIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

const HomePage = () => {
  const features = [
    {
      icon: MicrophoneIcon,
      title: "AI-Driven Interviews",
      description: "Smart questions that adapt to responses, building rapport while capturing meaningful stories."
    },
    {
      icon: UserGroupIcon,
      title: "Family Collaboration",
      description: "Assign questions to family members or let AI handle interviews with seamless coordination."
    },
    {
      icon: DocumentTextIcon,
      title: "Multiple Outputs",
      description: "Transform interviews into podcasts, storybooks, web pages, or timeline narratives."
    }
  ];

  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero Section */}
      <div className="text-center py-16">
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          Preserve Your Family's
          <span className="text-blue-600 block">Legacy Stories</span>
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          Capture and preserve personal legacies through AI-driven, collaborative interviews. 
          Turn precious memories into lasting stories for future generations.
        </p>
        <div className="flex justify-center space-x-4">
          <Link to="/create-project" className="btn-primary text-lg px-8 py-3">
            Start Your First Interview
            <ArrowRightIcon className="w-5 h-5 ml-2 inline" />
          </Link>
          <button className="btn-secondary text-lg px-8 py-3">
            Watch Demo
          </button>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          How It Works
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="interview-card text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <feature.icon className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">
                {feature.title}
              </h3>
              <p className="text-gray-600">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Process Flow */}
      <div className="py-16 bg-gray-50 -mx-4 px-4 rounded-lg">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          The Interview Process
        </h2>
        <div className="grid md:grid-cols-4 gap-6">
          {[
            {
              step: "1",
              title: "Setup Project",
              description: "Create family group, set consents, choose interview mode"
            },
            {
              step: "2", 
              title: "Seed Questions",
              description: "AI generates warm-up questions to build rapport and gather basics"
            },
            {
              step: "3",
              title: "Deep Dive",
              description: "Explore themes with family members or AI interviewer"
            },
            {
              step: "4",
              title: "Create Legacy",
              description: "Generate podcasts, stories, or web pages from interviews"
            }
          ].map((item, index) => (
            <div key={index} className="text-center">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-lg font-bold">
                {item.step}
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {item.title}
              </h3>
              <p className="text-gray-600 text-sm">
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA Section */}
      <div className="text-center py-16">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Ready to Start Preserving Stories?
        </h2>
        <p className="text-xl text-gray-600 mb-8">
          Every family has stories worth preserving. Let's capture yours.
        </p>
        <Link to="/create-project" className="btn-primary text-lg px-8 py-3">
          Create Your First Project
        </Link>
      </div>
    </div>
  );
};

export default HomePage;

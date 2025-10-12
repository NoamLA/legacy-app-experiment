import React from 'react';
import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">L</span>
            </div>
            <h1 className="text-xl font-bold text-gray-900">Legacy Interview</h1>
          </Link>
          
          <nav className="flex items-center space-x-6">
            <Link 
              to="/" 
              className="text-gray-600 hover:text-gray-900 transition-colors"
            >
              Home
            </Link>
            <Link 
              to="/projects" 
              className="text-gray-600 hover:text-gray-900 transition-colors"
            >
              My Projects
            </Link>
            <Link 
              to="/create-project" 
              className="btn-primary"
            >
              New Project
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;

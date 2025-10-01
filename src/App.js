import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

// Components
import Header from './components/Header';
import HomePage from './pages/HomePage';
import ProjectCreate from './pages/ProjectCreate';
import ProjectList from './pages/ProjectList';
import InterviewFlow from './pages/InterviewFlow';
import ProjectDashboard from './pages/ProjectDashboard';
import ConversationManager from './pages/ConversationManager';

function App() {
  return (
    <Router>
      <div className="App min-h-screen bg-gray-50">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/create-project" element={<ProjectCreate />} />
            <Route path="/projects" element={<ProjectList />} />
            <Route path="/project/:projectId" element={<ProjectDashboard />} />
            <Route path="/interview/:projectId" element={<InterviewFlow />} />
            <Route path="/project/:projectId/conversations" element={<ConversationManager />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

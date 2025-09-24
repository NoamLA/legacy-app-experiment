import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

// Components
import Header from './components/Header';
import HomePage from './pages/HomePage';
import ProjectCreate from './pages/ProjectCreate';
import InterviewFlow from './pages/InterviewFlow';
import ProjectDashboard from './pages/ProjectDashboard';

function App() {
  return (
    <Router>
      <div className="App min-h-screen bg-gray-50">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/create-project" element={<ProjectCreate />} />
            <Route path="/project/:projectId" element={<ProjectDashboard />} />
            <Route path="/interview/:projectId" element={<InterviewFlow />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

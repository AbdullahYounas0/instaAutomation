import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './components/LoginPage';
import HomePage from './components/HomePage';
import DailyPostPage from './components/DailyPostPage';
import DMAutomationPage from './components/DMAutomationPage';
import WarmupPage from './components/WarmupPage';
import AdminDashboard from './components/AdminDashboard';
import ProtectedRoute from './components/ProtectedRoute';
import ToastManager from './components/ToastManager';
import './App.css';

function App() {
  return (
    <ToastManager>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route 
              path="/home" 
              element={
                <ProtectedRoute>
                  <HomePage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/daily-post" 
              element={
                <ProtectedRoute>
                  <DailyPostPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/dm-automation" 
              element={
                <ProtectedRoute>
                  <DMAutomationPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/warmup" 
              element={
                <ProtectedRoute>
                  <WarmupPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/admin" 
              element={
                <ProtectedRoute adminOnly>
                  <AdminDashboard />
                </ProtectedRoute>
              } 
            />
            <Route path="/" element={<Navigate to="/login" replace />} />
          </Routes>
        </div>
      </Router>
    </ToastManager>
  );
}

export default App;

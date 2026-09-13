
import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { AnalysisProvider } from './contexts/AnalysisContext';
import { WardrobeProvider } from './contexts/WardrobeContext';

import WelcomePage from './pages/WelcomePage';
import SignInPage from './pages/SignInPage';
import SignUpPage from './pages/SignUpPage';
import HomePage from './pages/HomePage';
import StyleConsultationIntroPage from './pages/StyleConsultationIntroPage';
import FaceAnalysisPage from './pages/FaceAnalysisPage';
import FaceAnalysisResultsPage from './pages/FaceAnalysisResultsPage';
import ChromaticQuizPage from './pages/ChromaticQuizPage';
import SeasonResultsPage from './pages/SeasonResultsPage';
import StyleTipsPage from './pages/StyleTipsPage';
import ProfilePage from './pages/ProfilePage';
import { WardrobePage } from './pages/WardrobePage';
import { OutfitGeneratorPage } from './pages/OutfitGeneratorPage';
import BottomNavigationBar from './components/Navigation/BottomNavigationBar';
import PageHeader from './components/UI/PageHeader';

// ProtectedRoute component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const auth = useAuth();
  if (!auth.isAuthenticated) {
    return <Navigate to="/welcome" replace />;
  }
  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <div className="flex-grow pb-16 sm:pb-20"> {/* Padding for bottom nav */}
        {children}
      </div>
      <BottomNavigationBar />
    </div>
  );
};

// AuthLayout component
const AuthLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-rose-100 to-teal-100 p-4">
      <div className="w-full max-w-md">
        {children}
      </div>
    </div>
  );
};


const App: React.FC = () => {
  return (
    <AuthProvider>
      <AnalysisProvider>
        <WardrobeProvider>
          <HashRouter>
          <Routes>
            <Route path="/welcome" element={<WelcomePage />} />
            <Route path="/signin" element={<AuthLayout><SignInPage /></AuthLayout>} />
            <Route path="/signup" element={<AuthLayout><SignUpPage /></AuthLayout>} />
            
            <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
            <Route path="/style-consultation" element={<ProtectedRoute><StyleConsultationIntroPage /></ProtectedRoute>} />
            <Route path="/face-analysis" element={<ProtectedRoute><FaceAnalysisPage /></ProtectedRoute>} />
            <Route path="/face-analysis-results" element={<ProtectedRoute><FaceAnalysisResultsPage /></ProtectedRoute>} />
            <Route path="/chromatic-quiz" element={<ProtectedRoute><ChromaticQuizPage /></ProtectedRoute>} />
            <Route path="/season-results" element={<ProtectedRoute><SeasonResultsPage /></ProtectedRoute>} />
            <Route path="/style-tips" element={<ProtectedRoute><StyleTipsPage /></ProtectedRoute>} />
            <Route path="/wardrobe" element={<ProtectedRoute><WardrobePage /></ProtectedRoute>} />
            <Route path="/outfit-generator" element={<ProtectedRoute><OutfitGeneratorPage /></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
            
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </HashRouter>
        </WardrobeProvider>
      </AnalysisProvider>
    </AuthProvider>
  );
};

export default App;

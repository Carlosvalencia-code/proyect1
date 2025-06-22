
import React from 'react';
import { Link, Navigate } from 'react-router-dom';
import Button from '../components/UI/Button';
import { APP_NAME, APP_SLOGAN } from '../constants';
import { useAuth } from '../contexts/AuthContext';

const WelcomePage: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-300 via-purple-300 to-indigo-400">
        {/* You can add a spinner here */}
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  
  return (
    <div className="min-h-screen flex flex-col">
      <div className="relative h-2/5 sm:h-1/2">
        <img 
          src="https://picsum.photos/seed/synthiafashion/1200/800" 
          alt="Fashion model" 
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-white via-white/70 to-transparent"></div>
      </div>
      
      <div className="flex-grow flex flex-col items-center justify-center text-center px-6 py-8 bg-white -mt-16 sm:-mt-24 relative z-10 rounded-t-3xl shadow-2xl">
        <h1 className="text-4xl sm:text-5xl font-bold text-gray-800 mb-3 tracking-tight">{APP_NAME}</h1>
        <p className="text-lg text-gray-600 mb-12">{APP_SLOGAN}</p>
        
        <div className="w-full max-w-xs space-y-4">
          <Link to="/signup" className="block w-full">
            <Button variant="primary" fullWidth size="lg">Create Account</Button>
          </Link>
          <Link to="/signin" className="block w-full">
            <Button variant="secondary" fullWidth size="lg">Sign In</Button>
          </Link>
        </div>
        <p className="text-xs text-gray-400 mt-12">
          Discover your unique style with AI.
        </p>
      </div>
    </div>
  );
};

export default WelcomePage;

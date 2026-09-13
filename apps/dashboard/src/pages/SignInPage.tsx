
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Button from '../components/UI/Button';
import Input from '../components/UI/Input';
import { useAuth } from '../contexts/AuthContext';
import { APP_NAME } from '../constants';
import { ArrowLeftIcon } from '../components/icons';

const SignInPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const auth = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await auth.signIn(email); // Mocked sign in
      navigate('/');
    } catch (err) {
      setError((err as Error).message || "Sign in failed. Please check your credentials.");
    }
  };

  return (
    <div className="bg-white p-6 sm:p-8 rounded-xl shadow-2xl w-full max-w-md">
      <button onClick={() => navigate('/welcome')} className="absolute top-4 left-4 text-gray-600 hover:text-gray-800">
         <ArrowLeftIcon className="w-6 h-6" />
      </button>
      <h2 className="text-3xl font-bold text-center text-gray-800 mb-2">Log In</h2>
      <p className="text-center text-gray-500 mb-8">Welcome back to {APP_NAME}!</p>
      
      {error && <p className="mb-4 text-center text-sm text-red-600 bg-red-100 p-2 rounded-md">{error}</p>}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <Input 
          label="Email" 
          id="email" 
          type="email" 
          value={email} 
          onChange={(e) => setEmail(e.target.value)} 
          placeholder="Enter your email" 
          required 
        />
        <Input 
          label="Password" 
          id="password" 
          type="password" 
          value={password} 
          onChange={(e) => setPassword(e.target.value)} 
          placeholder="Enter your password" 
          required 
        />
        
        <div className="flex items-center justify-end">
          <div className="text-sm">
            <a href="#" className="font-medium text-blue-600 hover:text-blue-500">
              Forgot Password?
            </a>
          </div>
        </div>
        
        <Button type="submit" variant="primary" fullWidth size="lg" isLoading={auth.isLoading}>
          Log In
        </Button>
      </form>
      
      <p className="mt-8 text-center text-sm text-gray-600">
        Don't have an account?{' '}
        <Link to="/signup" className="font-medium text-blue-600 hover:text-blue-500">
          Sign up
        </Link>
      </p>
    </div>
  );
};

export default SignInPage;

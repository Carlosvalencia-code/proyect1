
import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  signIn: (email: string, fullName?: string) => Promise<void>; // fullName for signup
  signUp: (fullName: string, email: string) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Mock loading user from localStorage
    const storedUser = localStorage.getItem('synthiaUser');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const signIn = async (email: string, fullName?: string): Promise<void> => {
    setIsLoading(true);
    // Mock API call
    await new Promise(resolve => setTimeout(resolve, 500));
    const mockUser: User = { 
      id: Date.now().toString(), 
      email, 
      fullName: fullName || "Demo User", // Use provided name or default
      joinedDate: "Joined " + new Date().getFullYear()
    };
    setUser(mockUser);
    localStorage.setItem('synthiaUser', JSON.stringify(mockUser));
    setIsLoading(false);
  };
  
  const signUp = async (fullName: string, email: string): Promise<void> => {
    // In this mock, signUp is the same as signIn for simplicity
    return signIn(email, fullName);
  };

  const signOut = () => {
    setUser(null);
    localStorage.removeItem('synthiaUser');
    localStorage.removeItem('synthiaAnalysis'); // Also clear analysis data
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

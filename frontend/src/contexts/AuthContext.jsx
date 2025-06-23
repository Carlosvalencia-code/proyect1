import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import apiClient from '../services/api';
// Optional: import { jwtDecode } from 'jwt-decode'; // If you want to decode token for non-sensitive info

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null); // Stores user object {id, email, name, etc.}
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  const [isLoading, setIsLoading] = useState(true); // For initial auth state check

  // Function to fetch user profile if token exists (e.g., on app load)
  // This should ideally call a protected backend endpoint like /auth/me
  const verifyTokenAndFetchUser = useCallback(async (currentToken) => {
    if (!currentToken) {
      setUser(null);
      setToken(null); // Ensure token state is also cleared if local storage one is invalid
      localStorage.removeItem('authToken'); // Clean up local storage
      setIsLoading(false);
      return;
    }
    try {
      // Example: Replace with your actual /auth/me or similar endpoint
      // const response = await apiClient.get('/auth/me'); // apiClient already includes token
      // setUser(response.data); // Assuming response.data is the user object

      // SIMPLIFIED: If no /me endpoint, we'll assume token is valid for now
      // and just set a placeholder user or decode minimal info if available.
      // This is NOT secure for actual user data validation. A backend check is crucial.
      // For example, if token contained user email in 'sub' field:
      // const decoded = jwtDecode(currentToken);
      // setUser({ email: decoded.sub, id: decoded.user_id }); // If user_id is also in token

      // For this example, we'll just acknowledge a token is present.
      // Actual user data should be set after login or by a /me endpoint.
      // If you don't fetch user data here, 'user' state will be null until login.
      // This means isAuthenticated might be true, but 'user' object is not populated yet.
      // This is a common pattern if /me is called by specific components needing user data.
      console.log("AuthContext: Token found, assuming valid for now. User data not fetched on load in this example.");
      // setUser({ tempUser: true }); // Example if you want to mark user as present

    } catch (error) {
      console.error('AuthContext: Token validation failed or /me endpoint error:', error);
      localStorage.removeItem('authToken');
      setToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const currentToken = localStorage.getItem('authToken');
    if (currentToken) {
      setToken(currentToken); // Set token state from local storage
      verifyTokenAndFetchUser(currentToken);
    } else {
      setIsLoading(false); // No token, so not loading anymore
    }
  }, [verifyTokenAndFetchUser]);

  const login = async (email, password) => {
    setIsLoading(true);
    const formData = new URLSearchParams();
    formData.append('username', email); // Matches FastAPI's OAuth2PasswordRequestForm
    formData.append('password', password);

    try {
      const response = await apiClient.post('/auth/login', formData, {
         headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      const { access_token } = response.data;
      localStorage.setItem('authToken', access_token);
      setToken(access_token);
      // After successful login, you SHOULD fetch user details or decode token for user info
      // For example, if your /auth/me endpoint exists:
      // await verifyTokenAndFetchUser(access_token);
      // Or if login response includes user data: setUser(userDataFromLoginResponse);
      // For now, user state is not explicitly set here post-login, relying on verifyTokenAndFetchUser or component-level fetches.
      setIsLoading(false);
    } catch (error) {
      localStorage.removeItem('authToken'); // Clear token on failed login
      setToken(null);
      setUser(null);
      setIsLoading(false);
      throw error; // Re-throw error to be handled by the calling component (LoginPage)
    }
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    setToken(null);
    setUser(null);
    // Navigation (e.g., to '/login') should be handled by components or ProtectedRoute
    // based on the change in 'isAuthenticated' state.
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        setUser, // Expose setUser if components need to update user profile after fetching
        isAuthenticated: !!token, // Derived from token state
        isLoading,
        login,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

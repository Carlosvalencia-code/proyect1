// SEENTIA Frontend - Authentication Service

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'; // Default to local backend

export interface RegistrationPayload {
  email: string;
  password: string;
  name?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface UserResponse {
  id: string;
  email: string;
  name?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export const authService = {
  register: async (payload: RegistrationPayload): Promise<UserResponse> => {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(errorData.detail || 'Failed to register');
    }
    return response.json();
  },

  login: async (payload: LoginPayload): Promise<TokenResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', payload.email); // FastAPI's OAuth2PasswordRequestForm expects 'username'
    formData.append('password', payload.password);

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(errorData.detail || 'Failed to log in');
    }
    return response.json();
  },

  // TODO: Add logout function (e.g., clear token from storage)
  // TODO: Add function to get current user if token exists and is valid (requires backend endpoint)
  // TODO: Add functions to store and retrieve token from localStorage/sessionStorage
};

// Helper to manage token storage (example)
const TOKEN_KEY = 'seentia_access_token';

export const storeToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
};

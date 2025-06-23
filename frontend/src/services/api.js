import axios from 'axios';

// Determine the API base URL from environment variables (Vite specific)
// Fallback to localhost for development if not set.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    // Other default headers can be added here
  },
});

// Request interceptor to add the JWT token to Authorization header
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken'); // Key used for storing the token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    // Handle request error here
    return Promise.reject(error);
  }
);

// Optional: Response interceptor for global error handling or token refresh logic
apiClient.interceptors.response.use(
  (response) => {
    // Any status code that lie within the range of 2xx cause this function to trigger
    return response;
  },
  (error) => {
    // Any status codes that falls outside the range of 2xx cause this function to trigger
    if (error.response && error.response.status === 401) {
      // Handle 401 Unauthorized errors (e.g., token expired or invalid)
      console.error("API: Unauthorized access (401). Token might be invalid or expired.");
      // Consider removing the token and redirecting to login:
      // localStorage.removeItem('authToken');
      // window.location.href = '/login'; // Or use React Router navigation if accessible here
      // Or, if using an event bus or Zustand/Redux, dispatch a logout action.
    }
    // It's important to return a Promise.reject here so that the calling code's .catch() block is executed.
    return Promise.reject(error);
  }
);

export default apiClient;

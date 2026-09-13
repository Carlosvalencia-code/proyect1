// =============================================================================
// SYNTHIA STYLE - API SERVICE
// =============================================================================
// Centralized API service for FastAPI backend integration

import { 
  FacialAnalysisDataAPI, 
  ChromaticAnalysisDataAPI,
  User,
  FeedbackSubmission
} from '../types';

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface ApiError {
  detail: string;
  error_code?: string;
}

/**
 * Centralized API service for Synthia Style FastAPI backend
 */
export class SynthiaAPIService {
  private baseURL: string;
  private authToken: string | null = null;

  constructor(baseURL: string = '/api/v1') {
    this.baseURL = baseURL;
    
    // Try to load token from localStorage
    const savedToken = localStorage.getItem('synthia_auth_token');
    if (savedToken) {
      this.authToken = savedToken;
    }
  }

  /**
   * Set authentication token
   */
  setAuthToken(token: string): void {
    this.authToken = token;
    localStorage.setItem('synthia_auth_token', token);
  }

  /**
   * Clear authentication token
   */
  clearAuthToken(): void {
    this.authToken = null;
    localStorage.removeItem('synthia_auth_token');
  }

  /**
   * Get current auth token
   */
  getAuthToken(): string | null {
    return this.authToken;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.authToken !== null;
  }

  // =============================================================================
  // AUTHENTICATION ENDPOINTS
  // =============================================================================

  /**
   * Register new user
   */
  async register(userData: RegisterRequest): Promise<LoginResponse> {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
      headers: { 'Content-Type': 'application/json' },
    });
  }

  /**
   * Login user
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
      headers: { 'Content-Type': 'application/json' },
    });

    // Auto-save token on successful login
    this.setAuthToken(response.access_token);
    
    return response;
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', {
        method: 'POST',
      });
    } finally {
      // Always clear token, even if logout request fails
      this.clearAuthToken();
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<LoginResponse> {
    return this.request('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // =============================================================================
  // USER ENDPOINTS
  // =============================================================================

  /**
   * Get current user profile
   */
  async getProfile(): Promise<User> {
    return this.request('/users/me');
  }

  /**
   * Update user profile
   */
  async updateProfile(userData: Partial<User>): Promise<User> {
    return this.request('/users/profile', {
      method: 'PUT',
      body: JSON.stringify(userData),
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // =============================================================================
  // ANALYSIS ENDPOINTS
  // =============================================================================

  /**
   * Submit facial analysis with image
   */
  async facialAnalysis(imageFile: File, preferences?: Record<string, any>): Promise<FacialAnalysisDataAPI> {
    const formData = new FormData();
    formData.append('image', imageFile);
    
    if (preferences) {
      formData.append('preferences', JSON.stringify(preferences));
    }

    return this.request('/analysis/facial', {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * Get facial analysis result by ID
   */
  async getFacialAnalysis(analysisId: string): Promise<FacialAnalysisDataAPI> {
    return this.request(`/analysis/facial/${analysisId}`);
  }

  /**
   * Submit chromatic analysis quiz
   */
  async chromaticAnalysis(responses: Record<string, string>): Promise<ChromaticAnalysisDataAPI> {
    return this.request('/analysis/chromatic', {
      method: 'POST',
      body: JSON.stringify({ responses }),
      headers: { 'Content-Type': 'application/json' },
    });
  }

  /**
   * Get chromatic analysis result by ID
   */
  async getChromaticAnalysis(analysisId: string): Promise<ChromaticAnalysisDataAPI> {
    return this.request(`/analysis/chromatic/${analysisId}`);
  }

  /**
   * Get user's analysis history
   */
  async getAnalysisHistory(): Promise<{
    facial: FacialAnalysisDataAPI[];
    chromatic: ChromaticAnalysisDataAPI[];
  }> {
    return this.request('/analysis/history');
  }

  // =============================================================================
  // FEEDBACK ENDPOINTS
  // =============================================================================

  /**
   * Submit user feedback
   */
  async submitFeedback(feedback: FeedbackSubmission): Promise<{ success: boolean; id: string }> {
    return this.request('/feedback', {
      method: 'POST',
      body: JSON.stringify(feedback),
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // =============================================================================
  // FILE UPLOAD ENDPOINTS
  // =============================================================================

  /**
   * Upload file to server
   */
  async uploadFile(file: File, category?: string): Promise<{ url: string; filename: string }> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (category) {
      formData.append('category', category);
    }

    return this.request('/files/upload', {
      method: 'POST',
      body: formData,
    });
  }

  // =============================================================================
  // WARDROBE ENDPOINTS
  // =============================================================================

  /**
   * Get wardrobe items with filters
   */
  async getWardrobeItems(filters?: {
    category?: string;
    color?: string;
    season?: string;
    occasion?: string;
    style?: string;
    is_favorite?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<WardrobeItem[]> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    const endpoint = params.toString() ? `/wardrobe/items?${params}` : '/wardrobe/items';
    return this.request(endpoint);
  }

  /**
   * Get single wardrobe item
   */
  async getWardrobeItem(itemId: string): Promise<WardrobeItem> {
    return this.request(`/wardrobe/items/${itemId}`);
  }

  /**
   * Create new wardrobe item
   */
  async createWardrobeItem(itemData: FormData): Promise<WardrobeItem> {
    return this.request('/wardrobe/items', {
      method: 'POST',
      body: itemData,
    });
  }

  /**
   * Update wardrobe item
   */
  async updateWardrobeItem(itemId: string, updates: Partial<WardrobeItem>): Promise<WardrobeItem> {
    return this.request(`/wardrobe/items/${itemId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
      headers: { 'Content-Type': 'application/json' },
    });
  }

  /**
   * Delete wardrobe item
   */
  async deleteWardrobeItem(itemId: string): Promise<{ success: boolean }> {
    return this.request(`/wardrobe/items/${itemId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Record item wear
   */
  async recordItemWear(itemId: string): Promise<{ success: boolean; times_worn: number }> {
    return this.request(`/wardrobe/items/${itemId}/wear`, {
      method: 'POST',
    });
  }

  /**
   * Get wardrobe statistics
   */
  async getWardrobeStats(): Promise<WardrobeStats> {
    return this.request('/wardrobe/stats');
  }

  /**
   * Get wardrobe categories and enums
   */
  async getWardrobeCategories(): Promise<{
    categories: string[];
    subcategories: string[];
    styles: string[];
    seasons: string[];
    occasions: string[];
  }> {
    return this.request('/wardrobe/categories');
  }

  // =============================================================================
  // OUTFIT ENDPOINTS
  // =============================================================================

  /**
   * Generate outfit suggestions
   */
  async generateOutfits(request: OutfitGenerationRequest): Promise<OutfitGenerationResponse> {
    return this.request('/outfits/generate', {
      method: 'POST',
      body: JSON.stringify(request),
      headers: { 'Content-Type': 'application/json' },
    });
  }

  /**
   * Create/save outfit
   */
  async createOutfit(outfitData: {
    name: string;
    description?: string;
    style: string[];
    occasion: string[];
    season: string;
    item_ids: string[];
    tags?: string[];
  }): Promise<Outfit> {
    return this.request('/outfits', {
      method: 'POST',
      body: JSON.stringify(outfitData),
      headers: { 'Content-Type': 'application/json' },
    });
  }

  /**
   * Get user outfits
   */
  async getOutfits(filters?: {
    occasion?: string;
    season?: string;
    style?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<Outfit[]> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    const endpoint = params.toString() ? `/outfits?${params}` : '/outfits';
    return this.request(endpoint);
  }

  /**
   * Get single outfit
   */
  async getOutfit(outfitId: string): Promise<Outfit> {
    return this.request(`/outfits/${outfitId}`);
  }

  /**
   * Record outfit wear
   */
  async recordOutfitWear(outfitId: string): Promise<{ success: boolean }> {
    return this.request(`/outfits/${outfitId}/wear`, {
      method: 'POST',
    });
  }

  /**
   * Get daily outfit suggestions
   */
  async getDailyOutfitSuggestions(date?: string, weather?: {
    condition: string;
    temperature: number;
  }): Promise<OutfitSuggestion[]> {
    const params = new URLSearchParams();
    if (date) params.append('date', date);
    if (weather) {
      params.append('weather_condition', weather.condition);
      params.append('temperature', weather.temperature.toString());
    }
    
    const endpoint = params.toString() ? `/outfits/daily/suggestions?${params}` : '/outfits/daily/suggestions';
    return this.request(endpoint);
  }

  // =============================================================================
  // WARDROBE ANALYSIS ENDPOINTS
  // =============================================================================

  /**
   * Analyze wardrobe
   */
  async analyzeWardrobe(analysisType: 'GAPS_ANALYSIS' = 'GAPS_ANALYSIS'): Promise<WardrobeAnalysis> {
    return this.request('/wardrobe/analyze', {
      method: 'POST',
      body: JSON.stringify({ analysis_type: analysisType }),
      headers: { 'Content-Type': 'application/json' },
    });
  }

  /**
   * Get wardrobe insights
   */
  async getWardrobeInsights(type: 'color-palette' | 'versatility' | 'cost-efficiency'): Promise<any> {
    return this.request(`/wardrobe/insights/${type}`);
  }

  // =============================================================================
  // HEALTH CHECK ENDPOINTS
  // =============================================================================

  /**
   * Check API health
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request('/cache/health');
  }

  // =============================================================================
  // PRIVATE METHODS
  // =============================================================================

  /**
   * Make authenticated request to API
   */
  private async request<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    // Prepare headers
    const headers: Record<string, string> = {
      ...options.headers as Record<string, string>,
    };

    // Add auth token if available
    if (this.authToken && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    // Make request
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle response
    if (!response.ok) {
      await this.handleErrorResponse(response);
    }

    // Parse JSON response
    try {
      return await response.json();
    } catch (error) {
      throw new Error('Failed to parse response JSON');
    }
  }

  /**
   * Handle error responses
   */
  private async handleErrorResponse(response: Response): Promise<never> {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    let errorCode: string | undefined;

    try {
      const errorData: ApiError = await response.json();
      errorMessage = errorData.detail || errorMessage;
      errorCode = errorData.error_code;
    } catch {
      // If we can't parse error response, use default message
    }

    // Handle specific error cases
    switch (response.status) {
      case 401:
        // Unauthorized - clear token and redirect to login
        this.clearAuthToken();
        if (errorCode === 'TOKEN_EXPIRED') {
          errorMessage = 'Your session has expired. Please log in again.';
        } else {
          errorMessage = 'Authentication required. Please log in.';
        }
        break;
      
      case 403:
        errorMessage = 'Access denied. You do not have permission to perform this action.';
        break;
      
      case 404:
        errorMessage = 'The requested resource was not found.';
        break;
      
      case 422:
        errorMessage = 'Invalid request data. Please check your input and try again.';
        break;
      
      case 429:
        errorMessage = 'Too many requests. Please wait and try again.';
        break;
      
      case 500:
        errorMessage = 'Server error. Please try again later.';
        break;
    }

    const error = new Error(errorMessage) as Error & { 
      status: number; 
      code?: string;
      response: Response;
    };
    
    error.status = response.status;
    error.code = errorCode;
    error.response = response;
    
    throw error;
  }
}

// =============================================================================
// SINGLETON INSTANCE
// =============================================================================

/**
 * Default API service instance
 */
export const apiService = new SynthiaAPIService();

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Convert File to base64 string
 */
export const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const result = reader.result as string;
      resolve(result.split(',')[1]); // Return only base64 part
    };
    reader.onerror = error => reject(error);
  });
};

/**
 * Check if error is authentication related
 */
export const isAuthError = (error: any): boolean => {
  return error?.status === 401 || error?.status === 403;
};

/**
 * Check if error is network related
 */
export const isNetworkError = (error: any): boolean => {
  return error instanceof TypeError && error.message.includes('fetch');
};

/**
 * Format API error for user display
 */
export const formatErrorMessage = (error: any): string => {
  if (isNetworkError(error)) {
    return 'Network error. Please check your connection and try again.';
  }
  
  if (error?.message) {
    return error.message;
  }
  
  return 'An unexpected error occurred. Please try again.';
};

// =============================================================================
// TYPE EXPORTS
// =============================================================================

export type {
  LoginResponse,
  RegisterRequest,
  LoginRequest,
  ApiError,
};

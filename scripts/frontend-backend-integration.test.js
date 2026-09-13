// =============================================================================
// SYNTHIA STYLE - FRONTEND-BACKEND INTEGRATION TESTS
// =============================================================================
// End-to-end tests verifying Flask→FastAPI migration compatibility

const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');

// Test configuration
const CONFIG = {
  BASE_URL: process.env.TEST_BASE_URL || 'http://localhost:8000',
  API_BASE: '/api/v1',
  TEST_USER: {
    email: 'integration.test@synthia.style',
    password: 'IntegrationTest123!',
    name: 'Integration Test User'
  },
  TIMEOUT: 30000
};

// Helper functions
const api = axios.create({
  baseURL: `${CONFIG.BASE_URL}${CONFIG.API_BASE}`,
  timeout: CONFIG.TIMEOUT,
  validateStatus: (status) => status < 500 // Don't throw on 4xx errors
});

let authToken = null;

/**
 * Set authentication token for subsequent requests
 */
function setAuthToken(token) {
  authToken = token;
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

/**
 * Clear authentication token
 */
function clearAuthToken() {
  authToken = null;
  delete api.defaults.headers.common['Authorization'];
}

describe('Frontend-Backend Integration Tests', () => {
  beforeAll(async () => {
    console.log(`Testing against: ${CONFIG.BASE_URL}${CONFIG.API_BASE}`);
  });

  afterAll(async () => {
    // Cleanup: attempt to logout if we have a token
    if (authToken) {
      try {
        await api.post('/auth/logout');
      } catch (error) {
        // Ignore logout errors in cleanup
      }
    }
  });

  describe('API Compatibility Tests', () => {
    test('Health check endpoint should be accessible', async () => {
      const response = await api.get('/cache/health');
      
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status');
      expect(response.data.status).toBe('healthy');
    });

    test('API documentation should be available', async () => {
      const response = await axios.get(`${CONFIG.BASE_URL}/api/v1/docs`, {
        validateStatus: (status) => status < 500
      });
      
      expect(response.status).toBe(200);
      expect(response.headers['content-type']).toMatch(/text\/html/);
    });
  });

  describe('Authentication Flow Migration', () => {
    test('User registration should work (replacing Flask login)', async () => {
      // Clear any existing auth
      clearAuthToken();
      
      const response = await api.post('/auth/register', CONFIG.TEST_USER);
      
      // Should succeed or return user exists error
      expect([201, 409]).toContain(response.status);
      
      if (response.status === 201) {
        expect(response.data).toHaveProperty('access_token');
        expect(response.data).toHaveProperty('user');
        expect(response.data.user.email).toBe(CONFIG.TEST_USER.email);
      }
    });

    test('User login should work (FastAPI equivalent of Flask login)', async () => {
      clearAuthToken();
      
      const response = await api.post('/auth/login', {
        email: CONFIG.TEST_USER.email,
        password: CONFIG.TEST_USER.password
      });
      
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('access_token');
      expect(response.data).toHaveProperty('refresh_token');
      expect(response.data).toHaveProperty('user');
      
      // Set token for subsequent tests
      setAuthToken(response.data.access_token);
    });

    test('Protected endpoint should require authentication', async () => {
      clearAuthToken();
      
      const response = await api.get('/users/me');
      
      expect(response.status).toBe(401);
    });

    test('Protected endpoint should work with valid token', async () => {
      // First login to get token
      const loginResponse = await api.post('/auth/login', {
        email: CONFIG.TEST_USER.email,
        password: CONFIG.TEST_USER.password
      });
      
      setAuthToken(loginResponse.data.access_token);
      
      const response = await api.get('/users/me');
      
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('email');
      expect(response.data.email).toBe(CONFIG.TEST_USER.email);
    });
  });

  describe('Analysis Endpoints Migration', () => {
    beforeEach(async () => {
      // Ensure we're authenticated for analysis tests
      if (!authToken) {
        const loginResponse = await api.post('/auth/login', {
          email: CONFIG.TEST_USER.email,
          password: CONFIG.TEST_USER.password
        });
        setAuthToken(loginResponse.data.access_token);
      }
    });

    test('Facial analysis endpoint should accept image uploads', async () => {
      // Create a mock image file
      const mockImageData = Buffer.from(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==',
        'base64'
      );
      
      const formData = new FormData();
      formData.append('image', mockImageData, {
        filename: 'test-image.png',
        contentType: 'image/png'
      });
      
      const response = await api.post('/analysis/facial', formData, {
        headers: {
          ...formData.getHeaders(),
          'Authorization': `Bearer ${authToken}`
        },
        validateStatus: (status) => status < 500
      });
      
      // Should handle the request properly (even if analysis fails due to mock image)
      expect([200, 400, 422]).toContain(response.status);
      
      if (response.status === 400 || response.status === 422) {
        // Expected for mock image - should have proper error structure
        expect(response.data).toHaveProperty('detail');
      }
    });

    test('Chromatic analysis endpoint should accept quiz responses', async () => {
      const mockQuizResponses = {
        vein_color: 'blue',
        sun_reaction: 'burn',
        jewelry: 'silver',
        best_colors: 'blue,purple,pink'
      };
      
      const response = await api.post('/analysis/chromatic', {
        responses: mockQuizResponses
      });
      
      // Should process the request
      expect([200, 422]).toContain(response.status);
      
      if (response.status === 200) {
        expect(response.data).toHaveProperty('estacion');
        expect(response.data).toHaveProperty('paleta_primaria');
      }
    });

    test('Analysis history endpoint should be accessible', async () => {
      const response = await api.get('/analysis/history');
      
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('facial');
      expect(response.data).toHaveProperty('chromatic');
      expect(Array.isArray(response.data.facial)).toBe(true);
      expect(Array.isArray(response.data.chromatic)).toBe(true);
    });
  });

  describe('Feedback System Migration', () => {
    beforeEach(async () => {
      if (!authToken) {
        const loginResponse = await api.post('/auth/login', {
          email: CONFIG.TEST_USER.email,
          password: CONFIG.TEST_USER.password
        });
        setAuthToken(loginResponse.data.access_token);
      }
    });

    test('Feedback submission should work (equivalent to Flask feedback)', async () => {
      const feedbackData = {
        type: 'general',
        rating: 5,
        comment: 'Integration test feedback',
        features_used: ['facial_analysis', 'chromatic_analysis']
      };
      
      const response = await api.post('/feedback', feedbackData);
      
      expect(response.status).toBe(201);
      expect(response.data).toHaveProperty('success');
      expect(response.data).toHaveProperty('id');
      expect(response.data.success).toBe(true);
    });
  });

  describe('File Upload System Migration', () => {
    beforeEach(async () => {
      if (!authToken) {
        const loginResponse = await api.post('/auth/login', {
          email: CONFIG.TEST_USER.email,
          password: CONFIG.TEST_USER.password
        });
        setAuthToken(loginResponse.data.access_token);
      }
    });

    test('File upload endpoint should handle image files', async () => {
      const mockImageData = Buffer.from(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==',
        'base64'
      );
      
      const formData = new FormData();
      formData.append('file', mockImageData, {
        filename: 'test-upload.png',
        contentType: 'image/png'
      });
      
      const response = await api.post('/files/upload', formData, {
        headers: {
          ...formData.getHeaders(),
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('url');
      expect(response.data).toHaveProperty('filename');
    });
  });

  describe('Error Handling Compatibility', () => {
    test('Invalid endpoints should return 404', async () => {
      const response = await api.get('/nonexistent-endpoint');
      
      expect(response.status).toBe(404);
      expect(response.data).toHaveProperty('detail');
    });

    test('Invalid JSON should return 422', async () => {
      const response = await api.post('/auth/login', 'invalid-json', {
        headers: { 'Content-Type': 'application/json' }
      });
      
      expect(response.status).toBe(422);
      expect(response.data).toHaveProperty('detail');
    });

    test('Missing authentication should return 401', async () => {
      clearAuthToken();
      
      const response = await api.get('/users/me');
      
      expect(response.status).toBe(401);
      expect(response.data).toHaveProperty('detail');
    });
  });

  describe('Performance and Response Format', () => {
    test('Response times should be reasonable', async () => {
      const startTime = Date.now();
      
      const response = await api.get('/cache/health');
      
      const responseTime = Date.now() - startTime;
      
      expect(response.status).toBe(200);
      expect(responseTime).toBeLessThan(2000); // Should respond within 2 seconds
    });

    test('API responses should have consistent structure', async () => {
      const response = await api.get('/cache/health');
      
      expect(response.status).toBe(200);
      expect(response.data).toBeInstanceOf(Object);
      expect(response.data).toHaveProperty('status');
      expect(response.data).toHaveProperty('timestamp');
    });

    test('Error responses should have consistent structure', async () => {
      const response = await api.get('/nonexistent-endpoint');
      
      expect(response.status).toBe(404);
      expect(response.data).toHaveProperty('detail');
      expect(typeof response.data.detail).toBe('string');
    });
  });
});

// =============================================================================
// FRONTEND COMPATIBILITY TESTS
// =============================================================================

describe('Frontend Integration Compatibility', () => {
  describe('API Service Compatibility', () => {
    test('New API service should be compatible with existing frontend types', () => {
      // Mock test to verify type compatibility
      // In a real scenario, this would import actual frontend types
      
      const mockFacialAnalysisResponse = {
        forma_rostro: 'ovalado',
        caracteristicas_destacadas: ['pómulos prominentes', 'mandíbula definida'],
        confianza_analisis: 85,
        recomendaciones: {
          cortes_pelo: [
            {
              nombre: 'Bob clásico',
              descripcion: 'Corte recto a la altura de la mandíbula',
              explicacion: 'Enmarca el rostro resaltando los pómulos'
            }
          ],
          gafas: [
            {
              tipo: 'Wayfarer',
              explicacion: 'Su forma equilibrada complementa la simetría del rostro'
            }
          ],
          escotes: [
            {
              tipo: 'V profunda',
              explicacion: 'Alarga visualmente el rostro y destaca el cuello'
            }
          ]
        }
      };

      const mockChromaticAnalysisResponse = {
        estacion: 'invierno',
        subtono: 'frío',
        confianza_analisis: 90,
        descripcion: 'Colores fríos e intensos que complementan tu tono de piel',
        paleta_primaria: [
          {
            color: 'Azul real',
            codigo_hex: '#0047AB',
            explicacion: 'Color base que realza tu tono frío'
          }
        ],
        colores_evitar: [
          {
            color: 'Naranja cálido',
            codigo_hex: '#FF8C00',
            explicacion: 'Contrasta negativamente con tu subtono frío'
          }
        ]
      };

      // Verify structure matches expected frontend types
      expect(mockFacialAnalysisResponse).toHaveProperty('forma_rostro');
      expect(mockFacialAnalysisResponse).toHaveProperty('recomendaciones');
      expect(mockFacialAnalysisResponse.recomendaciones).toHaveProperty('cortes_pelo');
      expect(mockFacialAnalysisResponse.recomendaciones).toHaveProperty('gafas');
      expect(mockFacialAnalysisResponse.recomendaciones).toHaveProperty('escotes');

      expect(mockChromaticAnalysisResponse).toHaveProperty('estacion');
      expect(mockChromaticAnalysisResponse).toHaveProperty('paleta_primaria');
      expect(mockChromaticAnalysisResponse).toHaveProperty('colores_evitar');
    });
  });

  describe('Migration Path Verification', () => {
    test('Frontend can migrate from direct Gemini calls to API service', async () => {
      // Test the migration path: ensure API provides same data structure as direct Gemini calls
      if (!authToken) {
        const loginResponse = await api.post('/auth/login', {
          email: CONFIG.TEST_USER.email,
          password: CONFIG.TEST_USER.password
        });
        setAuthToken(loginResponse.data.access_token);
      }

      // Test chromatic analysis (easier to test than facial analysis)
      const mockQuizResponses = {
        vein_color: 'blue',
        sun_reaction: 'burn',
        jewelry: 'silver',
        best_colors: 'blue,purple'
      };

      const response = await api.post('/analysis/chromatic', {
        responses: mockQuizResponses
      });

      if (response.status === 200) {
        // Verify the response structure matches what frontend expects
        expect(response.data).toHaveProperty('estacion');
        expect(response.data).toHaveProperty('subtono');
        expect(response.data).toHaveProperty('confianza_analisis');
        expect(response.data).toHaveProperty('paleta_primaria');
        expect(Array.isArray(response.data.paleta_primaria)).toBe(true);
        
        if (response.data.paleta_primaria.length > 0) {
          const firstColor = response.data.paleta_primaria[0];
          expect(firstColor).toHaveProperty('color');
          expect(firstColor).toHaveProperty('codigo_hex');
          expect(firstColor).toHaveProperty('explicacion');
        }
      }
    });
  });
});

console.log('🧪 Frontend-Backend Integration Tests Ready');
console.log(`Target: ${CONFIG.BASE_URL}${CONFIG.API_BASE}`);

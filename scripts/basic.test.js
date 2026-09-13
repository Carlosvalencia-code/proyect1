// =============================================================================
// SYNTHIA STYLE - SMOKE TESTS
// =============================================================================
// Basic smoke tests to verify deployment success

const axios = require('axios');

// Test configuration
const getBaseUrl = () => {
  switch (process.env.TEST_ENV) {
    case 'development':
      return 'https://dev.synthia.style';
    case 'staging':
      return 'https://staging.synthia.style';
    case 'production':
      return 'https://synthia.style';
    default:
      return process.env.TEST_BASE_URL || 'https://staging.synthia.style';
  }
};

const BASE_URL = getBaseUrl();
const API_TIMEOUT = 15000;

describe('Synthia Style Smoke Tests', () => {
  beforeAll(() => {
    console.log(`Running smoke tests against: ${BASE_URL}`);
  });

  describe('Frontend Availability', () => {
    test('Homepage should be accessible', async () => {
      const response = await axios.get(BASE_URL, {
        timeout: API_TIMEOUT,
        validateStatus: (status) => status < 500, // Don't throw on 4xx
      });
      
      expect(response.status).toBe(200);
      expect(response.headers['content-type']).toMatch(/text\/html/);
    });

    test('Homepage should contain expected content', async () => {
      const response = await axios.get(BASE_URL, {
        timeout: API_TIMEOUT,
      });
      
      expect(response.data).toContain('Synthia Style');
      // Add more content checks as needed
    });
  });

  describe('API Health', () => {
    test('Health endpoint should respond', async () => {
      const response = await axios.get(`${BASE_URL}/api/v1/cache/health`, {
        timeout: API_TIMEOUT,
      });
      
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status');
    });

    test('API documentation should be accessible', async () => {
      const response = await axios.get(`${BASE_URL}/api/v1/docs`, {
        timeout: API_TIMEOUT,
        validateStatus: (status) => status < 500,
      });
      
      expect(response.status).toBe(200);
    });
  });

  describe('Security Headers', () => {
    test('Should have security headers', async () => {
      const response = await axios.get(BASE_URL, {
        timeout: API_TIMEOUT,
      });
      
      // Check for security headers
      expect(response.headers).toHaveProperty('x-frame-options');
      expect(response.headers).toHaveProperty('x-content-type-options');
      
      // Check HSTS for HTTPS
      if (BASE_URL.startsWith('https://')) {
        expect(response.headers).toHaveProperty('strict-transport-security');
      }
    });
  });

  describe('API Endpoints', () => {
    test('Auth endpoints should be accessible', async () => {
      // Test registration endpoint (should return validation error for empty body)
      const response = await axios.post(`${BASE_URL}/api/v1/auth/register`, {}, {
        timeout: API_TIMEOUT,
        validateStatus: (status) => status < 500,
      });
      
      // Should return 422 (validation error) or similar, not 500
      expect(response.status).toBeLessThan(500);
    });

    test('Analysis endpoints should be accessible', async () => {
      // Test facial analysis endpoint (should return auth error for no token)
      const response = await axios.post(`${BASE_URL}/api/v1/analysis/facial`, {}, {
        timeout: API_TIMEOUT,
        validateStatus: (status) => status < 500,
      });
      
      // Should return 401 (unauthorized) or 422 (validation error), not 500
      expect([401, 422]).toContain(response.status);
    });
  });

  describe('Performance', () => {
    test('Homepage should load within acceptable time', async () => {
      const startTime = Date.now();
      
      await axios.get(BASE_URL, {
        timeout: API_TIMEOUT,
      });
      
      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(5000); // Should load within 5 seconds
    });

    test('API health check should be fast', async () => {
      const startTime = Date.now();
      
      await axios.get(`${BASE_URL}/api/v1/cache/health`, {
        timeout: API_TIMEOUT,
      });
      
      const responseTime = Date.now() - startTime;
      expect(responseTime).toBeLessThan(2000); // Should respond within 2 seconds
    });
  });

  describe('SSL/TLS Configuration', () => {
    test('HTTPS should be properly configured', async () => {
      if (!BASE_URL.startsWith('https://')) {
        console.log('Skipping HTTPS test for non-HTTPS URL');
        return;
      }

      const response = await axios.get(BASE_URL, {
        timeout: API_TIMEOUT,
      });
      
      expect(response.status).toBe(200);
      // If we got here without SSL errors, the certificate is valid
    });
  });
});

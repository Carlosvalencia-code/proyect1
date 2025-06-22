// =============================================================================
// SYNTHIA STYLE - LOAD TESTING SCRIPT
// =============================================================================
// K6 load testing script for general API and frontend performance

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const responseTime = new Trend('response_time');
const requestCount = new Counter('request_count');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up
    { duration: '5m', target: 50 }, // Stay at 50 users
    { duration: '2m', target: 100 }, // Ramp up to 100 users
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests under 2s
    http_req_failed: ['rate<0.1'],     // Error rate under 10%
    error_rate: ['rate<0.05'],         // Custom error rate under 5%
  },
};

// Test data
const BASE_URL = __ENV.TARGET_URL || 'https://staging.synthia.style';

const testUsers = [
  { email: 'test1@synthia.style', password: 'TestPassword123!' },
  { email: 'test2@synthia.style', password: 'TestPassword123!' },
  { email: 'test3@synthia.style', password: 'TestPassword123!' },
];

// Helper functions
function getRandomUser() {
  return testUsers[Math.floor(Math.random() * testUsers.length)];
}

function makeAuthenticatedRequest(url, params = {}) {
  // In a real scenario, you'd handle authentication
  return http.get(url, params);
}

// Main test function
export default function () {
  const user = getRandomUser();
  
  // Test scenario: User journey
  testHomePage();
  sleep(1);
  
  testAPIHealth();
  sleep(1);
  
  testUserRegistration();
  sleep(2);
  
  testFacialAnalysis();
  sleep(3);
  
  testChromaticAnalysis();
  sleep(2);
}

function testHomePage() {
  const response = http.get(`${BASE_URL}/`);
  
  const success = check(response, {
    'homepage status is 200': (r) => r.status === 200,
    'homepage loads in reasonable time': (r) => r.timings.duration < 3000,
  });
  
  errorRate.add(!success);
  responseTime.add(response.timings.duration);
  requestCount.add(1);
}

function testAPIHealth() {
  const response = http.get(`${BASE_URL}/api/v1/cache/health`);
  
  const success = check(response, {
    'health endpoint status is 200': (r) => r.status === 200,
    'health endpoint response is valid': (r) => {
      try {
        const data = JSON.parse(r.body);
        return data.status === 'healthy';
      } catch (e) {
        return false;
      }
    },
  });
  
  errorRate.add(!success);
  responseTime.add(response.timings.duration);
  requestCount.add(1);
}

function testUserRegistration() {
  const timestamp = Date.now();
  const testUser = {
    email: `loadtest${timestamp}@synthia.style`,
    password: 'LoadTest123!',
    name: `Load Test User ${timestamp}`,
  };
  
  const response = http.post(
    `${BASE_URL}/api/v1/auth/register`,
    JSON.stringify(testUser),
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );
  
  const success = check(response, {
    'registration status is 201 or 409': (r) => r.status === 201 || r.status === 409,
    'registration response time < 5s': (r) => r.timings.duration < 5000,
  });
  
  errorRate.add(!success);
  responseTime.add(response.timings.duration);
  requestCount.add(1);
}

function testFacialAnalysis() {
  // Simulate facial analysis request
  const mockImageData = 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...'; // Mock base64 image
  
  const response = http.post(
    `${BASE_URL}/api/v1/analysis/facial`,
    JSON.stringify({
      image: mockImageData,
      preferences: {
        detailed: true,
        includeRecommendations: true,
      },
    }),
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer mock-token', // In real test, use actual token
      },
    }
  );
  
  const success = check(response, {
    'facial analysis status is 200 or 401': (r) => r.status === 200 || r.status === 401,
    'facial analysis response time < 10s': (r) => r.timings.duration < 10000,
  });
  
  errorRate.add(!success);
  responseTime.add(response.timings.duration);
  requestCount.add(1);
}

function testChromaticAnalysis() {
  const response = http.post(
    `${BASE_URL}/api/v1/analysis/chromatic`,
    JSON.stringify({
      responses: {
        question1: 'warm',
        question2: 'gold',
        question3: 'brown',
        question4: 'coral',
        question5: 'autumn',
      },
    }),
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer mock-token',
      },
    }
  );
  
  const success = check(response, {
    'chromatic analysis status is 200 or 401': (r) => r.status === 200 || r.status === 401,
    'chromatic analysis response time < 3s': (r) => r.timings.duration < 3000,
  });
  
  errorRate.add(!success);
  responseTime.add(response.timings.duration);
  requestCount.add(1);
}

// Setup function (runs once per VU)
export function setup() {
  console.log('Starting load test...');
  console.log(`Target URL: ${BASE_URL}`);
  console.log(`Test duration: ${options.stages.reduce((total, stage) => total + parseInt(stage.duration), 0)} minutes`);
  
  // Verify target is accessible
  const healthCheck = http.get(`${BASE_URL}/api/v1/cache/health`);
  if (healthCheck.status !== 200) {
    throw new Error(`Target ${BASE_URL} is not accessible. Health check failed with status ${healthCheck.status}`);
  }
  
  return { baseUrl: BASE_URL };
}

// Teardown function (runs once after all VUs finish)
export function teardown(data) {
  console.log('Load test completed');
  console.log(`Target URL: ${data.baseUrl}`);
}

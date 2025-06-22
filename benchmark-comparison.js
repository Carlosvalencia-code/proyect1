#!/usr/bin/env node

// =============================================================================
// SYNTHIA STYLE - FLASK vs FASTAPI PERFORMANCE BENCHMARK
// =============================================================================
// Comprehensive performance comparison between Flask and FastAPI implementations

const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');

/**
 * Performance benchmark configuration
 */
const BENCHMARK_CONFIG = {
  // Test endpoints
  endpoints: {
    flask: {
      health: 'http://localhost:5000/',
      facial_analysis: 'http://localhost:5000/facial-analysis',
      color_analysis: 'http://localhost:5000/color-analysis',
      login: 'http://localhost:5000/login',
    },
    fastapi: {
      health: 'http://localhost:8000/api/v1/cache/health',
      facial_analysis: 'http://localhost:8000/api/v1/analysis/facial',
      color_analysis: 'http://localhost:8000/api/v1/analysis/chromatic',
      login: 'http://localhost:8000/api/v1/auth/login',
    }
  },
  
  // Test parameters
  concurrency: [1, 5, 10, 25, 50],
  duration: 30, // seconds per test
  warmupRequests: 10,
  
  // Test data
  testUser: {
    email: 'benchmark@synthia.style',
    password: 'BenchmarkPassword123!',
    name: 'Benchmark User'
  },
  
  chromaticResponses: {
    vein_color: 'blue',
    sun_reaction: 'burn',
    jewelry: 'silver',
    best_colors: ['blue', 'purple', 'pink']
  }
};

/**
 * Benchmark results storage
 */
class BenchmarkResults {
  constructor() {
    this.results = {
      flask: {},
      fastapi: {},
      comparison: {},
      metadata: {
        timestamp: new Date().toISOString(),
        config: BENCHMARK_CONFIG,
        system: this.getSystemInfo()
      }
    };
  }

  getSystemInfo() {
    const os = require('os');
    return {
      platform: os.platform(),
      arch: os.arch(),
      cpus: os.cpus().length,
      memory: Math.round(os.totalmem() / 1024 / 1024 / 1024) + ' GB',
      node_version: process.version
    };
  }

  addResult(framework, endpoint, concurrency, stats) {
    if (!this.results[framework][endpoint]) {
      this.results[framework][endpoint] = {};
    }
    this.results[framework][endpoint][`c${concurrency}`] = stats;
  }

  generateComparison() {
    const comparison = {};
    
    for (const endpoint of Object.keys(BENCHMARK_CONFIG.endpoints.flask)) {
      comparison[endpoint] = {};
      
      for (const concurrency of BENCHMARK_CONFIG.concurrency) {
        const flaskStats = this.results.flask[endpoint]?.[`c${concurrency}`];
        const fastapiStats = this.results.fastapi[endpoint]?.[`c${concurrency}`];
        
        if (flaskStats && fastapiStats) {
          comparison[endpoint][`c${concurrency}`] = {
            response_time_improvement: this.calculateImprovement(
              flaskStats.avg_response_time,
              fastapiStats.avg_response_time
            ),
            throughput_improvement: this.calculateImprovement(
              fastapiStats.requests_per_second,
              flaskStats.requests_per_second
            ),
            error_rate_change: fastapiStats.error_rate - flaskStats.error_rate,
            p95_improvement: this.calculateImprovement(
              flaskStats.p95_response_time,
              fastapiStats.p95_response_time
            )
          };
        }
      }
    }
    
    this.results.comparison = comparison;
  }

  calculateImprovement(oldValue, newValue) {
    if (oldValue === 0) return newValue === 0 ? 0 : Infinity;
    return ((oldValue - newValue) / oldValue) * 100;
  }

  saveResults() {
    const filename = `benchmark-results-${Date.now()}.json`;
    const filepath = path.join(__dirname, 'results', filename);
    
    // Ensure results directory exists
    const resultsDir = path.dirname(filepath);
    if (!fs.existsSync(resultsDir)) {
      fs.mkdirSync(resultsDir, { recursive: true });
    }
    
    fs.writeFileSync(filepath, JSON.stringify(this.results, null, 2));
    console.log(`\n📊 Results saved to: ${filepath}`);
    
    return filepath;
  }
}

/**
 * HTTP request utility
 */
function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    const urlObj = new URL(url);
    const isHttps = urlObj.protocol === 'https:';
    const client = isHttps ? https : http;
    
    const requestOptions = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      headers: options.headers || {},
      timeout: 30000 // 30 second timeout
    };

    const req = client.request(requestOptions, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        const endTime = Date.now();
        resolve({
          statusCode: res.statusCode,
          responseTime: endTime - startTime,
          data: data,
          success: res.statusCode >= 200 && res.statusCode < 400
        });
      });
    });

    req.on('error', (error) => {
      const endTime = Date.now();
      reject({
        error: error.message,
        responseTime: endTime - startTime,
        success: false
      });
    });

    req.on('timeout', () => {
      req.destroy();
      const endTime = Date.now();
      reject({
        error: 'Request timeout',
        responseTime: endTime - startTime,
        success: false
      });
    });

    if (options.body) {
      req.write(options.body);
    }

    req.end();
  });
}

/**
 * Run load test for specific endpoint
 */
async function runLoadTest(url, options, concurrency, duration) {
  console.log(`  Running load test: ${concurrency} concurrent users for ${duration}s`);
  
  const results = [];
  const startTime = Date.now();
  const endTime = startTime + (duration * 1000);
  
  // Function to make a single request
  const makeRequestWithRetry = async () => {
    try {
      const result = await makeRequest(url, options);
      results.push(result);
    } catch (error) {
      results.push(error);
    }
  };

  // Start concurrent workers
  const workers = [];
  for (let i = 0; i < concurrency; i++) {
    workers.push(runWorker(makeRequestWithRetry, endTime));
  }

  // Wait for all workers to complete
  await Promise.all(workers);

  // Calculate statistics
  return calculateStats(results, Date.now() - startTime);
}

/**
 * Worker function for load testing
 */
async function runWorker(requestFunction, endTime) {
  while (Date.now() < endTime) {
    await requestFunction();
    // Small delay to prevent overwhelming
    await new Promise(resolve => setTimeout(resolve, 10));
  }
}

/**
 * Calculate performance statistics
 */
function calculateStats(results, totalDuration) {
  const successful = results.filter(r => r.success);
  const failed = results.filter(r => !r.success);
  const responseTimes = successful.map(r => r.responseTime);
  
  if (responseTimes.length === 0) {
    return {
      total_requests: results.length,
      successful_requests: 0,
      failed_requests: results.length,
      error_rate: 100,
      requests_per_second: 0,
      avg_response_time: 0,
      min_response_time: 0,
      max_response_time: 0,
      p95_response_time: 0,
      p99_response_time: 0
    };
  }

  responseTimes.sort((a, b) => a - b);
  
  return {
    total_requests: results.length,
    successful_requests: successful.length,
    failed_requests: failed.length,
    error_rate: (failed.length / results.length) * 100,
    requests_per_second: successful.length / (totalDuration / 1000),
    avg_response_time: responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length,
    min_response_time: responseTimes[0],
    max_response_time: responseTimes[responseTimes.length - 1],
    p95_response_time: responseTimes[Math.floor(responseTimes.length * 0.95)],
    p99_response_time: responseTimes[Math.floor(responseTimes.length * 0.99)]
  };
}

/**
 * Test health endpoint
 */
async function testHealthEndpoint(framework, url) {
  console.log(`\n🔍 Testing ${framework.toUpperCase()} health endpoint...`);
  
  try {
    const result = await makeRequest(url);
    if (result.success) {
      console.log(`  ✅ ${framework} server is responsive (${result.responseTime}ms)`);
      return true;
    } else {
      console.log(`  ❌ ${framework} server returned status ${result.statusCode}`);
      return false;
    }
  } catch (error) {
    console.log(`  ❌ ${framework} server is not accessible: ${error.error || error.message}`);
    return false;
  }
}

/**
 * Benchmark health endpoint
 */
async function benchmarkHealth(framework, url, results) {
  console.log(`\n📊 Benchmarking ${framework.toUpperCase()} health endpoint...`);
  
  for (const concurrency of BENCHMARK_CONFIG.concurrency) {
    const stats = await runLoadTest(url, {}, concurrency, BENCHMARK_CONFIG.duration);
    results.addResult(framework, 'health', concurrency, stats);
    
    console.log(`  Concurrency ${concurrency}: ${stats.requests_per_second.toFixed(1)} req/s, ` +
                `${stats.avg_response_time.toFixed(1)}ms avg, ${stats.error_rate.toFixed(1)}% errors`);
  }
}

/**
 * Benchmark authentication endpoint
 */
async function benchmarkAuth(framework, url, results) {
  console.log(`\n🔐 Benchmarking ${framework.toUpperCase()} auth endpoint...`);
  
  const authData = framework === 'flask' 
    ? `email=${BENCHMARK_CONFIG.testUser.email}&password=${BENCHMARK_CONFIG.testUser.password}`
    : JSON.stringify({
        email: BENCHMARK_CONFIG.testUser.email,
        password: BENCHMARK_CONFIG.testUser.password
      });

  const options = {
    method: 'POST',
    headers: framework === 'flask' 
      ? { 'Content-Type': 'application/x-www-form-urlencoded' }
      : { 'Content-Type': 'application/json' },
    body: authData
  };

  for (const concurrency of BENCHMARK_CONFIG.concurrency) {
    const stats = await runLoadTest(url, options, concurrency, BENCHMARK_CONFIG.duration);
    results.addResult(framework, 'login', concurrency, stats);
    
    console.log(`  Concurrency ${concurrency}: ${stats.requests_per_second.toFixed(1)} req/s, ` +
                `${stats.avg_response_time.toFixed(1)}ms avg, ${stats.error_rate.toFixed(1)}% errors`);
  }
}

/**
 * Generate performance report
 */
function generateReport(results) {
  console.log('\n' + '='.repeat(80));
  console.log('📊 FLASK vs FASTAPI PERFORMANCE COMPARISON REPORT');
  console.log('='.repeat(80));

  // Summary table
  console.log('\n📈 PERFORMANCE SUMMARY (25 concurrent users)');
  console.log('-'.repeat(80));
  console.log('Endpoint'.padEnd(20) + 'Flask RPS'.padEnd(12) + 'FastAPI RPS'.padEnd(14) + 'Improvement'.padEnd(12) + 'Response Time');
  console.log('-'.repeat(80));

  for (const endpoint of ['health', 'login']) {
    const flaskStats = results.results.flask[endpoint]?.c25;
    const fastapiStats = results.results.fastapi[endpoint]?.c25;
    
    if (flaskStats && fastapiStats) {
      const rpsImprovement = ((fastapiStats.requests_per_second - flaskStats.requests_per_second) / flaskStats.requests_per_second * 100).toFixed(1);
      const rtImprovement = ((flaskStats.avg_response_time - fastapiStats.avg_response_time) / flaskStats.avg_response_time * 100).toFixed(1);
      
      console.log(
        endpoint.padEnd(20) +
        flaskStats.requests_per_second.toFixed(1).padEnd(12) +
        fastapiStats.requests_per_second.toFixed(1).padEnd(14) +
        `+${rpsImprovement}%`.padEnd(12) +
        `${rtImprovement}% faster`
      );
    }
  }

  // Detailed comparison
  console.log('\n🔍 DETAILED COMPARISON');
  console.log('-'.repeat(80));

  for (const endpoint of Object.keys(results.results.comparison)) {
    if (Object.keys(results.results.comparison[endpoint]).length > 0) {
      console.log(`\n${endpoint.toUpperCase()} ENDPOINT:`);
      
      for (const concurrency of ['c1', 'c5', 'c10', 'c25', 'c50']) {
        const comp = results.results.comparison[endpoint][concurrency];
        if (comp) {
          console.log(`  ${concurrency.replace('c', '')} users: ` +
                     `${comp.response_time_improvement.toFixed(1)}% faster response, ` +
                     `${comp.throughput_improvement.toFixed(1)}% more throughput`);
        }
      }
    }
  }

  // System information
  console.log('\n💻 SYSTEM INFORMATION');
  console.log('-'.repeat(40));
  const sys = results.results.metadata.system;
  console.log(`Platform: ${sys.platform} ${sys.arch}`);
  console.log(`CPUs: ${sys.cpus}`);
  console.log(`Memory: ${sys.memory}`);
  console.log(`Node.js: ${sys.node_version}`);

  console.log('\n✅ Benchmark completed successfully!');
}

/**
 * Main benchmark execution
 */
async function runBenchmark() {
  console.log('🚀 Starting Flask vs FastAPI Performance Benchmark');
  console.log('=' .repeat(60));

  const results = new BenchmarkResults();

  // Check server availability
  console.log('\n🔍 Checking server availability...');
  
  const flaskAvailable = await testHealthEndpoint('flask', BENCHMARK_CONFIG.endpoints.flask.health);
  const fastapiAvailable = await testHealthEndpoint('fastapi', BENCHMARK_CONFIG.endpoints.fastapi.health);

  if (!flaskAvailable && !fastapiAvailable) {
    console.log('\n❌ Neither Flask nor FastAPI servers are available.');
    console.log('Please start the servers before running the benchmark.');
    process.exit(1);
  }

  if (!flaskAvailable) {
    console.log('\n⚠️  Flask server is not available. Skipping Flask benchmarks.');
  }

  if (!fastapiAvailable) {
    console.log('\n⚠️  FastAPI server is not available. Skipping FastAPI benchmarks.');
  }

  // Run benchmarks
  if (flaskAvailable) {
    await benchmarkHealth('flask', BENCHMARK_CONFIG.endpoints.flask.health, results);
    await benchmarkAuth('flask', BENCHMARK_CONFIG.endpoints.flask.login, results);
  }

  if (fastapiAvailable) {
    await benchmarkHealth('fastapi', BENCHMARK_CONFIG.endpoints.fastapi.health, results);
    await benchmarkAuth('fastapi', BENCHMARK_CONFIG.endpoints.fastapi.login, results);
  }

  // Generate comparison and report
  if (flaskAvailable && fastapiAvailable) {
    results.generateComparison();
    generateReport(results);
  } else {
    console.log('\n⚠️  Cannot generate comparison - both servers need to be available.');
  }

  // Save results
  results.saveResults();
}

// =============================================================================
// EXECUTION
// =============================================================================

if (require.main === module) {
  runBenchmark().catch(error => {
    console.error('\n❌ Benchmark failed:', error.message);
    process.exit(1);
  });
}

module.exports = {
  runBenchmark,
  BenchmarkResults,
  BENCHMARK_CONFIG
};

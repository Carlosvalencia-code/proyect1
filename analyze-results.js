#!/usr/bin/env node

// =============================================================================
// SYNTHIA STYLE - PERFORMANCE RESULTS ANALYZER
// =============================================================================
// Analyzes K6 performance test results and generates comprehensive reports

const fs = require('fs');
const path = require('path');

/**
 * Analyze K6 performance test results
 * @param {string} resultsFile - Path to K6 JSON results file
 */
function analyzeResults(resultsFile) {
  if (!fs.existsSync(resultsFile)) {
    console.error(`Results file not found: ${resultsFile}`);
    process.exit(1);
  }

  try {
    const rawData = fs.readFileSync(resultsFile, 'utf8');
    const lines = rawData.trim().split('\n');
    const metrics = [];
    
    // Parse NDJSON format from K6
    lines.forEach(line => {
      try {
        const data = JSON.parse(line);
        if (data.type === 'Point') {
          metrics.push(data);
        }
      } catch (e) {
        // Skip invalid JSON lines
      }
    });

    if (metrics.length === 0) {
      console.log('No metrics found in results file');
      return;
    }

    const analysis = generateAnalysis(metrics);
    generateReport(analysis);
    
  } catch (error) {
    console.error('Error analyzing results:', error.message);
    process.exit(1);
  }
}

/**
 * Generate performance analysis from metrics
 * @param {Array} metrics - Array of K6 metric points
 * @returns {Object} Analysis results
 */
function generateAnalysis(metrics) {
  const httpReqDuration = [];
  const httpReqFailed = [];
  const httpReqs = [];
  const vus = [];
  
  metrics.forEach(metric => {
    switch (metric.metric) {
      case 'http_req_duration':
        httpReqDuration.push(metric.data.value);
        break;
      case 'http_req_failed':
        httpReqFailed.push(metric.data.value);
        break;
      case 'http_reqs':
        httpReqs.push(metric.data.value);
        break;
      case 'vus':
        vus.push(metric.data.value);
        break;
    }
  });

  // Calculate statistics
  const analysis = {
    summary: {
      totalRequests: httpReqs.reduce((sum, val) => sum + val, 0),
      totalFailures: httpReqFailed.reduce((sum, val) => sum + val, 0),
      maxVUs: Math.max(...vus, 0),
      testDuration: calculateTestDuration(metrics),
    },
    responseTime: {
      min: Math.min(...httpReqDuration),
      max: Math.max(...httpReqDuration),
      avg: average(httpReqDuration),
      p95: percentile(httpReqDuration, 95),
      p99: percentile(httpReqDuration, 99),
    },
    errorRate: {
      total: httpReqFailed.reduce((sum, val) => sum + val, 0),
      percentage: (httpReqFailed.reduce((sum, val) => sum + val, 0) / httpReqs.reduce((sum, val) => sum + val, 0)) * 100 || 0,
    },
    throughput: {
      requestsPerSecond: httpReqs.reduce((sum, val) => sum + val, 0) / (calculateTestDuration(metrics) / 1000),
    },
  };

  return analysis;
}

/**
 * Calculate test duration from metrics
 * @param {Array} metrics - Array of metrics
 * @returns {number} Duration in milliseconds
 */
function calculateTestDuration(metrics) {
  if (metrics.length === 0) return 0;
  
  const timestamps = metrics.map(m => new Date(m.data.time).getTime());
  return Math.max(...timestamps) - Math.min(...timestamps);
}

/**
 * Calculate average of array
 * @param {Array} arr - Array of numbers
 * @returns {number} Average
 */
function average(arr) {
  if (arr.length === 0) return 0;
  return arr.reduce((sum, val) => sum + val, 0) / arr.length;
}

/**
 * Calculate percentile of array
 * @param {Array} arr - Array of numbers
 * @param {number} p - Percentile (0-100)
 * @returns {number} Percentile value
 */
function percentile(arr, p) {
  if (arr.length === 0) return 0;
  
  const sorted = arr.slice().sort((a, b) => a - b);
  const index = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[index] || 0;
}

/**
 * Generate performance report
 * @param {Object} analysis - Analysis results
 */
function generateReport(analysis) {
  const report = `
### 📊 Performance Test Results

#### 📈 Summary
- **Total Requests**: ${analysis.summary.totalRequests.toLocaleString()}
- **Failed Requests**: ${analysis.summary.totalFailures.toLocaleString()}
- **Error Rate**: ${analysis.errorRate.percentage.toFixed(2)}%
- **Max Virtual Users**: ${analysis.summary.maxVUs}
- **Test Duration**: ${(analysis.summary.testDuration / 1000 / 60).toFixed(1)} minutes
- **Throughput**: ${analysis.throughput.requestsPerSecond.toFixed(2)} requests/second

#### ⏱️ Response Time Statistics
- **Average**: ${analysis.responseTime.avg.toFixed(2)}ms
- **Minimum**: ${analysis.responseTime.min.toFixed(2)}ms
- **Maximum**: ${analysis.responseTime.max.toFixed(2)}ms
- **95th Percentile**: ${analysis.responseTime.p95.toFixed(2)}ms
- **99th Percentile**: ${analysis.responseTime.p99.toFixed(2)}ms

#### ✅ Performance Assessment
${generateAssessment(analysis)}

#### 📊 Recommendations
${generateRecommendations(analysis)}
`;

  console.log(report);
}

/**
 * Generate performance assessment
 * @param {Object} analysis - Analysis results
 * @returns {string} Assessment text
 */
function generateAssessment(analysis) {
  const assessments = [];

  // Response time assessment
  if (analysis.responseTime.p95 < 1000) {
    assessments.push('✅ **Excellent response times** - 95th percentile under 1 second');
  } else if (analysis.responseTime.p95 < 2000) {
    assessments.push('⚠️ **Good response times** - 95th percentile under 2 seconds');
  } else {
    assessments.push('❌ **Poor response times** - 95th percentile over 2 seconds');
  }

  // Error rate assessment
  if (analysis.errorRate.percentage < 1) {
    assessments.push('✅ **Excellent reliability** - Error rate under 1%');
  } else if (analysis.errorRate.percentage < 5) {
    assessments.push('⚠️ **Good reliability** - Error rate under 5%');
  } else {
    assessments.push('❌ **Poor reliability** - Error rate over 5%');
  }

  // Throughput assessment
  if (analysis.throughput.requestsPerSecond > 100) {
    assessments.push('✅ **High throughput** - Over 100 requests/second');
  } else if (analysis.throughput.requestsPerSecond > 50) {
    assessments.push('⚠️ **Moderate throughput** - 50-100 requests/second');
  } else {
    assessments.push('❌ **Low throughput** - Under 50 requests/second');
  }

  return assessments.join('\n');
}

/**
 * Generate performance recommendations
 * @param {Object} analysis - Analysis results
 * @returns {string} Recommendations text
 */
function generateRecommendations(analysis) {
  const recommendations = [];

  if (analysis.responseTime.p95 > 2000) {
    recommendations.push('🔧 **Optimize response times** - Consider caching, database optimization, or CDN implementation');
  }

  if (analysis.errorRate.percentage > 5) {
    recommendations.push('🔧 **Reduce error rate** - Investigate failing requests and improve error handling');
  }

  if (analysis.throughput.requestsPerSecond < 50) {
    recommendations.push('🔧 **Improve throughput** - Consider scaling resources or optimizing application performance');
  }

  if (analysis.responseTime.max > 10000) {
    recommendations.push('🔧 **Address slow requests** - Investigate and optimize slowest endpoints');
  }

  if (recommendations.length === 0) {
    recommendations.push('✅ **Performance looks good** - All metrics are within acceptable ranges');
  }

  return recommendations.join('\n');
}

// Main execution
if (require.main === module) {
  const resultsFile = process.argv[2];
  
  if (!resultsFile) {
    console.error('Usage: node analyze-results.js <results-file.json>');
    process.exit(1);
  }
  
  analyzeResults(resultsFile);
}

module.exports = {
  analyzeResults,
  generateAnalysis,
};

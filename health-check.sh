#!/bin/bash

# =============================================================================
# SYNTHIA STYLE - DEPLOYMENT HEALTH CHECK SCRIPT
# =============================================================================
# Comprehensive health checks for post-deployment validation
# Usage: ./health-check.sh [environment]
# Environments: development, staging, production

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Default values
ENVIRONMENT="${1:-development}"
TIMEOUT=300  # 5 minutes timeout
RETRY_INTERVAL=10  # Check every 10 seconds
MAX_RETRIES=30

# Environment-specific configuration
case "$ENVIRONMENT" in
    "development")
        BASE_URL="https://dev.synthia.style"
        EXPECTED_SERVICES=("backend" "frontend" "postgres" "redis" "nginx")
        ;;
    "staging")
        BASE_URL="https://staging.synthia.style"
        EXPECTED_SERVICES=("backend" "frontend" "postgres" "redis" "nginx")
        ;;
    "production")
        BASE_URL="https://synthia.style"
        EXPECTED_SERVICES=("backend" "frontend" "postgres" "redis" "nginx")
        ;;
    *)
        echo "❌ Error: Unknown environment '$ENVIRONMENT'"
        echo "   Valid environments: development, staging, production"
        exit 1
        ;;
esac

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to make HTTP requests with retries
make_request() {
    local url="$1"
    local expected_status="${2:-200}"
    local max_retries="${3:-3}"
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if response=$(curl -s -w "%{http_code}" -o /tmp/health_response "$url" 2>/dev/null); then
            if [ "$response" = "$expected_status" ]; then
                return 0
            fi
        fi
        
        retry_count=$((retry_count + 1))
        if [ $retry_count -lt $max_retries ]; then
            log_warning "Request failed, retrying in 5 seconds... ($retry_count/$max_retries)"
            sleep 5
        fi
    done
    
    return 1
}

# =============================================================================
# HEALTH CHECK FUNCTIONS
# =============================================================================

check_docker_services() {
    log_info "Checking Docker services status..."
    
    local failed_services=()
    
    for service in "${EXPECTED_SERVICES[@]}"; do
        if docker compose ps --services --filter "status=running" | grep -q "^${service}$"; then
            log_success "Service '$service' is running"
        else
            log_error "Service '$service' is not running or not found"
            failed_services+=("$service")
        fi
    done
    
    if [ ${#failed_services[@]} -eq 0 ]; then
        log_success "All Docker services are running"
        return 0
    else
        log_error "Failed services: ${failed_services[*]}"
        return 1
    fi
}

check_container_health() {
    log_info "Checking container health status..."
    
    local unhealthy_containers=()
    
    # Get all running containers and check their health
    while IFS= read -r container; do
        if [ -n "$container" ]; then
            health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-health-check")
            
            case "$health_status" in
                "healthy")
                    log_success "Container '$container' is healthy"
                    ;;
                "unhealthy")
                    log_error "Container '$container' is unhealthy"
                    unhealthy_containers+=("$container")
                    ;;
                "starting")
                    log_warning "Container '$container' is still starting"
                    ;;
                "no-health-check")
                    log_info "Container '$container' has no health check configured"
                    ;;
            esac
        fi
    done < <(docker compose ps -q)
    
    if [ ${#unhealthy_containers[@]} -eq 0 ]; then
        log_success "All containers are healthy or starting"
        return 0
    else
        log_error "Unhealthy containers: ${unhealthy_containers[*]}"
        return 1
    fi
}

check_api_health() {
    log_info "Checking API health endpoint..."
    
    local api_url="${BASE_URL}/api/v1/cache/health"
    
    if make_request "$api_url" 200 5; then
        local response_body=$(cat /tmp/health_response)
        
        # Parse JSON response
        if echo "$response_body" | jq -e '.status == "healthy"' >/dev/null 2>&1; then
            log_success "API health check passed"
            
            # Extract additional info if available
            if echo "$response_body" | jq -e '.database' >/dev/null 2>&1; then
                local db_status=$(echo "$response_body" | jq -r '.database.status // "unknown"')
                log_info "Database status: $db_status"
            fi
            
            if echo "$response_body" | jq -e '.cache' >/dev/null 2>&1; then
                local cache_status=$(echo "$response_body" | jq -r '.cache.status // "unknown"')
                log_info "Cache status: $cache_status"
            fi
            
            return 0
        else
            log_error "API returned unhealthy status"
            log_error "Response: $response_body"
            return 1
        fi
    else
        log_error "API health check failed - endpoint not responding"
        return 1
    fi
}

check_frontend_availability() {
    log_info "Checking frontend availability..."
    
    if make_request "$BASE_URL" 200 3; then
        local response_body=$(cat /tmp/health_response)
        
        # Check if response contains expected content
        if echo "$response_body" | grep -q "Synthia Style" || echo "$response_body" | grep -q "<!DOCTYPE html>"; then
            log_success "Frontend is accessible and serving content"
            return 0
        else
            log_warning "Frontend accessible but content may be incomplete"
            return 1
        fi
    else
        log_error "Frontend is not accessible"
        return 1
    fi
}

check_database_connectivity() {
    log_info "Checking database connectivity..."
    
    # Try to connect to database through the backend container
    if docker compose exec -T backend python -c "
import asyncio
import sys
from app.db.database import get_database
from app.core.config import get_settings

async def test_db():
    try:
        settings = get_settings()
        db = get_database()
        # Try a simple query
        result = await db.fetch_one('SELECT 1 as test')
        if result and result['test'] == 1:
            print('Database connection successful')
            return True
        else:
            print('Database query failed')
            return False
    except Exception as e:
        print(f'Database connection failed: {e}')
        return False

if __name__ == '__main__':
    result = asyncio.run(test_db())
    sys.exit(0 if result else 1)
" 2>/dev/null; then
        log_success "Database connectivity verified"
        return 0
    else
        log_error "Database connectivity check failed"
        return 1
    fi
}

check_redis_connectivity() {
    log_info "Checking Redis connectivity..."
    
    # Try to connect to Redis through the backend container
    if docker compose exec -T backend python -c "
import redis
import sys
import os

try:
    redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    r = redis.from_url(redis_url)
    r.ping()
    print('Redis connection successful')
    sys.exit(0)
except Exception as e:
    print(f'Redis connection failed: {e}')
    sys.exit(1)
" 2>/dev/null; then
        log_success "Redis connectivity verified"
        return 0
    else
        log_error "Redis connectivity check failed"
        return 1
    fi
}

check_ssl_certificate() {
    log_info "Checking SSL certificate..."
    
    if [[ "$BASE_URL" == https://* ]]; then
        local domain=$(echo "$BASE_URL" | sed 's|https://||' | sed 's|/.*||')
        
        if openssl s_client -connect "${domain}:443" -servername "$domain" </dev/null 2>/dev/null | openssl x509 -noout -dates 2>/dev/null; then
            log_success "SSL certificate is valid"
            
            # Check certificate expiration
            local expiry_date=$(openssl s_client -connect "${domain}:443" -servername "$domain" </dev/null 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
            local expiry_timestamp=$(date -d "$expiry_date" +%s 2>/dev/null || echo "0")
            local current_timestamp=$(date +%s)
            local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
            
            if [ $days_until_expiry -gt 30 ]; then
                log_success "SSL certificate expires in $days_until_expiry days"
            elif [ $days_until_expiry -gt 7 ]; then
                log_warning "SSL certificate expires in $days_until_expiry days (renewal recommended)"
            else
                log_error "SSL certificate expires in $days_until_expiry days (urgent renewal needed)"
            fi
            
            return 0
        else
            log_error "SSL certificate check failed"
            return 1
        fi
    else
        log_info "Skipping SSL check for non-HTTPS URL"
        return 0
    fi
}

check_api_endpoints() {
    log_info "Checking critical API endpoints..."
    
    local endpoints=(
        "/api/v1/cache/health:200"
        "/api/v1/docs:200"
    )
    
    local failed_endpoints=()
    
    for endpoint_config in "${endpoints[@]}"; do
        local endpoint=$(echo "$endpoint_config" | cut -d: -f1)
        local expected_status=$(echo "$endpoint_config" | cut -d: -f2)
        local url="${BASE_URL}${endpoint}"
        
        if make_request "$url" "$expected_status" 2; then
            log_success "Endpoint '$endpoint' responding correctly"
        else
            log_error "Endpoint '$endpoint' failed"
            failed_endpoints+=("$endpoint")
        fi
    done
    
    if [ ${#failed_endpoints[@]} -eq 0 ]; then
        log_success "All critical API endpoints are responding"
        return 0
    else
        log_error "Failed endpoints: ${failed_endpoints[*]}"
        return 1
    fi
}

check_performance_metrics() {
    log_info "Checking basic performance metrics..."
    
    local api_url="${BASE_URL}/api/v1/cache/health"
    local start_time=$(date +%s%N)
    
    if make_request "$api_url" 200 1; then
        local end_time=$(date +%s%N)
        local response_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
        
        if [ $response_time -lt 2000 ]; then
            log_success "API response time: ${response_time}ms (excellent)"
        elif [ $response_time -lt 5000 ]; then
            log_warning "API response time: ${response_time}ms (acceptable)"
        else
            log_error "API response time: ${response_time}ms (too slow)"
            return 1
        fi
        
        return 0
    else
        log_error "Performance check failed - API not responding"
        return 1
    fi
}

# =============================================================================
# MAIN HEALTH CHECK EXECUTION
# =============================================================================

main() {
    echo "============================================================================="
    echo "🏥 SYNTHIA STYLE HEALTH CHECK - $ENVIRONMENT ENVIRONMENT"
    echo "============================================================================="
    echo "🌍 Target URL: $BASE_URL"
    echo "⏰ Started at: $(date)"
    echo "============================================================================="
    
    local start_time=$(date +%s)
    local failed_checks=()
    
    # Array of check functions and their descriptions
    local checks=(
        "check_docker_services:Docker Services"
        "check_container_health:Container Health"
        "check_api_health:API Health"
        "check_frontend_availability:Frontend Availability"
        "check_database_connectivity:Database Connectivity"
        "check_redis_connectivity:Redis Connectivity"
        "check_ssl_certificate:SSL Certificate"
        "check_api_endpoints:API Endpoints"
        "check_performance_metrics:Performance Metrics"
    )
    
    # Execute all health checks
    for check_config in "${checks[@]}"; do
        local check_function=$(echo "$check_config" | cut -d: -f1)
        local check_description=$(echo "$check_config" | cut -d: -f2)
        
        echo ""
        log_info "Running $check_description check..."
        
        if $check_function; then
            log_success "$check_description check passed"
        else
            log_error "$check_description check failed"
            failed_checks+=("$check_description")
        fi
    done
    
    # Summary
    echo ""
    echo "============================================================================="
    echo "📊 HEALTH CHECK SUMMARY"
    echo "============================================================================="
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo "⏱️  Duration: ${duration} seconds"
    echo "🎯 Environment: $ENVIRONMENT"
    echo "🌍 URL: $BASE_URL"
    
    if [ ${#failed_checks[@]} -eq 0 ]; then
        log_success "ALL HEALTH CHECKS PASSED ✅"
        echo "🎉 $ENVIRONMENT environment is healthy and ready!"
        exit 0
    else
        echo ""
        log_error "FAILED CHECKS: ${#failed_checks[@]}"
        for failed_check in "${failed_checks[@]}"; do
            log_error "  - $failed_check"
        done
        echo ""
        log_error "$ENVIRONMENT environment has health issues!"
        echo "📋 Please check the logs and fix the issues before proceeding."
        exit 1
    fi
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

# Check if running in Docker context
if [ -f /.dockerenv ] || [ -f /proc/1/cgroup ] && grep -q docker /proc/1/cgroup 2>/dev/null; then
    log_warning "Running inside Docker container - some checks may be limited"
fi

# Check dependencies
if ! command -v curl &> /dev/null; then
    log_error "curl is required but not installed"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    log_warning "jq not found - JSON parsing will be limited"
fi

if ! command -v docker &> /dev/null; then
    log_error "docker is required but not installed"
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"

# Execute main function
main "$@"

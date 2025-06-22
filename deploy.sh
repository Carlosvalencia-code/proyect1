#!/bin/bash

# =============================================================================
# SYNTHIA STYLE - DEPLOYMENT SCRIPT
# =============================================================================
# Comprehensive deployment script with zero-downtime capabilities
# Usage: ./deploy.sh [environment] [deployment_strategy] [version]
# Environments: development, staging, production
# Strategies: rolling, blue-green, recreate

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Parameters
ENVIRONMENT="${1:-production}"
DEPLOYMENT_STRATEGY="${2:-blue-green}"
VERSION="${3:-latest}"

# Deployment configuration
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DEPLOYMENT_ID="deploy_${ENVIRONMENT}_${TIMESTAMP}"

# Environment-specific configuration
case "$ENVIRONMENT" in
    "development")
        DEPLOY_PATH="/opt/synthia-style-development"
        CONTAINER_PREFIX="synthia-style-development"
        BASE_URL="https://dev.synthia.style"
        HEALTH_CHECK_TIMEOUT=120
        ROLLBACK_ON_FAILURE=true
        ;;
    "staging")
        DEPLOY_PATH="/opt/synthia-style-staging"
        CONTAINER_PREFIX="synthia-style-staging"
        BASE_URL="https://staging.synthia.style"
        HEALTH_CHECK_TIMEOUT=180
        ROLLBACK_ON_FAILURE=true
        ;;
    "production")
        DEPLOY_PATH="/opt/synthia-style-production"
        CONTAINER_PREFIX="synthia-style-production"
        BASE_URL="https://synthia.style"
        HEALTH_CHECK_TIMEOUT=300
        ROLLBACK_ON_FAILURE=true
        ;;
    *)
        echo "❌ Error: Unknown environment '$ENVIRONMENT'"
        echo "   Valid environments: development, staging, production"
        exit 1
        ;;
esac

# Registry configuration
REGISTRY="ghcr.io"
IMAGE_NAME="synthia-style"
SERVICES=("backend" "frontend" "nginx")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

log_info() {
    echo -e "${BLUE}ℹ️  $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
}

log_step() {
    echo -e "${PURPLE}🔄 $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking deployment prerequisites..."
    
    # Check if deployment directory exists
    if [ ! -d "$DEPLOY_PATH" ]; then
        log_error "Deployment directory does not exist: $DEPLOY_PATH"
        return 1
    fi
    
    # Check if docker-compose file exists
    if [ ! -f "${DEPLOY_PATH}/docker-compose.yml" ]; then
        log_error "docker-compose.yml not found in deployment directory"
        return 1
    fi
    
    # Check if .env file exists
    if [ ! -f "${DEPLOY_PATH}/.env" ]; then
        log_error ".env file not found in deployment directory"
        return 1
    fi
    
    # Check docker daemon
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running or accessible"
        return 1
    fi
    
    # Check docker-compose
    if ! docker compose version >/dev/null 2>&1; then
        log_error "docker-compose is not available"
        return 1
    fi
    
    # Check available disk space
    local available_space=$(df "$DEPLOY_PATH" | awk 'NR==2 {print $4}')
    local required_space=2097152  # 2GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        log_error "Insufficient disk space. Required: 2GB, Available: $((available_space / 1024))MB"
        return 1
    fi
    
    log_success "Prerequisites check passed"
    return 0
}

# Function to validate deployment version
validate_deployment_version() {
    log_info "Validating deployment version: $VERSION"
    
    if [ "$VERSION" = "latest" ]; then
        log_info "Using latest version from registry"
        return 0
    fi
    
    # Check if specific version images exist in registry
    for service in "${SERVICES[@]}"; do
        local image="${REGISTRY}/${IMAGE_NAME}-${service}:${VERSION}"
        
        if docker manifest inspect "$image" >/dev/null 2>&1; then
            log_success "Image verified: $image"
        else
            log_error "Image not found: $image"
            return 1
        fi
    done
    
    log_success "Version validation passed"
    return 0
}

# =============================================================================
# BACKUP AND SNAPSHOT FUNCTIONS
# =============================================================================

create_deployment_snapshot() {
    log_step "Creating deployment snapshot..."
    
    local snapshot_dir="${DEPLOY_PATH}/snapshots/pre_deploy_${TIMESTAMP}"
    mkdir -p "$snapshot_dir"
    
    # Save current configuration
    cp "${DEPLOY_PATH}/docker-compose.yml" "${snapshot_dir}/"
    cp "${DEPLOY_PATH}/.env" "${snapshot_dir}/"
    
    # Save current container states
    docker compose ps --format json > "${snapshot_dir}/container_states.json" 2>/dev/null || echo "[]" > "${snapshot_dir}/container_states.json"
    
    # Save current image information
    docker compose config | grep "image:" > "${snapshot_dir}/current_images.txt" || touch "${snapshot_dir}/current_images.txt"
    
    # Save version information
    docker compose exec -T backend python -c "
import os
print(f'VERSION={os.getenv(\"APP_VERSION\", \"unknown\")}')
print(f'COMMIT_SHA={os.getenv(\"COMMIT_SHA\", \"unknown\")}')
print(f'ENVIRONMENT={os.getenv(\"ENVIRONMENT\", \"unknown\")}')
" > "${snapshot_dir}/version_info.txt" 2>/dev/null || echo "VERSION=unknown" > "${snapshot_dir}/version_info.txt"
    
    # Create database snapshot
    if [ "$ENVIRONMENT" = "production" ] || [ "${CREATE_DB_BACKUP:-true}" = "true" ]; then
        log_info "Creating database backup as part of snapshot..."
        "${SCRIPT_DIR}/backup-db.sh" "$ENVIRONMENT" "full" || log_warning "Database backup failed"
        
        # Link latest backup to snapshot
        local latest_backup=$(ls -t /opt/synthia-backups/${ENVIRONMENT}/daily/ | head -1 2>/dev/null || echo "")
        if [ -n "$latest_backup" ]; then
            ln -sf "/opt/synthia-backups/${ENVIRONMENT}/daily/${latest_backup}" "${snapshot_dir}/database_backup.sql.gz"
        fi
    fi
    
    # Create metadata
    cat > "${snapshot_dir}/metadata.json" << EOF
{
    "deployment_id": "${DEPLOYMENT_ID}",
    "environment": "${ENVIRONMENT}",
    "timestamp": "$(date -Iseconds)",
    "version_before": "$(cat "${snapshot_dir}/version_info.txt" | grep VERSION | cut -d= -f2)",
    "version_target": "${VERSION}",
    "deployment_strategy": "${DEPLOYMENT_STRATEGY}",
    "snapshot_path": "${snapshot_dir}"
}
EOF
    
    log_success "Deployment snapshot created: $(basename "$snapshot_dir")"
    echo "$snapshot_dir"
}

# =============================================================================
# DEPLOYMENT STRATEGIES
# =============================================================================

deploy_recreate() {
    log_step "Executing recreate deployment strategy..."
    
    # Stop all services
    log_info "Stopping all services..."
    docker compose down --remove-orphans
    
    # Pull new images
    log_info "Pulling new images..."
    update_image_versions
    docker compose pull
    
    # Start services
    log_info "Starting services with new images..."
    docker compose up -d
    
    log_success "Recreate deployment completed"
}

deploy_rolling() {
    log_step "Executing rolling deployment strategy..."
    
    # Update images in compose file
    update_image_versions
    
    # Rolling update for each service
    for service in "${SERVICES[@]}"; do
        log_info "Rolling update for service: $service"
        
        # Scale up new version
        docker compose up -d --no-deps "$service"
        
        # Wait for health check
        sleep 30
        
        # Verify service health
        if ! verify_service_health "$service"; then
            log_error "Health check failed for $service during rolling update"
            return 1
        fi
        
        log_success "Rolling update completed for $service"
    done
    
    # Clean up old containers
    docker compose down --remove-orphans
    docker system prune -f
    
    log_success "Rolling deployment completed"
}

deploy_blue_green() {
    log_step "Executing blue-green deployment strategy..."
    
    # Determine current environment color
    local current_color="blue"
    local new_color="green"
    
    if docker compose ps | grep -q "green"; then
        current_color="green"
        new_color="blue"
    fi
    
    log_info "Current environment: $current_color, Deploying to: $new_color"
    
    # Create new environment configuration
    local green_compose="docker-compose.${new_color}.yml"
    cp docker-compose.yml "$green_compose"
    
    # Update service names for new color
    sed -i "s/${CONTAINER_PREFIX}/${CONTAINER_PREFIX}-${new_color}/g" "$green_compose"
    
    # Update image versions
    update_image_versions "$green_compose"
    
    # Start new environment
    log_info "Starting $new_color environment..."
    docker compose -f "$green_compose" up -d
    
    # Wait for new environment to be ready
    log_info "Waiting for $new_color environment to be ready..."
    sleep 60
    
    # Health check new environment
    if ! verify_deployment_health "$green_compose"; then
        log_error "$new_color environment health check failed"
        log_info "Cleaning up failed $new_color environment..."
        docker compose -f "$green_compose" down --remove-orphans
        return 1
    fi
    
    # Switch traffic (in a real scenario, this would update load balancer)
    log_info "Switching traffic to $new_color environment..."
    
    # Update main docker-compose to point to new environment
    cp "$green_compose" docker-compose.yml
    
    # Stop old environment
    if docker compose ps --format "table {{.Service}}" | grep -q "$current_color"; then
        log_info "Stopping $current_color environment..."
        docker compose -f "docker-compose.${current_color}.yml" down --remove-orphans
    fi
    
    # Clean up temporary files
    rm -f "$green_compose" "docker-compose.${current_color}.yml"
    
    log_success "Blue-green deployment completed"
}

# =============================================================================
# IMAGE AND CONFIGURATION MANAGEMENT
# =============================================================================

update_image_versions() {
    local compose_file="${1:-docker-compose.yml}"
    
    log_info "Updating image versions in $compose_file..."
    
    # Backup original compose file
    cp "$compose_file" "${compose_file}.backup"
    
    # Update image versions for each service
    for service in "${SERVICES[@]}"; do
        local new_image="${REGISTRY}/${IMAGE_NAME}-${service}:${VERSION}"
        
        # Update image in docker-compose file
        sed -i "s|image: .*${service}:.*|image: ${new_image}|g" "$compose_file"
        
        log_info "Updated $service image to: $new_image"
    done
    
    # Update environment variables
    update_environment_variables
    
    log_success "Image versions updated"
}

update_environment_variables() {
    log_info "Updating environment variables..."
    
    # Update .env file with deployment-specific variables
    cat >> .env << EOF

# Deployment Information
DEPLOYMENT_ID=${DEPLOYMENT_ID}
DEPLOYED_AT=$(date -Iseconds)
DEPLOYED_VERSION=${VERSION}
DEPLOYMENT_STRATEGY=${DEPLOYMENT_STRATEGY}
EOF

    log_success "Environment variables updated"
}

# =============================================================================
# HEALTH CHECK AND VALIDATION
# =============================================================================

verify_service_health() {
    local service="$1"
    local max_attempts=30
    local attempt=1
    
    log_info "Verifying health of service: $service"
    
    while [ $attempt -le $max_attempts ]; do
        if docker compose ps "$service" | grep -q "Up"; then
            # Check if service has health check
            local health_status=$(docker compose ps "$service" --format "{{.Health}}" 2>/dev/null || echo "no-health-check")
            
            case "$health_status" in
                "healthy")
                    log_success "Service $service is healthy"
                    return 0
                    ;;
                "unhealthy")
                    log_error "Service $service is unhealthy"
                    return 1
                    ;;
                "starting")
                    log_info "Service $service is starting... (attempt $attempt/$max_attempts)"
                    ;;
                *)
                    # No health check defined, check if container is running
                    log_success "Service $service is running (no health check defined)"
                    return 0
                    ;;
            esac
        else
            log_warning "Service $service is not running (attempt $attempt/$max_attempts)"
        fi
        
        sleep 10
        attempt=$((attempt + 1))
    done
    
    log_error "Service $service health check timed out"
    return 1
}

verify_deployment_health() {
    local compose_file="${1:-docker-compose.yml}"
    
    log_info "Verifying overall deployment health..."
    
    # Check all services
    for service in "${SERVICES[@]}"; do
        if ! verify_service_health "$service"; then
            return 1
        fi
    done
    
    # Run comprehensive health checks
    log_info "Running comprehensive health checks..."
    if "${SCRIPT_DIR}/health-check.sh" "$ENVIRONMENT"; then
        log_success "Comprehensive health checks passed"
        return 0
    else
        log_error "Comprehensive health checks failed"
        return 1
    fi
}

run_smoke_tests() {
    log_info "Running post-deployment smoke tests..."
    
    # Basic connectivity tests
    local api_url="${BASE_URL}/api/v1/cache/health"
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$api_url" >/dev/null; then
            log_success "API connectivity test passed"
            break
        else
            log_info "API connectivity test failed (attempt $attempt/$max_attempts)"
            if [ $attempt -eq $max_attempts ]; then
                log_error "API connectivity test failed after $max_attempts attempts"
                return 1
            fi
        fi
        
        sleep 10
        attempt=$((attempt + 1))
    done
    
    # Frontend test
    if curl -s -f "$BASE_URL" >/dev/null; then
        log_success "Frontend connectivity test passed"
    else
        log_error "Frontend connectivity test failed"
        return 1
    fi
    
    # Database connectivity test
    if docker compose exec -T backend python -c "
import asyncio
from app.db.database import get_database

async def test_db():
    try:
        db = get_database()
        result = await db.fetch_one('SELECT 1 as test')
        return result['test'] == 1
    except Exception:
        return False

print('SUCCESS' if asyncio.run(test_db()) else 'FAILED')
" 2>/dev/null | grep -q "SUCCESS"; then
        log_success "Database connectivity test passed"
    else
        log_warning "Database connectivity test failed or skipped"
    fi
    
    log_success "Smoke tests completed"
    return 0
}

# =============================================================================
# ROLLBACK FUNCTIONALITY
# =============================================================================

perform_automatic_rollback() {
    local snapshot_path="$1"
    
    log_error "Deployment failed. Initiating automatic rollback..."
    
    # Set emergency rollback flag
    export EMERGENCY_ROLLBACK=true
    
    # Use rollback script
    if "${SCRIPT_DIR}/rollback.sh" "$ENVIRONMENT" "quick" "$(basename "$snapshot_path")"; then
        log_success "Automatic rollback completed successfully"
        return 0
    else
        log_error "Automatic rollback failed! Manual intervention required."
        return 1
    fi
}

# =============================================================================
# NOTIFICATION FUNCTIONS
# =============================================================================

send_deployment_notification() {
    local status="$1"
    local details="$2"
    
    local message="🚀 Synthia Style Deployment: $status"
    local color="good"
    
    if [ "$status" = "FAILED" ]; then
        color="danger"
    elif [ "$status" = "STARTED" ]; then
        color="warning"
    fi
    
    # Send Slack notification if webhook is configured
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"text\": \"$message\",
                \"attachments\": [
                    {
                        \"color\": \"$color\",
                        \"fields\": [
                            {\"title\": \"Environment\", \"value\": \"$ENVIRONMENT\", \"short\": true},
                            {\"title\": \"Version\", \"value\": \"$VERSION\", \"short\": true},
                            {\"title\": \"Strategy\", \"value\": \"$DEPLOYMENT_STRATEGY\", \"short\": true},
                            {\"title\": \"Deployment ID\", \"value\": \"$DEPLOYMENT_ID\", \"short\": true},
                            {\"title\": \"URL\", \"value\": \"$BASE_URL\", \"short\": false},
                            {\"title\": \"Details\", \"value\": \"$details\", \"short\": false}
                        ]
                    }
                ]
            }" \
            "${SLACK_WEBHOOK_URL}" >/dev/null 2>&1 || true
    fi
    
    log_info "Notification sent: $message"
}

# =============================================================================
# MAIN DEPLOYMENT EXECUTION
# =============================================================================

main() {
    echo "============================================================================="
    echo "🚀 SYNTHIA STYLE DEPLOYMENT"
    echo "============================================================================="
    echo "🌍 Environment: $ENVIRONMENT"
    echo "📦 Version: $VERSION"
    echo "📋 Strategy: $DEPLOYMENT_STRATEGY"
    echo "🆔 Deployment ID: $DEPLOYMENT_ID"
    echo "⏰ Started at: $(date)"
    echo "============================================================================="
    
    local start_time=$(date +%s)
    local snapshot_path=""
    
    # Send start notification
    send_deployment_notification "STARTED" "Deployment process initiated"
    
    # Prerequisites check
    if ! check_prerequisites; then
        send_deployment_notification "FAILED" "Prerequisites check failed"
        exit 1
    fi
    
    # Validate deployment version
    if ! validate_deployment_version; then
        send_deployment_notification "FAILED" "Version validation failed"
        exit 1
    fi
    
    # Create pre-deployment snapshot
    snapshot_path=$(create_deployment_snapshot)
    
    # Execute deployment strategy
    case "$DEPLOYMENT_STRATEGY" in
        "recreate")
            if ! deploy_recreate; then
                if [ "$ROLLBACK_ON_FAILURE" = "true" ]; then
                    perform_automatic_rollback "$snapshot_path"
                fi
                send_deployment_notification "FAILED" "Recreate deployment failed"
                exit 1
            fi
            ;;
        "rolling")
            if ! deploy_rolling; then
                if [ "$ROLLBACK_ON_FAILURE" = "true" ]; then
                    perform_automatic_rollback "$snapshot_path"
                fi
                send_deployment_notification "FAILED" "Rolling deployment failed"
                exit 1
            fi
            ;;
        "blue-green")
            if ! deploy_blue_green; then
                if [ "$ROLLBACK_ON_FAILURE" = "true" ]; then
                    perform_automatic_rollback "$snapshot_path"
                fi
                send_deployment_notification "FAILED" "Blue-green deployment failed"
                exit 1
            fi
            ;;
        *)
            log_error "Unknown deployment strategy: $DEPLOYMENT_STRATEGY"
            log_error "Valid strategies: recreate, rolling, blue-green"
            send_deployment_notification "FAILED" "Invalid deployment strategy"
            exit 1
            ;;
    esac
    
    # Wait for services to stabilize
    log_info "Waiting for services to stabilize..."
    sleep $HEALTH_CHECK_TIMEOUT
    
    # Verify deployment health
    if ! verify_deployment_health; then
        log_error "Deployment health verification failed"
        if [ "$ROLLBACK_ON_FAILURE" = "true" ]; then
            perform_automatic_rollback "$snapshot_path"
        fi
        send_deployment_notification "FAILED" "Health verification failed"
        exit 1
    fi
    
    # Run smoke tests
    if ! run_smoke_tests; then
        log_warning "Some smoke tests failed, but deployment continues"
    fi
    
    # Calculate execution time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Success summary
    echo ""
    echo "============================================================================="
    echo "📊 DEPLOYMENT COMPLETION SUMMARY"
    echo "============================================================================="
    log_success "Deployment completed successfully!"
    echo "🌍 Environment: $ENVIRONMENT"
    echo "📦 Version: $VERSION"
    echo "📋 Strategy: $DEPLOYMENT_STRATEGY"
    echo "🆔 Deployment ID: $DEPLOYMENT_ID"
    echo "⏱️  Duration: ${duration} seconds"
    echo "🌐 URL: $BASE_URL"
    echo "📸 Snapshot: $(basename "$snapshot_path")"
    
    # Send success notification
    send_deployment_notification "SUCCESS" "Deployment completed successfully in ${duration} seconds"
    
    log_success "Deployment process completed. System is ready!"
    exit 0
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

# Validate parameters
case "$DEPLOYMENT_STRATEGY" in
    "recreate"|"rolling"|"blue-green")
        ;;
    *)
        echo "❌ Error: Invalid deployment strategy '$DEPLOYMENT_STRATEGY'"
        echo "   Valid strategies: recreate, rolling, blue-green"
        exit 1
        ;;
esac

# Check dependencies
for cmd in docker curl; do
    if ! command -v "$cmd" &> /dev/null; then
        log_error "$cmd is required but not installed"
        exit 1
    fi
done

# Change to project directory
cd "$PROJECT_DIR"

# Change to deployment directory
if [ -d "$DEPLOY_PATH" ]; then
    cd "$DEPLOY_PATH"
else
    log_error "Deployment directory not found: $DEPLOY_PATH"
    exit 1
fi

# Execute main function
main "$@"

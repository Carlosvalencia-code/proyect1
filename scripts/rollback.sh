#!/bin/bash

# =============================================================================
# SYNTHIA STYLE - DEPLOYMENT ROLLBACK SCRIPT
# =============================================================================
# Automated rollback to previous deployment version with safety checks
# Usage: ./rollback.sh [environment] [rollback_type] [target_version]
# Environments: development, staging, production
# Rollback types: quick, full, database

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Parameters
ENVIRONMENT="${1:-production}"
ROLLBACK_TYPE="${2:-quick}"
TARGET_VERSION="${3:-previous}"

# Rollback configuration
ROLLBACK_BASE_DIR="/opt/synthia-rollback"
ROLLBACK_DIR="${ROLLBACK_BASE_DIR}/${ENVIRONMENT}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Environment-specific configuration
case "$ENVIRONMENT" in
    "development")
        DEPLOY_PATH="/opt/synthia-style-development"
        CONTAINER_PREFIX="synthia-style-development"
        BASE_URL="https://dev.synthia.style"
        ;;
    "staging")
        DEPLOY_PATH="/opt/synthia-style-staging"
        CONTAINER_PREFIX="synthia-style-staging"
        BASE_URL="https://staging.synthia.style"
        ;;
    "production")
        DEPLOY_PATH="/opt/synthia-style-production"
        CONTAINER_PREFIX="synthia-style-production"
        BASE_URL="https://synthia.style"
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

# Function to confirm rollback action
confirm_rollback() {
    echo ""
    log_warning "⚠️  ROLLBACK CONFIRMATION REQUIRED ⚠️"
    echo "Environment: $ENVIRONMENT"
    echo "Rollback Type: $ROLLBACK_TYPE"
    echo "Target Version: $TARGET_VERSION"
    echo "Current Time: $(date)"
    echo ""
    
    if [ "$ENVIRONMENT" = "production" ]; then
        log_warning "🚨 THIS IS A PRODUCTION ROLLBACK 🚨"
        echo ""
    fi
    
    read -p "Are you sure you want to proceed with the rollback? (type 'YES' to confirm): " confirmation
    
    if [ "$confirmation" != "YES" ]; then
        log_error "Rollback cancelled by user"
        exit 1
    fi
    
    log_info "Rollback confirmed. Proceeding..."
}

# Function to check if we're in a safe rollback window
check_rollback_safety() {
    log_info "Checking rollback safety conditions..."
    
    # Check if services are currently running
    if ! docker compose ps | grep -q "Up"; then
        log_error "No services are currently running. Cannot determine current state."
        return 1
    fi
    
    # Check if there's a current backup available
    if [ ! -d "$ROLLBACK_DIR" ] || [ -z "$(ls -A "$ROLLBACK_DIR" 2>/dev/null)" ]; then
        log_warning "No rollback snapshots found. Creating emergency backup..."
        if ! create_emergency_backup; then
            log_error "Failed to create emergency backup. Rollback aborted for safety."
            return 1
        fi
    fi
    
    # Check system load
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local cpu_count=$(nproc)
    local load_threshold=$(echo "$cpu_count * 0.8" | bc -l)
    
    if (( $(echo "$load_avg > $load_threshold" | bc -l) )); then
        log_warning "High system load detected ($load_avg). Consider waiting for lower load."
        read -p "Continue anyway? (y/N): " continue_high_load
        if [[ ! "$continue_high_load" =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi
    
    log_success "Rollback safety checks passed"
    return 0
}

# =============================================================================
# BACKUP AND SNAPSHOT FUNCTIONS
# =============================================================================

create_emergency_backup() {
    log_info "Creating emergency backup before rollback..."
    
    mkdir -p "$ROLLBACK_DIR"
    
    # Backup current deployment state
    local backup_name="emergency_backup_${TIMESTAMP}"
    local backup_path="${ROLLBACK_DIR}/${backup_name}"
    
    mkdir -p "$backup_path"
    
    # Save current docker-compose.yml and .env
    cp "${DEPLOY_PATH}/docker-compose.yml" "${backup_path}/" 2>/dev/null || true
    cp "${DEPLOY_PATH}/.env" "${backup_path}/" 2>/dev/null || true
    
    # Save current container image information
    docker compose ps --format json > "${backup_path}/container_state.json" 2>/dev/null || true
    
    # Create database backup if possible
    if docker compose ps | grep -q postgres; then
        log_info "Creating emergency database backup..."
        "${SCRIPT_DIR}/backup-db.sh" "$ENVIRONMENT" "full" || log_warning "Emergency database backup failed"
    fi
    
    # Save current application version info
    docker compose exec -T backend python -c "
import os
print(f'VERSION={os.getenv(\"APP_VERSION\", \"unknown\")}')
print(f'COMMIT_SHA={os.getenv(\"COMMIT_SHA\", \"unknown\")}')
" > "${backup_path}/version_info.txt" 2>/dev/null || echo "VERSION=unknown" > "${backup_path}/version_info.txt"
    
    log_success "Emergency backup created: $backup_name"
    return 0
}

save_current_state() {
    log_info "Saving current deployment state..."
    
    local state_dir="${ROLLBACK_DIR}/current_state_${TIMESTAMP}"
    mkdir -p "$state_dir"
    
    # Save container states
    docker compose ps --format json > "${state_dir}/containers.json"
    
    # Save configuration files
    cp "${DEPLOY_PATH}/docker-compose.yml" "${state_dir}/"
    cp "${DEPLOY_PATH}/.env" "${state_dir}/"
    
    # Save current images
    docker compose config | grep image: > "${state_dir}/current_images.txt"
    
    # Save system state
    cat > "${state_dir}/system_state.txt" << EOF
Timestamp: $(date -Iseconds)
Environment: $ENVIRONMENT
Uptime: $(uptime)
Load Average: $(uptime | awk -F'load average:' '{print $2}')
Memory Usage: $(free -h | head -2)
Disk Usage: $(df -h "$DEPLOY_PATH")
EOF

    log_success "Current state saved to: $(basename "$state_dir")"
    echo "$state_dir"
}

# =============================================================================
# ROLLBACK FUNCTIONS
# =============================================================================

find_rollback_target() {
    log_info "Finding rollback target version..."
    
    case "$TARGET_VERSION" in
        "previous"|"last"|"latest")
            # Find the most recent backup/snapshot
            local latest_backup=$(ls -t "$ROLLBACK_DIR" | grep -E '^(snapshot|backup)_' | head -1)
            if [ -n "$latest_backup" ]; then
                TARGET_VERSION="$latest_backup"
                log_info "Found previous version: $TARGET_VERSION"
            else
                log_error "No previous version found for rollback"
                return 1
            fi
            ;;
        *)
            # Check if specified version exists
            if [ ! -d "${ROLLBACK_DIR}/${TARGET_VERSION}" ]; then
                log_error "Specified version '$TARGET_VERSION' not found"
                log_info "Available versions:"
                ls -la "$ROLLBACK_DIR" | grep "^d" | awk '{print $9}' | grep -v "^\.$\|^\.\.$" || echo "  None"
                return 1
            fi
            ;;
    esac
    
    log_success "Rollback target confirmed: $TARGET_VERSION"
    return 0
}

perform_quick_rollback() {
    log_info "Performing quick rollback (containers only)..."
    
    local target_path="${ROLLBACK_DIR}/${TARGET_VERSION}"
    
    # Stop current services
    log_info "Stopping current services..."
    docker compose down --remove-orphans
    
    # Restore previous configuration
    if [ -f "${target_path}/docker-compose.yml" ]; then
        log_info "Restoring docker-compose configuration..."
        cp "${target_path}/docker-compose.yml" "${DEPLOY_PATH}/"
    fi
    
    if [ -f "${target_path}/.env" ]; then
        log_info "Restoring environment configuration..."
        cp "${target_path}/.env" "${DEPLOY_PATH}/"
    fi
    
    # Pull and start previous images
    if [ -f "${target_path}/current_images.txt" ]; then
        log_info "Restoring previous container images..."
        
        # Extract image names and pull them
        while IFS= read -r line; do
            if [[ "$line" =~ image:\ (.+) ]]; then
                local image="${BASH_REMATCH[1]}"
                log_info "Pulling image: $image"
                docker pull "$image" || log_warning "Failed to pull $image"
            fi
        done < "${target_path}/current_images.txt"
    fi
    
    # Start services with previous configuration
    log_info "Starting services with previous configuration..."
    docker compose up -d
    
    # Wait for services to start
    log_info "Waiting for services to start..."
    sleep 30
    
    log_success "Quick rollback completed"
}

perform_full_rollback() {
    log_info "Performing full rollback (containers + database)..."
    
    # Create backup of current state before full rollback
    save_current_state
    
    # Stop all services
    log_info "Stopping all services..."
    docker compose down --volumes --remove-orphans
    
    # Rollback database if backup exists
    local target_path="${ROLLBACK_DIR}/${TARGET_VERSION}"
    if [ -f "${target_path}/database_backup.sql.gz" ]; then
        log_info "Restoring database from backup..."
        
        # Start only database container
        docker compose up -d postgres
        sleep 20
        
        # Restore database
        if restore_database "${target_path}/database_backup.sql.gz"; then
            log_success "Database restored successfully"
        else
            log_error "Database restore failed"
            return 1
        fi
    else
        log_warning "No database backup found for target version"
    fi
    
    # Perform quick rollback for containers
    perform_quick_rollback
    
    log_success "Full rollback completed"
}

perform_database_rollback() {
    log_info "Performing database-only rollback..."
    
    local target_path="${ROLLBACK_DIR}/${TARGET_VERSION}"
    local db_backup="${target_path}/database_backup.sql.gz"
    
    if [ ! -f "$db_backup" ]; then
        log_error "Database backup not found: $db_backup"
        return 1
    fi
    
    # Create current database backup before rollback
    log_info "Creating safety backup of current database..."
    "${SCRIPT_DIR}/backup-db.sh" "$ENVIRONMENT" "full"
    
    # Restore database
    if restore_database "$db_backup"; then
        log_success "Database rollback completed"
    else
        log_error "Database rollback failed"
        return 1
    fi
}

restore_database() {
    local backup_file="$1"
    
    log_info "Restoring database from: $(basename "$backup_file")"
    
    # Ensure database container is running
    if ! docker compose ps postgres | grep -q "Up"; then
        log_info "Starting database container..."
        docker compose up -d postgres
        sleep 20
    fi
    
    # Copy backup file to container
    local container_backup="/tmp/restore_backup.sql"
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" | docker exec -i "${CONTAINER_PREFIX}_postgres_1" psql -U postgres -d template1 -c "DROP DATABASE IF EXISTS synthia_db_temp;"
        gunzip -c "$backup_file" | docker exec -i "${CONTAINER_PREFIX}_postgres_1" psql -U postgres -d template1 -c "CREATE DATABASE synthia_db_temp;"
        gunzip -c "$backup_file" | docker exec -i "${CONTAINER_PREFIX}_postgres_1" psql -U postgres -d synthia_db_temp
    else
        docker exec -i "${CONTAINER_PREFIX}_postgres_1" psql -U postgres -d template1 < "$backup_file"
    fi
    
    log_success "Database restore completed"
    return 0
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

validate_rollback() {
    log_info "Validating rollback success..."
    
    # Wait for services to fully start
    sleep 60
    
    # Run health checks
    if "${SCRIPT_DIR}/health-check.sh" "$ENVIRONMENT"; then
        log_success "Rollback validation passed - all systems healthy"
        return 0
    else
        log_error "Rollback validation failed - system is not healthy"
        return 1
    fi
}

test_rollback_functionality() {
    log_info "Testing basic functionality after rollback..."
    
    # Test API endpoints
    local api_url="${BASE_URL}/api/v1/cache/health"
    if curl -s -f "$api_url" >/dev/null; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
        return 1
    fi
    
    # Test frontend
    if curl -s -f "$BASE_URL" >/dev/null; then
        log_success "Frontend accessibility test passed"
    else
        log_error "Frontend accessibility test failed"
        return 1
    fi
    
    # Test database connectivity (if backend is up)
    if docker compose exec -T backend python -c "
import asyncio
from app.db.database import get_database

async def test_db():
    try:
        db = get_database()
        result = await db.fetch_one('SELECT 1 as test')
        return result['test'] == 1
    except Exception as e:
        print(f'Error: {e}')
        return False

print('SUCCESS' if asyncio.run(test_db()) else 'FAILED')
" 2>/dev/null | grep -q "SUCCESS"; then
        log_success "Database connectivity test passed"
    else
        log_warning "Database connectivity test failed or skipped"
    fi
    
    log_success "Functionality tests completed"
    return 0
}

# =============================================================================
# NOTIFICATION FUNCTIONS
# =============================================================================

send_rollback_notification() {
    local status="$1"
    local details="$2"
    
    local message="🔄 Synthia Style Rollback: $status"
    local color="warning"
    
    if [ "$status" = "COMPLETED" ]; then
        color="good"
    elif [ "$status" = "FAILED" ]; then
        color="danger"
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
                            {\"title\": \"Rollback Type\", \"value\": \"$ROLLBACK_TYPE\", \"short\": true},
                            {\"title\": \"Target Version\", \"value\": \"$TARGET_VERSION\", \"short\": true},
                            {\"title\": \"Timestamp\", \"value\": \"$(date -Iseconds)\", \"short\": true},
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
# MAIN ROLLBACK EXECUTION
# =============================================================================

main() {
    echo "============================================================================="
    echo "🔄 SYNTHIA STYLE DEPLOYMENT ROLLBACK"
    echo "============================================================================="
    echo "🌍 Environment: $ENVIRONMENT"
    echo "📋 Rollback Type: $ROLLBACK_TYPE"
    echo "🎯 Target Version: $TARGET_VERSION"
    echo "⏰ Started at: $(date)"
    echo "============================================================================="
    
    local start_time=$(date +%s)
    
    # Confirm rollback (skip in emergency situations)
    if [ "${EMERGENCY_ROLLBACK:-false}" != "true" ]; then
        confirm_rollback
    fi
    
    # Safety checks
    if ! check_rollback_safety; then
        send_rollback_notification "ABORTED" "Safety checks failed"
        exit 1
    fi
    
    # Find rollback target
    if ! find_rollback_target; then
        send_rollback_notification "FAILED" "Could not find rollback target"
        exit 1
    fi
    
    # Save current state before rollback
    local current_state_backup=$(save_current_state)
    
    # Perform rollback based on type
    case "$ROLLBACK_TYPE" in
        "quick")
            if ! perform_quick_rollback; then
                send_rollback_notification "FAILED" "Quick rollback failed"
                exit 1
            fi
            ;;
        "full")
            if ! perform_full_rollback; then
                send_rollback_notification "FAILED" "Full rollback failed"
                exit 1
            fi
            ;;
        "database")
            if ! perform_database_rollback; then
                send_rollback_notification "FAILED" "Database rollback failed"
                exit 1
            fi
            ;;
        *)
            log_error "Unknown rollback type: $ROLLBACK_TYPE"
            log_error "Valid types: quick, full, database"
            exit 1
            ;;
    esac
    
    # Validate rollback success
    if ! validate_rollback; then
        log_error "Rollback validation failed. System may be in an inconsistent state."
        send_rollback_notification "FAILED" "Rollback validation failed"
        exit 1
    fi
    
    # Test functionality
    if ! test_rollback_functionality; then
        log_warning "Some functionality tests failed after rollback"
    fi
    
    # Calculate execution time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Success summary
    echo ""
    echo "============================================================================="
    echo "📊 ROLLBACK COMPLETION SUMMARY"
    echo "============================================================================="
    log_success "Rollback completed successfully!"
    echo "🔄 Rollback Type: $ROLLBACK_TYPE"
    echo "🎯 Target Version: $TARGET_VERSION"
    echo "🌍 Environment: $ENVIRONMENT"
    echo "⏱️  Duration: ${duration} seconds"
    echo "🔙 Previous State Backup: $(basename "$current_state_backup")"
    
    # Send success notification
    send_rollback_notification "COMPLETED" "Rollback completed successfully in ${duration} seconds"
    
    log_success "Rollback process completed. System should be operational."
    exit 0
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

# Validate parameters
case "$ROLLBACK_TYPE" in
    "quick"|"full"|"database")
        ;;
    *)
        echo "❌ Error: Invalid rollback type '$ROLLBACK_TYPE'"
        echo "   Valid types: quick, full, database"
        exit 1
        ;;
esac

# Check dependencies
for cmd in docker curl bc; do
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

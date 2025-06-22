#!/bin/bash

# =============================================================================
# SYNTHIA STYLE - DATABASE BACKUP SCRIPT
# =============================================================================
# Creates comprehensive database backups with retention management
# Usage: ./backup-db.sh [environment] [backup_type]
# Environments: development, staging, production
# Backup types: full, schema-only, data-only

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Parameters
ENVIRONMENT="${1:-production}"
BACKUP_TYPE="${2:-full}"

# Backup configuration
BACKUP_BASE_DIR="/opt/synthia-backups"
BACKUP_DIR="${BACKUP_BASE_DIR}/${ENVIRONMENT}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PREFIX="synthia_${ENVIRONMENT}_${BACKUP_TYPE}"
BACKUP_FILENAME="${BACKUP_PREFIX}_${TIMESTAMP}.sql"

# Retention settings (days)
RETENTION_DAILY=7
RETENTION_WEEKLY=30
RETENTION_MONTHLY=90

# Environment-specific configuration
case "$ENVIRONMENT" in
    "development")
        POSTGRES_DB="synthia_dev_db"
        POSTGRES_USER="synthia_dev_user"
        POSTGRES_CONTAINER="synthia-style-development_postgres_1"
        MAX_BACKUP_SIZE="100M"
        ;;
    "staging")
        POSTGRES_DB="synthia_staging_db"
        POSTGRES_USER="synthia_staging_user"
        POSTGRES_CONTAINER="synthia-style-staging_postgres_1"
        MAX_BACKUP_SIZE="500M"
        ;;
    "production")
        POSTGRES_DB="synthia_prod_db"
        POSTGRES_USER="synthia_prod_user"
        POSTGRES_CONTAINER="synthia-style-production_postgres_1"
        MAX_BACKUP_SIZE="2G"
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

# Function to format bytes to human readable
format_bytes() {
    local bytes=$1
    if [ $bytes -lt 1024 ]; then
        echo "${bytes}B"
    elif [ $bytes -lt 1048576 ]; then
        echo "$((bytes / 1024))KB"
    elif [ $bytes -lt 1073741824 ]; then
        echo "$((bytes / 1048576))MB"
    else
        echo "$((bytes / 1073741824))GB"
    fi
}

# Function to check disk space
check_disk_space() {
    local required_space_mb=$1
    local available_space_mb=$(df "$BACKUP_DIR" | awk 'NR==2 {print int($4/1024)}')
    
    if [ $available_space_mb -lt $required_space_mb ]; then
        log_error "Insufficient disk space. Required: ${required_space_mb}MB, Available: ${available_space_mb}MB"
        return 1
    fi
    
    log_info "Disk space check passed. Available: ${available_space_mb}MB"
    return 0
}

# Function to estimate database size
estimate_db_size() {
    local size_query="SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB}'));"
    
    if docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "$size_query" 2>/dev/null; then
        return 0
    else
        log_warning "Could not estimate database size"
        return 1
    fi
}

# =============================================================================
# BACKUP FUNCTIONS
# =============================================================================

create_backup_directory() {
    log_info "Creating backup directory structure..."
    
    # Create main backup directories
    sudo mkdir -p "$BACKUP_DIR"/{daily,weekly,monthly,temp}
    sudo chown -R $(whoami):$(whoami) "$BACKUP_BASE_DIR" 2>/dev/null || true
    
    # Create subdirectories for organization
    mkdir -p "$BACKUP_DIR"/daily
    mkdir -p "$BACKUP_DIR"/weekly  
    mkdir -p "$BACKUP_DIR"/monthly
    mkdir -p "$BACKUP_DIR"/temp
    
    log_success "Backup directory structure created: $BACKUP_DIR"
}

validate_database_connection() {
    log_info "Validating database connection..."
    
    # Check if container is running
    if ! docker ps | grep -q "$POSTGRES_CONTAINER"; then
        log_error "PostgreSQL container '$POSTGRES_CONTAINER' is not running"
        return 1
    fi
    
    # Test database connection
    if docker exec "$POSTGRES_CONTAINER" pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
        log_success "Database connection validated"
        return 0
    else
        log_error "Database connection failed"
        return 1
    fi
}

perform_full_backup() {
    log_info "Performing full database backup..."
    
    local backup_file="${BACKUP_DIR}/temp/${BACKUP_FILENAME}"
    local compressed_file="${backup_file}.gz"
    
    # Perform the backup
    if docker exec "$POSTGRES_CONTAINER" pg_dump \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --verbose \
        --format=custom \
        --no-password \
        --compress=6 \
        --file="/tmp/backup.dump" 2>/dev/null; then
        
        # Copy backup file from container
        docker cp "$POSTGRES_CONTAINER:/tmp/backup.dump" "$backup_file"
        
        # Compress the backup
        gzip "$backup_file"
        
        log_success "Full backup completed: $(basename "$compressed_file")"
        echo "$compressed_file"
        return 0
    else
        log_error "Full backup failed"
        return 1
    fi
}

perform_schema_backup() {
    log_info "Performing schema-only backup..."
    
    local backup_file="${BACKUP_DIR}/temp/${BACKUP_FILENAME}"
    
    if docker exec "$POSTGRES_CONTAINER" pg_dump \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --schema-only \
        --verbose \
        --no-password > "$backup_file" 2>/dev/null; then
        
        gzip "$backup_file"
        log_success "Schema backup completed: $(basename "${backup_file}.gz")"
        echo "${backup_file}.gz"
        return 0
    else
        log_error "Schema backup failed"
        return 1
    fi
}

perform_data_backup() {
    log_info "Performing data-only backup..."
    
    local backup_file="${BACKUP_DIR}/temp/${BACKUP_FILENAME}"
    
    if docker exec "$POSTGRES_CONTAINER" pg_dump \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --data-only \
        --verbose \
        --no-password > "$backup_file" 2>/dev/null; then
        
        gzip "$backup_file"
        log_success "Data backup completed: $(basename "${backup_file}.gz")"
        echo "${backup_file}.gz"
        return 0
    else
        log_error "Data backup failed"
        return 1
    fi
}

verify_backup_integrity() {
    local backup_file="$1"
    
    log_info "Verifying backup integrity..."
    
    # Check if backup file exists and is not empty
    if [ ! -f "$backup_file" ] || [ ! -s "$backup_file" ]; then
        log_error "Backup file is missing or empty"
        return 1
    fi
    
    # Check if file is properly compressed
    if [[ "$backup_file" == *.gz ]]; then
        if ! gzip -t "$backup_file" 2>/dev/null; then
            log_error "Backup file is corrupted (gzip test failed)"
            return 1
        fi
    fi
    
    # Get file size
    local file_size=$(stat -c%s "$backup_file" 2>/dev/null || echo "0")
    local file_size_human=$(format_bytes $file_size)
    
    log_success "Backup integrity verified. Size: $file_size_human"
    
    # Additional verification for custom format backups
    if [[ "$backup_file" == *.dump* ]]; then
        local temp_file="/tmp/backup_test_$(date +%s).dump"
        
        if [[ "$backup_file" == *.gz ]]; then
            gunzip -c "$backup_file" > "$temp_file"
        else
            cp "$backup_file" "$temp_file"
        fi
        
        # Test restore capability (dry run)
        if docker exec "$POSTGRES_CONTAINER" pg_restore \
            --list \
            "/tmp/$(basename "$temp_file")" >/dev/null 2>&1; then
            log_success "Backup restore capability verified"
        else
            log_warning "Backup restore test failed - backup may be incomplete"
        fi
        
        rm -f "$temp_file"
    fi
    
    return 0
}

organize_backup_by_schedule() {
    local backup_file="$1"
    local final_location=""
    
    log_info "Organizing backup by retention schedule..."
    
    # Determine backup schedule based on date
    local day_of_week=$(date +%u)  # 1=Monday, 7=Sunday
    local day_of_month=$(date +%d)
    
    if [ "$day_of_month" = "01" ]; then
        # First day of month - monthly backup
        final_location="${BACKUP_DIR}/monthly/$(basename "$backup_file")"
        log_info "Storing as monthly backup"
    elif [ "$day_of_week" = "7" ]; then
        # Sunday - weekly backup
        final_location="${BACKUP_DIR}/weekly/$(basename "$backup_file")"
        log_info "Storing as weekly backup"
    else
        # Daily backup
        final_location="${BACKUP_DIR}/daily/$(basename "$backup_file")"
        log_info "Storing as daily backup"
    fi
    
    # Move backup to final location
    mv "$backup_file" "$final_location"
    log_success "Backup moved to: $final_location"
    
    return 0
}

cleanup_old_backups() {
    log_info "Cleaning up old backups..."
    
    local cleanup_count=0
    
    # Clean daily backups older than retention period
    if [ -d "${BACKUP_DIR}/daily" ]; then
        cleanup_count=$(find "${BACKUP_DIR}/daily" -name "*.sql.gz" -type f -mtime +$RETENTION_DAILY | wc -l)
        find "${BACKUP_DIR}/daily" -name "*.sql.gz" -type f -mtime +$RETENTION_DAILY -delete
        if [ $cleanup_count -gt 0 ]; then
            log_info "Removed $cleanup_count old daily backups"
        fi
    fi
    
    # Clean weekly backups older than retention period
    if [ -d "${BACKUP_DIR}/weekly" ]; then
        cleanup_count=$(find "${BACKUP_DIR}/weekly" -name "*.sql.gz" -type f -mtime +$RETENTION_WEEKLY | wc -l)
        find "${BACKUP_DIR}/weekly" -name "*.sql.gz" -type f -mtime +$RETENTION_WEEKLY -delete
        if [ $cleanup_count -gt 0 ]; then
            log_info "Removed $cleanup_count old weekly backups"
        fi
    fi
    
    # Clean monthly backups older than retention period
    if [ -d "${BACKUP_DIR}/monthly" ]; then
        cleanup_count=$(find "${BACKUP_DIR}/monthly" -name "*.sql.gz" -type f -mtime +$RETENTION_MONTHLY | wc -l)
        find "${BACKUP_DIR}/monthly" -name "*.sql.gz" -type f -mtime +$RETENTION_MONTHLY -delete
        if [ $cleanup_count -gt 0 ]; then
            log_info "Removed $cleanup_count old monthly backups"
        fi
    fi
    
    # Clean temporary files
    find "${BACKUP_DIR}/temp" -type f -mtime +1 -delete 2>/dev/null || true
    
    log_success "Backup cleanup completed"
}

create_backup_metadata() {
    local backup_file="$1"
    local metadata_file="${backup_file%.gz}.meta"
    
    log_info "Creating backup metadata..."
    
    # Gather system and database information
    cat > "$metadata_file" << EOF
# Synthia Style Database Backup Metadata
# Generated on: $(date)

[backup_info]
environment=$ENVIRONMENT
backup_type=$BACKUP_TYPE
filename=$(basename "$backup_file")
timestamp=$TIMESTAMP
created_at=$(date -Iseconds)

[database_info]
database_name=$POSTGRES_DB
database_user=$POSTGRES_USER
container_name=$POSTGRES_CONTAINER

[file_info]
file_size=$(stat -c%s "$backup_file" 2>/dev/null || echo "unknown")
file_size_human=$(format_bytes $(stat -c%s "$backup_file" 2>/dev/null || echo "0"))
compression=gzip
checksum_md5=$(md5sum "$backup_file" | cut -d' ' -f1)

[system_info]
hostname=$(hostname)
backup_script_version=1.0
postgres_version=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT version();" 2>/dev/null | head -1 | xargs || echo "unknown")

[retention_info]
retention_type=$(basename $(dirname "$backup_file"))
daily_retention_days=$RETENTION_DAILY
weekly_retention_days=$RETENTION_WEEKLY
monthly_retention_days=$RETENTION_MONTHLY
EOF

    log_success "Backup metadata created: $(basename "$metadata_file")"
}

# =============================================================================
# NOTIFICATION FUNCTIONS
# =============================================================================

send_backup_notification() {
    local status="$1"
    local backup_file="$2"
    local details="$3"
    
    # Prepare notification message
    local message="📦 Synthia Style Database Backup: $status"
    local color="good"
    
    if [ "$status" = "FAILED" ]; then
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
                            {\"title\": \"Backup Type\", \"value\": \"$BACKUP_TYPE\", \"short\": true},
                            {\"title\": \"Filename\", \"value\": \"$(basename "$backup_file")\", \"short\": false},
                            {\"title\": \"Details\", \"value\": \"$details\", \"short\": false}
                        ]
                    }
                ]
            }" \
            "${SLACK_WEBHOOK_URL}" >/dev/null 2>&1 || true
    fi
    
    # Email notification could be added here
    log_info "Notification sent: $message"
}

# =============================================================================
# MAIN BACKUP EXECUTION
# =============================================================================

main() {
    echo "============================================================================="
    echo "📦 SYNTHIA STYLE DATABASE BACKUP"
    echo "============================================================================="
    echo "🌍 Environment: $ENVIRONMENT"
    echo "📋 Backup Type: $BACKUP_TYPE"
    echo "📁 Backup Directory: $BACKUP_DIR"
    echo "⏰ Started at: $(date)"
    echo "============================================================================="
    
    local start_time=$(date +%s)
    local backup_file=""
    
    # Create backup directory structure
    create_backup_directory
    
    # Validate database connection
    if ! validate_database_connection; then
        send_backup_notification "FAILED" "" "Database connection validation failed"
        exit 1
    fi
    
    # Estimate database size and check disk space
    log_info "Estimating database size..."
    estimate_db_size
    
    # Check available disk space (reserve 2GB for safety)
    if ! check_disk_space 2048; then
        send_backup_notification "FAILED" "" "Insufficient disk space"
        exit 1
    fi
    
    # Perform backup based on type
    case "$BACKUP_TYPE" in
        "full")
            backup_file=$(perform_full_backup)
            ;;
        "schema-only")
            backup_file=$(perform_schema_backup)
            ;;
        "data-only")
            backup_file=$(perform_data_backup)
            ;;
        *)
            log_error "Unknown backup type: $BACKUP_TYPE"
            log_error "Valid types: full, schema-only, data-only"
            exit 1
            ;;
    esac
    
    # Verify backup was created successfully
    if [ -z "$backup_file" ] || [ ! -f "$backup_file" ]; then
        send_backup_notification "FAILED" "" "Backup file creation failed"
        exit 1
    fi
    
    # Verify backup integrity
    if ! verify_backup_integrity "$backup_file"; then
        send_backup_notification "FAILED" "$backup_file" "Backup integrity verification failed"
        exit 1
    fi
    
    # Organize backup by schedule
    organize_backup_by_schedule "$backup_file"
    backup_file="${backup_file/temp/$(basename $(dirname "$backup_file"))}"
    
    # Create metadata
    create_backup_metadata "$backup_file"
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Calculate execution time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Success summary
    echo ""
    echo "============================================================================="
    echo "📊 BACKUP COMPLETION SUMMARY"
    echo "============================================================================="
    log_success "Backup completed successfully!"
    echo "📁 Backup File: $(basename "$backup_file")"
    echo "📏 File Size: $(format_bytes $(stat -c%s "$backup_file" 2>/dev/null || echo "0"))"
    echo "⏱️  Duration: ${duration} seconds"
    echo "🗂️  Backup Type: $BACKUP_TYPE"
    echo "🌍 Environment: $ENVIRONMENT"
    
    # Send success notification
    send_backup_notification "SUCCESS" "$backup_file" "Backup completed in ${duration} seconds"
    
    exit 0
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

# Validate parameters
case "$BACKUP_TYPE" in
    "full"|"schema-only"|"data-only")
        ;;
    *)
        echo "❌ Error: Invalid backup type '$BACKUP_TYPE'"
        echo "   Valid types: full, schema-only, data-only"
        exit 1
        ;;
esac

# Check dependencies
for cmd in docker gzip md5sum; do
    if ! command -v "$cmd" &> /dev/null; then
        log_error "$cmd is required but not installed"
        exit 1
    fi
done

# Change to project directory
cd "$PROJECT_DIR"

# Execute main function
main "$@"

#!/bin/bash
# =============================================================================
# SYNTHIA STYLE - PRODUCTION DEPLOYMENT SCRIPT
# =============================================================================
# Zero-downtime production deployment with rollback capability

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Default values
ENVIRONMENT="production"
SKIP_BACKUP=false
SKIP_MIGRATIONS=false
ROLLBACK=false
FORCE=false

# Function to print status messages
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Target environment (default: production)"
    echo "  -s, --skip-backup       Skip database backup"
    echo "  -m, --skip-migrations   Skip database migrations"
    echo "  -r, --rollback          Rollback to previous version"
    echo "  -f, --force             Force deployment without confirmations"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Normal production deployment"
    echo "  $0 --skip-backup                     # Deploy without backup"
    echo "  $0 --environment staging             # Deploy to staging"
    echo "  $0 --rollback                        # Rollback to previous version"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -s|--skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            -m|--skip-migrations)
                SKIP_MIGRATIONS=true
                shift
                ;;
            -r|--rollback)
                ROLLBACK=true
                shift
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE="docker compose"
    elif docker-compose --version &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        print_error "Docker Compose is not available"
        exit 1
    fi
    
    # Check if .env file exists
    if [[ ! -f "${PROJECT_ROOT}/.env" ]]; then
        print_error ".env file not found. Please create it from .env.example"
        exit 1
    fi
    
    # Check required environment variables
    source "${PROJECT_ROOT}/.env"
    
    required_vars=("POSTGRES_PASSWORD" "REDIS_PASSWORD" "JWT_SECRET_KEY" "GEMINI_API_KEY")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            print_error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    print_status "Prerequisites check passed"
}

# Confirm deployment
confirm_deployment() {
    if [[ "$FORCE" == "true" ]]; then
        return 0
    fi
    
    echo ""
    print_warning "🚀 PRODUCTION DEPLOYMENT CONFIRMATION"
    echo -e "${YELLOW}Environment: $ENVIRONMENT${NC}"
    echo -e "${YELLOW}Timestamp: $TIMESTAMP${NC}"
    echo -e "${YELLOW}Backup: $([ "$SKIP_BACKUP" == "true" ] && echo "SKIPPED" || echo "YES")${NC}"
    echo -e "${YELLOW}Migrations: $([ "$SKIP_MIGRATIONS" == "true" ] && echo "SKIPPED" || echo "YES")${NC}"
    echo ""
    
    read -p "Are you sure you want to proceed? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_info "Deployment cancelled"
        exit 0
    fi
}

# Create backup
create_backup() {
    if [[ "$SKIP_BACKUP" == "true" ]]; then
        print_warning "Skipping backup as requested"
        return 0
    fi
    
    print_info "Creating database backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Database backup
    $DOCKER_COMPOSE -f docker-compose.prod.yml exec -T postgres pg_dump \
        -U "${POSTGRES_USER:-synthia_user}" \
        -d "${POSTGRES_DB:-synthia_style_db}" \
        --clean --if-exists --verbose \
        > "${BACKUP_DIR}/database_backup_${TIMESTAMP}.sql"
    
    # Compress backup
    gzip "${BACKUP_DIR}/database_backup_${TIMESTAMP}.sql"
    
    # Create volumes backup
    docker run --rm \
        -v synthia_backend_uploads:/backup-uploads:ro \
        -v "${BACKUP_DIR}:/backup" \
        alpine tar czf "/backup/uploads_backup_${TIMESTAMP}.tar.gz" -C /backup-uploads .
    
    print_status "Backup created: database_backup_${TIMESTAMP}.sql.gz"
    print_status "Backup created: uploads_backup_${TIMESTAMP}.tar.gz"
}

# Pre-deployment health check
pre_deployment_health_check() {
    print_info "Running pre-deployment health check..."
    
    # Check if services are running
    if ! $DOCKER_COMPOSE -f docker-compose.prod.yml ps | grep -q "Up"; then
        print_warning "No running services found. This appears to be a fresh deployment."
        return 0
    fi
    
    # Check backend health
    if $DOCKER_COMPOSE -f docker-compose.prod.yml ps synthia-backend | grep -q "healthy"; then
        print_status "Backend service is healthy"
    else
        print_warning "Backend service is not healthy"
    fi
    
    # Check database connection
    if $DOCKER_COMPOSE -f docker-compose.prod.yml exec -T postgres pg_isready -U "${POSTGRES_USER:-synthia_user}" > /dev/null; then
        print_status "Database is accessible"
    else
        print_error "Database is not accessible"
        exit 1
    fi
    
    print_status "Pre-deployment health check completed"
}

# Build new images
build_images() {
    print_info "Building new images..."
    
    cd "$PROJECT_ROOT"
    
    # Build with no cache to ensure fresh build
    $DOCKER_COMPOSE -f docker-compose.prod.yml build --no-cache --parallel
    
    # Tag images with timestamp for rollback capability
    docker tag synthia-style-complete_synthia-backend:latest synthia-backend:${TIMESTAMP}
    docker tag synthia-style-complete_synthia-frontend:latest synthia-frontend:${TIMESTAMP}
    docker tag synthia-style-complete_nginx-proxy:latest synthia-nginx-proxy:${TIMESTAMP}
    
    print_status "Images built and tagged with timestamp: $TIMESTAMP"
}

# Deploy services with zero downtime
deploy_services() {
    print_info "Deploying services with zero downtime..."
    
    cd "$PROJECT_ROOT"
    
    # Deploy backend first (API services)
    print_info "Deploying backend service..."
    $DOCKER_COMPOSE -f docker-compose.prod.yml up -d --no-deps synthia-backend
    
    # Wait for backend to be healthy
    print_info "Waiting for backend to be healthy..."
    timeout=120
    counter=0
    while [ $counter -lt $timeout ]; do
        if $DOCKER_COMPOSE -f docker-compose.prod.yml ps synthia-backend | grep -q "healthy"; then
            print_status "Backend is healthy"
            break
        fi
        
        if [ $counter -eq $timeout ]; then
            print_error "Backend failed to become healthy within ${timeout}s"
            exit 1
        fi
        
        sleep 2
        counter=$((counter + 2))
    done
    
    # Deploy frontend
    print_info "Deploying frontend service..."
    $DOCKER_COMPOSE -f docker-compose.prod.yml up -d --no-deps synthia-frontend
    
    # Deploy proxy (last to ensure seamless transition)
    print_info "Deploying reverse proxy..."
    $DOCKER_COMPOSE -f docker-compose.prod.yml up -d --no-deps nginx-proxy
    
    print_status "Services deployed successfully"
}

# Run database migrations
run_migrations() {
    if [[ "$SKIP_MIGRATIONS" == "true" ]]; then
        print_warning "Skipping migrations as requested"
        return 0
    fi
    
    print_info "Running database migrations..."
    
    cd "$PROJECT_ROOT"
    
    # Run Prisma migrations
    $DOCKER_COMPOSE -f docker-compose.prod.yml exec synthia-backend npx prisma migrate deploy
    
    print_status "Database migrations completed"
}

# Post-deployment health check
post_deployment_health_check() {
    print_info "Running post-deployment health check..."
    
    cd "$PROJECT_ROOT"
    
    # Check all services
    services=("postgres" "redis" "synthia-backend" "synthia-frontend" "nginx-proxy")
    
    for service in "${services[@]}"; do
        print_info "Checking $service health..."
        
        timeout=60
        counter=0
        
        while [ $counter -lt $timeout ]; do
            if $DOCKER_COMPOSE -f docker-compose.prod.yml ps "$service" | grep -q "healthy\|Up"; then
                print_status "$service is healthy"
                break
            fi
            
            if [ $counter -eq $timeout ]; then
                print_error "$service failed health check"
                return 1
            fi
            
            sleep 2
            counter=$((counter + 2))
        done
    done
    
    # Test API endpoint
    print_info "Testing API endpoint..."
    if curl -f -s http://localhost/api/health > /dev/null; then
        print_status "API endpoint is responding"
    else
        print_error "API endpoint is not responding"
        return 1
    fi
    
    print_status "Post-deployment health check passed"
}

# Cleanup old images and containers
cleanup() {
    print_info "Cleaning up old images and containers..."
    
    # Remove old containers
    docker container prune -f
    
    # Remove old images (keep last 3 versions)
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}" | \
        grep -E "synthia-(backend|frontend|nginx-proxy)" | \
        sort -k3 -r | \
        tail -n +4 | \
        awk '{print $1":"$2}' | \
        xargs -r docker rmi || true
    
    print_status "Cleanup completed"
}

# Rollback function
rollback_deployment() {
    print_error "🔄 INITIATING ROLLBACK"
    
    # Find the previous version
    PREVIOUS_VERSION=$(docker images --format "table {{.Repository}}\t{{.Tag}}" | \
        grep "synthia-backend" | \
        grep -v "latest" | \
        sort -r | \
        head -n 1 | \
        awk '{print $2}')
    
    if [[ -z "$PREVIOUS_VERSION" ]]; then
        print_error "No previous version found for rollback"
        exit 1
    fi
    
    print_info "Rolling back to version: $PREVIOUS_VERSION"
    
    # Tag previous version as latest
    docker tag synthia-backend:${PREVIOUS_VERSION} synthia-backend:latest
    docker tag synthia-frontend:${PREVIOUS_VERSION} synthia-frontend:latest
    docker tag synthia-nginx-proxy:${PREVIOUS_VERSION} synthia-nginx-proxy:latest
    
    # Restart services with previous version
    $DOCKER_COMPOSE -f docker-compose.prod.yml up -d --force-recreate
    
    print_status "Rollback completed to version: $PREVIOUS_VERSION"
}

# Main deployment function
main() {
    cd "$PROJECT_ROOT"
    
    echo -e "${BLUE}🚀 Synthia Style - Production Deployment${NC}"
    echo -e "${BLUE}=======================================${NC}"
    
    if [[ "$ROLLBACK" == "true" ]]; then
        rollback_deployment
        exit 0
    fi
    
    check_prerequisites
    confirm_deployment
    
    # Start deployment process
    print_info "Starting deployment process..."
    
    create_backup
    pre_deployment_health_check
    build_images
    deploy_services
    run_migrations
    
    # Verify deployment
    if post_deployment_health_check; then
        cleanup
        
        echo ""
        print_status "🎉 DEPLOYMENT SUCCESSFUL!"
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}Environment: $ENVIRONMENT${NC}"
        echo -e "${GREEN}Timestamp: $TIMESTAMP${NC}"
        echo -e "${GREEN}Version: $TIMESTAMP${NC}"
        echo ""
        echo -e "${BLUE}📋 Service URLs:${NC}"
        echo -e "  🌐 Application: https://${DOMAIN:-synthia.style}"
        echo -e "  🚀 API: https://${DOMAIN:-synthia.style}/api/v1"
        echo -e "  📚 API Docs: https://${DOMAIN:-synthia.style}/api/v1/docs"
        echo ""
        echo -e "${YELLOW}💡 Useful Commands:${NC}"
        echo -e "  View logs: $DOCKER_COMPOSE -f docker-compose.prod.yml logs -f [service]"
        echo -e "  Monitor: $DOCKER_COMPOSE -f docker-compose.prod.yml --profile monitoring up -d"
        echo -e "  Rollback: $0 --rollback"
        
    else
        print_error "Deployment failed post-deployment health check"
        print_info "Initiating automatic rollback..."
        rollback_deployment
        exit 1
    fi
}

# Handle script interruption
trap 'echo -e "\n${RED}Deployment interrupted${NC}"; exit 1' INT

# Parse arguments and run main function
parse_args "$@"
main

print_status "Production deployment completed successfully! 🎉"

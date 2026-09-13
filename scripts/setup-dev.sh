#!/bin/bash
# =============================================================================
# SYNTHIA STYLE - DEVELOPMENT SETUP SCRIPT
# =============================================================================
# Automated setup for development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 Synthia Style - Development Environment Setup${NC}"
echo -e "${BLUE}=================================================${NC}"

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

# Check if Docker is installed and running
check_docker() {
    print_info "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    print_status "Docker is installed and running"
}

# Check if Docker Compose is available
check_docker_compose() {
    print_info "Checking Docker Compose..."
    
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE="docker compose"
    elif docker-compose --version &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        print_error "Docker Compose is not available"
        exit 1
    fi
    
    print_status "Docker Compose is available: $DOCKER_COMPOSE"
}

# Create .env file from template
setup_env_file() {
    print_info "Setting up environment file..."
    
    cd "$PROJECT_ROOT"
    
    if [[ ! -f .env ]]; then
        if [[ -f .env.example ]]; then
            cp .env.example .env
            print_status "Created .env file from template"
        else
            print_error ".env.example file not found"
            exit 1
        fi
    else
        print_warning ".env file already exists, skipping..."
    fi
    
    # Check if GEMINI_API_KEY is set
    if grep -q "GEMINI_API_KEY=your_gemini_api_key_here" .env 2>/dev/null; then
        print_warning "Please set your GEMINI_API_KEY in the .env file"
        print_info "Edit .env and replace 'your_gemini_api_key_here' with your actual API key"
    fi
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    
    cd "$PROJECT_ROOT"
    
    directories=(
        "backend/uploads/facial"
        "backend/uploads/temp"
        "backend/uploads/thumbnails"
        "backend/logs"
        "backups"
        "config"
        "monitoring"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
    done
    
    print_status "Created necessary directories"
}

# Build and start development services
start_services() {
    print_info "Building and starting development services..."
    
    cd "$PROJECT_ROOT"
    
    # Stop any existing services
    $DOCKER_COMPOSE -f docker-compose.dev.yml down --remove-orphans 2>/dev/null || true
    
    # Build and start services
    $DOCKER_COMPOSE -f docker-compose.dev.yml build --no-cache
    $DOCKER_COMPOSE -f docker-compose.dev.yml up -d
    
    print_status "Development services started"
}

# Wait for services to be healthy
wait_for_services() {
    print_info "Waiting for services to be healthy..."
    
    cd "$PROJECT_ROOT"
    
    # Define services to wait for
    services=("postgres" "redis" "synthia-backend")
    
    for service in "${services[@]}"; do
        print_info "Waiting for $service to be healthy..."
        
        # Wait up to 2 minutes for each service
        timeout=120
        counter=0
        
        while [ $counter -lt $timeout ]; do
            if $DOCKER_COMPOSE -f docker-compose.dev.yml ps "$service" | grep -q "healthy"; then
                print_status "$service is healthy"
                break
            fi
            
            if [ $counter -eq $timeout ]; then
                print_error "$service failed to become healthy within ${timeout}s"
                exit 1
            fi
            
            sleep 2
            counter=$((counter + 2))
        done
    done
}

# Run database migrations
run_migrations() {
    print_info "Running database migrations..."
    
    cd "$PROJECT_ROOT"
    
    # Run Prisma migrations
    $DOCKER_COMPOSE -f docker-compose.dev.yml exec synthia-backend npx prisma migrate deploy
    
    print_status "Database migrations completed"
}

# Display service URLs and information
display_info() {
    print_info "Development environment is ready! 🎉"
    echo ""
    echo -e "${BLUE}📋 Service URLs:${NC}"
    echo -e "  🌐 Frontend (React):     http://localhost:5173"
    echo -e "  🚀 Backend (FastAPI):    http://localhost:8000"
    echo -e "  📚 API Documentation:    http://localhost:8000/docs"
    echo -e "  📖 API ReDoc:            http://localhost:8000/redoc"
    echo -e "  🗄️  PostgreSQL:           localhost:5432"
    echo -e "  🔴 Redis:                localhost:6379"
    echo ""
    echo -e "${BLUE}🛠️  Optional Development Tools:${NC}"
    echo -e "  To start PgAdmin: $DOCKER_COMPOSE -f docker-compose.dev.yml --profile tools up -d pgadmin"
    echo -e "  📊 PgAdmin:              http://localhost:5050 (admin@synthia.style / admin_dev_2024)"
    echo -e "  To start Redis Commander: $DOCKER_COMPOSE -f docker-compose.dev.yml --profile tools up -d redis-commander"
    echo -e "  🔧 Redis Commander:      http://localhost:8081 (admin / admin_dev_2024)"
    echo ""
    echo -e "${BLUE}📝 Useful Commands:${NC}"
    echo -e "  View logs:     $DOCKER_COMPOSE -f docker-compose.dev.yml logs -f [service_name]"
    echo -e "  Stop services: $DOCKER_COMPOSE -f docker-compose.dev.yml down"
    echo -e "  Restart:       $DOCKER_COMPOSE -f docker-compose.dev.yml restart [service_name]"
    echo -e "  Shell access:  $DOCKER_COMPOSE -f docker-compose.dev.yml exec [service_name] sh"
    echo ""
    echo -e "${YELLOW}⚠️  Important Notes:${NC}"
    echo -e "  • Make sure to set your GEMINI_API_KEY in the .env file"
    echo -e "  • Backend has hot-reload enabled for development"
    echo -e "  • Frontend has hot-reload enabled for development"
    echo -e "  • Database data persists in Docker volumes"
    echo ""
    echo -e "${GREEN}🎯 Next Steps:${NC}"
    echo -e "  1. Edit .env file and set your GEMINI_API_KEY"
    echo -e "  2. Visit http://localhost:5173 to see the frontend"
    echo -e "  3. Visit http://localhost:8000/docs to explore the API"
    echo -e "  4. Start developing! 🚀"
}

# Main setup function
main() {
    echo -e "${BLUE}Starting development environment setup...${NC}"
    echo ""
    
    check_docker
    check_docker_compose
    setup_env_file
    create_directories
    start_services
    wait_for_services
    
    # Skip migrations if database is not ready
    if $DOCKER_COMPOSE -f docker-compose.dev.yml ps synthia-backend | grep -q "healthy"; then
        run_migrations
    else
        print_warning "Backend service not healthy, skipping migrations"
        print_info "You can run migrations later with:"
        print_info "$DOCKER_COMPOSE -f docker-compose.dev.yml exec synthia-backend npx prisma migrate deploy"
    fi
    
    display_info
}

# Handle script interruption
trap 'echo -e "\n${RED}Setup interrupted${NC}"; exit 1' INT

# Check if running from correct directory
if [[ ! -f "docker-compose.dev.yml" ]]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Run main setup
main

print_status "Development environment setup completed successfully! 🎉"

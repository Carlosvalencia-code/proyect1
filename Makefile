# =============================================================================
# SYNTHIA STYLE - MAKEFILE
# =============================================================================
# Simplified commands for development and deployment

.PHONY: help dev prod staging build test clean logs health backup restore

# Default target
.DEFAULT_GOAL := help

# Variables
DOCKER_COMPOSE := docker compose
ENVIRONMENT ?= development
BACKUP_DIR := ./backups

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

## Help
help: ## Show this help message
	@echo "$(BLUE)Synthia Style - Docker Management$(NC)"
	@echo "$(BLUE)==================================$(NC)"
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Examples:$(NC)"
	@echo "  make dev                    # Start development environment"
	@echo "  make prod                   # Deploy to production"
	@echo "  make logs service=backend   # View backend logs"
	@echo "  make health                 # Run health check"

## Development Environment
dev: ## Start development environment
	@echo "$(BLUE)🚀 Starting development environment...$(NC)"
	@chmod +x scripts/setup-dev.sh
	@./scripts/setup-dev.sh

dev-build: ## Build development environment
	@echo "$(BLUE)🔨 Building development environment...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml build

dev-up: ## Start development services (without setup)
	@echo "$(BLUE)📦 Starting development services...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d

dev-down: ## Stop development services
	@echo "$(BLUE)⏹️  Stopping development services...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

dev-restart: ## Restart development services
	@echo "$(BLUE)🔄 Restarting development services...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml restart

dev-clean: ## Clean development environment
	@echo "$(BLUE)🧹 Cleaning development environment...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml down -v --remove-orphans
	@docker system prune -f

## Production Environment
prod: ## Deploy to production
	@echo "$(BLUE)🚀 Deploying to production...$(NC)"
	@chmod +x scripts/deploy-prod.sh
	@./scripts/deploy-prod.sh

prod-build: ## Build production images
	@echo "$(BLUE)🔨 Building production images...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml build --no-cache

prod-up: ## Start production services
	@echo "$(BLUE)📦 Starting production services...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml up -d

prod-down: ## Stop production services
	@echo "$(BLUE)⏹️  Stopping production services...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml down

prod-restart: ## Restart production services
	@echo "$(BLUE)🔄 Restarting production services...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml restart

## Staging Environment
staging: ## Deploy to staging
	@echo "$(BLUE)🚀 Deploying to staging...$(NC)"
	@ENVIRONMENT=staging ./scripts/deploy-prod.sh --environment staging

staging-up: ## Start staging services
	@echo "$(BLUE)📦 Starting staging services...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml -p synthia-staging up -d

staging-down: ## Stop staging services
	@echo "$(BLUE)⏹️  Stopping staging services...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml -p synthia-staging down

## Build and Test
build: ## Build all images
	@echo "$(BLUE)🔨 Building all images...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml build
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml build

test: ## Run tests
	@echo "$(BLUE)🧪 Running tests...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec synthia-backend python -m pytest tests/ -v
	@echo "$(GREEN)✅ Tests completed$(NC)"

test-integration: ## Run integration tests
	@echo "$(BLUE)🔗 Running integration tests...$(NC)"
	@chmod +x test_integration.py
	@python test_integration.py

lint: ## Run code linting
	@echo "$(BLUE)🔍 Running code linting...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec synthia-backend black app/ --check
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec synthia-backend isort app/ --check-only
	@echo "$(GREEN)✅ Linting completed$(NC)"

format: ## Format code
	@echo "$(BLUE)🎨 Formatting code...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec synthia-backend black app/
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec synthia-backend isort app/
	@echo "$(GREEN)✅ Code formatted$(NC)"

## Monitoring and Logging
logs: ## View service logs (usage: make logs service=backend)
	@if [ -z "$(service)" ]; then \
		echo "$(YELLOW)Usage: make logs service=<service_name>$(NC)"; \
		echo "Available services: backend, frontend, postgres, redis, nginx-proxy"; \
	else \
		echo "$(BLUE)📋 Viewing logs for $(service)...$(NC)"; \
		$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f synthia-$(service); \
	fi

logs-all: ## View all service logs
	@echo "$(BLUE)📋 Viewing all service logs...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f

health: ## Run health check
	@echo "$(BLUE)🏥 Running health check...$(NC)"
	@chmod +x scripts/health-check.sh
	@./scripts/health-check.sh --environment $(ENVIRONMENT)

health-detailed: ## Run detailed health check
	@echo "$(BLUE)🏥 Running detailed health check...$(NC)"
	@chmod +x scripts/health-check.sh
	@./scripts/health-check.sh --environment $(ENVIRONMENT) --detailed

monitor: ## Start monitoring services
	@echo "$(BLUE)📊 Starting monitoring services...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml --profile monitoring up -d

## Database Operations
db-migrate: ## Run database migrations
	@echo "$(BLUE)🗄️  Running database migrations...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec synthia-backend npx prisma migrate deploy
	@echo "$(GREEN)✅ Migrations completed$(NC)"

db-reset: ## Reset database (WARNING: This will delete all data)
	@echo "$(RED)⚠️  WARNING: This will delete all database data!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec synthia-backend npx prisma migrate reset --force
	@echo "$(GREEN)✅ Database reset completed$(NC)"

db-studio: ## Open Prisma Studio
	@echo "$(BLUE)🎨 Opening Prisma Studio...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec synthia-backend npx prisma studio

db-shell: ## Connect to database shell
	@echo "$(BLUE)🐘 Connecting to database shell...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec postgres psql -U synthia_user -d synthia_style_db

## Backup and Restore
backup: ## Create database backup
	@echo "$(BLUE)💾 Creating database backup...$(NC)"
	@mkdir -p $(BACKUP_DIR)
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml exec -T postgres pg_dump \
		-U synthia_user -d synthia_style_db --clean --if-exists \
		> $(BACKUP_DIR)/backup_$(shell date +"%Y%m%d_%H%M%S").sql
	@echo "$(GREEN)✅ Backup created in $(BACKUP_DIR)$(NC)"

restore: ## Restore database from backup (usage: make restore file=backup.sql)
	@if [ -z "$(file)" ]; then \
		echo "$(YELLOW)Usage: make restore file=<backup_file>$(NC)"; \
		echo "Available backups:"; \
		ls -la $(BACKUP_DIR)/*.sql 2>/dev/null || echo "No backups found"; \
	else \
		echo "$(BLUE)🔄 Restoring database from $(file)...$(NC)"; \
		$(DOCKER_COMPOSE) -f docker-compose.prod.yml exec -T postgres psql \
			-U synthia_user -d synthia_style_db < $(BACKUP_DIR)/$(file); \
		echo "$(GREEN)✅ Database restored$(NC)"; \
	fi

## Utility Commands
shell: ## Access service shell (usage: make shell service=backend)
	@if [ -z "$(service)" ]; then \
		echo "$(YELLOW)Usage: make shell service=<service_name>$(NC)"; \
		echo "Available services: backend, frontend, postgres, redis"; \
	else \
		echo "$(BLUE)🐚 Accessing $(service) shell...$(NC)"; \
		$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec synthia-$(service) sh; \
	fi

ps: ## Show running services
	@echo "$(BLUE)📋 Running services:$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml ps

status: ## Show service status
	@echo "$(BLUE)📊 Service status:$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

clean: ## Clean up Docker resources
	@echo "$(BLUE)🧹 Cleaning up Docker resources...$(NC)"
	@docker system prune -f
	@docker volume prune -f
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

clean-all: ## Clean up all Docker resources (WARNING: This removes everything)
	@echo "$(RED)⚠️  WARNING: This will remove all Docker resources!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml down -v --remove-orphans
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml down -v --remove-orphans
	@docker system prune -a -f --volumes
	@echo "$(GREEN)✅ All resources cleaned$(NC)"

## SSL and Security
ssl-cert: ## Generate SSL certificates
	@echo "$(BLUE)🔐 Generating SSL certificates...$(NC)"
	@chmod +x docker/nginx/scripts/generate-ssl.sh
	@docker/nginx/scripts/generate-ssl.sh
	@echo "$(GREEN)✅ SSL certificates generated$(NC)"

ssl-renew: ## Renew SSL certificates (Let's Encrypt)
	@echo "$(BLUE)🔄 Renewing SSL certificates...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml --profile ssl up certbot
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml restart nginx-proxy
	@echo "$(GREEN)✅ SSL certificates renewed$(NC)"

## Development Tools
tools-up: ## Start development tools (PgAdmin, Redis Commander)
	@echo "$(BLUE)🛠️  Starting development tools...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml --profile tools up -d
	@echo "$(GREEN)📊 PgAdmin: http://localhost:5050 (admin@synthia.style / admin_dev_2024)$(NC)"
	@echo "$(GREEN)🔧 Redis Commander: http://localhost:8081 (admin / admin_dev_2024)$(NC)"

tools-down: ## Stop development tools
	@echo "$(BLUE)⏹️  Stopping development tools...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml --profile tools down

## Environment Setup
setup: ## Initial project setup
	@echo "$(BLUE)⚙️  Setting up project...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✅ Created .env file from template$(NC)"; \
		echo "$(YELLOW)⚠️  Please edit .env file and set your GEMINI_API_KEY$(NC)"; \
	fi
	@chmod +x scripts/*.sh
	@echo "$(GREEN)✅ Project setup completed$(NC)"

env-check: ## Check environment configuration
	@echo "$(BLUE)🔍 Checking environment configuration...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(RED)❌ .env file not found$(NC)"; \
		echo "$(YELLOW)Run 'make setup' to create it$(NC)"; \
		exit 1; \
	fi
	@grep -q "GEMINI_API_KEY=your_gemini_api_key_here" .env && \
		echo "$(YELLOW)⚠️  Please set your GEMINI_API_KEY in .env file$(NC)" || \
		echo "$(GREEN)✅ GEMINI_API_KEY is configured$(NC)"
	@echo "$(GREEN)✅ Environment check completed$(NC)"

## Information
info: ## Show project information
	@echo "$(BLUE)ℹ️  Synthia Style Project Information$(NC)"
	@echo "$(BLUE)====================================$(NC)"
	@echo "Project: Synthia Style - AI Style Analysis Platform"
	@echo "Version: 2.0.0"
	@echo "Architecture: FastAPI + PostgreSQL + Redis + React"
	@echo ""
	@echo "$(GREEN)Development URLs:$(NC)"
	@echo "  Frontend: http://localhost:5173"
	@echo "  Backend API: http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  PgAdmin: http://localhost:5050"
	@echo "  Redis Commander: http://localhost:8081"
	@echo ""
	@echo "$(GREEN)Production URLs:$(NC)"
	@echo "  Application: https://synthia.style"
	@echo "  API: https://synthia.style/api/v1"
	@echo "  API Docs: https://synthia.style/api/v1/docs"

version: ## Show version information
	@echo "$(BLUE)📋 Version Information$(NC)"
	@echo "$(BLUE)=====================$(NC)"
	@echo "Synthia Style: 2.0.0"
	@docker --version 2>/dev/null || echo "Docker: Not installed"
	@$(DOCKER_COMPOSE) version 2>/dev/null || echo "Docker Compose: Not installed"
	@echo "Environment: $(ENVIRONMENT)"

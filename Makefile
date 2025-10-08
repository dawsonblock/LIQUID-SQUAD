# Makefile for LIQUID HIVE 25 - Build Automation
# Provides common development and deployment tasks

.PHONY: help install dev build test lint clean docker up down logs

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip3
NPM := npm
DOCKER := docker
DOCKER_COMPOSE := docker compose
BACKEND_DIR := full_build_upgraded/full_build
GUI_DIR := full_build_upgraded/gui
DEPLOY_DIR := hive_deploy

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ Help
help: ## Display this help message
	@echo "$(BLUE)LIQUID HIVE 25 - Build Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(GREEN)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development
install: ## Install all dependencies (backend + frontend)
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@echo "$(YELLOW)Backend dependencies...$(NC)"
	cd $(BACKEND_DIR) && $(PIP) install -r requirements.txt
	@echo "$(YELLOW)Frontend dependencies...$(NC)"
	cd $(GUI_DIR) && $(NPM) install
	@echo "$(GREEN)✓ All dependencies installed$(NC)"

install-backend: ## Install backend dependencies only
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	cd $(BACKEND_DIR) && $(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"

install-frontend: ## Install frontend dependencies only
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	cd $(GUI_DIR) && $(NPM) install
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"

dev: ## Start development servers (backend + frontend)
	@echo "$(BLUE)Starting development servers...$(NC)"
	@trap 'kill 0' EXIT; \
	cd $(BACKEND_DIR) && uvicorn full_build.service.api_enhanced:app --reload --port 8000 & \
	cd $(GUI_DIR) && $(NPM) run dev

dev-backend: ## Start backend development server only
	@echo "$(BLUE)Starting backend dev server...$(NC)"
	cd $(BACKEND_DIR) && uvicorn full_build.service.api_enhanced:app --reload --port 8000

dev-frontend: ## Start frontend development server only
	@echo "$(BLUE)Starting frontend dev server...$(NC)"
	cd $(GUI_DIR) && $(NPM) run dev

##@ Building
build: build-backend build-frontend ## Build both backend and frontend for production

build-backend: ## Build backend Docker image (optimized)
	@echo "$(BLUE)Building optimized backend image...$(NC)"
	cd $(BACKEND_DIR) && $(DOCKER) build -f Dockerfile.optimized -t liquid-hive-api:latest .
	@echo "$(GREEN)✓ Backend image built$(NC)"

build-frontend: ## Build frontend Docker image (optimized)
	@echo "$(BLUE)Building optimized frontend image...$(NC)"
	cd $(GUI_DIR) && $(DOCKER) build -f Dockerfile.optimized -t liquid-hive-gui:latest .
	@echo "$(GREEN)✓ Frontend image built$(NC)"

build-dev: ## Build development Docker images (faster, unoptimized)
	@echo "$(BLUE)Building development images...$(NC)"
	cd $(BACKEND_DIR) && $(DOCKER) build -t liquid-hive-api:dev .
	cd $(GUI_DIR) && $(DOCKER) build -t liquid-hive-gui:dev .
	@echo "$(GREEN)✓ Development images built$(NC)"

##@ Testing
test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	@echo "$(BLUE)Running backend tests...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/ -v --tb=short
	@echo "$(GREEN)✓ Backend tests passed$(NC)"

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(NC)"
	cd $(GUI_DIR) && $(NPM) test
	@echo "$(GREEN)✓ Frontend tests passed$(NC)"

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/ --cov=full_build --cov-report=html --cov-report=term
	cd $(GUI_DIR) && $(NPM) run test:coverage
	@echo "$(GREEN)✓ Coverage reports generated$(NC)"

##@ Quality
lint: lint-backend lint-frontend ## Run linters on all code

lint-backend: ## Lint backend code
	@echo "$(BLUE)Linting backend...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m flake8 . --max-line-length=120 --exclude=__pycache__,venv,build,dist || true
	cd $(BACKEND_DIR) && $(PYTHON) -m mypy . --ignore-missing-imports || true
	@echo "$(GREEN)✓ Backend linting complete$(NC)"

lint-frontend: ## Lint frontend code
	@echo "$(BLUE)Linting frontend...$(NC)"
	cd $(GUI_DIR) && $(NPM) run lint
	@echo "$(GREEN)✓ Frontend linting complete$(NC)"

format: ## Format code (backend with black, frontend with prettier)
	@echo "$(BLUE)Formatting code...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m black . --line-length=120 || echo "Install black: pip install black"
	cd $(GUI_DIR) && $(NPM) run format || echo "Add format script to package.json"
	@echo "$(GREEN)✓ Code formatted$(NC)"

typecheck: ## Run type checking
	@echo "$(BLUE)Type checking...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m mypy . --ignore-missing-imports || echo "Install mypy: pip install mypy"
	cd $(GUI_DIR) && $(NPM) run type-check || npx tsc --noEmit
	@echo "$(GREEN)✓ Type checking complete$(NC)"

##@ Docker Operations
docker-build: ## Build all Docker images (production optimized)
	@echo "$(BLUE)Building all production images...$(NC)"
	$(MAKE) build
	@echo "$(GREEN)✓ All images built$(NC)"

docker-up: ## Start Docker Compose stack
	@echo "$(BLUE)Starting Docker Compose stack...$(NC)"
	cd $(DEPLOY_DIR) && $(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Stack started$(NC)"
	@echo "$(YELLOW)API: http://localhost:8000$(NC)"
	@echo "$(YELLOW)GUI: http://localhost:3000$(NC)"

docker-down: ## Stop Docker Compose stack
	@echo "$(BLUE)Stopping Docker Compose stack...$(NC)"
	cd $(DEPLOY_DIR) && $(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Stack stopped$(NC)"

docker-restart: docker-down docker-up ## Restart Docker Compose stack

docker-logs: ## View Docker Compose logs
	cd $(DEPLOY_DIR) && $(DOCKER_COMPOSE) logs -f

docker-logs-api: ## View API logs only
	cd $(DEPLOY_DIR) && $(DOCKER_COMPOSE) logs -f api

docker-logs-gui: ## View GUI logs only
	cd $(DEPLOY_DIR) && $(DOCKER_COMPOSE) logs -f gui

docker-ps: ## List running containers
	cd $(DEPLOY_DIR) && $(DOCKER_COMPOSE) ps

docker-clean: ## Remove all containers and volumes
	@echo "$(RED)Cleaning Docker resources...$(NC)"
	cd $(DEPLOY_DIR) && $(DOCKER_COMPOSE) down -v --remove-orphans
	@echo "$(GREEN)✓ Docker resources cleaned$(NC)"

##@ Deployment
deploy-prod: ## Deploy to production (build + up)
	@echo "$(BLUE)Deploying to production...$(NC)"
	$(MAKE) docker-build
	$(MAKE) docker-up
	@echo "$(GREEN)✓ Deployed to production$(NC)"

deploy-dev: ## Deploy development environment
	@echo "$(BLUE)Deploying development environment...$(NC)"
	$(MAKE) build-dev
	$(MAKE) docker-up
	@echo "$(GREEN)✓ Development environment deployed$(NC)"

##@ Database
db-migrate: ## Run database migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	@echo "$(YELLOW)Migrations not yet implemented$(NC)"

db-reset: ## Reset database
	@echo "$(RED)Resetting database...$(NC)"
	@echo "$(YELLOW)Database reset not yet implemented$(NC)"

##@ Monitoring
health: ## Check health of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@curl -s http://localhost:8000/health | jq '.' || echo "$(RED)API not responding$(NC)"
	@curl -s http://localhost:8000/ready | jq '.' || echo "$(RED)API not ready$(NC)"
	@echo "$(GREEN)✓ Health check complete$(NC)"

metrics: ## View Prometheus metrics
	@echo "$(BLUE)Fetching metrics...$(NC)"
	@curl -s http://localhost:8000/metrics | head -20
	@echo "..."
	@echo "$(YELLOW)Full metrics at http://localhost:8000/metrics$(NC)"

stats: ## View cache and conversation stats
	@echo "$(BLUE)Fetching stats...$(NC)"
	@curl -s http://localhost:8000/stats -H "Authorization: Bearer dev-token" | jq '.' || echo "$(RED)Stats not available$(NC)"

##@ Cleanup
clean: ## Clean build artifacts and caches
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -prune -o -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-docker: ## Clean Docker images and containers
	@echo "$(RED)Cleaning Docker resources...$(NC)"
	$(DOCKER) system prune -af --volumes
	@echo "$(GREEN)✓ Docker cleaned$(NC)"

clean-all: clean clean-docker ## Clean everything

##@ Utilities
version: ## Show versions of tools
	@echo "$(BLUE)Tool Versions:$(NC)"
	@echo "Python:  $$($(PYTHON) --version)"
	@echo "Node:    $$(node --version)"
	@echo "npm:     $$($(NPM) --version)"
	@echo "Docker:  $$($(DOCKER) --version)"

env-check: ## Check environment configuration
	@echo "$(BLUE)Checking environment...$(NC)"
	@echo "Backend directory: $(BACKEND_DIR)"
	@echo "GUI directory: $(GUI_DIR)"
	@echo "Deploy directory: $(DEPLOY_DIR)"
	@echo ""
	@echo "$(YELLOW)Environment Variables:$(NC)"
	@echo "NEXT_PUBLIC_API_URL: $${NEXT_PUBLIC_API_URL:-not set}"
	@echo "AUTH_TOKEN: $${AUTH_TOKEN:-not set}"
	@echo "RETRIEVAL_MODE: $${RETRIEVAL_MODE:-not set}"

docs: ## Generate documentation
	@echo "$(BLUE)Documentation available at:$(NC)"
	@echo "  - README.md"
	@echo "  - ENHANCEMENTS_COMPLETE.md"
	@echo "  - GUI_MODERNIZATION_COMPLETE.md"
	@echo "  - QUICK_START_ENHANCED.md"

##@ Quick Commands  
quick-start: install dev ## Install dependencies and start development servers

full-test: lint test ## Run linting and tests

ci: lint test build ## Run CI pipeline (lint, test, build)

.PHONY: all
all: install build test ## Install, build, and test everything

# Tomo
# Run, build, and test commands

SHELL := /bin/bash
BACKEND_DIR := backend
FRONTEND_DIR := frontend
DATA_DIR := $(BACKEND_DIR)/data

.PHONY: help setup check-setup dev dev-tmux backend frontend build test lint clean

# Default target
help: ## Show this help
	@echo "Tomo"
	@echo "================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Setup
setup: clean ## Install all dependencies (cleans first)
	@echo "Setting up backend with uv..."
	@cd $(BACKEND_DIR) && uv sync --all-extras
	@echo "Setting up frontend with bun..."
	@cd $(FRONTEND_DIR) && bun install
	@echo "Setup complete!"

check-setup: ## Check if setup is done, run if not
	@if [ ! -d "$(BACKEND_DIR)/.venv" ] || [ ! -d "$(FRONTEND_DIR)/node_modules" ]; then \
		echo "Dependencies not installed. Running setup..."; \
		$(MAKE) setup; \
	fi

# Development
dev: ## Run backend and frontend (use 'make dev' in separate terminals or with tmux)
	@echo "Starting development servers..."
	@echo ""
	@echo "Run in separate terminals:"
	@echo "  make backend   # Terminal 1"
	@echo "  make frontend  # Terminal 2"
	@echo ""
	@echo "Or use: make dev-tmux (requires tmux)"

dev-tmux: check-setup ## Run both servers in tmux split
	@if ! command -v tmux &> /dev/null; then \
		echo "Error: tmux is not installed"; \
		echo "Install with: brew install tmux"; \
		echo "Or run 'make backend' and 'make frontend' in separate terminals"; \
		exit 1; \
	fi
	@tmux new-session -d -s tomo 'make backend' \; split-window -h 'make frontend' \; attach

backend: check-setup ## Start backend server
	@echo "Starting backend on http://localhost:8000..."
	@cd $(BACKEND_DIR) && DATA_DIRECTORY="$(shell pwd)/$(DATA_DIR)" uv run python src/main.py

frontend: check-setup ## Start frontend dev server
	@echo "Starting frontend on http://localhost:5173..."
	@echo "Backend URL: http://localhost:8000/mcp"
	@cd $(FRONTEND_DIR) && VITE_MCP_SERVER_URL=http://localhost:8000/mcp bun dev

# Build
build: ## Build for production
	@echo "Building frontend..."
	@cd $(FRONTEND_DIR) && bun build
	@echo "Build complete! Output in frontend/dist/"

# Testing
test: ## Run all tests
	@$(MAKE) test-backend
	@$(MAKE) test-frontend

test-backend: ## Run backend tests
	@cd $(BACKEND_DIR) && PYTHONPATH=src uv run pytest tests/unit/ -v --no-cov

test-frontend: ## Run frontend tests
	@cd $(FRONTEND_DIR) && bun test

test-e2e: ## Run end-to-end tests (requires backend running)
	@echo "Note: E2E tests require backend running with admin user created"
	@echo "Run 'make backend' in another terminal first"
	@cd $(FRONTEND_DIR) && bun test:e2e --project=chromium

test-coverage: ## Run tests with coverage
	@cd $(BACKEND_DIR) && PYTHONPATH=src uv run pytest tests/unit/ --cov=src --cov-report=html
	@cd $(FRONTEND_DIR) && bun test:coverage

# Code Quality
backend-lint: ## Lint backend code
	@echo "Linting backend..."
	@cd $(BACKEND_DIR) && uv run ruff check src/

backend-format: ## Format backend code
	@echo "Formatting backend..."
	@cd $(BACKEND_DIR) && uv run ruff format src/

frontend-lint: ## Lint frontend code
	@echo "Linting frontend..."
	@cd $(FRONTEND_DIR) && bun lint

frontend-format: ## Format frontend code
	@echo "Formatting frontend..."
	@cd $(FRONTEND_DIR) && bun format

lint: backend-lint frontend-lint ## Run all linters

format: backend-format frontend-format ## Format all code

typecheck: ## Run type checking
	@echo "Type checking backend..."
	@cd $(BACKEND_DIR) && uv run mypy src/ || true
	@echo "Type checking frontend..."
	@cd $(FRONTEND_DIR) && bun type-check

# Cleanup
clean: ## Clean build artifacts and caches
	@echo "Cleaning..."
	@rm -rf $(BACKEND_DIR)/.pytest_cache
	@rm -rf $(BACKEND_DIR)/htmlcov
	@rm -rf $(BACKEND_DIR)/__pycache__
	@rm -rf $(FRONTEND_DIR)/dist
	@rm -rf $(FRONTEND_DIR)/coverage
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Done!"

clean-all: clean ## Clean everything including dependencies
	@rm -rf $(BACKEND_DIR)/.venv
	@rm -rf $(FRONTEND_DIR)/node_modules
	@echo "All dependencies removed. Run 'make setup' to reinstall."

# Docker
docker-dev: ## Run development environment with Docker
	docker compose -f docker-compose.dev.yml up --build

docker-dev-down: ## Stop Docker development environment
	docker compose -f docker-compose.dev.yml down

docker-prod: ## Build and run production Docker environment
	docker compose up --build -d

docker-prod-down: ## Stop production Docker environment
	docker compose down

docker-logs: ## View Docker logs
	docker compose logs -f

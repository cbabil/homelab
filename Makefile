# Homelab Assistant
# Run, build, and test commands

SHELL := /bin/bash
BACKEND_DIR := backend
FRONTEND_DIR := frontend
BACKEND_VENV := $(BACKEND_DIR)/venv
DATA_DIR := $(BACKEND_DIR)/data

.PHONY: help setup check-setup dev dev-tmux backend frontend build test lint clean

# Default target
help: ## Show this help
	@echo "Homelab Assistant"
	@echo "================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Setup
setup: clean ## Install all dependencies (cleans first)
	@echo "Setting up backend..."
	@python3 -m venv $(BACKEND_VENV)
	@cd $(BACKEND_DIR) && . venv/bin/activate && pip install -r requirements.txt
	@echo "Setting up frontend..."
	@cd $(FRONTEND_DIR) && yarn install
	@echo "Setup complete!"

check-setup: ## Check if setup is done, run if not
	@if [ ! -d "$(BACKEND_VENV)" ] || [ ! -d "$(FRONTEND_DIR)/node_modules" ]; then \
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
	@tmux new-session -d -s homelab 'make backend' \; split-window -h 'make frontend' \; attach

backend: check-setup ## Start backend server
	@echo "Starting backend on http://localhost:8000..."
	@cd $(BACKEND_DIR) && . venv/bin/activate && DATA_DIRECTORY="$(shell pwd)/$(DATA_DIR)" python src/main.py

frontend: check-setup ## Start frontend dev server
	@echo "Starting frontend on http://localhost:5173..."
	@cd $(FRONTEND_DIR) && yarn dev

# Build
build: ## Build for production
	@echo "Building frontend..."
	@cd $(FRONTEND_DIR) && yarn build
	@echo "Build complete! Output in frontend/dist/"

# Database
init-db: ## Initialize database
	@cd $(BACKEND_DIR) && . venv/bin/activate && DATA_DIRECTORY="$(shell pwd)/$(DATA_DIR)" python src/cli.py init-db

create-admin: ## Create admin user
	@cd $(BACKEND_DIR) && . venv/bin/activate && DATA_DIRECTORY="$(shell pwd)/$(DATA_DIR)" python src/cli.py create-admin

# Backup
backup: ## Export encrypted backup
	@cd $(BACKEND_DIR) && . venv/bin/activate && DATA_DIRECTORY="$(shell pwd)/$(DATA_DIR)" python src/cli.py export -o backup.enc

restore: ## Import backup (usage: make restore FILE=backup.enc)
	@cd $(BACKEND_DIR) && . venv/bin/activate && DATA_DIRECTORY="$(shell pwd)/$(DATA_DIR)" python src/cli.py import -i $(FILE)

# Testing
test: ## Run all tests
	@$(MAKE) test-backend
	@$(MAKE) test-frontend

test-backend: ## Run backend tests
	@cd $(BACKEND_DIR) && . venv/bin/activate && PYTHONPATH=src pytest tests/unit/ -v --no-cov

test-frontend: ## Run frontend tests
	@cd $(FRONTEND_DIR) && yarn test

test-e2e: ## Run end-to-end tests
	@cd $(FRONTEND_DIR) && yarn test:e2e

test-coverage: ## Run tests with coverage
	@cd $(BACKEND_DIR) && . venv/bin/activate && PYTHONPATH=src pytest tests/unit/ --cov=src --cov-report=html
	@cd $(FRONTEND_DIR) && yarn test:coverage

# Code Quality
lint: ## Run linters
	@echo "Linting backend..."
	@cd $(BACKEND_DIR) && . venv/bin/activate && python -m flake8 src/ || true
	@echo "Linting frontend..."
	@cd $(FRONTEND_DIR) && yarn lint

typecheck: ## Run type checking
	@echo "Type checking frontend..."
	@cd $(FRONTEND_DIR) && yarn type-check

format: ## Format code
	@cd $(BACKEND_DIR) && . venv/bin/activate && python -m black src/ || true
	@cd $(FRONTEND_DIR) && yarn lint --fix || true

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
	@rm -rf $(BACKEND_VENV)
	@rm -rf $(FRONTEND_DIR)/node_modules
	@echo "All dependencies removed. Run 'make setup' to reinstall."

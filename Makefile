# Homelab Assistant Test Management
#
# Provides unified commands for running tests across backend and frontend.
# Includes coverage reporting and CI-friendly test execution.

SHELL := /bin/bash

.PHONY: help test test-backend test-frontend test-coverage test-unit test-integration lint format clean \
	backend-lint backend-format backend-typecheck frontend-lint frontend-format frontend-typecheck \
	start-backend start-frontend

# Default target
help: ## Show this help message
	@echo "Homelab Assistant Test Commands"
	@echo "==============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Test Commands
test: ## Run all tests (backend + frontend)
	@echo "Running all tests..."
	$(MAKE) test-backend
	$(MAKE) test-frontend

test-backend: ## Run backend Python tests with pytest
	@echo "Running backend tests..."
	cd backend && python -m pytest -v

test-frontend: ## Run frontend TypeScript tests with Vitest
	@echo "Running frontend tests..."
	cd frontend && yarn test

test-coverage: ## Run all tests with coverage reporting
	@echo "Running tests with coverage..."
	cd backend && python -m pytest --cov=src --cov-report=html:../coverage/backend
	cd frontend && yarn test:coverage

test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	cd backend && python -m pytest tests/unit/ -v
	cd frontend && yarn test

test-integration: ## Run integration tests only
	@echo "Running integration tests..."
	cd backend && python -m pytest tests/integration/ -v
	cd frontend && yarn test:e2e

test-security: ## Run security-focused tests
	@echo "Running security tests..."
	cd backend && python -m pytest -m security -v

# Code Quality Commands
lint: ## Run linting for both backend and frontend
	@echo "Running linting..."
	$(MAKE) backend-lint
	$(MAKE) frontend-lint

format: ## Format code for both backend and frontend
	@echo "Formatting code..."
	$(MAKE) backend-format
	$(MAKE) frontend-format

typecheck: ## Run type checking
	@echo "Running type checks..."
	$(MAKE) backend-typecheck
	$(MAKE) frontend-typecheck

start-backend: ## Start the FastMCP backend server (requires backend/venv)
	@if [ ! -d "backend/venv" ]; then \
		echo "[make] Python virtual environment not found at backend/venv"; \
		echo "[make] Create one with: python -m venv backend/venv"; \
		exit 1; \
	fi
	@cd backend && . venv/bin/activate && python src/main.py

start-frontend: ## Start the frontend development server (Yarn Vite dev)
	cd frontend && yarn dev

backend-lint: ## Run backend lint checks (flake8)
	cd backend && python -m flake8 src/

backend-format: ## Format backend code (black)
	cd backend && python -m black src/

backend-typecheck: ## Run backend type checks (mypy)
	cd backend && python -m mypy src/

frontend-lint: ## Run frontend lint checks (eslint)
	cd frontend && yarn lint

frontend-format: ## Format frontend code (eslint --fix)
	cd frontend && yarn lint --fix

frontend-typecheck: ## Run frontend type checks (tsc)
	cd frontend && yarn type-check

# Utility Commands
clean: ## Clean test artifacts and cache
	@echo "Cleaning test artifacts..."
	rm -rf backend/.pytest_cache/
	rm -rf backend/__pycache__/
	rm -rf backend/htmlcov/
	rm -rf frontend/coverage/
	rm -rf coverage/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

install-deps: ## Install test dependencies
	@echo "Installing test dependencies..."
	cd backend && pip install -e ".[dev]"
	cd frontend && yarn install --frozen-lockfile

# CI/CD Commands
ci-test: ## Run tests in CI environment
	@echo "Running CI tests..."
	$(MAKE) test-coverage
	$(MAKE) lint
	$(MAKE) typecheck

ci-backend: ## Run backend CI checks
	cd backend && python -m pytest --cov=src --cov-report=xml --cov-fail-under=90

ci-frontend: ## Run frontend CI checks  
	cd frontend && yarn test:coverage && yarn lint && yarn type-check

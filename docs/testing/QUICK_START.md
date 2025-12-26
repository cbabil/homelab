# Testing Quick Start Guide

Essential commands and setup for running tests in the Homelab Assistant project.

## Prerequisites

```bash
# Install backend dependencies
cd backend && pip install -e ".[dev]"

# Install frontend dependencies  
cd frontend && npm install
```

## Quick Test Commands

### Run All Tests
```bash
# Everything
make test

# Backend only
make test-backend

# Frontend only
make test-frontend
```

### Coverage Reports
```bash
# All tests with coverage
make test-coverage

# Backend coverage
cd backend && pytest --cov=src --cov-report=html

# Frontend coverage
cd frontend && npm run test:coverage
```

### Test Types
```bash
# Unit tests only
make test-unit

# Integration tests only
make test-integration

# Security tests only
make test-security
```

### Development Workflow
```bash
# Watch mode for frontend
cd frontend && npm run test:watch

# Run specific backend test
cd backend && pytest tests/unit/test_ssh_service.py -v

# Run with debugging
cd backend && pytest --pdb tests/unit/test_encryption.py
```

## Code Quality
```bash
# Lint and format
make lint
make format

# Type checking
make typecheck
```

## Coverage Requirements
- **Backend**: 90% line coverage minimum
- **Frontend**: 80% line coverage minimum  
- **Security tests**: Must pass for all security-related code

## File Structure
- **Backend tests**: `backend/tests/{unit,integration}/`
- **Frontend tests**: `frontend/src/**/*.test.{ts,tsx}`
- **Configuration**: `backend/pyproject.toml`, `frontend/vitest.config.ts`

## CI/CD
Tests run automatically on push/PR via GitHub Actions. All quality gates must pass:
- Tests pass
- Coverage thresholds met
- Linting clean
- Type checking passes

See `docs/testing/README.md` for comprehensive testing documentation.
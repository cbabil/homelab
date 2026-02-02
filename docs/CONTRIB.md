# Development Guide

> Auto-generated from package.json, pyproject.toml, and Makefile

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd tomo
make setup

# Start development servers
make backend   # Terminal 1 - http://localhost:8000
make frontend  # Terminal 2 - http://localhost:5173
```

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend runtime |
| Yarn | 1.x | Frontend package manager |
| Make | - | Task runner |

## Available Scripts

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make setup` | Install all dependencies (cleans first) |
| `make check-setup` | Check if setup is done, run if not |
| `make dev` | Show instructions for running dev servers |
| `make dev-tmux` | Run both servers in tmux split |
| `make backend` | Start backend server |
| `make frontend` | Start frontend dev server |
| `make build` | Build for production |
| `make init-db` | Initialize database |
| `make create-admin` | Create admin user |
| `make backup` | Export encrypted backup |
| `make restore FILE=backup.enc` | Import backup |
| `make test` | Run all tests |
| `make test-backend` | Run backend tests |
| `make test-frontend` | Run frontend tests |
| `make test-e2e` | Run end-to-end tests |
| `make test-coverage` | Run tests with coverage |
| `make lint` | Run linters |
| `make typecheck` | Run type checking |
| `make format` | Format code |
| `make clean` | Clean build artifacts |
| `make clean-all` | Clean everything including dependencies |
| `make docker-dev` | Run development with Docker |
| `make docker-prod` | Build and run production Docker |

### Frontend Scripts (yarn)

| Script | Description |
|--------|-------------|
| `yarn dev` | Start Vite dev server |
| `yarn build` | Build for production (tsc + vite) |
| `yarn lint` | Run ESLint on .ts/.tsx files |
| `yarn type-check` | TypeScript type checking |
| `yarn preview` | Preview production build |
| `yarn test` | Run Vitest unit tests |
| `yarn test:ui` | Run tests with Vitest UI |
| `yarn test:coverage` | Run tests with coverage report |
| `yarn test:watch` | Run tests in watch mode |
| `yarn test:e2e` | Run Playwright E2E tests |
| `yarn test:e2e:ui` | Run E2E tests with Playwright UI |
| `yarn test:e2e:headed` | Run E2E tests in headed browser |
| `yarn test:all` | Run unit tests + E2E tests |

### Backend CLI

```bash
# Via installed package
tomo --help

# Via Python directly
cd backend && source venv/bin/activate
python src/cli.py --help
```

## Environment Setup

### Frontend (.env)

Copy `.env-default` to `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_APP_NAME` | Tomo | Application branding |
| `VITE_MCP_SERVER_URL` | /mcp | Backend connection URL |
| `VITE_USE_MOCK_DATA` | false | Enable mock data for development |
| `VITE_DEBUG_MODE` | false | Enable debug logging |

**Feature Flags:**
| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_FEATURE_SERVERS` | true | Server management |
| `VITE_FEATURE_APPLICATIONS` | true | Application management |
| `VITE_FEATURE_MARKETPLACE` | true | Marketplace access |
| `VITE_FEATURE_MONITORING` | true | Monitoring features |
| `VITE_FEATURE_DASHBOARD` | true | Dashboard page |
| `VITE_FEATURE_BACKUP` | true | Backup/restore |
| `VITE_FEATURE_DATA_RETENTION` | true | Data retention settings |

### Backend (.env)

Copy `.env-default` to `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | production | Environment (development/staging/production) |
| `APP_VERSION` | 1.0.0 | Application version |
| `DATA_DIRECTORY` | data | Database and storage location |
| `JWT_SECRET_KEY` | (required) | JWT signing key - generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `SSH_TIMEOUT` | 30 | SSH connection timeout (seconds) |
| `MAX_CONCURRENT_CONNECTIONS` | 10 | Max concurrent SSH connections |
| `ALLOWED_ORIGINS` | localhost:3000-3003 | CORS allowed origins |
| `DEBUG_MODE` | false | Enable verbose logging |

## Testing

### Unit Tests

```bash
# Backend
make test-backend
# or: cd backend && pytest tests/unit/ -v

# Frontend
make test-frontend
# or: cd frontend && yarn test
```

### E2E Tests

```bash
# Requires backend running with admin user
make backend          # Terminal 1
make create-admin     # One-time setup
make test-e2e         # Terminal 2
```

### Coverage

```bash
make test-coverage
# Reports at:
# - backend/htmlcov/index.html
# - frontend/coverage/index.html
```

## Code Quality

```bash
make lint       # Run all linters
make typecheck  # TypeScript checking
make format     # Auto-format code
```

## Docker Development

```bash
make docker-dev       # Start dev environment
make docker-dev-down  # Stop
make docker-logs      # View logs
```

---

*Last updated: 2026-01-22*

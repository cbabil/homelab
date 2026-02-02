# Development

This guide covers setting up a development environment for Tomo.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| **Python** | 3.12+ | [python.org](https://python.org) |
| **uv** | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Bun** | latest | `curl -fsSL https://bun.sh/install \| bash` |
| **Git** | any | [git-scm.com](https://git-scm.com) |

---

## Getting Started

### Clone Repository

```bash
git clone https://github.com/cbabil/tomo.git
cd tomo
```

### Install Dependencies

**Using Make:**
```bash
make setup
```

**Manually:**
```bash
# Backend
cd backend
uv sync --all-extras

# Frontend
cd ../frontend
bun install

# CLI
cd ../cli
bun install
```

---

## Project Structure

```
tomo/
├── backend/              # Python MCP server
│   ├── src/
│   │   ├── main.py       # FastMCP entry point
│   │   ├── tools/        # MCP tool implementations
│   │   ├── services/     # Business logic
│   │   ├── models/       # Pydantic models
│   │   └── lib/          # Utilities & security
│   ├── tests/
│   ├── pyproject.toml
│   └── uv.lock
│
├── frontend/             # React TypeScript SPA
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── pages/        # Route pages
│   │   ├── hooks/        # Custom hooks
│   │   ├── services/     # API clients
│   │   └── providers/    # Context providers
│   ├── package.json
│   └── bun.lock
│
├── cli/                  # Command-line interface
│   ├── src/
│   │   ├── commands/     # CLI commands
│   │   └── lib/          # MCP client
│   ├── package.json
│   └── bun.lock
│
├── agent/                # Remote server agent
│   ├── src/
│   │   ├── rpc/          # WebSocket RPC
│   │   └── collectors/   # Metrics collectors
│   ├── pyproject.toml
│   └── uv.lock
│
├── packaging/            # DEB/RPM packaging
└── docs/                 # Documentation
```

---

## Running Development Servers

### Backend

```bash
cd backend
uv run python src/main.py
```

Runs on http://localhost:8000

### Frontend

```bash
cd frontend
bun run dev
```

Runs on http://localhost:5173

### CLI

```bash
cd cli
bun run dev
```

---

## Using Make

The Makefile provides common development commands:

```bash
make setup          # Install all dependencies
make backend        # Start backend server
make frontend       # Start frontend dev server

make test           # Run all tests
make test-backend   # Backend tests only
make test-frontend  # Frontend tests only

make lint           # Lint all code
make format         # Format all code
make typecheck      # Type checking
```

---

## Environment Configuration

### Backend (.env)

```bash
# Create from template
cp backend/.env-default backend/.env
```

Key settings:
```bash
JWT_SECRET_KEY=development-secret-key-change-in-production
TOMO_MASTER_PASSWORD=development-master-password
TOMO_SALT=development-salt
DEBUG=true
LOG_LEVEL=DEBUG
```

### Frontend (.env)

```bash
cp frontend/.env-default frontend/.env
```

Key settings:
```bash
VITE_API_URL=http://localhost:8000
```

---

## Testing

### Backend Tests

```bash
cd backend

# Unit tests
uv run pytest tests/unit/ -v

# Integration tests
uv run pytest tests/integration/ -v

# With coverage
uv run pytest --cov=src --cov-report=html
```

### Frontend Tests

```bash
cd frontend

# Unit tests
bun run test

# E2E tests
bun run test:e2e

# With coverage
bun run test:coverage
```

### All Tests

```bash
make test
```

---

## Code Quality

### Linting

**Backend (Ruff):**
```bash
cd backend
uv run ruff check src/
```

**Frontend (ESLint):**
```bash
cd frontend
bun run lint
```

### Formatting

**Backend:**
```bash
cd backend
uv run ruff format src/
```

**Frontend:**
```bash
cd frontend
bun run format
```

### Type Checking

**Backend (Pyright):**
```bash
cd backend
uv run pyright
```

**Frontend (TypeScript):**
```bash
cd frontend
bun run typecheck
```

---

## Database

### Location

Development database: `backend/data/tomo.db`

### Migrations

Migrations are applied automatically on startup. To reset:

```bash
rm backend/data/tomo.db
# Restart backend
```

### Schema

See [[Architecture]] for database schema.

---

## Adding Features

### Adding a Backend Tool

1. Create tool file in `backend/src/tools/<category>/`
2. Implement MCP tool:
   ```python
   from mcp import tool

   @tool()
   async def my_tool(param: str) -> str:
       """Tool description."""
       return result
   ```
3. Add tests in `backend/tests/unit/`

### Adding a Frontend Page

1. Create page in `frontend/src/pages/`
2. Add route in `frontend/src/App.tsx`
3. Add navigation in `frontend/src/components/layout/Navigation.tsx`
4. Add tests

### Adding a CLI Command

1. Create command in `cli/src/commands/`
2. Register in `cli/src/bin/tomo.tsx`
3. Add tests

---

## Debugging

### Backend

```python
import structlog
logger = structlog.get_logger()
logger.debug("debug message", key="value")
```

Or use breakpoints:
```python
breakpoint()  # Python debugger
```

### Frontend

```typescript
console.log('debug', variable);
```

Or use React DevTools and browser debugger.

### VS Code

Launch configurations are provided in `.vscode/launch.json`:
- Python: Backend
- Chrome: Frontend
- Jest: Tests

---

## Common Issues

### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Module Not Found

```bash
# Reinstall dependencies
cd backend && uv sync --all-extras
cd frontend && bun install
```

### TypeScript Errors

```bash
# Restart TypeScript server in VS Code
Cmd/Ctrl + Shift + P > TypeScript: Restart TS Server
```

---

## Git Workflow

1. Create feature branch from `dev`:
   ```bash
   git checkout dev
   git pull
   git checkout -b feature/my-feature
   ```

2. Make changes and commit:
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

3. Run quality checks:
   ```bash
   make lint
   make test
   ```

4. Push and create PR to `dev`

### Commit Convention

```
type(scope): description

Types: feat, fix, docs, style, refactor, test, chore
```

Examples:
- `feat(auth): add password reset`
- `fix(servers): handle offline status`
- `docs(readme): update installation`

---

## Next Steps

- [[Architecture]] - System architecture
- [[API-Reference]] - API documentation
- [[Contributing]] - Contribution guidelines

<p align="center">
  <img src="assets/logo.png" alt="Tomo" width="200">
</p>

<h1 align="center">Tomo</h1>

<p align="center">
  <strong>A self-hosted platform for managing your tomo infrastructure</strong>
</p>

<p align="center">
  <a href="https://github.com/cbabil/tomo/releases/latest">
    <img src="https://img.shields.io/github/v/release/cbabil/tomo?label=release" alt="Latest Release">
  </a>
  <img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/typescript-5.0+-blue.svg" alt="TypeScript 5.0+">
  <img src="https://img.shields.io/badge/license-Proprietary-red.svg" alt="License">
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#installation">Installation</a> •
  <a href="#documentation">Documentation</a>
</p>

---

## Overview

Tomo is a web-based management platform for tomo infrastructure. Connect to remote servers via SSH, deploy Docker applications from a marketplace, monitor system health, and manage everything from a single dashboard.

<p align="center">
  <img src="assets/screenshot-dashboard.png" alt="Dashboard Screenshot" width="800">
</p>

## Features

### Server Management
- **SSH Connection Management** - Password or SSH key authentication
- **Real-time Health Monitoring** - CPU, memory, disk usage
- **Automated Provisioning** - Guided Docker and Agent installation
- **Multi-Server Support** - Manage all your servers from one place

### Application Marketplace
- **Git-based App Catalog** - Browse and deploy containerized apps
- **One-Click Deploy** - Deploy to any connected server
- **Custom Configuration** - Override environment variables and ports
- **Built-in Apps** - Portainer, Nginx Proxy Manager, Nextcloud, Jellyfin, and more

### Security
- **AES-256 Encryption** - Secure credential storage
- **JWT Authentication** - With bcrypt password hashing
- **NIST SP 800-63B Compliance** - Password policy with blocklist
- **Rate Limiting** - Brute force protection
- **Session Management** - View and revoke active sessions

### Remote Agent
- **WebSocket-based Agent** - Runs on remote servers
- **Secure Command Execution** - Allowlist-based validation
- **Token Rotation** - Automatic security token refresh
- **Docker Integration** - Container management via agent

---

## Installation

### Option 1: DEB Package (Debian/Ubuntu) - Recommended

**Requirements:** Debian 12+ or Ubuntu 22.04+

```bash
# Download latest release
wget https://github.com/cbabil/tomo/releases/latest/download/tomo_1.0.0-1_amd64.deb

# Install (automatically installs dependencies)
sudo apt install ./tomo_1.0.0-1_amd64.deb

# Start service
sudo systemctl start tomo

# Launch CLI and run /admin create to set up admin account
tomo

# Access web UI
open http://localhost
```

The package installs Python, Node.js, Nginx, and all dependencies automatically.

### Option 2: Docker

**Requirements:** Docker and Docker Compose

```bash
git clone https://github.com/cbabil/tomo.git
cd tomo
docker compose up -d
```

### Option 3: From Source (Development)

**Requirements:**

| Tool | Version | Install |
|------|---------|---------|
| **Python** | 3.12+ | [python.org](https://python.org) |
| **uv** | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Bun** | latest | `curl -fsSL https://bun.sh/install \| bash` |
| **Git** | any | [git-scm.com](https://git-scm.com) |

```bash
# Clone repository
git clone https://github.com/cbabil/tomo.git
cd tomo

# Backend
cd backend
uv sync --all-extras

# Frontend (new terminal)
cd frontend
bun install
bun run dev

# Start backend
cd backend
uv run python src/main.py
```

Access the application at **http://localhost:5173**

### Using Make (Development)

```bash
make setup      # Install all dependencies
make backend    # Start backend server
make frontend   # Start frontend dev server
make test       # Run all tests
```

See [Installation Guide](docs/INSTALLATION.md) for detailed instructions.

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
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/             # React TypeScript SPA
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── pages/        # Route pages
│   │   ├── hooks/        # Custom hooks
│   │   ├── services/     # API clients
│   │   └── providers/    # Context providers
│   ├── package.json
│   └── bun.lock
├── cli/                  # Command-line interface
│   ├── src/
│   │   ├── app/          # Interactive TUI (React Ink)
│   │   ├── bin/          # CLI entry point
│   │   ├── components/   # Shared UI components
│   │   ├── hooks/        # React hooks
│   │   └── lib/          # MCP client, auth, utilities
│   ├── package.json
│   └── bun.lock
├── agent/                # Remote server agent
│   ├── src/
│   │   ├── rpc/          # WebSocket RPC
│   │   └── collectors/   # Metrics collectors
│   ├── pyproject.toml
│   └── uv.lock
├── packaging/            # DEB/RPM packaging
└── docs/                 # Documentation
```

---

## Technology Stack

| Component | Technologies |
|-----------|-------------|
| **Backend** | Python 3.12, FastMCP, SQLite, Paramiko |
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS |
| **CLI** | TypeScript, Ink (React for CLI) |
| **Agent** | Python, WebSockets, Docker SDK |
| **Package Managers** | uv (Python), Bun (JavaScript) |
| **Protocol** | Model Context Protocol (MCP) |

---

## CLI Commands

```bash
# Launch interactive TUI
tomo
tomo -m <url>                  # With custom MCP server URL
tomo --version                 # Show version
```

All management commands are entered as slash commands inside the interactive TUI:

```
/help                          Show available commands
/status                        Show connection status
/login                         Authenticate as admin
/logout                        Clear authentication
/view <tab>                    Switch view (dashboard|agents|logs|settings)
/refresh                       Force data refresh

/agent list|status|ping|rotate|install <server>
/server list
/update                        Check for updates
/security list-locked|unlock <id>
/backup export [path]          Export encrypted backup
/backup import <path>          Import backup from file
/user reset-password <user>    Reset a user's password
/admin create                  Initial admin setup
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Installation Guide](docs/INSTALLATION.md) | Detailed installation instructions |
| [CLI Reference](docs/CLI_REFERENCE.md) | All CLI commands |
| [Environment Variables](docs/ENV_REFERENCE.md) | Configuration options |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues & solutions |
| [MCP Tools Reference](docs/MCP_TOOLS_REFERENCE.md) | API documentation |

---

## Development

### Running Tests

```bash
# Backend
cd backend
uv run pytest tests/unit/ -v

# Frontend
cd frontend
bun run test
bun run test:e2e

# CLI
cd cli
bun run test

# All tests
make test
```

### Code Quality

```bash
# Lint
make backend-lint    # Ruff
make frontend-lint   # ESLint

# Format
make backend-format  # Ruff
make frontend-format # Prettier

# Type check
make typecheck
```

---

## Security

- **Encryption**: AES-256 for credentials, PBKDF2 for backups
- **Authentication**: JWT with bcrypt (cost 12)
- **Password Policy**: NIST SP 800-63B compliant with blocklist
- **Session Security**: HttpOnly cookies, CSRF protection
- **Rate Limiting**: Brute force protection on auth endpoints
- **Audit Logging**: All operations logged with sanitization

---

## License

**Proprietary** - All rights reserved.

See [LICENSE](LICENSE) for details. For licensing inquiries, contact christophe@babilotte.com.

---

<p align="center">
  <strong>Tomo</strong> • Built by <a href="https://github.com/cbabil">Christophe Babilotte</a>
</p>

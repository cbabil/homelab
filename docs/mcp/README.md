# Tomo MCP Server Backend

The Tomo MCP Server is a Python-based FastMCP server that provides comprehensive tomo management and automation capabilities. It enables remote server management, Docker orchestration, application deployment, and system monitoring through a model-driven architecture.

## Overview

The backend is built on [FastMCP](https://github.com/jlowin/fastmcp), a Python framework for creating Model Context Protocol (MCP) servers. It provides 50+ tools organized into functional modules, with automatic tool discovery and dependency injection.

### Key Features

- **Server Management**: SSH-based remote server connection and management
- **Docker Orchestration**: Install, update, and manage Docker on remote servers
- **Application Deployment**: Deploy, manage, and monitor containerized applications
- **Marketplace Integration**: Browse and sync application repositories
- **System Monitoring**: Collect metrics from servers and containers
- **User Authentication**: JWT-based authentication with session management
- **Backup & Restore**: Encrypted backup and restore of system data
- **Settings Management**: User and system-level configuration management
- **Audit Logging**: Comprehensive activity and security event logging

## Quick Start

### Prerequisites

- Python 3.9+
- Virtual environment (recommended)

### Installation

```bash
# Clone the repository
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (copy .env_example to .env)
cp .env_example .env
# Edit .env with your configuration
```

### Configuration

Create a `.env` file in the backend directory with the following variables:

```bash
# Security (Required)
JWT_SECRET_KEY=your-secret-key-here
TOMO_MASTER_PASSWORD=your-master-password
TOMO_SALT=your-salt-value

# Application Settings
DATA_DIRECTORY=data
APP_ENV=production
VERSION=0.1.0

# SSH Configuration
SSH_TIMEOUT=30
MAX_CONCURRENT_CONNECTIONS=10

# Logging
MCP_LOG_LEVEL=INFO

# CORS (comma-separated origins)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Running the Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run the server
python src/main.py
```

The server will start on `http://0.0.0.0:8000` by default.

## Project Structure

```
backend/
├── src/
│   ├── main.py                 # FastMCP server entry point
│   ├── tools/                  # MCP tool modules (auto-discovered)
│   │   ├── app/               # Application deployment tools
│   │   ├── audit/             # Audit trail tools
│   │   ├── auth/              # Authentication tools
│   │   ├── backup/            # Backup and restore tools
│   │   ├── docker/            # Docker management tools
│   │   ├── health/            # Health check tools
│   │   ├── logs/              # Log management tools
│   │   ├── marketplace/       # Marketplace tools
│   │   ├── monitoring/        # System monitoring tools
│   │   ├── server/            # Server management tools
│   │   ├── settings/          # Settings management tools
│   │   └── common.py          # Shared utilities
│   ├── services/              # Business logic services
│   │   ├── app_service.py
│   │   ├── auth_service.py
│   │   ├── backup_service.py
│   │   ├── database_service.py
│   │   ├── deployment.py
│   │   ├── marketplace_service.py
│   │   ├── metrics_service.py
│   │   ├── monitoring_service.py
│   │   ├── server_service.py
│   │   ├── settings_service.py
│   │   └── ssh_service.py
│   ├── models/                # Pydantic data models
│   │   ├── app.py
│   │   ├── server.py
│   │   ├── marketplace.py
│   │   ├── metrics.py
│   │   ├── settings.py
│   │   └── log.py
│   ├── lib/                   # Shared libraries and utilities
│   │   ├── tool_loader.py    # Automatic tool discovery
│   │   ├── config.py         # Configuration management
│   │   ├── encryption.py     # Credential encryption
│   │   ├── logging_config.py # Structured logging setup
│   │   └── security.py       # Input validation
│   ├── database/             # Database connection management
│   │   ├── connection.py     # SQLite connection manager
│   │   └── migrations/       # Database migrations
│   └── init_db/              # Database schema initialization
│       ├── schema_servers.py
│       ├── schema_apps.py
│       └── schema_users.py
├── tests/                    # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── security/            # Security tests
├── data/                    # Runtime data (created on first run)
│   ├── tomo.db          # SQLite database
│   └── marketplace/        # Marketplace repositories
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Project configuration
└── README.md               # Quick start guide
```

## Architecture

The backend follows a layered architecture:

1. **MCP Tools Layer**: Exposes functionality as MCP tools (auto-discovered)
2. **Services Layer**: Implements business logic and orchestration
3. **Models Layer**: Defines data structures and validation (Pydantic)
4. **Database Layer**: Manages data persistence (SQLite)
5. **Infrastructure Layer**: SSH connections, encryption, logging

See [Architecture Documentation](./architecture.md) for detailed information.

## Tool Auto-Discovery

The backend uses an automatic tool discovery system that scans the `tools/` directory and registers all tools without manual configuration.

### How It Works

1. Each tool module is a subdirectory under `tools/` (e.g., `tools/server/`)
2. Each module contains a `tools.py` file with a `*Tools` class (e.g., `ServerTools`)
3. The `*Tools` class constructor declares its dependencies as parameters
4. All public async methods become MCP tools automatically
5. Dependencies are injected at initialization time

See [Architecture Documentation](./architecture.md#tool-auto-discovery) for details.

## Available Tools

The backend provides 52+ MCP tools across 11 modules:

| Module | Tool Count | Description |
|--------|-----------|-------------|
| **app** | 13 | Application deployment and lifecycle management |
| **audit** | 2 | Settings and authentication audit trails |
| **auth** | 3 | User authentication and session management |
| **backup** | 2 | System backup and restore |
| **docker** | 4 | Docker installation and management |
| **health** | 1 | Server health checks |
| **logs** | 3 | Log retrieval and management |
| **marketplace** | 11 | Marketplace repository and app management |
| **monitoring** | 5 | System, server, and application metrics |
| **server** | 6 | Server connection and management |
| **settings** | 2 | User and system settings |

See [Tools Reference](./tools.md) for complete tool documentation.

## Database Schema

The backend uses SQLite for data persistence with the following main tables:

- **users**: User accounts and authentication
- **servers**: Remote server definitions and credentials (encrypted)
- **installations**: Application deployment records
- **marketplace_repos**: Marketplace repository configurations
- **marketplace_apps**: Available applications catalog
- **settings**: User and system settings
- **logs**: System and application logs
- **activities**: Audit trail of user and system events
- **metrics**: Server and container performance metrics

Credentials are encrypted using Fernet symmetric encryption with a master password.

## Development

### Adding a New Tool Module

1. Create a new directory under `src/tools/` (e.g., `src/tools/mytool/`)
2. Create `__init__.py` and `tools.py` files
3. Define a `*Tools` class in `tools.py`:

```python
# src/tools/mytool/tools.py
import structlog
from services.my_service import MyService

logger = structlog.get_logger("mytool")

class MyTool:
    """My custom tool."""

    def __init__(self, my_service: MyService):
        """Initialize with dependencies."""
        self.my_service = my_service
        logger.info("My tool initialized")

    async def my_operation(self, param: str) -> dict:
        """Perform my custom operation."""
        result = await self.my_service.do_something(param)
        return {
            "success": True,
            "data": result,
            "message": "Operation completed"
        }
```

4. Register the service dependency in `src/main.py`:

```python
# Add to main.py
from services.my_service import MyService

my_service = MyService()

tool_dependencies = {
    # ... existing dependencies ...
    "my_service": my_service,
}
```

5. The tool will be auto-discovered and registered on server startup

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/security/ -v
```

### Logging

The backend uses structured logging with `structlog`:

```python
import structlog

logger = structlog.get_logger("module_name")

logger.info("Operation completed", user_id=user_id, count=5)
logger.error("Operation failed", error=str(e))
```

Logs are output to stdout in JSON format for easy parsing.

## Security Considerations

### Credential Encryption

All server credentials (passwords and private keys) are encrypted at rest using Fernet symmetric encryption:

- Master password and salt configured via environment variables
- Credentials encrypted before storing in database
- Decrypted only when needed for SSH connections

### JWT Authentication

User authentication uses JWT tokens with:

- Configurable expiration time
- Secure token signing with secret key
- Session tracking and revocation

### Input Validation

All user inputs are validated using:

- Pydantic models for type checking and validation
- Custom validators for security-sensitive inputs (IP addresses, ports)
- SQL injection prevention through parameterized queries

### SSH Security

SSH connections use:

- Paramiko for SSH client implementation
- Support for password and key-based authentication
- Connection timeout limits
- Concurrent connection limits

## Troubleshooting

### Database Initialization

If the database is corrupted or needs reset:

```bash
# Backup existing database
mv data/tomo.db data/tomo.db.backup

# Restart server to initialize new database
python src/main.py
```

### SSH Connection Issues

Check the following:

- Server is reachable on the network
- SSH port is correct (default: 22)
- Credentials are correct
- User has appropriate permissions
- Firewall allows SSH connections

### Docker Installation Failures

Common issues:

- Unsupported OS type (supported: Ubuntu, Debian, RHEL, Fedora, Alpine, Arch)
- Insufficient permissions (user needs sudo)
- Network connectivity issues
- Package repository problems

## API Reference

For detailed API documentation, see:

- [Tools Reference](./tools.md) - Complete tool documentation
- [Architecture](./architecture.md) - System design and patterns

## Contributing

When contributing to the backend:

1. Follow the existing code structure and patterns
2. Add tests for new functionality
3. Use type hints for all function parameters and return values
4. Document public APIs with docstrings
5. Use structured logging for all log statements
6. Validate all user inputs with Pydantic models

## License

See the project root LICENSE file for details.

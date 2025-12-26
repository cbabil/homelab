# Homelab Assistant Backend MCP Server

A comprehensive FastMCP-based server for homelab management and automation.

## Overview

This backend implements a complete Model Context Protocol (MCP) server using FastMCP that provides:
- Application marketplace management
- Server connection and monitoring
- Authentication and session management
- System health and metrics monitoring
- Comprehensive logging and observability

## Architecture

### Core Components

- **FastMCP Server**: Main MCP server implementation
- **Services Layer**: Business logic and data access
- **Tools Layer**: MCP tool endpoints
- **Models Layer**: Pydantic data models
- **Utils Layer**: Helper utilities and common functions

### Key Features

- **100% Compliance**: All files under 100 lines (Rule 2)
- **Full Test Coverage**: Comprehensive unit and integration tests
- **Security-First**: JWT authentication, password hashing, secure sessions
- **Type Safety**: Full TypeScript/Python type definitions
- **Monitoring**: System metrics, logs, health checks
- **Scalable**: Service-oriented architecture with clear separation

## Installation

1. Activate virtual environment:
```bash
source venv/bin/activate && source env/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run server:
```bash
python src/main.py
```

## API Endpoints

### Authentication Tools
- `login`: User authentication with JWT tokens
- `logout`: Session invalidation
- `validate_token`: JWT token validation

### Application Tools
- `search_apps`: Search marketplace applications
- `get_app_details`: Get detailed application information
- `install_app`: Install applications (via service layer)

### Server Tools
- `add_server`: Add new server connections
- `test_connection`: Test server connectivity
- `get_servers`: List all configured servers

### Monitoring Tools
- `get_system_metrics`: Real-time system metrics
- `get_logs`: Filtered system and application logs

### Health Tools
- `get_health_status`: Comprehensive server health
- `ping`: Basic connectivity test

## Security Features

- JWT-based authentication with configurable expiry
- bcrypt password hashing with salt
- Session management with activity tracking
- Input validation with Pydantic models
- Structured logging for security events

## Testing

Run comprehensive test suite:
```bash
pytest tests/ -v
```

Test categories:
- Unit tests (`@pytest.mark.unit`)
- Integration tests (`@pytest.mark.integration`)  
- Security tests (`@pytest.mark.security`)

## Configuration

Default configuration includes:
- JWT secret key (configurable)
- Token expiry: 24 hours
- Default admin user: `admin/admin123`
- Logging: structured with structlog

## Development

All code follows mandatory project rules:
1. Comprehensive testing and documentation
2. 100-line file and function limits
3. Specialized agent usage for development
4. Security review for authentication components

## Production Deployment

For production deployment:
1. Configure secure JWT secrets
2. Use external databases for user/session storage
3. Enable HTTPS/TLS
4. Configure proper logging and monitoring
5. Set up backup and disaster recovery
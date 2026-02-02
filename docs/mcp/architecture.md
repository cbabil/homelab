# Backend Architecture

This document describes the architecture, design patterns, and technical implementation of the Tomo MCP Server backend.

## Table of Contents

- [Overview](#overview)
- [Layered Architecture](#layered-architecture)
- [Tool Auto-Discovery System](#tool-auto-discovery-system)
- [Code Organization](#code-organization)
- [Services Layer](#services-layer)
- [Data Models](#data-models)
- [Database Design](#database-design)
- [Security Architecture](#security-architecture)
- [Dependency Injection](#dependency-injection)
- [Error Handling](#error-handling)
- [Logging Strategy](#logging-strategy)
- [Testing Strategy](#testing-strategy)

## Overview

The Tomo MCP Server is built on FastMCP, a Python framework for creating Model Context Protocol servers. The architecture follows clean architecture principles with clear separation of concerns across multiple layers.

### Technology Stack

- **Framework**: FastMCP (MCP protocol implementation)
- **Language**: Python 3.9+
- **Database**: SQLite with async support
- **SSH Client**: Paramiko
- **Encryption**: Cryptography (Fernet)
- **Validation**: Pydantic
- **Logging**: Structlog
- **Testing**: pytest

### Design Principles

1. **Modularity**: Each functional area is a self-contained module
2. **Auto-Discovery**: Tools are discovered and registered automatically
3. **Dependency Injection**: Services are injected via constructor parameters
4. **Type Safety**: All functions use type hints and Pydantic models
5. **Structured Logging**: All logs are structured for easy parsing
6. **Testability**: Clear boundaries enable comprehensive testing

## Layered Architecture

The backend follows a 5-layer architecture:

```
┌─────────────────────────────────────────────────┐
│            MCP Tools Layer                      │
│  (Auto-discovered from tools/ directory)        │
│  - App Tools    - Server Tools                  │
│  - Auth Tools   - Marketplace Tools             │
│  - Docker Tools - Monitoring Tools              │
└─────────────────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────┐
│           Services Layer                        │
│  (Business logic and orchestration)             │
│  - AppService    - ServerService                │
│  - AuthService   - DeploymentService            │
│  - SSHService    - MarketplaceService           │
└─────────────────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────┐
│            Models Layer                         │
│  (Pydantic models for validation)               │
│  - Server  - App  - Marketplace                 │
│  - User    - Settings  - Metrics                │
└─────────────────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────┐
│          Database Layer                         │
│  (SQLite with connection pooling)               │
│  - DatabaseService  - ConnectionManager         │
└─────────────────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────┐
│        Infrastructure Layer                     │
│  - SSH Client   - Encryption                    │
│  - Logging      - Configuration                 │
└─────────────────────────────────────────────────┘
```

### Layer Responsibilities

**1. MCP Tools Layer**
- Exposes functionality as MCP tools
- Validates input parameters
- Formats responses consistently
- Delegates to services for business logic

**2. Services Layer**
- Implements business logic
- Orchestrates operations across multiple resources
- Manages transactions and error handling
- Enforces business rules

**3. Models Layer**
- Defines data structures
- Validates data with Pydantic
- Provides serialization/deserialization
- Enforces type constraints

**4. Database Layer**
- Manages data persistence
- Provides query interfaces
- Handles migrations
- Manages connections

**5. Infrastructure Layer**
- Provides cross-cutting concerns
- Implements technical capabilities
- No business logic

## Tool Auto-Discovery System

The auto-discovery system eliminates manual tool registration and reduces boilerplate code.

### How It Works

```python
# src/lib/tool_loader.py

def register_all_tools(app, config, dependencies):
    """Discover and register all tool packages."""

    # 1. Scan tools/ directory for subdirectories
    tools_path = resolve_tools_path(config.get("tools_directory"))
    package_names = discover_tool_packages(tools_path)

    # 2. For each package, import tools.py module
    for package_name in package_names:
        module = importlib.import_module(f"tools.{package_name}.tools")

        # 3. Find *Tools class in module
        class_name, cls = find_tools_class(module)

        # 4. Instantiate with dependencies from constructor
        instance = instantiate_tools_class(cls, class_name, dependencies)

        # 5. Register all public methods as MCP tools
        for method_name, method in get_public_methods(instance):
            app.tool(method)
```

### Directory Structure Convention

```
tools/
├── __init__.py
├── common.py              # Shared utilities
├── app/
│   ├── __init__.py
│   └── tools.py          # Contains AppTools class
├── server/
│   ├── __init__.py
│   └── tools.py          # Contains ServerTools class
└── auth/
    ├── __init__.py
    └── tools.py          # Contains AuthTools class
```

### Tool Class Convention

```python
# src/tools/server/tools.py

import structlog
from services.ssh_service import SSHService
from services.server_service import ServerService

logger = structlog.get_logger("server_tools")

class ServerTools:
    """Server management tools."""

    def __init__(self, ssh_service: SSHService, server_service: ServerService):
        """Initialize with service dependencies."""
        self.ssh_service = ssh_service
        self.server_service = server_service
        logger.info("Server tools initialized")

    async def add_server(self, name: str, host: str, port: int) -> dict:
        """Add a new server."""
        # This method becomes an MCP tool automatically
        server = await self.server_service.add_server(name, host, port)
        return {
            "success": True,
            "data": server.model_dump(),
            "message": "Server added"
        }

    def _private_helper(self):
        """Private methods (starting with _) are NOT registered."""
        pass
```

### Dependency Resolution

Dependencies are resolved by matching constructor parameter names:

```python
# src/main.py

# 1. Initialize services
auth_service = AuthService(db_service=database_service)
ssh_service = SSHService()
server_service = ServerService(db_service=database_service)

# 2. Create dependency mapping
tool_dependencies = {
    "auth_service": auth_service,
    "ssh_service": ssh_service,
    "server_service": server_service,
    # ... more services
}

# 3. Auto-discovery matches parameter names to services
register_all_tools(app, config, tool_dependencies)
```

### Benefits

- **No Boilerplate**: No manual registration code
- **Type Safe**: Constructor parameters are checked
- **Discoverable**: New tools added by creating a directory
- **Testable**: Easy to mock dependencies
- **Maintainable**: Clear dependency graph

## Code Organization

### Directory Structure

```
backend/src/
├── main.py                    # Entry point, service initialization
├── tools/                     # MCP tools (auto-discovered)
│   ├── __init__.py
│   ├── common.py             # Shared log_event function
│   ├── app/                  # Application tools
│   │   ├── __init__.py
│   │   └── tools.py          # AppTools class
│   ├── auth/                 # Authentication tools
│   │   ├── __init__.py
│   │   ├── tools.py          # AuthTools class
│   │   └── login_tool.py     # Login implementation
│   ├── server/               # Server management tools
│   ├── docker/               # Docker tools
│   ├── marketplace/          # Marketplace tools
│   ├── monitoring/           # Monitoring tools
│   ├── backup/               # Backup tools
│   ├── health/               # Health check tools
│   ├── logs/                 # Log management tools
│   └── settings/             # Settings tools
├── services/                  # Business logic services
│   ├── app_service.py        # App catalog and search
│   ├── auth_service.py       # Authentication and JWT
│   ├── backup_service.py     # Backup/restore operations
│   ├── database_service.py   # Database operations
│   ├── deployment.py         # App deployment orchestration
│   ├── marketplace_service.py# Marketplace management
│   ├── metrics_service.py    # Metrics collection
│   ├── monitoring_service.py # System monitoring
│   ├── server_service.py     # Server CRUD operations
│   ├── settings_service.py   # Settings management
│   ├── ssh_service.py        # SSH client wrapper
│   ├── activity_service.py   # Activity logging
│   ├── dashboard_service.py  # Dashboard data
│   ├── preparation_service.py# Server preparation
│   └── service_log.py        # Logging service
├── models/                    # Pydantic models
│   ├── app.py                # Application models
│   ├── server.py             # Server models
│   ├── marketplace.py        # Marketplace models
│   ├── metrics.py            # Metrics models
│   ├── settings.py           # Settings models
│   ├── log.py                # Log models
│   └── user.py               # User models
├── lib/                       # Shared libraries
│   ├── tool_loader.py        # Auto-discovery system
│   ├── config.py             # Configuration loader
│   ├── encryption.py         # Fernet encryption
│   ├── logging_config.py     # Structured logging
│   └── security.py           # Input validation
├── database/                  # Database layer
│   ├── __init__.py
│   ├── connection.py         # Connection manager
│   └── migrations/           # Schema migrations
└── init_db/                   # Schema initialization
    ├── schema_servers.py     # Server tables
    ├── schema_apps.py        # App tables
    ├── schema_users.py       # User tables
    └── schema_settings.py    # Settings tables
```

### File Naming Conventions

- **Tools**: `tools/<module>/tools.py` with `<Module>Tools` class
- **Services**: `services/<name>_service.py` with `<Name>Service` class
- **Models**: `models/<name>.py` with model classes
- **Tests**: `tests/unit/tools/test_<module>.py`

## Services Layer

Services implement business logic and orchestrate operations.

### Service Structure

```python
# src/services/server_service.py

import structlog
from typing import List, Optional, Dict, Any
from models.server import Server, ServerStatus, AuthType
from database.connection import db_manager

logger = structlog.get_logger("server_service")

class ServerService:
    """Server management service."""

    def __init__(self, db_service):
        """Initialize with database service."""
        self.db_service = db_service
        logger.info("Server service initialized")

    async def add_server(
        self,
        server_id: str,
        name: str,
        host: str,
        port: int,
        username: str,
        auth_type: str,
        credentials: Dict[str, Any]
    ) -> Optional[Server]:
        """Add a new server with encrypted credentials."""
        try:
            # Encrypt credentials before storage
            encrypted_creds = self._encrypt_credentials(credentials)

            # Insert into database
            conn = await db_manager.get_connection()
            cursor = await conn.execute(
                """
                INSERT INTO servers (id, name, host, port, username, auth_type, credentials)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (server_id, name, host, port, username, auth_type, encrypted_creds)
            )
            await conn.commit()

            # Return server object
            return await self.get_server(server_id)

        except Exception as e:
            logger.error("Add server failed", error=str(e))
            return None

    async def get_server(self, server_id: str) -> Optional[Server]:
        """Get server by ID."""
        conn = await db_manager.get_connection()
        cursor = await conn.execute(
            "SELECT * FROM servers WHERE id = ?",
            (server_id,)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return Server.from_db_row(row)

    async def update_server_status(
        self,
        server_id: str,
        status: ServerStatus
    ) -> bool:
        """Update server status."""
        try:
            conn = await db_manager.get_connection()
            await conn.execute(
                "UPDATE servers SET status = ? WHERE id = ?",
                (status.value, server_id)
            )
            await conn.commit()
            return True
        except Exception as e:
            logger.error("Update status failed", error=str(e))
            return False
```

### Service Responsibilities

1. **Business Logic**: Implement domain rules
2. **Orchestration**: Coordinate multiple operations
3. **Transaction Management**: Ensure data consistency
4. **Error Handling**: Handle and log errors
5. **Validation**: Validate business rules (Pydantic handles schema)

### Common Service Patterns

**Pattern 1: CRUD Operations**
```python
async def create_entity(self, data): ...
async def get_entity(self, id): ...
async def update_entity(self, id, data): ...
async def delete_entity(self, id): ...
```

**Pattern 2: Complex Orchestration**
```python
async def deploy_app(self, server_id, app_id, config):
    # 1. Validate configuration
    # 2. Prepare server
    # 3. Pull Docker image
    # 4. Create container
    # 5. Update database
    # 6. Log activity
```

**Pattern 3: Data Aggregation**
```python
async def get_dashboard_summary(self):
    # Aggregate data from multiple sources
    servers = await self.get_all_servers()
    apps = await self.get_all_installations()
    metrics = await self.get_latest_metrics()
    return DashboardSummary(...)
```

## Data Models

All data structures are defined as Pydantic models.

### Model Structure

```python
# src/models/server.py

from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum
from datetime import datetime

class ServerStatus(str, Enum):
    """Server connection status."""
    IDLE = "idle"
    CONNECTED = "connected"
    PREPARING = "preparing"
    ERROR = "error"

class AuthType(str, Enum):
    """Authentication type."""
    PASSWORD = "password"
    KEY = "key"

class SystemInfo(BaseModel):
    """System information."""
    os: str
    hostname: str
    architecture: str
    docker_version: Optional[str] = None
    docker_compose_version: Optional[str] = None

class Server(BaseModel):
    """Server model."""
    id: str
    name: str
    host: str
    port: int = 22
    username: str
    auth_type: AuthType
    status: ServerStatus = ServerStatus.IDLE
    docker_installed: bool = False
    system_info: Optional[SystemInfo] = None
    created_at: datetime
    updated_at: datetime

    @validator('port')
    def validate_port(cls, v):
        """Validate port range."""
        if not 1 <= v <= 65535:
            raise ValueError('Port must be 1-65535')
        return v

    @validator('host')
    def validate_host(cls, v):
        """Validate hostname/IP."""
        if not v or not v.strip():
            raise ValueError('Host is required')
        return v.strip()

    class Config:
        """Model configuration."""
        use_enum_values = True
```

### Model Benefits

- **Type Safety**: Automatic type checking
- **Validation**: Built-in validation rules
- **Serialization**: JSON/dict conversion
- **Documentation**: Self-documenting schemas
- **IDE Support**: Autocomplete and type hints

### Common Model Patterns

**Pattern 1: Nested Models**
```python
class App(BaseModel):
    id: str
    name: str
    docker: DockerConfig  # Nested model
    requirements: Requirements  # Nested model
```

**Pattern 2: Enums for Constants**
```python
class ServerStatus(str, Enum):
    IDLE = "idle"
    CONNECTED = "connected"
```

**Pattern 3: Validators**
```python
@validator('email')
def validate_email(cls, v):
    if '@' not in v:
        raise ValueError('Invalid email')
    return v.lower()
```

## Database Design

The backend uses SQLite with a normalized schema.

### Key Tables

**servers**
```sql
CREATE TABLE servers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    host TEXT NOT NULL,
    port INTEGER DEFAULT 22,
    username TEXT NOT NULL,
    auth_type TEXT NOT NULL,
    credentials TEXT,  -- Encrypted JSON
    status TEXT DEFAULT 'idle',
    docker_installed BOOLEAN DEFAULT 0,
    system_info TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**installations**
```sql
CREATE TABLE installations (
    id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL,
    app_id TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    config TEXT,  -- JSON
    container_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id)
);
```

**marketplace_repos**
```sql
CREATE TABLE marketplace_repos (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    type TEXT NOT NULL,
    branch TEXT DEFAULT 'main',
    enabled BOOLEAN DEFAULT 1,
    last_synced TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**marketplace_apps**
```sql
CREATE TABLE marketplace_apps (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    version TEXT,
    docker_config TEXT,  -- JSON
    requirements TEXT,  -- JSON
    avg_rating REAL DEFAULT 0,
    rating_count INTEGER DEFAULT 0,
    featured BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES marketplace_repos(id)
);
```

### Database Patterns

**Pattern 1: JSON Columns**
```python
# Store complex data as JSON
system_info = json.dumps({
    "os": "Ubuntu 22.04",
    "architecture": "x86_64",
    "docker_version": "24.0.0"
})
```

**Pattern 2: Encrypted Columns**
```python
# Encrypt sensitive data before storage
credentials = encrypt_credentials({
    "password": "secret123"
})
```

**Pattern 3: Timestamps**
```python
# Track creation and updates
created_at = datetime.now(UTC)
updated_at = datetime.now(UTC)
```

## Security Architecture

### Credential Encryption

All server credentials are encrypted at rest using Fernet symmetric encryption:

```python
# src/lib/encryption.py

from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode
from hashlib import pbkdf2_hmac

def generate_key(password: str, salt: str) -> bytes:
    """Generate encryption key from password and salt."""
    key = pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        100000  # iterations
    )
    return urlsafe_b64encode(key)

def encrypt_credentials(credentials: dict) -> str:
    """Encrypt credentials dictionary."""
    fernet = Fernet(get_encryption_key())
    json_str = json.dumps(credentials)
    encrypted = fernet.encrypt(json_str.encode())
    return encrypted.decode()

def decrypt_credentials(encrypted: str) -> dict:
    """Decrypt credentials string."""
    fernet = Fernet(get_encryption_key())
    decrypted = fernet.decrypt(encrypted.encode())
    return json.loads(decrypted.decode())
```

### JWT Authentication

User authentication uses JWT tokens:

```python
# src/services/auth_service.py

import jwt
from datetime import datetime, timedelta, UTC

def _generate_jwt_token(self, user_id: str) -> str:
    """Generate JWT token for user."""
    payload = {
        "user_id": user_id,
        "exp": datetime.now(UTC) + timedelta(hours=24),
        "iat": datetime.now(UTC)
    }
    return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

def _validate_jwt_token(self, token: str) -> Optional[dict]:
    """Validate and decode JWT token."""
    try:
        payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        return None
```

### Input Validation

All inputs are validated:

```python
# src/lib/security.py

def validate_server_input(host: str, port: int) -> dict:
    """Validate server connection parameters."""
    errors = []

    # Validate port range
    if not 1 <= port <= 65535:
        errors.append("Port must be between 1 and 65535")

    # Validate host (basic check)
    if not host or not host.strip():
        errors.append("Host is required")

    # Block localhost/loopback
    if host.lower() in ['localhost', '127.0.0.1', '::1']:
        errors.append("Localhost connections not allowed")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
```

### Security Best Practices

1. **Credentials**: Never log or expose credentials
2. **SQL Injection**: Use parameterized queries
3. **JWT Secrets**: Store in environment variables
4. **Encryption Keys**: Derived from secure passwords
5. **Input Validation**: Validate all user inputs
6. **Error Messages**: Don't expose sensitive information

## Dependency Injection

The backend uses constructor-based dependency injection.

### Service Initialization

```python
# src/main.py

# 1. Initialize core services
database_service = DatabaseService(data_directory=data_directory)
auth_service = AuthService(db_service=database_service)
ssh_service = SSHService()

# 2. Initialize dependent services
server_service = ServerService(db_service=database_service)
deployment_service = DeploymentService(
    ssh_service=ssh_service,
    server_service=server_service,
    marketplace_service=marketplace_service,
    db_service=database_service
)

# 3. Create dependency map
tool_dependencies = {
    "database_service": database_service,
    "auth_service": auth_service,
    "ssh_service": ssh_service,
    "server_service": server_service,
    "deployment_service": deployment_service,
}

# 4. Auto-inject into tools
register_all_tools(app, config, tool_dependencies)
```

### Benefits

- **Testability**: Easy to mock dependencies
- **Flexibility**: Swap implementations
- **Clarity**: Explicit dependencies
- **Lifecycle**: Clear initialization order

## Error Handling

### Error Response Format

All tools return consistent error responses:

```python
{
    "success": False,
    "message": "Human-readable error message",
    "error": "ERROR_CODE"
}
```

### Error Handling Pattern

```python
async def add_server(self, name: str, host: str) -> dict:
    """Add a new server."""
    try:
        # Attempt operation
        server = await self.server_service.add_server(name, host)

        if not server:
            # Business logic failure
            return {
                "success": False,
                "message": "Failed to add server",
                "error": "ADD_SERVER_ERROR"
            }

        # Success
        return {
            "success": True,
            "data": server.model_dump(),
            "message": "Server added successfully"
        }

    except ValueError as e:
        # Validation error
        logger.warning("Validation error", error=str(e))
        return {
            "success": False,
            "message": str(e),
            "error": "VALIDATION_ERROR"
        }

    except Exception as e:
        # Unexpected error
        logger.error("Add server error", error=str(e))
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "error": "INTERNAL_ERROR"
        }
```

### Common Error Codes

```python
# Authentication
AUTHENTICATION_REQUIRED
INVALID_TOKEN
PERMISSION_DENIED

# Server management
SERVER_NOT_FOUND
CREDENTIALS_NOT_FOUND
CONNECTION_FAILED

# Deployment
DEPLOYMENT_FAILED
APP_NOT_FOUND
DOCKER_NOT_INSTALLED

# Validation
VALIDATION_ERROR
INVALID_PARAMETER
MISSING_PARAMETER
```

## Logging Strategy

### Structured Logging

All logs use structured logging with `structlog`:

```python
import structlog

logger = structlog.get_logger("module_name")

# Log with context
logger.info(
    "Operation completed",
    operation="add_server",
    server_id=server_id,
    duration_ms=123
)

# Log errors
logger.error(
    "Operation failed",
    operation="deploy_app",
    app_id=app_id,
    error=str(e),
    error_type=type(e).__name__
)
```

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: Normal operations and events
- **WARNING**: Unexpected but handled situations
- **ERROR**: Errors that prevent operations

### Log Output

Logs are output to stdout in JSON format:

```json
{
    "event": "Operation completed",
    "operation": "add_server",
    "server_id": "server-123",
    "duration_ms": 123,
    "level": "info",
    "timestamp": "2024-01-17T10:30:00Z",
    "logger": "server_tools"
}
```

### Database Logging

Events are also logged to the database for audit purposes:

```python
from tools.common import log_event

await log_event(
    source="srv",
    level="INFO",
    message="Server added successfully",
    tags=["server", "infrastructure"],
    metadata={
        "server_id": server_id,
        "host": host,
        "port": port
    }
)
```

## Testing Strategy

### Test Organization

```
tests/
├── unit/                  # Unit tests
│   ├── tools/            # Tool tests
│   │   ├── test_server.py
│   │   ├── test_auth.py
│   │   └── test_monitoring.py
│   └── services/         # Service tests
│       ├── test_server_service.py
│       └── test_deployment.py
├── integration/          # Integration tests
│   ├── test_deployment_flow.py
│   └── test_marketplace_sync.py
└── security/             # Security tests
    ├── test_encryption.py
    └── test_authentication.py
```

### Unit Test Pattern

```python
# tests/unit/tools/test_server.py

import pytest
from unittest.mock import AsyncMock, Mock
from tools.server.tools import ServerTools
from models.server import Server, ServerStatus

@pytest.fixture
def mock_ssh_service():
    """Mock SSH service."""
    service = Mock()
    service.test_connection = AsyncMock(return_value=(True, "OK", {}))
    return service

@pytest.fixture
def mock_server_service():
    """Mock server service."""
    service = Mock()
    service.add_server = AsyncMock(return_value=Server(
        id="server-123",
        name="Test",
        host="192.168.1.100",
        port=22,
        username="ubuntu",
        auth_type="password",
        status=ServerStatus.IDLE
    ))
    return service

@pytest.fixture
def server_tools(mock_ssh_service, mock_server_service):
    """Create ServerTools with mocked dependencies."""
    return ServerTools(
        ssh_service=mock_ssh_service,
        server_service=mock_server_service
    )

@pytest.mark.asyncio
async def test_add_server_success(server_tools):
    """Test adding a server successfully."""
    result = await server_tools.add_server(
        name="Test Server",
        host="192.168.1.100",
        port=22,
        username="ubuntu",
        auth_type="password",
        password="test123"
    )

    assert result["success"] is True
    assert result["data"]["name"] == "Test Server"
    assert "message" in result

@pytest.mark.asyncio
async def test_add_server_failure(server_tools, mock_server_service):
    """Test server addition failure."""
    mock_server_service.add_server = AsyncMock(return_value=None)

    result = await server_tools.add_server(
        name="Test",
        host="192.168.1.100",
        port=22,
        username="ubuntu",
        auth_type="password",
        password="test123"
    )

    assert result["success"] is False
    assert "error" in result
```

### Test Coverage Goals

- **Tools**: 80%+ coverage
- **Services**: 90%+ coverage
- **Models**: 100% coverage
- **Critical paths**: 100% coverage

---

## Adding New Features

### Step-by-Step Guide

**1. Define the Model**

```python
# src/models/myfeature.py

from pydantic import BaseModel
from typing import Optional

class MyFeature(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
```

**2. Create the Service**

```python
# src/services/myfeature_service.py

import structlog

logger = structlog.get_logger("myfeature_service")

class MyFeatureService:
    def __init__(self, db_service):
        self.db_service = db_service
        logger.info("MyFeature service initialized")

    async def create(self, data):
        # Implementation
        pass
```

**3. Create the Tool Module**

```bash
mkdir src/tools/myfeature
touch src/tools/myfeature/__init__.py
touch src/tools/myfeature/tools.py
```

```python
# src/tools/myfeature/tools.py

import structlog
from services.myfeature_service import MyFeatureService

logger = structlog.get_logger("myfeature_tools")

class MyFeatureTools:
    def __init__(self, myfeature_service: MyFeatureService):
        self.myfeature_service = myfeature_service
        logger.info("MyFeature tools initialized")

    async def create_feature(self, name: str) -> dict:
        result = await self.myfeature_service.create(name)
        return {
            "success": True,
            "data": result.model_dump(),
            "message": "Feature created"
        }
```

**4. Register the Service**

```python
# src/main.py

from services.myfeature_service import MyFeatureService

# Add to initialization
myfeature_service = MyFeatureService(db_service=database_service)

# Add to dependencies
tool_dependencies = {
    # ... existing dependencies
    "myfeature_service": myfeature_service,
}
```

**5. Write Tests**

```python
# tests/unit/tools/test_myfeature.py

import pytest
from unittest.mock import AsyncMock, Mock

@pytest.mark.asyncio
async def test_create_feature():
    # Test implementation
    pass
```

The tool will be automatically discovered and registered on server startup!

---

## Performance Considerations

### Connection Pooling

SQLite connections are managed by a connection pool:

```python
# src/database/connection.py

class DatabaseManager:
    def __init__(self):
        self._connection = None

    async def get_connection(self):
        if not self._connection:
            self._connection = await aiosqlite.connect(self.db_path)
        return self._connection
```

### Async Operations

All I/O operations are async to prevent blocking:

```python
# Good: Async I/O
async def get_server(self, server_id: str):
    conn = await db_manager.get_connection()
    result = await conn.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
    return await result.fetchone()

# Bad: Blocking I/O
def get_server(self, server_id: str):
    conn = sqlite3.connect("db.sqlite")
    result = conn.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
    return result.fetchone()
```

### Caching

Configuration is cached to avoid repeated file reads:

```python
@lru_cache(maxsize=1)
def _cached_config() -> Dict[str, Any]:
    # Load once, cache forever
    return load_config_from_file()
```

---

## Future Enhancements

Potential architectural improvements:

1. **PostgreSQL Support**: Add PostgreSQL as alternative database
2. **Message Queue**: Add Celery for background tasks
3. **WebSocket Support**: Real-time updates for deployments
4. **Plugin System**: Allow third-party tool modules
5. **API Versioning**: Support multiple API versions
6. **Rate Limiting**: Prevent abuse
7. **Metrics Collection**: Prometheus integration
8. **Distributed Tracing**: OpenTelemetry support

---

## References

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Structlog Documentation](https://www.structlog.org/)
- [Paramiko Documentation](https://www.paramiko.org/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

---

## Contributing

When contributing to the architecture:

1. Follow the layered architecture pattern
2. Use dependency injection for all services
3. Create Pydantic models for all data structures
4. Use structured logging everywhere
5. Write comprehensive tests
6. Document new patterns in this guide

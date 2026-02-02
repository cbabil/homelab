# Tomo Backend Architecture

The Tomo Backend is a Python-based MCP (Model Context Protocol) server that provides the central management API for the tomo system. It handles user authentication, server management, agent coordination, and application deployment.

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│                      MCP Client (WebSocket)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ MCP Protocol
┌─────────────────────────────────────────────────────────────────┐
│                     FastMCP Server (main.py)                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Tool Loader                           │   │
│  │   Auto-discovers and registers tools from tools/         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌─────────────┬─────────────┼─────────────┬─────────────┐     │
│  │ Auth Tools  │ Server Tools│ Agent Tools │ App Tools   │     │
│  │ Docker Tools│ Deploy Tools│ Settings    │ Marketplace │     │
│  │ Health      │ Monitoring  │ Backup      │ Audit       │     │
│  └─────────────┴─────────────┴─────────────┴─────────────┘     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Service Factory                        │   │
│  │   Creates and wires 22+ services with dependencies       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐      │
│  │ Auth     │ Agent    │ Server   │ Deploy   │ Settings │      │
│  │ Service  │ Service  │ Service  │ Service  │ Service  │      │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Database Services                       │   │
│  │   User │ Server │ Session │ Agent │ App │ Metrics       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│                      SQLite Database                            │
└─────────────────────────────────────────────────────────────────┘
          │                                        │
          ▼ WebSocket                              ▼ SSH
┌─────────────────────┐                 ┌─────────────────────┐
│   Tomo Agents    │                 │   Managed Servers   │
│  (Docker control)   │                 │   (Direct SSH)      │
└─────────────────────┘                 └─────────────────────┘
```

## Directory Structure

```
backend/
├── src/
│   ├── main.py                    # FastMCP entry point
│   │
│   ├── lib/                       # Core utilities
│   │   ├── config.py              # Configuration management
│   │   ├── tool_loader.py         # Dynamic tool discovery
│   │   ├── security.py            # Input validation, NIST compliance
│   │   ├── auth_helpers.py        # Password hashing, JWT
│   │   ├── encryption.py          # Data encryption
│   │   ├── git_sync.py            # Marketplace Git sync
│   │   ├── logging_config.py      # Structured logging
│   │   └── rate_limiter.py        # Connection rate limiting
│   │
│   ├── models/                    # Pydantic data models
│   │   ├── auth.py                # User, credentials, tokens
│   │   ├── agent.py               # Agent registration
│   │   ├── server.py              # Server connections
│   │   ├── app.py                 # Applications
│   │   ├── settings.py            # System/user settings
│   │   ├── session.py             # User sessions
│   │   ├── metrics.py             # Performance metrics
│   │   ├── retention.py           # Data retention
│   │   ├── notification.py        # Notifications
│   │   └── app_catalog.py         # Marketplace apps
│   │
│   ├── services/                  # Business logic (22+ services)
│   │   ├── factory.py             # Service dependency injection
│   │   ├── database_service.py    # Database facade
│   │   │
│   │   ├── database/              # Specialized DB services
│   │   │   ├── base.py            # Connection manager
│   │   │   ├── user_service.py    # User CRUD
│   │   │   ├── server_service.py  # Server CRUD
│   │   │   ├── session_service.py # Session management
│   │   │   ├── agent_service.py   # Agent DB operations
│   │   │   ├── app_service.py     # App tracking
│   │   │   ├── metrics_service.py # Metrics storage
│   │   │   └── ...
│   │   │
│   │   ├── deployment/            # App deployment
│   │   │   ├── service.py         # Main deployment logic
│   │   │   ├── docker_commands.py # OS-specific scripts
│   │   │   ├── ssh_executor.py    # Command execution
│   │   │   ├── status.py          # Status tracking
│   │   │   └── validation.py      # Deployment validation
│   │   │
│   │   ├── helpers/               # Service utilities
│   │   │   ├── ssh_helpers.py     # SSH operations
│   │   │   └── websocket_helpers.py
│   │   │
│   │   ├── auth_service.py        # Authentication
│   │   ├── session_service.py     # Session management
│   │   ├── agent_service.py       # Agent lifecycle
│   │   ├── agent_manager.py       # Active connections
│   │   ├── agent_lifecycle.py     # Health monitoring
│   │   ├── agent_websocket.py     # WebSocket handler
│   │   ├── command_router.py      # Agent/SSH routing
│   │   ├── server_service.py      # Server management
│   │   ├── app_service.py         # Application management
│   │   ├── marketplace_service.py # App catalog
│   │   ├── settings_service.py    # Settings with audit
│   │   ├── retention_service.py   # Data retention
│   │   ├── monitoring_service.py  # System health
│   │   ├── metrics_service.py     # Metrics collection
│   │   ├── notification_service.py# User notifications
│   │   ├── activity_service.py    # Activity logging
│   │   ├── dashboard_service.py   # Dashboard aggregation
│   │   ├── backup_service.py      # Backup operations
│   │   └── ssh_service.py         # SSH operations
│   │
│   ├── tools/                     # MCP tool implementations
│   │   ├── common.py              # Shared utilities
│   │   ├── auth/                  # Authentication tools
│   │   ├── server/                # Server management
│   │   ├── agent/                 # Agent tools
│   │   ├── app/                   # Application tools
│   │   ├── docker/                # Docker setup
│   │   ├── deployment/            # Deployment tools
│   │   ├── marketplace/           # Marketplace tools
│   │   ├── settings/              # Settings tools
│   │   ├── retention/             # Retention tools
│   │   ├── notification/          # Notification tools
│   │   ├── session/               # Session tools
│   │   ├── health/                # Health checks
│   │   ├── monitoring/            # Monitoring tools
│   │   ├── backup/                # Backup tools
│   │   ├── system/                # System info
│   │   ├── audit/                 # Audit tools
│   │   └── logs/                  # Log query tools
│   │
│   └── init_db/                   # Database schemas
│       ├── schema_users.py
│       ├── schema_sessions.py
│       ├── schema_servers.py
│       ├── schema_agents.py
│       ├── schema_apps_simple.py
│       ├── schema_account_locks.py
│       ├── schema_notifications.py
│       ├── schema_retention.py
│       ├── schema_logs.py
│       ├── schema_marketplace.py
│       ├── schema_system_info.py
│       └── schema_component_versions.py
│
├── tests/
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── security/                  # Security tests
│
├── data/                          # Runtime data
│   └── tomo.db                 # SQLite database
│
├── requirements.txt
└── pyproject.toml
```

## Core Components

### FastMCP Server (main.py)

The entry point that orchestrates the entire backend:

```python
# Create FastMCP application
app = FastMCP(
    name="tomo",
    version=config.VERSION,
    instructions="Tomo management system"
)

# Initialize services via factory
services = factory.create_services()

# Discover and register all tools
tool_loader.register_all_tools(app, services)

# Add agent WebSocket endpoint
starlette_app.add_route("/ws/agent", agent_websocket_handler)
```

**Responsibilities:**
- FastMCP application initialization
- CORS middleware configuration
- Service factory invocation
- Dynamic tool registration
- WebSocket endpoint for agents
- Database migration on startup
- Lifecycle management (startup/shutdown)

### Tool Loader (lib/tool_loader.py)

Auto-discovers and registers MCP tools:

```
tools/
├── auth/tools.py      → AuthTools class
├── server/tools.py    → ServerTools class
├── agent/tools.py     → AgentTools class
└── ...

Tool Loader Process:
1. Scan tools/ directory for packages
2. Import tools.py from each package
3. Find class matching *Tools pattern
4. Inspect constructor for dependencies
5. Create instance with services from factory
6. Register all public methods as MCP tools
```

### Service Factory (services/factory.py)

Centralized dependency injection:

```python
def create_services() -> Dict[str, Any]:
    # Create database services
    db_service = DatabaseService()

    # Create business services with dependencies
    auth_service = AuthService(db_service, session_service)
    agent_service = AgentService(db_service, settings_service)
    command_router = CommandRouter(agent_manager, ssh_service)

    # Return all services for tool injection
    return {
        "auth_service": auth_service,
        "agent_service": agent_service,
        "command_router": command_router,
        # ... 22+ services
    }
```

## MCP Tools

### Tool Categories

| Category | Purpose | Key Tools |
|----------|---------|-----------|
| **auth** | User authentication | `login`, `logout` |
| **server** | Server management | `add_server`, `remove_server`, `list_servers` |
| **agent** | Agent lifecycle | `register_agent`, `install_agent`, `execute_command` |
| **app** | Application management | `install_app`, `uninstall_app`, `list_apps` |
| **docker** | Docker setup | `install_docker`, `verify_docker` |
| **deployment** | App deployment | `deploy_app`, `check_status` |
| **marketplace** | App catalog | `search_apps`, `get_app_details`, `add_repository` |
| **settings** | Configuration | `get_setting`, `update_setting` |
| **retention** | Data policies | `create_policy`, `list_policies` |
| **notification** | User alerts | `get_notifications`, `mark_read` |
| **session** | Session management | `list_sessions`, `terminate_session` |
| **health** | System health | `check_health`, `get_status` |
| **monitoring** | Resource metrics | `get_metrics`, `get_resource_usage` |
| **backup** | Data backup | `create_backup`, `restore_backup` |
| **audit** | Audit logging | `query_audit_log` |
| **logs** | Event logs | `query_logs`, `get_logs_by_source` |
| **system** | System info | `get_system_info`, `get_version` |

### Tool Implementation Pattern

```python
# tools/server/tools.py
class ServerTools:
    def __init__(
        self,
        server_service: ServerService,
        ssh_service: SSHService,
        command_router: CommandRouter,
    ):
        self.server_service = server_service
        self.ssh_service = ssh_service
        self.command_router = command_router

    async def add_server(
        self,
        ctx: Context,
        hostname: str,
        port: int = 22,
        username: str = "root",
        auth_type: str = "password",
        credential: str = "",
    ) -> dict:
        """Add a new server to management."""
        # Validate input
        # Create server record
        # Test connection
        # Return result
```

## Services Layer

### Authentication Service

```
Login Flow:
┌─────────┐    ┌─────────────┐    ┌──────────────┐
│ Client  │───▶│ AuthService │───▶│ UserDBService│
└─────────┘    └─────────────┘    └──────────────┘
                     │                    │
                     ▼                    ▼
              ┌─────────────┐      ┌────────────┐
              │ bcrypt verify│     │ Get user   │
              │ (12 rounds) │      │ by username│
              └─────────────┘      └────────────┘
                     │
                     ▼
              ┌─────────────┐
              │ Generate JWT│
              │ (HS256, 24h)│
              └─────────────┘
                     │
                     ▼
              ┌─────────────────┐
              │ Create Session  │
              │ (DB persistent) │
              └─────────────────┘
                     │
                     ▼
              ┌─────────────────┐
              │ Log Security    │
              │ Event (IP, UA)  │
              └─────────────────┘
```

### Agent Service

Manages agent lifecycle:

| Operation | Description |
|-----------|-------------|
| `create_agent` | Create agent record for server |
| `generate_registration_code` | One-time code (30-day expiry) |
| `register_agent` | Exchange code for token |
| `authenticate_token` | Validate agent token (SHA256) |
| `revoke_agent` | Disable agent access |
| `update_status` | Track agent health |

### Command Router

Routes commands to best execution method:

```
Command Request
      │
      ▼
┌─────────────────────┐
│ Check Agent Status  │
└─────────────────────┘
      │
      ├─── Agent Connected ──▶ Execute via WebSocket RPC
      │
      └─── Agent Offline ────▶ Execute via SSH
                                     │
                                     ▼
                              ┌─────────────┐
                              │ SSH Service │
                              │ (Paramiko)  │
                              └─────────────┘
```

**Routing Logic:**
- Prefers agent when connected (lower latency, better security)
- Automatic SSH fallback when agent unavailable
- Configurable execution method preference
- Timing metrics per execution

### Deployment Service

Orchestrates application installation:

```
Deploy Request
      │
      ▼
┌─────────────────────┐
│ Resolve App from    │
│ Marketplace Catalog │
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ Validate Server     │
│ (Docker installed?) │
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ Route to Agent or   │
│ SSH Executor        │
└─────────────────────┘
      │
      ├─── Agent: docker.containers.run RPC
      │
      └─── SSH: docker run command
      │
      ▼
┌─────────────────────┐
│ Track Installation  │
│ in installed_apps   │
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ Log Activity        │
└─────────────────────┘
```

### Settings Service

Configuration with audit trail:

```python
# Update setting with audit
await settings_service.update_setting(
    scope="system",
    key="retention_days",
    value=30,
    user_id=current_user.id
)

# Audit record created:
{
    "setting_scope": "system",
    "setting_key": "retention_days",
    "old_value": "7",
    "new_value": "30",
    "changed_by": "admin",
    "checksum": "sha256:abc123...",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

## Database Architecture

### Schema Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Users & Authentication                    │
├─────────────────────────────────────────────────────────────┤
│  users              │ User accounts with roles               │
│  sessions           │ Persistent sessions with expiry        │
│  account_locks      │ Failed login tracking                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      Infrastructure                          │
├─────────────────────────────────────────────────────────────┤
│  servers            │ Server connections and credentials     │
│  agents             │ Agent registrations and status         │
│  agent_reg_codes    │ One-time registration codes            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       Applications                           │
├─────────────────────────────────────────────────────────────┤
│  installed_apps     │ Deployed applications                  │
│  app_catalogs       │ Marketplace app definitions            │
│  component_versions │ Version tracking                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                        Operations                            │
├─────────────────────────────────────────────────────────────┤
│  logs               │ Application event logs                 │
│  activity_log       │ User actions for dashboard             │
│  metrics            │ Performance and resource metrics       │
│  notifications      │ User notifications                     │
│  system_info        │ System hardware and OS                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       Configuration                          │
├─────────────────────────────────────────────────────────────┤
│  system_settings    │ Global system configuration            │
│  user_settings      │ Per-user preferences                   │
│  retention_policies │ Data retention rules                   │
│  settings_audit     │ Audit trail with checksums             │
└─────────────────────────────────────────────────────────────┘
```

### Database Services

Modular services under `services/database/`:

| Service | Responsibility |
|---------|----------------|
| `UserDatabaseService` | User CRUD, password management |
| `ServerDatabaseService` | Server CRUD, credentials |
| `SessionDatabaseService` | Session persistence |
| `AgentDatabaseService` | Agent records, tokens |
| `AppDatabaseService` | Installed apps tracking |
| `MetricsDatabaseService` | Metrics storage |
| `SystemDatabaseService` | System info, migrations |
| `ExportDatabaseService` | Data export/import |

## Security Architecture

### Defense Layers

```
┌────────────────────────────────────────────────────────────┐
│ Layer 1: Input Validation                                  │
│   • Hostname validation (RFC 1123)                         │
│   • Port range checks (1-65535)                            │
│   • Environment variable sanitization                      │
│   • SQL injection prevention (parameterized queries)       │
└────────────────────────────────────────────────────────────┘
                            │
┌────────────────────────────────────────────────────────────┐
│ Layer 2: Authentication                                    │
│   • bcrypt password hashing (12 rounds)                    │
│   • JWT tokens (HS256, 24-hour expiry)                     │
│   • Agent tokens (SHA256 hashed storage)                   │
│   • Registration code expiration (30 days)                 │
└────────────────────────────────────────────────────────────┘
                            │
┌────────────────────────────────────────────────────────────┐
│ Layer 3: Authorization                                     │
│   • Role-based access (admin, user, readonly)              │
│   • Scope-based settings (system vs. user)                 │
│   • Admin-only protected operations                        │
└────────────────────────────────────────────────────────────┘
                            │
┌────────────────────────────────────────────────────────────┐
│ Layer 4: Rate Limiting                                     │
│   • Connection attempt limiting                            │
│   • Account lockout after N failures                       │
│   • Per-IP rate limiting                                   │
└────────────────────────────────────────────────────────────┘
                            │
┌────────────────────────────────────────────────────────────┐
│ Layer 5: Audit & Monitoring                                │
│   • Security event logging (logins, failures)              │
│   • Settings audit trail with checksums                    │
│   • Activity logging for compliance                        │
│   • Log sanitization (masks sensitive data)                │
└────────────────────────────────────────────────────────────┘
```

### Password Security (NIST SP 800-63B-4)

```python
# lib/auth_helpers.py
BCRYPT_ROUNDS = 12  # ~250ms per hash

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(BCRYPT_ROUNDS))

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())
```

**NIST Compliance Features:**
- Minimum 8 characters (configurable)
- No arbitrary complexity rules
- Password blocklist checking
- HIBP integration (optional)

### Log Sanitization

```python
# lib/security.py
SENSITIVE_PATTERNS = [
    r'password["\']?\s*[:=]\s*["\']?[^"\']+',
    r'token["\']?\s*[:=]\s*["\']?[^"\']+',
    r'key["\']?\s*[:=]\s*["\']?[^"\']+',
    r'Bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+',
]

def sanitize_log(message: str) -> str:
    for pattern in SENSITIVE_PATTERNS:
        message = re.sub(pattern, '[REDACTED]', message)
    return message
```

## Agent Communication

### WebSocket Protocol

```
Frontend Request
      │
      ▼
┌─────────────────────┐
│ MCP Tool Called     │
│ (e.g., docker.run)  │
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ Command Router      │
│ checks agent status │
└─────────────────────┘
      │
      ▼
┌─────────────────────┐      WebSocket       ┌─────────────────┐
│ Agent Manager       │◀────────────────────▶│ Tomo Agent   │
│ (active connections)│   JSON-RPC 2.0       │ (on server)     │
└─────────────────────┘                      └─────────────────┘
      │
      ▼
┌─────────────────────┐
│ JSON-RPC Request    │
│ {method, params, id}│
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ JSON-RPC Response   │
│ {result, id}        │
└─────────────────────┘
```

### Agent Registration Flow

```
1. Admin creates agent for server
   └─▶ agent_service.create_agent(server_id)
   └─▶ Returns: agent_id

2. Admin generates registration code
   └─▶ agent_service.generate_registration_code(agent_id)
   └─▶ Returns: code (valid 30 days, hashed in DB)

3. Agent installs and connects with code
   └─▶ WebSocket: /ws/agent
   └─▶ Message: {type: "register", code: "..."}

4. Backend validates and issues token
   └─▶ agent_service.register_agent(code)
   └─▶ Returns: {agent_id, token}

5. Agent stores token and reconnects
   └─▶ Message: {type: "authenticate", token: "..."}
   └─▶ agent_manager.add_connection(agent_id, websocket)
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIRECTORY` | `data` | SQLite database location |
| `APP_ENV` | `production` | Environment mode |
| `VERSION` | `0.1.0` | Application version |
| `JWT_SECRET_KEY` | *required* | JWT signing secret |
| `SSH_TIMEOUT` | `30` | SSH timeout (seconds) |
| `MAX_CONCURRENT_CONNECTIONS` | `10` | SSH connection limit |
| `ALLOWED_ORIGINS` | `localhost:3000-3003` | CORS origins |
| `SERVER_URL` | `localhost:8000` | Server URL for agents |
| `TOOLS_DIRECTORY` | `src/tools` | Tools module location |
| `FEATURE_*` | varies | Feature flags |

### CORS Configuration

```python
# main.py
CORSMiddleware(
    app,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id"],
)
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `fastmcp` | >=0.1.0 | MCP server framework |
| `uvicorn` | >=0.23.0 | ASGI server |
| `pydantic` | >=2.0.0 | Data validation |
| `sqlalchemy` | >=2.0.0 | Database ORM |
| `aiosqlite` | >=0.19.0 | Async SQLite |
| `bcrypt` | >=4.0.0 | Password hashing |
| `pyjwt` | >=2.8.0 | JWT tokens |
| `cryptography` | >=41.0.0 | Encryption |
| `paramiko` | >=3.0.0 | SSH client |
| `docker` | >=6.0.0 | Docker API |
| `structlog` | >=23.0.0 | Structured logging |
| `aiofiles` | >=23.0.0 | Async file I/O |

## Testing

The backend includes comprehensive tests:

```bash
cd backend
source ~/source/pythonvenv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/security/ -v
```

**Test Categories:**
- **Unit tests**: Service logic, models, utilities
- **Integration tests**: End-to-end flows, MCP tools
- **Security tests**: Auth, input validation, SQL injection

## See Also

- [Agent Architecture](./agent.md) - Agent component documentation
- [Database Schema](../DATABASE_SCHEMA.md) - Full schema reference
- [MCP Tools Reference](../MCP_TOOLS_REFERENCE.md) - Tool documentation
- [Security Documentation](../security/README.md) - Security practices
- [Installation Guide](../INSTALLATION.md) - Deployment instructions

# Tomo Agent Architecture

The Tomo Agent is a Python-based daemon that runs on managed servers, providing secure remote management capabilities through a WebSocket connection to the Tomo backend.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Tomo Backend                         │
│                    (MCP WebSocket Server)                   │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ WSS (TLS 1.2+)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Tomo Agent                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   Auth   │  │Connection│  │   RPC    │  │Collectors│    │
│  │  Module  │  │  Manager │  │ Handler  │  │  (bg)    │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Security Layer                      │  │
│  │  Validation │ Rate Limit │ Replay Protection │ Audit │  │
│  └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   RPC Methods                         │  │
│  │  System │ Docker Containers │ Images │ Networks │ ... │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Docker Daemon  │
                    │  System (psutil)│
                    └─────────────────┘
```

## Directory Structure

```
agent/
├── src/
│   ├── __init__.py           # Package version
│   ├── main.py               # Entry point
│   ├── agent.py              # Main Agent class
│   ├── auth.py               # Authentication/registration
│   ├── config.py             # Configuration management
│   ├── connection.py         # WebSocket handling
│   ├── handler_setup.py      # RPC handler registration
│   ├── security.py           # Security re-exports
│   │
│   ├── collectors/           # Background tasks
│   │   ├── health.py         # Health status reporting
│   │   └── metrics.py        # System metrics collection
│   │
│   ├── lib/                  # Core libraries
│   │   ├── audit.py          # Audit logging
│   │   ├── encryption.py     # Token encryption (Fernet)
│   │   ├── permissions.py    # Permission levels
│   │   ├── rate_limiter.py   # Command rate limiting
│   │   ├── redact.py         # Sensitive data redaction
│   │   ├── replay.py         # Replay attack protection
│   │   └── validation.py     # Command validation
│   │
│   └── rpc/                  # JSON-RPC 2.0 implementation
│       ├── handler.py        # Request dispatcher
│       ├── errors.py         # Error codes/exceptions
│       ├── responses.py      # Response formatting
│       └── methods/          # Method implementations
│           ├── agent.py      # Agent control methods
│           ├── docker_client.py
│           ├── docker_containers.py
│           ├── docker_images.py
│           ├── docker_networks.py
│           ├── docker_volumes.py
│           └── system.py     # System methods
│
├── tests/                    # Test suite (309 tests)
├── Dockerfile
└── requirements.txt
```

## Core Components

### Agent (agent.py)

The central orchestrator managing the agent lifecycle:

```python
class Agent:
    def __init__(self):
        self._config = load_config()
        self.agent_id: Optional[str] = None
        self.websocket: Optional[Any] = None
        self.rpc_handler = RPCHandler()
        self.running = True
```

**Responsibilities:**
- Connection establishment and authentication
- Message loop orchestration
- Background collector lifecycle
- Graceful shutdown handling
- Automatic reconnection with exponential backoff

**Reconnection Strategy:**
- Initial delay: 1 second
- Exponential backoff: 2x multiplier
- Maximum delay: 60 seconds
- Jitter: ±20% to prevent thundering herd

### Authentication (auth.py)

Two authentication mechanisms:

1. **Token Authentication** - For reconnection using persisted token
2. **Registration Code** - For initial setup

```
Agent Start
    │
    ├─→ Has Token? ─→ authenticate_with_token()
    │                  └─→ {type: "authenticate", token, version}
    │
    └─→ Has Code? ─→ register_with_code()
                      └─→ {type: "register", code, version}
                      └─→ Save encrypted token
```

### Configuration (config.py)

**AgentConfig** - Runtime settings:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `server_url` | str | - | WebSocket server endpoint |
| `register_code` | str | None | Registration code |
| `metrics_interval` | int | 30 | Metrics push interval (seconds) |
| `health_interval` | int | 60 | Health report interval (seconds) |
| `reconnect_timeout` | int | 30 | Reconnection delay (seconds) |

**AgentState** - Persisted state (`/data/agent.json`):
| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | str | Unique agent identifier |
| `token` | str | Encrypted authentication token |
| `server_url` | str | Server URL from registration |
| `registered_at` | str | ISO timestamp |

### Connection (connection.py)

Handles WebSocket lifecycle and TLS:

**Production Mode:**
- TLS 1.2+ required
- Certificate validation via certifi
- Hostname verification enabled

**Development Mode** (`TOMO_DEV=1`):
- Self-signed certificates allowed
- Certificate verification disabled

### RPC Handler (rpc/handler.py)

Implements JSON-RPC 2.0 specification:

```python
# Request
{"jsonrpc": "2.0", "method": "system.info", "id": 1}

# Response
{"jsonrpc": "2.0", "result": {...}, "id": 1}

# Error
{"jsonrpc": "2.0", "error": {"code": -32600, "message": "..."}, "id": 1}
```

**Error Codes:**
| Code | Name | Description |
|------|------|-------------|
| -32700 | Parse Error | Invalid JSON |
| -32600 | Invalid Request | Malformed request |
| -32601 | Method Not Found | Unknown method |
| -32602 | Invalid Params | Bad parameters |
| -32603 | Internal Error | Server error |
| -32001 | Security Error | Security violation |
| -32002 | Rate Limit Error | Rate limit exceeded |
| -32003 | Docker Error | Docker operation failed |
| -32004 | Container Blocked | Container blocked by policy |
| -32005 | Command Blocked | Command blocked by policy |

### Collectors

Background tasks that push data to the server:

**HealthReporter** (`collectors/health.py`):
```python
{
    "jsonrpc": "2.0",
    "method": "health.status",
    "params": {
        "status": "healthy",
        "uptime": 3600,
        "version": "1.0.0"
    }
}
```

**MetricsCollector** (`collectors/metrics.py`):
```python
{
    "jsonrpc": "2.0",
    "method": "metrics.update",
    "params": {
        "cpu": 25.5,
        "memory": {"used": 1024, "total": 4096, "percent": 25.0},
        "disk": {"used": 50000, "total": 100000, "percent": 50.0},
        "containers": {"running": 5, "stopped": 2}
    }
}
```

## Security Architecture

### Defense in Depth

```
┌────────────────────────────────────────────────────────────┐
│ Layer 1: Transport Security                                │
│   • TLS 1.2+ with certificate validation                   │
│   • Hostname verification                                  │
└────────────────────────────────────────────────────────────┘
                            │
┌────────────────────────────────────────────────────────────┐
│ Layer 2: Authentication                                    │
│   • Token-based auth with Fernet encryption                │
│   • Machine-derived keys (PBKDF2, 480K iterations)         │
│   • Registration code for initial setup                    │
└────────────────────────────────────────────────────────────┘
                            │
┌────────────────────────────────────────────────────────────┐
│ Layer 3: Authorization                                     │
│   • READ: system.info, docker.containers.list              │
│   • EXECUTE: container start/stop/restart                  │
│   • ADMIN: exec, run, config.update                        │
└────────────────────────────────────────────────────────────┘
                            │
┌────────────────────────────────────────────────────────────┐
│ Layer 4: Input Validation                                  │
│   • Command allowlist (24+ patterns)                       │
│   • Docker parameter validation                            │
│   • Volume mount path protection                           │
│   • Shell metacharacter detection                          │
└────────────────────────────────────────────────────────────┘
                            │
┌────────────────────────────────────────────────────────────┐
│ Layer 5: Rate Limiting & Replay Protection                 │
│   • 30 commands/minute, 5 concurrent                       │
│   • Nonce + timestamp validation                           │
│   • 5-minute freshness window                              │
└────────────────────────────────────────────────────────────┘
                            │
┌────────────────────────────────────────────────────────────┐
│ Layer 6: Audit & Monitoring                                │
│   • Structured JSON audit logs                             │
│   • Trace IDs for correlation                              │
│   • Sensitive data redaction                               │
└────────────────────────────────────────────────────────────┘
```

### Permission Model (lib/permissions.py)

```python
class PermissionLevel(Enum):
    READ = "read"       # Read-only operations
    EXECUTE = "execute" # Container management
    ADMIN = "admin"     # Dangerous operations
```

| Method | Permission |
|--------|------------|
| `system.info` | READ |
| `docker.containers.list` | READ |
| `docker.containers.start` | EXECUTE |
| `docker.containers.stop` | EXECUTE |
| `docker.containers.run` | ADMIN |
| `system.exec` | ADMIN |
| `config.update` | ADMIN |

### Command Validation (lib/validation.py)

**Allowed Commands** (regex patterns):
- `docker (ps|images|info|version|stats)`
- `docker-compose (up|down|ps|logs)`
- `systemctl (status|is-active)`
- `df`, `free`, `uptime`, `hostname`
- `cat /etc/os-release`

**Blocked Docker Flags:**
- `--privileged`
- `--cap-add=ALL`, `--cap-add=SYS_ADMIN`
- `--pid=host`, `--network=host`, `--ipc=host`
- `--security-opt=apparmor:unconfined`
- `--device=/dev/*`

**Blocked Volume Mounts:**
- `/etc`, `/var`, `/root`, `/home`
- `/proc`, `/sys`, `/dev`
- `/var/run/docker.sock`
- `/boot`, `/usr`

### Token Encryption (lib/encryption.py)

```
┌──────────────────────────────────────────────────────────┐
│                  Token Encryption Flow                    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   Machine ID (/etc/machine-id)                           │
│         │                                                │
│         ▼                                                │
│   ┌─────────────┐                                        │
│   │   PBKDF2    │  + Salt (random, stored separately)   │
│   │ 480K iters  │                                        │
│   └─────────────┘                                        │
│         │                                                │
│         ▼                                                │
│   ┌─────────────┐                                        │
│   │ Fernet Key  │  (AES-128-CBC + HMAC)                 │
│   └─────────────┘                                        │
│         │                                                │
│         ▼                                                │
│   Encrypted Token → /data/agent.json                     │
│   Salt → /data/.token_salt                               │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Replay Protection (lib/replay.py)

```python
class ReplayProtection:
    FRESHNESS_WINDOW_SECONDS = 300    # 5 minutes
    MAX_NONCES = 10000                # Memory limit
    CLOCK_SKEW_TOLERANCE_SECONDS = 30 # Allow slight drift
```

**Validation:**
1. Check timestamp is within freshness window
2. Check timestamp is not in future (with skew tolerance)
3. Check nonce has not been seen before
4. Add nonce to seen set

## RPC Methods Reference

### System Methods

| Method | Description | Permission |
|--------|-------------|------------|
| `system.info` | OS, Docker, hostname info | READ |
| `system.exec` | Execute allowlisted command | ADMIN |
| `system.get_metrics` | CPU, memory, disk usage | READ |
| `system.preflight_check` | Pre-deployment checks | READ |
| `system.prepare_volumes` | Create volume directories | EXECUTE |

### Docker Methods

| Method | Description | Permission |
|--------|-------------|------------|
| `docker.containers.list` | List containers | READ |
| `docker.containers.get` | Get container details | READ |
| `docker.containers.run` | Run new container | ADMIN |
| `docker.containers.start` | Start container | EXECUTE |
| `docker.containers.stop` | Stop container | EXECUTE |
| `docker.containers.restart` | Restart container | EXECUTE |
| `docker.containers.remove` | Remove container | EXECUTE |
| `docker.containers.logs` | Get container logs | READ |
| `docker.images.list` | List images | READ |
| `docker.images.pull` | Pull image | EXECUTE |
| `docker.images.remove` | Remove image | EXECUTE |
| `docker.networks.list` | List networks | READ |
| `docker.networks.create` | Create network | EXECUTE |
| `docker.networks.remove` | Remove network | EXECUTE |
| `docker.volumes.list` | List volumes | READ |
| `docker.volumes.create` | Create volume | EXECUTE |
| `docker.volumes.remove` | Remove volume | EXECUTE |

### Agent Methods

| Method | Description | Permission |
|--------|-------------|------------|
| `agent.ping` | Liveness check | READ |
| `agent.update` | Update configuration | ADMIN |
| `agent.restart` | Graceful restart | ADMIN |

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SERVER_URL` | Yes | WebSocket server (wss://...) |
| `REGISTER_CODE` | Initial | Registration code for setup |
| `TOMO_DEV` | No | Set to "1" for dev mode |
| `HOSTNAME` | No | Container hostname identifier |

### File Locations

| Path | Description | Permissions |
|------|-------------|-------------|
| `/data/agent.json` | Persisted state | 0600 |
| `/data/.token_salt` | Encryption salt | 0600 |
| `/host` | Host filesystem mount | varies |

## Deployment

### Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONUNBUFFERED=1
VOLUME ["/data"]

ENTRYPOINT ["python", "-m", "src.main"]
```

### Docker Compose

```yaml
services:
  tomo-agent:
    image: tomo-agent:latest
    environment:
      - SERVER_URL=wss://tomo.example.com/agent/ws
      - REGISTER_CODE=${AGENT_REGISTER_CODE}
    volumes:
      - agent-data:/data
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /:/host:ro
    restart: unless-stopped

volumes:
  agent-data:
```

## Testing

The agent includes 309 tests covering:

- **Unit tests**: Core modules, validation, encryption
- **Integration tests**: Connection, authentication flow
- **Security tests**: Command blocking, rate limiting
- **Docker tests**: Container operations

Run tests:
```bash
cd agent
source ~/source/pythonvenv/bin/activate
pytest tests/ -v
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `websockets` | >=12.0 | WebSocket client |
| `docker` | >=7.0 | Docker SDK |
| `psutil` | >=5.9 | System metrics |
| `pydantic` | >=2.0 | Data validation |
| `certifi` | >=2024.0 | CA certificates |
| `cryptography` | >=42.0 | Token encryption |

## See Also

- [MCP Tools Reference](../MCP_TOOLS_REFERENCE.md) - Backend tool documentation
- [Security Documentation](../security/README.md) - Security practices
- [Installation Guide](../INSTALLATION.md) - Deployment instructions

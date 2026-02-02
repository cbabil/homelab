# Tomo Agent Design

> A lightweight Python agent that runs as a Docker container on managed servers, replacing SSH for all operations after initial Docker installation.

## Overview

### Problem

SSH-based server management has several pain points:
- Each command creates a new SSH connection (inefficient)
- No connection pooling across operations
- String concatenation for commands (injection risks)
- Text parsing of output (fragile)
- Metrics collection requires multiple separate SSH connections
- Background operations rely on temp files with no cleanup verification

### Solution

Deploy a persistent agent on each managed server that:
- Maintains a WebSocket connection to the tomo server
- Handles all Docker and system operations locally
- Pushes metrics and health status proactively
- Receives commands via JSON-RPC 2.0 protocol

### Scope

| Phase | Method | What happens |
|-------|--------|--------------|
| **Bootstrap** | SSH (one-time) | Install Docker → Deploy agent container → Agent connects |
| **Everything else** | WebSocket Agent | System info, metrics, Docker operations, command execution, logs streaming |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Tomo Server                              │
│  ┌─────────────┐  ┌─────────────────────────────────────────┐   │
│  │   Frontend  │  │            Backend (MCP)                │   │
│  │   (React)   │◄─┤  ┌────────────┐  ┌───────────────────┐  │   │
│  │             │  │  │ MCP Tools  │  │  WebSocket Server │  │   │
│  │             │  │  │            │  │  /ws/agent/{id}   │  │   │
│  └─────────────┘  │  └────────────┘  └─────────┬─────────┘  │   │
│                   └────────────────────────────┼────────────┘   │
└────────────────────────────────────────────────┼────────────────┘
                                                 │ WSS (TLS)
                    ┌────────────────────────────┼────────────────┐
                    │                            ▼                │
                    │  ┌──────────────────────────────────────┐   │
                    │  │           Tomo Agent              │   │
                    │  │  ┌─────────┐ ┌─────────┐ ┌────────┐  │   │
                    │  │  │ Metrics │ │ Docker  │ │ Command│  │   │
                    │  │  │Collector│ │  Proxy  │ │Executor│  │   │
                    │  │  └─────────┘ └─────────┘ └────────┘  │   │
                    │  └──────────────────┬───────────────────┘   │
                    │                     │                       │
                    │          ┌──────────┴──────────┐            │
                    │          ▼                     ▼            │
                    │   /var/run/docker.sock    /host (ro)        │
                    │                                             │
                    │              Managed Server                 │
                    └─────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Deployment | Docker container | Portable, isolated, easy updates |
| Communication | Persistent WebSocket | Real-time, bidirectional, simple reconnection |
| Language | Python | Matches backend, shared knowledge, good Docker SDK |
| Protocol | JSON-RPC 2.0 | Standard spec, request/response correlation, error format defined |
| Security | One-time registration code | Secure initial handshake, no secrets in process list |
| Container access | Docker socket + /host read-only | Full Docker control + system metrics |

---

## Registration & Authentication

### Flow

```
┌──────────┐         ┌──────────┐         ┌──────────┐         ┌──────────┐
│ Frontend │         │  Backend │         │    SSH   │         │  Agent   │
└────┬─────┘         └────┬─────┘         └────┬─────┘         └────┬─────┘
     │                    │                    │                    │
     │ 1. Add Server      │                    │                    │
     │ (host, credentials)│                    │                    │
     ├───────────────────►│                    │                    │
     │                    │                    │                    │
     │ 2. Create agent record (status: pending)                    │
     │    Generate registration code (6 chars, expires 5 min)      │
     │◄───────────────────┤                    │                    │
     │                    │                    │                    │
     │                    │ 3. SSH: Install Docker (if needed)     │
     │                    ├───────────────────►│                    │
     │                    │                    │                    │
     │                    │ 4. SSH: docker run tomo-agent       │
     │                    │    --env REGISTER_CODE=ABC123          │
     │                    │    --env SERVER_URL=wss://...          │
     │                    ├───────────────────►│────────────────────►
     │                    │                    │                    │
     │                    │                    │     5. Agent starts,
     │                    │                    │     connects to WSS
     │                    │◄───────────────────────────────────────┤
     │                    │                    │                    │
     │                    │ 6. Validate code, return permanent token
     │                    ├────────────────────────────────────────►
     │                    │                    │                    │
     │                    │ 7. Agent stores token in volume        │
     │                    │    Update agent status to 'connected'  │
     │                    │                    │                    │
     │ 8. Server status:  │                    │                    │
     │    "connected"     │                    │                    │
     │◄───────────────────┤                    │                    │
```

### Token Storage

Agent stores token in a Docker volume at `/data/agent.json`:

```json
{
  "server_id": "uuid",
  "token": "jwt-or-random-token",
  "registered_at": "2026-01-23T10:00:00Z"
}
```

### Reconnection

On restart or disconnect:
1. Agent reads token from `/data/agent.json`
2. Connects to WebSocket with `Authorization: Bearer <token>` header
3. Server validates token, resumes connection
4. No re-registration needed

### Token Revocation

If user removes server from tomo:
1. Server closes WebSocket connection
2. Invalidates token in database
3. Agent will fail to reconnect, logs "token revoked"

---

## Message Protocol (JSON-RPC 2.0)

### Server → Agent (commands)

```json
// List containers
{"jsonrpc":"2.0", "method":"docker.containers.list", "params":{}, "id":1}

// Run container
{"jsonrpc":"2.0", "method":"docker.containers.run", "params":{
  "image": "nginx:latest",
  "name": "my-nginx",
  "ports": {"80/tcp": 8080},
  "env": {"FOO": "bar"}
}, "id":2}

// Stream container logs
{"jsonrpc":"2.0", "method":"docker.containers.logs", "params":{
  "container": "my-nginx",
  "follow": true,
  "tail": 100
}, "id":3}

// Execute system command
{"jsonrpc":"2.0", "method":"system.exec", "params":{
  "command": "df -h"
}, "id":4}

// Request immediate metrics
{"jsonrpc":"2.0", "method":"metrics.get", "params":{}, "id":5}

// Push config update
{"jsonrpc":"2.0", "method":"config.update", "params":{
  "metrics_interval": 30,
  "health_interval": 60
}, "id":6}
```

### Agent → Server (responses)

```json
// Success
{"jsonrpc":"2.0", "result":{"containers":[...]}, "id":1}

// Error
{"jsonrpc":"2.0", "error":{"code":-32000, "message":"Container not found"}, "id":3}
```

### Agent → Server (notifications)

No response expected for these:

```json
// Metrics push
{"jsonrpc":"2.0", "method":"metrics.update", "params":{
  "cpu": 45.2,
  "memory": {"used": 4200, "total": 8000, "percent": 52.5},
  "disk": {"used": "50G", "total": "100G", "percent": 50.0},
  "containers": {"running": 5, "stopped": 2}
}}

// Health status
{"jsonrpc":"2.0", "method":"health.status", "params":{
  "status": "healthy",
  "uptime": 86400,
  "version": "1.0.0"
}}

// Log stream chunk
{"jsonrpc":"2.0", "method":"logs.stream", "params":{
  "request_id": 3,
  "container": "my-nginx",
  "line": "2026-01-23 10:00:00 GET /index.html 200"
}}
```

---

## Agent API Methods

### Docker Operations

| Method | Params | Description |
|--------|--------|-------------|
| `docker.containers.list` | `all?: bool` | List containers |
| `docker.containers.run` | `image, name, ports, env, volumes, ...` | Create and start container |
| `docker.containers.start` | `container` | Start stopped container |
| `docker.containers.stop` | `container, timeout?` | Stop container |
| `docker.containers.remove` | `container, force?` | Remove container |
| `docker.containers.restart` | `container` | Restart container |
| `docker.containers.logs` | `container, follow?, tail?` | Get/stream logs |
| `docker.containers.inspect` | `container` | Get container details |
| `docker.containers.stats` | `container` | Get container resource usage |
| `docker.images.list` | | List images |
| `docker.images.pull` | `image, tag?` | Pull image (streams progress) |
| `docker.images.remove` | `image, force?` | Remove image |
| `docker.images.prune` | | Remove unused images |
| `docker.volumes.list` | | List volumes |
| `docker.volumes.create` | `name, driver?` | Create volume |
| `docker.volumes.remove` | `name, force?` | Remove volume |
| `docker.networks.list` | | List networks |
| `docker.networks.create` | `name, driver?` | Create network |
| `docker.networks.remove` | `name` | Remove network |

### System Operations

| Method | Params | Description |
|--------|--------|-------------|
| `system.info` | | Get OS, kernel, arch, Docker version |
| `system.exec` | `command, timeout?` | Execute command (streams output) |
| `metrics.get` | | Get current CPU, memory, disk |

### Agent Operations

| Method | Params | Description |
|--------|--------|-------------|
| `agent.ping` | | Health check, returns version |
| `agent.update` | `version` | Pull new image and restart |
| `config.update` | `metrics_interval, ...` | Update agent config |

---

## Database Schema

### New Tables

**agents**

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `server_id` | UUID | FK to servers table (unique) |
| `token_hash` | TEXT | Hashed authentication token |
| `version` | TEXT | Agent version (e.g., "1.0.0") |
| `status` | TEXT | `'pending'`, `'connected'`, `'disconnected'`, `'updating'` |
| `last_seen` | TIMESTAMP | Last heartbeat/message |
| `registered_at` | TIMESTAMP | When agent was first registered |
| `config` | JSON | Agent-specific config overrides (optional) |

**agent_registration_codes**

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `agent_id` | UUID | FK to agents table |
| `code` | TEXT | 6-char registration code |
| `expires_at` | TIMESTAMP | Code expiry (created_at + 5 min) |
| `used` | BOOLEAN | Whether code was consumed |

### Settings Additions

| Key | Default | Description |
|-----|---------|-------------|
| `agent_metrics_interval` | 30 | Seconds between metrics push |
| `agent_health_interval` | 60 | Seconds between health reports |
| `agent_reconnect_timeout` | 30 | Seconds before reconnect attempt |

### Relationships

```
servers (1) ──────── (0..1) agents (1) ──────── (0..n) agent_registration_codes
```

A server may or may not have an agent (supports SSH-only servers).

---

## Agent Container

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY src/ ./src/

# Data volume for token persistence
VOLUME /data

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "-m", "src.main"]
```

### Requirements

```
websockets>=12.0
docker>=7.0
psutil>=5.9
pydantic>=2.0
```

### Deployment Command

```bash
docker run -d \
  --name tomo-agent \
  --restart unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /:/host:ro \
  -v tomo-agent-data:/data \
  -e REGISTER_CODE=ABC123 \
  -e SERVER_URL=wss://tomo.local:8000/ws/agent \
  ghcr.io/yourrepo/tomo-agent:latest
```

### Directory Structure

```
agent/
├── Dockerfile
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point, WebSocket connection
│   ├── config.py            # Configuration handling
│   ├── auth.py              # Registration & token management
│   ├── rpc/
│   │   ├── __init__.py
│   │   ├── handler.py       # JSON-RPC dispatcher
│   │   └── methods/
│   │       ├── __init__.py
│   │       ├── docker.py    # Docker operations
│   │       ├── system.py    # System info & exec
│   │       └── agent.py     # Agent operations (ping, update)
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── metrics.py       # CPU, memory, disk collection
│   │   └── health.py        # Health status
│   └── utils/
│       ├── __init__.py
│       └── logging.py
└── tests/
    └── ...
```

---

## Implementation Plan

### Phase 1: Backend Infrastructure
1. Create database schema (agents, agent_registration_codes tables)
2. Add agent settings to settings table
3. Create WebSocket server endpoint (`/ws/agent`)
4. Implement AgentManager (connection tracking, message routing)
5. Implement registration code generation & validation
6. Implement token generation & validation

### Phase 2: Agent Core
7. Set up agent project structure
8. Implement WebSocket client with reconnection logic
9. Implement registration flow (code → token exchange)
10. Implement JSON-RPC handler/dispatcher
11. Implement config management (receive settings from server)

### Phase 3: Agent Capabilities
12. Implement Docker methods (containers, images, volumes, networks)
13. Implement system methods (info, exec with streaming)
14. Implement metrics collector (CPU, memory, disk)
15. Implement health reporter
16. Implement log streaming

### Phase 4: Agent Lifecycle
17. Implement auto-update mechanism
18. Implement graceful shutdown
19. Build and publish Docker image

### Phase 5: Backend Integration
20. Create MCP tools that route through AgentManager
21. Update server service to use agent when available (fall back to SSH)
22. Add agent status to server responses
23. Add agent settings UI tab

### Phase 6: Frontend
24. Show agent status on server cards/table
25. Show agent version (like Docker version column)
26. Add "Install Agent" flow in UI
27. Display real-time metrics from agent
28. Agent settings in settings page
29. Agent update indicator (new version available)

---

## References

- [Portainer Agent Architecture](https://docs.portainer.io/start/architecture)
- [Portainer Edge Agent](https://docs.portainer.io/advanced/edge-agent)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [Chisel Tunnel](https://github.com/jpillora/chisel)

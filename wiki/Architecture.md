# Architecture

This document describes the technical architecture of Tomo.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User's Browser                         │
│                     (React SPA + MCP Client)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/WebSocket (MCP)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Tomo                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Backend   │  │   Frontend  │  │     CLI     │              │
│  │ (FastMCP)   │  │   (React)   │  │    (Ink)    │              │
│  │             │  │             │  │             │              │
│  │ • MCP Tools │  │ • Dashboard │  │ • Commands  │              │
│  │ • Services  │  │ • Pages     │  │ • Scripts   │              │
│  │ • Auth      │  │ • Components│  │             │              │
│  └──────┬──────┘  └─────────────┘  └──────┬──────┘              │
│         │                                  │                     │
│         ▼                                  ▼                     │
│  ┌─────────────┐                   ┌─────────────┐              │
│  │   SQLite    │                   │  MCP Client │              │
│  │  Database   │◄──────────────────┤  (Backend)  │              │
│  └─────────────┘                   └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ SSH / WebSocket
                             ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Server 1    │  │   Server 2    │  │   Server 3    │
│               │  │               │  │               │
│ ┌───────────┐ │  │ ┌───────────┐ │  │ ┌───────────┐ │
│ │   Agent   │ │  │ │   Agent   │ │  │ │   Agent   │ │
│ │           │ │  │ │           │ │  │ │           │ │
│ │ • Metrics │ │  │ │ • Metrics │ │  │ │ • Metrics │ │
│ │ • Docker  │ │  │ │ • Docker  │ │  │ │ • Docker  │ │
│ └───────────┘ │  │ └───────────┘ │  │ └───────────┘ │
│               │  │               │  │               │
│ ┌───────────┐ │  │ ┌───────────┐ │  │ ┌───────────┐ │
│ │  Docker   │ │  │ │  Docker   │ │  │ │  Docker   │ │
│ │ Containers│ │  │ │ Containers│ │  │ │ Containers│ │
│ └───────────┘ │  │ └───────────┘ │  │ └───────────┘ │
└───────────────┘  └───────────────┘  └───────────────┘
```

---

## Component Architecture

### Backend (Python)

**Technology:** Python 3.12, FastMCP, SQLite

```
backend/src/
├── main.py              # FastMCP server entry point
├── tools/               # MCP tool implementations
│   ├── auth/            # Authentication tools
│   ├── server/          # Server management tools
│   ├── app/             # Application deployment tools
│   ├── agent/           # Agent management tools
│   └── settings/        # Settings tools
├── services/            # Business logic layer
│   ├── auth_service.py
│   ├── server_service.py
│   ├── app_service.py
│   ├── agent_service.py
│   └── ssh_service.py
├── models/              # Pydantic models
│   ├── auth.py
│   ├── server.py
│   └── app.py
├── lib/                 # Utilities
│   ├── security.py      # Encryption
│   ├── config.py        # Configuration
│   └── auth_helpers.py  # JWT handling
└── init_db/             # Database schemas
```

**Key patterns:**
- MCP tools are thin wrappers around services
- Services contain business logic
- Models define data structures and validation
- Lib contains shared utilities

---

### Frontend (React)

**Technology:** React 19, TypeScript, Vite, TailwindCSS

```
frontend/src/
├── App.tsx              # Main app with routing
├── main.tsx             # Entry point
├── components/          # Reusable UI components
│   ├── ui/              # Base components (Button, Input)
│   ├── layout/          # Layout components (Header, Nav)
│   ├── servers/         # Server-related components
│   └── auth/            # Auth-related components
├── pages/               # Route page components
│   ├── dashboard/
│   ├── servers/
│   ├── applications/
│   ├── marketplace/
│   └── settings/
├── hooks/               # Custom React hooks
│   ├── useAuth.ts
│   ├── useServers.ts
│   └── useMcpClient.ts
├── services/            # API and data services
│   ├── mcpClient.ts     # MCP protocol client
│   └── authService.ts
├── providers/           # React context providers
│   ├── AuthProvider.tsx
│   └── MCPProvider.tsx
└── types/               # TypeScript type definitions
```

**Key patterns:**
- Components are small and focused
- Hooks extract reusable logic
- Providers manage global state
- MCP client handles all backend communication

---

### CLI (TypeScript)

**Technology:** TypeScript, Ink (React for CLI), Bun

```
cli/src/
├── bin/
│   └── tomo.tsx      # Entry point
├── commands/            # Command implementations
│   ├── admin.tsx
│   ├── user.tsx
│   ├── server.tsx
│   ├── agent.tsx
│   └── backup.tsx
├── components/          # Ink UI components
│   ├── Table.tsx
│   ├── Spinner.tsx
│   └── Form.tsx
└── lib/
    └── mcpClient.ts     # MCP client
```

---

### Agent (Python)

**Technology:** Python 3.12, WebSockets, Docker SDK

```
agent/src/
├── main.py              # Agent entry point
├── rpc/                 # WebSocket RPC
│   ├── server.py        # WebSocket client
│   └── handlers.py      # Command handlers
├── collectors/          # Metrics collectors
│   ├── system.py        # CPU, memory, disk
│   ├── docker.py        # Container metrics
│   └── network.py       # Network stats
└── security/
    ├── token.py         # Token management
    └── allowlist.py     # Command validation
```

---

## Database Schema

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT,
    role TEXT DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);

-- Servers table
CREATE TABLE servers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    hostname TEXT NOT NULL,
    port INTEGER DEFAULT 22,
    username TEXT NOT NULL,
    auth_type TEXT DEFAULT 'password',
    encrypted_password TEXT,
    encrypted_private_key TEXT,
    status TEXT DEFAULT 'unknown',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Applications table
CREATE TABLE applications (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    server_id INTEGER REFERENCES servers(id),
    image TEXT NOT NULL,
    status TEXT DEFAULT 'stopped',
    config JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    token_hash TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    last_activity DATETIME
);

-- Audit logs table
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details JSON,
    ip_address TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Communication Protocols

### MCP (Model Context Protocol)

Frontend and CLI communicate with backend using MCP:

```
Client                          Server
  │                                │
  │──── tool_call(name, args) ────▶│
  │                                │
  │◀─── result/error ──────────────│
  │                                │
```

**Tool example:**
```python
@tool()
async def list_servers() -> list[Server]:
    """List all servers."""
    return await server_service.list_all()
```

### Agent WebSocket

Agent communicates with backend via WebSocket:

```
Agent                          Backend
  │                                │
  │──── connect(token) ───────────▶│
  │                                │
  │◀─── acknowledge ───────────────│
  │                                │
  │──── metrics(data) ────────────▶│
  │                                │
  │◀─── command(action) ───────────│
  │                                │
  │──── result(data) ─────────────▶│
  │                                │
```

---

## Security Architecture

### Authentication Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │     │ Backend  │     │ Database │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │
     │ login(u,p)     │                │
     │───────────────▶│                │
     │                │ get_user(u)    │
     │                │───────────────▶│
     │                │◀───────────────│
     │                │                │
     │                │ verify(p,hash) │
     │                │                │
     │ JWT + cookie   │                │
     │◀───────────────│                │
     │                │                │
```

### Credential Encryption

```
┌─────────────────────────────────────────────────────┐
│                 Encryption Flow                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Password/Key                                       │
│       │                                             │
│       ▼                                             │
│  ┌─────────────────────────────────────────────┐    │
│  │  Master Password + Salt                     │    │
│  │           │                                 │    │
│  │           ▼                                 │    │
│  │  PBKDF2 (100,000 iterations)               │    │
│  │           │                                 │    │
│  │           ▼                                 │    │
│  │  Derived Key (256-bit)                     │    │
│  └─────────────────────────────────────────────┘    │
│       │                                             │
│       ▼                                             │
│  ┌─────────────────────────────────────────────┐    │
│  │  AES-256-GCM Encryption                     │    │
│  │           │                                 │    │
│  │           ▼                                 │    │
│  │  IV + Ciphertext + Auth Tag                │    │
│  └─────────────────────────────────────────────┘    │
│       │                                             │
│       ▼                                             │
│  Stored in Database                                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Data Flow

### Server Addition

```
User                Frontend            Backend              Remote Server
 │                     │                   │                      │
 │ Add Server          │                   │                      │
 │────────────────────▶│                   │                      │
 │                     │                   │                      │
 │                     │ add_server(data)  │                      │
 │                     │──────────────────▶│                      │
 │                     │                   │                      │
 │                     │                   │ SSH connect          │
 │                     │                   │─────────────────────▶│
 │                     │                   │                      │
 │                     │                   │◀─────────────────────│
 │                     │                   │                      │
 │                     │                   │ Encrypt credentials  │
 │                     │                   │ Save to database     │
 │                     │                   │                      │
 │                     │◀──────────────────│                      │
 │                     │                   │                      │
 │◀────────────────────│                   │                      │
 │                     │                   │                      │
```

### Application Deployment

```
User           Frontend         Backend          Agent           Docker
 │                │                │               │                │
 │ Deploy App     │                │               │                │
 │───────────────▶│                │               │                │
 │                │                │               │                │
 │                │ deploy(app)    │               │                │
 │                │───────────────▶│               │                │
 │                │                │               │                │
 │                │                │ deploy cmd    │                │
 │                │                │──────────────▶│                │
 │                │                │               │                │
 │                │                │               │ docker create  │
 │                │                │               │───────────────▶│
 │                │                │               │                │
 │                │                │               │◀───────────────│
 │                │                │               │                │
 │                │                │◀──────────────│                │
 │                │                │               │                │
 │                │◀───────────────│               │                │
 │                │                │               │                │
 │◀───────────────│                │               │                │
 │                │                │               │                │
```

---

## Scalability Considerations

### Current Design (Single Node)

- SQLite database (sufficient for hundreds of servers)
- Single backend process
- WebSocket connections for agents

### Future Scaling Options

| Component | Scaling Strategy |
|-----------|------------------|
| Database | PostgreSQL for larger deployments |
| Backend | Multiple workers behind load balancer |
| Agents | Connection pooling, message queue |
| Frontend | CDN distribution |

---

## Next Steps

- [[API-Reference]] - API documentation
- [[Development]] - Development guide
- [[Contributing]] - Contribution guidelines

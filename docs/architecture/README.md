# Architecture Overview

This section documents the system architecture, design decisions, and component structure of the Tomo.

## Quick Reference

| Document | Description |
|----------|-------------|
| [Decisions](decisions.md) | Architecture Decision Records (ADRs) |
| [Full Architecture](../ARCHITECTURE.md) | Comprehensive system architecture |
| [Backend Architecture](backend.md) | Backend services, MCP server, and tool system |
| [Agent Architecture](agent.md) | Tomo Agent design and RPC methods |
| [Settings System](settings.md) | Settings architecture and implementation |
| [Registration Feature](registration.md) | Registration feature design |
| [Marketplace Deployment](marketplace-deployment.md) | Marketplace deployment architecture |
| [Comparison: Homarr](comparison-homarr.md) | How Tomo compares to Homarr |

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Docker Container                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    │
│   │   React UI      │    │   nginx Proxy   │    │  FastMCP Server │    │
│   │   (Frontend)    │◄──►│   (Routing)     │◄──►│   (Backend)     │    │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘    │
│          │                                              │               │
│          │           MCP Protocol                       │               │
│          └──────────────────────────────────────────────┘               │
│                                                         │               │
│                              ┌───────────────────────────┤               │
│                              ▼                           ▼               │
│                    ┌─────────────────┐         ┌─────────────────┐      │
│                    │  SQLite DB      │         │  SSH Client     │      │
│                    │  (Data Store)   │         │  (paramiko)     │      │
│                    └─────────────────┘         └─────────────────┘      │
│                                                         │               │
└─────────────────────────────────────────────────────────│───────────────┘
                                                          ▼
                                                ┌─────────────────┐
                                                │ Remote Servers  │
                                                │ (SSH + Docker)  │
                                                └─────────────────┘
```

## Technology Stack

### Frontend
- **React 19** - Modern functional components with hooks
- **TypeScript** - Type safety and developer experience
- **Vite** - Fast builds and HMR
- **TailwindCSS** - Utility-first styling
- **React Query** - Data fetching and caching
- **shadcn/ui** - Accessible UI components

### Backend
- **Python 3.11+** - Modern Python with performance improvements
- **FastMCP** - Model Context Protocol server
- **SQLite** - Embedded database
- **Paramiko** - Pure Python SSH client
- **Pydantic** - Data validation
- **structlog** - Structured JSON logging

### Infrastructure
- **Docker** - Single container deployment
- **nginx** - Reverse proxy and static serving
- **supervisord** - Process management

## Key Architectural Decisions

### ADR-001: MCP over REST
We use the Model Context Protocol (MCP) instead of REST APIs for frontend-backend communication. This provides:
- Type-safe tool definitions
- Real-time capabilities
- Standardized error handling
- Easy extensibility

See [decisions.md](decisions.md) for full ADR.

### ADR-002: Single Container Deployment
Production deployment uses a single Docker container with nginx + Python backend + React frontend managed by supervisord. This simplifies:
- Deployment and operations
- Resource management
- Networking configuration

### ADR-003: Paramiko for SSH
Pure Python SSH library (paramiko) instead of system SSH commands:
- No external dependencies
- Cross-platform compatibility
- Programmatic control

## Component Architecture

### Frontend Structure
```
frontend/src/
├── components/          # Reusable UI components
│   ├── auth/            # Authentication (ProtectedRoute, SessionWarning)
│   ├── layout/          # AppLayout, Navigation, Header
│   ├── servers/         # Server management UI
│   ├── applications/    # Application browsing/deployment
│   ├── deployment/      # Deployment workflows
│   ├── settings/        # Settings management
│   ├── monitoring/      # Dashboard and metrics
│   └── ui/              # Generic UI components
├── pages/               # Page-level components
├── hooks/               # Custom React hooks
├── providers/           # Context providers (Auth, MCP, Theme)
├── services/            # API/MCP clients
├── types/               # TypeScript definitions
└── utils/               # Utility functions
```

### Backend Structure
```
backend/src/
├── main.py              # FastMCP server entry point
├── tools/               # MCP tool implementations
│   ├── auth_tools.py    # Authentication
│   ├── server_tools.py  # Server management
│   ├── app_tools.py     # Application catalog
│   ├── deployment_tools.py
│   ├── settings_tools.py
│   └── ...
├── services/            # Business logic
│   ├── auth_service.py
│   ├── database_service.py
│   ├── ssh_service.py
│   ├── deployment_service.py
│   └── ...
├── models/              # Pydantic data models
├── lib/                 # Utilities (encryption, logging)
├── database/            # Database connection management
└── config/              # Configuration
```

## Data Flow

### Authentication Flow
```
User → LoginPage → AuthProvider → authService.login()
                                        ↓
                        MCP call: login(username, password)
                                        ↓
                        Backend: auth_tools → auth_service
                                        ↓
                        JWT token generation + session creation
                                        ↓
                        Response: { token, user, expiresIn }
```

### Application Deployment Flow
```
User → MarketplacePage → select app → DeploymentModal
                                            ↓
                        Configure: server, ports, env vars
                                            ↓
                        MCP call: install_app(server_id, app_id, config)
                                            ↓
                        Backend: deployment_service
                                            ↓
                        SSH to server → Docker commands
                                            ↓
                        Response: { containerId, accessUrls }
```

## Security Architecture

### Credential Protection
- **AES-256** encryption for stored SSH credentials
- **bcrypt** (cost factor 12) for password hashing
- **PBKDF2** key derivation for master password

### Authentication
- **JWT tokens** with configurable expiration
- **Session management** with activity tracking
- **Cookie-based** secure token storage

### Input Validation
- **Pydantic** models for backend validation
- **zod** schemas for frontend validation
- Rate limiting on authentication endpoints

See [Security Documentation](../security/README.md) for details.

## Related Documentation

- [Full Architecture Details](../ARCHITECTURE.md) - Comprehensive architecture document
- [API Reference](../api/README.md) - MCP tools documentation
- [Developer Guide](../developer/README.md) - Development setup
- [Security](../security/README.md) - Security architecture

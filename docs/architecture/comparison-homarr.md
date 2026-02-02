# Comprehensive Comparison: Homarr vs Tomo

## Executive Summary

| Aspect | Homarr | Tomo |
|--------|--------|-------------------|
| **Primary Purpose** | Dashboard/Homepage for services | Infrastructure management platform |
| **Target User** | Users viewing/accessing services | Users managing/deploying services |
| **Core Function** | Aggregates links & status widgets | SSH/Agent-based server control |
| **Philosophy** | "View and monitor" | "Manage and deploy" |

---

## 1. Purpose & Philosophy

### Homarr
- **Dashboard-first**: A beautiful homepage to access all your self-hosted services
- **Read-mostly**: Displays status, links, and widgets - limited write operations
- **User-facing**: Designed as a daily landing page for tomo users
- **Integration-heavy**: Connects to 30+ existing services to display their status

### Tomo
- **Management-first**: Control plane for infrastructure operations
- **Write-heavy**: Deploy apps, configure servers, execute commands
- **Admin-facing**: Designed for operators managing the infrastructure
- **Self-contained**: Deploys and manages applications itself

---

## 2. Feature Comparison

| Feature | Homarr | Tomo |
|---------|--------|-------------------|
| **App Dashboard** | Primary feature | Secondary (installed apps view) |
| **Drag & Drop UI** | Extensive grid system | Fixed layouts |
| **Widget System** | Weather, calendar, RSS, etc. | No widgets |
| **Server SSH Access** | No | Full SSH management |
| **App Deployment** | Links to existing apps | Docker deployment from marketplace |
| **Agent-based Control** | No | WebSocket agents on servers |
| **Command Execution** | No | Remote shell commands |
| **Docker Management** | Start/stop via integration | Full lifecycle (deploy, configure, remove) |
| **Credential Storage** | Integration tokens | AES-256 encrypted SSH keys |
| **Multi-server** | Via integrations | Native multi-server architecture |
| **Marketplace** | No | Git-based app catalogs |
| **Server Provisioning** | No | Guided Docker installation |
| **Metrics Collection** | Via Prometheus/integrations | Native SSH/Agent metrics |
| **Activity Audit** | No | Full audit logging |
| **Data Retention** | No | Configurable policies |
| **Backup/Restore** | Config export | Encrypted full backups |

---

## 3. Technology Stack

| Component | Homarr | Tomo |
|-----------|--------|-------------------|
| **Frontend** | Next.js (TypeScript) | React 19 + Vite (TypeScript) |
| **Backend** | Next.js API / tRPC | FastMCP (Python) |
| **Database** | PostgreSQL/SQLite | SQLite |
| **Styling** | CSS Modules | TailwindCSS + MUI |
| **State** | React Query + tRPC | React Context + use-mcp |
| **API Protocol** | tRPC (type-safe RPC) | MCP (Model Context Protocol) |
| **Real-time** | WebSocket + Redis | WebSocket (native) |
| **Auth** | NextAuth (OIDC, LDAP, creds) | JWT + Sessions (creds only) |
| **Build Tool** | Turbo (monorepo) | Vite + pytest |
| **Package Manager** | pnpm | Yarn (frontend) / pip (backend) |
| **Containerization** | Docker | Docker + supervisord + nginx |

---

## 4. Architecture Differences

### Homarr

```
┌─────────────────────────────────────┐
│           User Browser              │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Next.js App (SSR + CSR)        │
│  ┌─────────────────────────────┐    │
│  │   tRPC API Layer            │    │
│  └──────────────┬──────────────┘    │
│                 │                   │
│  ┌──────────────▼──────────────┐    │
│  │   Integration Clients       │    │
│  │ (Plex, Sonarr, qBit, etc.)  │    │
│  └──────────────┬──────────────┘    │
└─────────────────┼───────────────────┘
                  │ HTTP APIs
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌───────┐   ┌───────┐     ┌───────┐
│ Plex  │   │Sonarr │     │ More  │
└───────┘   └───────┘     └───────┘
```

### Tomo

```
┌─────────────────────────────────────┐
│           User Browser              │
└──────────────┬──────────────────────┘
               │ MCP over WebSocket
┌──────────────▼──────────────────────┐
│         FastMCP Server              │
│  ┌─────────────────────────────┐    │
│  │   Tool Loader (50+ tools)   │    │
│  └──────────────┬──────────────┘    │
│                 │                   │
│  ┌──────────────▼──────────────┐    │
│  │   Command Router            │    │
│  │   (Agent → SSH fallback)    │    │
│  └──────────────┬──────────────┘    │
└─────────────────┼───────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │ WebSocket   │ SSH         │
    ▼             ▼             ▼
┌───────┐   ┌───────┐     ┌───────┐
│Agent 1│   │Server2│     │ServerN│
│(WS)   │   │(SSH)  │     │(SSH)  │
└───────┘   └───────┘     └───────┘
```

---

## 5. Security Comparison

| Security Feature | Homarr | Tomo |
|------------------|--------|-------------------|
| **Password Hashing** | bcrypt | bcrypt (12 rounds, NIST compliant) |
| **Credential Encryption** | AES-256-CBC | AES-256 (Fernet) |
| **SSO Support** | OIDC, LDAP | Credentials only |
| **Rate Limiting** | Unknown | 5 attempts, 15-min lockout |
| **Audit Logging** | No | Full activity trail |
| **Log Sanitization** | Unknown | Auto-masks secrets |
| **Permission Levels** | Groups & permissions | Roles (admin, user, readonly) |
| **Account Lockout** | Unknown | Automatic |
| **Settings Checksums** | No | SHA256 verification |
| **Agent Auth** | N/A | Registration codes + tokens |

---

## 6. Deployment & Scalability

| Aspect | Homarr | Tomo |
|--------|--------|-------------------|
| **Container Image** | Yes | Yes |
| **Kubernetes/Helm** | Extensive | Docker Compose |
| **Horizontal Scaling** | Redis + workers | Single instance |
| **Multi-user Scale** | Hundreds of users | Small team (< 10) |
| **Resource Usage** | Moderate (Node.js) | Light (Python + SQLite) |
| **ARM Support** | Raspberry Pi | Any Python platform |

---

## 7. Integration Philosophy

### Homarr: "Connect to everything"
- Integrates with 30+ existing services via their APIs
- Displays status from Plex, Sonarr, qBittorrent, Pi-hole, etc.
- Acts as a unified view layer
- Doesn't deploy or manage services

### Tomo: "Deploy and manage everything"
- Deploys applications via Docker to remote servers
- Manages the full lifecycle (install, configure, monitor, remove)
- SSH/Agent access for direct control
- Self-contained - doesn't require external services

---

## 8. Use Case Matrix

| Use Case | Homarr | Tomo |
|----------|--------|-------------------|
| "I want a pretty homepage for my services" | Perfect | Overkill |
| "I want to see all my service statuses" | Great | Limited |
| "I want to deploy a new app to my server" | No | Perfect |
| "I want to manage SSH access to servers" | No | Perfect |
| "I want to run commands on remote servers" | No | Perfect |
| "I want calendar/weather/RSS widgets" | Great | No |
| "I want to manage Docker containers" | Basic | Full control |
| "I want SSO with my existing auth" | OIDC/LDAP | Standalone |
| "I want to provision new servers" | No | Perfect |
| "I want audit logs for compliance" | No | Yes |

---

## 9. Complementary, Not Competing

These tools serve **different layers** of the tomo stack:

```
┌─────────────────────────────────────────────┐
│  User Layer: Homarr                         │
│  - Daily homepage                           │
│  - Service status at a glance               │
│  - Quick access to apps                     │
├─────────────────────────────────────────────┤
│  Management Layer: Tomo        │
│  - Deploy applications                      │
│  - Configure servers                        │
│  - Monitor infrastructure                   │
├─────────────────────────────────────────────┤
│  Infrastructure: Docker, VMs, Hardware      │
└─────────────────────────────────────────────┘
```

**Ideal Setup**: Use Tomo to deploy and manage your services (including Homarr!), then use Homarr as your daily dashboard.

---

## 10. Summary

| Dimension | Winner |
|-----------|--------|
| **Dashboard/Homepage** | Homarr |
| **Visual Customization** | Homarr |
| **Service Integrations** | Homarr |
| **SSO/Enterprise Auth** | Homarr |
| **Infrastructure Control** | Tomo |
| **App Deployment** | Tomo |
| **Security/Audit** | Tomo |
| **Server Management** | Tomo |
| **Agent Architecture** | Tomo |
| **Resource Efficiency** | Tomo |

**Bottom line**: Homarr is a **dashboard**, Tomo is a **control plane**. They solve different problems and work well together.

---

## References

- [Homarr Documentation](https://homarr.dev/)
- [Homarr GitHub](https://github.com/homarr-labs/homarr)

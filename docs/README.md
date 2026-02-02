# Tomo Documentation

Welcome to the Tomo documentation. This guide provides comprehensive information for users, developers, and operators of the Tomo platform.

## Quick Links

| Section | Description |
|---------|-------------|
| [Architecture](architecture/README.md) | System design, components, and technical decisions |
| [Developer Guide](developer/README.md) | Development setup, contributing, and extending |
| [API Reference](api/README.md) | MCP tools and API documentation |
| [Features](features/README.md) | User-facing feature documentation |
| [Security](security/README.md) | Security architecture and best practices |
| [Operations](operations/README.md) | Deployment, monitoring, and administration |
| [Testing](testing/README.md) | Test strategy and execution |

## Overview

Tomo is a self-hosted web application for managing tomo infrastructure. It provides:

- **Server Management** - Connect to servers via SSH, monitor health, and manage configurations
- **Application Marketplace** - Browse, deploy, and manage containerized applications
- **Monitoring & Metrics** - Real-time dashboards, logs, and system metrics
- **Security** - Encrypted credentials, JWT authentication, and audit logging
- **Backup & Recovery** - Encrypted backups with CLI management

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, TypeScript, Vite, TailwindCSS, React Query |
| Backend | Python 3.11+, FastMCP, SQLite, Paramiko, Pydantic |
| Protocol | Model Context Protocol (MCP) |
| Auth | JWT + bcrypt, AES-256 credential encryption |
| Deployment | Docker, nginx, systemd, RPM packaging |

## Documentation Structure

```
docs/
├── README.md                   # This file - documentation index
├── ARCHITECTURE.md             # Comprehensive system architecture
├── SECURITY_REVIEW.md          # Security assessment
├── architecture/               # Architecture details
│   ├── README.md               # Architecture overview
│   ├── decisions.md            # Architecture Decision Records (ADRs)
│   ├── settings.md             # Settings system architecture
│   ├── registration.md         # Registration feature design
│   └── marketplace-deployment.md
├── developer/                  # Developer documentation
│   ├── README.md               # Developer quick start
│   ├── agents.md               # AI agent workflow guidance
│   ├── mcp-protocol.md         # MCP protocol integration
│   ├── settings-implementation.md
│   └── frontend-settings-integration.md
├── api/                        # API reference
│   └── README.md               # Complete API documentation
├── features/                   # Feature documentation
│   ├── README.md               # Features index
│   ├── applications.md         # Application management
│   ├── marketplace.md          # Marketplace system
│   ├── deployment.md           # Deployment workflows
│   └── data-retention/         # Data retention docs
├── security/                   # Security documentation
│   ├── README.md               # Security overview
│   ├── cookie-auth.md          # Cookie-based auth
│   └── penetration-test-*.md   # Security audits
├── operations/                 # Operations documentation
│   ├── README.md               # Operations overview
│   └── data-retention-monitoring.md
├── compliance/                 # Compliance documentation
│   ├── README.md               # Compliance overview
│   └── data-retention.md       # Data retention compliance
├── admin/                      # Administrative procedures
│   └── data-retention-security-procedures.md
├── technical/                  # Technical specifications
│   ├── README.md               # Technical docs index
│   ├── database-schema.md      # Database schema design
│   ├── logging.md              # Logging specification
│   └── data-retention-architecture.md
├── testing/                    # Testing documentation
│   ├── README.md               # Test strategy overview
│   ├── quick-start.md          # Test execution guide
│   └── settings-test-suite.md  # Settings test summary
└── plans/                      # Implementation plans
    ├── README.md               # Plans index
    └── *.md                    # Phase and feature plans
```

## Getting Started

### For Users

1. **[Features Overview](features/README.md)** - Learn what Tomo can do
2. **[Application Marketplace](features/marketplace.md)** - Browse and deploy apps
3. **[Data Retention](features/data-retention/README.md)** - Configure data cleanup policies

### For Developers

1. **[Developer Quick Start](developer/README.md)** - Set up your development environment
2. **[Architecture Overview](architecture/README.md)** - Understand the system design
3. **[API Reference](api/README.md)** - Explore available MCP tools
4. **[Contributing](developer/README.md#contributing-guidelines)** - How to contribute

### For Operators

1. **[Deployment Guide](operations/README.md)** - Deploy to production
2. **[Security Best Practices](security/README.md)** - Secure your installation
3. **[Monitoring](operations/README.md#monitoring)** - Set up monitoring and alerting

## Related Resources

- **[Main README](../README.md)** - Project overview and quick start
- **[GitHub Repository](https://github.com/cbabil/tomo)** - Source code and issues
- **[Implementation Plans](plans/)** - Historical implementation roadmaps

## Version History

See [release notes](../CHANGELOG.md) for version history and migration guides.

# Tomo

Welcome to the **Tomo** documentation wiki.

Tomo is a self-hosted platform for managing your tomo infrastructure - connect servers, deploy applications, and monitor everything from a single dashboard.

---

## Quick Navigation

| I want to... | Go to |
|--------------|-------|
| **Install Tomo** | [[Installation]] |
| **Get started after installing** | [[Getting-Started]] |
| **Add and manage servers** | [[Server-Management]] |
| **Deploy applications** | [[Application-Deployment]] |
| **Configure settings** | [[Configuration]] |
| **Fix a problem** | [[Troubleshooting]] |
| **Contribute to the project** | [[Development]] |

---

## Installation Options

| Method | Best For | Guide |
|--------|----------|-------|
| **DEB Package** | Debian/Ubuntu servers | [[Installation#deb-package]] |
| **Docker** | Containerized deployments | [[Installation#docker]] |
| **From Source** | Development/customization | [[Installation#from-source]] |

---

## Features

### Server Management
- Connect via SSH (password or key authentication)
- Real-time health monitoring (CPU, memory, disk)
- Automated Docker and Agent provisioning
- Multi-server support

### Application Marketplace
- Browse containerized applications
- One-click deployment to any server
- Custom environment variables and ports
- Git-based catalog synchronization

### Security
- AES-256 encrypted credentials
- JWT authentication with bcrypt
- NIST SP 800-63B password policy
- Session management and audit logging

### Remote Agent
- WebSocket-based communication
- Secure command execution
- Automatic token rotation
- Docker container management

---

## System Requirements

### For the Server (where Tomo runs)

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Debian 12 / Ubuntu 22.04 | Ubuntu 24.04 LTS |
| **CPU** | 1 core | 2+ cores |
| **RAM** | 1 GB | 2+ GB |
| **Disk** | 5 GB | 20+ GB |
| **Network** | Internet access | Static IP |

### For Managed Servers (where you deploy apps)

| Component | Requirement |
|-----------|-------------|
| **OS** | Any Linux with SSH |
| **Docker** | Recommended (can be auto-installed) |
| **Agent** | Optional (for enhanced monitoring) |

---

## Getting Help

- **[[Troubleshooting]]** - Common issues and solutions
- **[[FAQ]]** - Frequently asked questions
- **[GitHub Issues](https://github.com/cbabil/tomo/issues)** - Report bugs or request features

---

## License

Tomo is proprietary software. See [LICENSE](https://github.com/cbabil/tomo/blob/main/LICENSE) for details.

For licensing inquiries: christophe@babilotte.com

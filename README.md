# Homelab Assistant

A self-hosted web application for managing homelab infrastructure. Connect to remote servers via SSH, deploy Docker applications through an extensible catalog, and monitor your infrastructure.

## Features

### Server Management
- **SSH Connection Management** - Connect to servers using password or SSH key authentication
- **Server Health Monitoring** - Real-time status checks and connectivity testing
- **Multi-Server Support** - Manage multiple homelab servers from one interface

### Application Deployment
- **App Catalog** - Browse and deploy containerized applications
- **One-Click Install** - Deploy apps with pre-configured Docker Compose templates
- **Custom Configuration** - Override environment variables and port mappings
- **Built-in Apps**: Portainer, Nginx Proxy Manager, Nextcloud, Jellyfin, Pi-hole

### Monitoring & Metrics
- **Server Metrics** - CPU, memory, disk usage monitoring
- **Container Status** - Track running containers across servers
- **Activity Logging** - Audit trail of all operations
- **Dashboard** - Unified view of infrastructure health

### Security
- **AES-256 Credential Encryption** - Secure storage of SSH credentials
- **JWT Authentication** - Secure user sessions with bcrypt password hashing
- **Role-Based Access** - Admin and user roles with permission controls
- **Input Validation** - Protection against injection attacks
- **Rate Limiting** - Brute force protection on auth endpoints

### Backup & Recovery
- **Encrypted Backups** - PBKDF2 + Fernet encryption for backup files
- **CLI Export/Import** - Command-line backup management
- **Full Data Backup** - Users, servers, and settings included

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ and Yarn
- Docker (on target servers)

### Development Setup

```bash
# Clone repository
git clone https://github.com/cbabil/homelab.git
cd homelab

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start backend
DATA_DIRECTORY="$(pwd)/data" python src/main.py

# Frontend setup (new terminal)
cd frontend
yarn install
yarn dev
```

Access the application at http://localhost:5173

### Production Deployment (RPM)

```bash
# Build RPM package
rpmbuild -ba packaging/homelab-assistant.spec

# Install
sudo dnf install homelab-assistant-1.0.0-1.x86_64.rpm

# Start service
sudo systemctl start homelab-assistant
sudo systemctl enable homelab-assistant
```

## Project Structure

```
homelab/
├── frontend/                 # React TypeScript frontend
│   ├── src/
│   │   ├── components/      # UI components
│   │   ├── services/        # MCP client & API services
│   │   ├── hooks/           # Custom React hooks
│   │   └── pages/           # Application pages
│   └── package.json
├── backend/                  # Python MCP server
│   ├── src/
│   │   ├── main.py          # FastMCP server entry
│   │   ├── tools/           # MCP tool implementations
│   │   ├── services/        # Business logic services
│   │   ├── models/          # Pydantic data models
│   │   └── lib/             # Security & utilities
│   ├── data/
│   │   └── catalog/         # App catalog YAML files
│   └── tests/               # Unit tests
├── packaging/                # RPM & systemd files
│   ├── homelab-assistant.spec
│   ├── homelab-assistant.service
│   └── config.yaml.example
└── docs/                     # Documentation & plans
```

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, TypeScript, Vite, TailwindCSS |
| Backend | Python 3.11+, FastMCP, SQLite, Paramiko |
| Protocol | Model Context Protocol (MCP) |
| Auth | JWT + bcrypt, AES-256 credential encryption |
| Deployment | RPM packaging, systemd |

## CLI Commands

```bash
# Create admin user
python src/cli.py create-admin

# Export encrypted backup
python src/cli.py export -o backup.enc -p

# Import backup
python src/cli.py import -i backup.enc -p

# Initialize database
python src/cli.py init-db
```

## Configuration

Configuration file: `/etc/homelab-assistant/config.yaml`

```yaml
server:
  host: 127.0.0.1
  port: 8080

security:
  session_timeout_minutes: 60
  max_login_attempts: 5
  lockout_duration_minutes: 15

metrics:
  enabled: true
  collection_interval_seconds: 300
  retention_days: 30
```

## App Catalog

Add custom apps by creating YAML files in `data/catalog/`:

```yaml
name: my-app
description: My custom application
category: productivity
docker_compose: |
  version: '3'
  services:
    app:
      image: myapp:latest
      ports:
        - "8080:80"
env_vars:
  - name: APP_SECRET
    description: Application secret key
    required: true
```

## API (MCP Tools)

| Tool | Description |
|------|-------------|
| `health_check` | System health status |
| `login` / `logout` | Authentication |
| `list_servers` / `add_server` | Server management |
| `test_connection` | SSH connectivity test |
| `list_apps` / `deploy_app` | App catalog operations |
| `get_server_metrics` | CPU, memory, disk stats |
| `get_activity_log` | Audit trail |
| `export_backup` / `import_backup` | Backup operations |

## Development

### Running Tests

```bash
# Backend tests
cd backend
source venv/bin/activate
PYTHONPATH=src pytest tests/unit/ -v

# Frontend tests
cd frontend
yarn test
yarn test:e2e
```

### Code Quality

```bash
# Frontend linting
yarn lint
yarn type-check

# Backend type checking
mypy src/
```

## Security Notes

- Credentials encrypted at rest with AES-256
- Passwords hashed with bcrypt (cost factor 12)
- JWT tokens with configurable expiration
- Constant-time comparison for sensitive operations
- Automatic log sanitization (passwords, tokens masked)
- Input validation on all endpoints
- Rate limiting on authentication

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Repository**: [github.com/cbabil/homelab](https://github.com/cbabil/homelab)

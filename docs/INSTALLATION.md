# Installation Guide

This guide covers installing Tomo on your system.

## Prerequisites

- **Python** 3.12 or later
- **uv** (fast Python package manager) - [Install uv](https://docs.astral.sh/uv/install.sh)
- **Bun** (fast JavaScript runtime) - [Install Bun](https://bun.sh)
- **Git** (for source installation)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/cbabil/tomo.git
cd tomo

# Set up backend (using uv)
cd backend
uv sync  # Creates venv and installs all dependencies from uv.lock

# Configure environment
cp ../.env.example .env
# Edit .env and set required values (see below)

# Set up frontend
cd ../frontend
bun install

# Set up CLI
cd ../cli
bun install
```

## Configuration

### Generate Required Secrets

Before starting the application, generate unique secrets:

```bash
# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Generate TOMO_MASTER_PASSWORD
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate TOMO_SALT
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

### Environment File

Create `.env` in the project root with these required values:

```bash
# Required
JWT_SECRET_KEY=<your-generated-jwt-secret>
TOMO_MASTER_PASSWORD=<your-generated-master-password>
TOMO_SALT=<your-generated-salt>

# Optional
PYTHON_ENV=development
MCP_LOG_LEVEL=INFO
```

See [ENV_REFERENCE.md](./ENV_REFERENCE.md) for all configuration options.

## Running the Application

### Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python src/main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
bun dev
```

Access the application at http://localhost:3000

### Production Mode

**Backend:**
```bash
cd backend
source venv/bin/activate
PYTHON_ENV=production python src/main.py
```

**Frontend:**
```bash
cd frontend
bun build
bun preview  # or serve with your preferred web server
```

## Initial Setup

1. Navigate to http://localhost:3000
2. You'll be redirected to the setup page
3. Create your admin account
4. Start managing your tomo!

Alternatively, use the CLI:
```bash
cd cli
bun tomo admin create
```

## Updating

```bash
# Pull latest changes
git pull

# Update backend dependencies
cd backend
uv sync

# Update frontend dependencies
cd ../frontend
bun install

# Update CLI dependencies
cd ../cli
bun install
```

## Uninstalling

```bash
# Remove the installation directory
rm -rf tomo

# Or keep configuration and remove just the code:
# Backup your .env and backend/data/ directory first
```

---

## Platform-Specific Instructions

### Ubuntu/Debian

```bash
# Install prerequisites
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git curl unzip

# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install bun (fast JavaScript runtime)
curl -fsSL https://bun.sh/install | bash

# Clone and install
git clone https://github.com/cbabil/tomo.git
cd tomo
# Follow Quick Start instructions above
```

### macOS

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install prerequisites
brew install python git uv bun

# Clone and install
git clone https://github.com/cbabil/tomo.git
cd tomo
# Follow Quick Start instructions above
```

### Windows

1. Install [Python 3.12+](https://www.python.org/downloads/)
2. Install [Git](https://git-scm.com/downloads)
3. Install [uv](https://docs.astral.sh/uv/getting-started/installation/): `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
4. Install [Bun](https://bun.sh/docs/installation): `powershell -c "irm bun.sh/install.ps1 | iex"`

```powershell
# Clone repository
git clone https://github.com/cbabil/tomo.git
cd tomo

# Backend setup
cd backend
uv sync

# Frontend setup
cd ..\frontend
bun install

# CLI setup
cd ..\cli
bun install
```

---

## DEB Package Installation (Debian/Ubuntu)

The easiest way to install on Debian-based systems.

### Download and Install

```bash
# Download the latest .deb package from GitHub Releases
wget https://github.com/cbabil/tomo/releases/latest/download/tomo_1.0.0-1_amd64.deb

# Install the package
sudo apt install ./tomo_1.0.0-1_amd64.deb
```

### Post-Installation Setup

1. **Configure CORS origins** (required for external access):
   ```bash
   sudo nano /etc/tomo/environment
   # Update ALLOWED_ORIGINS to your domain
   ```

2. **Start the service**:
   ```bash
   sudo systemctl start tomo
   ```

3. **Create admin account**:
   ```bash
   tomo admin create
   ```

4. **Access the web interface**:
   - http://localhost (or your domain)

### Service Management

```bash
# Start/stop/restart
sudo systemctl start tomo
sudo systemctl stop tomo
sudo systemctl restart tomo

# Check status
sudo systemctl status tomo

# View logs
journalctl -u tomo -f
```

### Upgrading

```bash
# Download new version
wget https://github.com/cbabil/tomo/releases/latest/download/tomo_X.Y.Z-1_amd64.deb

# Install (upgrades existing installation)
sudo apt install ./tomo_X.Y.Z-1_amd64.deb

# Service restarts automatically
```

### Uninstalling

```bash
# Remove (keeps data and configuration)
sudo apt remove tomo

# Purge (removes everything including data)
sudo apt purge tomo
```

### File Locations

| Purpose | Path |
|---------|------|
| Application | `/opt/tomo/` |
| Frontend | `/var/www/tomo/` |
| Data | `/var/lib/tomo/` |
| Logs | `/var/log/tomo/` |
| Config | `/etc/tomo/` |
| CLI | `/usr/local/bin/tomo` |

---

## Docker Installation

*Coming soon - Docker installation will be available in a future release.*

## Systemd Service (Linux)

To run Tomo as a system service:

**Create service file:** `/etc/systemd/system/tomo-backend.service`

```ini
[Unit]
Description=Tomo Backend
After=network.target

[Service]
Type=simple
User=tomo
WorkingDirectory=/opt/tomo/backend
Environment=PYTHON_ENV=production
ExecStart=/opt/tomo/backend/venv/bin/python src/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable tomo-backend
sudo systemctl start tomo-backend
```

---

## Reverse Proxy Configuration

### Nginx

```nginx
server {
    listen 80;
    server_name tomo.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name tomo.example.com;

    ssl_certificate /etc/ssl/certs/tomo.crt;
    ssl_certificate_key /etc/ssl/private/tomo.key;

    # Frontend
    location / {
        root /opt/tomo/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend MCP
    location /mcp {
        proxy_pass http://127.0.0.1:8000/mcp;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues and solutions.

## Next Steps

- [CLI Reference](./CLI_REFERENCE.md) - Learn CLI commands
- [Environment Variables](./ENV_REFERENCE.md) - Configure your installation
- [Troubleshooting](./TROUBLESHOOTING.md) - Resolve common issues

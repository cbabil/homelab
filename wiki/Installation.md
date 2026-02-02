# Installation

This guide covers all installation methods for Tomo.

---

## Quick Install (Recommended)

For Debian/Ubuntu systems, use the DEB package:

```bash
# Download
wget https://github.com/cbabil/tomo/releases/latest/download/tomo_1.0.0-1_amd64.deb

# Install
sudo apt install ./tomo_1.0.0-1_amd64.deb

# Start
sudo systemctl start tomo

# Create admin account
tomo admin create
```

Then open **http://your-server-ip** in your browser.

---

## Installation Methods

### DEB Package

**Supported:** Debian 12+, Ubuntu 22.04+

#### Step 1: Download

```bash
wget https://github.com/cbabil/tomo/releases/latest/download/tomo_1.0.0-1_amd64.deb
```

#### Step 2: Install

```bash
sudo apt install ./tomo_1.0.0-1_amd64.deb
```

This automatically installs all dependencies:
- Python 3.11+
- Node.js 18+
- Nginx
- Required Python packages

#### Step 3: Configure (Optional)

Edit the configuration file:

```bash
sudo nano /etc/tomo/environment
```

Key settings:
```bash
# Your domain or IP (for CORS)
ALLOWED_ORIGINS=http://localhost,https://tomo.example.com

# Session timeout in minutes
SESSION_TIMEOUT=60
```

#### Step 4: Start the Service

```bash
sudo systemctl start tomo
sudo systemctl enable tomo  # Start on boot
```

#### Step 5: Create Admin Account

```bash
tomo admin create
```

Follow the prompts to set username and password.

#### Step 6: Access Web UI

Open your browser to:
- **Local:** http://localhost
- **Remote:** http://your-server-ip

---

### Docker

**Requirements:** Docker and Docker Compose

#### Step 1: Clone Repository

```bash
git clone https://github.com/cbabil/tomo.git
cd tomo
```

#### Step 2: Configure Environment

```bash
cp .env.example .env
nano .env
```

Set required values:
```bash
JWT_SECRET_KEY=<generate-random-64-char-string>
TOMO_MASTER_PASSWORD=<generate-random-32-char-string>
TOMO_SALT=<generate-random-16-char-string>
```

Generate secrets:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

#### Step 3: Start Containers

```bash
docker compose up -d
```

#### Step 4: Create Admin Account

```bash
docker compose exec backend tomo admin create
```

#### Step 5: Access Web UI

Open http://localhost:3000

---

### From Source

**For development or customization.**

#### Prerequisites

| Tool | Install Command |
|------|-----------------|
| Python 3.12+ | `apt install python3` |
| uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Bun | `curl -fsSL https://bun.sh/install \| bash` |
| Git | `apt install git` |

#### Step 1: Clone Repository

```bash
git clone https://github.com/cbabil/tomo.git
cd tomo
```

#### Step 2: Install Backend

```bash
cd backend
uv sync --all-extras
```

#### Step 3: Install Frontend

```bash
cd ../frontend
bun install
```

#### Step 4: Install CLI

```bash
cd ../cli
bun install
```

#### Step 5: Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

#### Step 6: Start Development Servers

Terminal 1 (Backend):
```bash
cd backend
uv run python src/main.py
```

Terminal 2 (Frontend):
```bash
cd frontend
bun run dev
```

Access at http://localhost:5173

---

## Post-Installation

After installation, complete these steps:

### 1. Create Admin Account

```bash
tomo admin create
```

### 2. Log In

Open the web UI and log in with your admin credentials.

### 3. Add Your First Server

1. Go to **Servers** page
2. Click **Add Server**
3. Enter server details (hostname, SSH credentials)
4. The system will test connectivity and offer to install Docker/Agent

### 4. Deploy an Application

1. Go to **Marketplace**
2. Browse available applications
3. Click **Install** on any app
4. Select target server
5. Configure settings and deploy

---

## File Locations

| Purpose | Path |
|---------|------|
| Application | `/opt/tomo/` |
| Web UI | `/var/www/tomo/` |
| Database | `/var/lib/tomo/` |
| Logs | `/var/log/tomo/` |
| Config | `/etc/tomo/` |
| CLI | `/usr/local/bin/tomo` |

---

## Service Management

```bash
# Start/Stop/Restart
sudo systemctl start tomo
sudo systemctl stop tomo
sudo systemctl restart tomo

# Check status
sudo systemctl status tomo

# View logs
journalctl -u tomo -f
```

---

## Upgrading

### DEB Package

```bash
# Download new version
wget https://github.com/cbabil/tomo/releases/latest/download/tomo_X.Y.Z-1_amd64.deb

# Install (upgrades existing)
sudo apt install ./tomo_X.Y.Z-1_amd64.deb

# Service restarts automatically
```

### Docker

```bash
cd tomo
git pull
docker compose down
docker compose up -d --build
```

---

## Uninstalling

### DEB Package

```bash
# Keep data and config
sudo apt remove tomo

# Remove everything
sudo apt purge tomo
```

### Docker

```bash
docker compose down -v  # -v removes volumes
```

---

## Next Steps

- [[Getting-Started]] - First steps after installation
- [[Server-Management]] - Add and manage servers
- [[Configuration]] - Configure settings
- [[Troubleshooting]] - Solve common problems

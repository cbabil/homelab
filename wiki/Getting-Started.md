# Getting Started

This guide walks you through your first steps after installing Tomo.

---

## First Login

### 1. Open the Web UI

After installation, open your browser to:
- **Local:** http://localhost (DEB package) or http://localhost:5173 (development)
- **Remote:** http://your-server-ip

### 2. Log In

Enter the admin credentials you created during installation:
- Username (default: `admin`)
- Password (the one you set)

---

## Dashboard Overview

After logging in, you'll see the main dashboard:

| Section | Description |
|---------|-------------|
| **Server Status** | Overview of connected servers |
| **Recent Activity** | Latest actions and events |
| **System Health** | CPU, memory, disk usage |
| **Quick Actions** | Common tasks |

---

## Add Your First Server

### Step 1: Navigate to Servers

Click **Servers** in the left navigation menu.

### Step 2: Click Add Server

Click the **Add Server** button in the top right.

### Step 3: Enter Server Details

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Friendly name | `Production Server` |
| **Hostname** | IP or domain | `192.168.1.100` |
| **Port** | SSH port | `22` |
| **Username** | SSH user | `root` or `ubuntu` |

### Step 4: Choose Authentication

**Option A: Password**
- Enter the SSH password

**Option B: SSH Key** (Recommended)
- Upload your private key file
- Enter passphrase if required

### Step 5: Test Connection

Click **Test Connection** to verify SSH access.

### Step 6: Save

Click **Save** to add the server.

---

## Install Docker (Optional)

If your server doesn't have Docker installed:

1. Go to **Servers** page
2. Click on your server
3. Look for the **Docker Status** indicator
4. If not installed, click **Install Docker**
5. Wait for installation to complete

---

## Install Agent (Optional)

The Tomo Agent provides enhanced monitoring and secure command execution:

1. Go to **Servers** page
2. Click on your server
3. Look for **Agent Status**
4. Click **Install Agent**
5. The agent will be deployed automatically

Benefits of the agent:
- Real-time metrics collection
- Secure WebSocket communication
- Docker container management
- Automatic token rotation

---

## Deploy Your First Application

### Step 1: Browse Marketplace

1. Click **Marketplace** in the navigation
2. Browse available applications
3. Use search or filters to find apps

### Step 2: Select an Application

Click on any application to see details:
- Description
- Requirements
- Configuration options

### Step 3: Install

1. Click **Install**
2. Select the target server
3. Configure settings (ports, environment variables)
4. Click **Deploy**

### Step 4: Monitor Deployment

Watch the deployment progress. Once complete, you'll see:
- Application status
- Access URL
- Container logs

---

## Recommended First Applications

| Application | Purpose | Difficulty |
|-------------|---------|------------|
| **Portainer** | Docker management UI | Easy |
| **Nginx Proxy Manager** | Reverse proxy with SSL | Easy |
| **Uptime Kuma** | Monitoring dashboard | Easy |
| **Nextcloud** | File sync and share | Medium |

---

## Configure Settings

### Access Settings

Click the **gear icon** or go to **Settings** in the navigation.

### Key Settings

| Setting | Purpose |
|---------|---------|
| **Session Timeout** | Auto-logout after inactivity |
| **Timezone** | Display times in your timezone |
| **Notifications** | Enable/disable alerts |
| **Data Retention** | How long to keep logs |

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + K` | Quick search |
| `Ctrl + N` | New server |
| `Esc` | Close dialogs |

---

## Getting Help

- **[[Troubleshooting]]** - Common issues and solutions
- **[[FAQ]]** - Frequently asked questions
- **[GitHub Issues](https://github.com/cbabil/tomo/issues)** - Report bugs

---

## Next Steps

- [[Server-Management]] - Advanced server configuration
- [[Application-Deployment]] - Deploy more applications
- [[Configuration]] - Customize settings
- [[Security-Settings]] - Harden your installation

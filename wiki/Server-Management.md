# Server Management

This guide covers adding, configuring, and managing servers in Tomo.

---

## Adding a Server

### Prerequisites

Before adding a server, ensure:
- SSH access is available (port 22 or custom)
- You have valid credentials (password or SSH key)
- The server is reachable from where Tomo runs

### Add via Web UI

1. Navigate to **Servers** page
2. Click **Add Server**
3. Fill in the form:

| Field | Required | Description |
|-------|----------|-------------|
| Name | Yes | Display name for the server |
| Hostname | Yes | IP address or domain name |
| Port | Yes | SSH port (default: 22) |
| Username | Yes | SSH username |
| Auth Type | Yes | Password or SSH Key |

4. Click **Test Connection**
5. Click **Save**

### Add via CLI

```bash
tomo server add \
  --name "Production Server" \
  --hostname 192.168.1.100 \
  --port 22 \
  --username root \
  --auth-type password
```

---

## Authentication Methods

### Password Authentication

Simple but less secure. Enter the SSH password when adding the server.

### SSH Key Authentication (Recommended)

More secure. Upload your private key:

1. Select **SSH Key** as auth type
2. Click **Upload Key** or paste the key content
3. Enter passphrase if the key is encrypted

**Supported key formats:**
- RSA (recommended: 4096 bits)
- ED25519 (recommended: modern, fast)
- ECDSA

**Generate a new key:**
```bash
ssh-keygen -t ed25519 -C "tomo"
```

---

## Server Status

Each server shows real-time status:

| Status | Meaning |
|--------|---------|
| **Online** | Server is reachable and responding |
| **Offline** | Cannot connect to server |
| **Degraded** | Connected but issues detected |
| **Unknown** | Status not yet determined |

### Health Metrics

When connected, you'll see:
- **CPU Usage** - Current processor load
- **Memory Usage** - RAM utilization
- **Disk Usage** - Storage capacity
- **Uptime** - How long the server has been running

---

## Docker Management

### Check Docker Status

The server card shows Docker status:
- **Installed** - Docker is available
- **Not Installed** - Docker not found
- **Unknown** - Status not checked

### Install Docker

If Docker is not installed:

1. Click on the server
2. Find **Docker Status**
3. Click **Install Docker**
4. Wait for installation (may take a few minutes)

The installer handles:
- Package installation
- Service configuration
- User group setup

### View Containers

Once Docker is installed:
1. Click on the server
2. Go to **Containers** tab
3. See all running and stopped containers

---

## Agent Installation

### What is the Agent?

The Tomo Agent is a lightweight service that runs on your servers providing:
- Real-time metrics collection
- Secure command execution
- WebSocket-based communication
- Automatic security token rotation

### Install Agent

1. Click on the server
2. Find **Agent Status**
3. Click **Install Agent**
4. Wait for deployment

### Agent Requirements

- Python 3.11+ (auto-installed)
- Network access to Tomo
- Port 8765 (configurable)

### Agent Status

| Status | Meaning |
|--------|---------|
| **Connected** | Agent is running and communicating |
| **Disconnected** | Agent not responding |
| **Not Installed** | Agent not deployed |
| **Outdated** | Agent version mismatch |

### Update Agent

```bash
tomo agent update <server-id>
```

Or via web UI: **Server** > **Agent** > **Update**

---

## Server Actions

### Edit Server

1. Go to **Servers** page
2. Click the **Edit** button (pencil icon)
3. Modify settings
4. Click **Save**

### Delete Server

1. Go to **Servers** page
2. Click the **Delete** button (trash icon)
3. Confirm deletion

**Warning:** Deleting a server:
- Removes it from Tomo
- Does NOT affect the actual server
- Does NOT remove deployed applications

### Refresh Status

Click the **Refresh** button to update server status immediately.

### Test Connection

1. Click **Edit** on a server
2. Click **Test Connection**
3. See connection result

---

## Bulk Operations

### Select Multiple Servers

1. Check the boxes next to servers
2. Use the bulk action menu

Available bulk actions:
- **Refresh All** - Update status for all selected
- **Export** - Export server list
- **Delete** - Remove multiple servers

---

## Server Groups (Tags)

Organize servers with tags:

1. Edit a server
2. Add tags (e.g., `production`, `database`, `web`)
3. Filter by tags on the Servers page

---

## Troubleshooting

### Cannot Connect

| Issue | Solution |
|-------|----------|
| Connection refused | Check if SSH is running, verify port |
| Authentication failed | Verify username/password or key |
| Timeout | Check network, firewall rules |
| Host key verification | Accept the new host key |

### Agent Issues

| Issue | Solution |
|-------|----------|
| Agent not starting | Check logs: `journalctl -u tomo-agent` |
| Connection drops | Verify network stability, check firewall |
| Token errors | Rotate token: `tomo agent rotate-token <id>` |

### Docker Issues

| Issue | Solution |
|-------|----------|
| Cannot install | Check internet access on server |
| Permission denied | Verify user is in docker group |
| Service not starting | Check: `systemctl status docker` |

---

## CLI Reference

```bash
# List all servers
tomo server list

# Add a server
tomo server add --name "Server" --hostname 192.168.1.1

# Remove a server
tomo server remove <server-id>

# Test connection
tomo server test <server-id>

# Refresh status
tomo server refresh <server-id>

# Install Docker
tomo server install-docker <server-id>

# Install Agent
tomo agent install <server-id>
```

---

## Next Steps

- [[Application-Deployment]] - Deploy apps to your servers
- [[Marketplace]] - Browse available applications
- [[Troubleshooting]] - Solve common problems

# Server Management Guide

This guide covers everything you need to know about managing servers in Tomo.

## Overview

The Servers page is your central hub for managing SSH connections to your tomo machines. You can:

- Add new servers
- Edit server configurations
- Connect/disconnect from servers
- Install Docker on servers
- Import/export server configurations
- Perform bulk operations

## Navigating to Servers

1. Click **Servers** in the left sidebar, or
2. Click **Manage Servers** from the Dashboard quick actions

## Adding a Server

### Basic Information

1. Click the **Add Server** button
2. Fill in the required fields:

| Field | Description | Example |
|-------|-------------|---------|
| **Server Name** | A friendly identifier | `Media Server` |
| **Hostname** | IP address or domain name | `192.168.1.100` or `server.local` |
| **Port** | SSH port number | `22` (default) |
| **Username** | SSH login user | `admin` or `root` |

### Authentication Methods

#### Password Authentication

1. Select **Password** as the authentication type
2. Enter your SSH password
3. The password is securely stored and encrypted

#### SSH Key Authentication

1. Select **SSH Key** as the authentication type
2. Enter the path to your private key file
3. Example paths:
   - Linux/macOS: `~/.ssh/id_rsa`
   - Windows: `C:\Users\YourName\.ssh\id_rsa`

> **Security Note**: SSH key authentication is recommended for production environments.

### Saving the Server

Click **Save** to add the server. It will appear in your server list with a "Disconnected" status.

## Connecting to a Server

### Single Server Connection

1. Find the server in your list
2. Click the **Connect** button
3. Wait for the connection to establish
4. Status will change to "Connected" (green indicator)

### Connection Indicators

| Status | Color | Description |
|--------|-------|-------------|
| Connected | Green | Active SSH connection |
| Disconnected | Gray | No active connection |
| Connecting | Yellow | Connection in progress |
| Error | Red | Connection failed |

### Connection Errors

If connection fails, check:

1. **Network connectivity** - Can you ping the server?
2. **SSH service** - Is SSH running on the server?
3. **Credentials** - Are username/password correct?
4. **Firewall** - Is port 22 (or custom port) open?
5. **SSH key permissions** - Is your private key readable?

## Editing a Server

1. Find the server in your list
2. Click the **Edit** button (pencil icon)
3. Modify the desired fields
4. Click **Save** to apply changes

> **Note**: You may need to reconnect after changing connection details.

## Deleting a Server

1. Find the server in your list
2. Click the **Delete** button (trash icon)
3. Confirm the deletion in the dialog

> **Warning**: This removes the server configuration. It does not affect the actual server.

## Disconnecting from a Server

1. Find the connected server
2. Click the **Disconnect** button
3. The connection will be closed gracefully

## Server Information

When connected, you can view detailed information about your server:

- **Operating System** - Distribution and version
- **Kernel Version** - Linux kernel version
- **CPU** - Processor information
- **Memory** - RAM total and available
- **Disk Space** - Storage usage
- **Docker Status** - Whether Docker is installed

## Installing Docker

Tomo can install Docker on your servers:

1. Connect to the server
2. Click **Install Docker** button
3. Confirm the installation
4. Wait for the installation to complete

The installer will:
- Detect your Linux distribution
- Install Docker using the official method
- Start the Docker service
- Add your user to the docker group

### Supported Distributions

- Ubuntu 18.04+
- Debian 10+
- CentOS 7+
- Fedora 34+
- Rocky Linux 8+

## Bulk Operations

### Selecting Multiple Servers

1. Click the checkbox on each server card, or
2. Click **Select All** to select all servers

### Bulk Actions

With servers selected, you can:

- **Bulk Connect** - Connect to all selected servers
- **Bulk Disconnect** - Disconnect from all selected servers
- **Clear Selection** - Deselect all servers

## Search and Filter

### Searching Servers

1. Use the search bar at the top of the page
2. Search by:
   - Server name
   - Hostname
   - Username

### Clearing Search

Click the **X** button in the search bar or clear the text.

## Import/Export

### Exporting Servers

1. Click the **Export** button
2. Confirm the security warning
3. A JSON file will be downloaded

> **Security Warning**: Export files may contain sensitive information including SSH keys. Handle with care.

### Importing Servers

1. Click the **Import** button
2. Select your JSON export file
3. Review the import summary
4. Servers will be added to your list

> **Note**: Duplicate servers (same hostname:port) will be skipped.

### Export File Format

```json
{
  "version": "1.0",
  "exported_at": "2024-01-15T10:30:00Z",
  "servers": [
    {
      "name": "Media Server",
      "hostname": "192.168.1.100",
      "port": 22,
      "username": "admin",
      "authType": "password"
    }
  ]
}
```

## Best Practices

### Naming Conventions

Use descriptive names that indicate:
- Server purpose (e.g., "Media Server", "Database Server")
- Location (e.g., "Rack1-Server2")
- Environment (e.g., "Prod-Web1", "Dev-Test")

### Security Recommendations

1. **Use SSH keys** instead of passwords when possible
2. **Use non-root users** with sudo access
3. **Change default SSH port** if exposed to the internet
4. **Keep SSH updated** on all servers
5. **Review access logs** regularly

### Organization Tips

- Group related servers by name prefix
- Use consistent naming patterns
- Document server purposes in a separate wiki/notes
- Regularly audit and remove unused servers

## Troubleshooting

### "Connection Refused"

- SSH service not running: `sudo systemctl start sshd`
- Wrong port: Verify the SSH port in server config
- Firewall blocking: Check `ufw` or `firewalld` rules

### "Authentication Failed"

- Wrong password: Reset and try again
- SSH key not found: Verify the key path
- Key permissions: Run `chmod 600 ~/.ssh/id_rsa`
- User doesn't exist: Verify username on server

### "Host Key Verification Failed"

The server's SSH key changed. This could indicate:
- Server was reinstalled
- Man-in-the-middle attack (rare on local network)

To resolve (if you trust the server):
```bash
ssh-keygen -R hostname
```

### "Connection Timeout"

- Server is offline or unreachable
- Network issues between you and the server
- DNS resolution problems (try IP address instead)

---

**Related Guides:**
- [Quick Start Guide](./QUICK_START.md)
- [Application Deployment Guide](./APPLICATION_DEPLOYMENT.md)
- [Troubleshooting](../TROUBLESHOOTING.md)

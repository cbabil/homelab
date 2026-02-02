# Feature Documentation

This section documents user-facing features of the Tomo.

## Features

| Feature | Description |
|---------|-------------|
| [Applications](applications.md) | Application catalog and deployment |
| [Marketplace](marketplace.md) | Git-based app discovery and import |
| [Deployment](deployment.md) | Deployment workflows |
| [Data Retention](data-retention/README.md) | Data cleanup policies |

## Overview

### Server Management

Connect to and manage remote tomo servers:
- **SSH Connections** - Password or key-based authentication
- **Health Monitoring** - Real-time status checks
- **Multi-Server** - Manage multiple servers from one interface

### Application Marketplace

Browse and deploy containerized applications:
- **App Catalog** - Pre-configured application library
- **Search & Filter** - Find apps by name or category
- **One-Click Deploy** - Deploy to servers via SSH + Docker
- **Custom Configuration** - Override ports and environment variables

### Monitoring & Metrics

Track infrastructure health:
- **Dashboard** - Unified infrastructure view
- **Server Metrics** - CPU, memory, disk usage
- **Container Status** - Running containers across servers
- **Activity Logs** - Audit trail of operations

### Backup & Recovery

Protect your configuration:
- **Encrypted Backups** - PBKDF2 + Fernet encryption
- **CLI Management** - Export/import via command line
- **Full Data** - Users, servers, and settings included

## Quick Start

### Adding a Server

1. Navigate to **Servers** page
2. Click **Add Server**
3. Enter connection details (host, username, auth method)
4. Test connection
5. Save server

### Deploying an Application

1. Navigate to **Marketplace**
2. Browse or search for an app
3. Click **Deploy**
4. Select target server
5. Configure ports and environment (optional)
6. Click **Install**

### Managing Applications

1. Navigate to **Applications** page
2. View installed applications
3. Start/stop containers
4. Uninstall applications

## Related Documentation

- [API Reference](../api/README.md) - MCP tools for features
- [Architecture](../architecture/README.md) - System design
- [Operations](../operations/README.md) - Deployment and monitoring

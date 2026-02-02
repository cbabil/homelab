# API Reference

This document describes the MCP (Model Context Protocol) tools exposed by the Tomo backend.

---

## Overview

Tomo uses MCP for communication between frontend/CLI and backend. All operations are performed through MCP tools.

**Base URL:** `http://localhost:8000` (development)

---

## Authentication Tools

### login

Authenticate a user and create a session.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| username | string | Yes | Username |
| password | string | Yes | Password |

**Returns:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@local",
    "role": "admin"
  },
  "token": "eyJ..."
}
```

**Errors:**
- `AUTH001` - Invalid credentials
- `AUTH002` - Account locked

---

### logout

End the current session.

**Parameters:** None

**Returns:**
```json
{
  "success": true
}
```

---

### get_current_user

Get the currently authenticated user.

**Parameters:** None

**Returns:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@local",
  "role": "admin"
}
```

---

## Server Tools

### list_servers

List all configured servers.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| status | string | No | Filter by status |

**Returns:**
```json
[
  {
    "id": 1,
    "name": "Production",
    "hostname": "192.168.1.10",
    "port": 22,
    "username": "root",
    "status": "online",
    "docker_installed": true,
    "agent_connected": true
  }
]
```

---

### add_server

Add a new server.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Display name |
| hostname | string | Yes | IP or hostname |
| port | number | No | SSH port (default: 22) |
| username | string | Yes | SSH username |
| auth_type | string | Yes | "password" or "key" |
| password | string | Cond. | SSH password (if auth_type=password) |
| private_key | string | Cond. | SSH private key (if auth_type=key) |
| passphrase | string | No | Key passphrase |

**Returns:**
```json
{
  "id": 1,
  "name": "Production",
  "hostname": "192.168.1.10",
  "status": "online"
}
```

---

### remove_server

Remove a server.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| server_id | number | Yes | Server ID |

**Returns:**
```json
{
  "success": true
}
```

---

### test_connection

Test SSH connection to a server.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| server_id | number | Yes | Server ID |

**Returns:**
```json
{
  "connected": true,
  "latency_ms": 45,
  "ssh_version": "OpenSSH_8.9"
}
```

---

### get_server_metrics

Get real-time metrics from a server.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| server_id | number | Yes | Server ID |

**Returns:**
```json
{
  "cpu_percent": 23.5,
  "memory": {
    "total": 17179869184,
    "used": 8589934592,
    "percent": 50.0
  },
  "disk": {
    "total": 536870912000,
    "used": 128849018880,
    "percent": 24.0
  },
  "uptime_seconds": 432000
}
```

---

## Application Tools

### list_applications

List deployed applications.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| server_id | number | No | Filter by server |
| status | string | No | Filter by status |

**Returns:**
```json
[
  {
    "id": 1,
    "name": "nginx",
    "server_id": 1,
    "image": "nginx:latest",
    "status": "running",
    "ports": ["80:80"],
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

---

### deploy_application

Deploy an application to a server.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| server_id | number | Yes | Target server |
| app_id | string | Yes | Marketplace app ID |
| name | string | No | Custom name |
| config | object | No | Configuration overrides |

**Returns:**
```json
{
  "id": 1,
  "name": "nginx",
  "status": "deploying",
  "container_id": "abc123..."
}
```

---

### start_application

Start a stopped application.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| app_id | number | Yes | Application ID |

**Returns:**
```json
{
  "success": true,
  "status": "running"
}
```

---

### stop_application

Stop a running application.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| app_id | number | Yes | Application ID |

**Returns:**
```json
{
  "success": true,
  "status": "stopped"
}
```

---

### delete_application

Delete an application.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| app_id | number | Yes | Application ID |
| remove_volumes | boolean | No | Also remove volumes |

**Returns:**
```json
{
  "success": true
}
```

---

### get_application_logs

Get container logs.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| app_id | number | Yes | Application ID |
| lines | number | No | Number of lines (default: 100) |
| since | string | No | Since timestamp |

**Returns:**
```json
{
  "logs": "2024-01-15 10:00:00 Starting nginx...\n..."
}
```

---

## Agent Tools

### list_agents

List all agents.

**Parameters:** None

**Returns:**
```json
[
  {
    "id": 1,
    "server_id": 1,
    "server_name": "Production",
    "status": "connected",
    "version": "1.0.0",
    "last_seen": "2024-01-15T10:00:00Z"
  }
]
```

---

### install_agent

Install agent on a server.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| server_id | number | Yes | Target server |

**Returns:**
```json
{
  "success": true,
  "agent_id": 1
}
```

---

### rotate_agent_token

Rotate an agent's authentication token.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| agent_id | number | Yes | Agent ID |

**Returns:**
```json
{
  "success": true
}
```

---

## User Tools

### list_users

List all users (admin only).

**Parameters:** None

**Returns:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@local",
    "role": "admin",
    "status": "active",
    "last_login": "2024-01-15T10:00:00Z"
  }
]
```

---

### create_user

Create a new user (admin only).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| username | string | Yes | Username |
| email | string | Yes | Email |
| password | string | Yes | Password |
| role | string | No | "admin" or "user" |

**Returns:**
```json
{
  "id": 2,
  "username": "newuser",
  "email": "user@example.com",
  "role": "user"
}
```

---

### delete_user

Delete a user (admin only).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| user_id | number | Yes | User ID |

**Returns:**
```json
{
  "success": true
}
```

---

## Settings Tools

### get_settings

Get all settings.

**Parameters:** None

**Returns:**
```json
{
  "session_timeout": 60,
  "timezone": "UTC",
  "theme": "system",
  "notifications_enabled": true
}
```

---

### update_settings

Update settings.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| settings | object | Yes | Settings to update |

**Returns:**
```json
{
  "success": true,
  "settings": {...}
}
```

---

## Backup Tools

### export_backup

Create an encrypted backup.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| password | string | Yes | Backup password |

**Returns:**
```json
{
  "success": true,
  "data": "base64-encoded-backup"
}
```

---

### import_backup

Restore from backup.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| data | string | Yes | Base64 backup data |
| password | string | Yes | Backup password |
| mode | string | No | "full" or "merge" |

**Returns:**
```json
{
  "success": true,
  "imported": {
    "servers": 5,
    "users": 3,
    "applications": 12
  }
}
```

---

## Marketplace Tools

### list_marketplace_apps

List available marketplace applications.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| category | string | No | Filter by category |
| search | string | No | Search term |

**Returns:**
```json
[
  {
    "id": "nginx",
    "name": "Nginx",
    "description": "High-performance web server",
    "category": "networking",
    "image": "nginx:latest",
    "version": "1.25"
  }
]
```

---

### get_marketplace_app

Get details of a marketplace app.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| app_id | string | Yes | App ID |

**Returns:**
```json
{
  "id": "nginx",
  "name": "Nginx",
  "description": "High-performance web server",
  "category": "networking",
  "image": "nginx:latest",
  "version": "1.25",
  "ports": [{"container": 80, "host": 80}],
  "env": [{"name": "TZ", "default": "UTC"}],
  "volumes": [{"name": "data", "path": "/data"}],
  "requirements": {
    "cpu": 1,
    "memory": 256,
    "storage": 100
  }
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

See [[Error-Messages]] for a complete list of error codes.

---

## Next Steps

- [[Development]] - Development guide
- [[Architecture]] - System architecture
- [[Error-Messages]] - Error reference

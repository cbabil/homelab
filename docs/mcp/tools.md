# MCP Tools Reference

This document provides detailed documentation for all 56+ MCP tools available in the Tomo backend server.

## Table of Contents

- [App Tools](#app-tools) (13 tools)
- [Audit Tools](#audit-tools) (2 tools)
- [Auth Tools](#auth-tools) (3 tools)
- [Backup Tools](#backup-tools) (2 tools)
- [Docker Tools](#docker-tools) (4 tools)
- [Health Tools](#health-tools) (1 tool)
- [Logs Tools](#logs-tools) (3 tools)
- [Marketplace Tools](#marketplace-tools) (11 tools)
- [Monitoring Tools](#monitoring-tools) (5 tools)
- [Server Tools](#server-tools) (6 tools)
- [Settings Tools](#settings-tools) (2 tools)
- [System Tools](#system-tools) (4 tools)

## App Tools

Application deployment and lifecycle management tools. Located in `src/tools/app/tools.py`.

### get_app

Get application details from the catalog or installed apps.

**Parameters:**
- `app_id` (str, optional): Single app ID to retrieve
- `app_ids` (List[str], optional): Multiple app IDs to retrieve (bulk)
- `server_id` (str, optional): If provided, get installed apps on this server
- `filters` (Dict[str, Any], optional): Search filters (category, status, search, tags, etc.)

**Returns:**
```python
{
    "success": bool,
    "data": {
        "apps": [...],  # List of app objects
        "total": int    # Total count
    },
    "message": str
}
```

**Example:**
```python
# Get a single app from catalog
result = await get_app(app_id="nginx")

# Get installed apps on a server
result = await get_app(server_id="server-123")

# Search apps by category
result = await get_app(filters={"category": "media", "search": "plex"})
```

### add_app

Deploy application(s) to a server.

**Parameters:**
- `server_id` (str): Server to deploy to
- `app_id` (str, optional): Single app ID to deploy
- `app_ids` (List[str], optional): Multiple app IDs to deploy (bulk)
- `config` (Dict[str, Any], optional): Deployment configuration (ports, volumes, env vars)

**Returns:**
```python
{
    "success": bool,
    "data": {
        "installation_id": str,
        "server_id": str,
        "app_id": str
    },
    "message": str
}
```

**Example:**
```python
# Deploy single app
result = await add_app(
    server_id="server-123",
    app_id="nginx",
    config={
        "ports": {"80": "8080"},
        "volumes": {"/data": "/host/data"},
        "env": {"API_KEY": "secret"}
    }
)

# Bulk deploy multiple apps
result = await add_app(
    server_id="server-123",
    app_ids=["nginx", "postgres", "redis"]
)
```

### delete_app

Remove application(s) from a server.

**Parameters:**
- `server_id` (str): Server to remove from
- `app_id` (str, optional): Single app ID to remove
- `app_ids` (List[str], optional): Multiple app IDs to remove (bulk)
- `remove_data` (bool, optional): Whether to remove persistent data volumes (default: False)

**Returns:**
```python
{
    "success": bool,
    "data": {
        "server_id": str,
        "app_id": str
    },
    "message": str
}
```

**Example:**
```python
# Remove app but keep data
result = await delete_app(server_id="server-123", app_id="nginx")

# Remove app and all data
result = await delete_app(server_id="server-123", app_id="nginx", remove_data=True)
```

### update_app

Update application(s) to a new version.

**Parameters:**
- `server_id` (str): Server where app is installed
- `app_id` (str, optional): Single app ID to update
- `app_ids` (List[str], optional): Multiple app IDs to update (bulk)
- `version` (str, optional): Target version (latest if not specified)

**Returns:**
```python
{
    "success": bool,
    "data": {
        "installation_id": str,
        "server_id": str,
        "app_id": str,
        "version": str
    },
    "message": str
}
```

### start_app

Start a stopped application.

**Parameters:**
- `server_id` (str): Server where app is installed
- `app_id` (str): Application ID to start

**Returns:**
```python
{
    "success": bool,
    "data": {
        "server_id": str,
        "app_id": str
    },
    "message": str
}
```

### stop_app

Stop a running application.

**Parameters:**
- `server_id` (str): Server where app is installed
- `app_id` (str): Application ID to stop

**Returns:**
```python
{
    "success": bool,
    "data": {
        "server_id": str,
        "app_id": str
    },
    "message": str
}
```

### get_installation_status

Get installation status for polling during deployment.

**Parameters:**
- `installation_id` (str): Installation ID returned from install_app

**Returns:**
```python
{
    "success": bool,
    "data": {
        "status": str,  # pending, installing, running, failed
        "progress": int,
        "logs": [...]
    },
    "message": str
}
```

### refresh_installation_status

Refresh installation status from Docker and update database.

**Parameters:**
- `installation_id` (str): Installation ID to refresh

**Returns:**
```python
{
    "success": bool,
    "data": {
        "status": str,
        "container_details": {...}
    },
    "message": str
}
```

### validate_deployment_config

Validate deployment configuration before installation.

**Parameters:**
- `app_id` (str): Application ID to validate config for
- `config` (Dict[str, Any], optional): Configuration to validate

**Returns:**
```python
{
    "success": bool,
    "data": {
        "valid": bool,
        "errors": [...]
    },
    "message": str
}
```

### run_preflight_checks

Run pre-flight checks before deployment.

**Parameters:**
- `server_id` (str): Server to check
- `app_id` (str): App to deploy
- `config` (Dict[str, Any], optional): Deployment config

**Returns:**
```python
{
    "success": bool,
    "data": {
        "passed": bool,
        "checks": [
            {"name": str, "passed": bool, "message": str}
        ]
    },
    "message": str
}
```

**Checks include:**
- Docker is running
- Sufficient disk space
- Port availability
- Architecture compatibility

### check_container_health

Check container health after deployment.

**Parameters:**
- `server_id` (str): Server where container is running
- `container_name` (str): Container name to check

**Returns:**
```python
{
    "success": bool,
    "data": {
        "healthy": bool,
        "running": bool,
        "restart_count": int,
        "listening_ports": [...],
        "recent_logs": [...]
    },
    "message": str
}
```

### get_container_logs

Get recent logs from a container.

**Parameters:**
- `server_id` (str): Server where container is running
- `container_name` (str): Container name to get logs from
- `tail` (int, optional): Number of lines to return (default: 100)

**Returns:**
```python
{
    "success": bool,
    "data": {
        "logs": [...]
    },
    "message": str
}
```

### cleanup_failed_deployment

Clean up a failed deployment.

**Parameters:**
- `server_id` (str): Server where deployment failed
- `installation_id` (str): Installation ID to clean up

**Returns:**
```python
{
    "success": bool,
    "data": {
        "message": str,
        "removed": [...]
    },
    "message": str
}
```

**Cleanup actions:**
- Remove container
- Remove unused images
- Delete database record

---

## Auth Tools

User authentication and session management. Located in `src/tools/auth/tools.py`.

### login

Authenticate user with credentials.

**Parameters:**
- `credentials` (Dict[str, Any]): Login credentials
  - `username` (str): Username
  - `password` (str): Password
- `ctx` (Context): MCP context with client metadata

**Returns:**
```python
{
    "success": bool,
    "data": {
        "user": {...},
        "token": str,
        "session_id": str
    },
    "message": str
}
```

**Example:**
```python
result = await login(
    credentials={
        "username": "admin",
        "password": "password123"
    }
)
```

### logout

Logout user and invalidate session.

**Parameters:**
- `session_id` (str, optional): Session ID to invalidate
- `username` (str, optional): Username for logging
- `ctx` (Context, optional): MCP context

**Returns:**
```python
{
    "success": bool,
    "message": str
}
```

### get_current_user

Get current user from JWT token.

**Parameters:**
- `token` (str): JWT token

**Returns:**
```python
{
    "success": bool,
    "data": {
        "user": {
            "id": str,
            "username": str,
            "email": str,
            "is_active": bool,
            "is_admin": bool
        }
    },
    "message": str
}
```

---

## Audit Tools

Audit trail retrieval for settings and authentication events. Located in `src/tools/audit/tools.py`.

### get_settings_audit

Get settings change audit log (admin only).

**Parameters:**
- `setting_key` (str, optional): Filter by specific setting key
- `filter_user_id` (str, optional): Filter by user who made the changes
- `limit` (int, optional): Maximum entries to return (default: 100)
- `offset` (int, optional): Pagination offset (default: 0)
- `user_id` (str, optional): User ID from context (for auth)
- `ctx` (Context, optional): MCP context

**Returns:**
```python
{
    "success": bool,
    "data": {
        "audit_entries": [
            {
                "id": int,
                "table_name": str,  # "system_settings" | "user_settings"
                "record_id": str,
                "user_id": str,
                "setting_key": str,
                "old_value": Any,
                "new_value": Any,
                "change_type": str,  # "CREATE" | "UPDATE" | "DELETE"
                "change_reason": str,
                "client_ip": str,
                "user_agent": str,
                "created_at": str,
                "checksum": str
            }
        ],
        "total": int
    },
    "message": str
}
```

**Example:**
```python
# Get all settings audit entries
result = await get_settings_audit()

# Get audit for specific setting
result = await get_settings_audit(setting_key="ui.theme")

# Get audit entries by a specific user
result = await get_settings_audit(filter_user_id="user-123", limit=50)
```

### get_auth_audit

Get authentication event audit log (admin only).

Returns authentication events (login, logout, failures) from the log entries where `source='sec'`.

**Parameters:**
- `event_type` (str, optional): Filter by event type ("LOGIN", "LOGOUT")
- `username` (str, optional): Filter by username involved in the event
- `success_only` (bool, optional): Filter by success status (True=success, False=failure, None=all)
- `limit` (int, optional): Maximum entries to return (default: 100)
- `offset` (int, optional): Pagination offset (default: 0)
- `user_id` (str, optional): User ID from context (for auth)
- `ctx` (Context, optional): MCP context

**Returns:**
```python
{
    "success": bool,
    "data": {
        "audit_entries": [
            {
                "id": str,
                "timestamp": str,
                "level": str,  # "INFO" | "WARNING" | "ERROR"
                "event_type": str,  # "LOGIN" | "LOGOUT"
                "username": str,
                "success": bool,
                "client_ip": str,
                "user_agent": str,
                "message": str,
                "tags": [str]
            }
        ],
        "total": int
    },
    "message": str
}
```

**Example:**
```python
# Get all auth audit entries
result = await get_auth_audit()

# Get only login events
result = await get_auth_audit(event_type="LOGIN")

# Get failed login attempts
result = await get_auth_audit(event_type="LOGIN", success_only=False)

# Get auth events for specific user with pagination
result = await get_auth_audit(username="admin", limit=25, offset=50)
```

---

## Backup Tools

System backup and restore operations. Located in `src/tools/backup/tools.py`.

### export_backup

Export encrypted backup to file.

**Parameters:**
- `output_path` (str): File path for backup
- `password` (str): Encryption password

**Returns:**
```python
{
    "success": bool,
    "data": {
        "path": str,
        "checksum": str,
        "size": int,
        "timestamp": str
    },
    "message": str
}
```

**Example:**
```python
result = await export_backup(
    output_path="/backups/tomo-backup.enc",
    password="strong-password-123"
)
```

### import_backup

Import backup from encrypted file.

**Parameters:**
- `input_path` (str): File path to backup
- `password` (str): Decryption password
- `overwrite` (bool, optional): Overwrite existing data (default: False)

**Returns:**
```python
{
    "success": bool,
    "data": {
        "version": str,
        "timestamp": str,
        "users_imported": int,
        "servers_imported": int
    },
    "message": str
}
```

---

## Docker Tools

Docker installation and management on remote servers. Located in `src/tools/docker/tools.py`.

### install_docker

Install Docker on a remote server.

**Parameters:**
- `server_id` (str, optional): ID of saved server
- `host` (str, optional): Server hostname (required if no server_id)
- `port` (int, optional): SSH port (required if no server_id)
- `username` (str, optional): SSH username (required if no server_id)
- `auth_type` (str, optional): 'password' or 'key' (required if no server_id)
- `password` (str, optional): SSH password (if auth_type='password')
- `private_key` (str, optional): SSH private key (if auth_type='key')
- `tracked` (bool, optional): Enable progress tracking (default: False)

**Returns:**
```python
{
    "success": bool,
    "data": {
        "output": str,
        "system_info": {...}
    },
    "message": str
}
```

**Example:**
```python
# Install on saved server with tracking
result = await install_docker(server_id="server-123", tracked=True)

# Install on ad-hoc server
result = await install_docker(
    host="192.168.1.100",
    port=22,
    username="ubuntu",
    auth_type="password",
    password="password123"
)
```

**Supported OS:**
- Ubuntu
- Debian
- RHEL/CentOS/Rocky
- Fedora
- Alpine
- Arch/Manjaro

### get_docker_install_status

Get Docker installation status for tracking.

**Parameters:**
- `server_id` (str): Server ID

**Returns:**
```python
{
    "success": bool,
    "data": {
        "status": str,  # pending, installing, completed, failed
        "progress": int,
        "logs": [...]
    },
    "message": str
}
```

### update_docker

Update Docker to the latest version.

**Parameters:**
- `server_id` (str): Server ID

**Returns:**
```python
{
    "success": bool,
    "data": {
        "output": str,
        "system_info": {...}
    },
    "message": str
}
```

### remove_docker

Remove Docker from a server.

**Parameters:**
- `server_id` (str): Server ID

**Returns:**
```python
{
    "success": bool,
    "data": {
        "output": str
    },
    "message": str
}
```

**Warning:** This removes all Docker data and containers.

---

## Health Tools

Server health checks. Located in `src/tools/health/tools.py`.

### health_check

Check MCP server health status.

**Parameters:**
- `detailed` (bool, optional): Return comprehensive status (default: False)

**Returns:**
```python
{
    "success": bool,
    "data": {
        "status": str,
        "timestamp": str,
        "version": str,
        "components": {...},
        "configuration": {...}
    },
    "message": str
}
```

**Example:**
```python
# Simple ping
result = await health_check()  # Returns {"success": True, "message": "pong"}

# Detailed status
result = await health_check(detailed=True)
```

---

## Logs Tools

Log retrieval and management. Located in `src/tools/logs/tools.py`.

### get_logs

Get system and application logs with filtering.

**Parameters:**
- `level` (str, optional): Filter by level (INFO, WARNING, ERROR)
- `source` (str, optional): Filter by source (srv, app, dkr, etc.)
- `limit` (int, optional): Maximum entries to return (default: 100)
- `page` (int, optional): Page number for pagination

**Returns:**
```python
{
    "success": bool,
    "data": {
        "logs": [...],
        "total": int,
        "filtered": bool
    },
    "message": str
}
```

**Example:**
```python
# Get all logs
result = await get_logs()

# Get error logs from server module
result = await get_logs(level="ERROR", source="srv", limit=50)
```

### purge_logs

Delete all log entries from the database.

**Parameters:** None

**Returns:**
```python
{
    "success": bool,
    "message": str,
    "deleted": int
}
```

**Warning:** This permanently deletes all logs.

### get_audit_logs

Get audit logs tracking user and system events.

**Parameters:**
- `activity_types` (List[str], optional): Filter by types (e.g., "user_login", "app_installed")
- `server_id` (str, optional): Filter by server
- `user_id` (str, optional): Filter by user
- `limit` (int, optional): Max entries (default: 50)
- `offset` (int, optional): Pagination offset

**Returns:**
```python
{
    "success": bool,
    "data": {
        "logs": [...],
        "count": int,
        "total": int,
        "limit": int,
        "offset": int
    },
    "message": str
}
```

---

## Marketplace Tools

Marketplace repository and app management. Located in `src/tools/marketplace/tools.py`.

### list_repos

List all marketplace repositories.

**Parameters:** None

**Returns:**
```python
{
    "success": bool,
    "data": [
        {
            "id": str,
            "name": str,
            "url": str,
            "type": str,
            "enabled": bool,
            "app_count": int,
            "last_synced": str
        }
    ]
}
```

### add_repo

Add a new marketplace repository.

**Parameters:**
- `name` (str): Display name
- `url` (str): Git repository URL (https)
- `repo_type` (str, optional): 'official', 'community', 'personal' (default: 'community')
- `branch` (str, optional): Git branch (default: 'main')

**Returns:**
```python
{
    "success": bool,
    "data": {...},
    "message": str
}
```

**Example:**
```python
result = await add_repo(
    name="My Custom Repo",
    url="https://github.com/user/tomo-apps",
    repo_type="personal",
    branch="main"
)
```

### remove_repo

Remove a marketplace repository.

**Parameters:**
- `repo_id` (str): Repository ID

**Returns:**
```python
{
    "success": bool,
    "message": str
}
```

### sync_repo

Sync apps from a repository.

**Parameters:**
- `repo_id` (str): Repository ID

**Returns:**
```python
{
    "success": bool,
    "data": {
        "appCount": int
    },
    "message": str
}
```

### search_marketplace

Search marketplace apps.

**Parameters:**
- `search` (str, optional): Search term
- `category` (str, optional): Filter by category
- `tags` (List[str], optional): Filter by tags
- `featured` (bool, optional): Filter by featured status
- `sort_by` (str, optional): Sort field (default: 'name')
- `limit` (int, optional): Max results (default: 50)

**Returns:**
```python
{
    "success": bool,
    "data": {
        "apps": [...],
        "total": int
    }
}
```

### get_marketplace_app

Get details of a marketplace app.

**Parameters:**
- `app_id` (str): Application ID

**Returns:**
```python
{
    "success": bool,
    "data": {
        "id": str,
        "name": str,
        "description": str,
        "version": str,
        "category": str,
        "docker": {...},
        "requirements": {...}
    }
}
```

### get_marketplace_categories

Get all marketplace categories with counts.

**Parameters:** None

**Returns:**
```python
{
    "success": bool,
    "data": [
        {"name": str, "count": int}
    ]
}
```

### get_featured_apps

Get featured marketplace apps.

**Parameters:**
- `limit` (int, optional): Max apps to return (default: 10)

**Returns:**
```python
{
    "success": bool,
    "data": [...]
}
```

### get_trending_apps

Get trending marketplace apps.

**Parameters:**
- `limit` (int, optional): Max apps to return (default: 10)

**Returns:**
```python
{
    "success": bool,
    "data": [...]
}
```

### rate_marketplace_app

Rate a marketplace app (1-5 stars).

**Parameters:**
- `app_id` (str): Application ID
- `user_id` (str): User ID
- `rating` (int): Rating value (1-5)

**Returns:**
```python
{
    "success": bool,
    "data": {...},
    "message": str
}
```

### import_app

Import a marketplace app to local catalog.

**Parameters:**
- `app_id` (str): Application ID
- `user_id` (str): User performing the import

**Returns:**
```python
{
    "success": bool,
    "data": {
        "app_id": str,
        "app_name": str,
        "version": str
    },
    "message": str
}
```

---

## Monitoring Tools

System, server, and application metrics. Located in `src/tools/monitoring/tools.py`.

### get_system_metrics

Get current system metrics (CPU, memory, disk, network).

**Parameters:** None

**Returns:**
```python
{
    "success": bool,
    "data": {
        "cpu_percent": float,
        "memory_percent": float,
        "disk_percent": float,
        "network_sent": int,
        "network_recv": int
    },
    "message": str
}
```

### get_server_metrics

Get server metrics for a time period.

**Parameters:**
- `server_id` (str): Server ID
- `period` (str, optional): Time period (default: '24h')

**Returns:**
```python
{
    "success": bool,
    "data": {
        "server_id": str,
        "period": str,
        "metrics": [...],
        "count": int
    },
    "message": str
}
```

### get_app_metrics

Get container metrics for an app.

**Parameters:**
- `server_id` (str): Server ID
- `app_id` (str, optional): App ID
- `period` (str, optional): Time period (default: '24h')

**Returns:**
```python
{
    "success": bool,
    "data": {
        "server_id": str,
        "app_id": str,
        "period": str,
        "metrics": [...],
        "count": int
    },
    "message": str
}
```

### get_dashboard_metrics

Get aggregated dashboard metrics.

**Parameters:** None

**Returns:**
```python
{
    "success": bool,
    "data": {
        "total_servers": int,
        "online_servers": int,
        "total_apps": int,
        "running_apps": int,
        "avg_cpu_percent": float,
        "avg_memory_percent": float,
        "recent_activities": [...]
    },
    "message": str
}
```

### get_marketplace_metrics

Get marketplace statistics.

**Parameters:** None

**Returns:**
```python
{
    "success": bool,
    "data": {
        "total_repos": int,
        "total_apps": int,
        "featured_apps": int,
        "categories": [...],
        "avg_rating": float
    },
    "message": str
}
```

---

## Server Tools

Server connection and management. Located in `src/tools/server/tools.py`.

### add_server

Add a new server with credentials.

**Parameters:**
- `name` (str): Display name
- `host` (str): Hostname or IP
- `port` (int): SSH port
- `username` (str): SSH username
- `auth_type` (str): 'password' or 'key'
- `password` (str, optional): SSH password
- `private_key` (str, optional): SSH private key
- `server_id` (str, optional): Custom server ID
- `system_info` (Dict[str, Any], optional): System information

**Returns:**
```python
{
    "success": bool,
    "data": {
        "id": str,
        "name": str,
        "host": str,
        "port": int,
        "status": str,
        "docker_installed": bool
    },
    "message": str
}
```

**Example:**
```python
result = await add_server(
    name="Production Server",
    host="192.168.1.100",
    port=22,
    username="ubuntu",
    auth_type="password",
    password="password123"
)
```

### get_server

Get server by ID.

**Parameters:**
- `server_id` (str): Server ID

**Returns:**
```python
{
    "success": bool,
    "data": {...},
    "message": str
}
```

### list_servers

List all servers.

**Parameters:** None

**Returns:**
```python
{
    "success": bool,
    "data": {
        "servers": [...]
    },
    "message": str
}
```

### update_server

Update server configuration.

**Parameters:**
- `server_id` (str): Server ID
- `name` (str, optional): New name
- `host` (str, optional): New hostname
- `port` (int, optional): New port
- `username` (str, optional): New username

**Returns:**
```python
{
    "success": bool,
    "message": str
}
```

### delete_server

Delete a server.

**Parameters:**
- `server_id` (str): Server ID

**Returns:**
```python
{
    "success": bool,
    "message": str
}
```

### test_connection

Test SSH connection to a server.

**Parameters:**
- `server_id` (str): Server ID

**Returns:**
```python
{
    "success": bool,
    "data": {
        "system_info": {
            "os": str,
            "hostname": str,
            "architecture": str,
            "docker_version": str
        }
    },
    "message": str
}
```

---

## Settings Tools

User and system settings management. Located in `src/tools/settings/tools.py`.

### get_settings

Get settings for a user.

**Parameters:**
- `user_id` (str, optional): User ID (from context if not provided)
- `category` (str, optional): Filter by category
- `setting_keys` (List[str], optional): Specific settings to retrieve
- `include_system_defaults` (bool, optional): Include defaults (default: True)
- `include_user_overrides` (bool, optional): Include user overrides (default: True)
- `ctx` (Context, optional): MCP context

**Returns:**
```python
{
    "success": bool,
    "data": {...},
    "message": str,
    "checksum": str
}
```

**Example:**
```python
# Get all settings
result = await get_settings()

# Get specific category
result = await get_settings(category="appearance")

# Get specific keys
result = await get_settings(setting_keys=["theme", "timezone"])
```

### update_settings

Update settings with validation.

**Parameters:**
- `settings` (Dict[str, Any]): Settings to update
- `user_id` (str, optional): User ID (from context if not provided)
- `change_reason` (str, optional): Reason for change (audit)
- `validate_only` (bool, optional): Only validate, don't save (default: False)
- `ctx` (Context, optional): MCP context

**Returns:**
```python
{
    "success": bool,
    "data": {...},
    "message": str,
    "checksum": str
}
```

**Example:**
```python
result = await update_settings(
    settings={
        "theme": "dark",
        "timezone": "America/New_York"
    },
    change_reason="User preference update"
)
```

---

## System Tools

System information, setup status, and update management. Located in `src/tools/system/tools.py`.

### get_system_setup

Check if the system has completed initial setup.

**Parameters:** None

**Returns:**
```python
{
    "success": bool,
    "data": {
        "needs_setup": bool,    # True if initial setup is required
        "is_setup": bool,       # True if setup is complete
        "app_name": str         # Application name ("Tomo")
    },
    "message": str
}
```

**Example:**
```python
# Check if system needs setup
result = await get_system_setup()

if result["data"]["needs_setup"]:
    # Redirect to setup wizard
    pass
```

**Use case:** Called on application startup to determine if the user should be redirected to the setup wizard or the login page.

### get_system_info

Get system information (admin only).

**Parameters:**
- `user_id` (str, optional): User ID from context (for auth)
- `ctx` (Context, optional): MCP context

**Returns:**
```python
{
    "success": bool,
    "data": {
        "app_name": str,              # "Tomo"
        "is_setup": bool,             # Setup completion status
        "setup_completed_at": str,    # ISO timestamp
        "setup_by_user_id": str,      # User who completed setup
        "installation_id": str,       # Unique installation UUID
        "license_type": str,          # "community", "pro", "enterprise"
        "license_expires_at": str,    # License expiration (if applicable)
        "created_at": str,            # Record creation timestamp
        "updated_at": str             # Last update timestamp
    },
    "message": str
}
```

**Note:** The `license_key` field is never exposed in the response for security reasons.

**Example:**
```python
# Get system info for settings page
result = await get_system_info()

if result["success"]:
    installation_id = result["data"]["installation_id"]
    license_type = result["data"]["license_type"]
```

### get_component_versions

Get current versions of all system components.

**Parameters:** None

**Returns:**
```python
{
    "success": bool,
    "data": {
        "backend": str,        # Backend version (e.g., "1.2.0")
        "frontend": str,       # Frontend version (e.g., "1.2.0")
        "api": str,            # API version (e.g., "1.1.0")
        "components": {
            "backend": {"version": str, "updated_at": str},
            "frontend": {"version": str, "updated_at": str},
            "api": {"version": str, "updated_at": str}
        }
    },
    "message": str
}
```

**Example:**
```python
# Display versions in settings page
result = await get_component_versions()

if result["success"]:
    print(f"Backend: {result['data']['backend']}")
    print(f"Frontend: {result['data']['frontend']}")
    print(f"API: {result['data']['api']}")
```

**Use case:** Displayed in the Settings > General page to show current installed versions.

### check_updates

Check for available updates from GitHub releases.

**Parameters:** None

**Returns:**
```python
{
    "success": bool,
    "data": {
        "components": {
            "backend": str,
            "frontend": str,
            "api": str
        },
        "latest_version": str,        # Latest version from GitHub
        "update_available": bool,     # True if newer version exists
        "release_url": str,           # GitHub release URL
        "release_notes": str,         # Release notes/changelog
        "message": str                # Human-readable status message
    },
    "message": str
}
```

**Example:**
```python
# Check for updates in CLI
result = await check_updates()

if result["success"]:
    if result["data"]["update_available"]:
        print(f"Update available: {result['data']['latest_version']}")
        print(f"Download: {result['data']['release_url']}")
    else:
        print("You are running the latest version")
```

**Response when no releases exist:**
```python
{
    "success": True,
    "data": {
        "components": {...},
        "update_available": False,
        "message": "No releases found for repository"
    }
}
```

**Use case:** Used by the CLI `tomo update` command and can be used in the UI to display update notifications.

---

## Common Utilities

Shared utilities in `src/tools/common.py`.

### log_event

Log an event to the database (used internally by all tools).

**Parameters:**
- `source` (str): Short source identifier (e.g., "srv", "app", "dkr")
- `level` (str): Log level (INFO, WARNING, ERROR)
- `message` (str): Log message
- `tags` (List[str]): Tags for categorization
- `metadata` (Dict[str, Any], optional): Additional metadata

**Example:**
```python
from tools.common import log_event

await log_event(
    "srv",
    "INFO",
    "Server added successfully",
    ["server", "infrastructure"],
    {"server_id": "server-123", "host": "192.168.1.100"}
)
```

### Tag Definitions

Each module defines its own tags:

```python
# Server tools
SERVER_TAGS = ["server", "infrastructure"]

# App tools
APP_TAGS = ["app", "deployment"]

# Docker tools
DOCKER_TAGS = ["docker", "infrastructure"]

# Backup tools
BACKUP_TAGS = ["backup", "data"]

# Marketplace tools
MARKETPLACE_TAGS = ["marketplace"]

# Settings tools
SETTINGS_TAGS = ["settings", "configuration"]
```

---

## Error Handling

All tools follow a consistent error response format:

```python
{
    "success": False,
    "message": "Error description",
    "error": "ERROR_CODE"
}
```

Common error codes:

- `AUTHENTICATION_REQUIRED` - User not authenticated
- `SERVER_NOT_FOUND` - Server doesn't exist
- `CREDENTIALS_NOT_FOUND` - Server credentials missing
- `CONNECTION_FAILED` - SSH connection failed
- `DEPLOYMENT_FAILED` - App deployment failed
- `VALIDATION_ERROR` - Input validation failed
- `PERMISSION_DENIED` - Insufficient permissions

---

## Response Format

All tools return responses in this format:

```python
{
    "success": bool,           # Operation success status
    "data": {...},            # Response data (optional)
    "message": str,           # Human-readable message
    "error": str,             # Error code (only if success=False)
    "checksum": str           # Data checksum (settings only)
}
```

---

## Rate Limiting

Currently, there is no built-in rate limiting. Consider implementing rate limiting at the reverse proxy level for production deployments.

---

## Authentication

Most tools require authentication via JWT token. The token should be provided in the MCP context:

```python
ctx.meta = {
    "userId": "user-123",
    "clientIp": "192.168.1.10",
    "userAgent": "Mozilla/5.0..."
}
```

Tools that don't require authentication:
- `login`
- `health_check`

---

## Next Steps

- See [Architecture Documentation](./architecture.md) for implementation details
- See [Backend README](./README.md) for setup and configuration
- Check the source code in `src/tools/` for complete implementation

# MCP Tools Reference

Complete reference for all 85 MCP tools available in the Tomo backend.

## Summary by Domain

| Domain | Tool Count | Description |
|--------|-----------|-------------|
| [App](#app-tools) | 13 | Application deployment and management |
| [Audit](#audit-tools) | 2 | Audit trail and compliance |
| [Auth](#auth-tools) | 10 | Authentication and user management |
| [Backup](#backup-tools) | 2 | Backup and restore operations |
| [Docker](#docker-tools) | 4 | Docker installation and management |
| [Health](#health-tools) | 1 | Server health checks |
| [Logs](#logs-tools) | 3 | Log retrieval and management |
| [Marketplace](#marketplace-tools) | 11 | Repository and app discovery |
| [Monitoring](#monitoring-tools) | 5 | System and app metrics |
| [Notification](#notification-tools) | 8 | User notifications |
| [Retention](#retention-tools) | 5 | Data retention and cleanup |
| [Server](#server-tools) | 6 | Server connection management |
| [Session](#session-tools) | 5 | Session management |
| [Settings](#settings-tools) | 5 | Configuration management |
| [System](#system-tools) | 5 | System info and updates |

---

## App Tools

Tools for deploying and managing applications on servers.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `get_app` | Get app details from catalog or installed apps | `app_id`, `app_ids`, `server_id`, `filters` |
| `add_app` | Deploy app(s) to a server | `server_id`, `app_id`, `app_ids`, `config` |
| `delete_app` | Remove app(s) from a server | `server_id`, `app_id`, `app_ids`, `remove_data` |
| `update_app` | Update app(s) to a new version | `server_id`, `app_id`, `app_ids`, `version` |
| `start_app` | Start a stopped app | `server_id`, `app_id` |
| `stop_app` | Stop a running app | `server_id`, `app_id` |
| `get_installation_status` | Get installation status by ID for polling | `installation_id` |
| `refresh_installation_status` | Refresh status from Docker and update database | `installation_id` |
| `validate_deployment_config` | Validate deployment configuration before install | `app_id`, `config` |
| `run_preflight_checks` | Run pre-flight checks (Docker, disk, ports) | `server_id`, `app_id`, `config` |
| `check_container_health` | Check container health after deployment | `server_id`, `container_name` |
| `get_container_logs` | Get recent logs from a container | `server_id`, `container_name`, `tail` |
| `cleanup_failed_deployment` | Clean up a failed deployment | `server_id`, `installation_id` |

---

## Audit Tools

Tools for audit trail and compliance reporting.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `get_settings_audit` | Get settings change audit trail (admin only) | `setting_key`, `filter_user_id`, `limit`, `offset` |
| `get_auth_audit` | Get authentication audit trail (admin only) | `event_type`, `username`, `success_only`, `limit`, `offset` |

---

## Auth Tools

Tools for authentication and user management.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `login` | Authenticate user with credentials | `credentials` (dict with username/password) |
| `logout` | Logout user and invalidate session | `session_id`, `username` |
| `get_current_user` | Get current user from JWT token | `token` |
| `create_initial_admin` | Create first admin user during setup | `params` (username, email, password) |
| `get_user_by_username` | Get user information by username | `params` (username) |
| `reset_user_password` | Reset a user's password (admin CLI) | `params` (username, password) |
| `change_password` | Change password for authenticated user | `params` (token, current_password, new_password) |
| `update_avatar` | Update user's avatar | `params` (token, avatar base64) |
| `get_locked_accounts` | Get locked accounts (admin only) | `params` (token, identifier, identifier_type, lock_id) |
| `update_account_lock` | Lock or unlock an account (admin only) | `params` (token, lock_id, locked, notes) |

---

## Backup Tools

Tools for backup and restore operations.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `export_backup` | Export encrypted backup to file | `output_path`, `password` |
| `import_backup` | Import backup from encrypted file | `input_path`, `password`, `overwrite` |

---

## Docker Tools

Tools for Docker installation and management on remote servers.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `install_docker` | Install Docker on a remote server | `server_id` OR `host`, `port`, `username`, `auth_type`, `password`/`private_key`, `tracked` |
| `get_docker_install_status` | Get Docker installation status | `server_id` |
| `remove_docker` | Remove Docker from a server | `server_id` |
| `update_docker` | Update Docker to latest version | `server_id` |

---

## Health Tools

Tools for server health monitoring.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `health_check` | Check MCP server health status | `detailed` (bool) |

---

## Logs Tools

Tools for log retrieval and management.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `get_logs` | Get system and application logs | `level`, `source`, `limit`, `page` |
| `purge_logs` | Delete all log entries | — |
| `get_audit_logs` | Get audit logs for user/system events | `activity_types`, `server_id`, `user_id`, `limit`, `offset` |

---

## Marketplace Tools

Tools for marketplace repository and app management.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `list_repos` | List all marketplace repositories | — |
| `add_repo` | Add a new marketplace repository | `name`, `url`, `repo_type`, `branch` |
| `remove_repo` | Remove a marketplace repository | `repo_id` |
| `sync_repo` | Sync apps from a repository | `repo_id` |
| `search_marketplace` | Search marketplace apps | `search`, `category`, `tags`, `featured`, `sort_by`, `limit` |
| `get_marketplace_app` | Get details of a marketplace app | `app_id` |
| `get_marketplace_categories` | Get all categories with counts | — |
| `get_featured_apps` | Get featured marketplace apps | `limit` |
| `get_trending_apps` | Get trending marketplace apps | `limit` |
| `rate_marketplace_app` | Rate a marketplace app (1-5 stars) | `app_id`, `user_id`, `rating` |
| `import_app` | Import marketplace app to local catalog | `app_id`, `user_id` |

---

## Monitoring Tools

Tools for system and application metrics collection.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `get_system_metrics` | Get current system metrics (CPU, memory, disk) | — |
| `get_server_metrics` | Get server metrics for a time period | `server_id`, `period` |
| `get_app_metrics` | Get container metrics for an app | `server_id`, `app_id`, `period` |
| `get_dashboard_metrics` | Get aggregated dashboard metrics | — |
| `get_marketplace_metrics` | Get marketplace statistics | — |

---

## Notification Tools

Tools for user notification management.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `list_notifications` | List notifications for current user | `params` (read, type, limit, offset) |
| `get_notification` | Get a single notification by ID | `params` (notification_id) |
| `create_notification` | Create a notification (admin only for others) | `params` (user_id, type, title, message, source, metadata) |
| `mark_notification_read` | Mark a notification as read | `params` (notification_id) |
| `mark_all_notifications_read` | Mark all notifications as read | — |
| `dismiss_notification` | Dismiss (remove) a notification | `params` (notification_id) |
| `dismiss_all_notifications` | Dismiss all notifications | — |
| `get_unread_count` | Get unread notification count | — |

---

## Retention Tools

Tools for data retention management with CSRF protection.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `get_csrf_token` | Generate CSRF token for retention operations | — |
| `preview_retention_cleanup` | Preview cleanup operations (dry-run) | `params` (retention_type) |
| `perform_retention_cleanup` | Perform data cleanup with CSRF protection | `params` (retention_type, csrf_token, batch_size) |
| `get_retention_settings` | Get current retention settings | — |
| `update_retention_settings` | Update retention settings | `params` (log_retention, data_retention) |

---

## Server Tools

Tools for server connection and management.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `add_server` | Add a new server with credentials | `name`, `host`, `port`, `username`, `auth_type`, `password`/`private_key`, `server_id`, `system_info` |
| `get_server` | Get server by ID | `server_id` |
| `list_servers` | List all servers | — |
| `update_server` | Update server configuration | `server_id`, `name`, `host`, `port`, `username` |
| `delete_server` | Delete a server | `server_id` |
| `test_connection` | Test SSH connection to a server | `server_id` |

---

## Session Tools

Tools for session management with role-based access control.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `list_sessions` | List sessions for a user | `params` (user_id, status) |
| `get_session` | Get a single session by ID | `params` (session_id) |
| `update_session` | Update session last_activity | `params` (session_id) |
| `delete_session` | Terminate one or more sessions | `params` (session_id, user_id, all, exclude_current) |
| `cleanup_expired_sessions` | Mark expired sessions (admin only) | — |

---

## Settings Tools

Tools for application settings management.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `get_settings` | Get settings for current/provided user | `user_id`, `category`, `setting_keys`, `include_system_defaults`, `include_user_overrides` |
| `update_settings` | Update settings with validation and auditing | `settings`, `user_id`, `change_reason`, `validate_only` |
| `reset_user_settings` | Reset user settings to system defaults | `user_id`, `category` |
| `reset_system_settings` | Reset system settings to factory defaults (admin) | `user_id`, `category` |
| `get_default_settings` | Get factory default settings values | `category` |

---

## System Tools

Tools for system information and updates.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `get_system_setup` | Get system setup status (no auth required) | — |
| `get_system_info` | Get system information and metadata | — |
| `get_component_versions` | Get versions of all components | — |
| `check_updates` | Check for updates from GitHub releases | — |
| `parse_version` | Compare semantic version strings | (internal helper) |

---

## Response Format

All tools return a consistent response format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "error": null
}
```

On failure:

```json
{
  "success": false,
  "data": null,
  "message": "Human-readable error message",
  "error": "ERROR_CODE"
}
```

---

## Authentication

Most tools require authentication via JWT token passed in the context or parameters:

- **Public tools** (no auth): `health_check`, `get_system_setup`
- **User tools**: Require valid JWT token
- **Admin tools**: Require JWT token with admin role

The authentication context is extracted from `ctx.meta` containing:
- `user_id`: Authenticated user ID
- `session_id`: Current session ID
- `role`: User role (admin, user, readonly)
- `token`: JWT token
- `clientIp`: Client IP address
- `userAgent`: Client user agent

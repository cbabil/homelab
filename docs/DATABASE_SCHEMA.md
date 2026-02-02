# Database Schema Reference

This document describes the SQLite database schema for Tomo.

## Overview

The database uses SQLite with the following characteristics:
- **Location**: `backend/data/tomo.db`
- **Foreign Keys**: Enabled (`PRAGMA foreign_keys = ON`)
- **Journal Mode**: WAL (Write-Ahead Logging) for better concurrency
- **Encoding**: UTF-8

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATABASE SCHEMA                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐       ┌──────────────────┐       ┌──────────────────┐    │
│  │    users     │──────▶│    sessions      │       │  account_locks   │    │
│  │              │       │                  │       │                  │    │
│  │ id (PK)      │       │ id (PK)          │       │ id (PK)          │    │
│  │ username     │       │ user_id (FK)     │       │ identifier       │    │
│  │ email        │       │ ip_address       │       │ identifier_type  │    │
│  │ password_hash│       │ user_agent       │       │ attempt_count    │    │
│  │ role         │       │ created_at       │       │ locked_at        │    │
│  │ created_at   │       │ expires_at       │       │ lock_expires_at  │    │
│  │ last_login   │       │ last_activity    │       └──────────────────┘    │
│  │ is_active    │       │ status           │                               │
│  │ avatar       │       └──────────────────┘                               │
│  └──────┬───────┘                                                          │
│         │                                                                   │
│         │       ┌──────────────────┐       ┌──────────────────┐            │
│         └──────▶│  user_settings   │       │ system_settings  │            │
│                 │                  │       │                  │            │
│                 │ id (PK)          │       │ id (PK)          │            │
│                 │ user_id (FK)     │       │ setting_key      │            │
│                 │ setting_key      │       │ setting_value    │            │
│                 │ setting_value    │       │ default_value    │            │
│                 │ category         │       │ category         │            │
│                 └──────────────────┘       │ is_admin_only    │            │
│                                            └────────┬─────────┘            │
│                                                     │                      │
│                                            ┌────────▼─────────┐            │
│                                            │ settings_audit   │            │
│                                            │                  │            │
│                                            │ id (PK)          │            │
│                                            │ table_name       │            │
│                                            │ setting_key      │            │
│                                            │ old_value        │            │
│                                            │ new_value        │            │
│                                            │ change_type      │            │
│                                            │ checksum         │            │
│                                            └──────────────────┘            │
│                                                                             │
│  ┌──────────────┐       ┌──────────────────┐                               │
│  │   servers    │──────▶│server_credentials│                               │
│  │              │       │                  │                               │
│  │ id (PK)      │       │ server_id (PK,FK)│                               │
│  │ name         │       │ encrypted_data   │                               │
│  │ host         │       │ created_at       │                               │
│  │ port         │       │ updated_at       │                               │
│  │ username     │       └──────────────────┘                               │
│  │ auth_type    │                                                          │
│  │ status       │       ┌──────────────────┐                               │
│  │ docker_...   │──────▶│  installed_apps  │                               │
│  │ system_info  │       │                  │                               │
│  └──────┬───────┘       │ id (PK)          │                               │
│         │               │ server_id (FK)   │                               │
│         │               │ app_id           │                               │
│         │               │ container_id     │                               │
│         │               │ status           │                               │
│         │               │ config           │                               │
│         │               └──────────────────┘                               │
│         │                                                                   │
│         │       ┌──────────────────┐       ┌──────────────────┐            │
│         └──────▶│  server_metrics  │       │container_metrics │            │
│                 │                  │       │                  │            │
│                 │ id (PK)          │       │ id (PK)          │            │
│                 │ server_id (FK)   │       │ server_id (FK)   │            │
│                 │ cpu_percent      │       │ container_id     │            │
│                 │ memory_percent   │       │ cpu_percent      │            │
│                 │ disk_percent     │       │ memory_usage_mb  │            │
│                 │ timestamp        │       │ timestamp        │            │
│                 └──────────────────┘       └──────────────────┘            │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │   system_info    │  │component_versions│  │  activity_logs   │          │
│  │ (single row)     │  │                  │  │                  │          │
│  │ id = 1 (PK)      │  │ component (PK)   │  │ id (PK)          │          │
│  │ app_name         │  │ version          │  │ activity_type    │          │
│  │ is_setup         │  │ updated_at       │  │ user_id          │          │
│  │ installation_id  │  │ created_at       │  │ message          │          │
│  │ license_type     │  └──────────────────┘  │ timestamp        │          │
│  └──────────────────┘                        └──────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tables

### users

Stores user accounts for authentication.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | UUID identifier |
| `username` | TEXT | NOT NULL, UNIQUE | Login username |
| `email` | TEXT | DEFAULT '' | User email address |
| `password_hash` | TEXT | NOT NULL | Bcrypt hashed password |
| `role` | TEXT | NOT NULL, DEFAULT 'user' | Role: `admin`, `user`, `readonly` |
| `created_at` | TEXT | NOT NULL, DEFAULT now | ISO datetime of account creation |
| `last_login` | TEXT | NULL | ISO datetime of last login |
| `password_changed_at` | TEXT | DEFAULT now | ISO datetime of last password change |
| `is_active` | INTEGER | NOT NULL, DEFAULT 1 | Active status (0 or 1) |
| `preferences_json` | TEXT | DEFAULT '{}' | JSON user preferences |
| `avatar` | TEXT | DEFAULT NULL | Base64 avatar image or URL |

**Indexes:**
- `idx_users_username` on `username`
- `idx_users_email` on `email`
- `idx_users_role` on `role`
- `idx_users_active` on `is_active`
- `idx_users_created_at` on `created_at`

---

### sessions

Stores user sessions for authentication tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | Session token/UUID |
| `user_id` | TEXT | NOT NULL, FK(users.id) | User who owns the session |
| `ip_address` | TEXT | NULL | Client IP address |
| `user_agent` | TEXT | NULL | Browser/client user agent |
| `created_at` | TEXT | NOT NULL, DEFAULT now | Session start time |
| `expires_at` | TEXT | NOT NULL | Session expiration time |
| `last_activity` | TEXT | NOT NULL, DEFAULT now | Last activity timestamp |
| `status` | TEXT | NOT NULL, DEFAULT 'active' | Status: `active`, `idle`, `expired`, `terminated` |
| `terminated_at` | TEXT | NULL | When session was terminated |
| `terminated_by` | TEXT | NULL | Who terminated the session |

**Indexes:**
- `idx_sessions_user_id` on `user_id`
- `idx_sessions_status` on `status`
- `idx_sessions_expires_at` on `expires_at`
- `idx_sessions_last_activity` on `last_activity`

**Foreign Keys:**
- `user_id` → `users(id)` ON DELETE CASCADE

---

### account_locks

Tracks failed login attempts for brute force protection.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | UUID identifier |
| `identifier` | TEXT | NOT NULL | Username or IP being tracked |
| `identifier_type` | TEXT | NOT NULL | Type: `username`, `ip` |
| `attempt_count` | INTEGER | NOT NULL, DEFAULT 1 | Number of failed attempts |
| `first_attempt_at` | TEXT | NOT NULL, DEFAULT now | First failed attempt time |
| `last_attempt_at` | TEXT | NOT NULL, DEFAULT now | Most recent failed attempt |
| `locked_at` | TEXT | NULL | When account was locked |
| `lock_expires_at` | TEXT | NULL | When lock expires |
| `ip_address` | TEXT | NULL | Associated IP address |
| `user_agent` | TEXT | NULL | Client user agent |
| `reason` | TEXT | DEFAULT 'too_many_attempts' | Lock reason |
| `unlocked_at` | TEXT | NULL | When manually unlocked |
| `unlocked_by` | TEXT | NULL | Admin who unlocked |
| `notes` | TEXT | NULL | Admin notes |

**Indexes:**
- `idx_account_locks_identifier` on `identifier`
- `idx_account_locks_identifier_type` on `identifier_type`
- `idx_account_locks_locked_at` on `locked_at`
- `idx_account_locks_lock_expires_at` on `lock_expires_at`
- `idx_account_locks_ip_address` on `ip_address`

**Unique Constraint:** `(identifier, identifier_type)`

---

### servers

Stores server configurations for SSH connections.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | UUID identifier |
| `name` | TEXT | NOT NULL | Display name |
| `host` | TEXT | NOT NULL | Hostname or IP |
| `port` | INTEGER | NOT NULL, DEFAULT 22 | SSH port |
| `username` | TEXT | NOT NULL | SSH username |
| `auth_type` | TEXT | NOT NULL | Auth type: `password`, `key` |
| `status` | TEXT | NOT NULL, DEFAULT 'disconnected' | Connection status |
| `created_at` | TEXT | NOT NULL | Creation timestamp |
| `last_connected` | TEXT | NULL | Last successful connection |
| `system_info` | TEXT | NULL | JSON system information |
| `docker_installed` | INTEGER | NOT NULL, DEFAULT 0 | Docker available (0 or 1) |
| `system_info_updated_at` | TEXT | NULL | When system info was refreshed |

**Indexes:**
- `idx_servers_status` on `status`
- `idx_servers_host` on `host`
- `idx_servers_docker` on `docker_installed`

**Unique Constraint:** `(host, port, username)`

---

### server_credentials

Stores encrypted SSH credentials separately from server config.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `server_id` | TEXT | PRIMARY KEY, FK(servers.id) | Server this belongs to |
| `encrypted_data` | TEXT | NOT NULL | Encrypted password or private key |
| `created_at` | TEXT | NOT NULL | When credential was created |
| `updated_at` | TEXT | NOT NULL | When credential was last updated |

**Foreign Keys:**
- `server_id` → `servers(id)` ON DELETE CASCADE

---

### installed_apps

Tracks applications deployed to servers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | UUID identifier |
| `server_id` | TEXT | NOT NULL, FK(servers.id) | Target server |
| `app_id` | TEXT | NOT NULL | Application identifier from marketplace |
| `container_id` | TEXT | NULL | Docker container ID |
| `container_name` | TEXT | NULL | Docker container name |
| `status` | TEXT | NOT NULL, DEFAULT 'pending' | Deployment status |
| `config` | TEXT | NULL | JSON deployment configuration |
| `installed_at` | TEXT | NULL | Installation completion time |
| `started_at` | TEXT | NULL | When container was started |
| `error_message` | TEXT | NULL | Error details if failed |
| `step_durations` | TEXT | NULL | JSON timing for deployment steps |
| `step_started_at` | TEXT | NULL | Current step start time |
| `networks` | TEXT | NULL | JSON Docker networks |
| `named_volumes` | TEXT | NULL | JSON Docker named volumes |
| `bind_mounts` | TEXT | NULL | JSON Docker bind mounts |

**Indexes:**
- `idx_installed_apps_server` on `server_id`
- `idx_installed_apps_status` on `status`

**Unique Constraint:** `(server_id, app_id)`

**Foreign Keys:**
- `server_id` → `servers(id)` ON DELETE CASCADE

---

### system_settings

Stores system-wide configuration settings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTO | Auto-increment ID |
| `setting_key` | TEXT | NOT NULL, UNIQUE | Setting identifier (alphanumeric, dots, underscores) |
| `setting_value` | TEXT | NOT NULL | JSON-encoded current value |
| `default_value` | TEXT | NOT NULL | JSON-encoded factory default |
| `category` | TEXT | NOT NULL | Category: `ui`, `security`, `system`, `retention` |
| `scope` | TEXT | NOT NULL, DEFAULT 'system' | Scope: `system`, `user_overridable` |
| `data_type` | TEXT | NOT NULL | Type: `string`, `number`, `boolean`, `object`, `array` |
| `is_admin_only` | BOOLEAN | NOT NULL, DEFAULT 1 | Admin-only access flag |
| `description` | TEXT | NULL | Human-readable description |
| `validation_rules` | TEXT | NULL | JSON schema for validation |
| `created_at` | TEXT | NOT NULL, DEFAULT now | Creation timestamp |
| `updated_at` | TEXT | NOT NULL, DEFAULT now | Last update timestamp |
| `updated_by` | TEXT | NULL | User who last updated |
| `version` | INTEGER | NOT NULL, DEFAULT 1 | Optimistic locking version |

**Indexes:**
- `idx_system_settings_key` on `setting_key`
- `idx_system_settings_category` on `category`
- `idx_system_settings_scope` on `scope`
- `idx_system_settings_admin_only` on `is_admin_only`
- `idx_system_settings_updated_at` on `updated_at`

**Security Constraints:**
- `setting_key` must match pattern `[a-zA-Z0-9._]*`
- `setting_value` and `default_value` must be valid JSON
- Automatic audit logging via triggers

---

### user_settings

Stores per-user setting overrides.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTO | Auto-increment ID |
| `user_id` | TEXT | NOT NULL, FK(users.id) | User who owns this override |
| `setting_key` | TEXT | NOT NULL | Setting being overridden |
| `setting_value` | TEXT | NOT NULL | JSON-encoded user value |
| `category` | TEXT | NOT NULL | Category: `ui`, `security`, `system`, `retention` |
| `is_override` | BOOLEAN | NOT NULL, DEFAULT 1 | Whether this overrides system setting |
| `created_at` | TEXT | NOT NULL, DEFAULT now | Creation timestamp |
| `updated_at` | TEXT | NOT NULL, DEFAULT now | Last update timestamp |
| `version` | INTEGER | NOT NULL, DEFAULT 1 | Optimistic locking version |

**Indexes:**
- `idx_user_settings_user_id` on `user_id`
- `idx_user_settings_key` on `setting_key`
- `idx_user_settings_category` on `category`
- `idx_user_settings_updated_at` on `updated_at`

**Unique Constraint:** `(user_id, setting_key)`

**Foreign Keys:**
- `user_id` → `users(id)` ON DELETE CASCADE

---

### settings_audit

Tamper-resistant audit trail for settings changes.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTO | Auto-increment ID |
| `table_name` | TEXT | NOT NULL | Source table: `system_settings`, `user_settings` |
| `record_id` | INTEGER | NOT NULL | ID of the modified record |
| `user_id` | TEXT | NULL | User who made the change |
| `setting_key` | TEXT | NOT NULL | Setting that was changed |
| `old_value` | TEXT | NULL | Previous JSON value |
| `new_value` | TEXT | NOT NULL | New JSON value |
| `change_type` | TEXT | NOT NULL | Type: `CREATE`, `UPDATE`, `DELETE` |
| `change_reason` | TEXT | NULL | Optional reason (max 500 chars) |
| `client_ip` | TEXT | NULL | Client IP address |
| `user_agent` | TEXT | NULL | Client user agent |
| `created_at` | TEXT | NOT NULL, DEFAULT now | Change timestamp |
| `checksum` | TEXT | NOT NULL | SHA-256 integrity checksum (64 chars) |

**Indexes:**
- `idx_settings_audit_table_record` on `(table_name, record_id)`
- `idx_settings_audit_user_id` on `user_id`
- `idx_settings_audit_setting_key` on `setting_key`
- `idx_settings_audit_change_type` on `change_type`
- `idx_settings_audit_created_at` on `created_at`
- `idx_settings_audit_checksum` on `checksum`

**Triggers:**
- Automatic logging on INSERT/UPDATE/DELETE of `system_settings`
- Automatic logging on INSERT/UPDATE/DELETE of `user_settings`

---

### server_metrics

Stores server resource usage metrics.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | UUID identifier |
| `server_id` | TEXT | NOT NULL, FK(servers.id) | Server being monitored |
| `cpu_percent` | REAL | NOT NULL | CPU usage percentage |
| `memory_percent` | REAL | NOT NULL | Memory usage percentage |
| `memory_used_mb` | INTEGER | NOT NULL | Memory used in MB |
| `memory_total_mb` | INTEGER | NOT NULL | Total memory in MB |
| `disk_percent` | REAL | NOT NULL | Disk usage percentage |
| `disk_used_gb` | INTEGER | NOT NULL | Disk used in GB |
| `disk_total_gb` | INTEGER | NOT NULL | Total disk in GB |
| `network_rx_bytes` | INTEGER | DEFAULT 0 | Network bytes received |
| `network_tx_bytes` | INTEGER | DEFAULT 0 | Network bytes transmitted |
| `load_average_1m` | REAL | NULL | 1-minute load average |
| `load_average_5m` | REAL | NULL | 5-minute load average |
| `load_average_15m` | REAL | NULL | 15-minute load average |
| `uptime_seconds` | INTEGER | NULL | Server uptime in seconds |
| `timestamp` | TEXT | NOT NULL | Metric collection time |

**Indexes:**
- `idx_server_metrics_server` on `server_id`
- `idx_server_metrics_timestamp` on `timestamp`

**Foreign Keys:**
- `server_id` → `servers(id)` ON DELETE CASCADE

---

### container_metrics

Stores Docker container metrics.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | UUID identifier |
| `server_id` | TEXT | NOT NULL, FK(servers.id) | Server running the container |
| `container_id` | TEXT | NOT NULL | Docker container ID |
| `container_name` | TEXT | NOT NULL | Docker container name |
| `cpu_percent` | REAL | NOT NULL | CPU usage percentage |
| `memory_usage_mb` | INTEGER | NOT NULL | Memory used in MB |
| `memory_limit_mb` | INTEGER | NOT NULL | Memory limit in MB |
| `network_rx_bytes` | INTEGER | DEFAULT 0 | Network bytes received |
| `network_tx_bytes` | INTEGER | DEFAULT 0 | Network bytes transmitted |
| `status` | TEXT | NOT NULL | Container status |
| `timestamp` | TEXT | NOT NULL | Metric collection time |

**Indexes:**
- `idx_container_metrics_server` on `server_id`
- `idx_container_metrics_timestamp` on `timestamp`

**Foreign Keys:**
- `server_id` → `servers(id)` ON DELETE CASCADE

---

### activity_logs

Stores application activity and audit events.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | UUID identifier |
| `activity_type` | TEXT | NOT NULL | Type of activity |
| `user_id` | TEXT | NULL | User who performed the action |
| `server_id` | TEXT | NULL | Related server (if applicable) |
| `app_id` | TEXT | NULL | Related app (if applicable) |
| `message` | TEXT | NOT NULL | Human-readable message |
| `details` | TEXT | NULL | JSON additional details |
| `timestamp` | TEXT | NOT NULL | Event timestamp |

**Indexes:**
- `idx_activity_logs_type` on `activity_type`
- `idx_activity_logs_timestamp` on `timestamp`
- `idx_activity_logs_user` on `user_id`

---

### system_info

Single-row table for application metadata.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, CHECK (id = 1) | Always 1 |
| `app_name` | TEXT | NOT NULL, DEFAULT 'Tomo' | Application name |
| `is_setup` | INTEGER | NOT NULL, DEFAULT 0 | Setup complete flag (0 or 1) |
| `setup_completed_at` | TEXT | NULL | When setup was completed |
| `setup_by_user_id` | TEXT | NULL | Admin who completed setup |
| `installation_id` | TEXT | NOT NULL | Unique installation UUID |
| `license_type` | TEXT | DEFAULT 'community' | License: `community`, `pro`, `enterprise` |
| `license_key` | TEXT | NULL | License key if applicable |
| `license_expires_at` | TEXT | NULL | License expiration date |
| `created_at` | TEXT | NOT NULL, DEFAULT now | Installation timestamp |
| `updated_at` | TEXT | NOT NULL, DEFAULT now | Last update timestamp |

**Indexes:**
- `idx_system_info_is_setup` on `is_setup`

**Trigger:**
- `system_info_updated_at`: Auto-updates `updated_at` on modification

---

### component_versions

Tracks installed versions of application components.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `component` | TEXT | PRIMARY KEY | Component: `backend`, `frontend`, `api` |
| `version` | TEXT | NOT NULL, DEFAULT '1.0.0' | Semantic version |
| `updated_at` | TEXT | NOT NULL, DEFAULT now | Last version change |
| `created_at` | TEXT | NOT NULL, DEFAULT now | First tracked |

**Trigger:**
- `component_versions_updated_at`: Auto-updates `updated_at` on version change

---

## Views

### v_user_effective_settings

Combines system settings with user overrides to show effective values.

```sql
SELECT
    user_id,
    setting_key,
    effective_value,
    category,
    data_type,
    is_admin_only,
    description,
    is_user_override,
    last_updated
FROM v_user_effective_settings
WHERE user_id = 'user-uuid';
```

---

## Data Retention

Metrics and logs are subject to data retention policies:

| Table | Default Retention | Setting Key |
|-------|-------------------|-------------|
| `server_metrics` | 30 days | `retention.server_metrics_days` |
| `container_metrics` | 30 days | `retention.container_metrics_days` |
| `activity_logs` | 90 days | `retention.activity_logs_days` |
| `sessions` (expired) | 7 days | `retention.sessions_days` |
| `settings_audit` | 365 days | `retention.settings_audit_days` |

Cleanup is performed by the backend retention service according to configured intervals.

---

## Security Features

1. **Encrypted Credentials**: Server passwords and keys are encrypted at rest in `server_credentials`
2. **Password Hashing**: User passwords are hashed using bcrypt
3. **Audit Trail**: All settings changes are logged with checksums for integrity
4. **Input Validation**: SQL CHECK constraints prevent malformed data
5. **Foreign Key Cascade**: Related data is cleaned up automatically on deletion
6. **Brute Force Protection**: Failed login attempts tracked in `account_locks`

---

## Schema Initialization

Schema is initialized by the backend on startup:

```python
# backend/src/init_db/
├── schema_users.py            # users table
├── schema_sessions.py         # sessions table
├── schema_account_locks.py    # account_locks table
├── schema_servers.py          # servers, server_credentials tables
├── schema_apps_simple.py      # installed_apps table
├── schema_metrics.py          # server_metrics, container_metrics, activity_logs
├── schema_system_info.py      # system_info table
├── schema_component_versions.py # component_versions table

# backend/sql/
├── init_settings_schema.sql   # system_settings, user_settings, settings_audit
```

---

## Common Queries

### Get all active sessions for a user

```sql
SELECT * FROM sessions
WHERE user_id = ? AND status = 'active' AND expires_at > datetime('now')
ORDER BY last_activity DESC;
```

### Get server with credentials

```sql
SELECT s.*, sc.encrypted_data
FROM servers s
LEFT JOIN server_credentials sc ON s.id = sc.server_id
WHERE s.id = ?;
```

### Get effective setting for user

```sql
SELECT COALESCE(us.setting_value, ss.setting_value) as value
FROM system_settings ss
LEFT JOIN user_settings us ON ss.setting_key = us.setting_key AND us.user_id = ?
WHERE ss.setting_key = ?;
```

### Get recent activity

```sql
SELECT * FROM activity_logs
ORDER BY timestamp DESC
LIMIT 50;
```

### Check if account is locked

```sql
SELECT * FROM account_locks
WHERE identifier = ? AND identifier_type = 'username'
AND locked_at IS NOT NULL AND lock_expires_at > datetime('now');
```

---

## Related Documentation

- [MCP Tools Reference](./mcp/tools.md) - API for interacting with the database
- [Installation Guide](./INSTALLATION.md) - Setting up the database
- [Backup & Restore Guide](./user-guides/BACKUP_RESTORE.md) - Database backup procedures

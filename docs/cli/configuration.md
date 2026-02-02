# Configuration

## Database Discovery

The CLI automatically searches for the database in these locations (in order of priority):

| Priority | Location | Use Case |
|----------|----------|----------|
| 1 | `--data-dir` flag | Custom/explicit path |
| 2 | `../backend/data/tomo.db` | Development (relative to CLI) |
| 3 | `../../backend/data/tomo.db` | Development (nested) |
| 4 | `/var/lib/tomo/data/tomo.db` | Production (Linux) |
| 5 | `~/.tomo/data/tomo.db` | User installation |

The first location containing a valid `tomo.db` file is used.

## Custom Database Path

Specify a custom data directory with the `--data-dir` flag:

```bash
# Specify custom data directory
tomo admin create --data-dir /path/to/data

# The CLI expects tomo.db inside the specified directory
# e.g., /path/to/data/tomo.db
```

This is useful for:

- Non-standard installation paths
- Testing with different databases
- Docker or containerized environments

## Environment Variables

Currently, the CLI does not use environment variables. All configuration is done via command-line flags.

Future versions may support:

```bash
# Potential future support
TOMO_DATA_DIR=/path/to/data tomo admin create
```

## Database Requirements

The CLI requires:

1. **Database file exists** - The backend must have run at least once to create the schema
2. **Read/write access** - The CLI needs permissions to read and modify the database
3. **No exclusive locks** - The database should not be exclusively locked by another process

## WAL Mode

The CLI enables SQLite WAL (Write-Ahead Logging) mode for better concurrent access:

```typescript
db.pragma('journal_mode = WAL');
```

This allows the CLI to safely operate while the backend server is running.

## File Permissions

Recommended permissions for the data directory:

```bash
# Directory
chmod 755 /path/to/data

# Database file
chmod 644 /path/to/data/tomo.db

# WAL files (created automatically)
# tomo.db-wal
# tomo.db-shm
```

For production environments, restrict access to the user running the services:

```bash
chown -R tomo:tomo /path/to/data
chmod 700 /path/to/data
chmod 600 /path/to/data/tomo.db
```

## Backend Environment Configuration

The backend uses a `.env` file for configuration. A template is provided at `backend/.env-default`:

```bash
# Copy the template
cp backend/.env-default backend/.env

# Edit with your settings
nano backend/.env
```

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `production` | Environment: development, staging, production |
| `APP_VERSION` | `1.0.0` | Application version |
| `DATA_DIRECTORY` | `data` | Database and storage directory |
| `JWT_SECRET_KEY` | (required) | Secret key for JWT tokens |
| `SSH_TIMEOUT` | `30` | SSH connection timeout (seconds) |
| `MAX_CONCURRENT_CONNECTIONS` | `10` | Max concurrent SSH connections |
| `ALLOWED_ORIGINS` | `localhost:3000...` | CORS allowed origins (comma-separated) |

### Feature Flags

Feature flags allow enabling/disabling features without code changes. All flags use the `FEATURE_` prefix.

```bash
# Example: Disable marketplace
FEATURE_MARKETPLACE=false

# Example: Enable strict SSH
FEATURE_STRICT_SSH=true
```

| Category | Flags | Default |
|----------|-------|---------|
| **Core** | `FEATURE_SERVERS`, `FEATURE_SERVER_METRICS`, `FEATURE_SERVER_PREPARATION` | true |
| **Apps** | `FEATURE_APPLICATIONS`, `FEATURE_APP_DEPLOYMENT`, `FEATURE_APP_MANAGEMENT` | true |
| **Marketplace** | `FEATURE_MARKETPLACE`, `FEATURE_CASAOS_STORE`, `FEATURE_CUSTOM_MARKETPLACES` | true |
| **Docker** | `FEATURE_DOCKER_TOOLS`, `FEATURE_DOCKER_INSTALL`, `FEATURE_DOCKER_COMPOSE` | true |
| **Monitoring** | `FEATURE_MONITORING`, `FEATURE_SYSTEM_METRICS`, `FEATURE_CONTAINER_METRICS`, `FEATURE_DASHBOARD` | true |
| **Logging** | `FEATURE_ACTIVITY_LOGGING`, `FEATURE_AUDIT_LOGGING`, `FEATURE_LOGS_PAGE` | true |
| **Backup** | `FEATURE_BACKUP`, `FEATURE_BACKUP_ENCRYPTION`, `FEATURE_RESTORE` | true |
| **Data** | `FEATURE_DATA_RETENTION`, `FEATURE_AUTO_CLEANUP` | true |
| **Security** | `FEATURE_USER_REGISTRATION`, `FEATURE_SESSION_MANAGEMENT`, `FEATURE_JWT_AUTH` | true |
| **Security** | `FEATURE_STRICT_SSH`, `FEATURE_CREDENTIAL_ENCRYPTION` | false, true |
| **UI Pages** | `FEATURE_SERVERS_PAGE`, `FEATURE_APPLICATIONS_PAGE`, `FEATURE_MARKETPLACE_PAGE`, etc. | true |

### Using Feature Flags in Code

```python
from lib.config import is_feature_enabled, require_feature

# Check if feature is enabled
if is_feature_enabled("MARKETPLACE"):
    # Marketplace feature code
    pass

# Raise error if feature is disabled
require_feature("BACKUP", "create backup")  # Raises PermissionError if disabled
```

## Frontend Environment Configuration

The frontend uses a `.env` file with `VITE_` prefixed variables:

```bash
cp frontend/.env-default frontend/.env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_MCP_SERVER_URL` | `/mcp` | Backend MCP server URL |
| `VITE_FEATURE_*` | varies | Feature flags (must match backend) |
| `VITE_USE_MOCK_DATA` | `false` | Use mock data for development |
| `VITE_DEBUG_MODE` | `false` | Enable debug logging |

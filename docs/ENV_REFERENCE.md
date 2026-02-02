# Environment Variables Reference

This document describes all environment variables used by Tomo.

## Quick Start

1. Copy the example file: `cp .env.example .env`
2. Generate required secrets (see below)
3. Start the application

## Backend Environment Variables

### Required Variables

| Variable | Description | How to Generate |
|----------|-------------|-----------------|
| `JWT_SECRET_KEY` | Secret key for JWT token signing | `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `TOMO_MASTER_PASSWORD` | Master password for encrypting server credentials | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `TOMO_SALT` | Salt for key derivation (unique per installation) | `python -c "import secrets; print(secrets.token_urlsafe(16))"` |

> **Security Warning**: Never share or commit these values. Each installation should have unique secrets.

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHON_ENV` | `production` | Environment mode (`development` or `production`) |
| `ALLOWED_ORIGINS` | `http://localhost:3000,...` | CORS allowed origins (comma-separated) |
| `DATA_DIRECTORY` | `./data` | Directory for SQLite database and files |
| `MCP_LOG_LEVEL` | `INFO` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `APP_ENV` | `development` | Application environment |
| `TOOLS_DIRECTORY` | `src/tools` | Tool modules directory (internal) |
| `TOOLS_PACKAGE` | `tools` | Tools package name (internal) |

### Environment Modes

**Development** (`PYTHON_ENV=development`):
- Relaxed SSH host key checking
- Detailed error messages
- Debug logging enabled

**Production** (`PYTHON_ENV=production`):
- Strict SSH host key checking
- Generic error messages (no stack traces)
- Standard logging

## Frontend Environment Variables

All frontend variables must be prefixed with `VITE_` to be exposed to the client.

### Connection Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_MCP_SERVER_URL` | `/mcp` | Backend MCP server URL |

**Examples:**
- Development: `http://localhost:8000/mcp`
- Production: `/mcp` (uses reverse proxy)

### Feature Flags

Enable or disable features by setting to `true` or `false`:

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_FEATURE_SERVERS` | `true` | Server management feature |
| `VITE_FEATURE_APPLICATIONS` | `true` | Applications feature |
| `VITE_FEATURE_MARKETPLACE` | `true` | Marketplace feature |
| `VITE_FEATURE_MONITORING` | `true` | Monitoring capabilities |
| `VITE_FEATURE_DASHBOARD` | `true` | Dashboard feature |
| `VITE_FEATURE_BACKUP` | `true` | Backup/restore feature |
| `VITE_FEATURE_DATA_RETENTION` | `true` | Data retention settings |

### UI Page Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_FEATURE_SERVERS_PAGE` | `true` | Show Servers page |
| `VITE_FEATURE_APPLICATIONS_PAGE` | `true` | Show Applications page |
| `VITE_FEATURE_MARKETPLACE_PAGE` | `true` | Show Marketplace page |
| `VITE_FEATURE_DASHBOARD_PAGE` | `true` | Show Dashboard page |
| `VITE_FEATURE_LOGS_PAGE` | `true` | Show Logs page |
| `VITE_FEATURE_SETTINGS_PAGE` | `true` | Show Settings page |

### Development Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_USE_MOCK_DATA` | `false` | Use mock data when backend unavailable |
| `VITE_DEBUG_MODE` | `false` | Enable debug logging in browser console |

## File Locations

| Component | Config File | Location |
|-----------|-------------|----------|
| Root | `.env` | `/tomo/.env` |
| Backend | `.env` | `/tomo/backend/.env` |
| Frontend | `.env` | `/tomo/frontend/.env` |

## Example Configurations

### Development

```bash
# .env (root)
JWT_SECRET_KEY=dev-secret-key-change-in-production
TOMO_MASTER_PASSWORD=dev-master-password
TOMO_SALT=dev-salt-value
PYTHON_ENV=development
MCP_LOG_LEVEL=DEBUG
```

```bash
# frontend/.env
VITE_MCP_SERVER_URL=http://localhost:8000/mcp
VITE_DEBUG_MODE=true
```

### Production

```bash
# .env (root)
JWT_SECRET_KEY=<generated-64-char-secret>
TOMO_MASTER_PASSWORD=<generated-32-char-password>
TOMO_SALT=<generated-16-char-salt>
PYTHON_ENV=production
ALLOWED_ORIGINS=https://tomo.example.com
MCP_LOG_LEVEL=INFO
```

```bash
# frontend/.env
VITE_MCP_SERVER_URL=/mcp
VITE_DEBUG_MODE=false
```

## Database Settings (Not Environment Variables)

The following settings are stored in the database and configurable via the Settings API or frontend. They are NOT environment variables but are documented here for completeness.

### Agent Token Rotation

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| `agent_token_rotation_days` | 7 | 1-365 | Days until agent token expires and triggers rotation |
| `agent_token_grace_period_minutes` | 5 | 1-60 | Minutes old token remains valid during rotation |

These settings control automatic agent token rotation. The rotation scheduler checks hourly for agents with expired tokens.

## Security Best Practices

1. **Never commit `.env` files** - They contain secrets
2. **Use unique secrets** - Generate new values for each installation
3. **Restrict CORS origins** - Only allow necessary domains in production
4. **Use HTTPS in production** - Protect tokens in transit
5. **Rotate secrets periodically** - Update `JWT_SECRET_KEY` for security

## Troubleshooting

### Backend won't start

Check that all required variables are set:
```bash
grep -E "^(JWT_SECRET_KEY|TOMO_MASTER_PASSWORD|TOMO_SALT)=" .env
```

### Frontend can't connect to backend

Verify `VITE_MCP_SERVER_URL` is correct:
- Development: Should point to backend directly
- Production: Should use `/mcp` with reverse proxy configured

### CORS errors

Add your frontend URL to `ALLOWED_ORIGINS`:
```bash
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

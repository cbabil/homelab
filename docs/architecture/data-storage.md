# Data Storage Architecture

This document describes where different types of data are stored in the Tomo application.

## Overview

The application uses a hybrid storage strategy:
- **Backend database** - Single source of truth for persistent data
- **localStorage** - Client-side caching and preferences

## Storage by Data Type

### Servers

| Storage | Used | Rationale |
|---------|------|-----------|
| Backend | Yes | Single source of truth |
| localStorage | No | Removed - caused sync issues |

Server data changes frequently (connection status, system info) and having dual storage caused synchronization problems. The frontend fetches servers exclusively via the `list_servers` MCP tool.

**MCP Tools:**
- `list_servers` - Fetch all servers
- `add_server` - Add new server
- `update_server` - Update server details
- `delete_server` - Remove server
- `connect_server` - Establish connection

### Settings

| Storage | Used | Rationale |
|---------|------|-----------|
| Backend | Yes | Source of truth |
| localStorage | Yes | Cache/fallback |

Settings use a hybrid approach:
1. On load: Try backend first, fallback to localStorage
2. On save: Save to backend, cache to localStorage
3. Offline: Use cached localStorage values

This provides offline capability while keeping backend as authoritative.

**localStorage key:** `tomo_user_settings`

**MCP Tools:**
- `get_settings` - Fetch user settings
- `update_settings` - Save settings changes

### Authentication

| Storage | Used | Rationale |
|---------|------|-----------|
| Backend | Yes | Session validation, token generation |
| localStorage | Yes | Token persistence across page loads |

Auth tokens must persist in localStorage for session continuity. Backend validates tokens on each request.

**localStorage keys:**
- `tomo-auth-token` - JWT access token
- `tomo-auth-refresh-token` - Refresh token
- `tomo-auth-user` - Cached user object
- `tomo-auth-session-expiry` - Session expiry timestamp
- `tomo-auth-remember-me` - Remember me flag
- `current_session_id` - Active session ID

### UI Preferences

| Storage | Used | Rationale |
|---------|------|-----------|
| Backend | No | Not needed |
| localStorage | Yes | Client-side only |

UI preferences are purely client-side and don't need backend sync.

**localStorage keys:**
- `vite-ui-theme` - Dark/light theme
- `i18nextLng` - Selected language
- `dashboard_refresh_interval` - Auto-refresh rate

### Client-side Logs

| Storage | Used | Rationale |
|---------|------|-----------|
| Backend | No | Not needed |
| localStorage | Yes | Debugging only |

System logs for client-side debugging. Not persisted to backend.

**localStorage key:** `tomo-system-logs`

### Session Management

| Storage | Used | Rationale |
|---------|------|-----------|
| Backend | Yes | Session table |
| localStorage | Yes | Activity tracking |

**localStorage keys:**
- `sessionManager_sessions` - Session list
- `tomo-last-activity` - Last activity timestamp
- `tomo-activity-count` - Activity counter
- `tomo-session-expiry` - Expiry time

## Design Principles

1. **Backend is source of truth** for persistent, shared data (servers, settings)
2. **localStorage for client-only data** (theme, language, logs)
3. **localStorage as cache** when offline capability is needed (settings)
4. **No dual storage for frequently changing data** (servers) - causes sync issues

## Adding New Data Types

When adding new persistent data:

1. **Does it change frequently?** → Backend only (like servers)
2. **Does it need offline access?** → Backend + localStorage cache (like settings)
3. **Is it client-only?** → localStorage only (like theme)

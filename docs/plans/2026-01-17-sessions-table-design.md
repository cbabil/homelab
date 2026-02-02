# Sessions Table & MCP Tools Design

**Date:** 2026-01-17
**Status:** Approved

## Overview

Add persistent session management to the backend with a sessions table and MCP tools. Currently sessions are stored in-memory and the frontend uses localStorage with demo data.

## Goals

1. Persist sessions to database for reliability and audit history
2. Provide MCP tools for session CRUD operations
3. Support Access Logs page with real session data
4. Auto-expire sessions based on timeout settings
5. Soft-delete sessions to preserve history

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL,
    last_activity TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'idle', 'expired', 'terminated')),
    terminated_at TEXT,
    terminated_by TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON sessions(last_activity);
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| id | TEXT | Session ID (primary key) |
| user_id | TEXT | Foreign key to users table |
| ip_address | TEXT | Client IP address |
| user_agent | TEXT | Browser/device info |
| created_at | TEXT | Session start timestamp |
| expires_at | TEXT | Session expiration timestamp |
| last_activity | TEXT | Last activity timestamp |
| status | TEXT | active, idle, expired, terminated |
| terminated_at | TEXT | When session was terminated |
| terminated_by | TEXT | User ID or 'system' for auto-expire |

## Session Lifecycle

```
Login -> active -> (idle timeout) -> idle -> (expires_at reached) -> expired
                                          -> (user/admin action) -> terminated
```

- **active**: User has recent activity
- **idle**: No activity for idle timeout period
- **expired**: Past expires_at timestamp (auto-expire)
- **terminated**: Manually ended by user or admin (soft delete)

## MCP Tools (CRUD)

### Permissions

| Tool | User Access | Admin Access |
|------|-------------|--------------|
| create_session | Internal (login) | Internal |
| get_session | Own sessions | Any session |
| list_sessions | Own sessions | Any user's sessions |
| update_session | Own current session | Any session |
| delete_session | Own sessions | Any session or by user_id |
| cleanup_expired_sessions | No access | Admin only |

### Tool Definitions

#### create_session (Internal)
Called during login to create a new session.

```python
Params:
    user_id: str (required)
    ip_address: str (optional)
    user_agent: str (optional)
    expires_at: datetime (required)
Returns:
    Session object
```

#### get_session
Get a single session by ID.

```python
Params:
    session_id: str (required)
Returns:
    Session object or error if not found/not authorized
```

#### list_sessions
List sessions with optional filters.

```python
Params:
    user_id: str (optional - admin can specify, users get own)
    status: str (optional - filter by status)
Returns:
    List of SessionListResponse objects
```

#### update_session
Update session last_activity timestamp.

```python
Params:
    session_id: str (required)
Returns:
    Updated session object
```

#### delete_session
Soft-delete (terminate) one or more sessions.

```python
Params:
    session_id: str (optional - delete specific session)
    user_id: str (optional - admin: delete all for user)
    all: bool (optional - delete all own sessions)
    exclude_current: bool (default true - keep current session)
Returns:
    Count of terminated sessions
```

#### cleanup_expired_sessions (Admin only)
Mark sessions past expires_at as expired.

```python
Params: none
Returns:
    Count of sessions marked as expired
```

## Files to Create

| File | Purpose |
|------|---------|
| backend/src/init_db/schema_sessions.py | Sessions table schema |
| backend/src/models/session.py | Session Pydantic models |
| backend/src/services/session_service.py | Session CRUD operations |
| backend/src/tools/session/__init__.py | Module init |
| backend/src/tools/session/tools.py | MCP session tools |
| backend/src/tests/unit/tools/test_session.py | Session tools unit tests |
| backend/src/tests/unit/services/test_session_service.py | Session service unit tests |
| docs/database/diagrams/sessions.md | Schema documentation |

## Files to Modify

| File | Changes |
|------|---------|
| backend/src/services/auth_service.py | Use session_service instead of in-memory dict |
| backend/src/tools/auth/login_tool.py | Pass session_id from database |
| backend/src/main.py | Register session tools with MCP server |
| backend/src/init_db/__init__.py | Initialize sessions schema |
| docs/database/diagrams/users-settings.md | Add sessions table reference |

## Frontend Integration (Future)

| File | Changes |
|------|---------|
| frontend/src/services/sessionManager.ts | Call MCP tools instead of localStorage |
| frontend/src/hooks/useRealSessionData.ts | Fetch from backend |

## Security Considerations

- Users can only access their own sessions (unless admin)
- Session ID is embedded in JWT for validation
- Soft delete preserves audit trail
- Rate limiting on session operations
- Foreign key cascade deletes sessions when user is deleted

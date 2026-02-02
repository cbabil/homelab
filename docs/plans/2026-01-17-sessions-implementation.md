# Sessions Table & MCP Tools Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add persistent session management with database storage and MCP tools for the Access Logs page.

**Architecture:** Sessions stored in SQLite with CRUD operations via SessionService. MCP tools expose session operations with role-based permissions (user vs admin). Frontend will call these tools instead of using localStorage.

**Tech Stack:** Python, SQLite, FastMCP, Pydantic, pytest

---

## Task 1: Create Sessions Schema

**Files:**
- Create: `backend/src/init_db/schema_sessions.py`

**Step 1: Create the schema file**

```python
"""
Sessions Schema

Defines the sessions table for persistent session management.
"""

import structlog
from database.connection import DatabaseManager

logger = structlog.get_logger("schema_sessions")

SESSIONS_SCHEMA = """
-- Sessions Table
-- Stores user sessions for authentication tracking
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

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON sessions(last_activity);
"""


async def initialize_sessions_schema(db_manager: DatabaseManager = None) -> bool:
    """Initialize the sessions table schema.

    Args:
        db_manager: Optional DatabaseManager instance. If not provided, creates one.

    Returns:
        True if successful, False otherwise.
    """
    try:
        if db_manager is None:
            db_manager = DatabaseManager()

        async with db_manager.get_connection() as conn:
            await conn.executescript(SESSIONS_SCHEMA)
            await conn.commit()

        logger.info("Sessions schema initialized successfully")
        return True

    except Exception as e:
        logger.error("Failed to initialize sessions schema", error=str(e))
        return False
```

**Step 2: Commit**

```bash
git add backend/src/init_db/schema_sessions.py
git commit -m "feat(db): add sessions table schema"
```

---

## Task 2: Create Session Models

**Files:**
- Create: `backend/src/models/session.py`

**Step 1: Create the models file**

```python
"""
Session Data Models

Defines session management data models using Pydantic.
"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Session status values."""
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class Session(BaseModel):
    """Database session model."""
    id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Browser/device info")
    created_at: datetime = Field(..., description="Session start time")
    expires_at: datetime = Field(..., description="Expiration time")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE)
    terminated_at: Optional[datetime] = Field(None, description="When terminated")
    terminated_by: Optional[str] = Field(None, description="User ID or 'system'")


class SessionCreate(BaseModel):
    """Parameters for creating a session."""
    user_id: str = Field(..., description="User ID")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Browser/device info")
    expires_at: datetime = Field(..., description="Expiration time")


class SessionUpdate(BaseModel):
    """Parameters for updating a session."""
    last_activity: Optional[datetime] = Field(None)
    status: Optional[SessionStatus] = Field(None)


class SessionListResponse(BaseModel):
    """Response item for list_sessions tool."""
    id: str
    user_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: str
    expires_at: str
    last_activity: str
    status: str
    is_current: bool = False
```

**Step 2: Commit**

```bash
git add backend/src/models/session.py
git commit -m "feat(models): add session pydantic models"
```

---

## Task 3: Create Session Service - Part 1 (Create & Get)

**Files:**
- Create: `backend/src/services/session_service.py`
- Create: `backend/src/tests/unit/services/test_session_service.py`

**Step 1: Write failing tests for create and get**

```python
"""
Session Service Unit Tests
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from services.session_service import SessionService
from models.session import SessionStatus


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager."""
    manager = MagicMock()
    manager.get_connection = MagicMock()
    return manager


@pytest.fixture
def session_service(mock_db_manager):
    """Create a session service with mocked dependencies."""
    return SessionService(mock_db_manager)


class TestCreateSession:
    """Tests for create_session method."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, session_service, mock_db_manager):
        """Test successful session creation."""
        # Setup mock
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.commit = AsyncMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_db_manager.get_connection = MagicMock(return_value=mock_conn)

        expires_at = datetime.now() + timedelta(hours=1)

        result = await session_service.create_session(
            user_id="user123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            expires_at=expires_at
        )

        assert result is not None
        assert result.user_id == "user123"
        assert result.ip_address == "192.168.1.1"
        assert result.status == SessionStatus.ACTIVE


class TestGetSession:
    """Tests for get_session method."""

    @pytest.mark.asyncio
    async def test_get_session_found(self, session_service, mock_db_manager):
        """Test getting an existing session."""
        now = datetime.now()
        mock_row = {
            "id": "sess123",
            "user_id": "user123",
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "last_activity": now.isoformat(),
            "status": "active",
            "terminated_at": None,
            "terminated_by": None
        }

        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=mock_row)
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_db_manager.get_connection = MagicMock(return_value=mock_conn)

        result = await session_service.get_session("sess123")

        assert result is not None
        assert result.id == "sess123"
        assert result.user_id == "user123"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_service, mock_db_manager):
        """Test getting a non-existent session."""
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_db_manager.get_connection = MagicMock(return_value=mock_conn)

        result = await session_service.get_session("nonexistent")

        assert result is None
```

**Step 2: Run tests to verify they fail**

```bash
cd backend && source ../pythonvenv/bin/activate && pytest src/tests/unit/services/test_session_service.py -v
```

Expected: FAIL - module not found

**Step 3: Write minimal implementation**

```python
"""
Session Service

Handles session CRUD operations for persistent session management.
"""

import uuid
from datetime import datetime
from typing import Optional, List
import structlog
from database.connection import DatabaseManager
from models.session import Session, SessionStatus, SessionCreate, SessionListResponse

logger = structlog.get_logger("session_service")


class SessionService:
    """Service for managing user sessions."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize session service.

        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager

    async def create_session(
        self,
        user_id: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Session:
        """Create a new session.

        Args:
            user_id: User ID for the session.
            expires_at: When the session expires.
            ip_address: Client IP address.
            user_agent: Client user agent string.

        Returns:
            Created Session object.
        """
        session_id = f"sess_{uuid.uuid4().hex[:16]}"
        now = datetime.now()

        async with self.db_manager.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO sessions (id, user_id, ip_address, user_agent, created_at, expires_at, last_activity, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    user_id,
                    ip_address,
                    user_agent,
                    now.isoformat(),
                    expires_at.isoformat(),
                    now.isoformat(),
                    SessionStatus.ACTIVE.value
                )
            )
            await conn.commit()

        logger.info("Session created", session_id=session_id, user_id=user_id)

        return Session(
            id=session_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
            expires_at=expires_at,
            last_activity=now,
            status=SessionStatus.ACTIVE
        )

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID.

        Args:
            session_id: Session ID to retrieve.

        Returns:
            Session object if found, None otherwise.
        """
        async with self.db_manager.get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = await conn.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (session_id,)
            )
            row = await cursor.fetchone()

        if not row:
            return None

        return self._row_to_session(row)

    def _dict_factory(self, cursor, row):
        """Convert row to dictionary."""
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def _row_to_session(self, row: dict) -> Session:
        """Convert database row to Session model."""
        return Session(
            id=row["id"],
            user_id=row["user_id"],
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            last_activity=datetime.fromisoformat(row["last_activity"]),
            status=SessionStatus(row["status"]),
            terminated_at=datetime.fromisoformat(row["terminated_at"]) if row["terminated_at"] else None,
            terminated_by=row["terminated_by"]
        )
```

**Step 4: Run tests to verify they pass**

```bash
cd backend && source ../pythonvenv/bin/activate && pytest src/tests/unit/services/test_session_service.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/session_service.py backend/src/tests/unit/services/test_session_service.py
git commit -m "feat(services): add session service with create and get"
```

---

## Task 4: Session Service - Part 2 (List & Update)

**Files:**
- Modify: `backend/src/services/session_service.py`
- Modify: `backend/src/tests/unit/services/test_session_service.py`

**Step 1: Add failing tests for list and update**

Add to test file:

```python
class TestListSessions:
    """Tests for list_sessions method."""

    @pytest.mark.asyncio
    async def test_list_sessions_for_user(self, session_service, mock_db_manager):
        """Test listing sessions for a specific user."""
        now = datetime.now()
        mock_rows = [
            {
                "id": "sess1",
                "user_id": "user123",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0",
                "created_at": now.isoformat(),
                "expires_at": (now + timedelta(hours=1)).isoformat(),
                "last_activity": now.isoformat(),
                "status": "active",
                "terminated_at": None,
                "terminated_by": None
            },
            {
                "id": "sess2",
                "user_id": "user123",
                "ip_address": "10.0.0.1",
                "user_agent": "Chrome",
                "created_at": now.isoformat(),
                "expires_at": (now + timedelta(hours=1)).isoformat(),
                "last_activity": now.isoformat(),
                "status": "idle",
                "terminated_at": None,
                "terminated_by": None
            }
        ]

        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=mock_rows)
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_db_manager.get_connection = MagicMock(return_value=mock_conn)

        result = await session_service.list_sessions(user_id="user123")

        assert len(result) == 2
        assert result[0].id == "sess1"
        assert result[1].status == "idle"


class TestUpdateSession:
    """Tests for update_session method."""

    @pytest.mark.asyncio
    async def test_update_last_activity(self, session_service, mock_db_manager):
        """Test updating session last_activity."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.commit = AsyncMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_db_manager.get_connection = MagicMock(return_value=mock_conn)

        result = await session_service.update_session("sess123")

        assert result is True
        mock_conn.execute.assert_called_once()
```

**Step 2: Run tests to verify they fail**

```bash
cd backend && source ../pythonvenv/bin/activate && pytest src/tests/unit/services/test_session_service.py::TestListSessions -v
cd backend && source ../pythonvenv/bin/activate && pytest src/tests/unit/services/test_session_service.py::TestUpdateSession -v
```

Expected: FAIL - method not found

**Step 3: Add implementation**

Add to SessionService class:

```python
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None
    ) -> List[SessionListResponse]:
        """List sessions with optional filters.

        Args:
            user_id: Filter by user ID.
            status: Filter by status.

        Returns:
            List of SessionListResponse objects.
        """
        query = "SELECT * FROM sessions WHERE 1=1"
        params = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if status:
            query += " AND status = ?"
            params.append(status.value)

        query += " ORDER BY last_activity DESC"

        async with self.db_manager.get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

        return [
            SessionListResponse(
                id=row["id"],
                user_id=row["user_id"],
                ip_address=row["ip_address"],
                user_agent=row["user_agent"],
                created_at=row["created_at"],
                expires_at=row["expires_at"],
                last_activity=row["last_activity"],
                status=row["status"]
            )
            for row in rows
        ]

    async def update_session(self, session_id: str) -> bool:
        """Update session last_activity to now.

        Args:
            session_id: Session ID to update.

        Returns:
            True if updated, False otherwise.
        """
        now = datetime.now()

        async with self.db_manager.get_connection() as conn:
            await conn.execute(
                """
                UPDATE sessions
                SET last_activity = ?, status = ?
                WHERE id = ? AND status IN (?, ?)
                """,
                (
                    now.isoformat(),
                    SessionStatus.ACTIVE.value,
                    session_id,
                    SessionStatus.ACTIVE.value,
                    SessionStatus.IDLE.value
                )
            )
            await conn.commit()

        logger.debug("Session updated", session_id=session_id)
        return True
```

**Step 4: Run tests to verify they pass**

```bash
cd backend && source ../pythonvenv/bin/activate && pytest src/tests/unit/services/test_session_service.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/session_service.py backend/src/tests/unit/services/test_session_service.py
git commit -m "feat(services): add list and update session methods"
```

---

## Task 5: Session Service - Part 3 (Delete & Cleanup)

**Files:**
- Modify: `backend/src/services/session_service.py`
- Modify: `backend/src/tests/unit/services/test_session_service.py`

**Step 1: Add failing tests for delete and cleanup**

Add to test file:

```python
class TestDeleteSession:
    """Tests for delete_session method."""

    @pytest.mark.asyncio
    async def test_delete_single_session(self, session_service, mock_db_manager):
        """Test deleting a single session."""
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.commit = AsyncMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_db_manager.get_connection = MagicMock(return_value=mock_conn)

        result = await session_service.delete_session(
            session_id="sess123",
            terminated_by="user123"
        )

        assert result == 1

    @pytest.mark.asyncio
    async def test_delete_all_user_sessions(self, session_service, mock_db_manager):
        """Test deleting all sessions for a user."""
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 3
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.commit = AsyncMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_db_manager.get_connection = MagicMock(return_value=mock_conn)

        result = await session_service.delete_session(
            user_id="user123",
            terminated_by="user123",
            exclude_session_id="current_sess"
        )

        assert result == 3


class TestCleanupExpiredSessions:
    """Tests for cleanup_expired_sessions method."""

    @pytest.mark.asyncio
    async def test_cleanup_marks_expired(self, session_service, mock_db_manager):
        """Test that cleanup marks expired sessions."""
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 5
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.commit = AsyncMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_db_manager.get_connection = MagicMock(return_value=mock_conn)

        result = await session_service.cleanup_expired_sessions()

        assert result == 5
```

**Step 2: Run tests to verify they fail**

```bash
cd backend && source ../pythonvenv/bin/activate && pytest src/tests/unit/services/test_session_service.py::TestDeleteSession -v
cd backend && source ../pythonvenv/bin/activate && pytest src/tests/unit/services/test_session_service.py::TestCleanupExpiredSessions -v
```

Expected: FAIL - method not found

**Step 3: Add implementation**

Add to SessionService class:

```python
    async def delete_session(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        terminated_by: str = "system",
        exclude_session_id: Optional[str] = None
    ) -> int:
        """Soft-delete (terminate) sessions.

        Args:
            session_id: Specific session to terminate.
            user_id: Terminate all sessions for user.
            terminated_by: User ID who terminated or 'system'.
            exclude_session_id: Session to exclude (keep current session).

        Returns:
            Number of sessions terminated.
        """
        now = datetime.now()

        if session_id:
            # Delete specific session
            query = """
                UPDATE sessions
                SET status = ?, terminated_at = ?, terminated_by = ?
                WHERE id = ? AND status IN (?, ?)
            """
            params = (
                SessionStatus.TERMINATED.value,
                now.isoformat(),
                terminated_by,
                session_id,
                SessionStatus.ACTIVE.value,
                SessionStatus.IDLE.value
            )
        elif user_id:
            # Delete all sessions for user
            query = """
                UPDATE sessions
                SET status = ?, terminated_at = ?, terminated_by = ?
                WHERE user_id = ? AND status IN (?, ?)
            """
            params = [
                SessionStatus.TERMINATED.value,
                now.isoformat(),
                terminated_by,
                user_id,
                SessionStatus.ACTIVE.value,
                SessionStatus.IDLE.value
            ]

            if exclude_session_id:
                query = query.replace("AND status IN", "AND id != ? AND status IN")
                params.insert(4, exclude_session_id)

            params = tuple(params)
        else:
            logger.warning("delete_session called without session_id or user_id")
            return 0

        async with self.db_manager.get_connection() as conn:
            cursor = await conn.execute(query, params)
            await conn.commit()
            count = cursor.rowcount

        logger.info("Sessions terminated", count=count, terminated_by=terminated_by)
        return count

    async def cleanup_expired_sessions(self) -> int:
        """Mark expired sessions based on expires_at.

        Returns:
            Number of sessions marked as expired.
        """
        now = datetime.now()

        async with self.db_manager.get_connection() as conn:
            cursor = await conn.execute(
                """
                UPDATE sessions
                SET status = ?, terminated_at = ?, terminated_by = ?
                WHERE expires_at < ? AND status IN (?, ?)
                """,
                (
                    SessionStatus.EXPIRED.value,
                    now.isoformat(),
                    "system",
                    now.isoformat(),
                    SessionStatus.ACTIVE.value,
                    SessionStatus.IDLE.value
                )
            )
            await conn.commit()
            count = cursor.rowcount

        logger.info("Expired sessions cleaned up", count=count)
        return count
```

**Step 4: Run tests to verify they pass**

```bash
cd backend && source ../pythonvenv/bin/activate && pytest src/tests/unit/services/test_session_service.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/session_service.py backend/src/tests/unit/services/test_session_service.py
git commit -m "feat(services): add delete and cleanup session methods"
```

---

## Task 6: Create Session Tools

**Files:**
- Create: `backend/src/tools/session/__init__.py`
- Create: `backend/src/tools/session/tools.py`
- Create: `backend/src/tests/unit/tools/test_session.py`

**Step 1: Create module init**

```python
"""Session tools module."""

from tools.session.tools import SessionTools

__all__ = ["SessionTools"]
```

**Step 2: Write failing tests**

```python
"""
Session Tools Unit Tests
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from tools.session.tools import SessionTools
from models.session import SessionStatus, SessionListResponse


@pytest.fixture
def mock_session_service():
    """Create a mock session service."""
    service = AsyncMock()
    return service


@pytest.fixture
def mock_auth_service():
    """Create a mock auth service."""
    service = MagicMock()
    service.get_user_role = AsyncMock(return_value="user")
    return service


@pytest.fixture
def session_tools(mock_session_service, mock_auth_service):
    """Create session tools with mocked dependencies."""
    return SessionTools(mock_session_service, mock_auth_service)


class TestListSessions:
    """Tests for list_sessions tool."""

    @pytest.mark.asyncio
    async def test_user_lists_own_sessions(self, session_tools, mock_session_service):
        """Test that users can only list their own sessions."""
        mock_session_service.list_sessions.return_value = [
            SessionListResponse(
                id="sess1",
                user_id="user123",
                ip_address="192.168.1.1",
                user_agent="Mozilla",
                created_at="2024-01-01T00:00:00",
                expires_at="2024-01-01T01:00:00",
                last_activity="2024-01-01T00:30:00",
                status="active"
            )
        ]

        ctx = MagicMock()
        ctx.meta = {"user_id": "user123", "role": "user"}

        result = await session_tools.list_sessions({}, ctx)

        assert result["success"] is True
        assert len(result["data"]) == 1
        mock_session_service.list_sessions.assert_called_with(user_id="user123", status=None)


class TestDeleteSession:
    """Tests for delete_session tool."""

    @pytest.mark.asyncio
    async def test_user_deletes_own_session(self, session_tools, mock_session_service):
        """Test that users can delete their own sessions."""
        mock_session_service.get_session.return_value = MagicMock(user_id="user123")
        mock_session_service.delete_session.return_value = 1

        ctx = MagicMock()
        ctx.meta = {"user_id": "user123", "session_id": "current", "role": "user"}

        result = await session_tools.delete_session({"session_id": "sess123"}, ctx)

        assert result["success"] is True
        assert result["data"]["count"] == 1

    @pytest.mark.asyncio
    async def test_user_cannot_delete_others_session(self, session_tools, mock_session_service):
        """Test that users cannot delete other users' sessions."""
        mock_session_service.get_session.return_value = MagicMock(user_id="other_user")

        ctx = MagicMock()
        ctx.meta = {"user_id": "user123", "session_id": "current", "role": "user"}

        result = await session_tools.delete_session({"session_id": "sess456"}, ctx)

        assert result["success"] is False
        assert "permission" in result["message"].lower() or "denied" in result["message"].lower()
```

**Step 3: Run tests to verify they fail**

```bash
cd backend && source ../pythonvenv/bin/activate && pytest src/tests/unit/tools/test_session.py -v
```

Expected: FAIL - module not found

**Step 4: Write implementation**

```python
"""
Session Tools

Provides session management capabilities for the MCP server.
Implements CRUD operations with role-based access control.
"""

from typing import Dict, Any, Optional
import structlog
from fastmcp import Context
from services.session_service import SessionService
from models.session import SessionStatus

logger = structlog.get_logger("session_tools")


class SessionTools:
    """Session management tools for the MCP server."""

    def __init__(self, session_service: SessionService, auth_service=None):
        """Initialize session tools.

        Args:
            session_service: Session service instance.
            auth_service: Auth service for permission checks.
        """
        self.session_service = session_service
        self.auth_service = auth_service
        logger.info("Session tools initialized")

    def _get_user_context(self, ctx: Context) -> tuple[str, str, str]:
        """Extract user context from request.

        Returns:
            Tuple of (user_id, current_session_id, role)
        """
        meta = getattr(ctx, 'meta', {}) or {}
        user_id = meta.get('user_id', '')
        session_id = meta.get('session_id', '')
        role = meta.get('role', 'user')
        return user_id, session_id, role

    def _is_admin(self, role: str) -> bool:
        """Check if user has admin role."""
        return role == 'admin'

    async def list_sessions(self, params: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
        """List sessions for a user.

        Users can only list their own sessions.
        Admins can list any user's sessions.

        Params:
            user_id: Optional - Admin can specify target user
            status: Optional - Filter by status

        Returns:
            List of sessions.
        """
        try:
            current_user_id, _, role = self._get_user_context(ctx)
            target_user_id = params.get("user_id", current_user_id)
            status_filter = params.get("status")

            # Permission check: users can only list their own sessions
            if not self._is_admin(role) and target_user_id != current_user_id:
                return {
                    "success": False,
                    "message": "Permission denied: cannot list other users' sessions",
                    "error": "PERMISSION_DENIED"
                }

            status = SessionStatus(status_filter) if status_filter else None
            sessions = await self.session_service.list_sessions(
                user_id=target_user_id,
                status=status
            )

            return {
                "success": True,
                "data": [s.model_dump() for s in sessions],
                "message": f"Found {len(sessions)} sessions"
            }

        except Exception as e:
            logger.error("Failed to list sessions", error=str(e))
            return {
                "success": False,
                "message": f"Failed to list sessions: {str(e)}",
                "error": "LIST_ERROR"
            }

    async def get_session(self, params: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
        """Get a single session by ID.

        Users can only get their own sessions.
        Admins can get any session.

        Params:
            session_id: Required - Session ID to retrieve

        Returns:
            Session details.
        """
        try:
            current_user_id, _, role = self._get_user_context(ctx)
            session_id = params.get("session_id")

            if not session_id:
                return {
                    "success": False,
                    "message": "session_id is required",
                    "error": "MISSING_PARAM"
                }

            session = await self.session_service.get_session(session_id)

            if not session:
                return {
                    "success": False,
                    "message": "Session not found",
                    "error": "NOT_FOUND"
                }

            # Permission check
            if not self._is_admin(role) and session.user_id != current_user_id:
                return {
                    "success": False,
                    "message": "Permission denied: cannot access other users' sessions",
                    "error": "PERMISSION_DENIED"
                }

            return {
                "success": True,
                "data": session.model_dump(),
                "message": "Session retrieved"
            }

        except Exception as e:
            logger.error("Failed to get session", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get session: {str(e)}",
                "error": "GET_ERROR"
            }

    async def update_session(self, params: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
        """Update session last_activity.

        Users can only update their own current session.
        Admins can update any session.

        Params:
            session_id: Required - Session ID to update

        Returns:
            Success status.
        """
        try:
            current_user_id, current_session_id, role = self._get_user_context(ctx)
            session_id = params.get("session_id")

            if not session_id:
                return {
                    "success": False,
                    "message": "session_id is required",
                    "error": "MISSING_PARAM"
                }

            # For non-admins, verify they own this session
            if not self._is_admin(role):
                session = await self.session_service.get_session(session_id)
                if not session or session.user_id != current_user_id:
                    return {
                        "success": False,
                        "message": "Permission denied: cannot update other users' sessions",
                        "error": "PERMISSION_DENIED"
                    }

            await self.session_service.update_session(session_id)

            return {
                "success": True,
                "message": "Session updated"
            }

        except Exception as e:
            logger.error("Failed to update session", error=str(e))
            return {
                "success": False,
                "message": f"Failed to update session: {str(e)}",
                "error": "UPDATE_ERROR"
            }

    async def delete_session(self, params: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
        """Terminate one or more sessions.

        Users can only delete their own sessions.
        Admins can delete any session or all sessions for a user.

        Params:
            session_id: Optional - Delete specific session
            user_id: Optional - Admin: delete all sessions for user
            all: Optional - Delete all own sessions
            exclude_current: Optional - Keep current session (default: true)

        Returns:
            Count of terminated sessions.
        """
        try:
            current_user_id, current_session_id, role = self._get_user_context(ctx)
            target_session_id = params.get("session_id")
            target_user_id = params.get("user_id")
            delete_all = params.get("all", False)
            exclude_current = params.get("exclude_current", True)

            # Determine exclude session
            exclude_session_id = current_session_id if exclude_current else None

            if target_session_id:
                # Delete specific session
                session = await self.session_service.get_session(target_session_id)

                if not session:
                    return {
                        "success": False,
                        "message": "Session not found",
                        "error": "NOT_FOUND"
                    }

                # Permission check
                if not self._is_admin(role) and session.user_id != current_user_id:
                    return {
                        "success": False,
                        "message": "Permission denied: cannot delete other users' sessions",
                        "error": "PERMISSION_DENIED"
                    }

                count = await self.session_service.delete_session(
                    session_id=target_session_id,
                    terminated_by=current_user_id
                )

            elif delete_all or target_user_id:
                # Delete all sessions for a user
                user_to_delete = target_user_id or current_user_id

                # Permission check: only admin can delete other users' sessions
                if not self._is_admin(role) and user_to_delete != current_user_id:
                    return {
                        "success": False,
                        "message": "Permission denied: cannot delete other users' sessions",
                        "error": "PERMISSION_DENIED"
                    }

                count = await self.session_service.delete_session(
                    user_id=user_to_delete,
                    terminated_by=current_user_id,
                    exclude_session_id=exclude_session_id
                )

            else:
                return {
                    "success": False,
                    "message": "Must specify session_id, user_id, or all=true",
                    "error": "MISSING_PARAM"
                }

            return {
                "success": True,
                "data": {"count": count},
                "message": f"Terminated {count} session(s)"
            }

        except Exception as e:
            logger.error("Failed to delete session", error=str(e))
            return {
                "success": False,
                "message": f"Failed to delete session: {str(e)}",
                "error": "DELETE_ERROR"
            }

    async def cleanup_expired_sessions(self, params: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
        """Mark expired sessions. Admin only.

        Returns:
            Count of sessions marked as expired.
        """
        try:
            _, _, role = self._get_user_context(ctx)

            if not self._is_admin(role):
                return {
                    "success": False,
                    "message": "Permission denied: admin only",
                    "error": "PERMISSION_DENIED"
                }

            count = await self.session_service.cleanup_expired_sessions()

            return {
                "success": True,
                "data": {"count": count},
                "message": f"Cleaned up {count} expired session(s)"
            }

        except Exception as e:
            logger.error("Failed to cleanup sessions", error=str(e))
            return {
                "success": False,
                "message": f"Failed to cleanup sessions: {str(e)}",
                "error": "CLEANUP_ERROR"
            }
```

**Step 5: Run tests to verify they pass**

```bash
cd backend && source ../pythonvenv/bin/activate && pytest src/tests/unit/tools/test_session.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/src/tools/session/
git add backend/src/tests/unit/tools/test_session.py
git commit -m "feat(tools): add session MCP tools with RBAC"
```

---

## Task 7: Register Session Tools in Main

**Files:**
- Modify: `backend/src/main.py`

**Step 1: Read current main.py to understand structure**

Check how other tools are registered.

**Step 2: Add session tools registration**

Add imports and registration similar to other tools:

```python
# Add import
from tools.session import SessionTools
from services.session_service import SessionService

# In setup/initialization
session_service = SessionService(db_manager)
session_tools = SessionTools(session_service, auth_service)

# Register tools with MCP server
@mcp.tool()
async def list_sessions(params: dict, ctx: Context) -> dict:
    """List sessions for a user."""
    return await session_tools.list_sessions(params, ctx)

@mcp.tool()
async def get_session(params: dict, ctx: Context) -> dict:
    """Get a single session by ID."""
    return await session_tools.get_session(params, ctx)

@mcp.tool()
async def update_session(params: dict, ctx: Context) -> dict:
    """Update session last_activity."""
    return await session_tools.update_session(params, ctx)

@mcp.tool()
async def delete_session(params: dict, ctx: Context) -> dict:
    """Terminate one or more sessions."""
    return await session_tools.delete_session(params, ctx)

@mcp.tool()
async def cleanup_expired_sessions(params: dict, ctx: Context) -> dict:
    """Admin: Mark expired sessions."""
    return await session_tools.cleanup_expired_sessions(params, ctx)
```

**Step 3: Commit**

```bash
git add backend/src/main.py
git commit -m "feat(mcp): register session tools"
```

---

## Task 8: Initialize Sessions Schema on Startup

**Files:**
- Modify: `backend/src/init_db/__init__.py`

**Step 1: Add sessions schema initialization**

```python
from init_db.schema_sessions import initialize_sessions_schema

# In initialization sequence
await initialize_sessions_schema(db_manager)
```

**Step 2: Commit**

```bash
git add backend/src/init_db/__init__.py
git commit -m "feat(db): initialize sessions schema on startup"
```

---

## Task 9: Integrate with Auth Service

**Files:**
- Modify: `backend/src/services/auth_service.py`

**Step 1: Update authenticate_user to create database session**

Replace in-memory session storage with SessionService:

```python
# Add import
from services.session_service import SessionService

# In __init__
self.session_service = SessionService(db_manager)

# In authenticate_user method, replace:
# self.sessions[session_id] = {...}
# With:
session = await self.session_service.create_session(
    user_id=user.id,
    ip_address=client_ip,
    user_agent=user_agent,
    expires_at=expires_at
)
```

**Step 2: Update logout to use session service**

**Step 3: Commit**

```bash
git add backend/src/services/auth_service.py
git commit -m "feat(auth): integrate session service for persistent sessions"
```

---

## Task 10: Add Schema Documentation

**Files:**
- Create: `docs/database/diagrams/sessions.md`

**Step 1: Create documentation**

```markdown
# Sessions Table

## Overview

The sessions table stores user authentication sessions for tracking and management.

## Schema

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | Primary key, session ID |
| user_id | TEXT | Foreign key to users.id |
| ip_address | TEXT | Client IP address |
| user_agent | TEXT | Browser/device info |
| created_at | TEXT | Session creation timestamp |
| expires_at | TEXT | Session expiration timestamp |
| last_activity | TEXT | Last activity timestamp |
| status | TEXT | active, idle, expired, terminated |
| terminated_at | TEXT | When session was terminated |
| terminated_by | TEXT | User ID or 'system' |

## Relationships

- `user_id` references `users(id)` with CASCADE delete

## Indexes

- `idx_sessions_user_id` - Query sessions by user
- `idx_sessions_status` - Filter by status
- `idx_sessions_expires_at` - Find expired sessions
- `idx_sessions_last_activity` - Sort by activity

## Session Lifecycle

```
active -> idle -> expired
       -> terminated
```
```

**Step 2: Commit**

```bash
git add docs/database/diagrams/sessions.md
git commit -m "docs: add sessions table documentation"
```

---

## Task 11: Run Full Test Suite

**Step 1: Run all session-related tests**

```bash
cd backend && source ../pythonvenv/bin/activate && pytest src/tests/unit/services/test_session_service.py src/tests/unit/tools/test_session.py -v
```

**Step 2: Run full backend test suite to check for regressions**

```bash
cd backend && source ../pythonvenv/bin/activate && pytest src/tests/unit/ -v --override-ini="addopts="
```

**Step 3: Fix any failures**

**Step 4: Final commit if needed**

```bash
git add -A
git commit -m "test: fix any test regressions"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Sessions schema | schema_sessions.py |
| 2 | Session models | models/session.py |
| 3 | Service: create/get | session_service.py |
| 4 | Service: list/update | session_service.py |
| 5 | Service: delete/cleanup | session_service.py |
| 6 | MCP tools | tools/session/ |
| 7 | Register in main | main.py |
| 8 | Schema init | init_db/__init__.py |
| 9 | Auth integration | auth_service.py |
| 10 | Documentation | docs/ |
| 11 | Full test run | - |

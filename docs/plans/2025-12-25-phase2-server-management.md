# Phase 2: Server Management - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete server management with database persistence, encrypted credentials, and full MCP tool integration.

**Architecture:** Backend stores servers in SQLite with AES-256 encrypted credentials. Frontend connects via MCP tools. SSH testing via Paramiko.

**Tech Stack:** Python (FastMCP, SQLite, Paramiko, cryptography), React (TypeScript, MCP client)

---

## Current State Assessment

### Already Implemented
- Server model with validation (`backend/src/models/server.py`)
- SSH service with test_connection (`backend/src/services/ssh_service.py`)
- Encryption module (`backend/src/lib/encryption.py`)
- Basic server tools structure (`backend/src/tools/server_tools.py`)
- Server service (in-memory only) (`backend/src/services/server_service.py`)
- Frontend ServersPage with UI components

### Missing for Phase 2 Completion
1. ❌ Database persistence for servers (SQLite)
2. ❌ Encrypted credential storage in database
3. ❌ Complete MCP tools: `get_server`, `update_server`, `delete_server`
4. ❌ Wire server tools to database service
5. ❌ Backend tests for server operations
6. ❌ Frontend MCP integration (replace localStorage)

---

## Task 1: Add Server Database Schema and Service Methods

**Files:**
- Create: `backend/src/init_db/schema_servers.py`
- Modify: `backend/src/services/database_service.py`
- Test: `backend/tests/unit/test_server_database.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_server_database.py`:

```python
"""Tests for server database operations."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.database_service import DatabaseService
from models.server import ServerConnection, AuthType, ServerStatus


class TestServerDatabaseOperations:
    """Tests for server CRUD in database."""

    @pytest.fixture
    def db_service(self):
        """Create database service with mocked connection."""
        with patch('services.database_service.aiosqlite') as mock_sqlite:
            service = DatabaseService(data_directory="/tmp/test")
            service._connection = MagicMock()
            return service

    @pytest.mark.asyncio
    async def test_create_server(self, db_service):
        """Should create server in database."""
        db_service._connection.execute = AsyncMock()
        db_service._connection.commit = AsyncMock()

        server = await db_service.create_server(
            id="server-123",
            name="Test Server",
            host="192.168.1.100",
            port=22,
            username="admin",
            auth_type="password",
            encrypted_credentials="encrypted-data"
        )

        assert server is not None
        assert server.id == "server-123"
        assert server.name == "Test Server"

    @pytest.mark.asyncio
    async def test_get_server_by_id(self, db_service):
        """Should retrieve server by ID."""
        mock_row = {
            "id": "server-123",
            "name": "Test Server",
            "host": "192.168.1.100",
            "port": 22,
            "username": "admin",
            "auth_type": "password",
            "status": "disconnected",
            "created_at": "2025-01-01T00:00:00Z",
            "last_connected": None
        }
        db_service._connection.execute = AsyncMock(
            return_value=MagicMock(fetchone=AsyncMock(return_value=mock_row))
        )

        server = await db_service.get_server_by_id("server-123")

        assert server is not None
        assert server.name == "Test Server"

    @pytest.mark.asyncio
    async def test_get_all_servers(self, db_service):
        """Should retrieve all servers."""
        mock_rows = [
            {"id": "server-1", "name": "Server 1", "host": "192.168.1.100",
             "port": 22, "username": "admin", "auth_type": "password",
             "status": "connected", "created_at": "2025-01-01T00:00:00Z",
             "last_connected": None},
            {"id": "server-2", "name": "Server 2", "host": "192.168.1.101",
             "port": 22, "username": "root", "auth_type": "key",
             "status": "disconnected", "created_at": "2025-01-01T00:00:00Z",
             "last_connected": None}
        ]
        db_service._connection.execute = AsyncMock(
            return_value=MagicMock(fetchall=AsyncMock(return_value=mock_rows))
        )

        servers = await db_service.get_all_servers_from_db()

        assert len(servers) == 2

    @pytest.mark.asyncio
    async def test_update_server(self, db_service):
        """Should update server in database."""
        db_service._connection.execute = AsyncMock()
        db_service._connection.commit = AsyncMock()

        result = await db_service.update_server(
            server_id="server-123",
            name="Updated Server",
            host="192.168.1.200"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_server(self, db_service):
        """Should delete server from database."""
        db_service._connection.execute = AsyncMock()
        db_service._connection.commit = AsyncMock()

        result = await db_service.delete_server("server-123")

        assert result is True
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_server_database.py -v --no-cov
```

Expected: FAIL - methods don't exist

**Step 3: Create schema file**

Create `backend/src/init_db/schema_servers.py`:

```python
"""Server database schema initialization."""

SERVERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS servers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    host TEXT NOT NULL,
    port INTEGER NOT NULL DEFAULT 22,
    username TEXT NOT NULL,
    auth_type TEXT NOT NULL CHECK(auth_type IN ('password', 'key')),
    status TEXT NOT NULL DEFAULT 'disconnected',
    created_at TEXT NOT NULL,
    last_connected TEXT,
    UNIQUE(host, port, username)
);

CREATE TABLE IF NOT EXISTS server_credentials (
    server_id TEXT PRIMARY KEY,
    encrypted_data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_servers_status ON servers(status);
CREATE INDEX IF NOT EXISTS idx_servers_host ON servers(host);
"""


def get_servers_schema() -> str:
    """Return servers schema SQL."""
    return SERVERS_SCHEMA
```

**Step 4: Add database methods**

Add to `backend/src/services/database_service.py`:

```python
async def create_server(
    self,
    id: str,
    name: str,
    host: str,
    port: int,
    username: str,
    auth_type: str,
    encrypted_credentials: str
) -> Optional[ServerConnection]:
    """Create a new server in the database."""
    from datetime import datetime, UTC
    from models.server import ServerConnection, AuthType, ServerStatus

    try:
        now = datetime.now(UTC).isoformat()

        await self._connection.execute(
            """INSERT INTO servers (id, name, host, port, username, auth_type, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (id, name, host, port, username, auth_type, "disconnected", now)
        )

        await self._connection.execute(
            """INSERT INTO server_credentials (server_id, encrypted_data, created_at, updated_at)
               VALUES (?, ?, ?, ?)""",
            (id, encrypted_credentials, now, now)
        )

        await self._connection.commit()

        return ServerConnection(
            id=id,
            name=name,
            host=host,
            port=port,
            username=username,
            auth_type=AuthType(auth_type),
            status=ServerStatus.DISCONNECTED,
            created_at=now
        )
    except Exception as e:
        logger.error("Failed to create server", error=str(e))
        return None

async def get_server_by_id(self, server_id: str) -> Optional[ServerConnection]:
    """Get server by ID."""
    from models.server import ServerConnection, AuthType, ServerStatus

    try:
        cursor = await self._connection.execute(
            "SELECT * FROM servers WHERE id = ?", (server_id,)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return ServerConnection(
            id=row["id"],
            name=row["name"],
            host=row["host"],
            port=row["port"],
            username=row["username"],
            auth_type=AuthType(row["auth_type"]),
            status=ServerStatus(row["status"]),
            created_at=row["created_at"],
            last_connected=row["last_connected"]
        )
    except Exception as e:
        logger.error("Failed to get server", error=str(e))
        return None

async def get_all_servers_from_db(self) -> list:
    """Get all servers from database."""
    from models.server import ServerConnection, AuthType, ServerStatus

    try:
        cursor = await self._connection.execute("SELECT * FROM servers")
        rows = await cursor.fetchall()

        return [
            ServerConnection(
                id=row["id"],
                name=row["name"],
                host=row["host"],
                port=row["port"],
                username=row["username"],
                auth_type=AuthType(row["auth_type"]),
                status=ServerStatus(row["status"]),
                created_at=row["created_at"],
                last_connected=row["last_connected"]
            )
            for row in rows
        ]
    except Exception as e:
        logger.error("Failed to get servers", error=str(e))
        return []

async def get_server_credentials(self, server_id: str) -> Optional[str]:
    """Get encrypted credentials for a server."""
    try:
        cursor = await self._connection.execute(
            "SELECT encrypted_data FROM server_credentials WHERE server_id = ?",
            (server_id,)
        )
        row = await cursor.fetchone()
        return row["encrypted_data"] if row else None
    except Exception as e:
        logger.error("Failed to get credentials", error=str(e))
        return None

async def update_server(self, server_id: str, **kwargs) -> bool:
    """Update server in database."""
    try:
        updates = []
        values = []
        for key, value in kwargs.items():
            if value is not None:
                updates.append(f"{key} = ?")
                values.append(value)

        if not updates:
            return True

        values.append(server_id)
        query = f"UPDATE servers SET {', '.join(updates)} WHERE id = ?"
        await self._connection.execute(query, values)
        await self._connection.commit()
        return True
    except Exception as e:
        logger.error("Failed to update server", error=str(e))
        return False

async def delete_server(self, server_id: str) -> bool:
    """Delete server from database."""
    try:
        await self._connection.execute(
            "DELETE FROM servers WHERE id = ?", (server_id,)
        )
        await self._connection.commit()
        return True
    except Exception as e:
        logger.error("Failed to delete server", error=str(e))
        return False
```

**Step 5: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_server_database.py -v --no-cov
```

Expected: PASS

**Step 6: Commit**

```bash
cd /Users/christophebabilotte/source/tomo
git add backend/src/init_db/schema_servers.py backend/src/services/database_service.py backend/tests/unit/test_server_database.py
git commit -m "feat(server): add database schema and CRUD operations for servers"
```

---

## Task 2: Update Server Tools with Database Integration

**Files:**
- Modify: `backend/src/tools/server_tools.py`
- Modify: `backend/src/services/server_service.py`
- Test: `backend/tests/unit/test_server_tools.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_server_tools.py`:

```python
"""Tests for server MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tools.server_tools import ServerTools
from models.server import ServerConnection, AuthType, ServerStatus


@pytest.fixture
def mock_services():
    """Create mock services."""
    ssh_service = MagicMock()
    ssh_service.test_connection = AsyncMock(return_value=(True, "Connected", {"os": "Linux"}))

    server_service = MagicMock()
    server_service.add_server = AsyncMock()
    server_service.get_server = AsyncMock()
    server_service.get_all_servers = AsyncMock()
    server_service.update_server = AsyncMock()
    server_service.delete_server = AsyncMock()

    return ssh_service, server_service


@pytest.fixture
def server_tools(mock_services):
    """Create server tools with mocks."""
    ssh_service, server_service = mock_services
    return ServerTools(ssh_service, server_service)


class TestAddServer:
    """Tests for add_server tool."""

    @pytest.mark.asyncio
    async def test_add_server_success(self, server_tools, mock_services):
        """Should add server successfully."""
        ssh_service, server_service = mock_services
        server_service.add_server.return_value = ServerConnection(
            id="server-123",
            name="Test Server",
            host="192.168.1.100",
            port=22,
            username="admin",
            auth_type=AuthType.PASSWORD,
            status=ServerStatus.DISCONNECTED,
            created_at="2025-01-01T00:00:00Z"
        )

        result = await server_tools.add_server(
            name="Test Server",
            host="192.168.1.100",
            port=22,
            username="admin",
            auth_type="password",
            password="secret123"
        )

        assert result["success"] is True
        assert "server-123" in str(result["data"])


class TestGetServer:
    """Tests for get_server tool."""

    @pytest.mark.asyncio
    async def test_get_server_found(self, server_tools, mock_services):
        """Should return server when found."""
        _, server_service = mock_services
        server_service.get_server.return_value = ServerConnection(
            id="server-123",
            name="Test Server",
            host="192.168.1.100",
            port=22,
            username="admin",
            auth_type=AuthType.PASSWORD,
            status=ServerStatus.CONNECTED,
            created_at="2025-01-01T00:00:00Z"
        )

        result = await server_tools.get_server(server_id="server-123")

        assert result["success"] is True
        assert result["data"]["name"] == "Test Server"

    @pytest.mark.asyncio
    async def test_get_server_not_found(self, server_tools, mock_services):
        """Should return error when not found."""
        _, server_service = mock_services
        server_service.get_server.return_value = None

        result = await server_tools.get_server(server_id="nonexistent")

        assert result["success"] is False
        assert result["error"] == "SERVER_NOT_FOUND"


class TestListServers:
    """Tests for list_servers tool."""

    @pytest.mark.asyncio
    async def test_list_servers(self, server_tools, mock_services):
        """Should list all servers."""
        _, server_service = mock_services
        server_service.get_all_servers.return_value = [
            ServerConnection(
                id="server-1", name="Server 1", host="192.168.1.100",
                port=22, username="admin", auth_type=AuthType.PASSWORD,
                status=ServerStatus.CONNECTED, created_at="2025-01-01T00:00:00Z"
            ),
            ServerConnection(
                id="server-2", name="Server 2", host="192.168.1.101",
                port=22, username="root", auth_type=AuthType.KEY,
                status=ServerStatus.DISCONNECTED, created_at="2025-01-01T00:00:00Z"
            )
        ]

        result = await server_tools.list_servers()

        assert result["success"] is True
        assert len(result["data"]["servers"]) == 2


class TestDeleteServer:
    """Tests for delete_server tool."""

    @pytest.mark.asyncio
    async def test_delete_server_success(self, server_tools, mock_services):
        """Should delete server successfully."""
        _, server_service = mock_services
        server_service.delete_server.return_value = True

        result = await server_tools.delete_server(server_id="server-123")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_server_not_found(self, server_tools, mock_services):
        """Should return error when server not found."""
        _, server_service = mock_services
        server_service.delete_server.return_value = False

        result = await server_tools.delete_server(server_id="nonexistent")

        assert result["success"] is False


class TestTestConnection:
    """Tests for test_connection tool."""

    @pytest.mark.asyncio
    async def test_connection_success(self, server_tools, mock_services):
        """Should test connection successfully."""
        ssh_service, server_service = mock_services
        server_service.get_server.return_value = ServerConnection(
            id="server-123", name="Test Server", host="192.168.1.100",
            port=22, username="admin", auth_type=AuthType.PASSWORD,
            status=ServerStatus.DISCONNECTED, created_at="2025-01-01T00:00:00Z"
        )
        server_service.get_credentials.return_value = {"password": "secret"}

        result = await server_tools.test_connection(server_id="server-123")

        assert result["success"] is True
        assert "system_info" in result["data"]
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_server_tools.py -v --no-cov
```

Expected: FAIL - ServerTools class doesn't exist with this structure

**Step 3: Rewrite server_tools.py**

Replace `backend/src/tools/server_tools.py`:

```python
"""
Server Management Tools

Provides server connection and management capabilities for the MCP server.
"""

from typing import Dict, Any
import uuid
import structlog
from fastmcp import FastMCP
from models.server import ServerConnection, ServerStatus, AuthType
from services.ssh_service import SSHService
from services.server_service import ServerService


logger = structlog.get_logger("server_tools")


class ServerTools:
    """Server management tools for the MCP server."""

    def __init__(self, ssh_service: SSHService, server_service: ServerService):
        """Initialize server tools."""
        self.ssh_service = ssh_service
        self.server_service = server_service
        logger.info("Server tools initialized")

    async def add_server(
        self,
        name: str,
        host: str,
        port: int,
        username: str,
        auth_type: str,
        password: str = None,
        private_key: str = None
    ) -> Dict[str, Any]:
        """Add a new server with credentials."""
        try:
            server_id = f"server-{uuid.uuid4().hex[:8]}"
            credentials = {"password": password} if auth_type == "password" else {"private_key": private_key}

            server = await self.server_service.add_server(
                server_id=server_id,
                name=name,
                host=host,
                port=port,
                username=username,
                auth_type=auth_type,
                credentials=credentials
            )

            if not server:
                return {
                    "success": False,
                    "message": "Failed to add server",
                    "error": "ADD_SERVER_ERROR"
                }

            logger.info("Server added", server_id=server_id, name=name)
            return {
                "success": True,
                "data": server.model_dump(),
                "message": f"Server '{name}' added successfully"
            }
        except Exception as e:
            logger.error("Add server error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to add server: {str(e)}",
                "error": "ADD_SERVER_ERROR"
            }

    async def get_server(self, server_id: str) -> Dict[str, Any]:
        """Get server by ID."""
        try:
            server = await self.server_service.get_server(server_id)

            if not server:
                return {
                    "success": False,
                    "message": "Server not found",
                    "error": "SERVER_NOT_FOUND"
                }

            return {
                "success": True,
                "data": server.model_dump(),
                "message": "Server retrieved"
            }
        except Exception as e:
            logger.error("Get server error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get server: {str(e)}",
                "error": "GET_SERVER_ERROR"
            }

    async def list_servers(self) -> Dict[str, Any]:
        """List all servers."""
        try:
            servers = await self.server_service.get_all_servers()

            return {
                "success": True,
                "data": {"servers": [s.model_dump() for s in servers]},
                "message": f"Retrieved {len(servers)} servers"
            }
        except Exception as e:
            logger.error("List servers error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to list servers: {str(e)}",
                "error": "LIST_SERVERS_ERROR"
            }

    async def update_server(
        self,
        server_id: str,
        name: str = None,
        host: str = None,
        port: int = None,
        username: str = None
    ) -> Dict[str, Any]:
        """Update server configuration."""
        try:
            success = await self.server_service.update_server(
                server_id=server_id,
                name=name,
                host=host,
                port=port,
                username=username
            )

            if not success:
                return {
                    "success": False,
                    "message": "Server not found",
                    "error": "SERVER_NOT_FOUND"
                }

            return {
                "success": True,
                "message": "Server updated successfully"
            }
        except Exception as e:
            logger.error("Update server error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to update server: {str(e)}",
                "error": "UPDATE_SERVER_ERROR"
            }

    async def delete_server(self, server_id: str) -> Dict[str, Any]:
        """Delete a server."""
        try:
            success = await self.server_service.delete_server(server_id)

            if not success:
                return {
                    "success": False,
                    "message": "Server not found or delete failed",
                    "error": "DELETE_SERVER_ERROR"
                }

            logger.info("Server deleted", server_id=server_id)
            return {
                "success": True,
                "message": "Server deleted successfully"
            }
        except Exception as e:
            logger.error("Delete server error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to delete server: {str(e)}",
                "error": "DELETE_SERVER_ERROR"
            }

    async def test_connection(self, server_id: str) -> Dict[str, Any]:
        """Test SSH connection to a server."""
        try:
            server = await self.server_service.get_server(server_id)
            if not server:
                return {
                    "success": False,
                    "message": "Server not found",
                    "error": "SERVER_NOT_FOUND"
                }

            credentials = await self.server_service.get_credentials(server_id)
            if not credentials:
                return {
                    "success": False,
                    "message": "Credentials not found",
                    "error": "CREDENTIALS_NOT_FOUND"
                }

            success, message, system_info = await self.ssh_service.test_connection(
                host=server.host,
                port=server.port,
                username=server.username,
                auth_type=server.auth_type.value,
                credentials=credentials
            )

            if success:
                await self.server_service.update_server_status(server_id, ServerStatus.CONNECTED)
                return {
                    "success": True,
                    "data": {"system_info": system_info},
                    "message": "Connection successful"
                }
            else:
                await self.server_service.update_server_status(server_id, ServerStatus.ERROR)
                return {
                    "success": False,
                    "message": message,
                    "error": "CONNECTION_FAILED"
                }
        except Exception as e:
            logger.error("Test connection error", error=str(e))
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "error": "CONNECTION_TEST_ERROR"
            }


def register_server_tools(app: FastMCP, ssh_service: SSHService, server_service: ServerService):
    """Register server tools with FastMCP app."""
    tools = ServerTools(ssh_service, server_service)

    app.tool(tools.add_server)
    app.tool(tools.get_server)
    app.tool(tools.list_servers)
    app.tool(tools.update_server)
    app.tool(tools.delete_server)
    app.tool(tools.test_connection)

    logger.info("Server tools registered")
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_server_tools.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
cd /Users/christophebabilotte/source/tomo
git add backend/src/tools/server_tools.py backend/tests/unit/test_server_tools.py
git commit -m "feat(server): rewrite server tools with full CRUD and test connection"
```

---

## Task 3: Update Server Service with Database and Encryption

**Files:**
- Modify: `backend/src/services/server_service.py`
- Test: `backend/tests/unit/test_server_service.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_server_service.py`:

```python
"""Tests for server service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.server_service import ServerService
from models.server import AuthType


class TestServerService:
    """Tests for ServerService."""

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = MagicMock()
        db.create_server = AsyncMock()
        db.get_server_by_id = AsyncMock()
        db.get_all_servers_from_db = AsyncMock(return_value=[])
        db.update_server = AsyncMock(return_value=True)
        db.delete_server = AsyncMock(return_value=True)
        db.get_server_credentials = AsyncMock()
        return db

    @pytest.fixture
    def mock_credential_manager(self):
        """Create mock credential manager."""
        cm = MagicMock()
        cm.encrypt_credentials = MagicMock(return_value="encrypted-data")
        cm.decrypt_credentials = MagicMock(return_value={"password": "secret"})
        return cm

    @pytest.fixture
    def server_service(self, mock_db_service, mock_credential_manager):
        """Create server service with mocks."""
        with patch('services.server_service.CredentialManager', return_value=mock_credential_manager):
            service = ServerService(db_service=mock_db_service)
            return service

    @pytest.mark.asyncio
    async def test_add_server_with_password(self, server_service, mock_db_service):
        """Should add server with encrypted password."""
        mock_db_service.create_server.return_value = MagicMock(id="server-123")

        result = await server_service.add_server(
            server_id="server-123",
            name="Test",
            host="192.168.1.100",
            port=22,
            username="admin",
            auth_type="password",
            credentials={"password": "secret123"}
        )

        assert result is not None
        mock_db_service.create_server.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_credentials_decrypts(self, server_service, mock_db_service, mock_credential_manager):
        """Should decrypt credentials when retrieving."""
        mock_db_service.get_server_credentials.return_value = "encrypted-data"

        result = await server_service.get_credentials("server-123")

        assert result == {"password": "secret"}
        mock_credential_manager.decrypt_credentials.assert_called_with("encrypted-data")
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_server_service.py -v --no-cov
```

Expected: FAIL

**Step 3: Rewrite server_service.py**

Replace `backend/src/services/server_service.py`:

```python
"""
Server Management Service

Handles server connection management with database persistence and encryption.
"""

from typing import Dict, Any, List, Optional
import structlog
from models.server import ServerConnection, ServerStatus, AuthType
from services.database_service import DatabaseService
from lib.encryption import CredentialManager


logger = structlog.get_logger("server_service")


class ServerService:
    """Service for managing server connections with database persistence."""

    def __init__(self, db_service: DatabaseService = None):
        """Initialize server service with database and encryption."""
        self.db_service = db_service
        try:
            self.credential_manager = CredentialManager()
        except ValueError:
            logger.warning("Credential manager not initialized - encryption disabled")
            self.credential_manager = None
        logger.info("Server service initialized")

    async def add_server(
        self,
        server_id: str,
        name: str,
        host: str,
        port: int,
        username: str,
        auth_type: str,
        credentials: Dict[str, str]
    ) -> Optional[ServerConnection]:
        """Add new server with encrypted credentials."""
        try:
            encrypted_creds = ""
            if self.credential_manager and credentials:
                encrypted_creds = self.credential_manager.encrypt_credentials(credentials)

            server = await self.db_service.create_server(
                id=server_id,
                name=name,
                host=host,
                port=port,
                username=username,
                auth_type=auth_type,
                encrypted_credentials=encrypted_creds
            )

            logger.info("Server added", server_id=server_id, name=name)
            return server
        except Exception as e:
            logger.error("Failed to add server", error=str(e))
            return None

    async def get_server(self, server_id: str) -> Optional[ServerConnection]:
        """Get server by ID."""
        return await self.db_service.get_server_by_id(server_id)

    async def get_all_servers(self) -> List[ServerConnection]:
        """Get all servers."""
        return await self.db_service.get_all_servers_from_db()

    async def get_credentials(self, server_id: str) -> Optional[Dict[str, str]]:
        """Get decrypted credentials for a server."""
        try:
            encrypted = await self.db_service.get_server_credentials(server_id)
            if not encrypted or not self.credential_manager:
                return None
            return self.credential_manager.decrypt_credentials(encrypted)
        except Exception as e:
            logger.error("Failed to get credentials", error=str(e))
            return None

    async def update_server(
        self,
        server_id: str,
        name: str = None,
        host: str = None,
        port: int = None,
        username: str = None
    ) -> bool:
        """Update server configuration."""
        return await self.db_service.update_server(
            server_id=server_id,
            name=name,
            host=host,
            port=port,
            username=username
        )

    async def update_server_status(self, server_id: str, status: ServerStatus) -> bool:
        """Update server connection status."""
        return await self.db_service.update_server(
            server_id=server_id,
            status=status.value
        )

    async def delete_server(self, server_id: str) -> bool:
        """Delete server and its credentials."""
        return await self.db_service.delete_server(server_id)
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_server_service.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
cd /Users/christophebabilotte/source/tomo
git add backend/src/services/server_service.py backend/tests/unit/test_server_service.py
git commit -m "feat(server): add database persistence and credential encryption to server service"
```

---

## Task 4: Verify All Phase 2 Backend Tests Pass

**Step 1: Run all Phase 2 related tests**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_server_*.py -v --no-cov
```

**Step 2: Fix any failing tests**

**Step 3: Commit if fixes needed**

```bash
cd /Users/christophebabilotte/source/tomo
git add .
git commit -m "fix(server): fix test failures in Phase 2 implementation"
```

---

## Quality Gates Checklist

- [ ] Database schema for servers created
- [ ] Server CRUD operations work with database
- [ ] Credentials encrypted with AES-256
- [ ] MCP tools implemented:
  - [ ] add_server
  - [ ] get_server
  - [ ] list_servers
  - [ ] update_server
  - [ ] delete_server
  - [ ] test_connection
- [ ] Credentials never logged or exposed
- [ ] All unit tests pass

---

## Definition of Done

User can:
1. Add a server with SSH credentials (password or key)
2. See the server in the list
3. Test the SSH connection
4. Update server configuration
5. Delete the server

---

**Document Version:** 1.0
**Created:** 2025-12-25

"""Tests for server database operations."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager
from services.database_service import DatabaseService
from models.server import ServerConnection, AuthType, ServerStatus


class TestServerDatabaseOperations:
    """Tests for server CRUD in database."""

    @pytest.fixture
    def mock_connection(self):
        """Create mock database connection."""
        conn = MagicMock()
        conn.execute = AsyncMock()
        conn.commit = AsyncMock()
        conn.rollback = AsyncMock()
        return conn

    @pytest.fixture
    def db_service(self, mock_connection):
        """Create database service with mocked connection."""
        service = DatabaseService(data_directory="/tmp/test")

        # Mock the get_connection context manager
        @asynccontextmanager
        async def mock_get_connection():
            yield mock_connection

        service.get_connection = mock_get_connection
        return service

    @pytest.mark.asyncio
    async def test_create_server(self, db_service, mock_connection):
        """Should create server in database."""
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
        assert mock_connection.execute.call_count == 2  # Two inserts
        assert mock_connection.commit.call_count == 1

    @pytest.mark.asyncio
    async def test_get_server_by_id(self, db_service, mock_connection):
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
        mock_cursor = MagicMock()
        mock_cursor.fetchone = AsyncMock(return_value=mock_row)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        server = await db_service.get_server_by_id("server-123")

        assert server is not None
        assert server.name == "Test Server"
        assert server.host == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_get_all_servers(self, db_service, mock_connection):
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
        mock_cursor = MagicMock()
        mock_cursor.fetchall = AsyncMock(return_value=mock_rows)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        servers = await db_service.get_all_servers_from_db()

        assert len(servers) == 2
        assert servers[0].name == "Server 1"
        assert servers[1].name == "Server 2"

    @pytest.mark.asyncio
    async def test_update_server(self, db_service, mock_connection):
        """Should update server in database."""
        result = await db_service.update_server(
            server_id="server-123",
            name="Updated Server",
            host="192.168.1.200"
        )

        assert result is True
        assert mock_connection.execute.call_count == 1
        assert mock_connection.commit.call_count == 1

    @pytest.mark.asyncio
    async def test_delete_server(self, db_service, mock_connection):
        """Should delete server from database."""
        result = await db_service.delete_server("server-123")

        assert result is True
        assert mock_connection.execute.call_count == 1
        assert mock_connection.commit.call_count == 1

    @pytest.mark.asyncio
    async def test_get_server_credentials(self, db_service, mock_connection):
        """Should retrieve encrypted credentials."""
        mock_row = {"encrypted_data": "encrypted-secret-data"}
        mock_cursor = MagicMock()
        mock_cursor.fetchone = AsyncMock(return_value=mock_row)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        credentials = await db_service.get_server_credentials("server-123")

        assert credentials == "encrypted-secret-data"

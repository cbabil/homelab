"""Tests for app installation database operations."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager


class TestAppDatabaseOperations:
    """Tests for app installation CRUD in database."""

    @pytest.fixture
    def mock_connection(self):
        """Create mock database connection."""
        conn = MagicMock()
        conn.execute = AsyncMock()
        conn.commit = AsyncMock()
        return conn

    @pytest.fixture
    def db_service(self, mock_connection):
        """Create database service with mocked connection."""
        from services.database_service import DatabaseService

        service = DatabaseService(data_directory="/tmp/test")

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_connection

        service.get_connection = mock_get_connection
        return service

    @pytest.mark.asyncio
    async def test_create_installation(self, db_service, mock_connection):
        """Should create installation record."""
        result = await db_service.create_installation(
            id="inst-123",
            server_id="server-456",
            app_id="portainer",
            container_name="portainer-123",
            status="pending",
            config={"ports": {"9000": 9000}},
            installed_at="2025-01-01T00:00:00Z"
        )

        assert result is not None
        mock_connection.execute.assert_called()

    @pytest.mark.asyncio
    async def test_update_installation(self, db_service, mock_connection):
        """Should update installation record."""
        result = await db_service.update_installation(
            install_id="inst-123",
            status="running",
            container_id="abc123"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_installation(self, db_service, mock_connection):
        """Should get installation by server and app ID."""
        mock_row = {
            "id": "inst-123",
            "server_id": "server-456",
            "app_id": "portainer",
            "container_id": "abc123",
            "container_name": "portainer-123",
            "status": "running",
            "config": '{"ports": {"9000": 9000}}',
            "installed_at": "2025-01-01T00:00:00Z",
            "started_at": "2025-01-01T00:01:00Z",
            "error_message": None
        }
        mock_connection.execute.return_value = MagicMock(
            fetchone=AsyncMock(return_value=mock_row)
        )

        result = await db_service.get_installation("server-456", "portainer")

        assert result is not None
        assert result.status == "running"

    @pytest.mark.asyncio
    async def test_get_installations(self, db_service, mock_connection):
        """Should get all installations for a server."""
        mock_rows = [
            {"id": "inst-1", "server_id": "server-456", "app_id": "portainer",
             "container_id": "abc", "container_name": "portainer-1",
             "status": "running", "config": "{}", "installed_at": "2025-01-01T00:00:00Z",
             "started_at": None, "error_message": None},
            {"id": "inst-2", "server_id": "server-456", "app_id": "nginx",
             "container_id": "def", "container_name": "nginx-1",
             "status": "stopped", "config": "{}", "installed_at": "2025-01-01T00:00:00Z",
             "started_at": None, "error_message": None}
        ]
        mock_connection.execute.return_value = MagicMock(
            fetchall=AsyncMock(return_value=mock_rows)
        )

        result = await db_service.get_installations("server-456")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_delete_installation(self, db_service, mock_connection):
        """Should delete installation record."""
        result = await db_service.delete_installation("server-456", "portainer")

        assert result is True
        mock_connection.execute.assert_called()

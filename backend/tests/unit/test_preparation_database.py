"""Tests for preparation database operations."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager


class TestPreparationDatabaseOperations:
    """Tests for preparation CRUD in database."""

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

        # Mock the get_connection context manager
        @asynccontextmanager
        async def mock_get_connection():
            yield mock_connection

        service.get_connection = mock_get_connection
        return service

    @pytest.mark.asyncio
    async def test_create_preparation(self, db_service, mock_connection):
        """Should create preparation record."""
        result = await db_service.create_preparation(
            id="prep-123",
            server_id="server-456",
            status="pending",
            started_at="2025-01-01T00:00:00Z"
        )

        assert result is not None
        mock_connection.execute.assert_called()

    @pytest.mark.asyncio
    async def test_update_preparation(self, db_service, mock_connection):
        """Should update preparation record."""
        result = await db_service.update_preparation(
            prep_id="prep-123",
            status="in_progress",
            current_step="install_docker"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_add_preparation_log(self, db_service, mock_connection):
        """Should add preparation log entry."""
        result = await db_service.add_preparation_log(
            id="log-123",
            server_id="server-456",
            preparation_id="prep-123",
            step="detect_os",
            status="completed",
            message="Detected Ubuntu 22.04",
            timestamp="2025-01-01T00:00:00Z"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_preparation(self, db_service, mock_connection):
        """Should get preparation by server ID."""
        mock_row = {
            "id": "prep-123",
            "server_id": "server-456",
            "status": "in_progress",
            "current_step": "install_docker",
            "detected_os": "ubuntu",
            "started_at": "2025-01-01T00:00:00Z",
            "completed_at": None,
            "error_message": None
        }
        mock_cursor = MagicMock()
        mock_cursor.fetchone = AsyncMock(return_value=mock_row)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        result = await db_service.get_preparation("server-456")

        assert result is not None
        assert result.status == "in_progress"

    @pytest.mark.asyncio
    async def test_get_preparation_logs(self, db_service, mock_connection):
        """Should get all logs for a server."""
        mock_rows = [
            {"id": "log-1", "server_id": "server-456", "preparation_id": "prep-123",
             "step": "detect_os", "status": "completed", "message": "OK",
             "output": None, "error": None, "timestamp": "2025-01-01T00:00:00Z"},
            {"id": "log-2", "server_id": "server-456", "preparation_id": "prep-123",
             "step": "update_packages", "status": "completed", "message": "OK",
             "output": None, "error": None, "timestamp": "2025-01-01T00:01:00Z"}
        ]
        mock_cursor = MagicMock()
        mock_cursor.fetchall = AsyncMock(return_value=mock_rows)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        result = await db_service.get_preparation_logs("server-456")

        assert len(result) == 2

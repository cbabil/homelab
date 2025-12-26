"""Tests for metrics database operations."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager


class TestMetricsDatabaseOperations:
    """Tests for metrics CRUD in database."""

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
    async def test_save_server_metrics(self, db_service, mock_connection):
        """Should save server metrics."""
        from models.metrics import ServerMetrics

        metrics = ServerMetrics(
            id="sm-123",
            server_id="server-456",
            cpu_percent=45.5,
            memory_percent=62.3,
            memory_used_mb=4096,
            memory_total_mb=8192,
            disk_percent=78.0,
            disk_used_gb=156,
            disk_total_gb=200,
            timestamp="2025-01-01T00:00:00Z"
        )

        result = await db_service.save_server_metrics(metrics)

        assert result is True
        mock_connection.execute.assert_called()

    @pytest.mark.asyncio
    async def test_save_container_metrics(self, db_service, mock_connection):
        """Should save container metrics."""
        from models.metrics import ContainerMetrics

        metrics = ContainerMetrics(
            id="cm-123",
            server_id="server-456",
            container_id="abc123",
            container_name="portainer",
            cpu_percent=12.5,
            memory_usage_mb=256,
            memory_limit_mb=512,
            status="running",
            timestamp="2025-01-01T00:00:00Z"
        )

        result = await db_service.save_container_metrics(metrics)

        assert result is True

    @pytest.mark.asyncio
    async def test_save_activity_log(self, db_service, mock_connection):
        """Should save activity log."""
        from models.metrics import ActivityLog, ActivityType

        log = ActivityLog(
            id="act-123",
            activity_type=ActivityType.USER_LOGIN,
            user_id="user-456",
            message="User logged in",
            details={},
            timestamp="2025-01-01T00:00:00Z"
        )

        result = await db_service.save_activity_log(log)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_server_metrics(self, db_service, mock_connection):
        """Should get server metrics."""
        mock_rows = [
            {"id": "sm-1", "server_id": "server-456", "cpu_percent": 45.5,
             "memory_percent": 62.3, "memory_used_mb": 4096, "memory_total_mb": 8192,
             "disk_percent": 78.0, "disk_used_gb": 156, "disk_total_gb": 200,
             "network_rx_bytes": 0, "network_tx_bytes": 0, "load_average_1m": None,
             "load_average_5m": None, "load_average_15m": None, "uptime_seconds": None,
             "timestamp": "2025-01-01T00:00:00Z"}
        ]
        mock_cursor = MagicMock()
        mock_cursor.fetchall = AsyncMock(return_value=mock_rows)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        result = await db_service.get_server_metrics("server-456")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_activity_logs(self, db_service, mock_connection):
        """Should get activity logs."""
        mock_rows = [
            {"id": "act-1", "activity_type": "user_login", "user_id": "user-456",
             "server_id": None, "app_id": None, "message": "Login",
             "details": "{}", "timestamp": "2025-01-01T00:00:00Z"}
        ]
        mock_cursor = MagicMock()
        mock_cursor.fetchall = AsyncMock(return_value=mock_rows)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        result = await db_service.get_activity_logs(limit=10)

        assert len(result) == 1

"""
Unit tests for services/database/metrics_service.py.

Tests MetricsDatabaseService methods.
"""

import pytest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from services.database.metrics_service import MetricsDatabaseService
from models.metrics import ServerMetrics, ContainerMetrics, ActivityLog, ActivityType


@pytest.fixture
def mock_connection():
    """Create mock DatabaseConnection."""
    return MagicMock()


@pytest.fixture
def service(mock_connection):
    """Create MetricsDatabaseService instance."""
    return MetricsDatabaseService(mock_connection)


def create_mock_context(mock_conn):
    """Create async context manager for database connection."""
    @asynccontextmanager
    async def context():
        yield mock_conn
    return context()


@pytest.fixture
def sample_server_metrics():
    """Create sample server metrics."""
    return ServerMetrics(
        id="metric-123",
        server_id="server-456",
        cpu_percent=45.5,
        memory_percent=67.2,
        memory_used_mb=2048,
        memory_total_mb=4096,
        disk_percent=55.0,
        disk_used_gb=100,
        disk_total_gb=200,
        network_rx_bytes=1000000,
        network_tx_bytes=500000,
        load_average_1m=1.5,
        load_average_5m=1.2,
        load_average_15m=1.0,
        uptime_seconds=86400,
        timestamp="2024-01-15T10:00:00",
    )


@pytest.fixture
def sample_server_metrics_row():
    """Create sample server metrics row from database."""
    return {
        "id": "metric-123",
        "server_id": "server-456",
        "cpu_percent": 45.5,
        "memory_percent": 67.2,
        "memory_used_mb": 2048,
        "memory_total_mb": 4096,
        "disk_percent": 55.0,
        "disk_used_gb": 100,
        "disk_total_gb": 200,
        "network_rx_bytes": 1000000,
        "network_tx_bytes": 500000,
        "load_average_1m": 1.5,
        "load_average_5m": 1.2,
        "load_average_15m": 1.0,
        "uptime_seconds": 86400,
        "timestamp": "2024-01-15T10:00:00",
    }


@pytest.fixture
def sample_container_metrics():
    """Create sample container metrics."""
    return ContainerMetrics(
        id="container-metric-123",
        server_id="server-456",
        container_id="abc123",
        container_name="nginx",
        cpu_percent=10.5,
        memory_usage_mb=256,
        memory_limit_mb=512,
        network_rx_bytes=50000,
        network_tx_bytes=25000,
        status="running",
        timestamp="2024-01-15T10:00:00",
    )


@pytest.fixture
def sample_container_metrics_row():
    """Create sample container metrics row from database."""
    return {
        "id": "container-metric-123",
        "server_id": "server-456",
        "container_id": "abc123",
        "container_name": "nginx",
        "cpu_percent": 10.5,
        "memory_usage_mb": 256,
        "memory_limit_mb": 512,
        "network_rx_bytes": 50000,
        "network_tx_bytes": 25000,
        "status": "running",
        "timestamp": "2024-01-15T10:00:00",
    }


@pytest.fixture
def sample_activity_log():
    """Create sample activity log."""
    return ActivityLog(
        id="log-123",
        activity_type=ActivityType.USER_LOGIN,
        user_id="user-456",
        server_id=None,
        app_id=None,
        message="User logged in",
        details={"ip": "192.168.1.100"},
        timestamp="2024-01-15T10:00:00",
    )


@pytest.fixture
def sample_activity_log_row():
    """Create sample activity log row from database."""
    return {
        "id": "log-123",
        "activity_type": "user_login",
        "user_id": "user-456",
        "server_id": None,
        "app_id": None,
        "message": "User logged in",
        "details": '{"ip": "192.168.1.100"}',
        "timestamp": "2024-01-15T10:00:00",
    }


class TestMetricsDatabaseServiceInit:
    """Tests for MetricsDatabaseService initialization."""

    def test_init_stores_connection(self, mock_connection):
        """Service should store connection reference."""
        service = MetricsDatabaseService(mock_connection)
        assert service._conn is mock_connection


class TestSaveServerMetrics:
    """Tests for save_server_metrics method."""

    @pytest.mark.asyncio
    async def test_save_server_metrics_success(
        self, service, mock_connection, sample_server_metrics
    ):
        """save_server_metrics should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.save_server_metrics(sample_server_metrics)

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_server_metrics_exception(
        self, service, mock_connection, sample_server_metrics
    ):
        """save_server_metrics should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.metrics_service.logger"):
            result = await service.save_server_metrics(sample_server_metrics)

        assert result is False


class TestGetServerMetrics:
    """Tests for get_server_metrics method."""

    @pytest.mark.asyncio
    async def test_get_server_metrics_success(
        self, service, mock_connection, sample_server_metrics_row
    ):
        """get_server_metrics should return list of metrics."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[sample_server_metrics_row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.get_server_metrics("server-456")

        assert len(result) == 1
        assert result[0].id == "metric-123"
        assert result[0].cpu_percent == 45.5

    @pytest.mark.asyncio
    async def test_get_server_metrics_with_since(
        self, service, mock_connection, sample_server_metrics_row
    ):
        """get_server_metrics should filter by since timestamp."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[sample_server_metrics_row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            await service.get_server_metrics(
                "server-456", since="2024-01-15T00:00:00"
            )

        call_args = mock_conn.execute.call_args[0]
        assert "timestamp >=" in call_args[0]

    @pytest.mark.asyncio
    async def test_get_server_metrics_empty(self, service, mock_connection):
        """get_server_metrics should return empty list when no metrics."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.get_server_metrics("server-456")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_server_metrics_exception(self, service, mock_connection):
        """get_server_metrics should return empty list on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.metrics_service.logger"):
            result = await service.get_server_metrics("server-456")

        assert result == []


class TestSaveContainerMetrics:
    """Tests for save_container_metrics method."""

    @pytest.mark.asyncio
    async def test_save_container_metrics_success(
        self, service, mock_connection, sample_container_metrics
    ):
        """save_container_metrics should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.save_container_metrics(sample_container_metrics)

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_container_metrics_exception(
        self, service, mock_connection, sample_container_metrics
    ):
        """save_container_metrics should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.metrics_service.logger"):
            result = await service.save_container_metrics(sample_container_metrics)

        assert result is False


class TestGetContainerMetrics:
    """Tests for get_container_metrics method."""

    @pytest.mark.asyncio
    async def test_get_container_metrics_success(
        self, service, mock_connection, sample_container_metrics_row
    ):
        """get_container_metrics should return list of metrics."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[sample_container_metrics_row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.get_container_metrics("server-456")

        assert len(result) == 1
        assert result[0].container_name == "nginx"

    @pytest.mark.asyncio
    async def test_get_container_metrics_by_name(
        self, service, mock_connection, sample_container_metrics_row
    ):
        """get_container_metrics should filter by container name."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[sample_container_metrics_row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            await service.get_container_metrics("server-456", container_name="nginx")

        call_args = mock_conn.execute.call_args[0]
        assert "container_name" in call_args[0]

    @pytest.mark.asyncio
    async def test_get_container_metrics_with_since(
        self, service, mock_connection, sample_container_metrics_row
    ):
        """get_container_metrics should filter by since timestamp."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[sample_container_metrics_row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            await service.get_container_metrics(
                "server-456", since="2024-01-15T00:00:00"
            )

        call_args = mock_conn.execute.call_args[0]
        assert "timestamp >=" in call_args[0]

    @pytest.mark.asyncio
    async def test_get_container_metrics_empty(self, service, mock_connection):
        """get_container_metrics should return empty list when no metrics."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.get_container_metrics("server-456")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_container_metrics_exception(self, service, mock_connection):
        """get_container_metrics should return empty list on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.metrics_service.logger"):
            result = await service.get_container_metrics("server-456")

        assert result == []


class TestSaveActivityLog:
    """Tests for save_activity_log method."""

    @pytest.mark.asyncio
    async def test_save_activity_log_success(
        self, service, mock_connection, sample_activity_log
    ):
        """save_activity_log should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.save_activity_log(sample_activity_log)

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_activity_log_no_details(self, service, mock_connection):
        """save_activity_log should handle log with no details."""
        log = ActivityLog(
            id="log-123",
            activity_type=ActivityType.USER_LOGOUT,
            user_id="user-456",
            message="User logged out",
            details={},
            timestamp="2024-01-15T10:00:00",
        )
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.save_activity_log(log)

        assert result is True

    @pytest.mark.asyncio
    async def test_save_activity_log_exception(
        self, service, mock_connection, sample_activity_log
    ):
        """save_activity_log should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.metrics_service.logger"):
            result = await service.save_activity_log(sample_activity_log)

        assert result is False


class TestGetActivityLogs:
    """Tests for get_activity_logs method."""

    @pytest.mark.asyncio
    async def test_get_activity_logs_success(
        self, service, mock_connection, sample_activity_log_row
    ):
        """get_activity_logs should return list of logs."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[sample_activity_log_row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.get_activity_logs()

        assert len(result) == 1
        assert result[0].activity_type == ActivityType.USER_LOGIN

    @pytest.mark.asyncio
    async def test_get_activity_logs_by_types(
        self, service, mock_connection, sample_activity_log_row
    ):
        """get_activity_logs should filter by activity types."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[sample_activity_log_row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            await service.get_activity_logs(
                activity_types=["user_login", "user_logout"]
            )

        call_args = mock_conn.execute.call_args[0]
        assert "activity_type IN" in call_args[0]

    @pytest.mark.asyncio
    async def test_get_activity_logs_by_user(
        self, service, mock_connection, sample_activity_log_row
    ):
        """get_activity_logs should filter by user_id."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[sample_activity_log_row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            await service.get_activity_logs(user_id="user-456")

        call_args = mock_conn.execute.call_args[0]
        assert "user_id" in call_args[0]

    @pytest.mark.asyncio
    async def test_get_activity_logs_by_server(
        self, service, mock_connection, sample_activity_log_row
    ):
        """get_activity_logs should filter by server_id."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[sample_activity_log_row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            await service.get_activity_logs(server_id="server-456")

        call_args = mock_conn.execute.call_args[0]
        assert "server_id" in call_args[0]

    @pytest.mark.asyncio
    async def test_get_activity_logs_with_since_until(
        self, service, mock_connection, sample_activity_log_row
    ):
        """get_activity_logs should filter by time range."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[sample_activity_log_row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            await service.get_activity_logs(
                since="2024-01-15T00:00:00", until="2024-01-15T23:59:59"
            )

        call_args = mock_conn.execute.call_args[0]
        assert "timestamp >=" in call_args[0]
        assert "timestamp <=" in call_args[0]

    @pytest.mark.asyncio
    async def test_get_activity_logs_empty_details(
        self, service, mock_connection
    ):
        """get_activity_logs should handle empty details."""
        row = {
            "id": "log-123",
            "activity_type": "user_login",
            "user_id": "user-456",
            "server_id": None,
            "app_id": None,
            "message": "User logged in",
            "details": None,
            "timestamp": "2024-01-15T10:00:00",
        }
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.get_activity_logs()

        assert result[0].details == {}

    @pytest.mark.asyncio
    async def test_get_activity_logs_empty(self, service, mock_connection):
        """get_activity_logs should return empty list when no logs."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.get_activity_logs()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_activity_logs_exception(self, service, mock_connection):
        """get_activity_logs should return empty list on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.metrics_service.logger"):
            result = await service.get_activity_logs()

        assert result == []


class TestCountActivityLogs:
    """Tests for count_activity_logs method."""

    @pytest.mark.asyncio
    async def test_count_activity_logs_success(self, service, mock_connection):
        """count_activity_logs should return count."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value={"count": 42})
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.count_activity_logs()

        assert result == 42

    @pytest.mark.asyncio
    async def test_count_activity_logs_by_types(self, service, mock_connection):
        """count_activity_logs should filter by activity types."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value={"count": 10})
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            await service.count_activity_logs(
                activity_types=["user_login", "user_logout"]
            )

        call_args = mock_conn.execute.call_args[0]
        assert "activity_type IN" in call_args[0]

    @pytest.mark.asyncio
    async def test_count_activity_logs_with_since(self, service, mock_connection):
        """count_activity_logs should filter by since timestamp."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value={"count": 5})
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            await service.count_activity_logs(since="2024-01-15T00:00:00")

        call_args = mock_conn.execute.call_args[0]
        assert "timestamp >=" in call_args[0]

    @pytest.mark.asyncio
    async def test_count_activity_logs_no_result(self, service, mock_connection):
        """count_activity_logs should return 0 when no result."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.count_activity_logs()

        assert result == 0

    @pytest.mark.asyncio
    async def test_count_activity_logs_exception(self, service, mock_connection):
        """count_activity_logs should return 0 on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.metrics_service.logger"):
            result = await service.count_activity_logs()

        assert result == 0


class TestGetLogEntriesCountBeforeDate:
    """Tests for get_log_entries_count_before_date method."""

    @pytest.mark.asyncio
    async def test_get_count_success(self, service, mock_connection):
        """get_log_entries_count_before_date should return count."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value={"count": 100})
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.get_log_entries_count_before_date("2024-01-01")

        assert result == 100

    @pytest.mark.asyncio
    async def test_get_count_no_result(self, service, mock_connection):
        """get_log_entries_count_before_date should return 0 when no result."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.get_log_entries_count_before_date("2024-01-01")

        assert result == 0

    @pytest.mark.asyncio
    async def test_get_count_exception(self, service, mock_connection):
        """get_log_entries_count_before_date should return 0 on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.metrics_service.logger"):
            result = await service.get_log_entries_count_before_date("2024-01-01")

        assert result == 0


class TestDeleteLogEntriesBeforeDate:
    """Tests for delete_log_entries_before_date method."""

    @pytest.mark.asyncio
    async def test_delete_success_single_batch(self, service, mock_connection):
        """delete_log_entries_before_date should delete entries in batch."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 500
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.delete_log_entries_before_date("2024-01-01")

        assert result == 500
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_success_multiple_batches(self, service, mock_connection):
        """delete_log_entries_before_date should handle multiple batches."""
        mock_cursor1 = AsyncMock()
        mock_cursor1.rowcount = 1000
        mock_cursor2 = AsyncMock()
        mock_cursor2.rowcount = 500
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(
            side_effect=[None, mock_cursor1, mock_cursor2]
        )
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            result = await service.delete_log_entries_before_date(
                "2024-01-01", batch_size=1000
            )

        assert result == 1500
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_exception_in_loop(self, service, mock_connection):
        """delete_log_entries_before_date should rollback on exception in loop."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(
            side_effect=[None, Exception("Delete failed")]
        )
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.metrics_service.logger"):
            with pytest.raises(Exception, match="Delete failed"):
                await service.delete_log_entries_before_date("2024-01-01")

        mock_conn.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_exception_outer(self, service, mock_connection):
        """delete_log_entries_before_date should raise on outer exception."""
        mock_connection.get_connection.side_effect = Exception("Connection failed")

        with patch("services.database.metrics_service.logger"):
            with pytest.raises(Exception, match="Connection failed"):
                await service.delete_log_entries_before_date("2024-01-01")

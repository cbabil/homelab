"""
Unit tests for services/database_service.py - Metrics method delegation.

Tests metrics-related methods that delegate to MetricsDatabaseService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models.metrics import ServerMetrics, ContainerMetrics, ActivityLog


@pytest.fixture
def mock_metrics_service():
    """Create mock MetricsDatabaseService."""
    return MagicMock()


@pytest.fixture
def db_service_with_metrics_mock(mock_metrics_service):
    """Create DatabaseService with mocked metrics service."""
    with patch("services.database_service.DatabaseConnection"), \
         patch("services.database_service.UserDatabaseService"), \
         patch("services.database_service.ServerDatabaseService"), \
         patch("services.database_service.SessionDatabaseService"), \
         patch("services.database_service.AppDatabaseService"), \
         patch("services.database_service.MetricsDatabaseService") as MockMetrics, \
         patch("services.database_service.SystemDatabaseService"), \
         patch("services.database_service.ExportDatabaseService"), \
         patch("services.database_service.SchemaInitializer"):
        from services.database_service import DatabaseService
        MockMetrics.return_value = mock_metrics_service
        return DatabaseService()


@pytest.fixture
def sample_server_metrics():
    """Create sample ServerMetrics."""
    return ServerMetrics(
        id="metrics-123",
        server_id="srv-123",
        timestamp="2024-01-15T10:00:00Z",
        cpu_percent=45.5,
        memory_percent=60.2,
        memory_used_mb=4096,
        memory_total_mb=8192,
        disk_percent=75.0,
        disk_used_gb=150,
        disk_total_gb=200,
    )


@pytest.fixture
def sample_container_metrics():
    """Create sample ContainerMetrics."""
    return ContainerMetrics(
        id="container-metrics-123",
        server_id="srv-123",
        container_id="abc123def456",
        container_name="my-app",
        timestamp="2024-01-15T10:00:00Z",
        cpu_percent=25.0,
        memory_usage_mb=512,
        memory_limit_mb=1024,
        status="running",
    )


@pytest.fixture
def sample_activity_log():
    """Create sample ActivityLog."""
    from models.metrics import ActivityType
    return ActivityLog(
        id="log-123",
        activity_type=ActivityType.SERVER_ADDED,
        user_id="user-123",
        timestamp="2024-01-15T10:00:00Z",
        message="Server added",
        details={"server_id": "srv-123"},
    )


class TestSaveServerMetrics:
    """Tests for save_server_metrics method."""

    @pytest.mark.asyncio
    async def test_save_server_metrics_success(
        self, db_service_with_metrics_mock, mock_metrics_service, sample_server_metrics
    ):
        """save_server_metrics should delegate to metrics service."""
        mock_metrics_service.save_server_metrics = AsyncMock(return_value=True)

        result = await db_service_with_metrics_mock.save_server_metrics(
            sample_server_metrics
        )

        mock_metrics_service.save_server_metrics.assert_awaited_once_with(
            sample_server_metrics
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_save_server_metrics_failure(
        self, db_service_with_metrics_mock, mock_metrics_service, sample_server_metrics
    ):
        """save_server_metrics should return False on failure."""
        mock_metrics_service.save_server_metrics = AsyncMock(return_value=False)

        result = await db_service_with_metrics_mock.save_server_metrics(
            sample_server_metrics
        )

        assert result is False


class TestSaveContainerMetrics:
    """Tests for save_container_metrics method."""

    @pytest.mark.asyncio
    async def test_save_container_metrics_success(
        self,
        db_service_with_metrics_mock,
        mock_metrics_service,
        sample_container_metrics,
    ):
        """save_container_metrics should delegate to metrics service."""
        mock_metrics_service.save_container_metrics = AsyncMock(return_value=True)

        result = await db_service_with_metrics_mock.save_container_metrics(
            sample_container_metrics
        )

        mock_metrics_service.save_container_metrics.assert_awaited_once_with(
            sample_container_metrics
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_save_container_metrics_failure(
        self,
        db_service_with_metrics_mock,
        mock_metrics_service,
        sample_container_metrics,
    ):
        """save_container_metrics should return False on failure."""
        mock_metrics_service.save_container_metrics = AsyncMock(return_value=False)

        result = await db_service_with_metrics_mock.save_container_metrics(
            sample_container_metrics
        )

        assert result is False


class TestSaveActivityLog:
    """Tests for save_activity_log method."""

    @pytest.mark.asyncio
    async def test_save_activity_log_success(
        self, db_service_with_metrics_mock, mock_metrics_service, sample_activity_log
    ):
        """save_activity_log should delegate to metrics service."""
        mock_metrics_service.save_activity_log = AsyncMock(return_value=True)

        result = await db_service_with_metrics_mock.save_activity_log(
            sample_activity_log
        )

        mock_metrics_service.save_activity_log.assert_awaited_once_with(
            sample_activity_log
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_save_activity_log_failure(
        self, db_service_with_metrics_mock, mock_metrics_service, sample_activity_log
    ):
        """save_activity_log should return False on failure."""
        mock_metrics_service.save_activity_log = AsyncMock(return_value=False)

        result = await db_service_with_metrics_mock.save_activity_log(
            sample_activity_log
        )

        assert result is False


class TestGetServerMetrics:
    """Tests for get_server_metrics method."""

    @pytest.mark.asyncio
    async def test_get_server_metrics_default_params(
        self, db_service_with_metrics_mock, mock_metrics_service, sample_server_metrics
    ):
        """get_server_metrics should use default params."""
        mock_metrics_service.get_server_metrics = AsyncMock(
            return_value=[sample_server_metrics]
        )

        result = await db_service_with_metrics_mock.get_server_metrics("srv-123")

        mock_metrics_service.get_server_metrics.assert_awaited_once_with(
            "srv-123", None, 100
        )
        assert result == [sample_server_metrics]

    @pytest.mark.asyncio
    async def test_get_server_metrics_with_params(
        self, db_service_with_metrics_mock, mock_metrics_service, sample_server_metrics
    ):
        """get_server_metrics should pass all params."""
        mock_metrics_service.get_server_metrics = AsyncMock(
            return_value=[sample_server_metrics]
        )

        result = await db_service_with_metrics_mock.get_server_metrics(
            "srv-123", since="2024-01-01T00:00:00Z", limit=50
        )

        mock_metrics_service.get_server_metrics.assert_awaited_once_with(
            "srv-123", "2024-01-01T00:00:00Z", 50
        )
        assert result == [sample_server_metrics]

    @pytest.mark.asyncio
    async def test_get_server_metrics_empty(
        self, db_service_with_metrics_mock, mock_metrics_service
    ):
        """get_server_metrics should return empty list when none."""
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=[])

        result = await db_service_with_metrics_mock.get_server_metrics("srv-123")

        assert result == []


class TestGetContainerMetrics:
    """Tests for get_container_metrics method."""

    @pytest.mark.asyncio
    async def test_get_container_metrics_default_params(
        self,
        db_service_with_metrics_mock,
        mock_metrics_service,
        sample_container_metrics,
    ):
        """get_container_metrics should use default params."""
        mock_metrics_service.get_container_metrics = AsyncMock(
            return_value=[sample_container_metrics]
        )

        result = await db_service_with_metrics_mock.get_container_metrics("srv-123")

        mock_metrics_service.get_container_metrics.assert_awaited_once_with(
            "srv-123", None, None, 100
        )
        assert result == [sample_container_metrics]

    @pytest.mark.asyncio
    async def test_get_container_metrics_with_params(
        self,
        db_service_with_metrics_mock,
        mock_metrics_service,
        sample_container_metrics,
    ):
        """get_container_metrics should pass all params."""
        mock_metrics_service.get_container_metrics = AsyncMock(
            return_value=[sample_container_metrics]
        )

        result = await db_service_with_metrics_mock.get_container_metrics(
            "srv-123",
            container_name="my-app",
            since="2024-01-01T00:00:00Z",
            limit=25,
        )

        mock_metrics_service.get_container_metrics.assert_awaited_once_with(
            "srv-123", "my-app", "2024-01-01T00:00:00Z", 25
        )
        assert result == [sample_container_metrics]


class TestGetActivityLogs:
    """Tests for get_activity_logs method."""

    @pytest.mark.asyncio
    async def test_get_activity_logs_default_params(
        self, db_service_with_metrics_mock, mock_metrics_service, sample_activity_log
    ):
        """get_activity_logs should use default params."""
        mock_metrics_service.get_activity_logs = AsyncMock(
            return_value=[sample_activity_log]
        )

        result = await db_service_with_metrics_mock.get_activity_logs()

        mock_metrics_service.get_activity_logs.assert_awaited_once_with(
            None, None, None, None, None, 100, 0
        )
        assert result == [sample_activity_log]

    @pytest.mark.asyncio
    async def test_get_activity_logs_with_params(
        self, db_service_with_metrics_mock, mock_metrics_service, sample_activity_log
    ):
        """get_activity_logs should pass all params."""
        mock_metrics_service.get_activity_logs = AsyncMock(
            return_value=[sample_activity_log]
        )

        await db_service_with_metrics_mock.get_activity_logs(
            activity_types=["server_created"],
            user_id="user-123",
            server_id="srv-123",
            since="2024-01-01T00:00:00Z",
            until="2024-01-31T23:59:59Z",
            limit=50,
            offset=10,
        )

        mock_metrics_service.get_activity_logs.assert_awaited_once_with(
            ["server_created"],
            "user-123",
            "srv-123",
            "2024-01-01T00:00:00Z",
            "2024-01-31T23:59:59Z",
            50,
            10,
        )


class TestCountActivityLogs:
    """Tests for count_activity_logs method."""

    @pytest.mark.asyncio
    async def test_count_activity_logs_default_params(
        self, db_service_with_metrics_mock, mock_metrics_service
    ):
        """count_activity_logs should use default params."""
        mock_metrics_service.count_activity_logs = AsyncMock(return_value=42)

        result = await db_service_with_metrics_mock.count_activity_logs()

        mock_metrics_service.count_activity_logs.assert_awaited_once_with(None, None)
        assert result == 42

    @pytest.mark.asyncio
    async def test_count_activity_logs_with_params(
        self, db_service_with_metrics_mock, mock_metrics_service
    ):
        """count_activity_logs should pass all params."""
        mock_metrics_service.count_activity_logs = AsyncMock(return_value=15)

        result = await db_service_with_metrics_mock.count_activity_logs(
            activity_types=["login", "logout"], since="2024-01-01T00:00:00Z"
        )

        mock_metrics_service.count_activity_logs.assert_awaited_once_with(
            ["login", "logout"], "2024-01-01T00:00:00Z"
        )
        assert result == 15


class TestLogRetention:
    """Tests for log retention methods."""

    @pytest.mark.asyncio
    async def test_get_log_entries_count_before_date(
        self, db_service_with_metrics_mock, mock_metrics_service
    ):
        """get_log_entries_count_before_date should delegate to metrics service."""
        mock_metrics_service.get_log_entries_count_before_date = AsyncMock(
            return_value=500
        )

        result = await db_service_with_metrics_mock.get_log_entries_count_before_date(
            "2024-01-01T00:00:00Z"
        )

        mock_metrics_service.get_log_entries_count_before_date.assert_awaited_once_with(
            "2024-01-01T00:00:00Z"
        )
        assert result == 500

    @pytest.mark.asyncio
    async def test_delete_log_entries_before_date_default(
        self, db_service_with_metrics_mock, mock_metrics_service
    ):
        """delete_log_entries_before_date should use default batch_size."""
        mock_metrics_service.delete_log_entries_before_date = AsyncMock(
            return_value=250
        )

        result = await db_service_with_metrics_mock.delete_log_entries_before_date(
            "2024-01-01T00:00:00Z"
        )

        mock_metrics_service.delete_log_entries_before_date.assert_awaited_once_with(
            "2024-01-01T00:00:00Z", 1000
        )
        assert result == 250

    @pytest.mark.asyncio
    async def test_delete_log_entries_before_date_custom_batch(
        self, db_service_with_metrics_mock, mock_metrics_service
    ):
        """delete_log_entries_before_date should accept custom batch_size."""
        mock_metrics_service.delete_log_entries_before_date = AsyncMock(
            return_value=100
        )

        result = await db_service_with_metrics_mock.delete_log_entries_before_date(
            "2024-01-01T00:00:00Z", batch_size=500
        )

        mock_metrics_service.delete_log_entries_before_date.assert_awaited_once_with(
            "2024-01-01T00:00:00Z", 500
        )
        assert result == 100

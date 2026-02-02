"""
Unit tests for services/dashboard_service.py - Advanced functionality

Tests metrics calculation, error handling, and activities.
"""

import pytest
from unittest.mock import AsyncMock, patch
from dataclasses import dataclass
from datetime import datetime, UTC

from services.dashboard_service import DashboardService
from models.metrics import ActivityLog, ActivityType
from models.server import ServerStatus


@dataclass
class MockServer:
    """Mock server object for testing."""
    id: str
    status: ServerStatus = ServerStatus.CONNECTED


@dataclass
class MockApp:
    """Mock app object for testing."""
    status: str = "running"


@dataclass
class MockMetric:
    """Mock metric object for testing."""
    cpu_percent: float = 50.0
    memory_percent: float = 60.0
    disk_percent: float = 70.0


@pytest.fixture
def mock_server_service():
    """Create mock server service."""
    return AsyncMock()


@pytest.fixture
def mock_deployment_service():
    """Create mock deployment service."""
    return AsyncMock()


@pytest.fixture
def mock_metrics_service():
    """Create mock metrics service."""
    return AsyncMock()


@pytest.fixture
def mock_activity_service():
    """Create mock activity service."""
    return AsyncMock()


@pytest.fixture
def dashboard_service(
    mock_server_service,
    mock_deployment_service,
    mock_metrics_service,
    mock_activity_service
):
    """Create DashboardService instance with mocks."""
    return DashboardService(
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service
    )


class TestGetSummaryMetrics:
    """Tests for get_summary metrics calculation."""

    @pytest.mark.asyncio
    async def test_get_summary_calculates_avg_metrics(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service
    ):
        """get_summary should calculate average metrics."""
        servers = [MockServer(id="s1"), MockServer(id="s2")]

        async def get_metrics(server_id, period):
            if server_id == "s1":
                return [MockMetric(cpu_percent=40.0, memory_percent=50.0, disk_percent=60.0)]
            return [MockMetric(cpu_percent=60.0, memory_percent=70.0, disk_percent=80.0)]

        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(return_value=[])
        mock_metrics_service.get_server_metrics = AsyncMock(side_effect=get_metrics)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        assert result.avg_cpu_percent == 50.0  # (40 + 60) / 2
        assert result.avg_memory_percent == 60.0  # (50 + 70) / 2
        assert result.avg_disk_percent == 70.0  # (60 + 80) / 2

    @pytest.mark.asyncio
    async def test_get_summary_no_metrics_returns_zero(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service
    ):
        """get_summary should return 0.0 when no metrics available."""
        servers = [MockServer(id="s1")]

        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(return_value=[])
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=None)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        assert result.avg_cpu_percent == 0.0
        assert result.avg_memory_percent == 0.0
        assert result.avg_disk_percent == 0.0

    @pytest.mark.asyncio
    async def test_get_summary_empty_metrics_list_returns_zero(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service
    ):
        """get_summary should return 0.0 when metrics list is empty."""
        servers = [MockServer(id="s1")]

        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(return_value=[])
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=[])
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        assert result.avg_cpu_percent == 0.0

    @pytest.mark.asyncio
    async def test_get_summary_uses_first_metric_from_list(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service
    ):
        """get_summary should use first (most recent) metric from list."""
        servers = [MockServer(id="s1")]
        metrics = [
            MockMetric(cpu_percent=90.0, memory_percent=91.0, disk_percent=92.0),
            MockMetric(cpu_percent=10.0, memory_percent=11.0, disk_percent=12.0),
        ]

        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(return_value=[])
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=metrics)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        # Should use first metric (90, 91, 92), not second
        assert result.avg_cpu_percent == 90.0
        assert result.avg_memory_percent == 91.0
        assert result.avg_disk_percent == 92.0


class TestGetSummaryErrorHandling:
    """Tests for get_summary error handling."""

    @pytest.mark.asyncio
    async def test_get_summary_handles_app_fetch_error(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service
    ):
        """get_summary should handle app fetch errors silently."""
        servers = [MockServer(id="s1"), MockServer(id="s2")]

        async def get_apps(server_id):
            if server_id == "s1":
                raise Exception("Connection failed")
            return [MockApp(status="running")]

        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(side_effect=get_apps)
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=None)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        # Should count apps from s2 only
        assert result.total_apps == 1
        assert result.running_apps == 1

    @pytest.mark.asyncio
    async def test_get_summary_handles_metrics_fetch_error(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service
    ):
        """get_summary should handle metrics fetch errors silently."""
        servers = [MockServer(id="s1"), MockServer(id="s2")]

        async def get_metrics(server_id, period):
            if server_id == "s1":
                raise Exception("Timeout")
            return [MockMetric(cpu_percent=80.0, memory_percent=80.0, disk_percent=80.0)]

        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(return_value=[])
        mock_metrics_service.get_server_metrics = AsyncMock(side_effect=get_metrics)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        # Should use metrics from s2 only
        assert result.avg_cpu_percent == 80.0

    @pytest.mark.asyncio
    async def test_get_summary_general_error_returns_empty(
        self,
        dashboard_service,
        mock_server_service
    ):
        """get_summary should return empty DashboardSummary on error."""
        mock_server_service.get_all_servers = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await dashboard_service.get_summary()

        assert result.total_servers == 0
        assert result.total_apps == 0
        assert result.avg_cpu_percent == 0.0
        assert result.recent_activities == []

    @pytest.mark.asyncio
    async def test_get_summary_logs_error(
        self,
        dashboard_service,
        mock_server_service
    ):
        """get_summary should log errors."""
        mock_server_service.get_all_servers = AsyncMock(
            side_effect=Exception("Database error")
        )

        with patch("services.dashboard_service.logger") as mock_logger:
            await dashboard_service.get_summary()
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Failed to get dashboard summary" in call_args[0][0]


class TestGetSummaryActivities:
    """Tests for get_summary recent activities."""

    @pytest.mark.asyncio
    async def test_get_summary_includes_activities(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service
    ):
        """get_summary should include recent activities."""
        servers = []
        activities = [
            ActivityLog(
                id="act-1",
                activity_type=ActivityType.USER_LOGIN,
                message="User logged in",
                timestamp=datetime.now(UTC).isoformat()
            ),
            ActivityLog(
                id="act-2",
                activity_type=ActivityType.SERVER_ADDED,
                message="Server added",
                timestamp=datetime.now(UTC).isoformat()
            ),
        ]

        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=activities)

        result = await dashboard_service.get_summary()

        assert len(result.recent_activities) == 2
        assert result.recent_activities[0].id == "act-1"
        assert result.recent_activities[1].id == "act-2"

    @pytest.mark.asyncio
    async def test_get_summary_requests_10_activities(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service
    ):
        """get_summary should request 10 recent activities."""
        mock_server_service.get_all_servers = AsyncMock(return_value=[])
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        await dashboard_service.get_summary()

        mock_activity_service.get_recent_activities.assert_called_once_with(limit=10)

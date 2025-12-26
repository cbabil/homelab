"""Tests for metrics MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from tools.metrics_tools import MetricsTools
from models.metrics import DashboardSummary


@pytest.fixture
def mock_metrics_service():
    """Create mock metrics service."""
    svc = MagicMock()
    svc.get_server_metrics = AsyncMock(return_value=[])
    svc.get_container_metrics = AsyncMock(return_value=[])
    svc.collect_server_metrics = AsyncMock()
    return svc


@pytest.fixture
def mock_activity_service():
    """Create mock activity service."""
    svc = MagicMock()
    svc.get_activities = AsyncMock(return_value=[])
    svc.get_activity_count = AsyncMock(return_value=0)
    return svc


@pytest.fixture
def mock_dashboard_service():
    """Create mock dashboard service."""
    svc = MagicMock()
    svc.get_summary = AsyncMock(return_value=DashboardSummary())
    return svc


@pytest.fixture
def metrics_tools(mock_metrics_service, mock_activity_service, mock_dashboard_service):
    """Create metrics tools with mocks."""
    return MetricsTools(
        metrics_service=mock_metrics_service,
        activity_service=mock_activity_service,
        dashboard_service=mock_dashboard_service
    )


class TestGetServerMetrics:
    """Tests for get_server_metrics tool."""

    @pytest.mark.asyncio
    async def test_get_metrics_success(self, metrics_tools, mock_metrics_service):
        """Should return server metrics."""
        mock_metrics_service.get_server_metrics.return_value = [
            MagicMock(cpu_percent=45.0, memory_percent=60.0,
                     model_dump=lambda: {"cpu_percent": 45.0})
        ]

        result = await metrics_tools.get_server_metrics(
            server_id="server-123",
            period="24h"
        )

        assert result["success"] is True
        assert len(result["data"]["metrics"]) == 1


class TestGetActivityLogs:
    """Tests for get_activity_logs tool."""

    @pytest.mark.asyncio
    async def test_get_logs_success(self, metrics_tools, mock_activity_service):
        """Should return activity logs."""
        mock_activity_service.get_activities.return_value = [
            MagicMock(activity_type="user_login", message="Login",
                     model_dump=lambda: {"type": "user_login"})
        ]
        mock_activity_service.get_activity_count.return_value = 1

        result = await metrics_tools.get_activity_logs(limit=50)

        assert result["success"] is True


class TestGetDashboardSummary:
    """Tests for get_dashboard_summary tool."""

    @pytest.mark.asyncio
    async def test_get_summary_success(self, metrics_tools, mock_dashboard_service):
        """Should return dashboard summary."""
        mock_dashboard_service.get_summary.return_value = DashboardSummary(
            total_servers=5,
            online_servers=4,
            running_apps=10
        )

        result = await metrics_tools.get_dashboard_summary()

        assert result["success"] is True
        assert result["data"]["total_servers"] == 5

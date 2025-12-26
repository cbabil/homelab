"""Tests for dashboard service."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from services.dashboard_service import DashboardService
from models.metrics import DashboardSummary


class TestDashboardService:
    """Tests for DashboardService."""

    @pytest.fixture
    def mock_server_service(self):
        """Create mock server service."""
        svc = MagicMock()
        svc.list_servers = AsyncMock(return_value=[])
        return svc

    @pytest.fixture
    def mock_deployment_service(self):
        """Create mock deployment service."""
        svc = MagicMock()
        svc.get_installed_apps = AsyncMock(return_value=[])
        return svc

    @pytest.fixture
    def mock_metrics_service(self):
        """Create mock metrics service."""
        svc = MagicMock()
        svc.get_server_metrics = AsyncMock(return_value=[])
        return svc

    @pytest.fixture
    def mock_activity_service(self):
        """Create mock activity service."""
        svc = MagicMock()
        svc.get_recent_activities = AsyncMock(return_value=[])
        return svc

    @pytest.fixture
    def dashboard_service(self, mock_server_service, mock_deployment_service,
                          mock_metrics_service, mock_activity_service):
        """Create dashboard service with mocks."""
        return DashboardService(
            server_service=mock_server_service,
            deployment_service=mock_deployment_service,
            metrics_service=mock_metrics_service,
            activity_service=mock_activity_service
        )

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_empty(self, dashboard_service):
        """Should return empty summary when no data."""
        result = await dashboard_service.get_summary()

        assert isinstance(result, DashboardSummary)
        assert result.total_servers == 0
        assert result.total_apps == 0

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_with_servers(self, dashboard_service, mock_server_service):
        """Should count servers correctly."""
        mock_server_service.list_servers.return_value = [
            MagicMock(id="s1", status="online"),
            MagicMock(id="s2", status="online"),
            MagicMock(id="s3", status="offline"),
        ]

        result = await dashboard_service.get_summary()

        assert result.total_servers == 3
        assert result.online_servers == 2
        assert result.offline_servers == 1

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_with_apps(self, dashboard_service,
                                                    mock_server_service, mock_deployment_service):
        """Should count apps correctly."""
        mock_server_service.list_servers.return_value = [MagicMock(id="s1")]
        mock_deployment_service.get_installed_apps.return_value = [
            {"status": "running"},
            {"status": "running"},
            {"status": "stopped"},
        ]

        result = await dashboard_service.get_summary()

        assert result.total_apps == 3
        assert result.running_apps == 2
        assert result.stopped_apps == 1

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_with_metrics(self, dashboard_service,
                                                       mock_server_service, mock_metrics_service):
        """Should calculate average metrics."""
        mock_server_service.list_servers.return_value = [
            MagicMock(id="s1"),
            MagicMock(id="s2")
        ]
        mock_metrics_service.get_server_metrics.side_effect = [
            [MagicMock(cpu_percent=30.0, memory_percent=50.0, disk_percent=60.0)],
            [MagicMock(cpu_percent=40.0, memory_percent=60.0, disk_percent=70.0)],
        ]

        result = await dashboard_service.get_summary()

        assert result.avg_cpu_percent == pytest.approx(35.0, rel=0.1)
        assert result.avg_memory_percent == pytest.approx(55.0, rel=0.1)

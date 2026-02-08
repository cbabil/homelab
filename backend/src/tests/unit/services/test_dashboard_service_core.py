"""
Unit tests for services/dashboard_service.py - Core functionality

Tests initialization, server counts, and app counts.
"""

from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

import pytest

from models.server import ServerStatus
from services.dashboard_service import DashboardService


@dataclass
class MockServer:
    """Mock server object for testing."""

    id: str
    status: ServerStatus = ServerStatus.CONNECTED


@dataclass
class MockServerString:
    """Mock server with string status."""

    id: str
    status: str = "connected"


@dataclass
class MockApp:
    """Mock app object for testing."""

    status: str = "running"


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
    mock_activity_service,
):
    """Create DashboardService instance with mocks."""
    return DashboardService(
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    )


class TestDashboardServiceInit:
    """Tests for DashboardService initialization."""

    def test_init_stores_server_service(
        self,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """DashboardService should store server_service reference."""
        service = DashboardService(
            mock_server_service,
            mock_deployment_service,
            mock_metrics_service,
            mock_activity_service,
        )
        assert service.server_service is mock_server_service

    def test_init_stores_deployment_service(
        self,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """DashboardService should store deployment_service reference."""
        service = DashboardService(
            mock_server_service,
            mock_deployment_service,
            mock_metrics_service,
            mock_activity_service,
        )
        assert service.deployment_service is mock_deployment_service

    def test_init_stores_metrics_service(
        self,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """DashboardService should store metrics_service reference."""
        service = DashboardService(
            mock_server_service,
            mock_deployment_service,
            mock_metrics_service,
            mock_activity_service,
        )
        assert service.metrics_service is mock_metrics_service

    def test_init_stores_activity_service(
        self,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """DashboardService should store activity_service reference."""
        service = DashboardService(
            mock_server_service,
            mock_deployment_service,
            mock_metrics_service,
            mock_activity_service,
        )
        assert service.activity_service is mock_activity_service

    def test_init_logs_message(
        self,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """DashboardService should log initialization."""
        with patch("services.dashboard_service.logger") as mock_logger:
            DashboardService(
                mock_server_service,
                mock_deployment_service,
                mock_metrics_service,
                mock_activity_service,
            )
            mock_logger.info.assert_called_once_with("Dashboard service initialized")


class TestGetSummaryServerCounts:
    """Tests for get_summary server counting."""

    @pytest.mark.asyncio
    async def test_get_summary_no_servers(
        self, dashboard_service, mock_server_service, mock_activity_service
    ):
        """get_summary should return zeros when no servers."""
        mock_server_service.get_all_servers = AsyncMock(return_value=[])
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        assert result.total_servers == 0
        assert result.online_servers == 0
        assert result.offline_servers == 0

    @pytest.mark.asyncio
    async def test_get_summary_all_servers_online_enum(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """get_summary should count all servers as online with enum status."""
        servers = [
            MockServer(id="s1", status=ServerStatus.CONNECTED),
            MockServer(id="s2", status=ServerStatus.CONNECTED),
        ]
        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(return_value=[])
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=None)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        assert result.total_servers == 2
        assert result.online_servers == 2
        assert result.offline_servers == 0

    @pytest.mark.asyncio
    async def test_get_summary_all_servers_online_string(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """get_summary should count servers as online with string 'connected'."""
        servers = [
            MockServerString(id="s1", status="connected"),
            MockServerString(id="s2", status="connected"),
        ]
        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(return_value=[])
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=None)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        assert result.total_servers == 2
        assert result.online_servers == 2
        assert result.offline_servers == 0

    @pytest.mark.asyncio
    async def test_get_summary_all_servers_offline(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """get_summary should count all servers as offline when disconnected."""
        servers = [
            MockServer(id="s1", status=ServerStatus.DISCONNECTED),
            MockServer(id="s2", status=ServerStatus.DISCONNECTED),
        ]
        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(return_value=[])
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=None)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        assert result.total_servers == 2
        assert result.online_servers == 0
        assert result.offline_servers == 2

    @pytest.mark.asyncio
    async def test_get_summary_mixed_server_status(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """get_summary should correctly count mixed online/offline servers."""
        servers = [
            MockServer(id="s1", status=ServerStatus.CONNECTED),
            MockServer(id="s2", status=ServerStatus.DISCONNECTED),
            MockServer(id="s3", status=ServerStatus.CONNECTED),
            MockServer(id="s4", status=ServerStatus.DISCONNECTED),
        ]
        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(return_value=[])
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=None)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        assert result.total_servers == 4
        assert result.online_servers == 2
        assert result.offline_servers == 2

    @pytest.mark.asyncio
    async def test_get_summary_server_without_status(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """get_summary should handle servers without status attribute."""

        @dataclass
        class ServerNoStatus:
            id: str

        servers = [ServerNoStatus(id="s1")]
        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(return_value=[])
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=None)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        assert result.total_servers == 1
        assert result.online_servers == 0
        assert result.offline_servers == 1


class TestGetSummaryAppCounts:
    """Tests for get_summary app counting."""

    @pytest.mark.asyncio
    async def test_get_summary_counts_running_apps(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """get_summary should count running apps."""
        servers = [MockServer(id="s1")]
        apps = [MockApp(status="running"), MockApp(status="running")]

        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(return_value=apps)
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=None)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        assert result.total_apps == 2
        assert result.running_apps == 2
        assert result.stopped_apps == 0
        assert result.error_apps == 0

    @pytest.mark.asyncio
    async def test_get_summary_counts_stopped_apps(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """get_summary should count stopped apps."""
        servers = [MockServer(id="s1")]
        apps = [MockApp(status="stopped"), MockApp(status="stopped")]

        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(return_value=apps)
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=None)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        assert result.total_apps == 2
        assert result.running_apps == 0
        assert result.stopped_apps == 2
        assert result.error_apps == 0

    @pytest.mark.asyncio
    async def test_get_summary_counts_error_apps(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """get_summary should count error apps."""
        servers = [MockServer(id="s1")]
        apps = [MockApp(status="error")]

        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(return_value=apps)
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=None)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        assert result.total_apps == 1
        assert result.error_apps == 1

    @pytest.mark.asyncio
    async def test_get_summary_counts_mixed_app_status(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """get_summary should count mixed app statuses."""
        servers = [MockServer(id="s1")]
        apps = [
            MockApp(status="running"),
            MockApp(status="stopped"),
            MockApp(status="error"),
            MockApp(status="unknown"),
        ]

        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(return_value=apps)
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=None)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        assert result.total_apps == 4
        assert result.running_apps == 1
        assert result.stopped_apps == 1
        assert result.error_apps == 1

    @pytest.mark.asyncio
    async def test_get_summary_handles_dict_apps(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """get_summary should handle apps as dictionaries."""
        servers = [MockServer(id="s1")]
        apps = [{"status": "running"}, {"status": "stopped"}]

        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(return_value=apps)
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=None)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        assert result.total_apps == 2
        assert result.running_apps == 1
        assert result.stopped_apps == 1

    @pytest.mark.asyncio
    async def test_get_summary_handles_dict_apps_no_status(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """get_summary should handle dict apps without status key."""
        servers = [MockServer(id="s1")]
        apps = [{"name": "app1"}]

        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(return_value=apps)
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=None)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        assert result.total_apps == 1
        assert result.running_apps == 0

    @pytest.mark.asyncio
    async def test_get_summary_aggregates_apps_from_multiple_servers(
        self,
        dashboard_service,
        mock_server_service,
        mock_deployment_service,
        mock_metrics_service,
        mock_activity_service,
    ):
        """get_summary should aggregate apps from all servers."""
        servers = [MockServer(id="s1"), MockServer(id="s2")]

        async def get_apps(server_id):
            if server_id == "s1":
                return [MockApp(status="running")]
            return [MockApp(status="stopped"), MockApp(status="running")]

        mock_server_service.get_all_servers = AsyncMock(return_value=servers)
        mock_deployment_service.get_installed_apps = AsyncMock(side_effect=get_apps)
        mock_metrics_service.get_server_metrics = AsyncMock(return_value=None)
        mock_activity_service.get_recent_activities = AsyncMock(return_value=[])

        result = await dashboard_service.get_summary()

        assert result.total_apps == 3
        assert result.running_apps == 2
        assert result.stopped_apps == 1

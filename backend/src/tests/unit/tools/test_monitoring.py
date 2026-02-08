"""
Monitoring Tools Unit Tests

Tests for system monitoring tools: get_system_metrics, get_server_metrics,
get_app_metrics, get_dashboard_metrics, get_marketplace_metrics.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tools.monitoring.tools import MonitoringTools


class TestMonitoringToolsInit:
    """Tests for MonitoringTools initialization."""

    def test_initialization(self):
        """Test MonitoringTools is initialized correctly."""
        mock_monitoring = MagicMock()
        mock_metrics = MagicMock()
        mock_dashboard = MagicMock()
        mock_marketplace = MagicMock()

        with patch("tools.monitoring.tools.logger"):
            tools = MonitoringTools(
                mock_monitoring, mock_metrics, mock_dashboard, mock_marketplace
            )

        assert tools.monitoring_service == mock_monitoring
        assert tools.metrics_service == mock_metrics
        assert tools.dashboard_service == mock_dashboard
        assert tools.marketplace_service == mock_marketplace


class TestGetSystemMetrics:
    """Tests for the get_system_metrics tool."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "monitoring": MagicMock(),
            "metrics": MagicMock(),
            "dashboard": MagicMock(),
            "marketplace": MagicMock(),
        }

    @pytest.fixture
    def monitoring_tools(self, mock_services):
        """Create MonitoringTools instance."""
        with patch("tools.monitoring.tools.logger"):
            return MonitoringTools(
                mock_services["monitoring"],
                mock_services["metrics"],
                mock_services["dashboard"],
                mock_services["marketplace"],
            )

    @pytest.mark.asyncio
    async def test_get_system_metrics_success(self, monitoring_tools, mock_services):
        """Test successfully getting system metrics."""
        mock_services["monitoring"].get_current_metrics.return_value = {
            "cpu_percent": 45.2,
            "memory_percent": 62.8,
            "disk_percent": 35.0,
            "network_in": 1024000,
            "network_out": 512000,
        }

        result = await monitoring_tools.get_system_metrics()

        assert result["success"] is True
        assert result["data"]["cpu_percent"] == 45.2
        assert result["data"]["memory_percent"] == 62.8
        assert "System metrics retrieved successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_get_system_metrics_exception(self, monitoring_tools, mock_services):
        """Test get_system_metrics handles exceptions."""
        mock_services["monitoring"].get_current_metrics.side_effect = Exception(
            "System unavailable"
        )

        result = await monitoring_tools.get_system_metrics()

        assert result["success"] is False
        assert result["error"] == "METRICS_ERROR"
        assert "System unavailable" in result["message"]


class TestGetServerMetrics:
    """Tests for the get_server_metrics tool."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "monitoring": MagicMock(),
            "metrics": MagicMock(),
            "dashboard": MagicMock(),
            "marketplace": MagicMock(),
        }

    @pytest.fixture
    def monitoring_tools(self, mock_services):
        """Create MonitoringTools instance."""
        with patch("tools.monitoring.tools.logger"):
            return MonitoringTools(
                mock_services["monitoring"],
                mock_services["metrics"],
                mock_services["dashboard"],
                mock_services["marketplace"],
            )

    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics."""
        metric1 = MagicMock()
        metric1.model_dump.return_value = {
            "timestamp": "2024-01-15T10:00:00Z",
            "cpu_percent": 40.0,
            "memory_percent": 55.0,
        }
        metric2 = MagicMock()
        metric2.model_dump.return_value = {
            "timestamp": "2024-01-15T11:00:00Z",
            "cpu_percent": 42.0,
            "memory_percent": 58.0,
        }
        return [metric1, metric2]

    @pytest.mark.asyncio
    async def test_get_server_metrics_success(
        self, monitoring_tools, mock_services, sample_metrics
    ):
        """Test successfully getting server metrics."""
        mock_services["metrics"].get_server_metrics = AsyncMock(
            return_value=sample_metrics
        )

        result = await monitoring_tools.get_server_metrics("server-123")

        assert result["success"] is True
        assert result["data"]["server_id"] == "server-123"
        assert result["data"]["period"] == "24h"
        assert result["data"]["count"] == 2
        assert len(result["data"]["metrics"]) == 2

    @pytest.mark.asyncio
    async def test_get_server_metrics_custom_period(
        self, monitoring_tools, mock_services, sample_metrics
    ):
        """Test getting server metrics with custom period."""
        mock_services["metrics"].get_server_metrics = AsyncMock(
            return_value=sample_metrics
        )

        result = await monitoring_tools.get_server_metrics("server-123", period="7d")

        assert result["success"] is True
        assert result["data"]["period"] == "7d"
        mock_services["metrics"].get_server_metrics.assert_called_once_with(
            "server-123", "7d"
        )

    @pytest.mark.asyncio
    async def test_get_server_metrics_empty(self, monitoring_tools, mock_services):
        """Test getting server metrics when no metrics exist."""
        mock_services["metrics"].get_server_metrics = AsyncMock(return_value=[])

        result = await monitoring_tools.get_server_metrics("server-123")

        assert result["success"] is True
        assert result["data"]["count"] == 0
        assert result["data"]["metrics"] == []

    @pytest.mark.asyncio
    async def test_get_server_metrics_exception(self, monitoring_tools, mock_services):
        """Test get_server_metrics handles exceptions."""
        mock_services["metrics"].get_server_metrics = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await monitoring_tools.get_server_metrics("server-123")

        assert result["success"] is False
        assert result["error"] == "GET_METRICS_ERROR"
        assert "Database error" in result["message"]


class TestGetAppMetrics:
    """Tests for the get_app_metrics tool."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "monitoring": MagicMock(),
            "metrics": MagicMock(),
            "dashboard": MagicMock(),
            "marketplace": MagicMock(),
        }

    @pytest.fixture
    def monitoring_tools(self, mock_services):
        """Create MonitoringTools instance."""
        with patch("tools.monitoring.tools.logger"):
            return MonitoringTools(
                mock_services["monitoring"],
                mock_services["metrics"],
                mock_services["dashboard"],
                mock_services["marketplace"],
            )

    @pytest.fixture
    def sample_container_metrics(self):
        """Create sample container metrics."""
        metric = MagicMock()
        metric.model_dump.return_value = {
            "timestamp": "2024-01-15T10:00:00Z",
            "container_name": "nginx",
            "cpu_percent": 5.0,
            "memory_mb": 128,
        }
        return [metric]

    @pytest.mark.asyncio
    async def test_get_app_metrics_success(
        self, monitoring_tools, mock_services, sample_container_metrics
    ):
        """Test successfully getting app metrics."""
        mock_services["metrics"].get_container_metrics = AsyncMock(
            return_value=sample_container_metrics
        )

        result = await monitoring_tools.get_app_metrics("server-123", "nginx")

        assert result["success"] is True
        assert result["data"]["server_id"] == "server-123"
        assert result["data"]["app_id"] == "nginx"
        assert result["data"]["period"] == "24h"
        assert result["data"]["count"] == 1

    @pytest.mark.asyncio
    async def test_get_app_metrics_without_app_id(
        self, monitoring_tools, mock_services, sample_container_metrics
    ):
        """Test getting metrics without app_id (all containers)."""
        mock_services["metrics"].get_container_metrics = AsyncMock(
            return_value=sample_container_metrics
        )

        result = await monitoring_tools.get_app_metrics("server-123")

        assert result["success"] is True
        assert result["data"]["app_id"] is None
        mock_services["metrics"].get_container_metrics.assert_called_once_with(
            server_id="server-123", container_name=None, period="24h"
        )

    @pytest.mark.asyncio
    async def test_get_app_metrics_custom_period(
        self, monitoring_tools, mock_services, sample_container_metrics
    ):
        """Test getting app metrics with custom period."""
        mock_services["metrics"].get_container_metrics = AsyncMock(
            return_value=sample_container_metrics
        )

        result = await monitoring_tools.get_app_metrics(
            "server-123", "redis", period="1h"
        )

        assert result["success"] is True
        assert result["data"]["period"] == "1h"

    @pytest.mark.asyncio
    async def test_get_app_metrics_exception(self, monitoring_tools, mock_services):
        """Test get_app_metrics handles exceptions."""
        mock_services["metrics"].get_container_metrics = AsyncMock(
            side_effect=Exception("Container not found")
        )

        result = await monitoring_tools.get_app_metrics("server-123", "nginx")

        assert result["success"] is False
        assert result["error"] == "GET_APP_METRICS_ERROR"
        assert "Container not found" in result["message"]


class TestGetDashboardMetrics:
    """Tests for the get_dashboard_metrics tool."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "monitoring": MagicMock(),
            "metrics": MagicMock(),
            "dashboard": MagicMock(),
            "marketplace": MagicMock(),
        }

    @pytest.fixture
    def monitoring_tools(self, mock_services):
        """Create MonitoringTools instance."""
        with patch("tools.monitoring.tools.logger"):
            return MonitoringTools(
                mock_services["monitoring"],
                mock_services["metrics"],
                mock_services["dashboard"],
                mock_services["marketplace"],
            )

    @pytest.fixture
    def sample_dashboard_summary(self):
        """Create sample dashboard summary."""
        activity = MagicMock()
        activity.model_dump.return_value = {
            "type": "server_connected",
            "server_id": "server-123",
            "timestamp": "2024-01-15T10:00:00Z",
        }

        summary = MagicMock()
        summary.total_servers = 5
        summary.online_servers = 4
        summary.offline_servers = 1
        summary.total_apps = 20
        summary.running_apps = 18
        summary.stopped_apps = 1
        summary.error_apps = 1
        summary.avg_cpu_percent = 42.5
        summary.avg_memory_percent = 65.3
        summary.avg_disk_percent = 48.0
        summary.recent_activities = [activity]
        return summary

    @pytest.mark.asyncio
    async def test_get_dashboard_metrics_success(
        self, monitoring_tools, mock_services, sample_dashboard_summary
    ):
        """Test successfully getting dashboard metrics."""
        mock_services["dashboard"].get_summary = AsyncMock(
            return_value=sample_dashboard_summary
        )

        result = await monitoring_tools.get_dashboard_metrics()

        assert result["success"] is True
        assert result["data"]["total_servers"] == 5
        assert result["data"]["online_servers"] == 4
        assert result["data"]["offline_servers"] == 1
        assert result["data"]["total_apps"] == 20
        assert result["data"]["running_apps"] == 18
        assert result["data"]["stopped_apps"] == 1
        assert result["data"]["error_apps"] == 1
        assert result["data"]["avg_cpu_percent"] == 42.5
        assert result["data"]["avg_memory_percent"] == 65.3
        assert result["data"]["avg_disk_percent"] == 48.0
        assert len(result["data"]["recent_activities"]) == 1

    @pytest.mark.asyncio
    async def test_get_dashboard_metrics_exception(
        self, monitoring_tools, mock_services
    ):
        """Test get_dashboard_metrics handles exceptions."""
        mock_services["dashboard"].get_summary = AsyncMock(
            side_effect=Exception("Service unavailable")
        )

        result = await monitoring_tools.get_dashboard_metrics()

        assert result["success"] is False
        assert result["error"] == "GET_DASHBOARD_METRICS_ERROR"
        assert "Service unavailable" in result["message"]


class TestGetMarketplaceMetrics:
    """Tests for the get_marketplace_metrics tool."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "monitoring": MagicMock(),
            "metrics": MagicMock(),
            "dashboard": MagicMock(),
            "marketplace": MagicMock(),
        }

    @pytest.fixture
    def monitoring_tools(self, mock_services):
        """Create MonitoringTools instance."""
        with patch("tools.monitoring.tools.logger"):
            return MonitoringTools(
                mock_services["monitoring"],
                mock_services["metrics"],
                mock_services["dashboard"],
                mock_services["marketplace"],
            )

    @pytest.fixture
    def sample_repos(self):
        """Create sample repos."""
        repo1 = MagicMock()
        repo1.enabled = True
        repo1.last_synced = "2024-01-15T10:00:00Z"

        repo2 = MagicMock()
        repo2.enabled = False
        repo2.last_synced = None
        return [repo1, repo2]

    @pytest.fixture
    def sample_apps(self):
        """Create sample apps."""
        app1 = MagicMock()
        app1.rating_count = 10
        app1.avg_rating = 4.5
        app1.featured = True

        app2 = MagicMock()
        app2.rating_count = 5
        app2.avg_rating = 4.0
        app2.featured = False

        app3 = MagicMock()
        app3.rating_count = 0
        app3.avg_rating = 0.0
        app3.featured = False
        return [app1, app2, app3]

    @pytest.mark.asyncio
    async def test_get_marketplace_metrics_success(
        self, monitoring_tools, mock_services, sample_repos, sample_apps
    ):
        """Test successfully getting marketplace metrics."""
        mock_services["marketplace"].get_repos = AsyncMock(return_value=sample_repos)
        mock_services["marketplace"].search_apps = AsyncMock(return_value=sample_apps)
        mock_services["marketplace"].get_categories = AsyncMock(
            return_value=["database", "web", "monitoring"]
        )

        result = await monitoring_tools.get_marketplace_metrics()

        assert result["success"] is True
        assert result["data"]["total_repos"] == 2
        assert result["data"]["enabled_repos"] == 1
        assert result["data"]["synced_repos"] == 1
        assert result["data"]["total_apps"] == 3
        assert result["data"]["featured_apps"] == 1
        assert result["data"]["category_count"] == 3
        assert result["data"]["total_ratings"] == 15
        assert result["data"]["rated_apps"] == 2
        # Weighted average: (4.5*10 + 4.0*5) / 15 = 4.33
        assert result["data"]["avg_rating"] == 4.33

    @pytest.mark.asyncio
    async def test_get_marketplace_metrics_no_ratings(
        self, monitoring_tools, mock_services, sample_repos
    ):
        """Test marketplace metrics when no apps have ratings."""
        app_no_ratings = MagicMock()
        app_no_ratings.rating_count = 0
        app_no_ratings.avg_rating = 0.0
        app_no_ratings.featured = False

        mock_services["marketplace"].get_repos = AsyncMock(return_value=sample_repos)
        mock_services["marketplace"].search_apps = AsyncMock(
            return_value=[app_no_ratings]
        )
        mock_services["marketplace"].get_categories = AsyncMock(return_value=[])

        result = await monitoring_tools.get_marketplace_metrics()

        assert result["success"] is True
        assert result["data"]["total_ratings"] == 0
        assert result["data"]["avg_rating"] == 0.0
        assert result["data"]["rated_apps"] == 0

    @pytest.mark.asyncio
    async def test_get_marketplace_metrics_empty_marketplace(
        self, monitoring_tools, mock_services
    ):
        """Test marketplace metrics when marketplace is empty."""
        mock_services["marketplace"].get_repos = AsyncMock(return_value=[])
        mock_services["marketplace"].search_apps = AsyncMock(return_value=[])
        mock_services["marketplace"].get_categories = AsyncMock(return_value=[])

        result = await monitoring_tools.get_marketplace_metrics()

        assert result["success"] is True
        assert result["data"]["total_repos"] == 0
        assert result["data"]["total_apps"] == 0
        assert result["data"]["category_count"] == 0

    @pytest.mark.asyncio
    async def test_get_marketplace_metrics_exception(
        self, monitoring_tools, mock_services
    ):
        """Test get_marketplace_metrics handles exceptions."""
        mock_services["marketplace"].get_repos = AsyncMock(
            side_effect=Exception("Marketplace offline")
        )

        result = await monitoring_tools.get_marketplace_metrics()

        assert result["success"] is False
        assert result["error"] == "GET_MARKETPLACE_METRICS_ERROR"
        assert "Marketplace offline" in result["message"]

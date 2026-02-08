"""
Metrics Model Unit Tests

Tests for MetricType, ActivityType, ServerMetrics, ContainerMetrics,
ActivityLog, and DashboardSummary models.
"""

import pytest
from pydantic import ValidationError

from models.metrics import (
    ActivityLog,
    ActivityType,
    ContainerMetrics,
    DashboardSummary,
    MetricType,
    ServerMetrics,
)


class TestMetricType:
    """Tests for MetricType enum."""

    def test_cpu_value(self):
        """Test CPU metric type value."""
        assert MetricType.CPU.value == "cpu"

    def test_memory_value(self):
        """Test MEMORY metric type value."""
        assert MetricType.MEMORY.value == "memory"

    def test_disk_value(self):
        """Test DISK metric type value."""
        assert MetricType.DISK.value == "disk"

    def test_network_value(self):
        """Test NETWORK metric type value."""
        assert MetricType.NETWORK.value == "network"

    def test_all_values(self):
        """Test all metric types are strings."""
        for metric_type in MetricType:
            assert isinstance(metric_type.value, str)


class TestActivityType:
    """Tests for ActivityType enum."""

    def test_user_login_value(self):
        """Test USER_LOGIN activity type."""
        assert ActivityType.USER_LOGIN.value == "user_login"

    def test_user_logout_value(self):
        """Test USER_LOGOUT activity type."""
        assert ActivityType.USER_LOGOUT.value == "user_logout"

    def test_server_added_value(self):
        """Test SERVER_ADDED activity type."""
        assert ActivityType.SERVER_ADDED.value == "server_added"

    def test_app_installed_value(self):
        """Test APP_INSTALLED activity type."""
        assert ActivityType.APP_INSTALLED.value == "app_installed"

    def test_system_startup_value(self):
        """Test SYSTEM_STARTUP activity type."""
        assert ActivityType.SYSTEM_STARTUP.value == "system_startup"

    def test_all_activity_types_are_strings(self):
        """Test all activity types are string enums."""
        for activity_type in ActivityType:
            assert isinstance(activity_type.value, str)
            assert isinstance(activity_type, str)


class TestServerMetrics:
    """Tests for ServerMetrics model."""

    @pytest.fixture
    def valid_server_metrics_data(self):
        """Create valid server metrics data."""
        return {
            "id": "metric-123",
            "server_id": "server-456",
            "cpu_percent": 45.5,
            "memory_percent": 60.2,
            "memory_used_mb": 4096,
            "memory_total_mb": 8192,
            "disk_percent": 75.0,
            "disk_used_gb": 150,
            "disk_total_gb": 200,
            "timestamp": "2024-01-15T10:30:00Z",
        }

    def test_create_valid_server_metrics(self, valid_server_metrics_data):
        """Test creating valid server metrics."""
        metrics = ServerMetrics(**valid_server_metrics_data)

        assert metrics.id == "metric-123"
        assert metrics.server_id == "server-456"
        assert metrics.cpu_percent == 45.5
        assert metrics.memory_percent == 60.2
        assert metrics.memory_used_mb == 4096
        assert metrics.memory_total_mb == 8192
        assert metrics.disk_percent == 75.0
        assert metrics.disk_used_gb == 150
        assert metrics.disk_total_gb == 200
        assert metrics.timestamp == "2024-01-15T10:30:00Z"

    def test_server_metrics_default_network_values(self, valid_server_metrics_data):
        """Test server metrics have default network values."""
        metrics = ServerMetrics(**valid_server_metrics_data)

        assert metrics.network_rx_bytes == 0
        assert metrics.network_tx_bytes == 0

    def test_server_metrics_with_network_values(self, valid_server_metrics_data):
        """Test server metrics with network values."""
        valid_server_metrics_data["network_rx_bytes"] = 1024000
        valid_server_metrics_data["network_tx_bytes"] = 512000

        metrics = ServerMetrics(**valid_server_metrics_data)

        assert metrics.network_rx_bytes == 1024000
        assert metrics.network_tx_bytes == 512000

    def test_server_metrics_optional_load_averages(self, valid_server_metrics_data):
        """Test server metrics with optional load averages."""
        valid_server_metrics_data["load_average_1m"] = 1.5
        valid_server_metrics_data["load_average_5m"] = 2.0
        valid_server_metrics_data["load_average_15m"] = 1.8

        metrics = ServerMetrics(**valid_server_metrics_data)

        assert metrics.load_average_1m == 1.5
        assert metrics.load_average_5m == 2.0
        assert metrics.load_average_15m == 1.8

    def test_server_metrics_optional_uptime(self, valid_server_metrics_data):
        """Test server metrics with optional uptime."""
        valid_server_metrics_data["uptime_seconds"] = 86400

        metrics = ServerMetrics(**valid_server_metrics_data)

        assert metrics.uptime_seconds == 86400

    def test_server_metrics_missing_required_field(self, valid_server_metrics_data):
        """Test server metrics with missing required field."""
        del valid_server_metrics_data["cpu_percent"]

        with pytest.raises(ValidationError):
            ServerMetrics(**valid_server_metrics_data)


class TestContainerMetrics:
    """Tests for ContainerMetrics model."""

    @pytest.fixture
    def valid_container_metrics_data(self):
        """Create valid container metrics data."""
        return {
            "id": "metric-789",
            "server_id": "server-456",
            "container_id": "abc123def456",
            "container_name": "nginx-web",
            "cpu_percent": 25.0,
            "memory_usage_mb": 512,
            "memory_limit_mb": 1024,
            "status": "running",
            "timestamp": "2024-01-15T10:30:00Z",
        }

    def test_create_valid_container_metrics(self, valid_container_metrics_data):
        """Test creating valid container metrics."""
        metrics = ContainerMetrics(**valid_container_metrics_data)

        assert metrics.id == "metric-789"
        assert metrics.server_id == "server-456"
        assert metrics.container_id == "abc123def456"
        assert metrics.container_name == "nginx-web"
        assert metrics.cpu_percent == 25.0
        assert metrics.memory_usage_mb == 512
        assert metrics.memory_limit_mb == 1024
        assert metrics.status == "running"

    def test_container_metrics_default_network_values(
        self, valid_container_metrics_data
    ):
        """Test container metrics have default network values."""
        metrics = ContainerMetrics(**valid_container_metrics_data)

        assert metrics.network_rx_bytes == 0
        assert metrics.network_tx_bytes == 0

    def test_container_metrics_with_network_values(self, valid_container_metrics_data):
        """Test container metrics with network values."""
        valid_container_metrics_data["network_rx_bytes"] = 2048000
        valid_container_metrics_data["network_tx_bytes"] = 1024000

        metrics = ContainerMetrics(**valid_container_metrics_data)

        assert metrics.network_rx_bytes == 2048000
        assert metrics.network_tx_bytes == 1024000

    def test_container_metrics_missing_required_field(
        self, valid_container_metrics_data
    ):
        """Test container metrics with missing required field."""
        del valid_container_metrics_data["container_name"]

        with pytest.raises(ValidationError):
            ContainerMetrics(**valid_container_metrics_data)


class TestActivityLog:
    """Tests for ActivityLog model."""

    @pytest.fixture
    def valid_activity_log_data(self):
        """Create valid activity log data."""
        return {
            "id": "log-123",
            "activity_type": ActivityType.USER_LOGIN,
            "message": "User logged in successfully",
            "timestamp": "2024-01-15T10:30:00Z",
        }

    def test_create_valid_activity_log(self, valid_activity_log_data):
        """Test creating valid activity log."""
        log = ActivityLog(**valid_activity_log_data)

        assert log.id == "log-123"
        assert log.activity_type == ActivityType.USER_LOGIN
        assert log.message == "User logged in successfully"
        assert log.timestamp == "2024-01-15T10:30:00Z"

    def test_activity_log_optional_fields_none(self, valid_activity_log_data):
        """Test activity log optional fields default to None."""
        log = ActivityLog(**valid_activity_log_data)

        assert log.user_id is None
        assert log.server_id is None
        assert log.app_id is None

    def test_activity_log_with_optional_fields(self, valid_activity_log_data):
        """Test activity log with optional fields."""
        valid_activity_log_data["user_id"] = "user-456"
        valid_activity_log_data["server_id"] = "server-789"
        valid_activity_log_data["app_id"] = "app-abc"

        log = ActivityLog(**valid_activity_log_data)

        assert log.user_id == "user-456"
        assert log.server_id == "server-789"
        assert log.app_id == "app-abc"

    def test_activity_log_default_details(self, valid_activity_log_data):
        """Test activity log has empty default details."""
        log = ActivityLog(**valid_activity_log_data)

        assert log.details == {}

    def test_activity_log_with_details(self, valid_activity_log_data):
        """Test activity log with details."""
        valid_activity_log_data["details"] = {
            "ip_address": "192.168.1.100",
            "browser": "Chrome",
        }

        log = ActivityLog(**valid_activity_log_data)

        assert log.details["ip_address"] == "192.168.1.100"
        assert log.details["browser"] == "Chrome"

    def test_activity_log_with_string_activity_type(self, valid_activity_log_data):
        """Test activity log with string activity type."""
        valid_activity_log_data["activity_type"] = "user_login"

        log = ActivityLog(**valid_activity_log_data)

        assert log.activity_type == ActivityType.USER_LOGIN


class TestDashboardSummary:
    """Tests for DashboardSummary model."""

    def test_create_empty_dashboard_summary(self):
        """Test creating dashboard summary with defaults."""
        summary = DashboardSummary()

        assert summary.total_servers == 0
        assert summary.online_servers == 0
        assert summary.offline_servers == 0
        assert summary.total_apps == 0
        assert summary.running_apps == 0
        assert summary.stopped_apps == 0
        assert summary.error_apps == 0
        assert summary.avg_cpu_percent == 0.0
        assert summary.avg_memory_percent == 0.0
        assert summary.avg_disk_percent == 0.0
        assert summary.recent_activities == []

    def test_create_dashboard_summary_with_values(self):
        """Test creating dashboard summary with values."""
        summary = DashboardSummary(
            total_servers=5,
            online_servers=4,
            offline_servers=1,
            total_apps=10,
            running_apps=8,
            stopped_apps=1,
            error_apps=1,
            avg_cpu_percent=35.5,
            avg_memory_percent=55.2,
            avg_disk_percent=70.0,
        )

        assert summary.total_servers == 5
        assert summary.online_servers == 4
        assert summary.offline_servers == 1
        assert summary.total_apps == 10
        assert summary.running_apps == 8
        assert summary.stopped_apps == 1
        assert summary.error_apps == 1
        assert summary.avg_cpu_percent == 35.5
        assert summary.avg_memory_percent == 55.2
        assert summary.avg_disk_percent == 70.0

    def test_dashboard_summary_with_activities(self):
        """Test dashboard summary with recent activities."""
        activity = ActivityLog(
            id="log-1",
            activity_type=ActivityType.SERVER_ADDED,
            message="Server added",
            timestamp="2024-01-15T10:30:00Z",
        )

        summary = DashboardSummary(recent_activities=[activity])

        assert len(summary.recent_activities) == 1
        assert summary.recent_activities[0].id == "log-1"

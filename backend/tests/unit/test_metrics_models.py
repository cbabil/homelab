"""Tests for metrics and activity log models."""
import pytest
from models.metrics import (
    MetricType,
    ActivityType,
    ServerMetrics,
    ContainerMetrics,
    ActivityLog,
    DashboardSummary
)


class TestMetricsModels:
    """Tests for metrics data models."""

    def test_metric_type_enum(self):
        """Should have correct metric types."""
        assert MetricType.CPU.value == "cpu"
        assert MetricType.MEMORY.value == "memory"
        assert MetricType.DISK.value == "disk"
        assert MetricType.NETWORK.value == "network"

    def test_activity_type_enum(self):
        """Should have correct activity types."""
        assert ActivityType.USER_LOGIN.value == "user_login"
        assert ActivityType.USER_LOGOUT.value == "user_logout"
        assert ActivityType.SERVER_ADDED.value == "server_added"
        assert ActivityType.APP_INSTALLED.value == "app_installed"
        assert ActivityType.APP_STARTED.value == "app_started"
        assert ActivityType.PREPARATION_COMPLETE.value == "preparation_complete"

    def test_server_metrics_model(self):
        """Should create valid server metrics."""
        metrics = ServerMetrics(
            id="metric-123",
            server_id="server-456",
            cpu_percent=45.5,
            memory_percent=62.3,
            memory_used_mb=4096,
            memory_total_mb=8192,
            disk_percent=78.0,
            disk_used_gb=156,
            disk_total_gb=200,
            network_rx_bytes=1024000,
            network_tx_bytes=512000,
            timestamp="2025-01-01T00:00:00Z"
        )
        assert metrics.cpu_percent == 45.5
        assert metrics.memory_percent == 62.3

    def test_container_metrics_model(self):
        """Should create valid container metrics."""
        metrics = ContainerMetrics(
            id="cmetric-123",
            server_id="server-456",
            container_id="abc123",
            container_name="portainer",
            cpu_percent=12.5,
            memory_usage_mb=256,
            memory_limit_mb=512,
            status="running",
            timestamp="2025-01-01T00:00:00Z"
        )
        assert metrics.container_name == "portainer"
        assert metrics.status == "running"

    def test_activity_log_model(self):
        """Should create valid activity log."""
        log = ActivityLog(
            id="log-123",
            activity_type=ActivityType.USER_LOGIN,
            user_id="user-456",
            server_id=None,
            app_id=None,
            message="User admin logged in",
            details={"ip": "192.168.1.1"},
            timestamp="2025-01-01T00:00:00Z"
        )
        assert log.activity_type == ActivityType.USER_LOGIN
        assert log.user_id == "user-456"

    def test_dashboard_summary_model(self):
        """Should create valid dashboard summary."""
        summary = DashboardSummary(
            total_servers=5,
            online_servers=4,
            offline_servers=1,
            total_apps=12,
            running_apps=10,
            stopped_apps=2,
            avg_cpu_percent=35.0,
            avg_memory_percent=55.0,
            recent_activities=[]
        )
        assert summary.total_servers == 5
        assert summary.running_apps == 10

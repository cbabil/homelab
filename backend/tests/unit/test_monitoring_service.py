"""
Unit tests for services/monitoring_service.py

Tests for metrics collection and log management.
"""

from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import services.monitoring_service as monitor_module
from services.monitoring_service import MonitoringService


@pytest.fixture
def monitoring_service():
    """Create MonitoringService for testing."""
    with patch.object(monitor_module, "logger"):
        return MonitoringService()


class TestMonitoringServiceInit:
    """Tests for MonitoringService initialization."""

    def test_init_creates_metrics_cache(self):
        """Should initialize with metrics cache."""
        with patch.object(monitor_module, "logger"):
            service = MonitoringService()

            assert isinstance(service.metrics_cache, dict)

    def test_init_logs_initialization(self):
        """Should log initialization."""
        with patch.object(monitor_module, "logger") as mock_logger:
            MonitoringService()

            mock_logger.info.assert_any_call("Monitoring service initialized")

    def test_init_populates_metrics(self):
        """Should populate metrics with sample data."""
        with patch.object(monitor_module, "logger"):
            service = MonitoringService()

            assert "cpu" in service.metrics_cache
            assert "memory" in service.metrics_cache
            assert "disk" in service.metrics_cache
            assert "network" in service.metrics_cache


class TestInitializeSampleData:
    """Tests for _initialize_sample_data method."""

    def test_initialize_sample_data_calls_metrics(self, monitoring_service):
        """Should call _initialize_metrics."""
        with patch.object(monitoring_service, "_initialize_metrics") as mock_metrics:
            monitoring_service._initialize_sample_data()

            mock_metrics.assert_called_once()


class TestInitializeMetrics:
    """Tests for _initialize_metrics method."""

    def test_initialize_metrics_sets_cpu_data(self, monitoring_service):
        """Should set CPU metrics."""
        monitoring_service.metrics_cache = {}
        monitoring_service._initialize_metrics()

        cpu = monitoring_service.metrics_cache["cpu"]
        assert "usage" in cpu
        assert "cores" in cpu
        assert "temperature" in cpu

    def test_initialize_metrics_sets_memory_data(self, monitoring_service):
        """Should set memory metrics."""
        monitoring_service.metrics_cache = {}
        monitoring_service._initialize_metrics()

        memory = monitoring_service.metrics_cache["memory"]
        assert "used" in memory
        assert "total" in memory
        assert "percentage" in memory

    def test_initialize_metrics_sets_disk_data(self, monitoring_service):
        """Should set disk metrics."""
        monitoring_service.metrics_cache = {}
        monitoring_service._initialize_metrics()

        disk = monitoring_service.metrics_cache["disk"]
        assert "used" in disk
        assert "total" in disk
        assert "percentage" in disk

    def test_initialize_metrics_sets_network_data(self, monitoring_service):
        """Should set network metrics."""
        monitoring_service.metrics_cache = {}
        monitoring_service._initialize_metrics()

        network = monitoring_service.metrics_cache["network"]
        assert "inbound" in network
        assert "outbound" in network
        assert "connections" in network

    def test_initialize_metrics_sets_additional_data(self, monitoring_service):
        """Should set uptime, processes, and timestamp."""
        monitoring_service.metrics_cache = {}
        monitoring_service._initialize_metrics()

        assert "uptime" in monitoring_service.metrics_cache
        assert "processes" in monitoring_service.metrics_cache
        assert "timestamp" in monitoring_service.metrics_cache


class TestInitializeLogs:
    """Tests for _initialize_logs method."""

    @pytest.mark.asyncio
    async def test_initialize_logs_creates_sample_logs(self, monitoring_service):
        """Should create sample log entries."""
        mock_log_service = AsyncMock()

        with patch.object(monitor_module, "log_service", mock_log_service):
            await monitoring_service._initialize_logs()

            # Should create 12 sample logs
            assert mock_log_service.create_log_entry.call_count == 12

    @pytest.mark.asyncio
    async def test_initialize_logs_handles_exception(self, monitoring_service):
        """Should handle exceptions gracefully."""
        mock_log_service = AsyncMock()
        mock_log_service.create_log_entry.side_effect = RuntimeError("DB error")

        with (
            patch.object(monitor_module, "log_service", mock_log_service),
            patch.object(monitor_module, "logger") as mock_logger,
        ):
            # Should not raise
            await monitoring_service._initialize_logs()

            mock_logger.warning.assert_called_once()


class TestGetCurrentMetrics:
    """Tests for get_current_metrics method."""

    def test_get_current_metrics_returns_dict(self, monitoring_service):
        """Should return metrics dictionary."""
        result = monitoring_service.get_current_metrics()

        assert isinstance(result, dict)

    def test_get_current_metrics_updates_timestamp(self, monitoring_service):
        """Should update timestamp."""
        before = datetime.now(UTC)
        result = monitoring_service.get_current_metrics()
        after = datetime.now(UTC)

        timestamp = datetime.fromisoformat(result["timestamp"])
        assert before <= timestamp <= after

    def test_get_current_metrics_returns_all_fields(self, monitoring_service):
        """Should return all metric fields."""
        result = monitoring_service.get_current_metrics()

        assert "cpu" in result
        assert "memory" in result
        assert "disk" in result
        assert "network" in result
        assert "uptime" in result
        assert "processes" in result


class TestGetFilteredLogs:
    """Tests for get_filtered_logs method."""

    @pytest.mark.asyncio
    async def test_get_filtered_logs_without_filters(self, monitoring_service):
        """Should retrieve logs without filters."""
        mock_log_entry = MagicMock()
        mock_log_entry.id = "log-1"
        mock_log_entry.timestamp = datetime.now(UTC)
        mock_log_entry.level = "INFO"
        mock_log_entry.source = "test"
        mock_log_entry.message = "Test message"
        mock_log_entry.tags = ["test"]

        mock_log_service = AsyncMock()
        mock_log_service.get_logs.return_value = [mock_log_entry]

        with patch.object(monitor_module, "log_service", mock_log_service):
            result = await monitoring_service.get_filtered_logs()

            mock_log_service.get_logs.assert_called_once_with(None)
            assert len(result) == 1
            assert result[0]["id"] == "log-1"

    @pytest.mark.asyncio
    async def test_get_filtered_logs_with_level_filter(self, monitoring_service):
        """Should apply level filter."""
        mock_log_service = AsyncMock()
        mock_log_service.get_logs.return_value = []

        with patch.object(monitor_module, "log_service", mock_log_service):
            await monitoring_service.get_filtered_logs(filters={"level": "ERROR"})

            call_args = mock_log_service.get_logs.call_args[0][0]
            assert call_args.level == "ERROR"

    @pytest.mark.asyncio
    async def test_get_filtered_logs_with_source_filter(self, monitoring_service):
        """Should apply source filter."""
        mock_log_service = AsyncMock()
        mock_log_service.get_logs.return_value = []

        with patch.object(monitor_module, "log_service", mock_log_service):
            await monitoring_service.get_filtered_logs(filters={"source": "docker"})

            call_args = mock_log_service.get_logs.call_args[0][0]
            assert call_args.source == "docker"

    @pytest.mark.asyncio
    async def test_get_filtered_logs_with_limit(self, monitoring_service):
        """Should apply limit filter."""
        mock_log_service = AsyncMock()
        mock_log_service.get_logs.return_value = []

        with patch.object(monitor_module, "log_service", mock_log_service):
            await monitoring_service.get_filtered_logs(filters={"limit": 50})

            call_args = mock_log_service.get_logs.call_args[0][0]
            assert call_args.limit == 50

    @pytest.mark.asyncio
    async def test_get_filtered_logs_caps_limit_at_1000(self, monitoring_service):
        """Should cap limit at 1000."""
        mock_log_service = AsyncMock()
        mock_log_service.get_logs.return_value = []

        with patch.object(monitor_module, "log_service", mock_log_service):
            await monitoring_service.get_filtered_logs(filters={"limit": 5000})

            call_args = mock_log_service.get_logs.call_args[0][0]
            assert call_args.limit == 1000

    @pytest.mark.asyncio
    async def test_get_filtered_logs_initializes_if_empty(self, monitoring_service):
        """Should initialize sample logs if none exist."""
        mock_log_service = AsyncMock()
        mock_log_service.get_logs.side_effect = [[], []]  # Empty first, then still empty

        with (
            patch.object(monitor_module, "log_service", mock_log_service),
            patch.object(
                monitoring_service, "_initialize_logs", new_callable=AsyncMock
            ) as mock_init,
        ):
            await monitoring_service.get_filtered_logs()

            mock_init.assert_called_once()
            assert mock_log_service.get_logs.call_count == 2

    @pytest.mark.asyncio
    async def test_get_filtered_logs_converts_to_dict(self, monitoring_service):
        """Should convert LogEntry models to dicts."""
        mock_log_entry = MagicMock()
        mock_log_entry.id = "log-1"
        mock_log_entry.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_log_entry.level = "INFO"
        mock_log_entry.source = "test"
        mock_log_entry.message = "Test message"
        mock_log_entry.tags = ["tag1", "tag2"]

        mock_log_service = AsyncMock()
        mock_log_service.get_logs.return_value = [mock_log_entry]

        with patch.object(monitor_module, "log_service", mock_log_service):
            result = await monitoring_service.get_filtered_logs()

            assert len(result) == 1
            log_dict = result[0]
            assert log_dict["id"] == "log-1"
            assert log_dict["level"] == "INFO"
            assert log_dict["source"] == "test"
            assert log_dict["message"] == "Test message"
            assert log_dict["tags"] == ["tag1", "tag2"]
            assert "timestamp" in log_dict

    @pytest.mark.asyncio
    async def test_get_filtered_logs_handles_exception(self, monitoring_service):
        """Should return empty list on exception."""
        mock_log_service = AsyncMock()
        mock_log_service.get_logs.side_effect = RuntimeError("DB error")

        with (
            patch.object(monitor_module, "log_service", mock_log_service),
            patch.object(monitor_module, "logger") as mock_logger,
        ):
            result = await monitoring_service.get_filtered_logs()

            assert result == []
            mock_logger.error.assert_called_once()

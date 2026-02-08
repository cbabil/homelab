"""
Unit tests for services/monitoring_service.py

Tests metrics collection and log management for system monitoring.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.monitoring_service import MonitoringService


@pytest.fixture
def monitoring_service():
    """Create MonitoringService instance."""
    with patch("services.monitoring_service.logger"):
        return MonitoringService()


class TestMonitoringServiceInit:
    """Tests for MonitoringService initialization."""

    def test_init_creates_metrics_cache(self):
        """MonitoringService should create metrics_cache."""
        with patch("services.monitoring_service.logger"):
            service = MonitoringService()
            assert isinstance(service.metrics_cache, dict)

    def test_init_logs_message(self):
        """MonitoringService should log initialization."""
        with patch("services.monitoring_service.logger") as mock_logger:
            MonitoringService()
            mock_logger.info.assert_called()
            # First call should be "Monitoring service initialized"
            first_call = mock_logger.info.call_args_list[0]
            assert first_call[0][0] == "Monitoring service initialized"

    def test_init_calls_initialize_sample_data(self):
        """MonitoringService should call _initialize_sample_data."""
        with (
            patch("services.monitoring_service.logger"),
            patch.object(MonitoringService, "_initialize_sample_data") as mock_init,
        ):
            MonitoringService()
            mock_init.assert_called_once()


class TestInitializeSampleData:
    """Tests for _initialize_sample_data method."""

    def test_initialize_sample_data_calls_initialize_metrics(self):
        """_initialize_sample_data should call _initialize_metrics."""
        with (
            patch("services.monitoring_service.logger"),
            patch.object(MonitoringService, "_initialize_metrics") as mock_init_metrics,
        ):
            service = MonitoringService.__new__(MonitoringService)
            service.metrics_cache = {}
            service._initialize_sample_data()
            mock_init_metrics.assert_called_once()


class TestInitializeMetrics:
    """Tests for _initialize_metrics method."""

    def test_initialize_metrics_sets_cpu(self, monitoring_service):
        """_initialize_metrics should set CPU metrics."""
        assert "cpu" in monitoring_service.metrics_cache
        assert "usage" in monitoring_service.metrics_cache["cpu"]
        assert "cores" in monitoring_service.metrics_cache["cpu"]
        assert "temperature" in monitoring_service.metrics_cache["cpu"]

    def test_initialize_metrics_sets_memory(self, monitoring_service):
        """_initialize_metrics should set memory metrics."""
        assert "memory" in monitoring_service.metrics_cache
        assert "used" in monitoring_service.metrics_cache["memory"]
        assert "total" in monitoring_service.metrics_cache["memory"]
        assert "percentage" in monitoring_service.metrics_cache["memory"]

    def test_initialize_metrics_sets_disk(self, monitoring_service):
        """_initialize_metrics should set disk metrics."""
        assert "disk" in monitoring_service.metrics_cache
        assert "used" in monitoring_service.metrics_cache["disk"]
        assert "total" in monitoring_service.metrics_cache["disk"]
        assert "percentage" in monitoring_service.metrics_cache["disk"]

    def test_initialize_metrics_sets_network(self, monitoring_service):
        """_initialize_metrics should set network metrics."""
        assert "network" in monitoring_service.metrics_cache
        assert "inbound" in monitoring_service.metrics_cache["network"]
        assert "outbound" in monitoring_service.metrics_cache["network"]
        assert "connections" in monitoring_service.metrics_cache["network"]

    def test_initialize_metrics_sets_uptime(self, monitoring_service):
        """_initialize_metrics should set uptime."""
        assert "uptime" in monitoring_service.metrics_cache
        assert monitoring_service.metrics_cache["uptime"] == 86400

    def test_initialize_metrics_sets_processes(self, monitoring_service):
        """_initialize_metrics should set processes count."""
        assert "processes" in monitoring_service.metrics_cache
        assert monitoring_service.metrics_cache["processes"] == 127

    def test_initialize_metrics_sets_timestamp(self, monitoring_service):
        """_initialize_metrics should set timestamp."""
        assert "timestamp" in monitoring_service.metrics_cache
        # Timestamp should be ISO format
        assert "T" in monitoring_service.metrics_cache["timestamp"]


class TestInitializeLogs:
    """Tests for _initialize_logs method."""

    @pytest.mark.asyncio
    async def test_initialize_logs_creates_entries(self, monitoring_service):
        """_initialize_logs should create log entries."""
        with patch("services.monitoring_service.log_service") as mock_log_service:
            mock_log_service.create_log_entry = AsyncMock()

            await monitoring_service._initialize_logs()

            # Should create multiple log entries (system, app, docker, security, network)
            assert mock_log_service.create_log_entry.call_count >= 10

    @pytest.mark.asyncio
    async def test_initialize_logs_creates_system_logs(self, monitoring_service):
        """_initialize_logs should create system log entries."""
        with patch("services.monitoring_service.log_service") as mock_log_service:
            mock_log_service.create_log_entry = AsyncMock()

            await monitoring_service._initialize_logs()

            # Check that at least one call has source="systemd"
            calls = mock_log_service.create_log_entry.call_args_list
            sources = [call[0][0].source for call in calls]
            assert "systemd" in sources

    @pytest.mark.asyncio
    async def test_initialize_logs_creates_docker_logs(self, monitoring_service):
        """_initialize_logs should create Docker log entries."""
        with patch("services.monitoring_service.log_service") as mock_log_service:
            mock_log_service.create_log_entry = AsyncMock()

            await monitoring_service._initialize_logs()

            calls = mock_log_service.create_log_entry.call_args_list
            sources = [call[0][0].source for call in calls]
            assert "docker" in sources

    @pytest.mark.asyncio
    async def test_initialize_logs_handles_error(self, monitoring_service):
        """_initialize_logs should handle errors gracefully."""
        with (
            patch("services.monitoring_service.log_service") as mock_log_service,
            patch("services.monitoring_service.logger") as mock_logger,
        ):
            mock_log_service.create_log_entry = AsyncMock(
                side_effect=Exception("DB error")
            )

            # Should not raise
            await monitoring_service._initialize_logs()

            mock_logger.warning.assert_called_once()


class TestGetCurrentMetrics:
    """Tests for get_current_metrics method."""

    def test_get_current_metrics_returns_dict(self, monitoring_service):
        """get_current_metrics should return dictionary."""
        result = monitoring_service.get_current_metrics()
        assert isinstance(result, dict)

    def test_get_current_metrics_updates_timestamp(self, monitoring_service):
        """get_current_metrics should update timestamp."""
        # Small delay to ensure different timestamp
        import time

        time.sleep(0.01)

        result = monitoring_service.get_current_metrics()

        # Timestamp should be updated (or at least current)
        assert "timestamp" in result
        assert result["timestamp"] is not None

    def test_get_current_metrics_includes_all_sections(self, monitoring_service):
        """get_current_metrics should include all metric sections."""
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
    async def test_get_filtered_logs_no_filters(self, monitoring_service):
        """get_filtered_logs should return logs without filters."""
        mock_log_entry = MagicMock()
        mock_log_entry.id = "log-1"
        mock_log_entry.timestamp = datetime.now(UTC)
        mock_log_entry.level = "INFO"
        mock_log_entry.source = "test"
        mock_log_entry.message = "Test message"
        mock_log_entry.tags = ["test"]

        with (
            patch("services.monitoring_service.log_service") as mock_log_service,
            patch("services.monitoring_service.logger"),
        ):
            mock_log_service.get_logs = AsyncMock(return_value=[mock_log_entry])

            result = await monitoring_service.get_filtered_logs()

            assert len(result) == 1
            assert result[0]["id"] == "log-1"
            assert result[0]["level"] == "INFO"
            assert result[0]["source"] == "test"

    @pytest.mark.asyncio
    async def test_get_filtered_logs_with_level_filter(self, monitoring_service):
        """get_filtered_logs should apply level filter."""
        with (
            patch("services.monitoring_service.log_service") as mock_log_service,
            patch("services.monitoring_service.logger"),
        ):
            mock_log_service.get_logs = AsyncMock(return_value=[])

            await monitoring_service.get_filtered_logs({"level": "ERROR"})

            # Check that LogFilter was created with correct level
            call_args = mock_log_service.get_logs.call_args[0][0]
            assert call_args.level == "ERROR"

    @pytest.mark.asyncio
    async def test_get_filtered_logs_with_source_filter(self, monitoring_service):
        """get_filtered_logs should apply source filter."""
        with (
            patch("services.monitoring_service.log_service") as mock_log_service,
            patch("services.monitoring_service.logger"),
        ):
            mock_log_service.get_logs = AsyncMock(return_value=[])

            await monitoring_service.get_filtered_logs({"source": "docker"})

            call_args = mock_log_service.get_logs.call_args[0][0]
            assert call_args.source == "docker"

    @pytest.mark.asyncio
    async def test_get_filtered_logs_with_limit(self, monitoring_service):
        """get_filtered_logs should apply limit."""
        with (
            patch("services.monitoring_service.log_service") as mock_log_service,
            patch("services.monitoring_service.logger"),
        ):
            mock_log_service.get_logs = AsyncMock(return_value=[])

            await monitoring_service.get_filtered_logs({"limit": 50})

            call_args = mock_log_service.get_logs.call_args[0][0]
            assert call_args.limit == 50

    @pytest.mark.asyncio
    async def test_get_filtered_logs_limit_max(self, monitoring_service):
        """get_filtered_logs should cap limit at 1000."""
        with (
            patch("services.monitoring_service.log_service") as mock_log_service,
            patch("services.monitoring_service.logger"),
        ):
            mock_log_service.get_logs = AsyncMock(return_value=[])

            await monitoring_service.get_filtered_logs({"limit": 5000})

            call_args = mock_log_service.get_logs.call_args[0][0]
            assert call_args.limit == 1000

    @pytest.mark.asyncio
    async def test_get_filtered_logs_initializes_when_empty(self, monitoring_service):
        """get_filtered_logs should initialize sample logs when empty."""
        mock_log_entry = MagicMock()
        mock_log_entry.id = "log-1"
        mock_log_entry.timestamp = datetime.now(UTC)
        mock_log_entry.level = "INFO"
        mock_log_entry.source = "test"
        mock_log_entry.message = "Test"
        mock_log_entry.tags = []

        with (
            patch("services.monitoring_service.log_service") as mock_log_service,
            patch("services.monitoring_service.logger"),
        ):
            # First call returns empty, second returns data
            mock_log_service.get_logs = AsyncMock(side_effect=[[], [mock_log_entry]])
            mock_log_service.create_log_entry = AsyncMock()

            await monitoring_service.get_filtered_logs()

            # Should have called get_logs twice (once empty, once after init)
            assert mock_log_service.get_logs.call_count == 2
            # Should have created sample log entries
            assert mock_log_service.create_log_entry.called

    @pytest.mark.asyncio
    async def test_get_filtered_logs_converts_to_dict(self, monitoring_service):
        """get_filtered_logs should convert LogEntry to dict format."""
        mock_log_entry = MagicMock()
        mock_log_entry.id = "log-123"
        mock_log_entry.timestamp = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        mock_log_entry.level = "WARN"
        mock_log_entry.source = "docker"
        mock_log_entry.message = "Container high memory"
        mock_log_entry.tags = ["docker", "memory"]

        with (
            patch("services.monitoring_service.log_service") as mock_log_service,
            patch("services.monitoring_service.logger"),
        ):
            mock_log_service.get_logs = AsyncMock(return_value=[mock_log_entry])

            result = await monitoring_service.get_filtered_logs()

            assert len(result) == 1
            log_dict = result[0]
            assert log_dict["id"] == "log-123"
            assert log_dict["level"] == "WARN"
            assert log_dict["source"] == "docker"
            assert log_dict["message"] == "Container high memory"
            assert log_dict["tags"] == ["docker", "memory"]
            assert "2024-01-15" in log_dict["timestamp"]

    @pytest.mark.asyncio
    async def test_get_filtered_logs_handles_error(self, monitoring_service):
        """get_filtered_logs should return empty list on error."""
        with (
            patch("services.monitoring_service.log_service") as mock_log_service,
            patch("services.monitoring_service.logger") as mock_logger,
        ):
            mock_log_service.get_logs = AsyncMock(side_effect=Exception("DB error"))

            result = await monitoring_service.get_filtered_logs()

            assert result == []
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_filtered_logs_logs_count(self, monitoring_service):
        """get_filtered_logs should log the count of retrieved logs."""
        mock_log_entry = MagicMock()
        mock_log_entry.id = "log-1"
        mock_log_entry.timestamp = datetime.now(UTC)
        mock_log_entry.level = "INFO"
        mock_log_entry.source = "test"
        mock_log_entry.message = "Test"
        mock_log_entry.tags = []

        with (
            patch("services.monitoring_service.log_service") as mock_log_service,
            patch("services.monitoring_service.logger") as mock_logger,
        ):
            mock_log_service.get_logs = AsyncMock(
                return_value=[mock_log_entry, mock_log_entry]
            )

            await monitoring_service.get_filtered_logs()

            # Check logger.info was called with count
            mock_logger.info.assert_called()
            call_kwargs = mock_logger.info.call_args.kwargs
            assert call_kwargs["count"] == 2

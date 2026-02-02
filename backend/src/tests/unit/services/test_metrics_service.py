"""
Unit tests for services/metrics_service.py

Tests metrics collection and management via SSH.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.metrics_service import MetricsService, PERIOD_MAP


@pytest.fixture
def mock_ssh_service():
    """Create mock SSH service."""
    return MagicMock()


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    return MagicMock()


@pytest.fixture
def mock_server_service():
    """Create mock server service."""
    return MagicMock()


@pytest.fixture
def metrics_service(mock_ssh_service, mock_db_service, mock_server_service):
    """Create MetricsService instance."""
    with patch("services.metrics_service.logger"):
        return MetricsService(mock_ssh_service, mock_db_service, mock_server_service)


class TestMetricsServiceInit:
    """Tests for MetricsService initialization."""

    def test_init_stores_ssh_service(
        self, mock_ssh_service, mock_db_service, mock_server_service
    ):
        """MetricsService should store ssh_service reference."""
        with patch("services.metrics_service.logger"):
            service = MetricsService(
                mock_ssh_service, mock_db_service, mock_server_service
            )
            assert service.ssh_service is mock_ssh_service

    def test_init_stores_db_service(
        self, mock_ssh_service, mock_db_service, mock_server_service
    ):
        """MetricsService should store db_service reference."""
        with patch("services.metrics_service.logger"):
            service = MetricsService(
                mock_ssh_service, mock_db_service, mock_server_service
            )
            assert service.db_service is mock_db_service

    def test_init_logs_message(
        self, mock_ssh_service, mock_db_service, mock_server_service
    ):
        """MetricsService should log initialization."""
        with patch("services.metrics_service.logger") as mock_logger:
            MetricsService(mock_ssh_service, mock_db_service, mock_server_service)
            mock_logger.info.assert_called_with("Metrics service initialized")


class TestPeriodMap:
    """Tests for PERIOD_MAP constant."""

    def test_period_map_has_1h(self):
        """PERIOD_MAP should have 1h entry."""
        assert "1h" in PERIOD_MAP
        assert PERIOD_MAP["1h"].total_seconds() == 3600

    def test_period_map_has_24h(self):
        """PERIOD_MAP should have 24h entry."""
        assert "24h" in PERIOD_MAP
        assert PERIOD_MAP["24h"].total_seconds() == 86400

    def test_period_map_has_7d(self):
        """PERIOD_MAP should have 7d entry."""
        assert "7d" in PERIOD_MAP
        assert PERIOD_MAP["7d"].days == 7

    def test_period_map_has_30d(self):
        """PERIOD_MAP should have 30d entry."""
        assert "30d" in PERIOD_MAP
        assert PERIOD_MAP["30d"].days == 30


class TestParseCpuPercent:
    """Tests for _parse_cpu_percent method."""

    def test_parse_cpu_us_sy_format(self, metrics_service):
        """_parse_cpu_percent should parse 'us, sy' format."""
        output = "Cpu(s): 25.5 us, 10.2 sy, 0.0 ni"
        result = metrics_service._parse_cpu_percent(output)
        assert result == pytest.approx(35.7, rel=0.1)

    def test_parse_cpu_percent_format(self, metrics_service):
        """_parse_cpu_percent should parse '%us' format."""
        output = "%Cpu(s): 45.3%us, 12.1%sy"
        result = metrics_service._parse_cpu_percent(output)
        assert result == pytest.approx(57.4, rel=0.1)

    def test_parse_cpu_single_percent(self, metrics_service):
        """_parse_cpu_percent should parse single CPU percentage."""
        output = "CPU: 42.5% cpu"
        result = metrics_service._parse_cpu_percent(output)
        assert result == pytest.approx(42.5, rel=0.1)

    def test_parse_cpu_no_match(self, metrics_service):
        """_parse_cpu_percent should return 0.0 when no match."""
        output = "No CPU data here"
        result = metrics_service._parse_cpu_percent(output)
        assert result == 0.0

    def test_parse_cpu_error(self, metrics_service):
        """_parse_cpu_percent should return 0.0 on error."""
        with patch("services.metrics_service.logger"):
            # Pass None to cause an error
            result = metrics_service._parse_cpu_percent(None)
            assert result == 0.0


class TestParseMemory:
    """Tests for _parse_memory method."""

    def test_parse_memory_success(self, metrics_service):
        """_parse_memory should parse free command output."""
        output = """              total        used        free      shared  buff/cache   available
Mem:       16384000     8192000     4096000       1024      4096000     6144000"""
        used, total, percent = metrics_service._parse_memory(output)

        assert total == 16384000
        assert used == 8192000
        assert percent == pytest.approx(50.0, rel=0.1)

    def test_parse_memory_no_mem_line(self, metrics_service):
        """_parse_memory should return zeros when no Mem line."""
        output = "Some other output"
        used, total, percent = metrics_service._parse_memory(output)

        assert used == 0
        assert total == 0
        assert percent == 0.0

    def test_parse_memory_zero_total(self, metrics_service):
        """_parse_memory should handle zero total."""
        output = "Mem:       0     0     0       0      0     0"
        used, total, percent = metrics_service._parse_memory(output)

        assert percent == 0.0

    def test_parse_memory_error(self, metrics_service):
        """_parse_memory should return zeros on error."""
        with patch("services.metrics_service.logger"):
            result = metrics_service._parse_memory(None)
            assert result == (0, 0, 0.0)


class TestParseDisk:
    """Tests for _parse_disk method."""

    def test_parse_disk_success(self, metrics_service):
        """_parse_disk should parse df command output."""
        output = """/dev/sda1       200G  100G  100G  50% /"""
        used, total, percent = metrics_service._parse_disk(output)

        assert total == 200
        assert used == 100
        assert percent == 50.0

    def test_parse_disk_with_header(self, metrics_service):
        """_parse_disk should skip Filesystem header."""
        output = """Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       500G  250G  250G  50% /"""
        used, total, percent = metrics_service._parse_disk(output)

        assert total == 500
        assert used == 250
        assert percent == 50.0

    def test_parse_disk_no_match(self, metrics_service):
        """_parse_disk should return zeros when no match."""
        output = "No disk data"
        used, total, percent = metrics_service._parse_disk(output)

        assert used == 0
        assert total == 0
        assert percent == 0.0

    def test_parse_disk_error(self, metrics_service):
        """_parse_disk should return zeros on error."""
        with patch("services.metrics_service.logger"):
            result = metrics_service._parse_disk(None)
            assert result == (0, 0, 0.0)


class TestParseDockerStats:
    """Tests for _parse_docker_stats method."""

    def test_parse_docker_stats_success(self, metrics_service):
        """_parse_docker_stats should parse docker stats output."""
        output = "abc123|nginx|25.5|256MiB / 512MiB|1024|2048|running"
        result = metrics_service._parse_docker_stats(output)

        assert len(result) == 1
        assert result[0]["container_id"] == "abc123"
        assert result[0]["name"] == "nginx"
        assert result[0]["cpu_percent"] == 25.5
        assert result[0]["memory_usage_mb"] == 256
        assert result[0]["memory_limit_mb"] == 512
        assert result[0]["status"] == "running"

    def test_parse_docker_stats_multiple_containers(self, metrics_service):
        """_parse_docker_stats should parse multiple containers."""
        output = """abc123|nginx|25.5|256MiB / 512MiB|1024|2048|running
def456|redis|10.2|128MiB / 256MiB|512|1024|running"""
        result = metrics_service._parse_docker_stats(output)

        assert len(result) == 2
        assert result[0]["name"] == "nginx"
        assert result[1]["name"] == "redis"

    def test_parse_docker_stats_empty_line(self, metrics_service):
        """_parse_docker_stats should skip empty lines."""
        output = "\nabc123|nginx|25.5|256MiB / 512MiB|1024|2048|running\n"
        result = metrics_service._parse_docker_stats(output)

        assert len(result) == 1

    def test_parse_docker_stats_empty_line_in_middle(self, metrics_service):
        """_parse_docker_stats should skip empty lines in middle of output."""
        output = """abc123|nginx|25.5|256MiB / 512MiB|1024|2048|running

def456|redis|10.2|128MiB / 256MiB|512|1024|running"""
        result = metrics_service._parse_docker_stats(output)

        assert len(result) == 2

    def test_parse_docker_stats_incomplete_line(self, metrics_service):
        """_parse_docker_stats should skip incomplete lines."""
        output = "abc123|nginx|25.5"
        result = metrics_service._parse_docker_stats(output)

        assert len(result) == 0

    def test_parse_docker_stats_error(self, metrics_service):
        """_parse_docker_stats should return empty list on error."""
        with patch("services.metrics_service.logger"):
            result = metrics_service._parse_docker_stats(None)
            assert result == []


class TestCollectServerMetrics:
    """Tests for collect_server_metrics method."""

    @pytest.mark.asyncio
    async def test_collect_server_metrics_success(
        self, metrics_service, mock_ssh_service, mock_db_service
    ):
        """collect_server_metrics should collect and save metrics."""
        mock_ssh_service.execute_command = AsyncMock(
            side_effect=[
                (0, "Cpu(s): 25.5 us, 10.2 sy", ""),  # CPU
                (0, "Mem:    16384000  8192000  4096000", ""),  # Memory
                (0, "/dev/sda1  200G  100G  100G  50% /", ""),  # Disk
            ]
        )
        mock_db_service.save_server_metrics = AsyncMock()

        with patch("services.metrics_service.logger"):
            result = await metrics_service.collect_server_metrics("srv-123")

        assert result is not None
        assert result.server_id == "srv-123"
        mock_db_service.save_server_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_server_metrics_ssh_failure(
        self, metrics_service, mock_ssh_service, mock_db_service
    ):
        """collect_server_metrics should handle SSH failures gracefully."""
        mock_ssh_service.execute_command = AsyncMock(
            side_effect=[
                (1, "", "Error"),  # CPU failed
                (1, "", "Error"),  # Memory failed
                (1, "", "Error"),  # Disk failed
            ]
        )
        mock_db_service.save_server_metrics = AsyncMock()

        with patch("services.metrics_service.logger"):
            result = await metrics_service.collect_server_metrics("srv-123")

        assert result is not None
        assert result.cpu_percent == 0.0
        assert result.memory_percent == 0.0
        assert result.disk_percent == 0.0

    @pytest.mark.asyncio
    async def test_collect_server_metrics_error(
        self, metrics_service, mock_ssh_service
    ):
        """collect_server_metrics should return None on error."""
        mock_ssh_service.execute_command = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        with patch("services.metrics_service.logger"):
            result = await metrics_service.collect_server_metrics("srv-123")

        assert result is None


class TestCollectContainerMetrics:
    """Tests for collect_container_metrics method."""

    @pytest.mark.asyncio
    async def test_collect_container_metrics_success(
        self, metrics_service, mock_ssh_service, mock_db_service
    ):
        """collect_container_metrics should collect and save metrics."""
        docker_output = "abc123|nginx|25.5|256MiB / 512MiB|1024|2048|running"
        mock_ssh_service.execute_command = AsyncMock(return_value=(0, docker_output, ""))
        mock_db_service.save_container_metrics = AsyncMock()

        with patch("services.metrics_service.logger"):
            result = await metrics_service.collect_container_metrics("srv-123")

        assert len(result) == 1
        assert result[0].container_name == "nginx"
        mock_db_service.save_container_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_container_metrics_docker_failed(
        self, metrics_service, mock_ssh_service
    ):
        """collect_container_metrics should return empty list on docker failure."""
        mock_ssh_service.execute_command = AsyncMock(return_value=(1, "", "Error"))

        with patch("services.metrics_service.logger"):
            result = await metrics_service.collect_container_metrics("srv-123")

        assert result == []

    @pytest.mark.asyncio
    async def test_collect_container_metrics_error(
        self, metrics_service, mock_ssh_service
    ):
        """collect_container_metrics should return empty list on error."""
        mock_ssh_service.execute_command = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        with patch("services.metrics_service.logger"):
            result = await metrics_service.collect_container_metrics("srv-123")

        assert result == []


class TestGetServerMetrics:
    """Tests for get_server_metrics method."""

    @pytest.mark.asyncio
    async def test_get_server_metrics_success(
        self, metrics_service, mock_db_service
    ):
        """get_server_metrics should return historical metrics."""
        mock_metrics = [MagicMock(), MagicMock()]
        mock_db_service.get_server_metrics = AsyncMock(return_value=mock_metrics)

        with patch("services.metrics_service.logger"):
            result = await metrics_service.get_server_metrics("srv-123", "24h")

        assert len(result) == 2
        mock_db_service.get_server_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_server_metrics_different_periods(
        self, metrics_service, mock_db_service
    ):
        """get_server_metrics should use different time periods."""
        mock_db_service.get_server_metrics = AsyncMock(return_value=[])

        with patch("services.metrics_service.logger"):
            await metrics_service.get_server_metrics("srv-123", "7d")

        call_kwargs = mock_db_service.get_server_metrics.call_args.kwargs
        assert "since" in call_kwargs

    @pytest.mark.asyncio
    async def test_get_server_metrics_default_period(
        self, metrics_service, mock_db_service
    ):
        """get_server_metrics should use default period for unknown."""
        mock_db_service.get_server_metrics = AsyncMock(return_value=[])

        with patch("services.metrics_service.logger"):
            await metrics_service.get_server_metrics("srv-123", "unknown")

        # Should still work with default 24h
        mock_db_service.get_server_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_server_metrics_error(
        self, metrics_service, mock_db_service
    ):
        """get_server_metrics should return empty list on error."""
        mock_db_service.get_server_metrics = AsyncMock(
            side_effect=Exception("DB error")
        )

        with patch("services.metrics_service.logger"):
            result = await metrics_service.get_server_metrics("srv-123")

        assert result == []


class TestGetContainerMetrics:
    """Tests for get_container_metrics method."""

    @pytest.mark.asyncio
    async def test_get_container_metrics_success(
        self, metrics_service, mock_db_service
    ):
        """get_container_metrics should return historical metrics."""
        mock_metrics = [MagicMock()]
        mock_db_service.get_container_metrics = AsyncMock(return_value=mock_metrics)

        with patch("services.metrics_service.logger"):
            result = await metrics_service.get_container_metrics("srv-123")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_container_metrics_with_name(
        self, metrics_service, mock_db_service
    ):
        """get_container_metrics should pass container_name filter."""
        mock_db_service.get_container_metrics = AsyncMock(return_value=[])

        with patch("services.metrics_service.logger"):
            await metrics_service.get_container_metrics(
                "srv-123", container_name="nginx"
            )

        call_kwargs = mock_db_service.get_container_metrics.call_args.kwargs
        assert call_kwargs["container_name"] == "nginx"

    @pytest.mark.asyncio
    async def test_get_container_metrics_error(
        self, metrics_service, mock_db_service
    ):
        """get_container_metrics should return empty list on error."""
        mock_db_service.get_container_metrics = AsyncMock(
            side_effect=Exception("DB error")
        )

        with patch("services.metrics_service.logger"):
            result = await metrics_service.get_container_metrics("srv-123")

        assert result == []

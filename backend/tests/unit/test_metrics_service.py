"""Tests for metrics collection service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.metrics_service import MetricsService


class TestMetricsService:
    """Tests for MetricsService."""

    @pytest.fixture
    def mock_ssh_service(self):
        """Create mock SSH service."""
        ssh = MagicMock()
        ssh.execute_command = AsyncMock()
        return ssh

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = MagicMock()
        db.save_server_metrics = AsyncMock()
        db.save_container_metrics = AsyncMock()
        db.get_server_metrics = AsyncMock(return_value=[])
        db.get_container_metrics = AsyncMock(return_value=[])
        return db

    @pytest.fixture
    def mock_server_service(self):
        """Create mock server service."""
        svc = MagicMock()
        svc.list_servers = AsyncMock(return_value=[])
        return svc

    @pytest.fixture
    def metrics_service(self, mock_ssh_service, mock_db_service, mock_server_service):
        """Create metrics service with mocks."""
        return MetricsService(
            ssh_service=mock_ssh_service,
            db_service=mock_db_service,
            server_service=mock_server_service
        )

    def test_parse_cpu_output(self, metrics_service):
        """Should parse CPU usage from top command."""
        output = "top - 10:00:00 up 5 days, %Cpu(s): 25.5 us, 10.2 sy"
        result = metrics_service._parse_cpu_percent(output)
        assert result == pytest.approx(35.7, rel=0.1)

    def test_parse_memory_output(self, metrics_service):
        """Should parse memory usage from free command."""
        output = """              total        used        free
Mem:        8192000     4096000     2048000"""
        used, total, percent = metrics_service._parse_memory(output)
        assert total == 8192000
        assert used == 4096000
        assert percent == pytest.approx(50.0, rel=0.1)

    def test_parse_disk_output(self, metrics_service):
        """Should parse disk usage from df command."""
        output = """/dev/sda1      200G  156G   44G  78% /"""
        used, total, percent = metrics_service._parse_disk(output)
        assert total == 200
        assert used == 156
        assert percent == 78.0

    def test_parse_docker_stats(self, metrics_service):
        """Should parse docker stats output."""
        output = """abc123|portainer|12.5%|256MiB / 512MiB|1024|2048|running"""
        containers = metrics_service._parse_docker_stats(output)
        assert len(containers) == 1
        assert containers[0]["name"] == "portainer"
        assert containers[0]["cpu_percent"] == 12.5

    @pytest.mark.asyncio
    async def test_collect_server_metrics(self, metrics_service, mock_ssh_service, mock_db_service):
        """Should collect and save server metrics."""
        mock_ssh_service.execute_command.side_effect = [
            (0, "%Cpu(s): 25.0 us, 10.0 sy", ""),  # CPU
            (0, "Mem: 8192000 4096000 2048000", ""),  # Memory
            (0, "/dev/sda1 200G 156G 44G 78% /", ""),  # Disk
        ]

        result = await metrics_service.collect_server_metrics("server-123")

        assert result is not None
        mock_db_service.save_server_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_server_metrics_with_period(self, metrics_service, mock_db_service):
        """Should get metrics for specified period."""
        mock_db_service.get_server_metrics.return_value = [
            MagicMock(cpu_percent=30.0, memory_percent=50.0)
        ]

        result = await metrics_service.get_server_metrics("server-123", period="24h")

        assert result is not None
        mock_db_service.get_server_metrics.assert_called_once()

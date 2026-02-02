"""
Unit tests for services/deployment/status.py - Health check functionality

Tests for check_container_health and get_container_logs methods.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_ssh_executor():
    """Create mock SSH executor."""
    executor = MagicMock()
    executor.execute = AsyncMock(return_value=(0, "", ""))
    return executor


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    return MagicMock()


@pytest.fixture
def mock_server_service():
    """Create mock server service."""
    return MagicMock()


@pytest.fixture
def mock_marketplace_service():
    """Create mock marketplace service."""
    return MagicMock()


@pytest.fixture
def status_manager(
    mock_ssh_executor,
    mock_db_service,
    mock_server_service,
    mock_marketplace_service
):
    """Create StatusManager instance with mocked dependencies."""
    from services.deployment.status import StatusManager
    return StatusManager(
        ssh_executor=mock_ssh_executor,
        db_service=mock_db_service,
        server_service=mock_server_service,
        marketplace_service=mock_marketplace_service
    )


@pytest.fixture
def health_check_output_running():
    """Health check output for running container."""
    return """STATUS:running
RESTARTS:0
PORTS:8080/tcp -> 0.0.0.0:8080
LOGS_START
2024-01-01 Starting app...
2024-01-01 App started successfully
LOGS_END"""


@pytest.fixture
def health_check_output_unhealthy():
    """Health check output for unhealthy container."""
    return """STATUS:running
RESTARTS:5
PORTS:
LOGS_START
Error: Connection refused
Failed to start
LOGS_END"""


class TestCheckContainerHealth:
    """Tests for check_container_health method."""

    @pytest.mark.asyncio
    async def test_returns_health_dict(
        self, status_manager, mock_ssh_executor, health_check_output_running
    ):
        """Should return health status dict."""
        mock_ssh_executor.execute.return_value = (0, health_check_output_running, "")

        result = await status_manager.check_container_health("server-1", "test-container")

        assert isinstance(result, dict)
        assert "container_running" in result
        assert "healthy" in result

    @pytest.mark.asyncio
    async def test_parses_running_status(
        self, status_manager, mock_ssh_executor, health_check_output_running
    ):
        """Should correctly parse running status."""
        mock_ssh_executor.execute.return_value = (0, health_check_output_running, "")

        result = await status_manager.check_container_health("server-1", "test-container")

        assert result["container_running"] is True
        assert result["container_status"] == "running"

    @pytest.mark.asyncio
    async def test_parses_stopped_status(
        self, status_manager, mock_ssh_executor
    ):
        """Should correctly parse stopped status."""
        output = "STATUS:exited\nRESTARTS:0\nPORTS:\nLOGS_START\nLOGS_END"
        mock_ssh_executor.execute.return_value = (0, output, "")

        result = await status_manager.check_container_health("server-1", "test-container")

        assert result["container_running"] is False
        assert result["container_status"] == "exited"

    @pytest.mark.asyncio
    async def test_parses_restart_count(
        self, status_manager, mock_ssh_executor, health_check_output_unhealthy
    ):
        """Should correctly parse restart count."""
        mock_ssh_executor.execute.return_value = (0, health_check_output_unhealthy, "")

        result = await status_manager.check_container_health("server-1", "test-container")

        assert result["restart_count"] == 5

    @pytest.mark.asyncio
    async def test_handles_invalid_restart_count(
        self, status_manager, mock_ssh_executor
    ):
        """Should handle invalid restart count."""
        output = "STATUS:running\nRESTARTS:invalid\nPORTS:\nLOGS_START\nLOGS_END"
        mock_ssh_executor.execute.return_value = (0, output, "")

        result = await status_manager.check_container_health("server-1", "test-container")

        assert result["restart_count"] == 0

    @pytest.mark.asyncio
    async def test_parses_ports(
        self, status_manager, mock_ssh_executor, health_check_output_running
    ):
        """Should correctly parse port mappings."""
        mock_ssh_executor.execute.return_value = (0, health_check_output_running, "")

        result = await status_manager.check_container_health("server-1", "test-container")

        assert len(result["ports_listening"]) >= 1
        assert "8080/tcp -> 0.0.0.0:8080" in result["ports_listening"]

    @pytest.mark.asyncio
    async def test_parses_empty_ports(
        self, status_manager, mock_ssh_executor
    ):
        """Should handle empty ports."""
        output = "STATUS:running\nRESTARTS:0\nPORTS:\nLOGS_START\nLOGS_END"
        mock_ssh_executor.execute.return_value = (0, output, "")

        result = await status_manager.check_container_health("server-1", "test-container")

        assert result["ports_listening"] == []

    @pytest.mark.asyncio
    async def test_parses_logs(
        self, status_manager, mock_ssh_executor, health_check_output_running
    ):
        """Should correctly parse recent logs."""
        mock_ssh_executor.execute.return_value = (0, health_check_output_running, "")

        result = await status_manager.check_container_health("server-1", "test-container")

        # Logs include the full lines with timestamps
        assert any("Starting app" in log for log in result["recent_logs"])
        assert any("App started successfully" in log for log in result["recent_logs"])

    @pytest.mark.asyncio
    async def test_limits_logs_to_20_lines(
        self, status_manager, mock_ssh_executor
    ):
        """Should limit logs to last 20 lines."""
        log_lines = [f"Line {i}" for i in range(30)]
        output = "STATUS:running\nRESTARTS:0\nPORTS:\nLOGS_START\n"
        output += "\n".join(log_lines)
        output += "\nLOGS_END"
        mock_ssh_executor.execute.return_value = (0, output, "")

        result = await status_manager.check_container_health("server-1", "test-container")

        assert len(result["recent_logs"]) == 20

    @pytest.mark.asyncio
    async def test_healthy_when_running_and_low_restarts(
        self, status_manager, mock_ssh_executor, health_check_output_running
    ):
        """Should be healthy when running with low restarts."""
        mock_ssh_executor.execute.return_value = (0, health_check_output_running, "")

        result = await status_manager.check_container_health("server-1", "test-container")

        assert result["healthy"] is True

    @pytest.mark.asyncio
    async def test_unhealthy_when_high_restarts(
        self, status_manager, mock_ssh_executor, health_check_output_unhealthy
    ):
        """Should be unhealthy when restart count >= 3."""
        mock_ssh_executor.execute.return_value = (0, health_check_output_unhealthy, "")

        result = await status_manager.check_container_health("server-1", "test-container")

        assert result["healthy"] is False

    @pytest.mark.asyncio
    async def test_unhealthy_when_not_running(
        self, status_manager, mock_ssh_executor
    ):
        """Should be unhealthy when not running."""
        output = "STATUS:exited\nRESTARTS:0\nPORTS:\nLOGS_START\nLOGS_END"
        mock_ssh_executor.execute.return_value = (0, output, "")

        result = await status_manager.check_container_health("server-1", "test-container")

        assert result["healthy"] is False

    @pytest.mark.asyncio
    async def test_calls_ssh_with_timeout(
        self, status_manager, mock_ssh_executor
    ):
        """Should call SSH with 30 second timeout."""
        mock_ssh_executor.execute.return_value = (0, "STATUS:running\nRESTARTS:0\nPORTS:\nLOGS_START\nLOGS_END", "")

        await status_manager.check_container_health("server-1", "test-container")

        mock_ssh_executor.execute.assert_called_once()
        call_args = mock_ssh_executor.execute.call_args
        assert call_args[1]["timeout"] == 30

    @pytest.mark.asyncio
    async def test_handles_exception(
        self, status_manager, mock_ssh_executor
    ):
        """Should return error info on exception."""
        mock_ssh_executor.execute.side_effect = Exception("SSH error")

        with patch("services.deployment.status.logger") as mock_logger:
            result = await status_manager.check_container_health(
                "server-1", "test-container"
            )

        assert result["healthy"] is False
        assert result["error"] == "SSH error"
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_uses_health_check_script(
        self, status_manager, mock_ssh_executor
    ):
        """Should use health_check_script for the command."""
        mock_ssh_executor.execute.return_value = (0, "STATUS:running\nRESTARTS:0\nPORTS:\nLOGS_START\nLOGS_END", "")

        await status_manager.check_container_health("server-1", "my-container")

        call_args = mock_ssh_executor.execute.call_args
        script = call_args[0][1]
        assert "my-container" in script
        assert "docker inspect" in script


class TestGetContainerLogs:
    """Tests for get_container_logs method."""

    @pytest.mark.asyncio
    async def test_returns_logs_dict(
        self, status_manager, mock_ssh_executor
    ):
        """Should return logs dict with logs array."""
        mock_ssh_executor.execute.return_value = (
            0,
            "2024-01-01T00:00:00Z Log message 1\n2024-01-01T00:00:01Z Log message 2",
            ""
        )

        result = await status_manager.get_container_logs("server-1", "test-container")

        assert "logs" in result
        assert isinstance(result["logs"], list)

    @pytest.mark.asyncio
    async def test_parses_timestamped_logs(
        self, status_manager, mock_ssh_executor
    ):
        """Should parse logs with timestamps."""
        mock_ssh_executor.execute.return_value = (
            0,
            "2024-01-01T00:00:00Z Starting service\n2024-01-01T00:00:01Z Service started",
            ""
        )

        result = await status_manager.get_container_logs("server-1", "test-container")

        assert len(result["logs"]) == 2
        assert result["logs"][0]["timestamp"] == "2024-01-01T00:00:00Z"
        assert result["logs"][0]["message"] == "Starting service"

    @pytest.mark.asyncio
    async def test_handles_non_timestamped_logs(
        self, status_manager, mock_ssh_executor
    ):
        """Should handle logs without timestamps."""
        mock_ssh_executor.execute.return_value = (
            0,
            "Plain log message without timestamp",
            ""
        )

        result = await status_manager.get_container_logs("server-1", "test-container")

        assert len(result["logs"]) == 1
        assert result["logs"][0]["timestamp"] is None
        assert result["logs"][0]["message"] == "Plain log message without timestamp"

    @pytest.mark.asyncio
    async def test_default_tail_is_100(
        self, status_manager, mock_ssh_executor
    ):
        """Should use default tail of 100 lines."""
        mock_ssh_executor.execute.return_value = (0, "", "")

        await status_manager.get_container_logs("server-1", "test-container")

        call_args = mock_ssh_executor.execute.call_args
        cmd = call_args[0][1]
        assert "--tail 100" in cmd

    @pytest.mark.asyncio
    async def test_custom_tail_parameter(
        self, status_manager, mock_ssh_executor
    ):
        """Should use custom tail parameter."""
        mock_ssh_executor.execute.return_value = (0, "", "")

        await status_manager.get_container_logs("server-1", "test-container", tail=50)

        call_args = mock_ssh_executor.execute.call_args
        cmd = call_args[0][1]
        assert "--tail 50" in cmd

    @pytest.mark.asyncio
    async def test_includes_timestamps_flag(
        self, status_manager, mock_ssh_executor
    ):
        """Should include --timestamps flag."""
        mock_ssh_executor.execute.return_value = (0, "", "")

        await status_manager.get_container_logs("server-1", "test-container")

        call_args = mock_ssh_executor.execute.call_args
        cmd = call_args[0][1]
        assert "--timestamps" in cmd

    @pytest.mark.asyncio
    async def test_returns_container_name(
        self, status_manager, mock_ssh_executor
    ):
        """Should include container_name in result."""
        mock_ssh_executor.execute.return_value = (0, "", "")

        result = await status_manager.get_container_logs("server-1", "test-container")

        assert result["container_name"] == "test-container"

    @pytest.mark.asyncio
    async def test_returns_line_count(
        self, status_manager, mock_ssh_executor
    ):
        """Should include line_count in result."""
        mock_ssh_executor.execute.return_value = (
            0,
            "2024-01-01T00:00:00Z Line 1\n2024-01-01T00:00:01Z Line 2\n2024-01-01T00:00:02Z Line 3",
            ""
        )

        result = await status_manager.get_container_logs("server-1", "test-container")

        assert result["line_count"] == 3

    @pytest.mark.asyncio
    async def test_returns_error_when_container_not_found(
        self, status_manager, mock_ssh_executor
    ):
        """Should return error when container not found."""
        # First call fails (docker logs)
        # Second call (check if exists) returns empty
        mock_ssh_executor.execute.side_effect = [
            (1, "", "Error: No such container"),
            (0, "", ""),
        ]

        result = await status_manager.get_container_logs("server-1", "test-container")

        assert result["logs"] == []
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_returns_error_on_docker_logs_failure(
        self, status_manager, mock_ssh_executor
    ):
        """Should return error when docker logs fails."""
        mock_ssh_executor.execute.side_effect = [
            (1, "", "Some docker error"),
            (0, "test-container", ""),  # Container exists
        ]

        result = await status_manager.get_container_logs("server-1", "test-container")

        assert result["logs"] == []
        assert "error" in result

    @pytest.mark.asyncio
    async def test_calls_ssh_with_timeout(
        self, status_manager, mock_ssh_executor
    ):
        """Should call SSH with 30 second timeout."""
        mock_ssh_executor.execute.return_value = (0, "", "")

        await status_manager.get_container_logs("server-1", "test-container")

        call_args = mock_ssh_executor.execute.call_args
        assert call_args[1]["timeout"] == 30

    @pytest.mark.asyncio
    async def test_handles_exception(
        self, status_manager, mock_ssh_executor
    ):
        """Should return error info on exception."""
        mock_ssh_executor.execute.side_effect = Exception("SSH connection failed")

        with patch("services.deployment.status.logger") as mock_logger:
            result = await status_manager.get_container_logs(
                "server-1", "test-container"
            )

        assert result["logs"] == []
        assert result["error"] == "SSH connection failed"
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_empty_lines(
        self, status_manager, mock_ssh_executor
    ):
        """Should skip empty lines in output."""
        mock_ssh_executor.execute.return_value = (
            0,
            "2024-01-01T00:00:00Z Line 1\n\n2024-01-01T00:00:01Z Line 2\n",
            ""
        )

        result = await status_manager.get_container_logs("server-1", "test-container")

        assert result["line_count"] == 2

    @pytest.mark.asyncio
    async def test_handles_mixed_timestamp_formats(
        self, status_manager, mock_ssh_executor
    ):
        """Should handle both timestamped and non-timestamped lines."""
        mock_ssh_executor.execute.return_value = (
            0,
            "2024-01-01T00:00:00Z Timestamped line\nPlain line without timestamp",
            ""
        )

        result = await status_manager.get_container_logs("server-1", "test-container")

        assert len(result["logs"]) == 2
        assert result["logs"][0]["timestamp"] == "2024-01-01T00:00:00Z"
        assert result["logs"][1]["timestamp"] is None

"""
Unit tests for services/command_router.py - Main execute methods.

Tests for execute, execute_with_progress methods.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.command_router import (
    CommandRouter,
    ExecutionMethod,
)


@pytest.fixture
def mock_agent_service():
    """Create mock agent service."""
    return MagicMock()


@pytest.fixture
def mock_agent_manager():
    """Create mock agent manager."""
    manager = MagicMock()
    manager.is_connected.return_value = False
    manager.send_command = AsyncMock()
    return manager


@pytest.fixture
def mock_server_service():
    """Create mock server service."""
    service = MagicMock()
    service.get_server = AsyncMock()
    service.get_credentials = AsyncMock()
    return service


@pytest.fixture
def mock_ssh_service():
    """Create mock SSH service."""
    service = MagicMock()
    service.execute_command = AsyncMock()
    service.execute_command_with_progress = AsyncMock()
    return service


@pytest.fixture
def router(
    mock_agent_service, mock_agent_manager, mock_server_service, mock_ssh_service
):
    """Create CommandRouter instance with mocked dependencies."""
    return CommandRouter(
        agent_service=mock_agent_service,
        agent_manager=mock_agent_manager,
        server_service=mock_server_service,
        ssh_service=mock_ssh_service,
    )


@pytest.fixture
def mock_server():
    """Create mock server object."""
    server = MagicMock()
    server.host = "192.168.1.100"
    server.port = 22
    server.username = "admin"
    server.auth_type = "password"
    return server


class TestExecute:
    """Tests for main execute method."""

    @pytest.mark.asyncio
    async def test_execute_via_ssh(
        self,
        router,
        mock_agent_service,
        mock_server_service,
        mock_ssh_service,
        mock_server,
    ):
        """execute should route to SSH when agent not available."""
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=None)
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = {"password": "secret"}
        mock_ssh_service.execute_command.return_value = (True, "ssh output")

        with patch("services.command_router.logger"):
            result = await router.execute("server-123", "ls")

        assert result.success is True
        assert result.method == ExecutionMethod.SSH
        assert result.output == "ssh output"
        assert result.execution_time_ms is not None

    @pytest.mark.asyncio
    async def test_execute_via_agent(
        self, router, mock_agent_service, mock_agent_manager
    ):
        """execute should route to agent when available."""
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = True
        mock_agent_manager.send_command.return_value = {
            "exit_code": 0,
            "stdout": "agent output",
            "stderr": "",
        }

        with patch("services.command_router.logger"):
            result = await router.execute("server-123", "ls")

        assert result.success is True
        assert result.method == ExecutionMethod.AGENT
        assert result.output == "agent output"

    @pytest.mark.asyncio
    async def test_execute_force_ssh(
        self,
        router,
        mock_agent_service,
        mock_agent_manager,
        mock_server_service,
        mock_ssh_service,
        mock_server,
    ):
        """execute should use SSH when force_ssh=True even if agent available."""
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = True
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = {"password": "secret"}
        mock_ssh_service.execute_command.return_value = (True, "forced ssh")

        with patch("services.command_router.logger"):
            result = await router.execute("server-123", "ls", force_ssh=True)

        assert result.method == ExecutionMethod.SSH

    @pytest.mark.asyncio
    async def test_execute_force_agent_unavailable(self, router, mock_agent_service):
        """execute should return error when force_agent=True but agent unavailable."""
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=None)

        with patch("services.command_router.logger"):
            result = await router.execute("server-123", "ls", force_agent=True)

        assert result.success is False
        assert result.method == ExecutionMethod.NONE
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_records_execution_time(
        self,
        router,
        mock_agent_service,
        mock_server_service,
        mock_ssh_service,
        mock_server,
    ):
        """execute should record execution time in milliseconds."""
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=None)
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = {"password": "secret"}
        mock_ssh_service.execute_command.return_value = (True, "output")

        with patch("services.command_router.logger"):
            result = await router.execute("server-123", "ls")

        assert result.execution_time_ms is not None
        assert isinstance(result.execution_time_ms, float)
        assert result.execution_time_ms >= 0

    @pytest.mark.asyncio
    async def test_execute_logs_result(
        self,
        router,
        mock_agent_service,
        mock_server_service,
        mock_ssh_service,
        mock_server,
    ):
        """execute should log execution result."""
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=None)
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = {"password": "secret"}
        mock_ssh_service.execute_command.return_value = (True, "output")

        with patch("services.command_router.logger") as mock_logger:
            await router.execute("server-123", "ls")

            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args.kwargs
            assert call_kwargs["server_id"] == "server-123"
            assert call_kwargs["method"] == "ssh"
            assert call_kwargs["success"] is True


class TestExecuteWithProgress:
    """Tests for execute_with_progress method."""

    @pytest.mark.asyncio
    async def test_execute_with_progress_uses_ssh(
        self, router, mock_server_service, mock_ssh_service, mock_server
    ):
        """execute_with_progress should always use SSH."""
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = {"password": "secret"}
        mock_ssh_service.execute_command_with_progress.return_value = (True, "output")
        callback = MagicMock()

        result = await router.execute_with_progress("server-123", "long_cmd", callback)

        assert result.method == ExecutionMethod.SSH
        mock_ssh_service.execute_command_with_progress.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_progress_records_time(
        self, router, mock_server_service, mock_ssh_service, mock_server
    ):
        """execute_with_progress should record execution time."""
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = {"password": "secret"}
        mock_ssh_service.execute_command_with_progress.return_value = (True, "output")
        callback = MagicMock()

        result = await router.execute_with_progress(
            "server-123", "cmd", callback, timeout=600.0
        )

        assert result.execution_time_ms is not None
        assert result.execution_time_ms >= 0

"""
Unit tests for services/command_router.py - Internal execution methods

Tests for _execute_via_agent, _execute_via_ssh, and _execute_via_ssh_with_progress.
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


class TestExecuteViaAgent:
    """Tests for _execute_via_agent method."""

    @pytest.mark.asyncio
    async def test_agent_not_found(self, router, mock_agent_service):
        """_execute_via_agent should return error when agent not found."""
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=None)

        result = await router._execute_via_agent("server-123", "ls", 30.0)

        assert result.success is False
        assert result.method == ExecutionMethod.AGENT
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_agent_not_connected(
        self, router, mock_agent_service, mock_agent_manager
    ):
        """_execute_via_agent should return error when agent disconnected."""
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = False

        result = await router._execute_via_agent("server-123", "ls", 30.0)

        assert result.success is False
        assert result.method == ExecutionMethod.AGENT
        assert "not connected" in result.error.lower()

    @pytest.mark.asyncio
    async def test_agent_success_dict_response(
        self, router, mock_agent_service, mock_agent_manager
    ):
        """_execute_via_agent should parse dict response correctly."""
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = True
        mock_agent_manager.send_command.return_value = {
            "exit_code": 0,
            "stdout": "file1.txt\nfile2.txt",
            "stderr": "",
        }

        result = await router._execute_via_agent("server-123", "ls", 30.0)

        assert result.success is True
        assert result.method == ExecutionMethod.AGENT
        assert result.output == "file1.txt\nfile2.txt"
        assert result.exit_code == 0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_agent_failure_dict_response(
        self, router, mock_agent_service, mock_agent_manager
    ):
        """_execute_via_agent should parse failed dict response correctly."""
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = True
        mock_agent_manager.send_command.return_value = {
            "exit_code": 1,
            "stdout": "",
            "stderr": "command not found",
        }

        result = await router._execute_via_agent("server-123", "invalid_cmd", 30.0)

        assert result.success is False
        assert result.method == ExecutionMethod.AGENT
        assert result.output == "command not found"
        assert result.exit_code == 1
        assert result.error == "command not found"

    @pytest.mark.asyncio
    async def test_agent_non_dict_response(
        self, router, mock_agent_service, mock_agent_manager
    ):
        """_execute_via_agent should handle non-dict response."""
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = True
        mock_agent_manager.send_command.return_value = "simple string response"

        result = await router._execute_via_agent("server-123", "cmd", 30.0)

        assert result.success is True
        assert result.method == ExecutionMethod.AGENT
        assert result.output == "simple string response"

    @pytest.mark.asyncio
    async def test_agent_none_response(
        self, router, mock_agent_service, mock_agent_manager
    ):
        """_execute_via_agent should handle None response."""
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = True
        mock_agent_manager.send_command.return_value = None

        result = await router._execute_via_agent("server-123", "cmd", 30.0)

        assert result.success is True
        assert result.output == ""

    @pytest.mark.asyncio
    async def test_agent_timeout_error(
        self, router, mock_agent_service, mock_agent_manager
    ):
        """_execute_via_agent should handle timeout error."""
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = True
        mock_agent_manager.send_command.side_effect = TimeoutError("Command timed out")

        with patch("services.command_router.logger"):
            result = await router._execute_via_agent("server-123", "long_cmd", 30.0)

        assert result.success is False
        assert result.method == ExecutionMethod.AGENT
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_agent_generic_exception(
        self, router, mock_agent_service, mock_agent_manager
    ):
        """_execute_via_agent should handle generic exception."""
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = True
        mock_agent_manager.send_command.side_effect = Exception("Connection lost")

        with patch("services.command_router.logger"):
            result = await router._execute_via_agent("server-123", "cmd", 30.0)

        assert result.success is False
        assert result.method == ExecutionMethod.AGENT
        assert "Connection lost" in result.error

    @pytest.mark.asyncio
    async def test_agent_sends_correct_params(
        self, router, mock_agent_service, mock_agent_manager
    ):
        """_execute_via_agent should send correct parameters to agent."""
        mock_agent = MagicMock(id="agent-456")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = True
        mock_agent_manager.send_command.return_value = {
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
        }

        await router._execute_via_agent("server-123", "echo test", 60.0)

        mock_agent_manager.send_command.assert_called_once_with(
            agent_id="agent-456",
            method="system.exec",
            params={"command": "echo test", "timeout": 60.0},
            timeout=60.0,
        )


class TestExecuteViaSSH:
    """Tests for _execute_via_ssh method."""

    @pytest.mark.asyncio
    async def test_server_not_found(self, router, mock_server_service):
        """_execute_via_ssh should return error when server not found."""
        mock_server_service.get_server.return_value = None

        result = await router._execute_via_ssh("server-123", "ls", 30.0)

        assert result.success is False
        assert result.method == ExecutionMethod.SSH
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_credentials_not_found(
        self, router, mock_server_service, mock_server
    ):
        """_execute_via_ssh should return error when credentials not found."""
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = None

        result = await router._execute_via_ssh("server-123", "ls", 30.0)

        assert result.success is False
        assert result.method == ExecutionMethod.SSH
        assert "credentials" in result.error.lower()

    @pytest.mark.asyncio
    async def test_ssh_success(
        self, router, mock_server_service, mock_ssh_service, mock_server
    ):
        """_execute_via_ssh should execute command successfully."""
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = {"password": "secret"}
        mock_ssh_service.execute_command.return_value = (True, "output text")

        result = await router._execute_via_ssh("server-123", "ls -la", 30.0)

        assert result.success is True
        assert result.method == ExecutionMethod.SSH
        assert result.output == "output text"
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_ssh_failure(
        self, router, mock_server_service, mock_ssh_service, mock_server
    ):
        """_execute_via_ssh should handle command failure."""
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = {"password": "secret"}
        mock_ssh_service.execute_command.return_value = (False, "permission denied")

        result = await router._execute_via_ssh("server-123", "rm /root", 30.0)

        assert result.success is False
        assert result.method == ExecutionMethod.SSH
        assert result.output == "permission denied"
        assert result.exit_code == 1

    @pytest.mark.asyncio
    async def test_ssh_calls_with_correct_params(
        self, router, mock_server_service, mock_ssh_service, mock_server
    ):
        """_execute_via_ssh should call SSH service with correct parameters."""
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = {"password": "secret"}
        mock_ssh_service.execute_command.return_value = (True, "")

        await router._execute_via_ssh("server-123", "whoami", 120.0)

        mock_ssh_service.execute_command.assert_called_once_with(
            host="192.168.1.100",
            port=22,
            username="admin",
            auth_type="password",
            credentials={"password": "secret"},
            command="whoami",
            timeout=120,
        )

    @pytest.mark.asyncio
    async def test_ssh_exception(
        self, router, mock_server_service, mock_ssh_service, mock_server
    ):
        """_execute_via_ssh should handle exception."""
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = {"password": "secret"}
        mock_ssh_service.execute_command.side_effect = Exception("Connection refused")

        with patch("services.command_router.logger"):
            result = await router._execute_via_ssh("server-123", "ls", 30.0)

        assert result.success is False
        assert result.method == ExecutionMethod.SSH
        assert "Connection refused" in result.error


class TestExecuteViaSSHWithProgress:
    """Tests for _execute_via_ssh_with_progress method."""

    @pytest.mark.asyncio
    async def test_server_not_found(self, router, mock_server_service):
        """_execute_via_ssh_with_progress should return error when server not found."""
        mock_server_service.get_server.return_value = None
        callback = MagicMock()

        result = await router._execute_via_ssh_with_progress(
            "server-123", "ls", callback, 30.0
        )

        assert result.success is False
        assert result.method == ExecutionMethod.SSH
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_credentials_not_found(
        self, router, mock_server_service, mock_server
    ):
        """_execute_via_ssh_with_progress should return error when no credentials."""
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = None
        callback = MagicMock()

        result = await router._execute_via_ssh_with_progress(
            "server-123", "ls", callback, 30.0
        )

        assert result.success is False
        assert "credentials" in result.error.lower()

    @pytest.mark.asyncio
    async def test_progress_success(
        self, router, mock_server_service, mock_ssh_service, mock_server
    ):
        """_execute_via_ssh_with_progress should execute with progress callback."""
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = {"password": "secret"}
        mock_ssh_service.execute_command_with_progress.return_value = (
            True,
            "full output",
        )
        callback = MagicMock()

        result = await router._execute_via_ssh_with_progress(
            "server-123", "apt upgrade", callback, 600.0
        )

        assert result.success is True
        assert result.output == "full output"
        mock_ssh_service.execute_command_with_progress.assert_called_once()

    @pytest.mark.asyncio
    async def test_progress_calls_with_callback(
        self, router, mock_server_service, mock_ssh_service, mock_server
    ):
        """_execute_via_ssh_with_progress should pass callback to SSH service."""
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = {"password": "secret"}
        mock_ssh_service.execute_command_with_progress.return_value = (True, "output")
        callback = MagicMock()

        await router._execute_via_ssh_with_progress(
            "server-123", "cmd", callback, 300.0
        )

        call_kwargs = mock_ssh_service.execute_command_with_progress.call_args.kwargs
        assert call_kwargs["progress_callback"] is callback
        assert call_kwargs["timeout"] == 300

    @pytest.mark.asyncio
    async def test_progress_exception(
        self, router, mock_server_service, mock_ssh_service, mock_server
    ):
        """_execute_via_ssh_with_progress should handle exception."""
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = {"password": "secret"}
        mock_ssh_service.execute_command_with_progress.side_effect = Exception(
            "Network error"
        )
        callback = MagicMock()

        with patch("services.command_router.logger"):
            result = await router._execute_via_ssh_with_progress(
                "server-123", "cmd", callback, 30.0
            )

        assert result.success is False
        assert "Network error" in result.error

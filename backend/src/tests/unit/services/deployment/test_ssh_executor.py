"""
Unit tests for services/deployment/ssh_executor.py

Tests for SSHExecutor and AgentExecutor command execution classes.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestSSHExecutorInit:
    """Tests for SSHExecutor initialization."""

    def test_initializes_with_services(self):
        """Should initialize with ssh and server services."""
        from services.deployment.ssh_executor import SSHExecutor

        ssh_service = MagicMock()
        server_service = MagicMock()

        executor = SSHExecutor(ssh_service, server_service)

        assert executor.ssh_service is ssh_service
        assert executor.server_service is server_service


class TestSSHExecutorExecute:
    """Tests for SSHExecutor.execute method."""

    @pytest.fixture
    def mock_ssh_service(self):
        """Create mock SSH service."""
        service = MagicMock()
        service.execute_command = AsyncMock(return_value=(True, "output"))
        return service

    @pytest.fixture
    def mock_server_service(self):
        """Create mock server service."""
        service = MagicMock()
        server = MagicMock()
        server.host = "192.168.1.100"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        service.get_server = AsyncMock(return_value=server)
        service.get_credentials = AsyncMock(return_value={"password": "secret"})
        return service

    @pytest.fixture
    def ssh_executor(self, mock_ssh_service, mock_server_service):
        """Create SSHExecutor instance."""
        from services.deployment.ssh_executor import SSHExecutor

        return SSHExecutor(mock_ssh_service, mock_server_service)

    @pytest.mark.asyncio
    async def test_execute_success(self, ssh_executor, mock_ssh_service):
        """Should return success tuple on successful execution."""
        mock_ssh_service.execute_command.return_value = (True, "command output")

        result = await ssh_executor.execute("server-1", "echo hello")

        assert result == (0, "command output", "")

    @pytest.mark.asyncio
    async def test_execute_failure(self, ssh_executor, mock_ssh_service):
        """Should return error tuple on failed execution."""
        mock_ssh_service.execute_command.return_value = (False, "error message")

        result = await ssh_executor.execute("server-1", "bad command")

        assert result == (1, "", "error message")

    @pytest.mark.asyncio
    async def test_execute_server_not_found(self, ssh_executor, mock_server_service):
        """Should return error when server not found."""
        mock_server_service.get_server.return_value = None

        result = await ssh_executor.execute("invalid-server", "echo hello")

        assert result == (1, "", "Server not found")

    @pytest.mark.asyncio
    async def test_execute_credentials_not_found(
        self, ssh_executor, mock_server_service
    ):
        """Should return error when credentials not found."""
        mock_server_service.get_credentials.return_value = None

        result = await ssh_executor.execute("server-1", "echo hello")

        assert result == (1, "", "Could not get server credentials")

    @pytest.mark.asyncio
    async def test_execute_passes_correct_params(
        self, ssh_executor, mock_ssh_service, mock_server_service
    ):
        """Should pass correct parameters to SSH service."""
        await ssh_executor.execute("server-1", "test command", timeout=60)

        mock_ssh_service.execute_command.assert_called_once()
        call_kwargs = mock_ssh_service.execute_command.call_args[1]
        assert call_kwargs["host"] == "192.168.1.100"
        assert call_kwargs["port"] == 22
        assert call_kwargs["username"] == "admin"
        assert call_kwargs["auth_type"] == "password"
        assert call_kwargs["command"] == "test command"
        assert call_kwargs["timeout"] == 60


class TestSSHExecutorExecuteWithProgress:
    """Tests for SSHExecutor.execute_with_progress method."""

    @pytest.fixture
    def mock_ssh_service(self):
        """Create mock SSH service."""
        service = MagicMock()
        service.execute_command_with_progress = AsyncMock(return_value=(True, "output"))
        return service

    @pytest.fixture
    def mock_server_service(self):
        """Create mock server service."""
        service = MagicMock()
        server = MagicMock()
        server.host = "192.168.1.100"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="key")
        service.get_server = AsyncMock(return_value=server)
        service.get_credentials = AsyncMock(return_value={"private_key": "key-data"})
        return service

    @pytest.fixture
    def ssh_executor(self, mock_ssh_service, mock_server_service):
        """Create SSHExecutor instance."""
        from services.deployment.ssh_executor import SSHExecutor

        return SSHExecutor(mock_ssh_service, mock_server_service)

    @pytest.mark.asyncio
    async def test_execute_with_progress_success(self, ssh_executor, mock_ssh_service):
        """Should return success tuple with progress callback."""
        mock_ssh_service.execute_command_with_progress.return_value = (True, "output")
        callback = AsyncMock()

        result = await ssh_executor.execute_with_progress(
            "server-1", "long command", progress_callback=callback
        )

        assert result == (0, "output", "")

    @pytest.mark.asyncio
    async def test_execute_with_progress_failure(self, ssh_executor, mock_ssh_service):
        """Should return error tuple on failure."""
        mock_ssh_service.execute_command_with_progress.return_value = (
            False,
            "error occurred",
        )

        result = await ssh_executor.execute_with_progress("server-1", "failing command")

        assert result == (1, "", "error occurred")

    @pytest.mark.asyncio
    async def test_execute_with_progress_server_not_found(
        self, ssh_executor, mock_server_service
    ):
        """Should return error when server not found."""
        mock_server_service.get_server.return_value = None

        result = await ssh_executor.execute_with_progress("invalid-server", "command")

        assert result == (1, "", "Server not found")

    @pytest.mark.asyncio
    async def test_execute_with_progress_no_credentials(
        self, ssh_executor, mock_server_service
    ):
        """Should return error when credentials not found."""
        mock_server_service.get_credentials.return_value = None

        result = await ssh_executor.execute_with_progress("server-1", "command")

        assert result == (1, "", "Could not get server credentials")

    @pytest.mark.asyncio
    async def test_execute_with_progress_passes_callback(
        self, ssh_executor, mock_ssh_service
    ):
        """Should pass progress callback to SSH service."""
        callback = AsyncMock()

        await ssh_executor.execute_with_progress(
            "server-1", "cmd", progress_callback=callback, timeout=300
        )

        call_kwargs = mock_ssh_service.execute_command_with_progress.call_args[1]
        assert call_kwargs["progress_callback"] is callback
        assert call_kwargs["timeout"] == 300


class TestAgentExecutorInit:
    """Tests for AgentExecutor initialization."""

    def test_initializes_with_command_router(self):
        """Should initialize with command router."""
        from services.deployment.ssh_executor import AgentExecutor

        router = MagicMock()
        executor = AgentExecutor(router)

        assert executor.command_router is router


class TestAgentExecutorExecute:
    """Tests for AgentExecutor.execute method."""

    @pytest.fixture
    def mock_command_router(self):
        """Create mock command router."""
        router = MagicMock()
        result = MagicMock()
        result.success = True
        result.exit_code = 0
        result.output = "agent output"
        result.error = None
        router.execute = AsyncMock(return_value=result)
        return router

    @pytest.fixture
    def agent_executor(self, mock_command_router):
        """Create AgentExecutor instance."""
        from services.deployment.ssh_executor import AgentExecutor

        return AgentExecutor(mock_command_router)

    @pytest.mark.asyncio
    async def test_execute_success(self, agent_executor, mock_command_router):
        """Should return success tuple on successful execution."""
        result = await agent_executor.execute("server-1", "echo hello")

        assert result == (0, "agent output", "")
        mock_command_router.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_failure(self, agent_executor, mock_command_router):
        """Should return error tuple on failed execution."""
        result = MagicMock()
        result.success = False
        result.exit_code = 1
        result.output = ""
        result.error = "command failed"
        mock_command_router.execute.return_value = result

        exec_result = await agent_executor.execute("server-1", "bad command")

        assert exec_result == (1, "", "command failed")

    @pytest.mark.asyncio
    async def test_execute_uses_force_agent(self, agent_executor, mock_command_router):
        """Should force agent execution (no SSH fallback)."""
        await agent_executor.execute("server-1", "command", timeout=60)

        call_kwargs = mock_command_router.execute.call_args[1]
        assert call_kwargs["force_agent"] is True
        assert call_kwargs["server_id"] == "server-1"
        assert call_kwargs["command"] == "command"
        assert call_kwargs["timeout"] == 60.0

    @pytest.mark.asyncio
    async def test_execute_exit_code_none_success(
        self, agent_executor, mock_command_router
    ):
        """Should use 0 when exit_code is None and success is True."""
        result = MagicMock()
        result.success = True
        result.exit_code = None
        result.output = "output"
        result.error = None
        mock_command_router.execute.return_value = result

        exec_result = await agent_executor.execute("server-1", "cmd")

        assert exec_result[0] == 0

    @pytest.mark.asyncio
    async def test_execute_exit_code_none_failure(
        self, agent_executor, mock_command_router
    ):
        """Should use 1 when exit_code is None and success is False."""
        result = MagicMock()
        result.success = False
        result.exit_code = None
        result.output = "error output"
        result.error = None
        mock_command_router.execute.return_value = result

        exec_result = await agent_executor.execute("server-1", "cmd")

        assert exec_result[0] == 1
        assert exec_result[2] == "error output"

    @pytest.mark.asyncio
    async def test_execute_failure_uses_output_as_error(
        self, agent_executor, mock_command_router
    ):
        """Should use output as error when error is None."""
        result = MagicMock()
        result.success = False
        result.exit_code = 2
        result.output = "output as error"
        result.error = None
        mock_command_router.execute.return_value = result

        exec_result = await agent_executor.execute("server-1", "cmd")

        assert exec_result == (2, "", "output as error")


class TestAgentExecutorExecuteWithProgress:
    """Tests for AgentExecutor.execute_with_progress method."""

    @pytest.fixture
    def mock_command_router(self):
        """Create mock command router."""
        router = MagicMock()
        result = MagicMock()
        result.success = True
        result.exit_code = 0
        result.output = "output"
        result.error = None
        router.execute = AsyncMock(return_value=result)
        return router

    @pytest.fixture
    def agent_executor(self, mock_command_router):
        """Create AgentExecutor instance."""
        from services.deployment.ssh_executor import AgentExecutor

        return AgentExecutor(mock_command_router)

    @pytest.mark.asyncio
    async def test_execute_with_progress_calls_execute(
        self, agent_executor, mock_command_router
    ):
        """Should delegate to execute method (progress not supported)."""
        callback = AsyncMock()

        result = await agent_executor.execute_with_progress(
            "server-1", "command", progress_callback=callback, timeout=300
        )

        assert result == (0, "output", "")
        # Progress callback is ignored for agent
        mock_command_router.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_progress_ignores_callback(
        self, agent_executor, mock_command_router
    ):
        """Should ignore progress callback (not implemented for agent)."""
        callback = AsyncMock()

        await agent_executor.execute_with_progress(
            "server-1", "cmd", progress_callback=callback
        )

        # Callback should never be called
        callback.assert_not_called()

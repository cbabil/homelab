"""
Unit tests for services/command_router.py

Tests for command routing through agent or SSH.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import services.command_router as router_module
from services.command_router import (
    CommandResult,
    CommandRouter,
    ExecutionMethod,
    RoutedExecutor,
)


@pytest.fixture
def mock_agent_service():
    """Create mock agent service."""
    return AsyncMock()


@pytest.fixture
def mock_agent_manager():
    """Create mock agent manager."""
    return MagicMock()


@pytest.fixture
def mock_server_service():
    """Create mock server service."""
    return AsyncMock()


@pytest.fixture
def mock_ssh_service():
    """Create mock SSH service."""
    return AsyncMock()


@pytest.fixture
def command_router(
    mock_agent_service,
    mock_agent_manager,
    mock_server_service,
    mock_ssh_service,
):
    """Create command router with mocked services."""
    with patch.object(router_module, "logger"):
        return CommandRouter(
            agent_service=mock_agent_service,
            agent_manager=mock_agent_manager,
            server_service=mock_server_service,
            ssh_service=mock_ssh_service,
        )


class TestExecutionMethod:
    """Tests for ExecutionMethod enum."""

    def test_execution_method_values(self):
        """Should have correct enum values."""
        assert ExecutionMethod.AGENT.value == "agent"
        assert ExecutionMethod.SSH.value == "ssh"
        assert ExecutionMethod.NONE.value == "none"


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_command_result_creation(self):
        """Should create result with all fields."""
        result = CommandResult(
            success=True,
            output="hello",
            method=ExecutionMethod.SSH,
            exit_code=0,
            error=None,
            execution_time_ms=100.5,
        )

        assert result.success is True
        assert result.output == "hello"
        assert result.method == ExecutionMethod.SSH
        assert result.exit_code == 0
        assert result.execution_time_ms == 100.5

    def test_command_result_defaults(self):
        """Should have correct default values."""
        result = CommandResult(
            success=False,
            output="",
            method=ExecutionMethod.NONE,
        )

        assert result.exit_code is None
        assert result.error is None
        assert result.execution_time_ms is None


class TestCommandRouterInit:
    """Tests for CommandRouter initialization."""

    def test_init_sets_services(
        self,
        mock_agent_service,
        mock_agent_manager,
        mock_server_service,
        mock_ssh_service,
    ):
        """Should initialize with provided services."""
        with patch.object(router_module, "logger"):
            router = CommandRouter(
                agent_service=mock_agent_service,
                agent_manager=mock_agent_manager,
                server_service=mock_server_service,
                ssh_service=mock_ssh_service,
            )

            assert router._agent_service is mock_agent_service
            assert router._agent_manager is mock_agent_manager
            assert router._server_service is mock_server_service
            assert router._ssh_service is mock_ssh_service
            assert router._prefer_agent is True

    def test_init_with_prefer_agent_false(
        self,
        mock_agent_service,
        mock_agent_manager,
        mock_server_service,
        mock_ssh_service,
    ):
        """Should respect prefer_agent flag."""
        with patch.object(router_module, "logger"):
            router = CommandRouter(
                agent_service=mock_agent_service,
                agent_manager=mock_agent_manager,
                server_service=mock_server_service,
                ssh_service=mock_ssh_service,
                prefer_agent=False,
            )

            assert router._prefer_agent is False


class TestIsAgentAvailable:
    """Tests for is_agent_available method."""

    @pytest.mark.asyncio
    async def test_is_agent_available_true(
        self, command_router, mock_agent_service, mock_agent_manager
    ):
        """Should return True when agent is connected."""
        mock_agent = MagicMock()
        mock_agent.id = "agent-1"
        mock_agent_service.get_agent_by_server.return_value = mock_agent
        mock_agent_manager.is_connected.return_value = True

        result = await command_router.is_agent_available("server-1")

        assert result is True

    @pytest.mark.asyncio
    async def test_is_agent_available_no_agent(
        self, command_router, mock_agent_service
    ):
        """Should return False when no agent."""
        mock_agent_service.get_agent_by_server.return_value = None

        result = await command_router.is_agent_available("server-1")

        assert result is False

    @pytest.mark.asyncio
    async def test_is_agent_available_not_connected(
        self, command_router, mock_agent_service, mock_agent_manager
    ):
        """Should return False when agent not connected."""
        mock_agent = MagicMock()
        mock_agent.id = "agent-1"
        mock_agent_service.get_agent_by_server.return_value = mock_agent
        mock_agent_manager.is_connected.return_value = False

        result = await command_router.is_agent_available("server-1")

        assert result is False


class TestGetAvailableMethods:
    """Tests for get_available_methods method."""

    @pytest.mark.asyncio
    async def test_get_available_methods_both(
        self, command_router, mock_agent_service, mock_agent_manager, mock_server_service
    ):
        """Should return both methods when available."""
        mock_agent = MagicMock()
        mock_agent.id = "agent-1"
        mock_agent_service.get_agent_by_server.return_value = mock_agent
        mock_agent_manager.is_connected.return_value = True
        mock_server_service.get_server.return_value = MagicMock()

        result = await command_router.get_available_methods("server-1")

        assert ExecutionMethod.AGENT in result
        assert ExecutionMethod.SSH in result

    @pytest.mark.asyncio
    async def test_get_available_methods_ssh_only(
        self, command_router, mock_agent_service, mock_server_service
    ):
        """Should return only SSH when no agent."""
        mock_agent_service.get_agent_by_server.return_value = None
        mock_server_service.get_server.return_value = MagicMock()

        result = await command_router.get_available_methods("server-1")

        assert ExecutionMethod.AGENT not in result
        assert ExecutionMethod.SSH in result

    @pytest.mark.asyncio
    async def test_get_available_methods_none(
        self, command_router, mock_agent_service, mock_server_service
    ):
        """Should return empty list when nothing available."""
        mock_agent_service.get_agent_by_server.return_value = None
        mock_server_service.get_server.return_value = None

        result = await command_router.get_available_methods("server-1")

        assert len(result) == 0


class TestDetermineMethod:
    """Tests for _determine_method method."""

    @pytest.mark.asyncio
    async def test_determine_method_force_ssh(self, command_router):
        """Should return SSH when forced."""
        result = await command_router._determine_method(
            "server-1", force_ssh=True, force_agent=False
        )

        assert result == ExecutionMethod.SSH

    @pytest.mark.asyncio
    async def test_determine_method_force_agent_available(
        self, command_router, mock_agent_service, mock_agent_manager
    ):
        """Should return AGENT when forced and available."""
        mock_agent = MagicMock()
        mock_agent.id = "agent-1"
        mock_agent_service.get_agent_by_server.return_value = mock_agent
        mock_agent_manager.is_connected.return_value = True

        result = await command_router._determine_method(
            "server-1", force_ssh=False, force_agent=True
        )

        assert result == ExecutionMethod.AGENT

    @pytest.mark.asyncio
    async def test_determine_method_force_agent_unavailable(
        self, command_router, mock_agent_service
    ):
        """Should return NONE when agent forced but unavailable."""
        mock_agent_service.get_agent_by_server.return_value = None

        with patch.object(router_module, "logger"):
            result = await command_router._determine_method(
                "server-1", force_ssh=False, force_agent=True
            )

        assert result == ExecutionMethod.NONE

    @pytest.mark.asyncio
    async def test_determine_method_both_forced_prefers_agent(
        self, command_router, mock_agent_service, mock_agent_manager
    ):
        """Should prefer agent when both forced."""
        mock_agent = MagicMock()
        mock_agent.id = "agent-1"
        mock_agent_service.get_agent_by_server.return_value = mock_agent
        mock_agent_manager.is_connected.return_value = True

        with patch.object(router_module, "logger"):
            result = await command_router._determine_method(
                "server-1", force_ssh=True, force_agent=True
            )

        assert result == ExecutionMethod.AGENT

    @pytest.mark.asyncio
    async def test_determine_method_auto_prefers_agent(
        self, command_router, mock_agent_service, mock_agent_manager
    ):
        """Should prefer agent when available and prefer_agent=True."""
        mock_agent = MagicMock()
        mock_agent.id = "agent-1"
        mock_agent_service.get_agent_by_server.return_value = mock_agent
        mock_agent_manager.is_connected.return_value = True

        result = await command_router._determine_method(
            "server-1", force_ssh=False, force_agent=False
        )

        assert result == ExecutionMethod.AGENT

    @pytest.mark.asyncio
    async def test_determine_method_auto_fallback_ssh(
        self, command_router, mock_agent_service
    ):
        """Should fallback to SSH when agent not available."""
        mock_agent_service.get_agent_by_server.return_value = None

        result = await command_router._determine_method(
            "server-1", force_ssh=False, force_agent=False
        )

        assert result == ExecutionMethod.SSH


class TestGetAgentUnavailableReason:
    """Tests for _get_agent_unavailable_reason method."""

    @pytest.mark.asyncio
    async def test_reason_no_agent(self, command_router, mock_agent_service):
        """Should return installation message when no agent."""
        mock_agent_service.get_agent_by_server.return_value = None

        result = await command_router._get_agent_unavailable_reason("server-1")

        assert "not installed" in result.lower()

    @pytest.mark.asyncio
    async def test_reason_not_connected(
        self, command_router, mock_agent_service, mock_agent_manager
    ):
        """Should return connection message when not connected."""
        mock_agent = MagicMock()
        mock_agent.id = "agent-1"
        mock_agent_service.get_agent_by_server.return_value = mock_agent
        mock_agent_manager.is_connected.return_value = False

        result = await command_router._get_agent_unavailable_reason("server-1")

        assert "not connected" in result.lower()

    @pytest.mark.asyncio
    async def test_reason_error(self, command_router, mock_agent_service):
        """Should return generic message on error."""
        mock_agent_service.get_agent_by_server.side_effect = RuntimeError("DB error")

        with patch.object(router_module, "logger"):
            result = await command_router._get_agent_unavailable_reason("server-1")

        assert "not available" in result.lower()


class TestExecuteViaAgent:
    """Tests for _execute_via_agent method."""

    @pytest.mark.asyncio
    async def test_execute_via_agent_success(
        self, command_router, mock_agent_service, mock_agent_manager
    ):
        """Should execute command via agent successfully."""
        mock_agent = MagicMock()
        mock_agent.id = "agent-1"
        mock_agent_service.get_agent_by_server.return_value = mock_agent
        mock_agent_manager.is_connected.return_value = True
        mock_agent_manager.send_command = AsyncMock(
            return_value={"exit_code": 0, "stdout": "hello", "stderr": ""}
        )

        result = await command_router._execute_via_agent("server-1", "echo hello", 30)

        assert result.success is True
        assert result.output == "hello"
        assert result.method == ExecutionMethod.AGENT
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_execute_via_agent_command_failure(
        self, command_router, mock_agent_service, mock_agent_manager
    ):
        """Should handle command failure."""
        mock_agent = MagicMock()
        mock_agent.id = "agent-1"
        mock_agent_service.get_agent_by_server.return_value = mock_agent
        mock_agent_manager.is_connected.return_value = True
        mock_agent_manager.send_command = AsyncMock(
            return_value={"exit_code": 1, "stdout": "", "stderr": "command not found"}
        )

        result = await command_router._execute_via_agent("server-1", "badcmd", 30)

        assert result.success is False
        assert result.error == "command not found"
        assert result.exit_code == 1

    @pytest.mark.asyncio
    async def test_execute_via_agent_no_agent(
        self, command_router, mock_agent_service
    ):
        """Should return error when no agent."""
        mock_agent_service.get_agent_by_server.return_value = None

        result = await command_router._execute_via_agent("server-1", "echo", 30)

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_via_agent_not_connected(
        self, command_router, mock_agent_service, mock_agent_manager
    ):
        """Should return error when not connected."""
        mock_agent = MagicMock()
        mock_agent.id = "agent-1"
        mock_agent_service.get_agent_by_server.return_value = mock_agent
        mock_agent_manager.is_connected.return_value = False

        result = await command_router._execute_via_agent("server-1", "echo", 30)

        assert result.success is False
        assert "not connected" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_via_agent_timeout(
        self, command_router, mock_agent_service, mock_agent_manager
    ):
        """Should handle timeout."""
        mock_agent = MagicMock()
        mock_agent.id = "agent-1"
        mock_agent_service.get_agent_by_server.return_value = mock_agent
        mock_agent_manager.is_connected.return_value = True
        mock_agent_manager.send_command = AsyncMock(side_effect=TimeoutError())

        with patch.object(router_module, "logger"):
            result = await command_router._execute_via_agent("server-1", "sleep 100", 1)

        assert result.success is False
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_via_agent_exception(
        self, command_router, mock_agent_service, mock_agent_manager
    ):
        """Should handle exceptions."""
        mock_agent = MagicMock()
        mock_agent.id = "agent-1"
        mock_agent_service.get_agent_by_server.return_value = mock_agent
        mock_agent_manager.is_connected.return_value = True
        mock_agent_manager.send_command = AsyncMock(side_effect=RuntimeError("Network error"))

        with patch.object(router_module, "logger"):
            result = await command_router._execute_via_agent("server-1", "echo", 30)

        assert result.success is False
        assert "Network error" in result.error

    @pytest.mark.asyncio
    async def test_execute_via_agent_non_dict_result(
        self, command_router, mock_agent_service, mock_agent_manager
    ):
        """Should handle non-dict result."""
        mock_agent = MagicMock()
        mock_agent.id = "agent-1"
        mock_agent_service.get_agent_by_server.return_value = mock_agent
        mock_agent_manager.is_connected.return_value = True
        mock_agent_manager.send_command = AsyncMock(return_value="simple string")

        result = await command_router._execute_via_agent("server-1", "echo", 30)

        assert result.success is True
        assert result.output == "simple string"


class TestExecuteViaSsh:
    """Tests for _execute_via_ssh method."""

    @pytest.mark.asyncio
    async def test_execute_via_ssh_success(
        self, command_router, mock_server_service, mock_ssh_service
    ):
        """Should execute command via SSH successfully."""
        mock_server = MagicMock()
        mock_server.host = "192.168.1.100"
        mock_server.port = 22
        mock_server.username = "admin"
        mock_server.auth_type = "password"
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = "password123"
        mock_ssh_service.execute_command.return_value = (True, "hello")

        result = await command_router._execute_via_ssh("server-1", "echo hello", 30)

        assert result.success is True
        assert result.output == "hello"
        assert result.method == ExecutionMethod.SSH
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_execute_via_ssh_server_not_found(
        self, command_router, mock_server_service
    ):
        """Should return error when server not found."""
        mock_server_service.get_server.return_value = None

        result = await command_router._execute_via_ssh("server-1", "echo", 30)

        assert result.success is False
        assert "server not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_via_ssh_no_credentials(
        self, command_router, mock_server_service
    ):
        """Should return error when no credentials."""
        mock_server_service.get_server.return_value = MagicMock()
        mock_server_service.get_credentials.return_value = None

        result = await command_router._execute_via_ssh("server-1", "echo", 30)

        assert result.success is False
        assert "credentials" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_via_ssh_failure(
        self, command_router, mock_server_service, mock_ssh_service
    ):
        """Should handle command failure."""
        mock_server = MagicMock()
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = "pass"
        mock_ssh_service.execute_command.return_value = (False, "error output")

        result = await command_router._execute_via_ssh("server-1", "badcmd", 30)

        assert result.success is False
        assert result.exit_code == 1

    @pytest.mark.asyncio
    async def test_execute_via_ssh_exception(
        self, command_router, mock_server_service, mock_ssh_service
    ):
        """Should handle exceptions."""
        mock_server_service.get_server.side_effect = RuntimeError("DB error")

        with patch.object(router_module, "logger"):
            result = await command_router._execute_via_ssh("server-1", "echo", 30)

        assert result.success is False
        assert "DB error" in result.error


class TestExecuteViaSshWithProgress:
    """Tests for _execute_via_ssh_with_progress method."""

    @pytest.mark.asyncio
    async def test_execute_with_progress_success(
        self, command_router, mock_server_service, mock_ssh_service
    ):
        """Should execute with progress callback."""
        mock_server = MagicMock()
        mock_server.host = "192.168.1.100"
        mock_server.port = 22
        mock_server.username = "admin"
        mock_server.auth_type = "password"
        mock_server_service.get_server.return_value = mock_server
        mock_server_service.get_credentials.return_value = "password123"
        mock_ssh_service.execute_command_with_progress.return_value = (True, "done")

        callback = MagicMock()

        result = await command_router._execute_via_ssh_with_progress(
            "server-1", "apt update", callback, 300
        )

        assert result.success is True
        assert result.output == "done"
        mock_ssh_service.execute_command_with_progress.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_progress_server_not_found(
        self, command_router, mock_server_service
    ):
        """Should return error when server not found."""
        mock_server_service.get_server.return_value = None

        result = await command_router._execute_via_ssh_with_progress(
            "server-1", "apt update", MagicMock(), 300
        )

        assert result.success is False
        assert "server not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_with_progress_no_credentials(
        self, command_router, mock_server_service
    ):
        """Should return error when no credentials."""
        mock_server_service.get_server.return_value = MagicMock()
        mock_server_service.get_credentials.return_value = None

        result = await command_router._execute_via_ssh_with_progress(
            "server-1", "apt update", MagicMock(), 300
        )

        assert result.success is False
        assert "credentials" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_with_progress_exception(
        self, command_router, mock_server_service, mock_ssh_service
    ):
        """Should handle exceptions."""
        mock_server_service.get_server.return_value = MagicMock()
        mock_server_service.get_credentials.return_value = "pass"
        mock_ssh_service.execute_command_with_progress.side_effect = RuntimeError(
            "Connection error"
        )

        with patch.object(router_module, "logger"):
            result = await command_router._execute_via_ssh_with_progress(
                "server-1", "apt update", MagicMock(), 300
            )

        assert result.success is False
        assert "Connection error" in result.error


class TestExecute:
    """Tests for execute method."""

    @pytest.mark.asyncio
    async def test_execute_via_agent(self, command_router):
        """Should execute via agent when available."""
        with (
            patch.object(
                command_router,
                "_determine_method",
                new_callable=AsyncMock,
                return_value=ExecutionMethod.AGENT,
            ),
            patch.object(
                command_router,
                "_execute_via_agent",
                new_callable=AsyncMock,
            ) as mock_exec,
            patch.object(router_module, "logger"),
        ):
            mock_exec.return_value = CommandResult(
                success=True, output="hello", method=ExecutionMethod.AGENT
            )

            result = await command_router.execute("server-1", "echo hello")

            assert result.success is True
            assert result.method == ExecutionMethod.AGENT
            assert result.execution_time_ms is not None
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_via_ssh(self, command_router):
        """Should execute via SSH when agent not available."""
        with (
            patch.object(
                command_router,
                "_determine_method",
                new_callable=AsyncMock,
                return_value=ExecutionMethod.SSH,
            ),
            patch.object(
                command_router,
                "_execute_via_ssh",
                new_callable=AsyncMock,
            ) as mock_exec,
            patch.object(router_module, "logger"),
        ):
            mock_exec.return_value = CommandResult(
                success=True, output="hello", method=ExecutionMethod.SSH
            )

            result = await command_router.execute("server-1", "echo hello")

            assert result.success is True
            assert result.method == ExecutionMethod.SSH
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_none_available(self, command_router):
        """Should return error when no method available."""
        with (
            patch.object(
                command_router,
                "_determine_method",
                new_callable=AsyncMock,
                return_value=ExecutionMethod.NONE,
            ),
            patch.object(
                command_router,
                "_get_agent_unavailable_reason",
                new_callable=AsyncMock,
                return_value="Agent not available",
            ),
        ):
            result = await command_router.execute(
                "server-1", "echo hello", force_agent=True
            )

            assert result.success is False
            assert result.method == ExecutionMethod.NONE
            assert "not available" in result.error.lower()


class TestExecuteWithProgress:
    """Tests for execute_with_progress method."""

    @pytest.mark.asyncio
    async def test_execute_with_progress(self, command_router):
        """Should execute with progress."""
        with patch.object(
            command_router,
            "_execute_via_ssh_with_progress",
            new_callable=AsyncMock,
        ) as mock_exec:
            mock_exec.return_value = CommandResult(
                success=True, output="done", method=ExecutionMethod.SSH
            )
            callback = MagicMock()

            result = await command_router.execute_with_progress(
                "server-1", "apt update", callback, timeout=600
            )

            assert result.success is True
            assert result.execution_time_ms is not None
            mock_exec.assert_called_once()


class TestRoutedExecutorInit:
    """Tests for RoutedExecutor initialization."""

    def test_init_sets_router(self, command_router):
        """Should initialize with router."""
        executor = RoutedExecutor(command_router)

        assert executor._router is command_router


class TestRoutedExecutorExecute:
    """Tests for RoutedExecutor execute method."""

    @pytest.mark.asyncio
    async def test_execute_returns_tuple(self, command_router):
        """Should return (success, output) tuple."""
        executor = RoutedExecutor(command_router)

        with patch.object(
            command_router,
            "execute",
            new_callable=AsyncMock,
            return_value=CommandResult(
                success=True, output="hello", method=ExecutionMethod.SSH
            ),
        ):
            success, output = await executor.execute("server-1", "echo hello")

            assert success is True
            assert output == "hello"

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self, command_router):
        """Should pass timeout to router."""
        executor = RoutedExecutor(command_router)

        with patch.object(
            command_router,
            "execute",
            new_callable=AsyncMock,
            return_value=CommandResult(
                success=True, output="", method=ExecutionMethod.SSH
            ),
        ) as mock_exec:
            await executor.execute("server-1", "echo", timeout=60.0)

            mock_exec.assert_called_once_with("server-1", "echo", 60.0)


class TestRoutedExecutorExecuteWithExitCode:
    """Tests for RoutedExecutor execute_with_exit_code method."""

    @pytest.mark.asyncio
    async def test_execute_with_exit_code_success(self, command_router):
        """Should return (exit_code, stdout, stderr) tuple."""
        executor = RoutedExecutor(command_router)

        with patch.object(
            command_router,
            "execute",
            new_callable=AsyncMock,
            return_value=CommandResult(
                success=True,
                output="hello",
                method=ExecutionMethod.SSH,
                exit_code=0,
                error=None,
            ),
        ):
            exit_code, stdout, stderr = await executor.execute_with_exit_code(
                "server-1", "echo hello"
            )

            assert exit_code == 0
            assert stdout == "hello"
            assert stderr == ""

    @pytest.mark.asyncio
    async def test_execute_with_exit_code_failure(self, command_router):
        """Should return error in stderr on failure."""
        executor = RoutedExecutor(command_router)

        with patch.object(
            command_router,
            "execute",
            new_callable=AsyncMock,
            return_value=CommandResult(
                success=False,
                output="",
                method=ExecutionMethod.SSH,
                exit_code=1,
                error="command not found",
            ),
        ):
            exit_code, stdout, stderr = await executor.execute_with_exit_code(
                "server-1", "badcmd"
            )

            assert exit_code == 1
            assert stdout == ""
            assert stderr == "command not found"

    @pytest.mark.asyncio
    async def test_execute_with_exit_code_none_defaults(self, command_router):
        """Should default exit_code based on success."""
        executor = RoutedExecutor(command_router)

        with patch.object(
            command_router,
            "execute",
            new_callable=AsyncMock,
            return_value=CommandResult(
                success=False,
                output="",
                method=ExecutionMethod.SSH,
                exit_code=None,  # No explicit exit code
                error="error message",
            ),
        ):
            exit_code, stdout, stderr = await executor.execute_with_exit_code(
                "server-1", "badcmd"
            )

            assert exit_code == 1  # Default to 1 for failure
            assert stderr == "error message"

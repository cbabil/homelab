"""
Unit tests for services/command_router.py

Tests command routing between agent and SSH execution methods.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.command_router import (
    CommandResult,
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


class TestExecutionMethodEnum:
    """Tests for ExecutionMethod enum."""

    def test_agent_value(self):
        """ExecutionMethod.AGENT should have value 'agent'."""
        assert ExecutionMethod.AGENT.value == "agent"

    def test_ssh_value(self):
        """ExecutionMethod.SSH should have value 'ssh'."""
        assert ExecutionMethod.SSH.value == "ssh"

    def test_none_value(self):
        """ExecutionMethod.NONE should have value 'none'."""
        assert ExecutionMethod.NONE.value == "none"


class TestCommandResultDataclass:
    """Tests for CommandResult dataclass."""

    def test_required_fields(self):
        """CommandResult should require success, output, and method."""
        result = CommandResult(
            success=True,
            output="test output",
            method=ExecutionMethod.SSH,
        )
        assert result.success is True
        assert result.output == "test output"
        assert result.method == ExecutionMethod.SSH

    def test_optional_fields_default_none(self):
        """CommandResult optional fields should default to None."""
        result = CommandResult(
            success=True,
            output="",
            method=ExecutionMethod.AGENT,
        )
        assert result.exit_code is None
        assert result.error is None
        assert result.execution_time_ms is None

    def test_all_fields(self):
        """CommandResult should store all provided fields."""
        result = CommandResult(
            success=False,
            output="error output",
            method=ExecutionMethod.SSH,
            exit_code=1,
            error="Command failed",
            execution_time_ms=150.5,
        )
        assert result.success is False
        assert result.output == "error output"
        assert result.method == ExecutionMethod.SSH
        assert result.exit_code == 1
        assert result.error == "Command failed"
        assert result.execution_time_ms == 150.5


class TestCommandRouterInit:
    """Tests for CommandRouter initialization."""

    def test_init_stores_services(
        self,
        mock_agent_service,
        mock_agent_manager,
        mock_server_service,
        mock_ssh_service,
    ):
        """CommandRouter should store all service references."""
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

    def test_init_prefer_agent_default(
        self,
        mock_agent_service,
        mock_agent_manager,
        mock_server_service,
        mock_ssh_service,
    ):
        """CommandRouter should prefer agent by default."""
        router = CommandRouter(
            agent_service=mock_agent_service,
            agent_manager=mock_agent_manager,
            server_service=mock_server_service,
            ssh_service=mock_ssh_service,
        )
        assert router._prefer_agent is True

    def test_init_prefer_agent_false(
        self,
        mock_agent_service,
        mock_agent_manager,
        mock_server_service,
        mock_ssh_service,
    ):
        """CommandRouter should accept prefer_agent=False."""
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
    async def test_agent_available_returns_true(
        self, router, mock_agent_service, mock_agent_manager
    ):
        """is_agent_available should return True when agent is connected."""
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = True

        result = await router.is_agent_available("server-456")

        assert result is True
        mock_agent_service.get_agent_by_server.assert_called_once_with("server-456")
        mock_agent_manager.is_connected.assert_called_once_with("agent-123")

    @pytest.mark.asyncio
    async def test_agent_not_available_no_agent(self, router, mock_agent_service):
        """is_agent_available should return False when no agent exists."""
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=None)

        result = await router.is_agent_available("server-456")

        assert result is False

    @pytest.mark.asyncio
    async def test_agent_not_available_disconnected(
        self, router, mock_agent_service, mock_agent_manager
    ):
        """is_agent_available should return False when agent is disconnected."""
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = False

        result = await router.is_agent_available("server-456")

        assert result is False


class TestGetAvailableMethods:
    """Tests for get_available_methods method."""

    @pytest.mark.asyncio
    async def test_both_methods_available(
        self, router, mock_agent_service, mock_agent_manager, mock_server_service
    ):
        """get_available_methods should return both when agent and server exist."""
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = True
        mock_server_service.get_server.return_value = MagicMock()

        result = await router.get_available_methods("server-456")

        assert ExecutionMethod.AGENT in result
        assert ExecutionMethod.SSH in result

    @pytest.mark.asyncio
    async def test_only_ssh_available(
        self, router, mock_agent_service, mock_server_service
    ):
        """get_available_methods should return only SSH when no agent."""
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=None)
        mock_server_service.get_server.return_value = MagicMock()

        result = await router.get_available_methods("server-456")

        assert ExecutionMethod.SSH in result
        assert ExecutionMethod.AGENT not in result

    @pytest.mark.asyncio
    async def test_no_methods_available(
        self, router, mock_agent_service, mock_server_service
    ):
        """get_available_methods should return empty when no server exists."""
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=None)
        mock_server_service.get_server.return_value = None

        result = await router.get_available_methods("server-456")

        assert result == []


class TestDetermineMethod:
    """Tests for _determine_method method."""

    @pytest.mark.asyncio
    async def test_force_ssh(self, router):
        """_determine_method should return SSH when forced."""
        result = await router._determine_method(
            "server-123", force_ssh=True, force_agent=False
        )
        assert result == ExecutionMethod.SSH

    @pytest.mark.asyncio
    async def test_force_agent_available(
        self, router, mock_agent_service, mock_agent_manager
    ):
        """_determine_method should return AGENT when forced and available."""
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = True

        result = await router._determine_method(
            "server-123", force_ssh=False, force_agent=True
        )

        assert result == ExecutionMethod.AGENT

    @pytest.mark.asyncio
    async def test_force_agent_not_available(self, router, mock_agent_service):
        """_determine_method should return NONE when agent forced but not available."""
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=None)

        with patch("services.command_router.logger"):
            result = await router._determine_method(
                "server-123", force_ssh=False, force_agent=True
            )

        assert result == ExecutionMethod.NONE

    @pytest.mark.asyncio
    async def test_both_force_flags_prefers_agent(
        self, router, mock_agent_service, mock_agent_manager
    ):
        """_determine_method should prefer agent when both force flags set."""
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = True

        with patch("services.command_router.logger"):
            result = await router._determine_method(
                "server-123", force_ssh=True, force_agent=True
            )

        assert result == ExecutionMethod.AGENT

    @pytest.mark.asyncio
    async def test_auto_select_prefers_agent(
        self, router, mock_agent_service, mock_agent_manager
    ):
        """_determine_method should prefer agent when available and prefer_agent=True."""
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = True

        result = await router._determine_method(
            "server-123", force_ssh=False, force_agent=False
        )

        assert result == ExecutionMethod.AGENT

    @pytest.mark.asyncio
    async def test_auto_select_falls_back_to_ssh(self, router, mock_agent_service):
        """_determine_method should fall back to SSH when agent not available."""
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=None)

        result = await router._determine_method(
            "server-123", force_ssh=False, force_agent=False
        )

        assert result == ExecutionMethod.SSH

    @pytest.mark.asyncio
    async def test_auto_select_uses_ssh_when_prefer_agent_false(
        self,
        mock_agent_service,
        mock_agent_manager,
        mock_server_service,
        mock_ssh_service,
    ):
        """_determine_method should use SSH when prefer_agent=False."""
        router = CommandRouter(
            agent_service=mock_agent_service,
            agent_manager=mock_agent_manager,
            server_service=mock_server_service,
            ssh_service=mock_ssh_service,
            prefer_agent=False,
        )
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = True

        result = await router._determine_method(
            "server-123", force_ssh=False, force_agent=False
        )

        assert result == ExecutionMethod.SSH


class TestGetAgentUnavailableReason:
    """Tests for _get_agent_unavailable_reason method."""

    @pytest.mark.asyncio
    async def test_agent_not_installed(self, router, mock_agent_service):
        """_get_agent_unavailable_reason should return install message when no agent."""
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=None)

        result = await router._get_agent_unavailable_reason("server-123")

        assert "not installed" in result.lower()
        assert "install" in result.lower()

    @pytest.mark.asyncio
    async def test_agent_not_connected(
        self, router, mock_agent_service, mock_agent_manager
    ):
        """_get_agent_unavailable_reason should return connect message when disconnected."""
        mock_agent = MagicMock(id="agent-123")
        mock_agent_service.get_agent_by_server = AsyncMock(return_value=mock_agent)
        mock_agent_manager.is_connected.return_value = False

        result = await router._get_agent_unavailable_reason("server-123")

        assert "not connected" in result.lower()
        assert "running" in result.lower()

    @pytest.mark.asyncio
    async def test_handles_exception(self, router, mock_agent_service):
        """_get_agent_unavailable_reason should return generic message on error."""
        mock_agent_service.get_agent_by_server = AsyncMock(
            side_effect=Exception("DB error")
        )

        with patch("services.command_router.logger"):
            result = await router._get_agent_unavailable_reason("server-123")

        assert "not available" in result.lower()

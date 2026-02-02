"""Tests for AgentExecutor."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.deployment import DeploymentService, DeploymentError, SSHExecutor, AgentExecutor
from services.deployment.ssh_executor import AgentExecutor as DirectAgentExecutor
from services.command_router import CommandResult, ExecutionMethod


class TestImports:
    """Test that all deployment imports work correctly."""

    def test_import_deployment_service(self):
        """Should import DeploymentService."""
        assert DeploymentService is not None

    def test_import_deployment_error(self):
        """Should import DeploymentError."""
        assert DeploymentError is not None

    def test_import_ssh_executor(self):
        """Should import SSHExecutor."""
        assert SSHExecutor is not None

    def test_import_agent_executor(self):
        """Should import AgentExecutor."""
        assert AgentExecutor is not None

    def test_agent_executor_same_class(self):
        """AgentExecutor from package should be same as direct import."""
        assert AgentExecutor is DirectAgentExecutor


class TestAgentExecutor:
    """Tests for AgentExecutor."""

    @pytest.fixture
    def mock_command_router(self):
        """Create mock command router."""
        router = MagicMock()
        router.execute = AsyncMock()
        return router

    @pytest.fixture
    def agent_executor(self, mock_command_router):
        """Create AgentExecutor with mock router."""
        return AgentExecutor(mock_command_router)

    @pytest.mark.asyncio
    async def test_execute_success(self, agent_executor, mock_command_router):
        """Should execute command via agent successfully."""
        mock_command_router.execute.return_value = CommandResult(
            success=True,
            output="command output",
            method=ExecutionMethod.AGENT,
            exit_code=0,
        )

        exit_code, stdout, stderr = await agent_executor.execute(
            server_id="server-123",
            command="echo hello",
            timeout=30,
        )

        assert exit_code == 0
        assert stdout == "command output"
        assert stderr == ""
        mock_command_router.execute.assert_called_once_with(
            server_id="server-123",
            command="echo hello",
            timeout=30.0,
            force_agent=True,
        )

    @pytest.mark.asyncio
    async def test_execute_agent_not_connected(self, agent_executor, mock_command_router):
        """Should return error when agent not connected."""
        mock_command_router.execute.return_value = CommandResult(
            success=False,
            output="",
            method=ExecutionMethod.AGENT,
            error="Agent not connected",
        )

        exit_code, stdout, stderr = await agent_executor.execute(
            server_id="server-123",
            command="echo hello",
        )

        assert exit_code == 1
        assert stdout == ""
        assert stderr == "Agent not connected"

    @pytest.mark.asyncio
    async def test_execute_agent_not_found(self, agent_executor, mock_command_router):
        """Should return error when agent not found for server."""
        mock_command_router.execute.return_value = CommandResult(
            success=False,
            output="",
            method=ExecutionMethod.AGENT,
            error="Agent not found for server",
        )

        exit_code, stdout, stderr = await agent_executor.execute(
            server_id="server-456",
            command="ls -la",
        )

        assert exit_code == 1
        assert stderr == "Agent not found for server"

    @pytest.mark.asyncio
    async def test_execute_command_timeout(self, agent_executor, mock_command_router):
        """Should return error on command timeout."""
        mock_command_router.execute.return_value = CommandResult(
            success=False,
            output="",
            method=ExecutionMethod.AGENT,
            error="Command timed out",
        )

        exit_code, stdout, stderr = await agent_executor.execute(
            server_id="server-123",
            command="sleep 1000",
            timeout=5,
        )

        assert exit_code == 1
        assert stderr == "Command timed out"

    @pytest.mark.asyncio
    async def test_execute_with_progress_delegates_to_execute(
        self, agent_executor, mock_command_router
    ):
        """execute_with_progress should delegate to execute (no streaming yet)."""
        mock_command_router.execute.return_value = CommandResult(
            success=True,
            output="output",
            method=ExecutionMethod.AGENT,
            exit_code=0,
        )

        progress_callback = MagicMock()
        exit_code, stdout, stderr = await agent_executor.execute_with_progress(
            server_id="server-123",
            command="docker pull image",
            progress_callback=progress_callback,
            timeout=300,
        )

        assert exit_code == 0
        assert stdout == "output"
        # Progress callback is ignored (agent streaming not implemented)
        mock_command_router.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_force_agent_flag_always_set(self, agent_executor, mock_command_router):
        """Should always set force_agent=True (no SSH fallback)."""
        mock_command_router.execute.return_value = CommandResult(
            success=True,
            output="",
            method=ExecutionMethod.AGENT,
        )

        await agent_executor.execute("srv", "cmd")

        call_kwargs = mock_command_router.execute.call_args.kwargs
        assert call_kwargs.get("force_agent") is True


class TestAgentStartupCleanup:
    """Tests for agent status cleanup on server startup."""

    @pytest.fixture
    def mock_agent_service(self):
        """Create a mock agent service."""
        from unittest.mock import patch
        from models.agent import Agent, AgentStatus

        # Mock the database service
        mock_db = MagicMock()
        mock_db.db_path = "/tmp/test.db"

        with patch("services.agent_service.DatabaseService", return_value=mock_db):
            from services.agent_service import AgentService
            service = AgentService(db_service=mock_db)
            return service

    @pytest.mark.asyncio
    async def test_reset_stale_agent_statuses_resets_connected_agents(
        self, mock_agent_service
    ):
        """Should reset CONNECTED agents to DISCONNECTED on startup."""
        from models.agent import Agent, AgentStatus, AgentUpdate
        from datetime import datetime, UTC

        # Create mock agents with different statuses
        mock_agents = [
            Agent(
                id="agent-1",
                server_id="server-1",
                status=AgentStatus.CONNECTED,
                registered_at=datetime.now(UTC),
            ),
            Agent(
                id="agent-2",
                server_id="server-2",
                status=AgentStatus.DISCONNECTED,
                registered_at=datetime.now(UTC),
            ),
            Agent(
                id="agent-3",
                server_id="server-3",
                status=AgentStatus.CONNECTED,
                registered_at=datetime.now(UTC),
            ),
        ]

        # Mock the database calls (import happens inside the method)
        with patch("services.database.DatabaseConnection"), \
             patch("services.database.AgentDatabaseService") as MockAgentDB:
            mock_agent_db = MagicMock()
            mock_agent_db.list_all_agents = AsyncMock(return_value=mock_agents)
            mock_agent_db.update_agent = AsyncMock()
            MockAgentDB.return_value = mock_agent_db

            reset_count = await mock_agent_service.reset_stale_agent_statuses()

            # Should reset 2 agents (agent-1 and agent-3 were CONNECTED)
            assert reset_count == 2
            # Should have called update_agent twice
            assert mock_agent_db.update_agent.call_count == 2

    @pytest.mark.asyncio
    async def test_reset_stale_agent_statuses_no_connected_agents(
        self, mock_agent_service
    ):
        """Should return 0 when no agents are CONNECTED."""
        from models.agent import Agent, AgentStatus
        from datetime import datetime, UTC

        mock_agents = [
            Agent(
                id="agent-1",
                server_id="server-1",
                status=AgentStatus.DISCONNECTED,
                registered_at=datetime.now(UTC),
            ),
        ]

        with patch("services.database.DatabaseConnection"), \
             patch("services.database.AgentDatabaseService") as MockAgentDB:
            mock_agent_db = MagicMock()
            mock_agent_db.list_all_agents = AsyncMock(return_value=mock_agents)
            mock_agent_db.update_agent = AsyncMock()
            MockAgentDB.return_value = mock_agent_db

            reset_count = await mock_agent_service.reset_stale_agent_statuses()

            assert reset_count == 0
            mock_agent_db.update_agent.assert_not_called()

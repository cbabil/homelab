"""
Agent Tools Unit Tests - Agent Operations

Tests for install_agent, get_agent_status, revoke_agent_token, uninstall_agent.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.agent import AgentStatus
from tools.agent.tools import AgentTools


class TestInstallAgent:
    """Tests for install_agent method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "agent_service": MagicMock(),
            "agent_manager": MagicMock(),
            "ssh_service": MagicMock(),
            "server_service": MagicMock(),
            "packager": MagicMock(),
        }

    @pytest.fixture
    def agent_tools(self, mock_services):
        """Create AgentTools instance."""
        mock_services["packager"].package.return_value = "BASE64=="
        mock_services["packager"].get_version.return_value = "1.0.0"

        with patch("tools.agent.tools.logger"):
            return AgentTools(
                mock_services["agent_service"],
                mock_services["agent_manager"],
                mock_services["ssh_service"],
                mock_services["server_service"],
                mock_services["packager"],
            )

    @pytest.mark.asyncio
    async def test_install_agent_server_not_found(self, agent_tools, mock_services):
        """Test install_agent when server not found."""
        mock_services["server_service"].get_server = AsyncMock(return_value=None)

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.install_agent("server-123")

        assert result["success"] is False
        assert result["error"] == "SERVER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_install_agent_docker_not_installed(self, agent_tools, mock_services):
        """Test install_agent when Docker not installed on server."""
        server = MagicMock()
        server.name = "test-server"
        server.system_info = MagicMock()
        server.system_info.docker_version = "not installed"
        mock_services["server_service"].get_server = AsyncMock(return_value=server)

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.install_agent("server-123")

        assert result["success"] is False
        assert result["error"] == "DOCKER_NOT_INSTALLED"

    @pytest.mark.asyncio
    async def test_install_agent_docker_version_none(self, agent_tools, mock_services):
        """Test install_agent when Docker version is None."""
        server = MagicMock()
        server.name = "test-server"
        server.system_info = MagicMock()
        server.system_info.docker_version = None
        mock_services["server_service"].get_server = AsyncMock(return_value=server)

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.install_agent("server-123")

        assert result["success"] is False
        assert result["error"] == "DOCKER_NOT_INSTALLED"

    @pytest.mark.asyncio
    async def test_install_agent_no_system_info(self, agent_tools, mock_services):
        """Test install_agent when server has no system_info."""
        server = MagicMock()
        server.name = "test-server"
        server.system_info = None
        mock_services["server_service"].get_server = AsyncMock(return_value=server)

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.install_agent("server-123")

        assert result["success"] is False
        assert result["error"] == "DOCKER_NOT_INSTALLED"

    @pytest.mark.asyncio
    async def test_install_agent_credentials_not_found(
        self, agent_tools, mock_services
    ):
        """Test install_agent when credentials not found."""
        server = MagicMock()
        server.name = "test-server"
        server.system_info = MagicMock()
        server.system_info.docker_version = "24.0.0"
        mock_services["server_service"].get_server = AsyncMock(return_value=server)
        mock_services["server_service"].get_credentials = AsyncMock(return_value=None)

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.install_agent("server-123")

        assert result["success"] is False
        assert result["error"] == "CREDENTIALS_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_install_agent_deploy_failed(self, agent_tools, mock_services):
        """Test install_agent when SSH deployment fails."""
        server = MagicMock()
        server.name = "test-server"
        server.host = "192.168.1.1"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        server.system_info = MagicMock()
        server.system_info.docker_version = "24.0.0"

        agent = MagicMock()
        agent.id = "agent-123"
        reg_code = MagicMock()
        reg_code.code = "validcode123"

        mock_services["server_service"].get_server = AsyncMock(return_value=server)
        mock_services["server_service"].get_credentials = AsyncMock(
            return_value="password123"
        )
        mock_services["agent_service"].create_agent = AsyncMock(
            return_value=(agent, reg_code)
        )
        mock_services["ssh_service"].execute_command = AsyncMock(
            return_value=(False, "Connection refused")
        )

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.install_agent("server-123")

        assert result["success"] is False
        assert result["error"] == "DEPLOY_FAILED"
        assert "Connection refused" in result["message"]

    @pytest.mark.asyncio
    async def test_install_agent_success(self, agent_tools, mock_services):
        """Test successful agent installation."""
        server = MagicMock()
        server.name = "test-server"
        server.host = "192.168.1.1"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        server.system_info = MagicMock()
        server.system_info.docker_version = "24.0.0"

        agent = MagicMock()
        agent.id = "agent-123"
        reg_code = MagicMock()
        reg_code.code = "validcode123"

        mock_services["server_service"].get_server = AsyncMock(return_value=server)
        mock_services["server_service"].get_credentials = AsyncMock(
            return_value="password123"
        )
        mock_services["server_service"].update_server_system_info = AsyncMock()
        mock_services["agent_service"].create_agent = AsyncMock(
            return_value=(agent, reg_code)
        )
        mock_services["ssh_service"].execute_command = AsyncMock(
            return_value=(True, "Agent installed!")
        )

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.install_agent("server-123")

        assert result["success"] is True
        assert result["data"]["agent_id"] == "agent-123"
        assert result["data"]["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_install_agent_exception(self, agent_tools, mock_services):
        """Test install_agent handles exceptions."""
        mock_services["server_service"].get_server = AsyncMock(
            side_effect=Exception("Database error")
        )

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.install_agent("server-123")

        assert result["success"] is False
        assert result["error"] == "INSTALL_AGENT_ERROR"
        assert "Database error" in result["message"]


class TestGetAgentStatus:
    """Tests for get_agent_status method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "agent_service": MagicMock(),
            "agent_manager": MagicMock(),
            "ssh_service": MagicMock(),
            "server_service": MagicMock(),
        }

    @pytest.fixture
    def agent_tools(self, mock_services):
        """Create AgentTools instance."""
        with patch("tools.agent.tools.logger"):
            return AgentTools(
                mock_services["agent_service"],
                mock_services["agent_manager"],
                mock_services["ssh_service"],
                mock_services["server_service"],
            )

    @pytest.mark.asyncio
    async def test_get_agent_status_no_agent(self, agent_tools, mock_services):
        """Test get_agent_status when no agent exists."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=None
        )

        result = await agent_tools.get_agent_status("server-123")

        assert result["success"] is True
        assert result["data"] is None
        assert "No agent found" in result["message"]

    @pytest.mark.asyncio
    async def test_get_agent_status_connected(self, agent_tools, mock_services):
        """Test get_agent_status when agent is connected."""
        agent = MagicMock()
        agent.id = "agent-123"
        agent.server_id = "server-123"
        agent.status = AgentStatus.CONNECTED
        agent.version = "1.0.0"
        agent.last_seen = datetime.now(UTC)
        agent.registered_at = datetime.now(UTC)

        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True

        result = await agent_tools.get_agent_status("server-123")

        assert result["success"] is True
        assert result["data"]["is_connected"] is True
        assert result["data"]["id"] == "agent-123"

    @pytest.mark.asyncio
    async def test_get_agent_status_disconnected(self, agent_tools, mock_services):
        """Test get_agent_status when agent is not connected."""
        agent = MagicMock()
        agent.id = "agent-123"
        agent.server_id = "server-123"
        agent.status = AgentStatus.DISCONNECTED
        agent.version = "1.0.0"
        agent.last_seen = None
        agent.registered_at = datetime.now(UTC)

        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = False

        result = await agent_tools.get_agent_status("server-123")

        assert result["success"] is True
        assert result["data"]["is_connected"] is False

    @pytest.mark.asyncio
    async def test_get_agent_status_exception(self, agent_tools, mock_services):
        """Test get_agent_status handles exceptions."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            side_effect=Exception("Service error")
        )

        result = await agent_tools.get_agent_status("server-123")

        assert result["success"] is False
        assert result["error"] == "GET_AGENT_STATUS_ERROR"


class TestRevokeAgentToken:
    """Tests for revoke_agent_token method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "agent_service": MagicMock(),
            "agent_manager": MagicMock(),
            "ssh_service": MagicMock(),
            "server_service": MagicMock(),
        }

    @pytest.fixture
    def agent_tools(self, mock_services):
        """Create AgentTools instance."""
        with patch("tools.agent.tools.logger"):
            return AgentTools(
                mock_services["agent_service"],
                mock_services["agent_manager"],
                mock_services["ssh_service"],
                mock_services["server_service"],
            )

    @pytest.mark.asyncio
    async def test_revoke_agent_token_no_agent(self, agent_tools, mock_services):
        """Test revoke_agent_token when no agent exists."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=None
        )

        result = await agent_tools.revoke_agent_token("server-123")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_revoke_agent_token_success_connected(
        self, agent_tools, mock_services
    ):
        """Test successful token revocation for connected agent."""
        agent = MagicMock()
        agent.id = "agent-123"

        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_manager"].unregister_connection = AsyncMock()
        mock_services["agent_service"].revoke_agent_token = AsyncMock(return_value=True)

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.revoke_agent_token("server-123")

        assert result["success"] is True
        assert result["data"]["agent_id"] == "agent-123"
        mock_services["agent_manager"].unregister_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_agent_token_success_not_connected(
        self, agent_tools, mock_services
    ):
        """Test successful token revocation for disconnected agent."""
        agent = MagicMock()
        agent.id = "agent-123"

        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = False
        mock_services["agent_service"].revoke_agent_token = AsyncMock(return_value=True)

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.revoke_agent_token("server-123")

        assert result["success"] is True
        mock_services["agent_manager"].unregister_connection.assert_not_called()

    @pytest.mark.asyncio
    async def test_revoke_agent_token_failed(self, agent_tools, mock_services):
        """Test token revocation failure."""
        agent = MagicMock()
        agent.id = "agent-123"

        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = False
        mock_services["agent_service"].revoke_agent_token = AsyncMock(
            return_value=False
        )

        result = await agent_tools.revoke_agent_token("server-123")

        assert result["success"] is False
        assert result["error"] == "REVOKE_TOKEN_ERROR"

    @pytest.mark.asyncio
    async def test_revoke_agent_token_exception(self, agent_tools, mock_services):
        """Test revoke_agent_token handles exceptions."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            side_effect=Exception("DB error")
        )

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.revoke_agent_token("server-123")

        assert result["success"] is False
        assert result["error"] == "REVOKE_TOKEN_ERROR"


class TestUninstallAgent:
    """Tests for uninstall_agent method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "agent_service": MagicMock(),
            "agent_manager": MagicMock(),
            "ssh_service": MagicMock(),
            "server_service": MagicMock(),
        }

    @pytest.fixture
    def agent_tools(self, mock_services):
        """Create AgentTools instance."""
        with patch("tools.agent.tools.logger"):
            return AgentTools(
                mock_services["agent_service"],
                mock_services["agent_manager"],
                mock_services["ssh_service"],
                mock_services["server_service"],
            )

    @pytest.mark.asyncio
    async def test_uninstall_agent_server_not_found(self, agent_tools, mock_services):
        """Test uninstall_agent when server not found."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=None
        )
        mock_services["server_service"].get_server = AsyncMock(return_value=None)

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.uninstall_agent("server-123")

        assert result["success"] is False
        assert result["error"] == "SERVER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_uninstall_agent_credentials_not_found(
        self, agent_tools, mock_services
    ):
        """Test uninstall_agent when credentials not found."""
        agent = MagicMock()
        agent.id = "agent-123"
        server = MagicMock()
        server.name = "test-server"

        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = False
        mock_services["server_service"].get_server = AsyncMock(return_value=server)
        mock_services["server_service"].get_credentials = AsyncMock(return_value=None)

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.uninstall_agent("server-123")

        assert result["success"] is False
        assert result["error"] == "CREDENTIALS_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_uninstall_agent_success(self, agent_tools, mock_services):
        """Test successful agent uninstallation."""
        agent = MagicMock()
        agent.id = "agent-123"
        server = MagicMock()
        server.name = "test-server"
        server.host = "192.168.1.1"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        server.system_info = MagicMock()
        server.system_info.model_dump.return_value = {}

        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_manager"].unregister_connection = AsyncMock()
        mock_services["server_service"].get_server = AsyncMock(return_value=server)
        mock_services["server_service"].get_credentials = AsyncMock(return_value="pass")
        mock_services["server_service"].update_server_system_info = AsyncMock()
        mock_services["ssh_service"].execute_command = AsyncMock(
            return_value=(True, "OK")
        )
        mock_services["agent_service"].delete_agent = AsyncMock(return_value=True)

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.uninstall_agent("server-123")

        assert result["success"] is True
        assert result["data"]["agent_id"] == "agent-123"

    @pytest.mark.asyncio
    async def test_uninstall_agent_no_agent_record(self, agent_tools, mock_services):
        """Test uninstalling when no agent record exists (orphaned container)."""
        server = MagicMock()
        server.name = "test-server"
        server.host = "192.168.1.1"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        server.system_info = None

        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=None
        )
        mock_services["server_service"].get_server = AsyncMock(return_value=server)
        mock_services["server_service"].get_credentials = AsyncMock(return_value="pass")
        mock_services["ssh_service"].execute_command = AsyncMock(
            return_value=(True, "OK")
        )

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.uninstall_agent("server-123")

        assert result["success"] is True
        assert result["data"]["agent_id"] is None

    @pytest.mark.asyncio
    async def test_uninstall_agent_ssh_failure_continues(
        self, agent_tools, mock_services
    ):
        """Test uninstall continues even if SSH command fails."""
        agent = MagicMock()
        agent.id = "agent-123"
        server = MagicMock()
        server.name = "test-server"
        server.host = "192.168.1.1"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        server.system_info = None

        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = False
        mock_services["server_service"].get_server = AsyncMock(return_value=server)
        mock_services["server_service"].get_credentials = AsyncMock(return_value="pass")
        mock_services["ssh_service"].execute_command = AsyncMock(
            return_value=(False, "SSH error")
        )
        mock_services["agent_service"].delete_agent = AsyncMock(return_value=True)

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.uninstall_agent("server-123")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_uninstall_agent_delete_record_fails(
        self, agent_tools, mock_services
    ):
        """Test uninstall continues even if delete_agent fails."""
        agent = MagicMock()
        agent.id = "agent-123"
        server = MagicMock()
        server.name = "test-server"
        server.host = "192.168.1.1"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        server.system_info = None

        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = False
        mock_services["server_service"].get_server = AsyncMock(return_value=server)
        mock_services["server_service"].get_credentials = AsyncMock(return_value="pass")
        mock_services["ssh_service"].execute_command = AsyncMock(
            return_value=(True, "OK")
        )
        mock_services["agent_service"].delete_agent = AsyncMock(return_value=False)

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            with patch("tools.agent.lifecycle.logger") as mock_logger:
                result = await agent_tools.uninstall_agent("server-123")

        assert result["success"] is True
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_uninstall_agent_exception(self, agent_tools, mock_services):
        """Test uninstall_agent handles exceptions."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            side_effect=Exception("DB error")
        )

        with patch("tools.agent.lifecycle.log_event", new_callable=AsyncMock):
            result = await agent_tools.uninstall_agent("server-123")

        assert result["success"] is False
        assert result["error"] == "UNINSTALL_AGENT_ERROR"

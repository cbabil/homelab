"""Tests for server MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tools.server.tools import ServerTools
from models.server import ServerConnection, AuthType, ServerStatus
from models.agent import Agent, AgentStatus


@pytest.fixture
def mock_services():
    """Create mock services."""
    ssh_service = MagicMock()
    ssh_service.test_connection = AsyncMock(return_value=(True, "Connected", {"os": "Linux"}))

    server_service = MagicMock()
    server_service.add_server = AsyncMock()
    server_service.get_server = AsyncMock()
    server_service.get_server_by_connection = AsyncMock(return_value=None)
    server_service.get_all_servers = AsyncMock()
    server_service.update_server = AsyncMock()
    server_service.delete_server = AsyncMock()
    server_service.get_credentials = AsyncMock()
    server_service.update_server_status = AsyncMock()
    server_service.update_server_system_info = AsyncMock(return_value=True)

    agent_service = MagicMock()
    agent_service.get_agent_by_server = AsyncMock(return_value=None)
    agent_service.delete_agent = AsyncMock(return_value=True)
    agent_service._get_agent_db = MagicMock()

    return ssh_service, server_service, agent_service


@pytest.fixture
def server_tools(mock_services):
    """Create server tools with mocks."""
    ssh_service, server_service, agent_service = mock_services
    return ServerTools(ssh_service, server_service, agent_service)


class TestAddServer:
    """Tests for add_server tool."""

    @pytest.mark.asyncio
    async def test_add_server_success(self, server_tools, mock_services):
        """Should add server successfully."""
        ssh_service, server_service, agent_service = mock_services
        server_service.add_server.return_value = ServerConnection(
            id="server-123",
            name="Test Server",
            host="192.168.1.100",
            port=22,
            username="admin",
            auth_type=AuthType.PASSWORD,
            status=ServerStatus.DISCONNECTED,
            created_at="2025-01-01T00:00:00Z"
        )

        result = await server_tools.add_server(
            name="Test Server",
            host="192.168.1.100",
            port=22,
            username="admin",
            auth_type="password",
            password="secret123"
        )

        assert result["success"] is True
        assert "server-123" in str(result["data"])


class TestGetServer:
    """Tests for get_server tool."""

    @pytest.mark.asyncio
    async def test_get_server_found(self, server_tools, mock_services):
        """Should return server when found."""
        _, server_service, _ = mock_services
        server_service.get_server.return_value = ServerConnection(
            id="server-123",
            name="Test Server",
            host="192.168.1.100",
            port=22,
            username="admin",
            auth_type=AuthType.PASSWORD,
            status=ServerStatus.CONNECTED,
            created_at="2025-01-01T00:00:00Z"
        )

        result = await server_tools.get_server(server_id="server-123")

        assert result["success"] is True
        assert result["data"]["name"] == "Test Server"

    @pytest.mark.asyncio
    async def test_get_server_not_found(self, server_tools, mock_services):
        """Should return error when not found."""
        _, server_service, _ = mock_services
        server_service.get_server.return_value = None

        result = await server_tools.get_server(server_id="nonexistent")

        assert result["success"] is False
        assert result["error"] == "SERVER_NOT_FOUND"


class TestListServers:
    """Tests for list_servers tool."""

    @pytest.mark.asyncio
    async def test_list_servers(self, server_tools, mock_services):
        """Should list all servers."""
        _, server_service, _ = mock_services
        server_service.get_all_servers.return_value = [
            ServerConnection(
                id="server-1", name="Server 1", host="192.168.1.100",
                port=22, username="admin", auth_type=AuthType.PASSWORD,
                status=ServerStatus.CONNECTED, created_at="2025-01-01T00:00:00Z"
            ),
            ServerConnection(
                id="server-2", name="Server 2", host="192.168.1.101",
                port=22, username="root", auth_type=AuthType.KEY,
                status=ServerStatus.DISCONNECTED, created_at="2025-01-01T00:00:00Z"
            )
        ]

        result = await server_tools.list_servers()

        assert result["success"] is True
        assert len(result["data"]["servers"]) == 2


class TestDeleteServer:
    """Tests for delete_server tool."""

    @pytest.mark.asyncio
    async def test_delete_server_success(self, server_tools, mock_services):
        """Should delete server successfully."""
        _, server_service, _ = mock_services
        server_service.delete_server.return_value = True

        result = await server_tools.delete_server(server_id="server-123")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_server_not_found(self, server_tools, mock_services):
        """Should return error when server not found."""
        _, server_service, _ = mock_services
        server_service.delete_server.return_value = False

        result = await server_tools.delete_server(server_id="nonexistent")

        assert result["success"] is False


class TestTestConnection:
    """Tests for test_connection tool."""

    @pytest.mark.asyncio
    async def test_connection_success(self, server_tools, mock_services):
        """Should test connection successfully."""
        ssh_service, server_service, agent_service = mock_services
        server_service.get_server.return_value = ServerConnection(
            id="server-123", name="Test Server", host="192.168.1.100",
            port=22, username="admin", auth_type=AuthType.PASSWORD,
            status=ServerStatus.DISCONNECTED, created_at="2025-01-01T00:00:00Z"
        )
        server_service.get_credentials.return_value = {"password": "secret"}
        ssh_service.test_connection.return_value = (
            True, "Connected", {"os": "Linux", "agent_status": "not running"}
        )

        result = await server_tools.test_connection(server_id="server-123")

        assert result["success"] is True
        assert result["system_info"]["os"] == "Linux"


class TestAgentStatusSync:
    """Tests for agent status synchronization during test_connection."""

    @pytest.mark.asyncio
    async def test_agent_running_no_db_record(self, server_tools, mock_services):
        """When agent container running but no DB record - no error, awaits WS connection."""
        ssh_service, server_service, agent_service = mock_services
        server_service.get_server.return_value = ServerConnection(
            id="server-123", name="Test Server", host="192.168.1.100",
            port=22, username="admin", auth_type=AuthType.PASSWORD,
            status=ServerStatus.DISCONNECTED, created_at="2025-01-01T00:00:00Z"
        )
        server_service.get_credentials.return_value = {"password": "secret"}
        ssh_service.test_connection.return_value = (
            True, "Connected", {
                "os": "Linux",
                "docker_version": "24.0.0",
                "agent_status": "running",
                "agent_version": "1.0.0"
            }
        )
        agent_service.get_agent_by_server.return_value = None

        result = await server_tools.test_connection(server_id="server-123")

        assert result["success"] is True
        assert result["agent_installed"] is True
        # No DB record to update
        agent_service._get_agent_db.assert_not_called()

    @pytest.mark.asyncio
    async def test_agent_not_running_no_db_record(self, server_tools, mock_services):
        """When agent container not running and no DB record - show Install."""
        ssh_service, server_service, agent_service = mock_services
        server_service.get_server.return_value = ServerConnection(
            id="server-123", name="Test Server", host="192.168.1.100",
            port=22, username="admin", auth_type=AuthType.PASSWORD,
            status=ServerStatus.DISCONNECTED, created_at="2025-01-01T00:00:00Z"
        )
        server_service.get_credentials.return_value = {"password": "secret"}
        ssh_service.test_connection.return_value = (
            True, "Connected", {
                "os": "Linux",
                "docker_version": "24.0.0",
                "agent_status": "not running",
            }
        )
        agent_service.get_agent_by_server.return_value = None

        result = await server_tools.test_connection(server_id="server-123")

        assert result["success"] is True
        assert result["agent_installed"] is False
        # No DB record to update
        agent_service._get_agent_db.assert_not_called()

    @pytest.mark.asyncio
    async def test_agent_not_running_with_connected_db_record(self, server_tools, mock_services):
        """When container removed but DB says CONNECTED - update to DISCONNECTED."""
        ssh_service, server_service, agent_service = mock_services
        server_service.get_server.return_value = ServerConnection(
            id="server-123", name="Test Server", host="192.168.1.100",
            port=22, username="admin", auth_type=AuthType.PASSWORD,
            status=ServerStatus.DISCONNECTED, created_at="2025-01-01T00:00:00Z"
        )
        server_service.get_credentials.return_value = {"password": "secret"}
        ssh_service.test_connection.return_value = (
            True, "Connected", {
                "os": "Linux",
                "docker_version": "24.0.0",
                "agent_status": "not running",
            }
        )
        # DB record says CONNECTED but container is gone
        mock_agent = MagicMock()
        mock_agent.id = "agent-123"
        mock_agent.status = AgentStatus.CONNECTED
        agent_service.get_agent_by_server.return_value = mock_agent

        mock_agent_db = MagicMock()
        mock_agent_db.update_agent = AsyncMock()
        agent_service._get_agent_db.return_value = mock_agent_db

        result = await server_tools.test_connection(server_id="server-123")

        assert result["success"] is True
        assert result["agent_installed"] is False
        # Should update DB record to DISCONNECTED
        mock_agent_db.update_agent.assert_called_once()
        call_args = mock_agent_db.update_agent.call_args
        assert call_args[0][0] == "agent-123"
        assert call_args[0][1].status == AgentStatus.DISCONNECTED

    @pytest.mark.asyncio
    async def test_agent_not_running_with_pending_db_record(self, server_tools, mock_services):
        """When container removed but DB says PENDING - update to DISCONNECTED."""
        ssh_service, server_service, agent_service = mock_services
        server_service.get_server.return_value = ServerConnection(
            id="server-123", name="Test Server", host="192.168.1.100",
            port=22, username="admin", auth_type=AuthType.PASSWORD,
            status=ServerStatus.DISCONNECTED, created_at="2025-01-01T00:00:00Z"
        )
        server_service.get_credentials.return_value = {"password": "secret"}
        ssh_service.test_connection.return_value = (
            True, "Connected", {
                "os": "Linux",
                "docker_version": "24.0.0",
                "agent_status": "not running",
            }
        )
        # DB record says PENDING but container is gone
        mock_agent = MagicMock()
        mock_agent.id = "agent-456"
        mock_agent.status = AgentStatus.PENDING
        agent_service.get_agent_by_server.return_value = mock_agent

        mock_agent_db = MagicMock()
        mock_agent_db.update_agent = AsyncMock()
        agent_service._get_agent_db.return_value = mock_agent_db

        result = await server_tools.test_connection(server_id="server-123")

        assert result["success"] is True
        # Should update to DISCONNECTED
        mock_agent_db.update_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_not_running_already_disconnected(self, server_tools, mock_services):
        """When container not running and DB already DISCONNECTED - no update needed."""
        ssh_service, server_service, agent_service = mock_services
        server_service.get_server.return_value = ServerConnection(
            id="server-123", name="Test Server", host="192.168.1.100",
            port=22, username="admin", auth_type=AuthType.PASSWORD,
            status=ServerStatus.DISCONNECTED, created_at="2025-01-01T00:00:00Z"
        )
        server_service.get_credentials.return_value = {"password": "secret"}
        ssh_service.test_connection.return_value = (
            True, "Connected", {
                "os": "Linux",
                "docker_version": "24.0.0",
                "agent_status": "not running",
            }
        )
        # DB record already DISCONNECTED
        mock_agent = MagicMock()
        mock_agent.id = "agent-789"
        mock_agent.status = AgentStatus.DISCONNECTED
        agent_service.get_agent_by_server.return_value = mock_agent

        result = await server_tools.test_connection(server_id="server-123")

        assert result["success"] is True
        # No update needed - already disconnected
        agent_service._get_agent_db.assert_not_called()

    @pytest.mark.asyncio
    async def test_agent_running_with_disconnected_db_record(self, server_tools, mock_services):
        """When container running but DB says DISCONNECTED - await WS reconnection."""
        ssh_service, server_service, agent_service = mock_services
        server_service.get_server.return_value = ServerConnection(
            id="server-123", name="Test Server", host="192.168.1.100",
            port=22, username="admin", auth_type=AuthType.PASSWORD,
            status=ServerStatus.DISCONNECTED, created_at="2025-01-01T00:00:00Z"
        )
        server_service.get_credentials.return_value = {"password": "secret"}
        ssh_service.test_connection.return_value = (
            True, "Connected", {
                "os": "Linux",
                "docker_version": "24.0.0",
                "agent_status": "running",
                "agent_version": "1.0.0"
            }
        )
        # DB record says DISCONNECTED but container is running
        mock_agent = MagicMock()
        mock_agent.id = "agent-abc"
        mock_agent.status = AgentStatus.DISCONNECTED
        agent_service.get_agent_by_server.return_value = mock_agent

        result = await server_tools.test_connection(server_id="server-123")

        assert result["success"] is True
        assert result["agent_installed"] is True
        # Don't update - let WebSocket handle reconnection
        agent_service._get_agent_db.assert_not_called()

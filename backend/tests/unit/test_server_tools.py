"""Tests for server MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tools.server_tools import ServerTools
from models.server import ServerConnection, AuthType, ServerStatus


@pytest.fixture
def mock_services():
    """Create mock services."""
    ssh_service = MagicMock()
    ssh_service.test_connection = AsyncMock(return_value=(True, "Connected", {"os": "Linux"}))

    server_service = MagicMock()
    server_service.add_server = AsyncMock()
    server_service.get_server = AsyncMock()
    server_service.get_all_servers = AsyncMock()
    server_service.update_server = AsyncMock()
    server_service.delete_server = AsyncMock()
    server_service.get_credentials = AsyncMock()
    server_service.update_server_status = AsyncMock()

    return ssh_service, server_service


@pytest.fixture
def server_tools(mock_services):
    """Create server tools with mocks."""
    ssh_service, server_service = mock_services
    return ServerTools(ssh_service, server_service)


class TestAddServer:
    """Tests for add_server tool."""

    @pytest.mark.asyncio
    async def test_add_server_success(self, server_tools, mock_services):
        """Should add server successfully."""
        ssh_service, server_service = mock_services
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
        _, server_service = mock_services
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
        _, server_service = mock_services
        server_service.get_server.return_value = None

        result = await server_tools.get_server(server_id="nonexistent")

        assert result["success"] is False
        assert result["error"] == "SERVER_NOT_FOUND"


class TestListServers:
    """Tests for list_servers tool."""

    @pytest.mark.asyncio
    async def test_list_servers(self, server_tools, mock_services):
        """Should list all servers."""
        _, server_service = mock_services
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
        _, server_service = mock_services
        server_service.delete_server.return_value = True

        result = await server_tools.delete_server(server_id="server-123")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_server_not_found(self, server_tools, mock_services):
        """Should return error when server not found."""
        _, server_service = mock_services
        server_service.delete_server.return_value = False

        result = await server_tools.delete_server(server_id="nonexistent")

        assert result["success"] is False


class TestTestConnection:
    """Tests for test_connection tool."""

    @pytest.mark.asyncio
    async def test_connection_success(self, server_tools, mock_services):
        """Should test connection successfully."""
        ssh_service, server_service = mock_services
        server_service.get_server.return_value = ServerConnection(
            id="server-123", name="Test Server", host="192.168.1.100",
            port=22, username="admin", auth_type=AuthType.PASSWORD,
            status=ServerStatus.DISCONNECTED, created_at="2025-01-01T00:00:00Z"
        )
        server_service.get_credentials.return_value = {"password": "secret"}

        result = await server_tools.test_connection(server_id="server-123")

        assert result["success"] is True
        assert "system_info" in result["data"]

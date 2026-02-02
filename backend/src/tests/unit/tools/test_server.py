"""
Server Tools Unit Tests

Tests for server management tools: add_server, get_server, list_servers,
update_server, delete_server, test_connection.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestServerTools:
    """Tests for server management tools."""

    @pytest.fixture
    def mock_ssh_service(self):
        """Create mock SSH service."""
        service = MagicMock()
        service.test_connection = AsyncMock(return_value=(
            True,
            "Connected",
            {"os": "Ubuntu 22.04", "docker_version": "24.0.0"}
        ))
        service.execute_command = AsyncMock(return_value=(True, "success"))
        return service

    @pytest.fixture
    def mock_server_service(self):
        """Create mock server service."""
        service = MagicMock()
        service.add_server = AsyncMock()
        service.get_server = AsyncMock()
        service.get_all_servers = AsyncMock(return_value=[])
        service.update_server = AsyncMock(return_value=True)
        service.delete_server = AsyncMock(return_value=True)
        service.get_credentials = AsyncMock(return_value={"password": "secret"})
        service.update_server_status = AsyncMock()
        service.update_server_system_info = AsyncMock()
        return service

    @pytest.fixture
    def mock_agent_service(self):
        """Create mock agent service."""
        service = MagicMock()
        service.get_agent_status = AsyncMock(return_value=None)
        return service

    @pytest.fixture
    def mock_server(self):
        """Create a mock server object."""
        server = MagicMock()
        server.id = "server-123"
        server.name = "Test Server"
        server.host = "192.168.1.100"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        server.docker_installed = True
        server.model_dump = MagicMock(return_value={
            "id": "server-123",
            "name": "Test Server",
            "host": "192.168.1.100",
            "port": 22,
            "username": "admin",
            "docker_installed": True
        })
        return server

    @pytest.fixture
    def server_tools(self, mock_ssh_service, mock_server_service, mock_agent_service):
        """Create ServerTools instance."""
        from tools.server.tools import ServerTools
        return ServerTools(mock_ssh_service, mock_server_service, mock_agent_service)


class TestAddServer:
    """Tests for the add_server tool."""

    @pytest.fixture
    def mock_ssh_service(self):
        service = MagicMock()
        return service

    @pytest.fixture
    def mock_server_service(self):
        service = MagicMock()
        return service

    @pytest.fixture
    def mock_agent_service(self):
        service = MagicMock()
        return service

    @pytest.fixture
    def mock_server(self):
        server = MagicMock()
        server.id = "server-new"
        server.name = "New Server"
        server.host = "10.0.0.1"
        server.docker_installed = False
        server.model_dump = MagicMock(return_value={
            "id": "server-new",
            "name": "New Server",
            "host": "10.0.0.1"
        })
        return server

    @pytest.mark.asyncio
    async def test_add_server_success(
        self, mock_ssh_service, mock_server_service, mock_agent_service, mock_server
    ):
        """Test adding a server successfully."""
        from tools.server.tools import ServerTools

        mock_server_service.get_server_by_connection = AsyncMock(return_value=None)
        mock_server_service.add_server = AsyncMock(return_value=mock_server)
        mock_server_service.get_server = AsyncMock(return_value=mock_server)
        mock_server_service.update_server_system_info = AsyncMock()

        tools = ServerTools(mock_ssh_service, mock_server_service, mock_agent_service)

        with patch('tools.server.tools.log_event', new_callable=AsyncMock):
            result = await tools.add_server(
                name="New Server",
                host="10.0.0.1",
                port=22,
                username="admin",
                auth_type="password",
                password="secret123"
            )

        assert result["success"] is True
        assert result["data"]["name"] == "New Server"

    @pytest.mark.asyncio
    async def test_add_server_failure(
        self, mock_ssh_service, mock_server_service, mock_agent_service
    ):
        """Test adding a server that fails."""
        from tools.server.tools import ServerTools

        mock_server_service.get_server_by_connection = AsyncMock(return_value=None)
        mock_server_service.add_server = AsyncMock(return_value=None)

        tools = ServerTools(mock_ssh_service, mock_server_service, mock_agent_service)

        with patch('tools.server.tools.log_event', new_callable=AsyncMock):
            result = await tools.add_server(
                name="Bad Server",
                host="invalid",
                port=22,
                username="admin",
                auth_type="password",
                password="secret"
            )

        assert result["success"] is False
        assert result["error"] == "ADD_SERVER_ERROR"


class TestGetServer:
    """Tests for the get_server tool."""

    @pytest.fixture
    def mock_ssh_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_server_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_agent_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_server(self):
        server = MagicMock()
        server.id = "server-123"
        server.name = "Test Server"
        server.model_dump = MagicMock(return_value={
            "id": "server-123",
            "name": "Test Server"
        })
        return server

    @pytest.mark.asyncio
    async def test_get_server_found(
        self, mock_ssh_service, mock_server_service, mock_agent_service, mock_server
    ):
        """Test getting an existing server."""
        from tools.server.tools import ServerTools

        mock_server_service.get_server = AsyncMock(return_value=mock_server)
        tools = ServerTools(mock_ssh_service, mock_server_service, mock_agent_service)

        result = await tools.get_server("server-123")

        assert result["success"] is True
        assert result["data"]["id"] == "server-123"

    @pytest.mark.asyncio
    async def test_get_server_not_found(
        self, mock_ssh_service, mock_server_service, mock_agent_service
    ):
        """Test getting a non-existent server."""
        from tools.server.tools import ServerTools

        mock_server_service.get_server = AsyncMock(return_value=None)
        tools = ServerTools(mock_ssh_service, mock_server_service, mock_agent_service)

        result = await tools.get_server("nonexistent")

        assert result["success"] is False
        assert result["error"] == "SERVER_NOT_FOUND"


class TestListServers:
    """Tests for the list_servers tool."""

    @pytest.fixture
    def mock_ssh_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_server_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_agent_service(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_list_servers_empty(
        self, mock_ssh_service, mock_server_service, mock_agent_service
    ):
        """Test listing servers when none exist."""
        from tools.server.tools import ServerTools

        mock_server_service.get_all_servers = AsyncMock(return_value=[])
        tools = ServerTools(mock_ssh_service, mock_server_service, mock_agent_service)

        result = await tools.list_servers()

        assert result["success"] is True
        assert result["data"]["servers"] == []
        assert "0 servers" in result["message"]

    @pytest.mark.asyncio
    async def test_list_servers_multiple(
        self, mock_ssh_service, mock_server_service, mock_agent_service
    ):
        """Test listing multiple servers."""
        from tools.server.tools import ServerTools

        server1 = MagicMock()
        server1.model_dump = MagicMock(return_value={"id": "srv-1", "name": "Server 1"})
        server2 = MagicMock()
        server2.model_dump = MagicMock(return_value={"id": "srv-2", "name": "Server 2"})

        mock_server_service.get_all_servers = AsyncMock(return_value=[server1, server2])
        tools = ServerTools(mock_ssh_service, mock_server_service, mock_agent_service)

        result = await tools.list_servers()

        assert result["success"] is True
        assert len(result["data"]["servers"]) == 2


class TestUpdateServer:
    """Tests for the update_server tool."""

    @pytest.fixture
    def mock_ssh_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_server_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_agent_service(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_update_server_success(
        self, mock_ssh_service, mock_server_service, mock_agent_service
    ):
        """Test updating a server successfully."""
        from tools.server.tools import ServerTools

        mock_server_service.update_server = AsyncMock(return_value=True)
        tools = ServerTools(mock_ssh_service, mock_server_service, mock_agent_service)

        with patch('tools.server.tools.log_event', new_callable=AsyncMock):
            result = await tools.update_server(
                server_id="server-123",
                name="Updated Server"
            )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_update_server_not_found(
        self, mock_ssh_service, mock_server_service, mock_agent_service
    ):
        """Test updating a non-existent server."""
        from tools.server.tools import ServerTools

        mock_server_service.update_server = AsyncMock(return_value=False)
        tools = ServerTools(mock_ssh_service, mock_server_service, mock_agent_service)

        result = await tools.update_server(
            server_id="nonexistent",
            name="New Name"
        )

        assert result["success"] is False
        assert result["error"] == "SERVER_NOT_FOUND"


class TestDeleteServer:
    """Tests for the delete_server tool."""

    @pytest.fixture
    def mock_ssh_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_server_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_agent_service(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_delete_server_success(
        self, mock_ssh_service, mock_server_service, mock_agent_service
    ):
        """Test deleting a server successfully."""
        from tools.server.tools import ServerTools

        mock_server = MagicMock()
        mock_server.name = "Test Server"
        mock_server_service.get_server = AsyncMock(return_value=mock_server)
        mock_server_service.delete_server = AsyncMock(return_value=True)
        tools = ServerTools(mock_ssh_service, mock_server_service, mock_agent_service)

        with patch('tools.server.tools.log_event', new_callable=AsyncMock):
            result = await tools.delete_server("server-123")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_server_not_found(
        self, mock_ssh_service, mock_server_service, mock_agent_service
    ):
        """Test deleting a non-existent server."""
        from tools.server.tools import ServerTools

        mock_server_service.get_server = AsyncMock(return_value=None)
        mock_server_service.delete_server = AsyncMock(return_value=False)
        tools = ServerTools(mock_ssh_service, mock_server_service, mock_agent_service)

        with patch('tools.server.tools.log_event', new_callable=AsyncMock):
            result = await tools.delete_server("nonexistent")

        assert result["success"] is False
        assert result["error"] == "DELETE_SERVER_ERROR"


class TestTestConnection:
    """Tests for the test_connection tool."""

    @pytest.fixture
    def mock_ssh_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_server_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_agent_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_server(self):
        server = MagicMock()
        server.id = "server-123"
        server.name = "Test Server"
        server.host = "192.168.1.100"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        return server

    @pytest.mark.asyncio
    async def test_test_connection_success(
        self, mock_ssh_service, mock_server_service, mock_agent_service, mock_server
    ):
        """Test successful connection test."""
        from tools.server.tools import ServerTools

        mock_server_service.get_server = AsyncMock(return_value=mock_server)
        mock_server_service.get_credentials = AsyncMock(return_value={"password": "secret"})
        mock_server_service.update_server_status = AsyncMock()
        mock_server_service.update_server_system_info = AsyncMock()

        mock_ssh_service.test_connection = AsyncMock(return_value=(
            True,
            "Connected",
            {"os": "Ubuntu 22.04", "docker_version": "24.0.0"}
        ))

        mock_agent_service.get_agent_by_server = AsyncMock(return_value=None)

        tools = ServerTools(
            mock_ssh_service, mock_server_service, mock_agent_service
        )

        with patch('tools.server.tools.log_event', new_callable=AsyncMock):
            result = await tools.test_connection("server-123")

        assert result["success"] is True
        assert result["system_info"]["os"] == "Ubuntu 22.04"

    @pytest.mark.asyncio
    async def test_test_connection_server_not_found(
        self, mock_ssh_service, mock_server_service, mock_agent_service
    ):
        """Test connection when server doesn't exist."""
        from tools.server.tools import ServerTools

        mock_server_service.get_server = AsyncMock(return_value=None)
        tools = ServerTools(
            mock_ssh_service, mock_server_service, mock_agent_service
        )

        result = await tools.test_connection("nonexistent")

        assert result["success"] is False
        assert result["error"] == "SERVER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_test_connection_failed(
        self, mock_ssh_service, mock_server_service, mock_agent_service, mock_server
    ):
        """Test failed connection."""
        from tools.server.tools import ServerTools

        mock_server_service.get_server = AsyncMock(return_value=mock_server)
        mock_server_service.get_credentials = AsyncMock(return_value={"password": "secret"})
        mock_server_service.update_server_status = AsyncMock()

        mock_ssh_service.test_connection = AsyncMock(return_value=(
            False,
            "Connection refused",
            None
        ))

        tools = ServerTools(
            mock_ssh_service, mock_server_service, mock_agent_service
        )

        with patch('tools.server.tools.log_event', new_callable=AsyncMock):
            result = await tools.test_connection("server-123")

        assert result["success"] is False
        assert result["error"] == "CONNECTION_FAILED"

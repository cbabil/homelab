"""
Server Tools Unit Tests - Additional Methods

Tests for update_server, delete_server, test_connection, execute_command,
get_execution_methods, update_server_status, and exception handlers.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from tools.server.tools import ServerTools


class TestAddServerExisting:
    """Tests for add_server with existing server."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "ssh": MagicMock(),
            "server": MagicMock(),
            "agent": MagicMock(),
        }

    @pytest.fixture
    def server_tools(self, mock_services):
        """Create ServerTools instance."""
        with patch("tools.server.tools.logger"):
            return ServerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["agent"],
            )

    @pytest.mark.asyncio
    async def test_update_existing_server(self, server_tools, mock_services):
        """Test add_server updates existing server."""
        existing_server = MagicMock()
        existing_server.id = "server-existing"
        mock_services["server"].get_server_by_connection = AsyncMock(
            return_value=existing_server
        )
        mock_services["server"].update_credentials = AsyncMock()
        mock_services["server"].update_server = AsyncMock()

        updated_server = MagicMock()
        updated_server.model_dump = MagicMock(return_value={"id": "server-existing"})
        mock_services["server"].get_server = AsyncMock(return_value=updated_server)

        with patch("tools.server.tools.log_event", new_callable=AsyncMock):
            result = await server_tools.add_server(
                name="Updated Server",
                host="192.168.1.1",
                port=22,
                username="admin",
                auth_type="password",
                password="newpass",
            )

        assert result["success"] is True
        assert result["was_existing"] is True

    @pytest.mark.asyncio
    async def test_add_server_with_system_info(self, server_tools, mock_services):
        """Test add_server persists system_info."""
        mock_services["server"].get_server_by_connection = AsyncMock(return_value=None)
        server = MagicMock()
        server.docker_installed = True
        server.model_dump = MagicMock(return_value={"id": "server-new"})
        mock_services["server"].add_server = AsyncMock(return_value=server)
        mock_services["server"].update_server_system_info = AsyncMock()
        mock_services["server"].get_server = AsyncMock(return_value=server)

        with patch("tools.server.tools.log_event", new_callable=AsyncMock):
            result = await server_tools.add_server(
                name="New Server",
                host="192.168.1.1",
                port=22,
                username="admin",
                auth_type="key",
                private_key="-----BEGIN RSA-----\ntest\n-----END RSA-----",
                system_info={"os": "Ubuntu 22.04"},
            )

        assert result["success"] is True
        mock_services["server"].update_server_system_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_server_exception(self, server_tools, mock_services):
        """Test add_server handles exceptions."""
        mock_services["server"].get_server_by_connection = AsyncMock(
            side_effect=Exception("DB error")
        )

        with patch("tools.server.tools.log_event", new_callable=AsyncMock):
            result = await server_tools.add_server(
                name="Server",
                host="192.168.1.1",
                port=22,
                username="admin",
                auth_type="password",
                password="pass",
            )

        assert result["success"] is False
        assert result["error"] == "ADD_SERVER_ERROR"


class TestGetServerExceptions:
    """Tests for get_server exception handling."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "ssh": MagicMock(),
            "server": MagicMock(),
            "agent": MagicMock(),
        }

    @pytest.fixture
    def server_tools(self, mock_services):
        """Create ServerTools instance."""
        with patch("tools.server.tools.logger"):
            return ServerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["agent"],
            )

    @pytest.mark.asyncio
    async def test_get_server_exception(self, server_tools, mock_services):
        """Test get_server handles exceptions."""
        mock_services["server"].get_server = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await server_tools.get_server("server-123")

        assert result["success"] is False
        assert result["error"] == "GET_SERVER_ERROR"


class TestListServersExceptions:
    """Tests for list_servers exception handling."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "ssh": MagicMock(),
            "server": MagicMock(),
            "agent": MagicMock(),
        }

    @pytest.fixture
    def server_tools(self, mock_services):
        """Create ServerTools instance."""
        with patch("tools.server.tools.logger"):
            return ServerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["agent"],
            )

    @pytest.mark.asyncio
    async def test_list_servers_exception(self, server_tools, mock_services):
        """Test list_servers handles exceptions."""
        mock_services["server"].get_all_servers = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await server_tools.list_servers()

        assert result["success"] is False
        assert result["error"] == "LIST_SERVERS_ERROR"


class TestUpdateServerExceptions:
    """Tests for update_server exception handling."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "ssh": MagicMock(),
            "server": MagicMock(),
            "agent": MagicMock(),
        }

    @pytest.fixture
    def server_tools(self, mock_services):
        """Create ServerTools instance."""
        with patch("tools.server.tools.logger"):
            return ServerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["agent"],
            )

    @pytest.mark.asyncio
    async def test_update_server_exception(self, server_tools, mock_services):
        """Test update_server handles exceptions."""
        mock_services["server"].update_server = AsyncMock(
            side_effect=Exception("DB error")
        )

        with patch("tools.server.tools.log_event", new_callable=AsyncMock):
            result = await server_tools.update_server(
                server_id="server-123",
                name="Updated Name",
            )

        assert result["success"] is False
        assert result["error"] == "UPDATE_SERVER_ERROR"


class TestDeleteServerExceptions:
    """Tests for delete_server exception handling."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "ssh": MagicMock(),
            "server": MagicMock(),
            "agent": MagicMock(),
        }

    @pytest.fixture
    def server_tools(self, mock_services):
        """Create ServerTools instance."""
        with patch("tools.server.tools.logger"):
            return ServerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["agent"],
            )

    @pytest.mark.asyncio
    async def test_delete_server_exception(self, server_tools, mock_services):
        """Test delete_server handles exceptions."""
        mock_services["server"].get_server = AsyncMock(
            side_effect=Exception("DB error")
        )

        with patch("tools.server.tools.log_event", new_callable=AsyncMock):
            result = await server_tools.delete_server("server-123")

        assert result["success"] is False
        assert result["error"] == "DELETE_SERVER_ERROR"


class TestTestConnectionAdvanced:
    """Tests for test_connection advanced scenarios."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "ssh": MagicMock(),
            "server": MagicMock(),
            "agent": MagicMock(),
        }

    @pytest.fixture
    def mock_server(self):
        """Create mock server."""
        server = MagicMock()
        server.name = "Test Server"
        server.host = "192.168.1.1"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        return server

    @pytest.fixture
    def server_tools(self, mock_services):
        """Create ServerTools instance."""
        with patch("tools.server.tools.logger"):
            return ServerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["agent"],
            )

    @pytest.mark.asyncio
    async def test_connection_credentials_not_found(
        self, server_tools, mock_services, mock_server
    ):
        """Test test_connection when credentials not found."""
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["server"].get_credentials = AsyncMock(return_value=None)

        result = await server_tools.test_connection("server-123")

        assert result["success"] is False
        assert result["error"] == "CREDENTIALS_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_connection_agent_status_sync_running(
        self, server_tools, mock_services, mock_server
    ):
        """Test test_connection syncs agent status when running."""
        from models.agent import AgentStatus as AgentStatusEnum

        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["server"].get_credentials = AsyncMock(
            return_value={"password": "x"}
        )
        mock_services["server"].update_server_status = AsyncMock()
        mock_services["server"].update_server_system_info = AsyncMock()

        mock_services["ssh"].test_connection = AsyncMock(
            return_value=(
                True,
                "OK",
                {"docker_version": "24.0", "agent_status": "running"},
            )
        )

        agent = MagicMock()
        agent.id = "agent-123"
        agent.status = AgentStatusEnum.DISCONNECTED
        mock_services["agent"].get_agent_by_server = AsyncMock(return_value=agent)

        with patch("tools.server.tools.log_event", new_callable=AsyncMock):
            result = await server_tools.test_connection("server-123")

        assert result["success"] is True
        assert result["agent_installed"] is True

    @pytest.mark.asyncio
    async def test_connection_agent_status_sync_not_running(
        self, server_tools, mock_services, mock_server
    ):
        """Test test_connection syncs agent status when not running."""
        from models.agent import AgentStatus as AgentStatusEnum

        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["server"].get_credentials = AsyncMock(
            return_value={"password": "x"}
        )
        mock_services["server"].update_server_status = AsyncMock()
        mock_services["server"].update_server_system_info = AsyncMock()

        mock_services["ssh"].test_connection = AsyncMock(
            return_value=(
                True,
                "OK",
                {"docker_version": "24.0", "agent_status": "not running"},
            )
        )

        agent = MagicMock()
        agent.id = "agent-123"
        agent.status = AgentStatusEnum.CONNECTED
        mock_services["agent"].get_agent_by_server = AsyncMock(return_value=agent)
        mock_services["agent"]._get_agent_db = MagicMock()
        mock_services["agent"]._get_agent_db().update_agent = AsyncMock()

        with patch("tools.server.tools.log_event", new_callable=AsyncMock):
            result = await server_tools.test_connection("server-123")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_connection_exception(self, server_tools, mock_services):
        """Test test_connection handles exceptions."""
        mock_services["server"].get_server = AsyncMock(
            side_effect=Exception("DB error")
        )

        with patch("tools.server.tools.log_event", new_callable=AsyncMock):
            result = await server_tools.test_connection("server-123")

        assert result["success"] is False
        assert result["error"] == "CONNECTION_TEST_ERROR"


class TestExecuteCommand:
    """Tests for execute_command method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "ssh": MagicMock(),
            "server": MagicMock(),
            "agent": MagicMock(),
        }

    @pytest.fixture
    def mock_server(self):
        """Create mock server."""
        server = MagicMock()
        server.host = "192.168.1.1"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        return server

    @pytest.mark.asyncio
    async def test_execute_with_router(self, mock_services, mock_server):
        """Test execute_command with command router."""
        mock_router = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.output = "output"
        mock_result.method = MagicMock(value="agent")
        mock_result.exit_code = 0
        mock_result.execution_time_ms = 100
        mock_router.execute = AsyncMock(return_value=mock_result)

        with patch("tools.server.tools.logger"):
            tools = ServerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["agent"],
                command_router=mock_router,
            )

        result = await tools.execute_command("server-123", "ls -la")

        assert result["success"] is True
        assert result["data"]["method"] == "agent"

    @pytest.mark.asyncio
    async def test_execute_with_router_failure(self, mock_services):
        """Test execute_command with router returning failure."""
        mock_router = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.output = ""
        mock_result.method = MagicMock(value="ssh")
        mock_result.exit_code = 1
        mock_result.execution_time_ms = 50
        mock_result.error = "Connection failed"
        mock_router.execute = AsyncMock(return_value=mock_result)

        with patch("tools.server.tools.logger"):
            tools = ServerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["agent"],
                command_router=mock_router,
            )

        result = await tools.execute_command("server-123", "ls -la")

        assert result["success"] is False
        assert result["error"] == "COMMAND_FAILED"

    @pytest.mark.asyncio
    async def test_execute_without_router(self, mock_services, mock_server):
        """Test execute_command falls back to SSH."""
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["server"].get_credentials = AsyncMock(
            return_value={"password": "x"}
        )
        mock_services["ssh"].execute_command = AsyncMock(return_value=(True, "output"))

        with patch("tools.server.tools.logger"):
            tools = ServerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["agent"],
            )

        result = await tools.execute_command("server-123", "ls -la")

        assert result["success"] is True
        assert result["data"]["method"] == "ssh"

    @pytest.mark.asyncio
    async def test_execute_exception(self, mock_services):
        """Test execute_command handles exceptions."""
        mock_router = MagicMock()
        mock_router.execute = AsyncMock(side_effect=Exception("Router error"))

        with patch("tools.server.tools.logger"):
            tools = ServerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["agent"],
                command_router=mock_router,
            )

        with patch("tools.server.tools.log_event", new_callable=AsyncMock):
            result = await tools.execute_command("server-123", "ls -la")

        assert result["success"] is False
        assert result["error"] == "EXECUTE_COMMAND_ERROR"


class TestGetExecutionMethods:
    """Tests for get_execution_methods method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "ssh": MagicMock(),
            "server": MagicMock(),
            "agent": MagicMock(),
        }

    @pytest.mark.asyncio
    async def test_get_methods_with_router(self, mock_services):
        """Test get_execution_methods with command router."""
        mock_router = MagicMock()
        mock_method = MagicMock(value="agent")
        mock_router.get_available_methods = AsyncMock(return_value=[mock_method])
        mock_router.is_agent_available = AsyncMock(return_value=True)

        with patch("tools.server.tools.logger"):
            tools = ServerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["agent"],
                command_router=mock_router,
            )

        result = await tools.get_execution_methods("server-123")

        assert result["success"] is True
        assert "agent" in result["data"]["methods"]
        assert result["data"]["agent_available"] is True

    @pytest.mark.asyncio
    async def test_get_methods_without_router(self, mock_services):
        """Test get_execution_methods without router (SSH only)."""
        server = MagicMock()
        mock_services["server"].get_server = AsyncMock(return_value=server)

        with patch("tools.server.tools.logger"):
            tools = ServerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["agent"],
            )

        result = await tools.get_execution_methods("server-123")

        assert result["success"] is True
        assert result["data"]["methods"] == ["ssh"]
        assert result["data"]["agent_available"] is False

    @pytest.mark.asyncio
    async def test_get_methods_exception(self, mock_services):
        """Test get_execution_methods handles exceptions."""
        mock_router = MagicMock()
        mock_router.get_available_methods = AsyncMock(
            side_effect=Exception("Router error")
        )

        with patch("tools.server.tools.logger"):
            tools = ServerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["agent"],
                command_router=mock_router,
            )

        result = await tools.get_execution_methods("server-123")

        assert result["success"] is False
        assert result["error"] == "GET_METHODS_ERROR"


class TestUpdateServerStatus:
    """Tests for update_server_status method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "ssh": MagicMock(),
            "server": MagicMock(),
            "agent": MagicMock(),
        }

    @pytest.fixture
    def server_tools(self, mock_services):
        """Create ServerTools instance."""
        with patch("tools.server.tools.logger"):
            return ServerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["agent"],
            )

    @pytest.mark.asyncio
    async def test_update_status_success(self, server_tools, mock_services):
        """Test successful status update."""
        mock_services["server"].update_server_status = AsyncMock(return_value=True)

        with patch("tools.server.tools.log_event", new_callable=AsyncMock):
            result = await server_tools.update_server_status("server-123", "connected")

        assert result["success"] is True
        assert "connected" in result["message"]

    @pytest.mark.asyncio
    async def test_update_status_invalid(self, server_tools):
        """Test update with invalid status."""
        result = await server_tools.update_server_status("server-123", "invalid_status")

        assert result["success"] is False
        assert result["error"] == "INVALID_STATUS"

    @pytest.mark.asyncio
    async def test_update_status_server_not_found(self, server_tools, mock_services):
        """Test update when server not found."""
        mock_services["server"].update_server_status = AsyncMock(return_value=False)

        result = await server_tools.update_server_status("server-123", "connected")

        assert result["success"] is False
        assert result["error"] == "SERVER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_update_status_exception(self, server_tools, mock_services):
        """Test update handles exceptions."""
        mock_services["server"].update_server_status = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await server_tools.update_server_status("server-123", "connected")

        assert result["success"] is False
        assert result["error"] == "UPDATE_STATUS_ERROR"


class TestExecuteViaSSH:
    """Tests for _execute_via_ssh private method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "ssh": MagicMock(),
            "server": MagicMock(),
            "agent": MagicMock(),
        }

    @pytest.fixture
    def mock_server(self):
        """Create mock server."""
        server = MagicMock()
        server.host = "192.168.1.1"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        return server

    @pytest.fixture
    def server_tools(self, mock_services):
        """Create ServerTools instance."""
        with patch("tools.server.tools.logger"):
            return ServerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["agent"],
            )

    @pytest.mark.asyncio
    async def test_ssh_server_not_found(self, server_tools, mock_services):
        """Test SSH execution when server not found."""
        mock_services["server"].get_server = AsyncMock(return_value=None)

        result = await server_tools._execute_via_ssh("server-123", "ls", 120)

        assert result["success"] is False
        assert result["error"] == "SERVER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_ssh_credentials_not_found(
        self, server_tools, mock_services, mock_server
    ):
        """Test SSH execution when credentials not found."""
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["server"].get_credentials = AsyncMock(return_value=None)

        result = await server_tools._execute_via_ssh("server-123", "ls", 120)

        assert result["success"] is False
        assert result["error"] == "CREDENTIALS_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_ssh_success(self, server_tools, mock_services, mock_server):
        """Test successful SSH execution."""
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["server"].get_credentials = AsyncMock(
            return_value={"password": "x"}
        )
        mock_services["ssh"].execute_command = AsyncMock(
            return_value=(True, "command output")
        )

        result = await server_tools._execute_via_ssh("server-123", "ls -la", 120)

        assert result["success"] is True
        assert result["data"]["output"] == "command output"
        assert result["data"]["method"] == "ssh"

    @pytest.mark.asyncio
    async def test_ssh_failure(self, server_tools, mock_services, mock_server):
        """Test SSH execution failure."""
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["server"].get_credentials = AsyncMock(
            return_value={"password": "x"}
        )
        mock_services["ssh"].execute_command = AsyncMock(
            return_value=(False, "Permission denied")
        )

        result = await server_tools._execute_via_ssh("server-123", "ls -la", 120)

        assert result["success"] is False
        assert result["error"] == "COMMAND_FAILED"

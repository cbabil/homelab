"""
Docker Tools Unit Tests - Additional Methods

Tests for tracked installation, get_docker_install_status, remove_docker, update_docker.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from tools.docker.tools import DockerTools, _build_docker_install_script


class TestBuildDockerInstallScript:
    """Tests for _build_docker_install_script helper."""

    def test_build_script_ubuntu(self):
        """Test building install script for Ubuntu."""
        script = _build_docker_install_script("ubuntu")
        assert script is not None
        assert "apt-get" in script

    def test_build_script_unsupported(self):
        """Test building script for unsupported OS returns None."""
        script = _build_docker_install_script("windows")
        assert script is None


class TestInstallDockerTracked:
    """Tests for tracked Docker installation."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        ssh = MagicMock()
        server = MagicMock()
        database = MagicMock()
        return {"ssh": ssh, "server": server, "database": database}

    @pytest.fixture
    def docker_tools(self, mock_services):
        """Create DockerTools instance."""
        with patch("tools.docker.tools.logger"):
            return DockerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["database"],
            )

    @pytest.mark.asyncio
    async def test_tracked_missing_server_id(self, docker_tools):
        """Test tracked installation without server_id."""
        result = await docker_tools.install_docker(tracked=True)

        assert result["success"] is False
        assert result["error"] == "MISSING_SERVER_ID"

    @pytest.mark.asyncio
    async def test_tracked_installation_start_failed(self, docker_tools, mock_services):
        """Test tracked installation when DB creation fails."""
        mock_services["database"].create_installation = AsyncMock(return_value=None)

        with patch("tools.docker.tools.log_event", new_callable=AsyncMock):
            result = await docker_tools.install_docker(
                server_id="server-123",
                tracked=True,
            )

        assert result["success"] is False
        assert result["error"] == "INSTALL_START_FAILED"

    @pytest.mark.asyncio
    async def test_tracked_installation_success(self, docker_tools, mock_services):
        """Test successful tracked installation start."""
        installation = MagicMock()
        installation.id = "docker-abc123"
        mock_services["database"].create_installation = AsyncMock(
            return_value=installation
        )

        with patch("tools.docker.tools.log_event", new_callable=AsyncMock):
            result = await docker_tools.install_docker(
                server_id="server-123",
                tracked=True,
            )

        assert result["success"] is True
        assert result["data"]["installation_id"] == "docker-abc123"


class TestInstallDockerFailure:
    """Tests for Docker installation failure scenarios."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        ssh = MagicMock()
        server = MagicMock()
        database = MagicMock()
        return {"ssh": ssh, "server": server, "database": database}

    @pytest.fixture
    def mock_server(self):
        """Create a mock server object."""
        server = MagicMock()
        server.name = "Test Server"
        server.host = "192.168.1.100"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        server.system_info = MagicMock(os="Ubuntu 22.04")
        return server

    @pytest.fixture
    def docker_tools(self, mock_services):
        """Create DockerTools instance."""
        with patch("tools.docker.tools.logger"):
            return DockerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["database"],
            )

    @pytest.mark.asyncio
    async def test_install_failure(self, docker_tools, mock_services, mock_server):
        """Test installation failure with server_id."""
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["server"].get_credentials = AsyncMock(
            return_value={"password": "secret"}
        )
        mock_services["server"].update_server_status = AsyncMock()
        mock_services["ssh"].execute_command = AsyncMock(
            return_value=(False, "Installation failed")
        )

        with patch("tools.docker.tools.log_event", new_callable=AsyncMock):
            result = await docker_tools.install_docker(server_id="server-123")

        assert result["success"] is False
        assert result["error"] == "DOCKER_INSTALL_FAILED"

    @pytest.mark.asyncio
    async def test_install_exception(self, docker_tools, mock_services):
        """Test installation with exception."""
        mock_services["server"].get_server = AsyncMock(
            side_effect=Exception("DB error")
        )
        mock_services["server"].update_server_status = AsyncMock()

        result = await docker_tools.install_docker(server_id="server-123")

        assert result["success"] is False
        assert result["error"] == "DOCKER_INSTALL_ERROR"

    @pytest.mark.asyncio
    async def test_install_validation_error(self, docker_tools, mock_services):
        """Test installation with validation error."""
        with patch(
            "lib.security.validate_server_input",
            return_value={"valid": False, "error": "Invalid hostname"},
        ):
            result = await docker_tools.install_docker(
                host="invalid!host",
                port=22,
                username="admin",
                auth_type="password",
                password="secret",
            )

        assert result["success"] is False
        assert result["error"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_install_with_key_auth(self, docker_tools, mock_services):
        """Test installation with key authentication."""
        mock_services["ssh"].test_connection = AsyncMock(
            return_value=(True, "Connected", {"os": "Ubuntu 22.04"})
        )
        mock_services["ssh"].execute_command = AsyncMock(return_value=(True, "Success"))

        with patch("lib.security.validate_server_input", return_value={"valid": True}):
            with patch("tools.docker.tools.log_event", new_callable=AsyncMock):
                result = await docker_tools.install_docker(
                    host="192.168.1.100",
                    port=22,
                    username="admin",
                    auth_type="key",
                    private_key="-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----",
                )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_install_no_script_available_with_server_id(
        self, docker_tools, mock_services, mock_server
    ):
        """Test installation when _build_docker_install_script returns None with server_id."""
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["server"].get_credentials = AsyncMock(
            return_value={"password": "secret"}
        )
        mock_services["server"].update_server_status = AsyncMock()
        mock_services["ssh"].test_connection = AsyncMock(
            return_value=(True, "Connected", {"os": "Ubuntu 22.04"})
        )

        # Mock _build_docker_install_script to return None
        with (
            patch(
                "tools.docker.tools._build_docker_install_script", return_value=None
            ),
            patch(
                "tools.docker.tools._detect_os_type", return_value="ubuntu"
            ),
        ):
            result = await docker_tools.install_docker(server_id="server-123")

        assert result["success"] is False
        assert result["error"] == "UNSUPPORTED_OS"
        assert "No Docker commands available" in result["message"]
        mock_services["server"].update_server_status.assert_called()


class TestGetDockerInstallStatus:
    """Tests for get_docker_install_status method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        ssh = MagicMock()
        server = MagicMock()
        database = MagicMock()
        return {"ssh": ssh, "server": server, "database": database}

    @pytest.fixture
    def docker_tools(self, mock_services):
        """Create DockerTools instance."""
        with patch("tools.docker.tools.logger"):
            return DockerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["database"],
            )

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, docker_tools, mock_services):
        """Test getting status when no installation found."""
        mock_services["database"].get_installation = AsyncMock(return_value=None)

        result = await docker_tools.get_docker_install_status("server-123")

        assert result["success"] is False
        assert result["error"] == "INSTALL_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_status_success(self, docker_tools, mock_services):
        """Test getting status successfully."""
        installation = MagicMock()
        installation.id = "install-123"
        installation.server_id = "server-123"
        installation.status = MagicMock(value="completed")
        installation.config = {"install_type": "docker"}
        installation.installed_at = "2025-01-01T00:00:00Z"
        installation.started_at = "2025-01-01T00:00:01Z"
        installation.error_message = None

        mock_services["database"].get_installation = AsyncMock(
            return_value=installation
        )

        result = await docker_tools.get_docker_install_status("server-123")

        assert result["success"] is True
        assert result["data"]["id"] == "install-123"
        assert result["data"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_status_exception(self, docker_tools, mock_services):
        """Test getting status handles exceptions."""
        mock_services["database"].get_installation = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await docker_tools.get_docker_install_status("server-123")

        assert result["success"] is False
        assert result["error"] == "GET_STATUS_ERROR"


class TestRemoveDocker:
    """Tests for remove_docker method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        ssh = MagicMock()
        server = MagicMock()
        database = MagicMock()
        return {"ssh": ssh, "server": server, "database": database}

    @pytest.fixture
    def mock_server(self):
        """Create a mock server object."""
        server = MagicMock()
        server.name = "Test Server"
        server.host = "192.168.1.100"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        server.system_info = MagicMock(os="Ubuntu 22.04")
        return server

    @pytest.fixture
    def docker_tools(self, mock_services):
        """Create DockerTools instance."""
        with patch("tools.docker.tools.logger"):
            return DockerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["database"],
            )

    @pytest.mark.asyncio
    async def test_remove_server_not_found(self, docker_tools, mock_services):
        """Test remove when server not found."""
        mock_services["server"].get_server = AsyncMock(return_value=None)

        result = await docker_tools.remove_docker("server-123")

        assert result["success"] is False
        assert result["error"] == "SERVER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_remove_credentials_not_found(
        self, docker_tools, mock_services, mock_server
    ):
        """Test remove when credentials not found."""
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["server"].get_credentials = AsyncMock(return_value=None)

        result = await docker_tools.remove_docker("server-123")

        assert result["success"] is False
        assert result["error"] == "CREDENTIALS_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_remove_unsupported_os(self, docker_tools, mock_services):
        """Test remove on unsupported OS."""
        server = MagicMock()
        server.system_info = MagicMock(os="Windows Server")
        mock_services["server"].get_server = AsyncMock(return_value=server)
        mock_services["server"].get_credentials = AsyncMock(
            return_value={"password": "x"}
        )

        result = await docker_tools.remove_docker("server-123")

        assert result["success"] is False
        assert result["error"] == "UNSUPPORTED_OS"

    @pytest.mark.asyncio
    async def test_remove_success(self, docker_tools, mock_services, mock_server):
        """Test successful Docker removal."""
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["server"].get_credentials = AsyncMock(
            return_value={"password": "x"}
        )
        mock_services["server"].update_server_system_info = AsyncMock()
        mock_services["ssh"].execute_command = AsyncMock(return_value=(True, "Removed"))
        mock_services["ssh"].test_connection = AsyncMock(
            return_value=(True, "OK", {"docker_version": None})
        )

        with patch("tools.docker.tools.log_event", new_callable=AsyncMock):
            result = await docker_tools.remove_docker("server-123")

        assert result["success"] is True
        assert "removed successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_remove_failure(self, docker_tools, mock_services, mock_server):
        """Test Docker removal failure."""
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["server"].get_credentials = AsyncMock(
            return_value={"password": "x"}
        )
        mock_services["ssh"].execute_command = AsyncMock(
            return_value=(False, "Removal failed")
        )

        with patch("tools.docker.tools.log_event", new_callable=AsyncMock):
            result = await docker_tools.remove_docker("server-123")

        assert result["success"] is False
        assert result["error"] == "DOCKER_REMOVE_FAILED"

    @pytest.mark.asyncio
    async def test_remove_exception(self, docker_tools, mock_services):
        """Test remove handles exceptions."""
        mock_services["server"].get_server = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await docker_tools.remove_docker("server-123")

        assert result["success"] is False
        assert result["error"] == "DOCKER_REMOVE_ERROR"


class TestUpdateDocker:
    """Tests for update_docker method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        ssh = MagicMock()
        server = MagicMock()
        database = MagicMock()
        return {"ssh": ssh, "server": server, "database": database}

    @pytest.fixture
    def mock_server(self):
        """Create a mock server object."""
        server = MagicMock()
        server.name = "Test Server"
        server.host = "192.168.1.100"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        server.system_info = MagicMock(os="Ubuntu 22.04")
        return server

    @pytest.fixture
    def docker_tools(self, mock_services):
        """Create DockerTools instance."""
        with patch("tools.docker.tools.logger"):
            return DockerTools(
                mock_services["ssh"],
                mock_services["server"],
                mock_services["database"],
            )

    @pytest.mark.asyncio
    async def test_update_server_not_found(self, docker_tools, mock_services):
        """Test update when server not found."""
        mock_services["server"].get_server = AsyncMock(return_value=None)

        result = await docker_tools.update_docker("server-123")

        assert result["success"] is False
        assert result["error"] == "SERVER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_update_credentials_not_found(
        self, docker_tools, mock_services, mock_server
    ):
        """Test update when credentials not found."""
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["server"].get_credentials = AsyncMock(return_value=None)

        result = await docker_tools.update_docker("server-123")

        assert result["success"] is False
        assert result["error"] == "CREDENTIALS_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_update_unsupported_os(self, docker_tools, mock_services):
        """Test update on unsupported OS."""
        server = MagicMock()
        server.system_info = MagicMock(os="Windows Server")
        mock_services["server"].get_server = AsyncMock(return_value=server)
        mock_services["server"].get_credentials = AsyncMock(
            return_value={"password": "x"}
        )

        result = await docker_tools.update_docker("server-123")

        assert result["success"] is False
        assert result["error"] == "UNSUPPORTED_OS"

    @pytest.mark.asyncio
    async def test_update_success(self, docker_tools, mock_services, mock_server):
        """Test successful Docker update."""
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["server"].get_credentials = AsyncMock(
            return_value={"password": "x"}
        )
        mock_services["server"].update_server_system_info = AsyncMock()
        mock_services["ssh"].execute_command = AsyncMock(return_value=(True, "Updated"))
        mock_services["ssh"].test_connection = AsyncMock(
            return_value=(True, "OK", {"docker_version": "24.1.0"})
        )

        with patch("tools.docker.tools.log_event", new_callable=AsyncMock):
            result = await docker_tools.update_docker("server-123")

        assert result["success"] is True
        assert "updated successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_update_failure(self, docker_tools, mock_services, mock_server):
        """Test Docker update failure."""
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["server"].get_credentials = AsyncMock(
            return_value={"password": "x"}
        )
        mock_services["ssh"].execute_command = AsyncMock(
            return_value=(False, "Update failed")
        )

        with patch("tools.docker.tools.log_event", new_callable=AsyncMock):
            result = await docker_tools.update_docker("server-123")

        assert result["success"] is False
        assert result["error"] == "DOCKER_UPDATE_FAILED"

    @pytest.mark.asyncio
    async def test_update_exception(self, docker_tools, mock_services):
        """Test update handles exceptions."""
        mock_services["server"].get_server = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await docker_tools.update_docker("server-123")

        assert result["success"] is False
        assert result["error"] == "DOCKER_UPDATE_ERROR"

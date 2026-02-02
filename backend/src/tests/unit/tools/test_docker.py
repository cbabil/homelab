"""
Docker Tools Unit Tests

Tests for Docker installation tool.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestDockerTools:
    """Tests for Docker tools."""

    @pytest.fixture
    def mock_ssh_service(self):
        """Create mock SSH service."""
        service = MagicMock()
        service.test_connection = AsyncMock(return_value=(
            True,
            "Connected",
            {"os": "Ubuntu 22.04", "docker_version": "Not installed"}
        ))
        service.execute_command = AsyncMock(return_value=(True, "Docker installed"))
        return service

    @pytest.fixture
    def mock_server_service(self):
        """Create mock server service."""
        service = MagicMock()
        service.get_server = AsyncMock()
        service.get_credentials = AsyncMock(return_value={"password": "secret"})
        service.update_server_status = AsyncMock()
        service.update_server_system_info = AsyncMock()
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
        server.system_info = MagicMock(os="Ubuntu 22.04")
        return server


class TestInstallDockerWithServerId:
    """Tests for install_docker with server_id parameter."""

    @pytest.fixture
    def mock_ssh_service(self):
        service = MagicMock()
        service.test_connection = AsyncMock(return_value=(
            True, "Connected", {"os": "Ubuntu 22.04", "docker_version": "24.0.0"}
        ))
        service.execute_command = AsyncMock(return_value=(True, "Docker installed"))
        return service

    @pytest.fixture
    def mock_server_service(self):
        service = MagicMock()
        return service

    @pytest.fixture
    def mock_database_service(self):
        service = MagicMock()
        return service

    @pytest.fixture
    def mock_server(self):
        server = MagicMock()
        server.id = "server-123"
        server.host = "192.168.1.100"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        server.system_info = MagicMock(os="Ubuntu 22.04")
        return server

    @pytest.mark.asyncio
    async def test_install_docker_success(
        self, mock_ssh_service, mock_server_service, mock_database_service, mock_server
    ):
        """Test successful Docker installation via server_id."""
        from tools.docker.tools import DockerTools

        mock_server_service.get_server = AsyncMock(return_value=mock_server)
        mock_server_service.get_credentials = AsyncMock(return_value={"password": "secret"})
        mock_server_service.update_server_status = AsyncMock()
        mock_server_service.update_server_system_info = AsyncMock()

        tools = DockerTools(mock_ssh_service, mock_server_service, mock_database_service)

        with patch('tools.docker.tools.log_event', new_callable=AsyncMock):
            result = await tools.install_docker(server_id="server-123")

        assert result["success"] is True
        assert "Docker installed" in result["message"]

    @pytest.mark.asyncio
    async def test_install_docker_server_not_found(
        self, mock_ssh_service, mock_server_service, mock_database_service
    ):
        """Test Docker installation when server doesn't exist."""
        from tools.docker.tools import DockerTools

        mock_server_service.get_server = AsyncMock(return_value=None)
        tools = DockerTools(mock_ssh_service, mock_server_service, mock_database_service)

        result = await tools.install_docker(server_id="nonexistent")

        assert result["success"] is False
        assert result["error"] == "SERVER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_install_docker_no_credentials(
        self, mock_ssh_service, mock_server_service, mock_database_service, mock_server
    ):
        """Test Docker installation when credentials not found."""
        from tools.docker.tools import DockerTools

        mock_server_service.get_server = AsyncMock(return_value=mock_server)
        mock_server_service.get_credentials = AsyncMock(return_value=None)

        tools = DockerTools(mock_ssh_service, mock_server_service, mock_database_service)

        result = await tools.install_docker(server_id="server-123")

        assert result["success"] is False
        assert result["error"] == "CREDENTIALS_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_install_docker_unsupported_os(
        self, mock_ssh_service, mock_server_service, mock_database_service
    ):
        """Test Docker installation on unsupported OS."""
        from tools.docker.tools import DockerTools

        server = MagicMock()
        server.host = "192.168.1.100"
        server.port = 22
        server.username = "admin"
        server.auth_type = MagicMock(value="password")
        server.system_info = MagicMock(os="Windows Server 2019")  # Unsupported

        mock_server_service.get_server = AsyncMock(return_value=server)
        mock_server_service.get_credentials = AsyncMock(return_value={"password": "secret"})
        mock_server_service.update_server_status = AsyncMock()

        tools = DockerTools(mock_ssh_service, mock_server_service, mock_database_service)

        result = await tools.install_docker(server_id="server-123")

        assert result["success"] is False
        assert result["error"] == "UNSUPPORTED_OS"


class TestInstallDockerDirect:
    """Tests for install_docker with direct credentials."""

    @pytest.fixture
    def mock_ssh_service(self):
        service = MagicMock()
        service.test_connection = AsyncMock(return_value=(
            True, "Connected", {"os": "Ubuntu 22.04", "docker_version": "24.0.0"}
        ))
        service.execute_command = AsyncMock(return_value=(True, "Docker installed"))
        return service

    @pytest.fixture
    def mock_server_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_database_service(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_install_docker_direct_success(
        self, mock_ssh_service, mock_server_service, mock_database_service
    ):
        """Test successful Docker installation with direct credentials."""
        from tools.docker.tools import DockerTools

        tools = DockerTools(mock_ssh_service, mock_server_service, mock_database_service)

        with patch('tools.docker.tools.log_event', new_callable=AsyncMock):
            with patch('lib.security.validate_server_input', return_value={"valid": True}):
                result = await tools.install_docker(
                    host="192.168.1.100",
                    port=22,
                    username="admin",
                    auth_type="password",
                    password="secret123"
                )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_install_docker_direct_missing_params(
        self, mock_ssh_service, mock_server_service, mock_database_service
    ):
        """Test Docker installation with missing parameters."""
        from tools.docker.tools import DockerTools

        tools = DockerTools(mock_ssh_service, mock_server_service, mock_database_service)

        # Missing host
        result = await tools.install_docker(
            port=22,
            username="admin",
            auth_type="password",
            password="secret"
        )

        assert result["success"] is False
        assert result["error"] == "MISSING_PARAMETERS"

    @pytest.mark.asyncio
    async def test_install_docker_direct_missing_password(
        self, mock_ssh_service, mock_server_service, mock_database_service
    ):
        """Test Docker installation with password auth but no password."""
        from tools.docker.tools import DockerTools

        tools = DockerTools(mock_ssh_service, mock_server_service, mock_database_service)

        with patch('lib.security.validate_server_input', return_value={"valid": True}):
            result = await tools.install_docker(
                host="192.168.1.100",
                port=22,
                username="admin",
                auth_type="password"
                # No password provided
            )

        assert result["success"] is False
        assert result["error"] == "MISSING_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_install_docker_direct_missing_key(
        self, mock_ssh_service, mock_server_service, mock_database_service
    ):
        """Test Docker installation with key auth but no key."""
        from tools.docker.tools import DockerTools

        tools = DockerTools(mock_ssh_service, mock_server_service, mock_database_service)

        with patch('lib.security.validate_server_input', return_value={"valid": True}):
            result = await tools.install_docker(
                host="192.168.1.100",
                port=22,
                username="admin",
                auth_type="key"
                # No private_key provided
            )

        assert result["success"] is False
        assert result["error"] == "MISSING_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_install_docker_direct_connection_failed(
        self, mock_ssh_service, mock_server_service, mock_database_service
    ):
        """Test Docker installation when connection fails."""
        from tools.docker.tools import DockerTools

        mock_ssh_service.test_connection = AsyncMock(return_value=(
            False, "Connection refused", None
        ))

        tools = DockerTools(mock_ssh_service, mock_server_service, mock_database_service)

        with patch('lib.security.validate_server_input', return_value={"valid": True}):
            result = await tools.install_docker(
                host="192.168.1.100",
                port=22,
                username="admin",
                auth_type="password",
                password="secret"
            )

        assert result["success"] is False
        assert result["error"] == "CONNECTION_FAILED"

    @pytest.mark.asyncio
    async def test_install_docker_invalid_auth_type(
        self, mock_ssh_service, mock_server_service, mock_database_service
    ):
        """Test Docker installation with invalid auth type."""
        from tools.docker.tools import DockerTools

        tools = DockerTools(mock_ssh_service, mock_server_service, mock_database_service)

        with patch('lib.security.validate_server_input', return_value={"valid": True}):
            result = await tools.install_docker(
                host="192.168.1.100",
                port=22,
                username="admin",
                auth_type="invalid_auth",
                password="secret"
            )

        assert result["success"] is False
        assert result["error"] == "INVALID_AUTH_TYPE"


class TestOsDetection:
    """Tests for OS detection helper."""

    def test_detect_ubuntu(self):
        """Test detecting Ubuntu OS."""
        from tools.docker.tools import _detect_os_type

        assert _detect_os_type("Ubuntu 22.04 LTS") == "ubuntu"
        assert _detect_os_type("ubuntu 20.04") == "ubuntu"

    def test_detect_debian(self):
        """Test detecting Debian OS."""
        from tools.docker.tools import _detect_os_type

        assert _detect_os_type("Debian GNU/Linux 11") == "debian"
        assert _detect_os_type("debian 12") == "debian"

    def test_detect_rhel(self):
        """Test detecting RHEL-based OS."""
        from tools.docker.tools import _detect_os_type

        assert _detect_os_type("Rocky Linux 9") == "rhel"
        assert _detect_os_type("CentOS Stream 8") == "rhel"
        assert _detect_os_type("Red Hat Enterprise Linux 8") == "rhel"

    def test_detect_fedora(self):
        """Test detecting Fedora."""
        from tools.docker.tools import _detect_os_type

        assert _detect_os_type("Fedora 39") == "fedora"

    def test_detect_alpine(self):
        """Test detecting Alpine."""
        from tools.docker.tools import _detect_os_type

        assert _detect_os_type("Alpine Linux 3.18") == "alpine"

    def test_detect_arch(self):
        """Test detecting Arch-based OS."""
        from tools.docker.tools import _detect_os_type

        assert _detect_os_type("Arch Linux") == "arch"
        assert _detect_os_type("Manjaro Linux") == "arch"

    def test_detect_unknown(self):
        """Test detecting unknown OS."""
        from tools.docker.tools import _detect_os_type

        assert _detect_os_type("Windows Server 2019") == "unknown"
        assert _detect_os_type("FreeBSD 13") == "unknown"
        assert _detect_os_type("") == "unknown"

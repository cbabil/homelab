"""
Unit tests for models/server.py

Tests server models including connection, credentials, and validation.
"""

import pytest
from pydantic import ValidationError

from models.server import (
    AuthType,
    ServerConnection,
    ServerCredentials,
    ServerStatus,
    SystemInfo,
)


class TestAuthType:
    """Tests for AuthType enum."""

    def test_auth_type_values(self):
        """Test all auth type enum values."""
        assert AuthType.PASSWORD == "password"
        assert AuthType.KEY == "key"

    def test_auth_type_is_string_enum(self):
        """Test that auth type values are strings."""
        assert isinstance(AuthType.PASSWORD.value, str)
        assert isinstance(AuthType.KEY.value, str)

    def test_auth_type_from_value(self):
        """Test creating enum from string value."""
        assert AuthType("password") == AuthType.PASSWORD
        assert AuthType("key") == AuthType.KEY


class TestServerStatus:
    """Tests for ServerStatus enum."""

    def test_server_status_values(self):
        """Test all server status enum values."""
        assert ServerStatus.CONNECTED == "connected"
        assert ServerStatus.DISCONNECTED == "disconnected"
        assert ServerStatus.ERROR == "error"
        assert ServerStatus.PREPARING == "preparing"

    def test_server_status_is_string_enum(self):
        """Test that server status values are strings."""
        for status in ServerStatus:
            assert isinstance(status.value, str)


class TestSystemInfo:
    """Tests for SystemInfo model."""

    def test_required_fields(self):
        """Test required fields."""
        info = SystemInfo(
            os="Ubuntu 22.04 LTS",
            kernel="5.15.0-generic",
            architecture="x86_64",
        )
        assert info.os == "Ubuntu 22.04 LTS"
        assert info.kernel == "5.15.0-generic"
        assert info.architecture == "x86_64"

    def test_default_values(self):
        """Test default values for optional fields."""
        info = SystemInfo(
            os="Debian 12",
            kernel="6.1.0",
            architecture="aarch64",
        )
        assert info.docker_version is None
        assert info.agent_status is None
        assert info.agent_version is None

    def test_all_fields(self):
        """Test all fields populated."""
        info = SystemInfo(
            os="Ubuntu 24.04 LTS",
            kernel="6.8.0-generic",
            architecture="x86_64",
            docker_version="26.0.0",
            agent_status="running",
            agent_version="1.2.0",
        )
        assert info.docker_version == "26.0.0"
        assert info.agent_status == "running"
        assert info.agent_version == "1.2.0"

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            SystemInfo(os="Ubuntu")


class TestServerConnection:
    """Tests for ServerConnection model."""

    def test_required_fields(self):
        """Test required fields."""
        server = ServerConnection(
            id="server-123",
            name="Web Server",
            host="192.168.1.100",
            username="admin",
            auth_type=AuthType.PASSWORD,
            created_at="2024-01-15T10:00:00Z",
        )
        assert server.id == "server-123"
        assert server.name == "Web Server"
        assert server.host == "192.168.1.100"
        assert server.username == "admin"
        assert server.auth_type == AuthType.PASSWORD
        assert server.created_at == "2024-01-15T10:00:00Z"

    def test_default_values(self):
        """Test default values."""
        server = ServerConnection(
            id="server-123",
            name="Test Server",
            host="10.0.0.1",
            username="root",
            auth_type=AuthType.KEY,
            created_at="2024-01-15T10:00:00Z",
        )
        assert server.port == 22
        assert server.status == ServerStatus.DISCONNECTED
        assert server.last_connected is None
        assert server.system_info is None
        assert server.docker_installed is False
        assert server.system_info_updated_at is None

    def test_all_fields(self):
        """Test all fields populated."""
        system_info = SystemInfo(
            os="Ubuntu 22.04",
            kernel="5.15.0",
            architecture="x86_64",
            docker_version="24.0.0",
        )
        server = ServerConnection(
            id="server-456",
            name="Production DB",
            host="db.example.com",
            port=2222,
            username="dbadmin",
            auth_type=AuthType.KEY,
            status=ServerStatus.CONNECTED,
            created_at="2024-01-01T00:00:00Z",
            last_connected="2024-01-15T10:00:00Z",
            system_info=system_info,
            docker_installed=True,
            system_info_updated_at="2024-01-15T10:00:00Z",
        )
        assert server.port == 2222
        assert server.status == ServerStatus.CONNECTED
        assert server.last_connected == "2024-01-15T10:00:00Z"
        assert server.system_info.os == "Ubuntu 22.04"
        assert server.docker_installed is True

    # Host validation tests
    def test_host_valid_ipv4(self):
        """Test valid IPv4 address."""
        server = ServerConnection(
            id="server-1",
            name="Test",
            host="192.168.1.1",
            username="admin",
            auth_type=AuthType.PASSWORD,
            created_at="2024-01-15T10:00:00Z",
        )
        assert server.host == "192.168.1.1"

    def test_host_valid_ipv6(self):
        """Test valid IPv6 address."""
        server = ServerConnection(
            id="server-1",
            name="Test",
            host="::1",
            username="admin",
            auth_type=AuthType.PASSWORD,
            created_at="2024-01-15T10:00:00Z",
        )
        assert server.host == "::1"

    def test_host_valid_ipv6_full(self):
        """Test valid full IPv6 address."""
        server = ServerConnection(
            id="server-1",
            name="Test",
            host="2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            username="admin",
            auth_type=AuthType.PASSWORD,
            created_at="2024-01-15T10:00:00Z",
        )
        assert server.host == "2001:0db8:85a3:0000:0000:8a2e:0370:7334"

    def test_host_valid_hostname(self):
        """Test valid hostname."""
        server = ServerConnection(
            id="server-1",
            name="Test",
            host="server1.example.com",
            username="admin",
            auth_type=AuthType.PASSWORD,
            created_at="2024-01-15T10:00:00Z",
        )
        assert server.host == "server1.example.com"

    def test_host_valid_simple_hostname(self):
        """Test valid simple hostname without domain."""
        server = ServerConnection(
            id="server-1",
            name="Test",
            host="myserver",
            username="admin",
            auth_type=AuthType.PASSWORD,
            created_at="2024-01-15T10:00:00Z",
        )
        assert server.host == "myserver"

    def test_host_valid_hostname_with_hyphen(self):
        """Test valid hostname with hyphens."""
        server = ServerConnection(
            id="server-1",
            name="Test",
            host="web-server-01",
            username="admin",
            auth_type=AuthType.PASSWORD,
            created_at="2024-01-15T10:00:00Z",
        )
        assert server.host == "web-server-01"

    def test_host_invalid_format(self):
        """Test invalid host format."""
        with pytest.raises(ValidationError) as exc_info:
            ServerConnection(
                id="server-1",
                name="Test",
                host="invalid_host!@#",
                username="admin",
                auth_type=AuthType.PASSWORD,
                created_at="2024-01-15T10:00:00Z",
            )
        assert "host" in str(exc_info.value).lower()

    def test_host_invalid_starts_with_hyphen(self):
        """Test hostname starting with hyphen is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            ServerConnection(
                id="server-1",
                name="Test",
                host="-invalid-host",
                username="admin",
                auth_type=AuthType.PASSWORD,
                created_at="2024-01-15T10:00:00Z",
            )
        assert "host" in str(exc_info.value).lower()

    # Username validation tests
    def test_username_valid_simple(self):
        """Test valid simple username."""
        server = ServerConnection(
            id="server-1",
            name="Test",
            host="192.168.1.1",
            username="admin",
            auth_type=AuthType.PASSWORD,
            created_at="2024-01-15T10:00:00Z",
        )
        assert server.username == "admin"

    def test_username_valid_root(self):
        """Test valid root username."""
        server = ServerConnection(
            id="server-1",
            name="Test",
            host="192.168.1.1",
            username="root",
            auth_type=AuthType.PASSWORD,
            created_at="2024-01-15T10:00:00Z",
        )
        assert server.username == "root"

    def test_username_valid_with_underscore(self):
        """Test valid username with underscore."""
        server = ServerConnection(
            id="server-1",
            name="Test",
            host="192.168.1.1",
            username="deploy_user",
            auth_type=AuthType.PASSWORD,
            created_at="2024-01-15T10:00:00Z",
        )
        assert server.username == "deploy_user"

    def test_username_valid_with_hyphen(self):
        """Test valid username with hyphen."""
        server = ServerConnection(
            id="server-1",
            name="Test",
            host="192.168.1.1",
            username="deploy-user",
            auth_type=AuthType.PASSWORD,
            created_at="2024-01-15T10:00:00Z",
        )
        assert server.username == "deploy-user"

    def test_username_valid_starts_with_underscore(self):
        """Test valid username starting with underscore."""
        server = ServerConnection(
            id="server-1",
            name="Test",
            host="192.168.1.1",
            username="_sysuser",
            auth_type=AuthType.PASSWORD,
            created_at="2024-01-15T10:00:00Z",
        )
        assert server.username == "_sysuser"

    def test_username_invalid_starts_with_number(self):
        """Test username starting with number is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            ServerConnection(
                id="server-1",
                name="Test",
                host="192.168.1.1",
                username="1admin",
                auth_type=AuthType.PASSWORD,
                created_at="2024-01-15T10:00:00Z",
            )
        assert "username" in str(exc_info.value).lower()

    def test_username_invalid_uppercase(self):
        """Test username with uppercase is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            ServerConnection(
                id="server-1",
                name="Test",
                host="192.168.1.1",
                username="Admin",
                auth_type=AuthType.PASSWORD,
                created_at="2024-01-15T10:00:00Z",
            )
        assert "username" in str(exc_info.value).lower()

    def test_username_invalid_special_chars(self):
        """Test username with special characters is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            ServerConnection(
                id="server-1",
                name="Test",
                host="192.168.1.1",
                username="admin@server",
                auth_type=AuthType.PASSWORD,
                created_at="2024-01-15T10:00:00Z",
            )
        assert "username" in str(exc_info.value).lower()

    # Port validation tests
    def test_port_min_boundary(self):
        """Test minimum port boundary (1)."""
        server = ServerConnection(
            id="server-1",
            name="Test",
            host="192.168.1.1",
            port=1,
            username="admin",
            auth_type=AuthType.PASSWORD,
            created_at="2024-01-15T10:00:00Z",
        )
        assert server.port == 1

    def test_port_max_boundary(self):
        """Test maximum port boundary (65535)."""
        server = ServerConnection(
            id="server-1",
            name="Test",
            host="192.168.1.1",
            port=65535,
            username="admin",
            auth_type=AuthType.PASSWORD,
            created_at="2024-01-15T10:00:00Z",
        )
        assert server.port == 65535

    def test_port_below_min(self):
        """Test port below minimum is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            ServerConnection(
                id="server-1",
                name="Test",
                host="192.168.1.1",
                port=0,
                username="admin",
                auth_type=AuthType.PASSWORD,
                created_at="2024-01-15T10:00:00Z",
            )
        assert "port" in str(exc_info.value)

    def test_port_above_max(self):
        """Test port above maximum is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            ServerConnection(
                id="server-1",
                name="Test",
                host="192.168.1.1",
                port=65536,
                username="admin",
                auth_type=AuthType.PASSWORD,
                created_at="2024-01-15T10:00:00Z",
            )
        assert "port" in str(exc_info.value)

    # Name validation tests
    def test_name_max_length(self):
        """Test name at maximum length."""
        server = ServerConnection(
            id="server-1",
            name="a" * 100,
            host="192.168.1.1",
            username="admin",
            auth_type=AuthType.PASSWORD,
            created_at="2024-01-15T10:00:00Z",
        )
        assert len(server.name) == 100

    def test_name_exceeds_max_length(self):
        """Test name exceeding max length."""
        with pytest.raises(ValidationError) as exc_info:
            ServerConnection(
                id="server-1",
                name="a" * 101,
                host="192.168.1.1",
                username="admin",
                auth_type=AuthType.PASSWORD,
                created_at="2024-01-15T10:00:00Z",
            )
        assert "name" in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            ServerConnection(id="server-1")


class TestServerCredentials:
    """Tests for ServerCredentials model."""

    def test_required_fields(self):
        """Test required fields."""
        creds = ServerCredentials(
            server_id="server-123",
            encrypted_data="encrypted_blob_here",
            created_at="2024-01-15T10:00:00Z",
        )
        assert creds.server_id == "server-123"
        assert creds.encrypted_data == "encrypted_blob_here"
        assert creds.created_at == "2024-01-15T10:00:00Z"

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            ServerCredentials(server_id="server-123")

    def test_missing_encrypted_data(self):
        """Test validation error when encrypted data is missing."""
        with pytest.raises(ValidationError):
            ServerCredentials(
                server_id="server-123",
                created_at="2024-01-15T10:00:00Z",
            )

"""
Unit tests for Pydantic Data Models.

Tests server connection models with comprehensive validation scenarios.
Covers valid data, invalid formats, and edge cases for security.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from models.server import (
    AuthType, ServerStatus, SystemInfo, 
    ServerConnection, ServerCredentials
)


class TestAuthType:
    """Test suite for authentication type enum."""

    def test_auth_type_values(self):
        """Test authentication type enum values."""
        assert AuthType.PASSWORD == "password"
        assert AuthType.KEY == "key"

    def test_auth_type_from_string(self):
        """Test creating auth type from string."""
        assert AuthType("password") == AuthType.PASSWORD
        assert AuthType("key") == AuthType.KEY


class TestServerStatus:
    """Test suite for server status enum."""

    def test_server_status_values(self):
        """Test server status enum values."""
        assert ServerStatus.CONNECTED == "connected"
        assert ServerStatus.DISCONNECTED == "disconnected"
        assert ServerStatus.ERROR == "error"
        assert ServerStatus.PREPARING == "preparing"


class TestSystemInfo:
    """Test suite for system information model."""

    def test_system_info_valid_data(self):
        """Test system info with valid data."""
        data = {
            "os": "Ubuntu 22.04.1 LTS",
            "kernel": "5.15.0-56-generic",
            "architecture": "x86_64",
            "uptime": "up 1 day, 2 hours, 30 minutes"
        }
        
        system_info = SystemInfo(**data)
        
        assert system_info.os == "Ubuntu 22.04.1 LTS"
        assert system_info.kernel == "5.15.0-56-generic"
        assert system_info.architecture == "x86_64"
        assert system_info.uptime == "up 1 day, 2 hours, 30 minutes"
        assert system_info.docker_version is None

    def test_system_info_with_docker(self):
        """Test system info with Docker version."""
        data = {
            "os": "Ubuntu 22.04",
            "kernel": "5.15.0",
            "architecture": "x86_64",
            "uptime": "up 1 day",
            "docker_version": "24.0.5"
        }
        
        system_info = SystemInfo(**data)
        assert system_info.docker_version == "24.0.5"

    def test_system_info_missing_required_fields(self):
        """Test system info validation with missing fields."""
        data = {"os": "Ubuntu 22.04"}
        
        with pytest.raises(ValidationError) as exc_info:
            SystemInfo(**data)
        
        errors = exc_info.value.errors()
        assert len(errors) >= 3  # Missing kernel, architecture, uptime


class TestServerConnection:
    """Test suite for server connection model."""

    @pytest.fixture
    def valid_server_data(self):
        """Valid server connection data for testing."""
        return {
            "id": "server-001",
            "name": "Production Server",
            "host": "192.168.1.100",
            "port": 22,
            "username": "admin",
            "auth_type": AuthType.PASSWORD,
            "created_at": "2024-01-01T12:00:00Z"
        }

    def test_server_connection_valid_data(self, valid_server_data):
        """Test server connection with valid data."""
        connection = ServerConnection(**valid_server_data)
        
        assert connection.id == "server-001"
        assert connection.name == "Production Server"
        assert connection.host == "192.168.1.100"
        assert connection.port == 22
        assert connection.username == "admin"
        assert connection.auth_type == AuthType.PASSWORD
        assert connection.status == ServerStatus.DISCONNECTED
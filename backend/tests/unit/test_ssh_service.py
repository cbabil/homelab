"""
Unit tests for SSH Service.

Tests SSH connection management with comprehensive paramiko mocking.
Covers authentication methods, error handling, and security configurations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import paramiko
from services.ssh_service import SSHService


class TestSSHService:
    """Test suite for SSH service functionality."""

    @pytest.fixture
    def ssh_service(self):
        """Create SSH service instance for testing."""
        return SSHService()

    @pytest.fixture
    def mock_ssh_client(self):
        """Mock paramiko.SSHClient for testing."""
        client = MagicMock(spec=paramiko.SSHClient)
        client.connect = MagicMock()
        client.close = MagicMock()
        client.set_missing_host_key_policy = MagicMock()
        client.get_transport = MagicMock()
        return client

    def test_init_ssh_service(self, ssh_service):
        """Test SSH service initialization."""
        assert ssh_service.connections == {}
        assert ssh_service.connection_configs['timeout'] == 30
        assert ssh_service.connection_configs['auth_timeout'] == 10
        assert ssh_service.connection_configs['banner_timeout'] == 30
        assert ssh_service.connection_configs['compress'] is True

    @patch('paramiko.SSHClient')
    def test_create_ssh_client(self, mock_client_class, ssh_service):
        """Test SSH client creation with security settings."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = ssh_service.create_ssh_client()

        assert client == mock_client
        mock_client.set_missing_host_key_policy.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_connection_password_success(self, ssh_service):
        """Test successful password authentication."""
        with patch('services.ssh_service.connect_password', new_callable=AsyncMock) as mock_connect, \
             patch('services.ssh_service.get_system_info', new_callable=AsyncMock) as mock_info, \
             patch.object(ssh_service, 'create_ssh_client') as mock_create:
            
            mock_client = MagicMock()
            mock_create.return_value = mock_client
            mock_info.return_value = {'os': 'Ubuntu 22.04', 'uptime': '1 day'}

            success, message, info = await ssh_service.test_connection(
                'test.example.com', 22, 'testuser', 'password', {'password': 'testpass'}
            )

            assert success is True
            assert message == "Connection successful"
            assert info == {'os': 'Ubuntu 22.04', 'uptime': '1 day'}
            mock_connect.assert_called_once()
            mock_client.close.assert_called_once()
"""
Unit tests for SSH Helper Functions.

Tests SSH connection helpers with paramiko mocking.
Covers authentication methods and system information gathering.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import paramiko
from services.helpers.ssh_helpers import connect_password, connect_key, get_system_info


class TestSSHHelpers:
    """Test suite for SSH helper functions."""

    @pytest.fixture
    def mock_ssh_client(self):
        """Mock paramiko.SSHClient for testing."""
        client = MagicMock(spec=paramiko.SSHClient)
        return client

    @pytest.fixture
    def sample_credentials(self):
        """Sample credentials for testing."""
        return {
            'password': 'testpass',
            'private_key': '-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----',
            'passphrase': 'keypass'
        }

    @pytest.mark.asyncio
    async def test_connect_password(self, mock_ssh_client, sample_credentials):
        """Test password authentication connection."""
        config = {'timeout': 30, 'compress': True}
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            await connect_password(
                mock_ssh_client, 'test.example.com', 22, 'testuser', sample_credentials, config
            )
            
            mock_thread.assert_called_once_with(
                mock_ssh_client.connect,
                hostname='test.example.com',
                port=22,
                username='testuser',
                password='testpass',
                **config
            )

    @pytest.mark.asyncio
    async def test_connect_key(self, mock_ssh_client, sample_credentials):
        """Test SSH key authentication connection."""
        config = {'timeout': 30, 'compress': True}
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread, \
             patch('paramiko.RSAKey.from_private_key') as mock_key:
            
            mock_private_key = MagicMock()
            mock_key.return_value = mock_private_key
            
            await connect_key(
                mock_ssh_client, 'test.example.com', 22, 'testuser', sample_credentials, config
            )
            
            mock_thread.assert_called_once_with(
                mock_ssh_client.connect,
                hostname='test.example.com',
                port=22,
                username='testuser',
                pkey=mock_private_key,
                **config
            )

    @pytest.mark.asyncio 
    async def test_get_system_info_success(self, mock_ssh_client):
        """Test successful system information gathering."""
        # Mock command execution responses
        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        
        mock_stdout.read.return_value.decode.return_value.strip.side_effect = [
            'Ubuntu 22.04.1 LTS',
            '5.15.0-56-generic',
            'x86_64',
            'up 1 day, 2 hours, 30 minutes'
        ]
        
        mock_ssh_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        
        result = await get_system_info(mock_ssh_client)
        
        expected_result = {
            'os': 'Ubuntu 22.04.1 LTS',
            'kernel': '5.15.0-56-generic',
            'architecture': 'x86_64',
            'uptime': 'up 1 day, 2 hours, 30 minutes'
        }
        
        assert result == expected_result
        assert mock_ssh_client.exec_command.call_count == 4
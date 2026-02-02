"""
Unit tests for services/helpers/ssh_helpers.py

Tests SSH connection and system info gathering functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import paramiko

from services.helpers.ssh_helpers import connect_password, connect_key, get_system_info


class TestConnectPassword:
    """Tests for connect_password function."""

    @pytest.mark.asyncio
    async def test_connect_password_calls_connect(self):
        """connect_password should call client.connect with password."""
        mock_client = MagicMock(spec=paramiko.SSHClient)
        credentials = {"password": "testpass"}
        config = {"timeout": 30}

        with patch("services.helpers.ssh_helpers.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            await connect_password(
                mock_client, "host.example.com", 22, "user", credentials, config
            )

            mock_thread.assert_called_once_with(
                mock_client.connect,
                hostname="host.example.com",
                port=22,
                username="user",
                password="testpass",
                timeout=30,
            )

    @pytest.mark.asyncio
    async def test_connect_password_handles_missing_password(self):
        """connect_password should pass None if password missing."""
        mock_client = MagicMock(spec=paramiko.SSHClient)
        credentials = {}
        config = {}

        with patch("services.helpers.ssh_helpers.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            await connect_password(
                mock_client, "host", 22, "user", credentials, config
            )

            call_kwargs = mock_thread.call_args.kwargs
            assert call_kwargs["password"] is None

    @pytest.mark.asyncio
    async def test_connect_password_passes_all_config(self):
        """connect_password should pass all config options."""
        mock_client = MagicMock(spec=paramiko.SSHClient)
        credentials = {"password": "pass"}
        config = {"timeout": 60, "compress": True, "allow_agent": False}

        with patch("services.helpers.ssh_helpers.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            await connect_password(
                mock_client, "host", 2222, "admin", credentials, config
            )

            call_args = mock_thread.call_args
            assert call_args.kwargs["timeout"] == 60
            assert call_args.kwargs["compress"] is True
            assert call_args.kwargs["allow_agent"] is False


class TestConnectKey:
    """Tests for connect_key function."""

    @pytest.mark.asyncio
    async def test_connect_key_tries_ed25519_first(self):
        """connect_key should try Ed25519 key type first."""
        mock_client = MagicMock(spec=paramiko.SSHClient)
        credentials = {"private_key": "key_data"}
        config = {}
        mock_key = MagicMock()

        with patch("services.helpers.ssh_helpers.asyncio.to_thread", new_callable=AsyncMock), \
             patch("paramiko.Ed25519Key.from_private_key", return_value=mock_key) as mock_ed25519:
            await connect_key(mock_client, "host", 22, "user", credentials, config)
            mock_ed25519.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_key_falls_back_to_rsa(self):
        """connect_key should fall back to RSA if Ed25519 fails."""
        mock_client = MagicMock(spec=paramiko.SSHClient)
        credentials = {"private_key": "key_data"}
        config = {}
        mock_key = MagicMock()

        with patch("services.helpers.ssh_helpers.asyncio.to_thread", new_callable=AsyncMock), \
             patch("paramiko.Ed25519Key.from_private_key", side_effect=Exception("Not Ed25519")), \
             patch("paramiko.RSAKey.from_private_key", return_value=mock_key) as mock_rsa:
            await connect_key(mock_client, "host", 22, "user", credentials, config)
            mock_rsa.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_key_falls_back_to_ecdsa(self):
        """connect_key should fall back to ECDSA if RSA fails."""
        mock_client = MagicMock(spec=paramiko.SSHClient)
        credentials = {"private_key": "key_data"}
        config = {}
        mock_key = MagicMock()

        with patch("services.helpers.ssh_helpers.asyncio.to_thread", new_callable=AsyncMock), \
             patch("paramiko.Ed25519Key.from_private_key", side_effect=Exception("Not Ed25519")), \
             patch("paramiko.RSAKey.from_private_key", side_effect=Exception("Not RSA")), \
             patch("paramiko.ECDSAKey.from_private_key", return_value=mock_key) as mock_ecdsa:
            await connect_key(mock_client, "host", 22, "user", credentials, config)
            mock_ecdsa.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_key_raises_if_all_fail(self):
        """connect_key should raise ValueError if no key type works."""
        mock_client = MagicMock(spec=paramiko.SSHClient)
        credentials = {"private_key": "invalid_key"}
        config = {}

        with patch("paramiko.Ed25519Key.from_private_key", side_effect=Exception("Not Ed25519")), \
             patch("paramiko.RSAKey.from_private_key", side_effect=Exception("Not RSA")), \
             patch("paramiko.ECDSAKey.from_private_key", side_effect=Exception("Not ECDSA")):
            with pytest.raises(ValueError) as exc_info:
                await connect_key(mock_client, "host", 22, "user", credentials, config)
            assert "Could not parse private key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_connect_key_uses_passphrase(self):
        """connect_key should pass passphrase to key parser."""
        mock_client = MagicMock(spec=paramiko.SSHClient)
        credentials = {"private_key": "key_data", "passphrase": "secret"}
        config = {}
        mock_key = MagicMock()

        with patch("services.helpers.ssh_helpers.asyncio.to_thread", new_callable=AsyncMock), \
             patch("paramiko.Ed25519Key.from_private_key", return_value=mock_key) as mock_ed25519:
            await connect_key(mock_client, "host", 22, "user", credentials, config)

            call_kwargs = mock_ed25519.call_args.kwargs
            assert call_kwargs["password"] == "secret"

    @pytest.mark.asyncio
    async def test_connect_key_calls_connect_with_pkey(self):
        """connect_key should call client.connect with pkey."""
        mock_client = MagicMock(spec=paramiko.SSHClient)
        credentials = {"private_key": "key_data"}
        config = {"timeout": 30}
        mock_key = MagicMock()

        with patch("services.helpers.ssh_helpers.asyncio.to_thread", new_callable=AsyncMock) as mock_thread, \
             patch("paramiko.Ed25519Key.from_private_key", return_value=mock_key):
            await connect_key(mock_client, "host.example.com", 22, "user", credentials, config)

            mock_thread.assert_called_once_with(
                mock_client.connect,
                hostname="host.example.com",
                port=22,
                username="user",
                pkey=mock_key,
                timeout=30,
            )

    @pytest.mark.asyncio
    async def test_connect_key_logs_success(self):
        """connect_key should log successful key loading."""
        mock_client = MagicMock(spec=paramiko.SSHClient)
        credentials = {"private_key": "key_data"}
        config = {}
        mock_key = MagicMock()

        with patch("services.helpers.ssh_helpers.asyncio.to_thread", new_callable=AsyncMock), \
             patch("paramiko.Ed25519Key.from_private_key", return_value=mock_key), \
             patch("services.helpers.ssh_helpers.logger") as mock_logger:
            await connect_key(mock_client, "host", 22, "user", credentials, config)
            mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_connect_key_logs_error_on_failure(self):
        """connect_key should log error when all key types fail."""
        mock_client = MagicMock(spec=paramiko.SSHClient)
        credentials = {"private_key": "invalid_key"}
        config = {}

        with patch("paramiko.Ed25519Key.from_private_key", side_effect=Exception("err")), \
             patch("paramiko.RSAKey.from_private_key", side_effect=Exception("err")), \
             patch("paramiko.ECDSAKey.from_private_key", side_effect=Exception("err")), \
             patch("services.helpers.ssh_helpers.logger") as mock_logger:
            with pytest.raises(ValueError):
                await connect_key(mock_client, "host", 22, "user", credentials, config)
            mock_logger.error.assert_called_once()


class TestGetSystemInfo:
    """Tests for get_system_info function."""

    @pytest.mark.asyncio
    async def test_get_system_info_returns_dict(self):
        """get_system_info should return dict with system info."""
        mock_client = MagicMock(spec=paramiko.SSHClient)
        mock_stdout = MagicMock()
        mock_stdout.read.return_value.decode.return_value.strip.return_value = "test_value"
        mock_client.exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

        result = await get_system_info(mock_client)

        assert isinstance(result, dict)
        assert "os" in result
        assert "kernel" in result
        assert "architecture" in result
        assert "docker_version" in result
        assert "agent_status" in result
        assert "agent_version" in result

    @pytest.mark.asyncio
    async def test_get_system_info_executes_commands(self):
        """get_system_info should execute commands for each info type."""
        mock_client = MagicMock(spec=paramiko.SSHClient)
        mock_stdout = MagicMock()
        mock_stdout.read.return_value.decode.return_value.strip.return_value = "value"
        mock_client.exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

        await get_system_info(mock_client)

        # Should call exec_command 6 times (os, kernel, architecture, docker, agent_status, agent_version)
        assert mock_client.exec_command.call_count == 6

    @pytest.mark.asyncio
    async def test_get_system_info_handles_command_error(self):
        """get_system_info should return 'Unknown' on command error."""
        mock_client = MagicMock(spec=paramiko.SSHClient)
        mock_client.exec_command.side_effect = Exception("Command failed")

        result = await get_system_info(mock_client)

        for key in ["os", "kernel", "architecture", "docker_version", "agent_status", "agent_version"]:
            assert result[key] == "Unknown"

    @pytest.mark.asyncio
    async def test_get_system_info_logs_warning_on_error(self):
        """get_system_info should log warning when command fails."""
        mock_client = MagicMock(spec=paramiko.SSHClient)
        mock_client.exec_command.side_effect = Exception("Command failed")

        with patch("services.helpers.ssh_helpers.logger") as mock_logger:
            await get_system_info(mock_client)
            # Should log warning for each failed command
            assert mock_logger.warning.call_count == 6

    @pytest.mark.asyncio
    async def test_get_system_info_captures_output(self):
        """get_system_info should capture stdout output correctly."""
        mock_client = MagicMock(spec=paramiko.SSHClient)

        outputs = {
            "os": "Ubuntu 22.04",
            "kernel": "5.15.0",
            "architecture": "x86_64",
            "docker_version": "24.0.0",
            "agent_status": "running",
            "agent_version": "1.0.0",
        }
        output_list = list(outputs.values())
        call_count = [0]

        def mock_exec_command(cmd):
            mock_stdout = MagicMock()
            mock_stdout.read.return_value.decode.return_value.strip.return_value = output_list[call_count[0]]
            call_count[0] += 1
            return (MagicMock(), mock_stdout, MagicMock())

        mock_client.exec_command.side_effect = mock_exec_command

        result = await get_system_info(mock_client)

        assert result["os"] == "Ubuntu 22.04"
        assert result["kernel"] == "5.15.0"
        assert result["architecture"] == "x86_64"
        assert result["docker_version"] == "24.0.0"
        assert result["agent_status"] == "running"
        assert result["agent_version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_get_system_info_partial_failure(self):
        """get_system_info should handle partial command failures."""
        mock_client = MagicMock(spec=paramiko.SSHClient)
        call_count = [0]

        def mock_exec_command(cmd):
            call_count[0] += 1
            if call_count[0] == 2:  # Fail on second command (kernel)
                raise Exception("Kernel command failed")
            mock_stdout = MagicMock()
            mock_stdout.read.return_value.decode.return_value.strip.return_value = f"value_{call_count[0]}"
            return (MagicMock(), mock_stdout, MagicMock())

        mock_client.exec_command.side_effect = mock_exec_command

        result = await get_system_info(mock_client)

        assert result["os"] == "value_1"
        assert result["kernel"] == "Unknown"
        assert result["architecture"] == "value_3"

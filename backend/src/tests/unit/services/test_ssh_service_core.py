"""
Unit tests for SSHService in services/ssh_service.py

Tests the core SSH service functionality including initialization,
connection creation, and connection management.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import paramiko
import pytest

from services.ssh_service import SSHService


@pytest.fixture
def mock_pool():
    """Create a mock connection pool."""
    pool = MagicMock()
    pool._make_key.return_value = "host:22:user"
    pool.get = AsyncMock(return_value=None)
    pool.put = AsyncMock()
    pool.release = AsyncMock()
    pool.close = AsyncMock()
    pool.close_all = AsyncMock()
    return pool


@pytest.fixture
def mock_ssh_client():
    """Create a mock SSH client."""
    client = MagicMock(spec=paramiko.SSHClient)
    transport = MagicMock()
    transport.is_active.return_value = True
    client.get_transport.return_value = transport
    return client


@pytest.fixture
def ssh_service():
    """Create an SSHService instance with mocked dependencies."""
    with (
        patch("services.ssh_service.logger"),
        patch("services.ssh_service.SSHConnectionPool") as MockPool,
    ):
        # Set up async mock methods on the pool
        mock_pool = MagicMock()
        mock_pool._make_key.return_value = "host:22:user"
        mock_pool.get = AsyncMock(return_value=None)
        mock_pool.put = AsyncMock()
        mock_pool.release = AsyncMock()
        mock_pool.close = AsyncMock()
        mock_pool.close_all = AsyncMock()
        MockPool.return_value = mock_pool
        service = SSHService(strict_host_key_checking=False)
        return service


class TestSSHServiceInit:
    """Tests for SSHService initialization."""

    def test_init_creates_pool(self):
        """SSHService should create connection pool."""
        with (
            patch("services.ssh_service.logger"),
            patch("services.ssh_service.SSHConnectionPool") as MockPool,
        ):
            service = SSHService()
            MockPool.assert_called_once()
            assert service._pool is MockPool.return_value

    def test_init_with_explicit_strict_checking(self):
        """SSHService should use explicit strict_host_key_checking."""
        with (
            patch("services.ssh_service.logger"),
            patch("services.ssh_service.SSHConnectionPool"),
        ):
            service = SSHService(strict_host_key_checking=True)
            assert service.strict_host_key_checking is True

            service = SSHService(strict_host_key_checking=False)
            assert service.strict_host_key_checking is False

    def test_init_defaults_to_production_env(self):
        """SSHService should default to production behavior from env."""
        with (
            patch("services.ssh_service.logger"),
            patch("services.ssh_service.SSHConnectionPool"),
            patch.dict("os.environ", {"APP_ENV": "production"}),
        ):
            service = SSHService()
            assert service.strict_host_key_checking is True

    def test_init_always_strict_by_default(self):
        """SSHService should use strict checking by default regardless of env."""
        with (
            patch("services.ssh_service.logger"),
            patch("services.ssh_service.SSHConnectionPool"),
            patch.dict("os.environ", {"APP_ENV": "development"}),
        ):
            service = SSHService()
            assert service.strict_host_key_checking is True

    def test_init_default_config_values(self, ssh_service):
        """SSHService should have correct default configs."""
        assert ssh_service.connection_configs["timeout"] == 60
        assert ssh_service.connection_configs["auth_timeout"] == 30
        assert ssh_service.connection_configs["banner_timeout"] == 60
        assert ssh_service.connection_configs["compress"] is True
        assert ssh_service.connection_configs["allow_agent"] is False
        assert ssh_service.connection_configs["look_for_keys"] is False

    def test_init_logs_message(self):
        """SSHService should log initialization."""
        with (
            patch("services.ssh_service.logger") as mock_logger,
            patch("services.ssh_service.SSHConnectionPool"),
        ):
            SSHService(strict_host_key_checking=True)
            mock_logger.info.assert_called_with(
                "SSH service initialized with connection pooling",
                strict_host_key_checking=True,
            )


class TestCreateSSHClient:
    """Tests for _create_ssh_client method."""

    def test_creates_paramiko_client(self, ssh_service):
        """_create_ssh_client should create paramiko.SSHClient."""
        with (
            patch("services.ssh_service.paramiko") as mock_paramiko,
            patch("services.ssh_service.logger"),
        ):
            mock_paramiko.SSHClient.return_value = MagicMock()
            client = ssh_service._create_ssh_client()
            mock_paramiko.SSHClient.assert_called_once()
            assert client is mock_paramiko.SSHClient.return_value

    def test_loads_known_hosts_when_exists(self, ssh_service):
        """_create_ssh_client should load known_hosts if exists."""
        mock_client = MagicMock()

        with (
            patch("services.ssh_service.paramiko") as mock_paramiko,
            patch("services.ssh_service.Path") as MockPath,
            patch("services.ssh_service.logger"),
        ):
            mock_paramiko.SSHClient.return_value = mock_client
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            MockPath.home.return_value.__truediv__.return_value.__truediv__.return_value = mock_path

            ssh_service._create_ssh_client()
            mock_client.load_host_keys.assert_called_once()

    def test_handles_known_hosts_load_error(self, ssh_service):
        """_create_ssh_client should handle known_hosts load errors."""
        mock_client = MagicMock()
        mock_client.load_host_keys.side_effect = Exception("Parse error")

        with (
            patch("services.ssh_service.paramiko") as mock_paramiko,
            patch("services.ssh_service.Path") as MockPath,
            patch("services.ssh_service.logger") as mock_logger,
        ):
            mock_paramiko.SSHClient.return_value = mock_client
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            MockPath.home.return_value.__truediv__.return_value.__truediv__.return_value = mock_path

            client = ssh_service._create_ssh_client()
            assert client is mock_client
            mock_logger.warning.assert_called()

    def test_sets_reject_policy_when_strict(self):
        """_create_ssh_client should use RejectPolicy when strict."""
        with (
            patch("services.ssh_service.logger"),
            patch("services.ssh_service.SSHConnectionPool"),
            patch("services.ssh_service.paramiko") as mock_paramiko,
            patch("services.ssh_service.Path") as MockPath,
        ):
            MockPath.home.return_value.__truediv__.return_value.__truediv__.return_value.exists.return_value = False
            mock_client = MagicMock()
            mock_paramiko.SSHClient.return_value = mock_client

            service = SSHService(strict_host_key_checking=True)
            service._create_ssh_client()

            mock_client.set_missing_host_key_policy.assert_called_once()
            call_args = mock_client.set_missing_host_key_policy.call_args
            assert call_args[0][0] is mock_paramiko.RejectPolicy.return_value

    def test_sets_warning_policy_when_not_strict(self):
        """_create_ssh_client should use WarningPolicy when not strict."""
        with (
            patch("services.ssh_service.logger"),
            patch("services.ssh_service.SSHConnectionPool"),
            patch("services.ssh_service.paramiko") as mock_paramiko,
            patch("services.ssh_service.Path") as MockPath,
        ):
            MockPath.home.return_value.__truediv__.return_value.__truediv__.return_value.exists.return_value = False
            mock_client = MagicMock()
            mock_paramiko.SSHClient.return_value = mock_client

            service = SSHService(strict_host_key_checking=False)
            service._create_ssh_client()

            mock_client.set_missing_host_key_policy.assert_called_once()
            call_args = mock_client.set_missing_host_key_policy.call_args
            assert call_args[0][0] is mock_paramiko.WarningPolicy.return_value


class TestGetConnection:
    """Tests for _get_connection context manager."""

    @pytest.mark.asyncio
    async def test_returns_pooled_connection_when_available(self, ssh_service):
        """_get_connection should return pooled connection if available."""
        mock_client = MagicMock()
        ssh_service._pool.get = AsyncMock(return_value=mock_client)

        with patch("services.ssh_service.logger"):
            async with ssh_service._get_connection(
                "host", 22, "user", "password", {"password": "secret"}
            ) as client:
                assert client is mock_client

    @pytest.mark.asyncio
    async def test_creates_new_connection_when_not_pooled(self, ssh_service):
        """_get_connection should create new connection when not pooled."""
        ssh_service._pool.get = AsyncMock(return_value=None)
        mock_client = MagicMock()

        with (
            patch.object(ssh_service, "_create_ssh_client", return_value=mock_client),
            patch("services.ssh_service.logger"),
            patch(
                "services.helpers.ssh_helpers.connect_password", new_callable=AsyncMock
            ),
        ):
            async with ssh_service._get_connection(
                "host", 22, "user", "password", {"password": "secret"}
            ) as client:
                assert client is mock_client

    @pytest.mark.asyncio
    async def test_uses_password_auth(self, ssh_service):
        """_get_connection should use password authentication."""
        ssh_service._pool.get = AsyncMock(return_value=None)
        mock_client = MagicMock()

        with (
            patch.object(ssh_service, "_create_ssh_client", return_value=mock_client),
            patch("services.ssh_service.logger"),
            patch(
                "services.helpers.ssh_helpers.connect_password", new_callable=AsyncMock
            ) as mock_connect,
        ):
            async with ssh_service._get_connection(
                "host", 22, "user", "password", {"password": "secret"}
            ):
                mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_uses_key_auth(self, ssh_service):
        """_get_connection should use key authentication."""
        ssh_service._pool.get = AsyncMock(return_value=None)
        mock_client = MagicMock()

        with (
            patch.object(ssh_service, "_create_ssh_client", return_value=mock_client),
            patch("services.ssh_service.logger"),
            patch(
                "services.helpers.ssh_helpers.connect_key", new_callable=AsyncMock
            ) as mock_connect,
        ):
            async with ssh_service._get_connection(
                "host", 22, "user", "key", {"private_key": "..."}
            ):
                mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_on_unsupported_auth_type(self, ssh_service):
        """_get_connection should raise ValueError for unsupported auth."""
        ssh_service._pool.get = AsyncMock(return_value=None)
        mock_client = MagicMock()

        with (
            patch.object(ssh_service, "_create_ssh_client", return_value=mock_client),
            patch("services.ssh_service.logger"),
            pytest.raises(ValueError, match="Unsupported auth type"),
        ):
            async with ssh_service._get_connection(
                "host", 22, "user", "certificate", {}
            ):
                pass

    @pytest.mark.asyncio
    async def test_adds_to_pool_after_successful_connection(self, ssh_service):
        """_get_connection should add new connection to pool."""
        ssh_service._pool.get = AsyncMock(return_value=None)
        ssh_service._pool.put = AsyncMock()
        mock_client = MagicMock()

        with (
            patch.object(ssh_service, "_create_ssh_client", return_value=mock_client),
            patch("services.ssh_service.logger"),
            patch(
                "services.helpers.ssh_helpers.connect_password", new_callable=AsyncMock
            ),
        ):
            async with ssh_service._get_connection(
                "host", 22, "user", "password", {"password": "secret"}
            ):
                pass
            ssh_service._pool.put.assert_called_once()

    @pytest.mark.asyncio
    async def test_releases_connection_after_use(self, ssh_service):
        """_get_connection should release connection back to pool."""
        mock_client = MagicMock()
        ssh_service._pool.get = AsyncMock(return_value=mock_client)
        ssh_service._pool.release = AsyncMock()

        with patch("services.ssh_service.logger"):
            async with ssh_service._get_connection("host", 22, "user", "password", {}):
                pass

            ssh_service._pool.release.assert_called_once()

    @pytest.mark.asyncio
    async def test_closes_client_on_connection_failure(self, ssh_service):
        """_get_connection should close client on connection failure."""
        ssh_service._pool.get = AsyncMock(return_value=None)
        mock_client = MagicMock()

        with (
            patch.object(ssh_service, "_create_ssh_client", return_value=mock_client),
            patch("services.ssh_service.logger"),
            patch(
                "services.helpers.ssh_helpers.connect_password", new_callable=AsyncMock
            ) as mock_connect,
        ):
            mock_connect.side_effect = Exception("Connection failed")

            with pytest.raises(Exception, match="Connection failed"):
                async with ssh_service._get_connection(
                    "host", 22, "user", "password", {}
                ):
                    pass

            mock_client.close.assert_called_once()


class TestCloseConnection:
    """Tests for close_connection method."""

    @pytest.mark.asyncio
    async def test_close_connection_calls_pool_close(self, ssh_service):
        """close_connection should close specific pooled connection."""
        ssh_service._pool._make_key.return_value = "host:22:user"
        ssh_service._pool.close = AsyncMock()

        await ssh_service.close_connection("host", 22, "user")

        ssh_service._pool._make_key.assert_called_once_with("host", 22, "user")
        ssh_service._pool.close.assert_called_once_with("host:22:user")


class TestCloseAllConnections:
    """Tests for close_all_connections method."""

    @pytest.mark.asyncio
    async def test_close_all_connections_calls_pool(self, ssh_service):
        """close_all_connections should close all pooled connections."""
        ssh_service._pool.close_all = AsyncMock()

        await ssh_service.close_all_connections()

        ssh_service._pool.close_all.assert_called_once()

"""
Unit tests for services/server_service.py

Tests server management with database persistence and encryption.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.server_service import ServerService
from models.server import ServerConnection, ServerStatus


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    return MagicMock()


@pytest.fixture
def mock_credential_manager():
    """Create mock credential manager."""
    manager = MagicMock()
    manager.encrypt_credentials.return_value = "encrypted_data"
    manager.decrypt_credentials.return_value = {"password": "decrypted"}
    return manager


@pytest.fixture
def server_service(mock_db_service, mock_credential_manager):
    """Create ServerService instance with mocked dependencies."""
    with patch("services.server_service.CredentialManager") as MockCM, \
         patch("services.server_service.logger"):
        MockCM.return_value = mock_credential_manager
        service = ServerService(mock_db_service)
        return service


class TestServerServiceInit:
    """Tests for ServerService initialization."""

    def test_init_stores_db_service(self, mock_db_service, mock_credential_manager):
        """ServerService should store db_service reference."""
        with patch("services.server_service.CredentialManager") as MockCM, \
             patch("services.server_service.logger"):
            MockCM.return_value = mock_credential_manager
            service = ServerService(mock_db_service)
            assert service.db_service is mock_db_service

    def test_init_creates_credential_manager(self, mock_db_service):
        """ServerService should create credential manager."""
        with patch("services.server_service.CredentialManager") as MockCM, \
             patch("services.server_service.logger"):
            MockCM.return_value = MagicMock()
            service = ServerService(mock_db_service)
            assert service.credential_manager is not None

    def test_init_handles_credential_manager_error(self, mock_db_service):
        """ServerService should handle credential manager initialization error."""
        with patch("services.server_service.CredentialManager") as MockCM, \
             patch("services.server_service.logger"):
            MockCM.side_effect = ValueError("No encryption key")
            service = ServerService(mock_db_service)
            assert service.credential_manager is None

    def test_init_logs_message(self, mock_db_service, mock_credential_manager):
        """ServerService should log initialization."""
        with patch("services.server_service.CredentialManager") as MockCM, \
             patch("services.server_service.logger") as mock_logger:
            MockCM.return_value = mock_credential_manager
            ServerService(mock_db_service)
            mock_logger.info.assert_called_with("Server service initialized")


class TestAddServer:
    """Tests for add_server method."""

    @pytest.mark.asyncio
    async def test_add_server_success(self, server_service, mock_db_service):
        """add_server should create server with encrypted credentials."""
        mock_server = MagicMock(spec=ServerConnection)
        mock_db_service.create_server = AsyncMock(return_value=mock_server)

        with patch("services.server_service.logger"):
            result = await server_service.add_server(
                server_id="srv-123",
                name="Test Server",
                host="192.168.1.1",
                port=22,
                username="admin",
                auth_type="password",
                credentials={"password": "secret"},
            )

        assert result is mock_server
        mock_db_service.create_server.assert_called_once()
        call_kwargs = mock_db_service.create_server.call_args.kwargs
        assert call_kwargs["id"] == "srv-123"
        assert call_kwargs["encrypted_credentials"] == "encrypted_data"

    @pytest.mark.asyncio
    async def test_add_server_without_credential_manager(self, mock_db_service):
        """add_server should work without credential manager."""
        with patch("services.server_service.CredentialManager") as MockCM, \
             patch("services.server_service.logger"):
            MockCM.side_effect = ValueError("No key")
            service = ServerService(mock_db_service)

            mock_server = MagicMock(spec=ServerConnection)
            mock_db_service.create_server = AsyncMock(return_value=mock_server)

            result = await service.add_server(
                server_id="srv-123",
                name="Test",
                host="192.168.1.1",
                port=22,
                username="admin",
                auth_type="password",
                credentials={"password": "secret"},
            )

            assert result is mock_server
            call_kwargs = mock_db_service.create_server.call_args.kwargs
            assert call_kwargs["encrypted_credentials"] == ""

    @pytest.mark.asyncio
    async def test_add_server_empty_credentials(
        self, server_service, mock_db_service
    ):
        """add_server should handle empty credentials."""
        mock_server = MagicMock(spec=ServerConnection)
        mock_db_service.create_server = AsyncMock(return_value=mock_server)

        with patch("services.server_service.logger"):
            result = await server_service.add_server(
                server_id="srv-123",
                name="Test",
                host="192.168.1.1",
                port=22,
                username="admin",
                auth_type="key",
                credentials={},
            )

            assert result is mock_server
            call_kwargs = mock_db_service.create_server.call_args.kwargs
            assert call_kwargs["encrypted_credentials"] == ""

    @pytest.mark.asyncio
    async def test_add_server_error(self, server_service, mock_db_service):
        """add_server should return None on error."""
        mock_db_service.create_server = AsyncMock(side_effect=Exception("DB error"))

        with patch("services.server_service.logger"):
            result = await server_service.add_server(
                server_id="srv-123",
                name="Test",
                host="192.168.1.1",
                port=22,
                username="admin",
                auth_type="password",
                credentials={},
            )

            assert result is None


class TestGetServer:
    """Tests for get_server method."""

    @pytest.mark.asyncio
    async def test_get_server_found(self, server_service, mock_db_service):
        """get_server should return server when found."""
        mock_server = MagicMock(spec=ServerConnection)
        mock_db_service.get_server_by_id = AsyncMock(return_value=mock_server)

        with patch("services.server_service.logger"):
            result = await server_service.get_server("srv-123")

        assert result is mock_server
        mock_db_service.get_server_by_id.assert_called_once_with("srv-123")

    @pytest.mark.asyncio
    async def test_get_server_not_found(self, server_service, mock_db_service):
        """get_server should return None when not found."""
        mock_db_service.get_server_by_id = AsyncMock(return_value=None)

        with patch("services.server_service.logger"):
            result = await server_service.get_server("nonexistent")

        assert result is None


class TestGetServerByConnection:
    """Tests for get_server_by_connection method."""

    @pytest.mark.asyncio
    async def test_get_server_by_connection(self, server_service, mock_db_service):
        """get_server_by_connection should find server by connection details."""
        mock_server = MagicMock(spec=ServerConnection)
        mock_db_service.get_server_by_connection = AsyncMock(return_value=mock_server)

        result = await server_service.get_server_by_connection(
            "192.168.1.1", 22, "admin"
        )

        assert result is mock_server
        mock_db_service.get_server_by_connection.assert_called_once_with(
            "192.168.1.1", 22, "admin"
        )


class TestGetAllServers:
    """Tests for get_all_servers method."""

    @pytest.mark.asyncio
    async def test_get_all_servers(self, server_service, mock_db_service):
        """get_all_servers should return all servers."""
        mock_servers = [MagicMock(spec=ServerConnection), MagicMock(spec=ServerConnection)]
        mock_db_service.get_all_servers_from_db = AsyncMock(return_value=mock_servers)

        result = await server_service.get_all_servers()

        assert result == mock_servers
        assert len(result) == 2


class TestGetCredentials:
    """Tests for get_credentials method."""

    @pytest.mark.asyncio
    async def test_get_credentials_success(
        self, server_service, mock_db_service, mock_credential_manager
    ):
        """get_credentials should return decrypted credentials."""
        mock_db_service.get_server_credentials = AsyncMock(return_value="encrypted")

        with patch("services.server_service.logger"):
            result = await server_service.get_credentials("srv-123")

        assert result == {"password": "decrypted"}
        mock_credential_manager.decrypt_credentials.assert_called_once_with("encrypted")

    @pytest.mark.asyncio
    async def test_get_credentials_no_encrypted(self, server_service, mock_db_service):
        """get_credentials should return None when no encrypted credentials."""
        mock_db_service.get_server_credentials = AsyncMock(return_value=None)

        with patch("services.server_service.logger"):
            result = await server_service.get_credentials("srv-123")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_credentials_no_credential_manager(self, mock_db_service):
        """get_credentials should return None without credential manager."""
        with patch("services.server_service.CredentialManager") as MockCM, \
             patch("services.server_service.logger"):
            MockCM.side_effect = ValueError("No key")
            service = ServerService(mock_db_service)
            mock_db_service.get_server_credentials = AsyncMock(return_value="encrypted")

            result = await service.get_credentials("srv-123")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_credentials_error(
        self, server_service, mock_db_service
    ):
        """get_credentials should return None on error."""
        mock_db_service.get_server_credentials = AsyncMock(
            side_effect=Exception("DB error")
        )

        with patch("services.server_service.logger"):
            result = await server_service.get_credentials("srv-123")

        assert result is None


class TestUpdateCredentials:
    """Tests for update_credentials method."""

    @pytest.mark.asyncio
    async def test_update_credentials_success(
        self, server_service, mock_db_service, mock_credential_manager
    ):
        """update_credentials should encrypt and update credentials."""
        mock_db_service.update_server_credentials = AsyncMock(return_value=True)

        with patch("services.server_service.logger"):
            result = await server_service.update_credentials(
                "srv-123", {"password": "new_secret"}
            )

        assert result is True
        mock_credential_manager.encrypt_credentials.assert_called_once_with(
            {"password": "new_secret"}
        )
        mock_db_service.update_server_credentials.assert_called_once_with(
            "srv-123", "encrypted_data"
        )

    @pytest.mark.asyncio
    async def test_update_credentials_no_credential_manager(self, mock_db_service):
        """update_credentials should return False without credential manager."""
        with patch("services.server_service.CredentialManager") as MockCM, \
             patch("services.server_service.logger"):
            MockCM.side_effect = ValueError("No key")
            service = ServerService(mock_db_service)

            result = await service.update_credentials("srv-123", {"password": "new"})

            assert result is False

    @pytest.mark.asyncio
    async def test_update_credentials_error(
        self, server_service, mock_db_service
    ):
        """update_credentials should return False on error."""
        mock_db_service.update_server_credentials = AsyncMock(
            side_effect=Exception("DB error")
        )

        with patch("services.server_service.logger"):
            result = await server_service.update_credentials(
                "srv-123", {"password": "new"}
            )

        assert result is False


class TestUpdateServer:
    """Tests for update_server method."""

    @pytest.mark.asyncio
    async def test_update_server(self, server_service, mock_db_service):
        """update_server should delegate to db_service."""
        mock_db_service.update_server = AsyncMock(return_value=True)

        result = await server_service.update_server(
            server_id="srv-123",
            name="New Name",
            host="192.168.1.2",
        )

        assert result is True
        mock_db_service.update_server.assert_called_once_with(
            server_id="srv-123",
            name="New Name",
            host="192.168.1.2",
            port=None,
            username=None,
            auth_type=None,
        )


class TestUpdateServerStatus:
    """Tests for update_server_status method."""

    @pytest.mark.asyncio
    async def test_update_server_status(self, server_service, mock_db_service):
        """update_server_status should update status value."""
        mock_db_service.update_server = AsyncMock(return_value=True)

        result = await server_service.update_server_status(
            "srv-123", ServerStatus.CONNECTED
        )

        assert result is True
        mock_db_service.update_server.assert_called_once_with(
            server_id="srv-123",
            status="connected",
        )


class TestDeleteServer:
    """Tests for delete_server method."""

    @pytest.mark.asyncio
    async def test_delete_server(self, server_service, mock_db_service):
        """delete_server should delegate to db_service."""
        mock_db_service.delete_server = AsyncMock(return_value=True)

        result = await server_service.delete_server("srv-123")

        assert result is True
        mock_db_service.delete_server.assert_called_once_with("srv-123")


class TestUpdateServerSystemInfo:
    """Tests for update_server_system_info method."""

    @pytest.mark.asyncio
    async def test_update_system_info_with_docker(self, server_service, mock_db_service):
        """update_server_system_info should detect docker_installed."""
        mock_db_service.update_server = AsyncMock(return_value=True)

        with patch("services.server_service.logger"):
            result = await server_service.update_server_system_info(
                "srv-123",
                {
                    "docker_version": "24.0.1",
                    "os": "Ubuntu 22.04",
                    "agent_status": "connected",
                    "agent_version": "1.0.0",
                },
            )

        assert result is True
        call_kwargs = mock_db_service.update_server.call_args.kwargs
        assert call_kwargs["docker_installed"] == 1

    @pytest.mark.asyncio
    async def test_update_system_info_without_docker(
        self, server_service, mock_db_service
    ):
        """update_server_system_info should handle no docker."""
        mock_db_service.update_server = AsyncMock(return_value=True)

        with patch("services.server_service.logger"):
            result = await server_service.update_server_system_info(
                "srv-123",
                {"docker_version": "not installed", "os": "Ubuntu 22.04"},
            )

        assert result is True
        call_kwargs = mock_db_service.update_server.call_args.kwargs
        assert call_kwargs["docker_installed"] == 0

    @pytest.mark.asyncio
    async def test_update_system_info_docker_na(
        self, server_service, mock_db_service
    ):
        """update_server_system_info should handle docker_version='n/a'."""
        mock_db_service.update_server = AsyncMock(return_value=True)

        with patch("services.server_service.logger"):
            result = await server_service.update_server_system_info(
                "srv-123",
                {"docker_version": "n/a"},
            )

        assert result is True
        call_kwargs = mock_db_service.update_server.call_args.kwargs
        assert call_kwargs["docker_installed"] == 0

    @pytest.mark.asyncio
    async def test_update_system_info_stores_json(
        self, server_service, mock_db_service
    ):
        """update_server_system_info should store system_info as JSON."""
        import json

        mock_db_service.update_server = AsyncMock(return_value=True)
        system_info = {"os": "Ubuntu", "docker_version": "24.0.1"}

        with patch("services.server_service.logger"):
            await server_service.update_server_system_info("srv-123", system_info)

        call_kwargs = mock_db_service.update_server.call_args.kwargs
        stored_info = json.loads(call_kwargs["system_info"])
        assert stored_info["os"] == "Ubuntu"

    @pytest.mark.asyncio
    async def test_update_system_info_logs_success(
        self, server_service, mock_db_service
    ):
        """update_server_system_info should log on success."""
        mock_db_service.update_server = AsyncMock(return_value=True)

        with patch("services.server_service.logger") as mock_logger:
            await server_service.update_server_system_info(
                "srv-123",
                {"docker_version": "24.0.1", "agent_status": "active"},
            )

            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args.kwargs
            assert call_kwargs["server_id"] == "srv-123"
            assert call_kwargs["docker_installed"] is True

    @pytest.mark.asyncio
    async def test_update_system_info_error(self, server_service, mock_db_service):
        """update_server_system_info should return False on error."""
        mock_db_service.update_server = AsyncMock(side_effect=Exception("DB error"))

        with patch("services.server_service.logger"):
            result = await server_service.update_server_system_info(
                "srv-123",
                {"docker_version": "24.0.1"},
            )

        assert result is False

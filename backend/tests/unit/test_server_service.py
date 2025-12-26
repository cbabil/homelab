"""Tests for server service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.server_service import ServerService
from models.server import AuthType


class TestServerService:
    """Tests for ServerService."""

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = MagicMock()
        db.create_server = AsyncMock()
        db.get_server_by_id = AsyncMock()
        db.get_all_servers_from_db = AsyncMock(return_value=[])
        db.update_server = AsyncMock(return_value=True)
        db.delete_server = AsyncMock(return_value=True)
        db.get_server_credentials = AsyncMock()
        return db

    @pytest.fixture
    def mock_credential_manager(self):
        """Create mock credential manager."""
        cm = MagicMock()
        cm.encrypt_credentials = MagicMock(return_value="encrypted-data")
        cm.decrypt_credentials = MagicMock(return_value={"password": "secret"})
        return cm

    @pytest.fixture
    def server_service(self, mock_db_service, mock_credential_manager):
        """Create server service with mocks."""
        with patch('services.server_service.CredentialManager', return_value=mock_credential_manager):
            service = ServerService(db_service=mock_db_service)
            return service

    @pytest.mark.asyncio
    async def test_add_server_with_password(self, server_service, mock_db_service):
        """Should add server with encrypted password."""
        mock_db_service.create_server.return_value = MagicMock(id="server-123")

        result = await server_service.add_server(
            server_id="server-123",
            name="Test",
            host="192.168.1.100",
            port=22,
            username="admin",
            auth_type="password",
            credentials={"password": "secret123"}
        )

        assert result is not None
        mock_db_service.create_server.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_credentials_decrypts(self, server_service, mock_db_service, mock_credential_manager):
        """Should decrypt credentials when retrieving."""
        mock_db_service.get_server_credentials.return_value = "encrypted-data"

        result = await server_service.get_credentials("server-123")

        assert result == {"password": "secret"}
        mock_credential_manager.decrypt_credentials.assert_called_with("encrypted-data")

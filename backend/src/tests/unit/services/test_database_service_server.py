"""
Unit tests for services/database_service.py - Server method delegation.

Tests server-related methods that delegate to ServerDatabaseService.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.server import ServerConnection


@pytest.fixture
def mock_server_service():
    """Create mock ServerDatabaseService."""
    return MagicMock()


@pytest.fixture
def db_service_with_server_mock(mock_server_service):
    """Create DatabaseService with mocked server service."""
    with (
        patch("services.database_service.DatabaseConnection"),
        patch("services.database_service.UserDatabaseService"),
        patch("services.database_service.ServerDatabaseService") as MockServer,
        patch("services.database_service.SessionDatabaseService"),
        patch("services.database_service.AppDatabaseService"),
        patch("services.database_service.MetricsDatabaseService"),
        patch("services.database_service.SystemDatabaseService"),
        patch("services.database_service.ExportDatabaseService"),
        patch("services.database_service.SchemaInitializer"),
    ):
        from services.database_service import DatabaseService

        MockServer.return_value = mock_server_service
        return DatabaseService()


@pytest.fixture
def sample_server():
    """Create sample ServerConnection."""
    from models.server import AuthType, ServerStatus

    return ServerConnection(
        id="srv-123",
        name="Test Server",
        host="192.168.1.100",
        port=22,
        username="admin",
        auth_type=AuthType.PASSWORD,
        status=ServerStatus.CONNECTED,
        created_at="2024-01-15T10:00:00Z",
    )


class TestCreateServer:
    """Tests for create_server method."""

    @pytest.mark.asyncio
    async def test_create_server_success(
        self, db_service_with_server_mock, mock_server_service, sample_server
    ):
        """create_server should delegate to server service."""
        mock_server_service.create_server = AsyncMock(return_value=sample_server)

        result = await db_service_with_server_mock.create_server(
            id="srv-123",
            name="Test Server",
            host="192.168.1.100",
            port=22,
            username="admin",
            auth_type="password",
            encrypted_credentials="encrypted",
        )

        mock_server_service.create_server.assert_awaited_once_with(
            "srv-123",
            "Test Server",
            "192.168.1.100",
            22,
            "admin",
            "password",
            "encrypted",
        )
        assert result == sample_server

    @pytest.mark.asyncio
    async def test_create_server_failure(
        self, db_service_with_server_mock, mock_server_service
    ):
        """create_server should return None on failure."""
        mock_server_service.create_server = AsyncMock(return_value=None)

        result = await db_service_with_server_mock.create_server(
            id="srv-123",
            name="Test",
            host="host",
            port=22,
            username="user",
            auth_type="password",
            encrypted_credentials="creds",
        )

        assert result is None


class TestGetServerById:
    """Tests for get_server_by_id method."""

    @pytest.mark.asyncio
    async def test_get_server_by_id_found(
        self, db_service_with_server_mock, mock_server_service, sample_server
    ):
        """get_server_by_id should return server when found."""
        mock_server_service.get_server_by_id = AsyncMock(return_value=sample_server)

        result = await db_service_with_server_mock.get_server_by_id("srv-123")

        mock_server_service.get_server_by_id.assert_awaited_once_with("srv-123")
        assert result == sample_server

    @pytest.mark.asyncio
    async def test_get_server_by_id_not_found(
        self, db_service_with_server_mock, mock_server_service
    ):
        """get_server_by_id should return None when not found."""
        mock_server_service.get_server_by_id = AsyncMock(return_value=None)

        result = await db_service_with_server_mock.get_server_by_id("nonexistent")

        assert result is None


class TestGetServerByConnection:
    """Tests for get_server_by_connection method."""

    @pytest.mark.asyncio
    async def test_get_server_by_connection_found(
        self, db_service_with_server_mock, mock_server_service, sample_server
    ):
        """get_server_by_connection should return server when found."""
        mock_server_service.get_server_by_connection = AsyncMock(
            return_value=sample_server
        )

        result = await db_service_with_server_mock.get_server_by_connection(
            host="192.168.1.100", port=22, username="admin"
        )

        mock_server_service.get_server_by_connection.assert_awaited_once_with(
            "192.168.1.100", 22, "admin"
        )
        assert result == sample_server

    @pytest.mark.asyncio
    async def test_get_server_by_connection_not_found(
        self, db_service_with_server_mock, mock_server_service
    ):
        """get_server_by_connection should return None when not found."""
        mock_server_service.get_server_by_connection = AsyncMock(return_value=None)

        result = await db_service_with_server_mock.get_server_by_connection(
            host="unknown", port=22, username="user"
        )

        assert result is None


class TestGetAllServersFromDb:
    """Tests for get_all_servers_from_db method."""

    @pytest.mark.asyncio
    async def test_get_all_servers_returns_list(
        self, db_service_with_server_mock, mock_server_service, sample_server
    ):
        """get_all_servers_from_db should return list of servers."""
        mock_server_service.get_all_servers_from_db = AsyncMock(
            return_value=[sample_server]
        )

        result = await db_service_with_server_mock.get_all_servers_from_db()

        mock_server_service.get_all_servers_from_db.assert_awaited_once()
        assert result == [sample_server]

    @pytest.mark.asyncio
    async def test_get_all_servers_empty(
        self, db_service_with_server_mock, mock_server_service
    ):
        """get_all_servers_from_db should return empty list when none."""
        mock_server_service.get_all_servers_from_db = AsyncMock(return_value=[])

        result = await db_service_with_server_mock.get_all_servers_from_db()

        assert result == []


class TestGetServerCredentials:
    """Tests for get_server_credentials method."""

    @pytest.mark.asyncio
    async def test_get_server_credentials_found(
        self, db_service_with_server_mock, mock_server_service
    ):
        """get_server_credentials should return encrypted credentials."""
        mock_server_service.get_server_credentials = AsyncMock(
            return_value="encrypted_creds"
        )

        result = await db_service_with_server_mock.get_server_credentials("srv-123")

        mock_server_service.get_server_credentials.assert_awaited_once_with("srv-123")
        assert result == "encrypted_creds"

    @pytest.mark.asyncio
    async def test_get_server_credentials_not_found(
        self, db_service_with_server_mock, mock_server_service
    ):
        """get_server_credentials should return None when not found."""
        mock_server_service.get_server_credentials = AsyncMock(return_value=None)

        result = await db_service_with_server_mock.get_server_credentials("nonexistent")

        assert result is None


class TestUpdateServerCredentials:
    """Tests for update_server_credentials method."""

    @pytest.mark.asyncio
    async def test_update_server_credentials_success(
        self, db_service_with_server_mock, mock_server_service
    ):
        """update_server_credentials should delegate to server service."""
        mock_server_service.update_server_credentials = AsyncMock(return_value=True)

        result = await db_service_with_server_mock.update_server_credentials(
            "srv-123", "new_encrypted_creds"
        )

        mock_server_service.update_server_credentials.assert_awaited_once_with(
            "srv-123", "new_encrypted_creds"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_update_server_credentials_failure(
        self, db_service_with_server_mock, mock_server_service
    ):
        """update_server_credentials should return False on failure."""
        mock_server_service.update_server_credentials = AsyncMock(return_value=False)

        result = await db_service_with_server_mock.update_server_credentials(
            "unknown", "creds"
        )

        assert result is False


class TestUpdateServer:
    """Tests for update_server method."""

    @pytest.mark.asyncio
    async def test_update_server_success(
        self, db_service_with_server_mock, mock_server_service
    ):
        """update_server should delegate kwargs to server service."""
        mock_server_service.update_server = AsyncMock(return_value=True)

        result = await db_service_with_server_mock.update_server(
            "srv-123", name="New Name", status="offline"
        )

        mock_server_service.update_server.assert_awaited_once_with(
            "srv-123", name="New Name", status="offline"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_update_server_single_field(
        self, db_service_with_server_mock, mock_server_service
    ):
        """update_server should handle single field update."""
        mock_server_service.update_server = AsyncMock(return_value=True)

        result = await db_service_with_server_mock.update_server(
            "srv-123", host="192.168.1.200"
        )

        mock_server_service.update_server.assert_awaited_once_with(
            "srv-123", host="192.168.1.200"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_update_server_failure(
        self, db_service_with_server_mock, mock_server_service
    ):
        """update_server should return False on failure."""
        mock_server_service.update_server = AsyncMock(return_value=False)

        result = await db_service_with_server_mock.update_server("unknown", name="X")

        assert result is False


class TestDeleteServer:
    """Tests for delete_server method."""

    @pytest.mark.asyncio
    async def test_delete_server_success(
        self, db_service_with_server_mock, mock_server_service
    ):
        """delete_server should delegate to server service."""
        mock_server_service.delete_server = AsyncMock(return_value=True)

        result = await db_service_with_server_mock.delete_server("srv-123")

        mock_server_service.delete_server.assert_awaited_once_with("srv-123")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_server_failure(
        self, db_service_with_server_mock, mock_server_service
    ):
        """delete_server should return False on failure."""
        mock_server_service.delete_server = AsyncMock(return_value=False)

        result = await db_service_with_server_mock.delete_server("nonexistent")

        assert result is False

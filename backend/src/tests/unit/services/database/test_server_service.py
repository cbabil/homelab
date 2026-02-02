"""
Unit tests for services/database/server_service.py.

Tests ServerDatabaseService methods.
"""

import pytest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from services.database.server_service import ServerDatabaseService
from models.server import ServerStatus


@pytest.fixture
def mock_connection():
    """Create mock DatabaseConnection."""
    return MagicMock()


@pytest.fixture
def service(mock_connection):
    """Create ServerDatabaseService instance."""
    return ServerDatabaseService(mock_connection)


def create_mock_context(mock_conn):
    """Create async context manager for database connection."""
    @asynccontextmanager
    async def context():
        yield mock_conn
    return context()


@pytest.fixture
def sample_server_row():
    """Create sample server row from database."""
    return {
        "id": "server-123",
        "name": "Test Server",
        "host": "192.168.1.100",
        "port": 22,
        "username": "admin",
        "auth_type": "password",
        "status": "connected",
        "created_at": "2024-01-15T10:00:00",
        "last_connected": "2024-01-15T11:00:00",
        "system_info": '{"os": "Linux", "kernel": "5.4.0", "architecture": "x86_64"}',
        "docker_installed": 1,
        "system_info_updated_at": "2024-01-15T10:30:00",
    }


class TestServerDatabaseServiceInit:
    """Tests for ServerDatabaseService initialization."""

    def test_init_stores_connection(self, mock_connection):
        """Service should store connection reference."""
        service = ServerDatabaseService(mock_connection)
        assert service._conn is mock_connection


class TestCreateServer:
    """Tests for create_server method."""

    @pytest.mark.asyncio
    async def test_create_server_success(self, service, mock_connection):
        """create_server should return ServerConnection on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.create_server(
                id="server-123",
                name="Test Server",
                host="192.168.1.100",
                port=22,
                username="admin",
                auth_type="password",
                encrypted_credentials="encrypted_data",
            )

        assert result is not None
        assert result.id == "server-123"
        assert result.status == ServerStatus.DISCONNECTED
        assert mock_conn.execute.call_count == 2
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_server_exception(self, service, mock_connection):
        """create_server should return None on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.server_service.logger"):
            result = await service.create_server(
                id="s", name="n", host="h", port=22,
                username="u", auth_type="password", encrypted_credentials="e"
            )

        assert result is None


class TestGetServerByConnection:
    """Tests for get_server_by_connection method."""

    @pytest.mark.asyncio
    async def test_get_server_by_connection_found(self, service, mock_connection, sample_server_row):
        """get_server_by_connection should return server when found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=sample_server_row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.get_server_by_connection("192.168.1.100", 22, "admin")

        assert result is not None
        assert result.host == "192.168.1.100"
        assert result.system_info is not None

    @pytest.mark.asyncio
    async def test_get_server_by_connection_not_found(self, service, mock_connection):
        """get_server_by_connection should return None when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.get_server_by_connection("unknown", 22, "user")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_server_by_connection_invalid_system_info(self, service, mock_connection, sample_server_row):
        """get_server_by_connection should handle invalid system_info JSON."""
        row = dict(sample_server_row)
        row["system_info"] = "invalid json"
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.get_server_by_connection("192.168.1.100", 22, "admin")

        assert result is not None
        assert result.system_info is None

    @pytest.mark.asyncio
    async def test_get_server_by_connection_null_system_info(self, service, mock_connection, sample_server_row):
        """get_server_by_connection should handle null system_info."""
        row = dict(sample_server_row)
        row["system_info"] = None
        row["docker_installed"] = None
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.get_server_by_connection("192.168.1.100", 22, "admin")

        assert result is not None
        assert result.system_info is None
        assert result.docker_installed is False

    @pytest.mark.asyncio
    async def test_get_server_by_connection_exception(self, service, mock_connection):
        """get_server_by_connection should return None on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.server_service.logger"):
            result = await service.get_server_by_connection("host", 22, "user")

        assert result is None


class TestGetServerById:
    """Tests for get_server_by_id method."""

    @pytest.mark.asyncio
    async def test_get_server_by_id_found(self, service, mock_connection, sample_server_row):
        """get_server_by_id should return server when found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=sample_server_row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.get_server_by_id("server-123")

        assert result is not None
        assert result.id == "server-123"

    @pytest.mark.asyncio
    async def test_get_server_by_id_not_found(self, service, mock_connection):
        """get_server_by_id should return None when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.get_server_by_id("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_server_by_id_exception(self, service, mock_connection):
        """get_server_by_id should return None on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.server_service.logger"):
            result = await service.get_server_by_id("server-123")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_server_by_id_type_error_in_system_info(self, service, mock_connection, sample_server_row):
        """get_server_by_id should handle TypeError when system_info is non-dict JSON."""
        row = dict(sample_server_row)
        # Valid JSON but not a dict - will cause TypeError when unpacking with **
        row["system_info"] = '[1, 2, 3]'
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.get_server_by_id("server-123")

        assert result is not None
        assert result.system_info is None


class TestGetAllServersFromDb:
    """Tests for get_all_servers_from_db method."""

    @pytest.mark.asyncio
    async def test_get_all_servers_success(self, service, mock_connection, sample_server_row):
        """get_all_servers_from_db should return list of servers."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[sample_server_row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.get_all_servers_from_db()

        assert len(result) == 1
        assert result[0].id == "server-123"

    @pytest.mark.asyncio
    async def test_get_all_servers_empty(self, service, mock_connection):
        """get_all_servers_from_db should return empty list when none."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.get_all_servers_from_db()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_servers_invalid_system_info(self, service, mock_connection, sample_server_row):
        """get_all_servers_from_db should handle invalid system_info."""
        row = dict(sample_server_row)
        row["system_info"] = "not json"
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.get_all_servers_from_db()

        assert len(result) == 1
        assert result[0].system_info is None

    @pytest.mark.asyncio
    async def test_get_all_servers_exception(self, service, mock_connection):
        """get_all_servers_from_db should return empty list on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.server_service.logger"):
            result = await service.get_all_servers_from_db()

        assert result == []


class TestGetServerCredentials:
    """Tests for get_server_credentials method."""

    @pytest.mark.asyncio
    async def test_get_server_credentials_found(self, service, mock_connection):
        """get_server_credentials should return credentials when found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value={"encrypted_data": "secret"})
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.get_server_credentials("server-123")

        assert result == "secret"

    @pytest.mark.asyncio
    async def test_get_server_credentials_not_found(self, service, mock_connection):
        """get_server_credentials should return None when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.get_server_credentials("unknown")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_server_credentials_exception(self, service, mock_connection):
        """get_server_credentials should return None on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.server_service.logger"):
            result = await service.get_server_credentials("server-123")

        assert result is None


class TestUpdateServerCredentials:
    """Tests for update_server_credentials method."""

    @pytest.mark.asyncio
    async def test_update_server_credentials_success(self, service, mock_connection):
        """update_server_credentials should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.update_server_credentials("server-123", "new_creds")

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_server_credentials_exception(self, service, mock_connection):
        """update_server_credentials should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.server_service.logger"):
            result = await service.update_server_credentials("server-123", "creds")

        assert result is False


class TestUpdateServer:
    """Tests for update_server method."""

    @pytest.mark.asyncio
    async def test_update_server_success(self, service, mock_connection):
        """update_server should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.update_server("server-123", status="connected")

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_server_no_updates(self, service, mock_connection):
        """update_server should return True when no updates provided."""
        with patch("services.database.server_service.logger"):
            result = await service.update_server("server-123")

        assert result is True

    @pytest.mark.asyncio
    async def test_update_server_invalid_column(self, service, mock_connection):
        """update_server should reject invalid column names."""
        with patch("services.database.server_service.logger"):
            result = await service.update_server("server-123", invalid_col="value")

        assert result is False

    @pytest.mark.asyncio
    async def test_update_server_multiple_fields(self, service, mock_connection):
        """update_server should handle multiple fields."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.update_server(
                "server-123", status="connected", name="New Name"
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_update_server_exception(self, service, mock_connection):
        """update_server should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.server_service.logger"):
            result = await service.update_server("server-123", status="connected")

        assert result is False


class TestDeleteServer:
    """Tests for delete_server method."""

    @pytest.mark.asyncio
    async def test_delete_server_success(self, service, mock_connection):
        """delete_server should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.server_service.logger"):
            result = await service.delete_server("server-123")

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_server_exception(self, service, mock_connection):
        """delete_server should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.server_service.logger"):
            result = await service.delete_server("server-123")

        assert result is False

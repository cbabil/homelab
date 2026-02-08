"""
Unit tests for services/database/export_service.py

Tests backup import and export operations.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.database.export_service import ExportDatabaseService


@pytest.fixture
def mock_connection():
    """Create mock DatabaseConnection."""
    return MagicMock()


@pytest.fixture
def export_service(mock_connection):
    """Create ExportDatabaseService instance."""
    return ExportDatabaseService(mock_connection)


def create_mock_context(mock_conn):
    """Create async context manager for database connection."""

    @asynccontextmanager
    async def context():
        yield mock_conn

    return context()


class TestExportDatabaseServiceInit:
    """Tests for ExportDatabaseService initialization."""

    def test_init_stores_connection(self, mock_connection):
        """ExportDatabaseService should store connection reference."""
        service = ExportDatabaseService(mock_connection)
        assert service._conn is mock_connection


class TestExportUsers:
    """Tests for export_users method."""

    @pytest.mark.asyncio
    async def test_export_users_success(self, export_service, mock_connection):
        """export_users should return list of user dicts."""
        mock_rows = [
            {
                "id": "u1",
                "username": "admin",
                "email": "a@b.c",
                "role": "admin",
                "is_active": 1,
                "created_at": "2024-01-01",
            },
            {
                "id": "u2",
                "username": "user",
                "email": "d@e.f",
                "role": "user",
                "is_active": 1,
                "created_at": "2024-01-02",
            },
        ]
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = mock_rows

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await export_service.export_users()

        assert len(result) == 2
        assert result[0]["username"] == "admin"
        assert result[1]["username"] == "user"

    @pytest.mark.asyncio
    async def test_export_users_empty(self, export_service, mock_connection):
        """export_users should return empty list when no users."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await export_service.export_users()

        assert result == []

    @pytest.mark.asyncio
    async def test_export_users_error_returns_empty(
        self, export_service, mock_connection
    ):
        """export_users should return empty list on error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.export_service.logger"):
            result = await export_service.export_users()

        assert result == []


class TestExportServers:
    """Tests for export_servers method."""

    @pytest.mark.asyncio
    async def test_export_servers_success(self, export_service, mock_connection):
        """export_servers should return list of server dicts."""
        mock_rows = [
            {"id": "s1", "name": "Server 1", "host": "192.168.1.1"},
            {"id": "s2", "name": "Server 2", "host": "192.168.1.2"},
        ]
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = mock_rows

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await export_service.export_servers()

        assert len(result) == 2
        assert result[0]["name"] == "Server 1"

    @pytest.mark.asyncio
    async def test_export_servers_error_returns_empty(
        self, export_service, mock_connection
    ):
        """export_servers should return empty list on error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.export_service.logger"):
            result = await export_service.export_servers()

        assert result == []


class TestExportSettings:
    """Tests for export_settings method."""

    @pytest.mark.asyncio
    async def test_export_settings_success(self, export_service, mock_connection):
        """export_settings should return dict of settings."""
        mock_rows = [
            {"key": "theme", "value": "dark"},
            {"key": "language", "value": "en"},
        ]
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = mock_rows

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await export_service.export_settings()

        assert result == {"theme": "dark", "language": "en"}

    @pytest.mark.asyncio
    async def test_export_settings_empty(self, export_service, mock_connection):
        """export_settings should return empty dict when no settings."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await export_service.export_settings()

        assert result == {}

    @pytest.mark.asyncio
    async def test_export_settings_error_returns_empty(
        self, export_service, mock_connection
    ):
        """export_settings should return empty dict on error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.export_service.logger"):
            result = await export_service.export_settings()

        assert result == {}


class TestImportUsers:
    """Tests for import_users method."""

    @pytest.mark.asyncio
    async def test_import_users_success(self, export_service, mock_connection):
        """import_users should insert users."""
        users = [
            {"id": "u1", "username": "admin", "email": "a@b.c"},
            {"id": "u2", "username": "user"},
        ]

        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.export_service.logger"):
            await export_service.import_users(users)

        # Should have 2 insert calls (no delete calls without overwrite)
        assert mock_conn.execute.call_count == 2
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_users_with_overwrite(self, export_service, mock_connection):
        """import_users with overwrite should delete before insert."""
        users = [{"id": "u1", "username": "admin"}]

        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.export_service.logger"):
            await export_service.import_users(users, overwrite=True)

        # Should have 2 calls: 1 delete + 1 insert
        assert mock_conn.execute.call_count == 2
        # First call should be DELETE
        first_call = mock_conn.execute.call_args_list[0]
        assert "DELETE" in first_call[0][0]

    @pytest.mark.asyncio
    async def test_import_users_error_raises(self, export_service, mock_connection):
        """import_users should raise on error."""
        users = [{"id": "u1", "username": "admin"}]

        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.export_service.logger"):
            with pytest.raises(Exception):
                await export_service.import_users(users)

    @pytest.mark.asyncio
    async def test_import_users_uses_defaults(self, export_service, mock_connection):
        """import_users should use default values for missing fields."""
        users = [{"id": "u1", "username": "admin"}]  # Missing email, role, etc.

        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.export_service.logger"):
            await export_service.import_users(users)

        # Check the insert call has defaults
        call_args = mock_conn.execute.call_args_list[0][0]
        params = call_args[1]
        assert params[2] is None  # email defaults to None
        assert params[3] == "user"  # role defaults to "user"
        assert params[4] == 1  # is_active defaults to 1


class TestImportServers:
    """Tests for import_servers method."""

    @pytest.mark.asyncio
    async def test_import_servers_success(self, export_service, mock_connection):
        """import_servers should insert servers."""
        servers = [
            {"id": "s1", "name": "Server 1", "host": "192.168.1.1"},
        ]

        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.export_service.logger"):
            await export_service.import_servers(servers)

        mock_conn.execute.assert_called()
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_servers_with_overwrite(self, export_service, mock_connection):
        """import_servers with overwrite should delete before insert."""
        servers = [{"id": "s1", "name": "Server", "host": "127.0.0.1"}]

        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.export_service.logger"):
            await export_service.import_servers(servers, overwrite=True)

        # Should have 2 calls: 1 delete + 1 insert
        assert mock_conn.execute.call_count == 2
        first_call = mock_conn.execute.call_args_list[0]
        assert "DELETE" in first_call[0][0]

    @pytest.mark.asyncio
    async def test_import_servers_error_raises(self, export_service, mock_connection):
        """import_servers should raise on error."""
        servers = [{"id": "s1", "name": "Server", "host": "127.0.0.1"}]

        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.export_service.logger"):
            with pytest.raises(Exception):
                await export_service.import_servers(servers)

    @pytest.mark.asyncio
    async def test_import_servers_uses_defaults(self, export_service, mock_connection):
        """import_servers should use default values for missing fields."""
        servers = [{"id": "s1", "name": "Server", "host": "127.0.0.1"}]

        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.export_service.logger"):
            await export_service.import_servers(servers)

        call_args = mock_conn.execute.call_args_list[0][0]
        params = call_args[1]
        assert params[3] == 22  # port defaults to 22
        assert params[7] == "unknown"  # status defaults to "unknown"


class TestImportSettings:
    """Tests for import_settings method."""

    @pytest.mark.asyncio
    async def test_import_settings_success(self, export_service, mock_connection):
        """import_settings should insert settings."""
        settings = {"theme": "dark", "language": "en"}

        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.export_service.logger"):
            await export_service.import_settings(settings)

        assert mock_conn.execute.call_count == 2
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_settings_with_overwrite(
        self, export_service, mock_connection
    ):
        """import_settings with overwrite should use INSERT OR REPLACE."""
        settings = {"theme": "dark"}

        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.export_service.logger"):
            await export_service.import_settings(settings, overwrite=True)

        call_args = mock_conn.execute.call_args_list[0][0]
        assert "INSERT OR REPLACE" in call_args[0]

    @pytest.mark.asyncio
    async def test_import_settings_without_overwrite(
        self, export_service, mock_connection
    ):
        """import_settings without overwrite should use INSERT OR IGNORE."""
        settings = {"theme": "dark"}

        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.export_service.logger"):
            await export_service.import_settings(settings, overwrite=False)

        call_args = mock_conn.execute.call_args_list[0][0]
        assert "INSERT OR IGNORE" in call_args[0]

    @pytest.mark.asyncio
    async def test_import_settings_error_raises(self, export_service, mock_connection):
        """import_settings should raise on error."""
        settings = {"theme": "dark"}

        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.export_service.logger"):
            with pytest.raises(Exception):
                await export_service.import_settings(settings)

    @pytest.mark.asyncio
    async def test_import_settings_empty(self, export_service, mock_connection):
        """import_settings with empty dict should still commit."""
        settings = {}

        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.export_service.logger"):
            await export_service.import_settings(settings)

        mock_conn.execute.assert_not_called()
        mock_conn.commit.assert_called_once()

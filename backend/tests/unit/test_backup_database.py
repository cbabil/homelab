"""Tests for backup database operations."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager


class TestBackupDatabaseOperations:
    """Tests for backup export/import in database."""

    @pytest.mark.asyncio
    async def test_export_users(self):
        """Should export all users."""
        from services.database_service import DatabaseService

        mock_rows = [
            {"id": "u1", "username": "admin", "email": "admin@test.com",
             "role": "admin", "is_active": 1, "created_at": "2025-01-01"}
        ]

        mock_connection = MagicMock()
        cursor = MagicMock()
        cursor.fetchall = AsyncMock(return_value=mock_rows)
        mock_connection.execute = AsyncMock(return_value=cursor)

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_connection

        db_service = DatabaseService(data_directory="/tmp/test")
        with patch.object(db_service, 'get_connection', mock_get_connection):
            result = await db_service.export_users()

        assert len(result) == 1
        assert result[0]["username"] == "admin"

    @pytest.mark.asyncio
    async def test_export_servers(self):
        """Should export all servers."""
        from services.database_service import DatabaseService

        mock_rows = [
            {"id": "s1", "name": "server1", "host": "192.168.1.1",
             "port": 22, "username": "root", "auth_type": "password"}
        ]

        mock_connection = MagicMock()
        cursor = MagicMock()
        cursor.fetchall = AsyncMock(return_value=mock_rows)
        mock_connection.execute = AsyncMock(return_value=cursor)

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_connection

        db_service = DatabaseService(data_directory="/tmp/test")
        with patch.object(db_service, 'get_connection', mock_get_connection):
            result = await db_service.export_servers()

        assert len(result) == 1
        assert result[0]["name"] == "server1"

    @pytest.mark.asyncio
    async def test_import_users(self):
        """Should import users."""
        from services.database_service import DatabaseService

        users = [
            {"id": "u1", "username": "admin", "email": "admin@test.com"}
        ]

        mock_connection = MagicMock()
        mock_connection.execute = AsyncMock()
        mock_connection.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_connection

        db_service = DatabaseService(data_directory="/tmp/test")
        with patch.object(db_service, 'get_connection', mock_get_connection):
            await db_service.import_users(users, overwrite=True)

        mock_connection.execute.assert_called()

    @pytest.mark.asyncio
    async def test_import_servers(self):
        """Should import servers."""
        from services.database_service import DatabaseService

        servers = [
            {"id": "s1", "name": "server1", "host": "192.168.1.1"}
        ]

        mock_connection = MagicMock()
        mock_connection.execute = AsyncMock()
        mock_connection.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_connection

        db_service = DatabaseService(data_directory="/tmp/test")
        with patch.object(db_service, 'get_connection', mock_get_connection):
            await db_service.import_servers(servers, overwrite=True)

        mock_connection.execute.assert_called()

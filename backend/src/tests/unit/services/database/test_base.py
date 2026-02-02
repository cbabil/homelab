"""
Unit tests for services/database/base.py

Tests database connection manager and column whitelists.
"""

import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path

from services.database.base import (
    DatabaseConnection,
    ALLOWED_SERVER_COLUMNS,
    ALLOWED_INSTALLATION_COLUMNS,
    ALLOWED_SYSTEM_INFO_COLUMNS,
)


class TestAllowedColumns:
    """Tests for column whitelist constants."""

    def test_server_columns_is_frozenset(self):
        """ALLOWED_SERVER_COLUMNS should be a frozenset."""
        assert isinstance(ALLOWED_SERVER_COLUMNS, frozenset)

    def test_server_columns_contains_name(self):
        """ALLOWED_SERVER_COLUMNS should contain 'name'."""
        assert "name" in ALLOWED_SERVER_COLUMNS

    def test_server_columns_contains_host(self):
        """ALLOWED_SERVER_COLUMNS should contain 'host'."""
        assert "host" in ALLOWED_SERVER_COLUMNS

    def test_server_columns_contains_status(self):
        """ALLOWED_SERVER_COLUMNS should contain 'status'."""
        assert "status" in ALLOWED_SERVER_COLUMNS

    def test_installation_columns_is_frozenset(self):
        """ALLOWED_INSTALLATION_COLUMNS should be a frozenset."""
        assert isinstance(ALLOWED_INSTALLATION_COLUMNS, frozenset)

    def test_installation_columns_contains_status(self):
        """ALLOWED_INSTALLATION_COLUMNS should contain 'status'."""
        assert "status" in ALLOWED_INSTALLATION_COLUMNS

    def test_installation_columns_contains_container_id(self):
        """ALLOWED_INSTALLATION_COLUMNS should contain 'container_id'."""
        assert "container_id" in ALLOWED_INSTALLATION_COLUMNS

    def test_system_info_columns_is_frozenset(self):
        """ALLOWED_SYSTEM_INFO_COLUMNS should be a frozenset."""
        assert isinstance(ALLOWED_SYSTEM_INFO_COLUMNS, frozenset)

    def test_system_info_columns_contains_app_name(self):
        """ALLOWED_SYSTEM_INFO_COLUMNS should contain 'app_name'."""
        assert "app_name" in ALLOWED_SYSTEM_INFO_COLUMNS


class TestDatabaseConnectionInit:
    """Tests for DatabaseConnection initialization."""

    def test_init_with_db_path(self, tmp_path):
        """DatabaseConnection should accept db_path."""
        db_file = tmp_path / "test.db"
        conn = DatabaseConnection(db_path=db_file)
        assert conn.db_path == str(db_file)

    def test_init_with_data_directory(self, tmp_path):
        """DatabaseConnection should use data_directory/tomo.db."""
        conn = DatabaseConnection(data_directory=tmp_path)
        assert conn.db_path == str(tmp_path / "tomo.db")

    def test_init_with_neither_uses_default(self):
        """DatabaseConnection should use default 'data' directory."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("services.database.base.os.getenv", return_value="data"):
                conn = DatabaseConnection()
                assert "data" in conn.db_path
                assert conn.db_path.endswith("tomo.db")

    def test_init_with_env_data_directory(self, tmp_path):
        """DatabaseConnection should use DATA_DIRECTORY env var."""
        with patch.dict("os.environ", {"DATA_DIRECTORY": str(tmp_path)}):
            conn = DatabaseConnection()
            assert conn.db_path == str(tmp_path / "tomo.db")

    def test_init_with_both_raises_value_error(self, tmp_path):
        """DatabaseConnection should raise if both db_path and data_directory given."""
        db_file = tmp_path / "test.db"
        with pytest.raises(ValueError) as exc_info:
            DatabaseConnection(db_path=db_file, data_directory=tmp_path)
        assert "not both" in str(exc_info.value)

    def test_init_relative_db_path(self):
        """DatabaseConnection should resolve relative db_path."""
        conn = DatabaseConnection(db_path="relative/path.db")
        assert Path(conn.db_path).is_absolute()

    def test_init_relative_data_directory(self):
        """DatabaseConnection should resolve relative data_directory."""
        conn = DatabaseConnection(data_directory="relative/data")
        assert Path(conn.db_path).is_absolute()

    def test_init_absolute_db_path(self, tmp_path):
        """DatabaseConnection should keep absolute db_path."""
        db_file = tmp_path / "test.db"
        conn = DatabaseConnection(db_path=db_file)
        assert conn.db_path == str(db_file)

    def test_init_logs_message(self, tmp_path):
        """DatabaseConnection should log initialization."""
        with patch("services.database.base.logger") as mock_logger:
            DatabaseConnection(db_path=tmp_path / "test.db")
            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args.kwargs
            assert "db_path" in call_kwargs


class TestPathProperty:
    """Tests for path property."""

    def test_path_returns_db_path(self, tmp_path):
        """path property should return db_path."""
        db_file = tmp_path / "test.db"
        conn = DatabaseConnection(db_path=db_file)
        assert conn.path == str(db_file)

    def test_path_same_as_db_path(self, tmp_path):
        """path property should equal db_path attribute."""
        db_file = tmp_path / "test.db"
        conn = DatabaseConnection(db_path=db_file)
        assert conn.path == conn.db_path


class TestGetConnection:
    """Tests for get_connection async context manager."""

    @pytest.mark.asyncio
    async def test_get_connection_yields_connection(self, tmp_path):
        """get_connection should yield an aiosqlite connection."""
        db_file = tmp_path / "test.db"
        db_file.touch()
        conn = DatabaseConnection(db_path=db_file)

        async with conn.get_connection() as db:
            # Should be able to execute queries
            await db.execute("SELECT 1")

    @pytest.mark.asyncio
    async def test_get_connection_sets_row_factory(self, tmp_path):
        """get_connection should set row_factory to aiosqlite.Row."""
        import aiosqlite

        db_file = tmp_path / "test.db"
        db_file.touch()
        conn = DatabaseConnection(db_path=db_file)

        async with conn.get_connection() as db:
            assert db.row_factory == aiosqlite.Row

    @pytest.mark.asyncio
    async def test_get_connection_rollback_on_exception(self, tmp_path):
        """get_connection should rollback on exception."""
        db_file = tmp_path / "test.db"
        db_file.touch()
        conn = DatabaseConnection(db_path=db_file)

        mock_connection = AsyncMock()
        mock_connection.row_factory = None

        # Create mock context manager
        async def mock_connect(*args, **kwargs):
            return mock_connection

        mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection.__aexit__ = AsyncMock(return_value=False)

        with patch("services.database.base.aiosqlite.connect", return_value=mock_connection):
            with pytest.raises(RuntimeError):
                async with conn.get_connection():
                    raise RuntimeError("Test error")

            mock_connection.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_connection_creates_database(self, tmp_path):
        """get_connection should create database file if not exists."""
        db_file = tmp_path / "new_database.db"
        assert not db_file.exists()

        conn = DatabaseConnection(db_path=db_file)
        async with conn.get_connection() as db:
            await db.execute("SELECT 1")

        assert db_file.exists()

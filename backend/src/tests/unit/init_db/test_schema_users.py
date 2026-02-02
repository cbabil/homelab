"""
Users Schema Unit Tests

Tests for schema_users.py - SQL schema, migrations, and initialization.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from init_db.schema_users import (
    USERS_SCHEMA,
    _migrate_add_password_changed_at,
    initialize_users_schema,
)


class TestUsersSchema:
    """Tests for USERS_SCHEMA constant."""

    def test_schema_is_string(self):
        """Test that schema is a non-empty string."""
        assert isinstance(USERS_SCHEMA, str)
        assert len(USERS_SCHEMA) > 0

    def test_schema_creates_table(self):
        """Test that schema contains CREATE TABLE statement."""
        assert "CREATE TABLE IF NOT EXISTS users" in USERS_SCHEMA

    def test_schema_has_required_columns(self):
        """Test that schema has all required columns."""
        required_columns = [
            "id TEXT PRIMARY KEY",
            "username TEXT NOT NULL UNIQUE",
            "email TEXT",
            "password_hash TEXT NOT NULL",
            "role TEXT NOT NULL",
            "created_at TEXT",
            "last_login TEXT",
            "password_changed_at TEXT",
            "is_active INTEGER",
            "preferences_json TEXT",
            "avatar TEXT",
        ]
        for column in required_columns:
            assert column in USERS_SCHEMA, f"Missing column: {column}"

    def test_schema_has_role_check(self):
        """Test that role has CHECK constraint."""
        assert "CHECK (role IN ('admin', 'user', 'readonly'))" in USERS_SCHEMA

    def test_schema_has_is_active_check(self):
        """Test that is_active has CHECK constraint."""
        assert "CHECK (is_active IN (0, 1))" in USERS_SCHEMA

    def test_schema_has_indexes(self):
        """Test that schema creates required indexes."""
        indexes = [
            "idx_users_username",
            "idx_users_email",
            "idx_users_role",
            "idx_users_active",
            "idx_users_created_at",
        ]
        for index in indexes:
            assert index in USERS_SCHEMA, f"Missing index: {index}"


class TestMigrateAddPasswordChangedAt:
    """Tests for _migrate_add_password_changed_at function."""

    @pytest.mark.asyncio
    async def test_migration_adds_column_when_missing(self):
        """Test migration adds column when it doesn't exist."""
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[
            (0, "id", "TEXT", 0, None, 1),
            (1, "username", "TEXT", 1, None, 0),
        ])
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        with patch("init_db.schema_users.logger"):
            await _migrate_add_password_changed_at(mock_conn)

        # Should have called execute 3 times: PRAGMA, ALTER TABLE, UPDATE
        assert mock_conn.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_migration_skips_when_column_exists(self):
        """Test migration skips when column already exists."""
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[
            (0, "id", "TEXT", 0, None, 1),
            (1, "username", "TEXT", 1, None, 0),
            (2, "password_changed_at", "TEXT", 0, None, 0),
        ])
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        with patch("init_db.schema_users.logger"):
            await _migrate_add_password_changed_at(mock_conn)

        # Should have called execute only once for PRAGMA
        assert mock_conn.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_migration_handles_exception(self):
        """Test migration handles exception gracefully."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("DB error"))

        with patch("init_db.schema_users.logger") as mock_logger:
            await _migrate_add_password_changed_at(mock_conn)
            mock_logger.warning.assert_called()


class TestInitializeUsersSchema:
    """Tests for initialize_users_schema function."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        manager = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.executescript = AsyncMock()
        mock_conn.commit = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[
            (0, "password_changed_at", "TEXT", 0, None, 0),
        ])
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        manager.get_connection = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(return_value=None),
        ))
        return manager, mock_conn

    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_db_manager):
        """Test successful schema initialization."""
        manager, mock_conn = mock_db_manager

        with patch("init_db.schema_users.logger"):
            result = await initialize_users_schema(manager)

        assert result is True
        mock_conn.executescript.assert_called_once_with(USERS_SCHEMA)

    @pytest.mark.asyncio
    async def test_initialize_creates_manager_if_none(self):
        """Test that function creates DatabaseManager if none provided."""
        mock_conn = AsyncMock()
        mock_conn.executescript = AsyncMock()
        mock_conn.commit = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[
            (0, "password_changed_at", "TEXT", 0, None, 0),
        ])
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        mock_manager = MagicMock()
        mock_manager.get_connection = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(return_value=None),
        ))

        with (
            patch("init_db.schema_users.DatabaseManager",
                  return_value=mock_manager),
            patch("init_db.schema_users.logger"),
        ):
            result = await initialize_users_schema(None)

        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_handles_exception(self, mock_db_manager):
        """Test that function handles exceptions gracefully."""
        manager, mock_conn = mock_db_manager
        mock_conn.executescript.side_effect = Exception("Database error")

        with patch("init_db.schema_users.logger"):
            result = await initialize_users_schema(manager)

        assert result is False

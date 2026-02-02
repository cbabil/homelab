"""
Notifications Schema Unit Tests

Tests for schema_notifications.py - SQL schema and initialization.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from init_db.schema_notifications import (
    NOTIFICATIONS_SCHEMA,
    initialize_notifications_schema,
)


class TestNotificationsSchema:
    """Tests for NOTIFICATIONS_SCHEMA constant."""

    def test_schema_is_string(self):
        """Test that schema is a non-empty string."""
        assert isinstance(NOTIFICATIONS_SCHEMA, str)
        assert len(NOTIFICATIONS_SCHEMA) > 0

    def test_schema_creates_table(self):
        """Test that schema contains CREATE TABLE statement."""
        assert "CREATE TABLE IF NOT EXISTS notifications" in NOTIFICATIONS_SCHEMA

    def test_schema_has_required_columns(self):
        """Test that schema has all required columns."""
        required_columns = [
            "id TEXT PRIMARY KEY",
            "user_id TEXT NOT NULL",
            "type TEXT NOT NULL",
            "title TEXT NOT NULL",
            "message TEXT NOT NULL",
            "read INTEGER NOT NULL",
            "created_at TEXT NOT NULL",
            "read_at TEXT",
            "dismissed_at TEXT",
            "expires_at TEXT",
            "source TEXT",
            "metadata TEXT",
        ]
        for column in required_columns:
            assert column in NOTIFICATIONS_SCHEMA, f"Missing column: {column}"

    def test_schema_has_type_check(self):
        """Test that type has CHECK constraint."""
        assert "CHECK (type IN ('info', 'success', 'warning', 'error'))" in NOTIFICATIONS_SCHEMA

    def test_schema_has_foreign_key(self):
        """Test that schema has foreign key to users."""
        assert "FOREIGN KEY (user_id) REFERENCES users(id)" in NOTIFICATIONS_SCHEMA

    def test_schema_has_indexes(self):
        """Test that schema creates required indexes."""
        indexes = [
            "idx_notifications_user_id",
            "idx_notifications_read",
            "idx_notifications_created_at",
            "idx_notifications_type",
            "idx_notifications_user_read",
        ]
        for index in indexes:
            assert index in NOTIFICATIONS_SCHEMA, f"Missing index: {index}"


class TestInitializeNotificationsSchema:
    """Tests for initialize_notifications_schema function."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        manager = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.executescript = AsyncMock()
        mock_conn.commit = AsyncMock()

        manager.get_connection = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(return_value=None),
        ))
        return manager, mock_conn

    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_db_manager):
        """Test successful schema initialization."""
        manager, mock_conn = mock_db_manager

        with patch("init_db.schema_notifications.logger"):
            result = await initialize_notifications_schema(manager)

        assert result is True
        mock_conn.executescript.assert_called_once_with(NOTIFICATIONS_SCHEMA)
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_creates_manager_if_none(self):
        """Test that function creates DatabaseManager if none provided."""
        mock_conn = AsyncMock()
        mock_conn.executescript = AsyncMock()
        mock_conn.commit = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.get_connection = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(return_value=None),
        ))

        with (
            patch("init_db.schema_notifications.DatabaseManager",
                  return_value=mock_manager),
            patch("init_db.schema_notifications.logger"),
        ):
            result = await initialize_notifications_schema(None)

        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_handles_exception(self, mock_db_manager):
        """Test that function handles exceptions gracefully."""
        manager, mock_conn = mock_db_manager
        mock_conn.executescript.side_effect = Exception("Database error")

        with patch("init_db.schema_notifications.logger"):
            result = await initialize_notifications_schema(manager)

        assert result is False

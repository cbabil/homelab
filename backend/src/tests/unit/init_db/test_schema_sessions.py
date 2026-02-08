"""
Sessions Schema Unit Tests

Tests for schema_sessions.py - SQL schema and initialization.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from init_db.schema_sessions import (
    SESSIONS_SCHEMA,
    initialize_sessions_schema,
)


class TestSessionsSchema:
    """Tests for SESSIONS_SCHEMA constant."""

    def test_schema_is_string(self):
        """Test that schema is a non-empty string."""
        assert isinstance(SESSIONS_SCHEMA, str)
        assert len(SESSIONS_SCHEMA) > 0

    def test_schema_creates_table(self):
        """Test that schema contains CREATE TABLE statement."""
        assert "CREATE TABLE IF NOT EXISTS sessions" in SESSIONS_SCHEMA

    def test_schema_has_required_columns(self):
        """Test that schema has all required columns."""
        required_columns = [
            "id TEXT PRIMARY KEY",
            "user_id TEXT NOT NULL",
            "ip_address TEXT",
            "user_agent TEXT",
            "created_at TEXT NOT NULL",
            "expires_at TEXT NOT NULL",
            "last_activity TEXT NOT NULL",
            "status TEXT NOT NULL",
            "terminated_at TEXT",
            "terminated_by TEXT",
        ]
        for column in required_columns:
            assert column in SESSIONS_SCHEMA, f"Missing column: {column}"

    def test_schema_has_status_check(self):
        """Test that status has CHECK constraint."""
        assert (
            "CHECK (status IN ('active', 'idle', 'expired', 'terminated'))"
            in SESSIONS_SCHEMA
        )

    def test_schema_has_foreign_key(self):
        """Test that schema has foreign key to users."""
        assert "FOREIGN KEY (user_id) REFERENCES users(id)" in SESSIONS_SCHEMA

    def test_schema_has_indexes(self):
        """Test that schema creates required indexes."""
        indexes = [
            "idx_sessions_user_id",
            "idx_sessions_status",
            "idx_sessions_expires_at",
            "idx_sessions_last_activity",
        ]
        for index in indexes:
            assert index in SESSIONS_SCHEMA, f"Missing index: {index}"


class TestInitializeSessionsSchema:
    """Tests for initialize_sessions_schema function."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        manager = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.executescript = AsyncMock()
        mock_conn.commit = AsyncMock()

        manager.get_connection = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_conn),
                __aexit__=AsyncMock(return_value=None),
            )
        )
        return manager, mock_conn

    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_db_manager):
        """Test successful schema initialization."""
        manager, mock_conn = mock_db_manager

        with patch("init_db.schema_sessions.logger"):
            result = await initialize_sessions_schema(manager)

        assert result is True
        mock_conn.executescript.assert_called_once_with(SESSIONS_SCHEMA)
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_creates_manager_if_none(self):
        """Test that function creates DatabaseManager if none provided."""
        mock_conn = AsyncMock()
        mock_conn.executescript = AsyncMock()
        mock_conn.commit = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.get_connection = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_conn),
                __aexit__=AsyncMock(return_value=None),
            )
        )

        with (
            patch("init_db.schema_sessions.DatabaseManager", return_value=mock_manager),
            patch("init_db.schema_sessions.logger"),
        ):
            result = await initialize_sessions_schema(None)

        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_handles_exception(self, mock_db_manager):
        """Test that function handles exceptions gracefully."""
        manager, mock_conn = mock_db_manager
        mock_conn.executescript.side_effect = Exception("Database error")

        with patch("init_db.schema_sessions.logger"):
            result = await initialize_sessions_schema(manager)

        assert result is False

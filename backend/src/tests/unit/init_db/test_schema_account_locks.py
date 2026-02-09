"""
Account Locks Schema Unit Tests

Tests for schema_account_locks.py - SQL schema and initialization.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from init_db.schema_account_locks import (
    ACCOUNT_LOCKS_SCHEMA,
    initialize_account_locks_schema,
)


class TestAccountLocksSchema:
    """Tests for ACCOUNT_LOCKS_SCHEMA constant."""

    def test_schema_is_string(self):
        """Test that schema is a non-empty string."""
        assert isinstance(ACCOUNT_LOCKS_SCHEMA, str)
        assert len(ACCOUNT_LOCKS_SCHEMA) > 0

    def test_schema_creates_table(self):
        """Test that schema contains CREATE TABLE statement."""
        assert "CREATE TABLE IF NOT EXISTS account_locks" in ACCOUNT_LOCKS_SCHEMA

    def test_schema_has_required_columns(self):
        """Test that schema has all required columns."""
        required_columns = [
            "id TEXT PRIMARY KEY",
            "identifier TEXT NOT NULL",
            "identifier_type TEXT NOT NULL",
            "attempt_count INTEGER",
            "first_attempt_at TEXT",
            "last_attempt_at TEXT",
            "locked_at TEXT",
            "lock_expires_at TEXT",
            "ip_address TEXT",
            "user_agent TEXT",
            "reason TEXT",
            "unlocked_at TEXT",
            "unlocked_by TEXT",
            "notes TEXT",
        ]
        for column in required_columns:
            assert column in ACCOUNT_LOCKS_SCHEMA, f"Missing column: {column}"

    def test_schema_has_identifier_type_check(self):
        """Test that identifier_type has CHECK constraint."""
        assert "CHECK (identifier_type IN ('username', 'ip'))" in ACCOUNT_LOCKS_SCHEMA

    def test_schema_has_unique_constraint(self):
        """Test that schema has UNIQUE constraint."""
        assert "UNIQUE(identifier, identifier_type)" in ACCOUNT_LOCKS_SCHEMA

    def test_schema_has_indexes(self):
        """Test that schema creates required indexes."""
        indexes = [
            "idx_account_locks_identifier",
            "idx_account_locks_identifier_type",
            "idx_account_locks_locked_at",
            "idx_account_locks_lock_expires_at",
            "idx_account_locks_ip_address",
        ]
        for index in indexes:
            assert index in ACCOUNT_LOCKS_SCHEMA, f"Missing index: {index}"


class TestInitializeAccountLocksSchema:
    """Tests for initialize_account_locks_schema function."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        manager = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.executescript = AsyncMock()
        mock_conn.commit = AsyncMock()

        async def mock_get_connection():
            return mock_conn

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

        with patch("init_db.schema_account_locks.logger"):
            result = await initialize_account_locks_schema(manager)

        assert result is True
        mock_conn.executescript.assert_called_once_with(ACCOUNT_LOCKS_SCHEMA)
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_creates_manager_if_none(self):
        """Test that function creates DatabaseService if none provided."""
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
            patch(
                "init_db.schema_account_locks.DatabaseService",
                return_value=mock_manager,
            ),
            patch("init_db.schema_account_locks.logger"),
        ):
            result = await initialize_account_locks_schema(None)

        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_handles_exception(self, mock_db_manager):
        """Test that function handles exceptions gracefully."""
        manager, mock_conn = mock_db_manager
        mock_conn.executescript.side_effect = Exception("Database error")

        with patch("init_db.schema_account_locks.logger"):
            result = await initialize_account_locks_schema(manager)

        assert result is False

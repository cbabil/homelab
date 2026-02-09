"""
System Info Schema Unit Tests

Tests for schema_system_info.py - SQL schema and initialization.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from init_db.schema_system_info import (
    SYSTEM_INFO_SCHEMA,
    check_system_info_exists,
    initialize_system_info_schema,
)


class TestSystemInfoSchema:
    """Tests for SYSTEM_INFO_SCHEMA constant."""

    def test_schema_is_string(self):
        """Test that schema is a non-empty string."""
        assert isinstance(SYSTEM_INFO_SCHEMA, str)
        assert len(SYSTEM_INFO_SCHEMA) > 0

    def test_schema_creates_table(self):
        """Test that schema contains CREATE TABLE statement."""
        assert "CREATE TABLE IF NOT EXISTS system_info" in SYSTEM_INFO_SCHEMA

    def test_schema_has_required_columns(self):
        """Test that schema has all required columns."""
        required_columns = [
            "id INTEGER PRIMARY KEY",
            "app_name TEXT NOT NULL",
            "is_setup INTEGER NOT NULL",
            "setup_completed_at TEXT",
            "setup_by_user_id TEXT",
            "installation_id TEXT NOT NULL",
            "license_type TEXT",
            "license_key TEXT",
            "license_expires_at TEXT",
            "created_at TEXT NOT NULL",
            "updated_at TEXT NOT NULL",
        ]
        for column in required_columns:
            assert column in SYSTEM_INFO_SCHEMA, f"Missing column: {column}"

    def test_schema_has_single_row_check(self):
        """Test that id has CHECK constraint for single row."""
        assert "CHECK (id = 1)" in SYSTEM_INFO_SCHEMA

    def test_schema_has_is_setup_check(self):
        """Test that is_setup has CHECK constraint."""
        assert "CHECK (is_setup IN (0, 1))" in SYSTEM_INFO_SCHEMA

    def test_schema_has_license_type_check(self):
        """Test that license_type has CHECK constraint."""
        assert (
            "CHECK (license_type IN ('community', 'pro', 'enterprise'))"
            in SYSTEM_INFO_SCHEMA
        )

    def test_schema_inserts_default_row(self):
        """Test that schema inserts default system info row."""
        assert "INSERT OR IGNORE INTO system_info" in SYSTEM_INFO_SCHEMA
        assert "randomblob(16)" in SYSTEM_INFO_SCHEMA  # Installation ID generation

    def test_schema_has_update_trigger(self):
        """Test that schema creates update trigger."""
        assert (
            "CREATE TRIGGER IF NOT EXISTS system_info_updated_at" in SYSTEM_INFO_SCHEMA
        )
        assert "AFTER UPDATE ON system_info" in SYSTEM_INFO_SCHEMA

    def test_schema_has_index(self):
        """Test that schema creates index."""
        assert "idx_system_info_is_setup" in SYSTEM_INFO_SCHEMA


class TestInitializeSystemInfoSchema:
    """Tests for initialize_system_info_schema function."""

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

        with patch("init_db.schema_system_info.logger"):
            result = await initialize_system_info_schema(manager)

        assert result is True
        mock_conn.executescript.assert_called_once_with(SYSTEM_INFO_SCHEMA)
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
                "init_db.schema_system_info.DatabaseService", return_value=mock_manager
            ),
            patch("init_db.schema_system_info.logger"),
        ):
            result = await initialize_system_info_schema(None)

        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_handles_exception(self, mock_db_manager):
        """Test that function handles exceptions gracefully."""
        manager, mock_conn = mock_db_manager
        mock_conn.executescript.side_effect = Exception("Database error")

        with patch("init_db.schema_system_info.logger"):
            result = await initialize_system_info_schema(manager)

        assert result is False


class TestCheckSystemInfoExists:
    """Tests for check_system_info_exists function."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        manager = MagicMock()
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        manager.get_connection = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_conn),
                __aexit__=AsyncMock(return_value=None),
            )
        )
        return manager, mock_cursor

    @pytest.mark.asyncio
    async def test_check_returns_true_when_exists(self, mock_db_manager):
        """Test that check returns True when table exists."""
        manager, mock_cursor = mock_db_manager
        mock_cursor.fetchone = AsyncMock(return_value=("system_info",))

        with patch("init_db.schema_system_info.logger"):
            result = await check_system_info_exists(manager)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_returns_false_when_not_exists(self, mock_db_manager):
        """Test that check returns False when table doesn't exist."""
        manager, mock_cursor = mock_db_manager
        mock_cursor.fetchone = AsyncMock(return_value=None)

        with patch("init_db.schema_system_info.logger"):
            result = await check_system_info_exists(manager)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_creates_manager_if_none(self):
        """Test that check creates DatabaseService if none provided."""
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=("system_info",))
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        mock_manager = MagicMock()
        mock_manager.get_connection = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_conn),
                __aexit__=AsyncMock(return_value=None),
            )
        )

        with (
            patch(
                "init_db.schema_system_info.DatabaseService", return_value=mock_manager
            ),
            patch("init_db.schema_system_info.logger"),
        ):
            result = await check_system_info_exists(None)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_handles_exception(self, mock_db_manager):
        """Test that check handles exceptions gracefully."""
        manager, mock_cursor = mock_db_manager
        mock_cursor.fetchone.side_effect = Exception("Database error")

        with patch("init_db.schema_system_info.logger"):
            result = await check_system_info_exists(manager)

        assert result is False

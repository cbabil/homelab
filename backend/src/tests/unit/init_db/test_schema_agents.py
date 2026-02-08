"""
Agents Schema Unit Tests

Tests for schema_agents.py - SQL schema and initialization.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from init_db.schema_agents import (
    AGENTS_SCHEMA,
    initialize_agents_schema,
    migrate_token_rotation_fields,
)


class TestAgentsSchema:
    """Tests for AGENTS_SCHEMA constant."""

    def test_schema_is_string(self):
        """Test that schema is a non-empty string."""
        assert isinstance(AGENTS_SCHEMA, str)
        assert len(AGENTS_SCHEMA) > 0

    def test_schema_creates_table(self):
        """Test that schema contains CREATE TABLE statement."""
        assert "CREATE TABLE IF NOT EXISTS agents" in AGENTS_SCHEMA

    def test_schema_has_required_columns(self):
        """Test that schema has all required columns."""
        required_columns = [
            "id TEXT PRIMARY KEY",
            "server_id TEXT",
            "token_hash TEXT",
            "status TEXT",
            "version TEXT",
            "last_seen TEXT",
            "registered_at TEXT",
        ]
        for column in required_columns:
            assert column in AGENTS_SCHEMA, f"Missing column: {column}"


class TestInitializeAgentsSchema:
    """Tests for initialize_agents_schema function."""

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

        with patch("init_db.schema_agents.logger"):
            result = await initialize_agents_schema(manager)

        assert result is True
        mock_conn.executescript.assert_called_once_with(AGENTS_SCHEMA)
        assert mock_conn.commit.call_count >= 1

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
            patch("init_db.schema_agents.DatabaseManager", return_value=mock_manager),
            patch("init_db.schema_agents.logger"),
        ):
            result = await initialize_agents_schema(None)

        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_handles_exception(self, mock_db_manager):
        """Test that function handles exceptions gracefully."""
        manager, mock_conn = mock_db_manager
        mock_conn.executescript.side_effect = Exception("Database error")

        with patch("init_db.schema_agents.logger"):
            result = await initialize_agents_schema(manager)

        assert result is False


class TestMigrateTokenRotationFields:
    """Tests for migrate_token_rotation_fields function."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager with configurable column state."""
        manager = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.commit = AsyncMock()

        manager.get_connection = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_conn),
                __aexit__=AsyncMock(return_value=None),
            )
        )
        return manager, mock_conn

    @pytest.mark.asyncio
    async def test_migration_on_fresh_database(self, mock_db_manager):
        """Test migration adds all three columns to fresh table."""
        manager, mock_conn = mock_db_manager

        # Fresh table has no rotation columns
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                (0, "id", "TEXT", 0, None, 1),
                (1, "server_id", "TEXT", 0, None, 0),
                (2, "token_hash", "TEXT", 0, None, 0),
                (3, "status", "TEXT", 0, None, 0),
            ]
        )
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        with patch("init_db.schema_agents.logger") as mock_logger:
            result = await migrate_token_rotation_fields(manager)

        assert result is True

        # Verify all three ALTER TABLE calls were made
        calls = [str(c) for c in mock_conn.execute.call_args_list]
        assert any("pending_token_hash" in c for c in calls)
        assert any("token_issued_at" in c for c in calls)
        assert any("token_expires_at" in c for c in calls)

        mock_conn.commit.assert_called_once()
        assert mock_logger.info.call_count >= 3  # One log per column + completion

    @pytest.mark.asyncio
    async def test_migration_on_existing_database_with_agents(self, mock_db_manager):
        """Test migration skips columns that already exist."""
        manager, mock_conn = mock_db_manager

        # Table already has rotation columns
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                (0, "id", "TEXT", 0, None, 1),
                (1, "server_id", "TEXT", 0, None, 0),
                (2, "token_hash", "TEXT", 0, None, 0),
                (3, "status", "TEXT", 0, None, 0),
                (4, "pending_token_hash", "TEXT", 0, None, 0),
                (5, "token_issued_at", "TEXT", 0, None, 0),
                (6, "token_expires_at", "TEXT", 0, None, 0),
            ]
        )
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        with patch("init_db.schema_agents.logger") as mock_logger:
            result = await migrate_token_rotation_fields(manager)

        assert result is True

        # Only PRAGMA call should happen, no ALTER TABLE
        execute_calls = mock_conn.execute.call_args_list
        assert len(execute_calls) == 1  # Only the PRAGMA table_info call
        assert "PRAGMA table_info" in str(execute_calls[0])

        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_migration_handles_partial_migration(self, mock_db_manager):
        """Test migration adds missing columns when some already exist."""
        manager, mock_conn = mock_db_manager

        # Table has only pending_token_hash, missing other two
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                (0, "id", "TEXT", 0, None, 1),
                (1, "server_id", "TEXT", 0, None, 0),
                (2, "pending_token_hash", "TEXT", 0, None, 0),
            ]
        )
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        with patch("init_db.schema_agents.logger") as mock_logger:
            result = await migrate_token_rotation_fields(manager)

        assert result is True

        # Should add token_issued_at and token_expires_at, but not pending_token_hash
        calls = [str(c) for c in mock_conn.execute.call_args_list]
        assert any("token_issued_at" in c for c in calls)
        assert any("token_expires_at" in c for c in calls)
        # pending_token_hash should not be in ALTER TABLE calls (only in PRAGMA result)
        alter_calls = [c for c in calls if "ALTER TABLE" in c]
        assert not any("pending_token_hash" in c for c in alter_calls)

    @pytest.mark.asyncio
    async def test_migration_handles_exception(self, mock_db_manager):
        """Test migration returns False on exception."""
        manager, mock_conn = mock_db_manager
        mock_conn.execute.side_effect = Exception("Database error")

        with patch("init_db.schema_agents.logger") as mock_logger:
            result = await migrate_token_rotation_fields(manager)

        assert result is False
        mock_logger.error.assert_called_once()

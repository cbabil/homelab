"""
Component Versions Schema Unit Tests

Tests for schema_component_versions.py - SQL schema and initialization.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from init_db.schema_component_versions import (
    COMPONENT_VERSIONS_SCHEMA,
    initialize_component_versions_schema,
    check_component_versions_exists,
)


class TestComponentVersionsSchema:
    """Tests for COMPONENT_VERSIONS_SCHEMA constant."""

    def test_schema_is_string(self):
        """Test that schema is a non-empty string."""
        assert isinstance(COMPONENT_VERSIONS_SCHEMA, str)
        assert len(COMPONENT_VERSIONS_SCHEMA) > 0

    def test_schema_creates_table(self):
        """Test that schema contains CREATE TABLE statement."""
        assert "CREATE TABLE IF NOT EXISTS component_versions" in COMPONENT_VERSIONS_SCHEMA

    def test_schema_has_required_columns(self):
        """Test that schema has all required columns."""
        required_columns = [
            "component TEXT PRIMARY KEY",
            "version TEXT NOT NULL",
            "updated_at TEXT NOT NULL",
            "created_at TEXT NOT NULL",
        ]
        for column in required_columns:
            assert column in COMPONENT_VERSIONS_SCHEMA, f"Missing column: {column}"

    def test_schema_has_component_check(self):
        """Test that component has CHECK constraint."""
        assert "CHECK (component IN ('backend', 'frontend', 'api'))" in COMPONENT_VERSIONS_SCHEMA

    def test_schema_inserts_default_values(self):
        """Test that schema inserts default component versions."""
        assert "INSERT OR IGNORE INTO component_versions" in COMPONENT_VERSIONS_SCHEMA
        assert "('backend', '1.0.0')" in COMPONENT_VERSIONS_SCHEMA
        assert "('frontend', '1.0.0')" in COMPONENT_VERSIONS_SCHEMA
        assert "('api', '1.0.0')" in COMPONENT_VERSIONS_SCHEMA

    def test_schema_has_update_trigger(self):
        """Test that schema creates update trigger."""
        assert "CREATE TRIGGER IF NOT EXISTS component_versions_updated_at" in COMPONENT_VERSIONS_SCHEMA
        assert "AFTER UPDATE ON component_versions" in COMPONENT_VERSIONS_SCHEMA


class TestInitializeComponentVersionsSchema:
    """Tests for initialize_component_versions_schema function."""

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

        with patch("init_db.schema_component_versions.logger"):
            result = await initialize_component_versions_schema(manager)

        assert result is True
        mock_conn.executescript.assert_called_once_with(COMPONENT_VERSIONS_SCHEMA)
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
            patch("init_db.schema_component_versions.DatabaseManager",
                  return_value=mock_manager),
            patch("init_db.schema_component_versions.logger"),
        ):
            result = await initialize_component_versions_schema(None)

        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_handles_exception(self, mock_db_manager):
        """Test that function handles exceptions gracefully."""
        manager, mock_conn = mock_db_manager
        mock_conn.executescript.side_effect = Exception("Database error")

        with patch("init_db.schema_component_versions.logger"):
            result = await initialize_component_versions_schema(manager)

        assert result is False


class TestCheckComponentVersionsExists:
    """Tests for check_component_versions_exists function."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        manager = MagicMock()
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        manager.get_connection = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(return_value=None),
        ))
        return manager, mock_cursor

    @pytest.mark.asyncio
    async def test_check_returns_true_when_exists(self, mock_db_manager):
        """Test that check returns True when table exists."""
        manager, mock_cursor = mock_db_manager
        mock_cursor.fetchone = AsyncMock(return_value=("component_versions",))

        with patch("init_db.schema_component_versions.logger"):
            result = await check_component_versions_exists(manager)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_returns_false_when_not_exists(self, mock_db_manager):
        """Test that check returns False when table doesn't exist."""
        manager, mock_cursor = mock_db_manager
        mock_cursor.fetchone = AsyncMock(return_value=None)

        with patch("init_db.schema_component_versions.logger"):
            result = await check_component_versions_exists(manager)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_creates_manager_if_none(self):
        """Test that check creates DatabaseManager if none provided."""
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=("component_versions",))
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        mock_manager = MagicMock()
        mock_manager.get_connection = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(return_value=None),
        ))

        with (
            patch("init_db.schema_component_versions.DatabaseManager",
                  return_value=mock_manager),
            patch("init_db.schema_component_versions.logger"),
        ):
            result = await check_component_versions_exists(None)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_handles_exception(self, mock_db_manager):
        """Test that check handles exceptions gracefully."""
        manager, mock_cursor = mock_db_manager
        mock_cursor.fetchone.side_effect = Exception("Database error")

        with patch("init_db.schema_component_versions.logger"):
            result = await check_component_versions_exists(manager)

        assert result is False

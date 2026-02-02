"""
Marketplace Schema Unit Tests

Tests for schema_marketplace.py - SQLAlchemy-based schema initialization.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestCreateMarketplaceSchema:
    """Tests for create_marketplace_schema function."""

    @pytest.mark.asyncio
    async def test_create_schema_success(self):
        """Test successful schema creation."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.begin = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(return_value=None),
        ))
        mock_conn.run_sync = AsyncMock()

        with (
            patch("init_db.schema_marketplace.db_manager") as mock_db_manager,
            patch("init_db.schema_marketplace.Base") as mock_base,
            patch("init_db.schema_marketplace.logger"),
        ):
            mock_db_manager.initialize = AsyncMock()
            mock_db_manager.engine = mock_engine
            mock_base.metadata.create_all = MagicMock()

            from init_db.schema_marketplace import create_marketplace_schema
            await create_marketplace_schema()

            mock_db_manager.initialize.assert_called_once()
            mock_conn.run_sync.assert_called_once()


class TestCheckMarketplaceSchemaExists:
    """Tests for check_marketplace_schema_exists function."""

    @pytest.mark.asyncio
    async def test_check_returns_true_when_exists(self):
        """Test that check returns True when table exists."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.begin = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(return_value=None),
        ))
        # Simulate table exists
        mock_conn.run_sync = AsyncMock(return_value=("marketplace_repos",))

        with (
            patch("init_db.schema_marketplace.db_manager") as mock_db_manager,
            patch("init_db.schema_marketplace.logger"),
        ):
            mock_db_manager.initialize = AsyncMock()
            mock_db_manager.engine = mock_engine

            from init_db.schema_marketplace import check_marketplace_schema_exists
            result = await check_marketplace_schema_exists()

            assert result is True

    @pytest.mark.asyncio
    async def test_check_returns_false_when_not_exists(self):
        """Test that check returns False when table doesn't exist."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.begin = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(return_value=None),
        ))
        # Simulate table doesn't exist
        mock_conn.run_sync = AsyncMock(return_value=None)

        with (
            patch("init_db.schema_marketplace.db_manager") as mock_db_manager,
            patch("init_db.schema_marketplace.logger"),
        ):
            mock_db_manager.initialize = AsyncMock()
            mock_db_manager.engine = mock_engine

            from init_db.schema_marketplace import check_marketplace_schema_exists
            result = await check_marketplace_schema_exists()

            assert result is False


class TestMigrateMarketplaceSchema:
    """Tests for migrate_marketplace_schema function."""

    @pytest.mark.asyncio
    async def test_migrate_adds_column_when_missing(self):
        """Test that migration adds maintainers column when missing."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.begin = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(return_value=None),
        ))
        # Simulate PRAGMA table_info returning columns without 'maintainers'
        mock_conn.run_sync = AsyncMock(side_effect=[
            [(0, "id", "TEXT", 0, None, 1), (1, "name", "TEXT", 0, None, 0)],
            None,  # ALTER TABLE result
        ])

        with (
            patch("init_db.schema_marketplace.db_manager") as mock_db_manager,
            patch("init_db.schema_marketplace.logger"),
        ):
            mock_db_manager.initialize = AsyncMock()
            mock_db_manager.engine = mock_engine

            from init_db.schema_marketplace import migrate_marketplace_schema
            await migrate_marketplace_schema()

            # Should have called run_sync twice: PRAGMA and ALTER TABLE
            assert mock_conn.run_sync.call_count == 2

    @pytest.mark.asyncio
    async def test_migrate_skips_when_column_exists(self):
        """Test that migration skips when maintainers column exists."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.begin = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(return_value=None),
        ))
        # Simulate PRAGMA table_info returning columns with 'maintainers'
        mock_conn.run_sync = AsyncMock(return_value=[
            (0, "id", "TEXT", 0, None, 1),
            (1, "name", "TEXT", 0, None, 0),
            (2, "maintainers", "TEXT", 0, None, 0),
        ])

        with (
            patch("init_db.schema_marketplace.db_manager") as mock_db_manager,
            patch("init_db.schema_marketplace.logger"),
        ):
            mock_db_manager.initialize = AsyncMock()
            mock_db_manager.engine = mock_engine

            from init_db.schema_marketplace import migrate_marketplace_schema
            await migrate_marketplace_schema()

            # Should have called run_sync only once for PRAGMA
            mock_conn.run_sync.assert_called_once()


class TestInitializeMarketplaceDatabase:
    """Tests for initialize_marketplace_database function."""

    @pytest.mark.asyncio
    async def test_initialize_creates_schema_when_not_exists(self):
        """Test that initialize creates schema when it doesn't exist."""
        with (
            patch("init_db.schema_marketplace.check_marketplace_schema_exists",
                  new_callable=AsyncMock) as mock_check,
            patch("init_db.schema_marketplace.create_marketplace_schema",
                  new_callable=AsyncMock) as mock_create,
            patch("init_db.schema_marketplace.migrate_marketplace_schema",
                  new_callable=AsyncMock) as mock_migrate,
            patch("init_db.schema_marketplace.logger"),
        ):
            mock_check.return_value = False

            from init_db.schema_marketplace import initialize_marketplace_database
            await initialize_marketplace_database()

            mock_check.assert_called_once()
            mock_create.assert_called_once()
            mock_migrate.assert_not_called()

    @pytest.mark.asyncio
    async def test_initialize_runs_migrations_when_exists(self):
        """Test that initialize runs migrations when schema exists."""
        with (
            patch("init_db.schema_marketplace.check_marketplace_schema_exists",
                  new_callable=AsyncMock) as mock_check,
            patch("init_db.schema_marketplace.create_marketplace_schema",
                  new_callable=AsyncMock) as mock_create,
            patch("init_db.schema_marketplace.migrate_marketplace_schema",
                  new_callable=AsyncMock) as mock_migrate,
            patch("init_db.schema_marketplace.logger"),
        ):
            mock_check.return_value = True

            from init_db.schema_marketplace import initialize_marketplace_database
            await initialize_marketplace_database()

            mock_check.assert_called_once()
            mock_create.assert_not_called()
            mock_migrate.assert_called_once()

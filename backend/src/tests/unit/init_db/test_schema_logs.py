"""
Logs Schema Unit Tests

Tests for schema_logs.py - SQLAlchemy-based schema initialization.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCreateLogsSchema:
    """Tests for create_logs_schema function."""

    @pytest.mark.asyncio
    async def test_create_schema_success(self):
        """Test successful schema creation."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.begin = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_conn),
                __aexit__=AsyncMock(return_value=None),
            )
        )
        mock_conn.run_sync = AsyncMock()

        with (
            patch("init_db.schema_logs.db_manager") as mock_db_manager,
            patch("init_db.schema_logs.Base") as mock_base,
            patch("init_db.schema_logs.logger"),
        ):
            mock_db_manager.initialize = AsyncMock()
            mock_db_manager.engine = mock_engine
            mock_base.metadata.create_all = MagicMock()

            from init_db.schema_logs import create_logs_schema

            await create_logs_schema()

            mock_db_manager.initialize.assert_called_once()
            mock_conn.run_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_schema_raises_on_error(self):
        """Test that create_logs_schema raises on error."""
        with (
            patch("init_db.schema_logs.db_manager") as mock_db_manager,
            patch("init_db.schema_logs.logger"),
        ):
            mock_db_manager.initialize = AsyncMock(side_effect=Exception("DB error"))

            from init_db.schema_logs import create_logs_schema

            with pytest.raises(Exception, match="DB error"):
                await create_logs_schema()


class TestCheckSchemaExists:
    """Tests for check_schema_exists function."""

    @pytest.mark.asyncio
    async def test_check_returns_true_when_exists(self):
        """Test that check returns True when table exists."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.begin = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_conn),
                __aexit__=AsyncMock(return_value=None),
            )
        )
        # Simulate table exists
        mock_conn.run_sync = AsyncMock(return_value=("log_entries",))

        with (
            patch("init_db.schema_logs.db_manager") as mock_db_manager,
            patch("init_db.schema_logs.logger"),
        ):
            mock_db_manager.initialize = AsyncMock()
            mock_db_manager.engine = mock_engine

            from init_db.schema_logs import check_schema_exists

            result = await check_schema_exists()

            assert result is True

    @pytest.mark.asyncio
    async def test_check_returns_false_when_not_exists(self):
        """Test that check returns False when table doesn't exist."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.begin = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_conn),
                __aexit__=AsyncMock(return_value=None),
            )
        )
        # Simulate table doesn't exist
        mock_conn.run_sync = AsyncMock(return_value=None)

        with (
            patch("init_db.schema_logs.db_manager") as mock_db_manager,
            patch("init_db.schema_logs.logger"),
        ):
            mock_db_manager.initialize = AsyncMock()
            mock_db_manager.engine = mock_engine

            from init_db.schema_logs import check_schema_exists

            result = await check_schema_exists()

            assert result is False

    @pytest.mark.asyncio
    async def test_check_returns_false_on_error(self):
        """Test that check returns False on error."""
        with (
            patch("init_db.schema_logs.db_manager") as mock_db_manager,
            patch("init_db.schema_logs.logger"),
        ):
            mock_db_manager.initialize = AsyncMock(side_effect=Exception("DB error"))

            from init_db.schema_logs import check_schema_exists

            result = await check_schema_exists()

            assert result is False


class TestInitializeLogsDatabase:
    """Tests for initialize_logs_database function."""

    @pytest.mark.asyncio
    async def test_initialize_creates_schema_when_not_exists(self):
        """Test that initialize creates schema when it doesn't exist."""
        with (
            patch(
                "init_db.schema_logs.check_schema_exists", new_callable=AsyncMock
            ) as mock_check,
            patch(
                "init_db.schema_logs.create_logs_schema", new_callable=AsyncMock
            ) as mock_create,
            patch("init_db.schema_logs.logger"),
        ):
            mock_check.return_value = False

            from init_db.schema_logs import initialize_logs_database

            await initialize_logs_database()

            mock_check.assert_called_once()
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_skips_creation_when_exists(self):
        """Test that initialize skips creation when schema exists."""
        with (
            patch(
                "init_db.schema_logs.check_schema_exists", new_callable=AsyncMock
            ) as mock_check,
            patch(
                "init_db.schema_logs.create_logs_schema", new_callable=AsyncMock
            ) as mock_create,
            patch("init_db.schema_logs.logger"),
        ):
            mock_check.return_value = True

            from init_db.schema_logs import initialize_logs_database

            await initialize_logs_database()

            mock_check.assert_called_once()
            mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_initialize_raises_on_error(self):
        """Test that initialize raises on error."""
        with (
            patch(
                "init_db.schema_logs.check_schema_exists", new_callable=AsyncMock
            ) as mock_check,
            patch("init_db.schema_logs.logger"),
        ):
            mock_check.side_effect = Exception("DB error")

            from init_db.schema_logs import initialize_logs_database

            with pytest.raises(Exception, match="DB error"):
                await initialize_logs_database()

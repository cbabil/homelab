"""
Apps Schema Unit Tests

Tests for schema_apps.py - SQLAlchemy ORM schema initialization and seeding.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCreateAppSchema:
    """Tests for create_app_schema function."""

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
            patch("init_db.schema_apps.db_manager") as mock_db_manager,
            patch("init_db.schema_apps.Base") as mock_base,
            patch("init_db.schema_apps.logger"),
        ):
            mock_db_manager.initialize = AsyncMock()
            mock_db_manager.engine = mock_engine
            mock_base.metadata.create_all = MagicMock()

            from init_db.schema_apps import create_app_schema

            await create_app_schema()

            mock_db_manager.initialize.assert_called_once()
            mock_conn.run_sync.assert_called_once()


class TestCheckAppSchemaExists:
    """Tests for check_app_schema_exists function."""

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
        mock_conn.run_sync = AsyncMock(return_value=("applications",))

        with (
            patch("init_db.schema_apps.db_manager") as mock_db_manager,
            patch("init_db.schema_apps.logger"),
        ):
            mock_db_manager.initialize = AsyncMock()
            mock_db_manager.engine = mock_engine

            from init_db.schema_apps import check_app_schema_exists

            result = await check_app_schema_exists()

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
            patch("init_db.schema_apps.db_manager") as mock_db_manager,
            patch("init_db.schema_apps.logger"),
        ):
            mock_db_manager.initialize = AsyncMock()
            mock_db_manager.engine = mock_engine

            from init_db.schema_apps import check_app_schema_exists

            result = await check_app_schema_exists()

            assert result is False


class TestSeedApplicationData:
    """Tests for seed_application_data function."""

    @pytest.mark.asyncio
    async def test_seed_skips_when_data_exists(self):
        """Test that seeding is skipped when data already exists."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one = MagicMock(return_value=5)
        mock_session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("init_db.schema_apps.db_manager") as mock_db_manager,
            patch("init_db.schema_apps.logger"),
        ):
            mock_db_manager.initialize = AsyncMock()
            mock_db_manager.get_session = MagicMock(
                return_value=AsyncMock(
                    __aenter__=AsyncMock(return_value=mock_session),
                    __aexit__=AsyncMock(return_value=None),
                )
            )

            from init_db.schema_apps import seed_application_data

            await seed_application_data()

            # Should not add any data since count > 0
            mock_session.add_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_seed_adds_data_when_empty(self):
        """Test that seeding adds data when database is empty."""
        mock_session = AsyncMock()

        # First execute: count query returns 0
        mock_count_result = MagicMock()
        mock_count_result.scalar_one = MagicMock(return_value=0)

        # Second execute: existing categories query
        mock_categories_result = MagicMock()
        mock_categories_result.all = MagicMock(return_value=[])

        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_categories_result]
        )
        mock_session.add_all = MagicMock()
        mock_session.add = MagicMock()

        with (
            patch("init_db.schema_apps.db_manager") as mock_db_manager,
            patch(
                "init_db.schema_apps.CATEGORIES",
                [{"id": "cat1", "name": "Category 1", "description": "Test category"}],
            ),
            patch(
                "init_db.schema_apps.APPLICATIONS",
                [
                    {
                        "id": "app1",
                        "name": "App 1",
                        "description": "Test app",
                        "version": "1.0.0",
                        "category_id": "cat1",
                        "author": "Test",
                        "license": "MIT",
                        "status": "available",
                        "created_at": "2024-01-01",
                        "updated_at": "2024-01-01",
                    }
                ],
            ),
            patch("init_db.schema_apps.AppCategory") as mock_app_category,
            patch("init_db.schema_apps.App") as mock_app,
            patch("init_db.schema_apps.AppRequirements") as mock_requirements,
            patch("init_db.schema_apps.AppStatus") as mock_status,
            patch("init_db.schema_apps.logger"),
        ):
            mock_db_manager.initialize = AsyncMock()
            mock_db_manager.get_session = MagicMock(
                return_value=AsyncMock(
                    __aenter__=AsyncMock(return_value=mock_session),
                    __aexit__=AsyncMock(return_value=None),
                )
            )

            # Mock category model
            mock_category_instance = MagicMock()
            mock_category_instance.id = "cat1"
            mock_category_instance.to_table_model = MagicMock(return_value=MagicMock())
            mock_app_category.return_value = mock_category_instance

            # Mock app model
            mock_app_instance = MagicMock()
            mock_app_instance.to_table_model = MagicMock(return_value=MagicMock())
            mock_app.return_value = mock_app_instance

            # Mock requirements
            mock_requirements.return_value = MagicMock()

            # Mock status
            mock_status.return_value = MagicMock()

            from init_db.schema_apps import seed_application_data

            await seed_application_data()

            # Should add categories and apps
            mock_session.add_all.assert_called_once()
            mock_session.add.assert_called()


class TestInitializeAppDatabase:
    """Tests for initialize_app_database function."""

    @pytest.mark.asyncio
    async def test_initialize_creates_schema_when_not_exists(self):
        """Test that initialize creates schema when it doesn't exist."""
        with (
            patch(
                "init_db.schema_apps.check_app_schema_exists", new_callable=AsyncMock
            ) as mock_check,
            patch(
                "init_db.schema_apps.create_app_schema", new_callable=AsyncMock
            ) as mock_create,
            patch(
                "init_db.schema_apps.seed_application_data", new_callable=AsyncMock
            ) as mock_seed,
            patch("init_db.schema_apps.logger"),
        ):
            mock_check.return_value = False

            from init_db.schema_apps import initialize_app_database

            await initialize_app_database()

            mock_check.assert_called_once()
            mock_create.assert_called_once()
            mock_seed.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_skips_creation_when_exists(self):
        """Test that initialize skips creation when schema exists."""
        with (
            patch(
                "init_db.schema_apps.check_app_schema_exists", new_callable=AsyncMock
            ) as mock_check,
            patch(
                "init_db.schema_apps.create_app_schema", new_callable=AsyncMock
            ) as mock_create,
            patch(
                "init_db.schema_apps.seed_application_data", new_callable=AsyncMock
            ) as mock_seed,
            patch("init_db.schema_apps.logger"),
        ):
            mock_check.return_value = True

            from init_db.schema_apps import initialize_app_database

            await initialize_app_database()

            mock_check.assert_called_once()
            mock_create.assert_not_called()
            mock_seed.assert_called_once()

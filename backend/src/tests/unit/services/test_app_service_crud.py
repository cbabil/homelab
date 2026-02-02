"""
Unit tests for services/app_service.py - Add and Remove Operations

Tests add_app, remove_app, remove_apps_bulk, and get_app_ids methods.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from services.app_service import AppService
from models.app import (
    ApplicationTable,
    AppCategoryTable,
)


@pytest.fixture
def mock_db_session():
    """Create mock database session with async context manager."""
    session = AsyncMock()
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = session
    context_manager.__aexit__.return_value = None
    return session, context_manager


@pytest.fixture
def sample_app_table():
    """Create mock ApplicationTable row."""
    app = MagicMock(spec=ApplicationTable)
    app.id = "plex"
    app.name = "Plex"
    app.description = "Media server"
    app.long_description = None
    app.version = "1.0.0"
    app.category_id = "media"
    app.tags = '["media", "streaming"]'
    app.icon = None
    app.screenshots = None
    app.author = "Plex Inc"
    app.repository = None
    app.documentation = None
    app.license = "MIT"
    app.requirements = None
    app.status = "available"
    app.install_count = 100
    app.rating = 4.5
    app.featured = True
    app.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    app.updated_at = datetime(2024, 6, 1, tzinfo=UTC)
    app.connected_server_id = None
    return app


@pytest.fixture
def sample_category_table():
    """Create mock AppCategoryTable row."""
    cat = MagicMock(spec=AppCategoryTable)
    cat.id = "media"
    cat.name = "Media"
    cat.description = "Media applications"
    cat.icon = "Video"
    cat.color = "text-blue-500"
    return cat


class TestAddApp:
    """Tests for add_app method."""

    @pytest.mark.asyncio
    async def test_add_app_success(self, mock_db_session, sample_category_table):
        """add_app should create new application."""
        session, context_manager = mock_db_session

        existing_result = MagicMock()
        existing_result.first.return_value = None

        cat_result = MagicMock()
        cat_result.first.return_value = (sample_category_table,)

        session.execute = AsyncMock(side_effect=[existing_result, cat_result])
        session.add = MagicMock()

        with patch("services.app_service.logger"), \
             patch("services.app_service.initialize_app_database"), \
             patch("services.app_service.db_manager") as mock_db:
            mock_db.get_session.return_value = context_manager

            service = AppService()
            app_data = {
                "id": "new-app",
                "name": "New App",
                "description": "A new application",
                "version": "1.0.0",
                "category_id": "media",
                "author": "Test Author",
                "license": "MIT",
            }
            result = await service.add_app(app_data)

            assert result.id == "new-app"
            assert result.name == "New App"
            session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_app_already_exists(self, mock_db_session):
        """add_app should raise ValueError if app exists."""
        session, context_manager = mock_db_session

        existing_result = MagicMock()
        existing_result.first.return_value = (MagicMock(),)
        session.execute = AsyncMock(return_value=existing_result)

        with patch("services.app_service.logger"), \
             patch("services.app_service.initialize_app_database"), \
             patch("services.app_service.db_manager") as mock_db:
            mock_db.get_session.return_value = context_manager

            service = AppService()
            with pytest.raises(ValueError, match="already exists"):
                await service.add_app({"id": "existing", "name": "Test"})

    @pytest.mark.asyncio
    async def test_add_app_creates_category(self, mock_db_session):
        """add_app should create category if it doesn't exist."""
        session, context_manager = mock_db_session

        existing_result = MagicMock()
        existing_result.first.return_value = None

        cat_result = MagicMock()
        cat_result.first.return_value = None

        session.execute = AsyncMock(side_effect=[existing_result, cat_result])
        session.add = MagicMock()
        session.flush = AsyncMock()

        with patch("services.app_service.logger"), \
             patch("services.app_service.initialize_app_database"), \
             patch("services.app_service.db_manager") as mock_db:
            mock_db.get_session.return_value = context_manager

            service = AppService()
            app_data = {
                "id": "new-app",
                "name": "New App",
                "description": "A new application",
                "version": "1.0.0",
                "category_id": "new-category",
                "author": "Test Author",
                "license": "MIT",
            }
            result = await service.add_app(app_data)

            assert result.category.id == "new-category"
            session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_app_with_requirements(
        self, mock_db_session, sample_category_table
    ):
        """add_app should handle requirements data."""
        session, context_manager = mock_db_session

        existing_result = MagicMock()
        existing_result.first.return_value = None

        cat_result = MagicMock()
        cat_result.first.return_value = (sample_category_table,)

        session.execute = AsyncMock(side_effect=[existing_result, cat_result])
        session.add = MagicMock()

        with patch("services.app_service.logger"), \
             patch("services.app_service.initialize_app_database"), \
             patch("services.app_service.db_manager") as mock_db:
            mock_db.get_session.return_value = context_manager

            service = AppService()
            app_data = {
                "id": "new-app",
                "name": "New App",
                "description": "A new application",
                "version": "1.0.0",
                "category_id": "media",
                "author": "Test Author",
                "license": "MIT",
                "requirements": {
                    "min_ram": "2GB",
                    "min_storage": "10GB",
                    "architectures": ["x86_64", "arm64"],
                },
            }
            result = await service.add_app(app_data)

            assert result.requirements.min_ram == "2GB"
            assert result.requirements.min_storage == "10GB"


class TestRemoveApp:
    """Tests for remove_app method."""

    @pytest.mark.asyncio
    async def test_remove_app_success(self, mock_db_session, sample_app_table):
        """remove_app should delete app and return True."""
        session, context_manager = mock_db_session
        sample_app_table.status = "available"

        result = MagicMock()
        result.first.return_value = (sample_app_table,)
        session.execute = AsyncMock(return_value=result)

        with patch("services.app_service.logger"), \
             patch("services.app_service.initialize_app_database"), \
             patch("services.app_service.db_manager") as mock_db:
            mock_db.get_session.return_value = context_manager

            service = AppService()
            success = await service.remove_app("plex")

            assert success is True

    @pytest.mark.asyncio
    async def test_remove_app_not_found(self, mock_db_session):
        """remove_app should return False when not found."""
        session, context_manager = mock_db_session

        result = MagicMock()
        result.first.return_value = None
        session.execute = AsyncMock(return_value=result)

        with patch("services.app_service.logger"), \
             patch("services.app_service.initialize_app_database"), \
             patch("services.app_service.db_manager") as mock_db:
            mock_db.get_session.return_value = context_manager

            service = AppService()
            success = await service.remove_app("nonexistent")

            assert success is False

    @pytest.mark.asyncio
    async def test_remove_app_installed_raises(self, mock_db_session, sample_app_table):
        """remove_app should raise ValueError for installed app."""
        session, context_manager = mock_db_session
        sample_app_table.status = "installed"

        result = MagicMock()
        result.first.return_value = (sample_app_table,)
        session.execute = AsyncMock(return_value=result)

        with patch("services.app_service.logger"), \
             patch("services.app_service.initialize_app_database"), \
             patch("services.app_service.db_manager") as mock_db:
            mock_db.get_session.return_value = context_manager

            service = AppService()
            with pytest.raises(ValueError, match="Cannot remove installed app"):
                await service.remove_app("plex")


class TestRemoveAppsBulk:
    """Tests for remove_apps_bulk method."""

    @pytest.mark.asyncio
    async def test_remove_apps_bulk_success(self, mock_db_session, sample_app_table):
        """remove_apps_bulk should remove multiple apps."""
        session, context_manager = mock_db_session
        sample_app_table.status = "available"

        result = MagicMock()
        result.first.return_value = (sample_app_table,)
        session.execute = AsyncMock(return_value=result)

        with patch("services.app_service.logger"), \
             patch("services.app_service.initialize_app_database"), \
             patch("services.app_service.db_manager") as mock_db:
            mock_db.get_session.return_value = context_manager

            service = AppService()
            result = await service.remove_apps_bulk(["plex", "jellyfin"])

            assert result["removed_count"] == 2
            assert len(result["removed"]) == 2

    @pytest.mark.asyncio
    async def test_remove_apps_bulk_partial(self, mock_db_session, sample_app_table):
        """remove_apps_bulk should handle partial success with not found."""
        session, context_manager = mock_db_session

        with patch("services.app_service.logger"), \
             patch("services.app_service.initialize_app_database"), \
             patch("services.app_service.db_manager") as mock_db, \
             patch.object(AppService, "remove_app") as mock_remove:

            async def remove_side_effect(app_id):
                if app_id == "app1":
                    return True
                return False

            mock_remove.side_effect = remove_side_effect
            mock_db.get_session.return_value = context_manager

            service = AppService()
            result = await service.remove_apps_bulk(["app1", "app2"])

            assert result["removed_count"] == 1
            assert result["skipped_count"] == 1
            assert "app1" in result["removed"]

    @pytest.mark.asyncio
    async def test_remove_apps_bulk_valueerror(self, mock_db_session, sample_app_table):
        """remove_apps_bulk should handle ValueError from installed app."""
        session, context_manager = mock_db_session

        with patch("services.app_service.logger"), \
             patch("services.app_service.initialize_app_database"), \
             patch("services.app_service.db_manager") as mock_db, \
             patch.object(AppService, "remove_app") as mock_remove:

            async def remove_side_effect(app_id):
                if app_id == "installed-app":
                    raise ValueError("Cannot remove installed app")
                return True

            mock_remove.side_effect = remove_side_effect
            mock_db.get_session.return_value = context_manager

            service = AppService()
            result = await service.remove_apps_bulk(["app1", "installed-app"])

            assert result["removed_count"] == 1
            assert result["skipped_count"] == 1
            assert "Cannot remove installed app" in result["skipped"][0]["reason"]


class TestGetAppIds:
    """Tests for get_app_ids method."""

    @pytest.mark.asyncio
    async def test_get_app_ids(self, mock_db_session):
        """get_app_ids should return list of IDs."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = [("plex",), ("jellyfin",), ("sonarr",)]
        session.execute = AsyncMock(return_value=mock_result)

        with patch("services.app_service.logger"), \
             patch("services.app_service.initialize_app_database"), \
             patch("services.app_service.db_manager") as mock_db:
            mock_db.get_session.return_value = context_manager

            service = AppService()
            ids = await service.get_app_ids()

            assert ids == ["plex", "jellyfin", "sonarr"]

    @pytest.mark.asyncio
    async def test_get_app_ids_empty(self, mock_db_session):
        """get_app_ids should return empty list when no apps."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        with patch("services.app_service.logger"), \
             patch("services.app_service.initialize_app_database"), \
             patch("services.app_service.db_manager") as mock_db:
            mock_db.get_session.return_value = context_manager

            service = AppService()
            ids = await service.get_app_ids()

            assert ids == []

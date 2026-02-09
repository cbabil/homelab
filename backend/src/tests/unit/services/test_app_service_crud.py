"""
Unit tests for services/app_service.py - Add and Remove Operations

Tests add_app, remove_app, remove_apps_bulk, and get_app_ids methods.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.app_service import AppService


@pytest.fixture
def mock_db_conn():
    """Create mock DatabaseConnection with get_connection context manager."""
    mock_aiosqlite_conn = AsyncMock()
    mock_connection = MagicMock()
    ctx = AsyncMock()
    ctx.__aenter__.return_value = mock_aiosqlite_conn
    ctx.__aexit__.return_value = None
    mock_connection.get_connection.return_value = ctx
    return mock_connection, mock_aiosqlite_conn


@pytest.fixture
def sample_category_row():
    """Create dict-like category row as returned by aiosqlite."""
    return {
        "id": "media",
        "name": "Media",
        "description": "Media applications",
        "icon": "Video",
        "color": "text-blue-500",
    }


class TestAddApp:
    """Tests for add_app method."""

    @pytest.mark.asyncio
    async def test_add_app_success(self, mock_db_conn, sample_category_row):
        """add_app should create new application."""
        mock_conn, mock_aiosqlite = mock_db_conn

        # First execute: SELECT id FROM applications WHERE id = ? -> not found
        cursor_exists = AsyncMock()
        cursor_exists.fetchone.return_value = None

        # Second execute: SELECT * FROM app_categories WHERE id = ? -> found
        cursor_cat = AsyncMock()
        cursor_cat.fetchone.return_value = sample_category_row

        # Third execute: INSERT INTO applications
        cursor_insert = AsyncMock()

        mock_aiosqlite.execute = AsyncMock(
            side_effect=[cursor_exists, cursor_cat, cursor_insert]
        )
        mock_aiosqlite.commit = AsyncMock()

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
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
            mock_aiosqlite.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_app_already_exists(self, mock_db_conn):
        """add_app should raise ValueError if app exists."""
        mock_conn, mock_aiosqlite = mock_db_conn

        cursor_exists = AsyncMock()
        cursor_exists.fetchone.return_value = {"id": "existing"}
        mock_aiosqlite.execute = AsyncMock(return_value=cursor_exists)

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            with pytest.raises(ValueError, match="already exists"):
                await service.add_app({"id": "existing", "name": "Test"})

    @pytest.mark.asyncio
    async def test_add_app_creates_category(self, mock_db_conn):
        """add_app should create category if it doesn't exist."""
        mock_conn, mock_aiosqlite = mock_db_conn

        new_cat_row = {
            "id": "new-category",
            "name": "New-category",
            "description": "Applications in the new-category category",
            "icon": "Package",
            "color": "text-primary",
        }

        # 1: SELECT id FROM applications WHERE id = ? -> not found
        cursor_exists = AsyncMock()
        cursor_exists.fetchone.return_value = None

        # 2: SELECT * FROM app_categories WHERE id = ? -> not found
        cursor_cat_check = AsyncMock()
        cursor_cat_check.fetchone.return_value = None

        # 3: INSERT INTO app_categories
        cursor_cat_insert = AsyncMock()

        # 4: SELECT * FROM app_categories WHERE id = ? -> now found
        cursor_cat_refetch = AsyncMock()
        cursor_cat_refetch.fetchone.return_value = new_cat_row

        # 5: INSERT INTO applications
        cursor_app_insert = AsyncMock()

        mock_aiosqlite.execute = AsyncMock(
            side_effect=[
                cursor_exists,
                cursor_cat_check,
                cursor_cat_insert,
                cursor_cat_refetch,
                cursor_app_insert,
            ]
        )
        mock_aiosqlite.commit = AsyncMock()

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
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

    @pytest.mark.asyncio
    async def test_add_app_with_requirements(
        self, mock_db_conn, sample_category_row
    ):
        """add_app should handle requirements data."""
        mock_conn, mock_aiosqlite = mock_db_conn

        cursor_exists = AsyncMock()
        cursor_exists.fetchone.return_value = None

        cursor_cat = AsyncMock()
        cursor_cat.fetchone.return_value = sample_category_row

        cursor_insert = AsyncMock()

        mock_aiosqlite.execute = AsyncMock(
            side_effect=[cursor_exists, cursor_cat, cursor_insert]
        )
        mock_aiosqlite.commit = AsyncMock()

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
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
    async def test_remove_app_success(self, mock_db_conn):
        """remove_app should delete app and return True."""
        mock_conn, mock_aiosqlite = mock_db_conn

        cursor_select = AsyncMock()
        cursor_select.fetchone.return_value = {"status": "available"}

        cursor_delete = AsyncMock()

        mock_aiosqlite.execute = AsyncMock(
            side_effect=[cursor_select, cursor_delete]
        )
        mock_aiosqlite.commit = AsyncMock()

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            success = await service.remove_app("plex")

            assert success is True
            mock_aiosqlite.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_app_not_found(self, mock_db_conn):
        """remove_app should return False when not found."""
        mock_conn, mock_aiosqlite = mock_db_conn

        cursor_select = AsyncMock()
        cursor_select.fetchone.return_value = None
        mock_aiosqlite.execute = AsyncMock(return_value=cursor_select)

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            success = await service.remove_app("nonexistent")

            assert success is False

    @pytest.mark.asyncio
    async def test_remove_app_installed_raises(self, mock_db_conn):
        """remove_app should raise ValueError for installed app."""
        mock_conn, mock_aiosqlite = mock_db_conn

        cursor_select = AsyncMock()
        cursor_select.fetchone.return_value = {"status": "installed"}
        mock_aiosqlite.execute = AsyncMock(return_value=cursor_select)

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            with pytest.raises(ValueError, match="Cannot remove installed app"):
                await service.remove_app("plex")


class TestRemoveAppsBulk:
    """Tests for remove_apps_bulk method."""

    @pytest.mark.asyncio
    async def test_remove_apps_bulk_success(self, mock_db_conn):
        """remove_apps_bulk should remove multiple apps."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_log = MagicMock()

        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)

        with patch.object(service, "remove_app", new_callable=AsyncMock) as mock_remove:
            mock_remove.return_value = True
            result = await service.remove_apps_bulk(["plex", "jellyfin"])

            assert result["removed_count"] == 2
            assert len(result["removed"]) == 2

    @pytest.mark.asyncio
    async def test_remove_apps_bulk_partial(self, mock_db_conn):
        """remove_apps_bulk should handle partial success with not found."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_log = MagicMock()

        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)

        async def remove_side_effect(app_id):
            if app_id == "app1":
                return True
            return False

        with patch.object(service, "remove_app", side_effect=remove_side_effect):
            result = await service.remove_apps_bulk(["app1", "app2"])

            assert result["removed_count"] == 1
            assert result["skipped_count"] == 1
            assert "app1" in result["removed"]

    @pytest.mark.asyncio
    async def test_remove_apps_bulk_valueerror(self, mock_db_conn):
        """remove_apps_bulk should handle ValueError from installed app."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_log = MagicMock()

        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)

        async def remove_side_effect(app_id):
            if app_id == "installed-app":
                raise ValueError("Cannot remove installed app")
            return True

        with patch.object(service, "remove_app", side_effect=remove_side_effect):
            result = await service.remove_apps_bulk(["app1", "installed-app"])

            assert result["removed_count"] == 1
            assert result["skipped_count"] == 1
            assert "Cannot remove installed app" in result["skipped"][0]["reason"]


class TestGetAppIds:
    """Tests for get_app_ids method."""

    @pytest.mark.asyncio
    async def test_get_app_ids(self, mock_db_conn):
        """get_app_ids should return list of IDs."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [
            {"id": "plex"}, {"id": "jellyfin"}, {"id": "sonarr"}
        ]
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            ids = await service.get_app_ids()

            assert ids == ["plex", "jellyfin", "sonarr"]

    @pytest.mark.asyncio
    async def test_get_app_ids_empty(self, mock_db_conn):
        """get_app_ids should return empty list when no apps."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            ids = await service.get_app_ids()

            assert ids == []

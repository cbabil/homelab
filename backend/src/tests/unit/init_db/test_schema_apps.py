"""
Apps Schema Unit Tests

Tests for schema_apps.py - application catalog seeding via raw SQL.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from init_db.schema_apps import seed_application_data


class TestSeedApplicationData:
    """Tests for seed_application_data function."""

    @pytest.fixture
    def mock_connection(self):
        """Create mock DatabaseConnection with async context manager."""
        connection = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.commit = AsyncMock()

        connection.get_connection = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_conn),
                __aexit__=AsyncMock(return_value=None),
            )
        )
        return connection, mock_conn

    @pytest.mark.asyncio
    async def test_seed_skips_when_data_exists(self, mock_connection):
        """Test that seeding is skipped when data already exists."""
        connection, mock_conn = mock_connection

        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=(5,))
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        with patch("init_db.schema_apps.logger"):
            await seed_application_data(connection)

        # Only the COUNT query should have been executed
        mock_conn.execute.assert_called_once()
        mock_conn.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_seed_adds_data_when_empty(self, mock_connection):
        """Test that seeding inserts categories and apps when empty."""
        connection, mock_conn = mock_connection

        # First call returns count of 0
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=(0,))
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        test_categories = [
            {
                "id": "cat1",
                "name": "Category 1",
                "description": "Test category",
            },
        ]
        test_apps = [
            {
                "id": "app1",
                "name": "App 1",
                "description": "Test app",
                "version": "1.0.0",
                "category_id": "cat1",
                "author": "Test",
                "license": "MIT",
                "status": "available",
            },
        ]

        with (
            patch("init_db.schema_apps.CATEGORIES", test_categories),
            patch("init_db.schema_apps.APPLICATIONS", test_apps),
            patch("init_db.schema_apps.logger"),
        ):
            await seed_application_data(connection)

        # COUNT query + 1 category INSERT + 1 app INSERT = 3 calls
        assert mock_conn.execute.call_count == 3
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_seed_proceeds_when_count_is_none(self, mock_connection):
        """Test that seeding proceeds when fetchone returns None (empty table)."""
        connection, mock_conn = mock_connection

        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        test_categories = [
            {
                "id": "cat1",
                "name": "Category 1",
                "description": "Test category",
            },
        ]
        test_apps = [
            {
                "id": "app1",
                "name": "App 1",
                "description": "Test app",
                "version": "1.0.0",
                "category_id": "cat1",
                "author": "Test",
                "license": "MIT",
                "status": "available",
            },
        ]

        with (
            patch("init_db.schema_apps.CATEGORIES", test_categories),
            patch("init_db.schema_apps.APPLICATIONS", test_apps),
            patch("init_db.schema_apps.logger"),
        ):
            await seed_application_data(connection)

        # COUNT query + 1 category INSERT + 1 app INSERT = 3 calls
        assert mock_conn.execute.call_count == 3
        mock_conn.commit.assert_called_once()

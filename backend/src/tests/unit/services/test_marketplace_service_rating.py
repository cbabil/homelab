"""
Unit tests for services/marketplace_service.py - Rating operations.

Tests rate_app and get_user_rating methods.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.marketplace_service import MarketplaceService


@pytest.fixture
def mock_db_conn():
    """Create mock DatabaseConnection with async context manager."""
    mock_aiosqlite_conn = AsyncMock()
    mock_connection = MagicMock()
    ctx = AsyncMock()
    ctx.__aenter__.return_value = mock_aiosqlite_conn
    ctx.__aexit__.return_value = None
    mock_connection.get_connection.return_value = ctx
    return mock_connection, mock_aiosqlite_conn


class TestRateApp:
    """Tests for rate_app method."""

    @pytest.mark.asyncio
    async def test_rate_app_creates_new_rating(self, mock_db_conn):
        """rate_app should create a new rating when none exists."""
        mock_conn, mock_aiosqlite = mock_db_conn

        # Track execute calls to return different cursors
        call_count = [0]

        async def mock_execute(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            cursor = AsyncMock()
            if idx == 0:
                # Check existing rating -> None
                cursor.fetchone.return_value = None
            elif idx == 1:
                # INSERT new rating
                pass
            elif idx == 2:
                # SELECT all ratings for average
                cursor.fetchall.return_value = [{"rating": 4}]
            else:
                # UPDATE app avg rating
                pass
            return cursor

        mock_aiosqlite.execute = mock_execute
        mock_aiosqlite.commit = AsyncMock()

        with patch("services.marketplace_service.logger") as mock_logger:
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.rate_app("test-app", "user-123", 4)

            assert result.app_id == "test-app"
            assert result.user_id == "user-123"
            assert result.rating == 4
            mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_rate_app_updates_existing_rating(self, mock_db_conn):
        """rate_app should update existing rating."""
        mock_conn, mock_aiosqlite = mock_db_conn

        call_count = [0]

        async def mock_execute(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            cursor = AsyncMock()
            if idx == 0:
                # Check existing rating -> found
                cursor.fetchone.return_value = {"id": "rating-abc123"}
            elif idx == 1:
                # UPDATE existing rating
                pass
            elif idx == 2:
                # SELECT all ratings for average
                cursor.fetchall.return_value = [{"rating": 5}]
            else:
                # UPDATE app avg rating
                pass
            return cursor

        mock_aiosqlite.execute = mock_execute
        mock_aiosqlite.commit = AsyncMock()

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.rate_app("test-app", "user-123", 5)

            assert result.rating == 5
            assert result.id == "rating-abc123"

    @pytest.mark.asyncio
    async def test_rate_app_validates_rating_range(self, mock_db_conn):
        """rate_app should raise ValueError for invalid rating."""
        mock_conn, _ = mock_db_conn

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            # Rating too low
            with pytest.raises(
                ValueError, match="Rating must be between 1 and 5"
            ):
                await service.rate_app("test-app", "user-123", 0)

            # Rating too high
            with pytest.raises(
                ValueError, match="Rating must be between 1 and 5"
            ):
                await service.rate_app("test-app", "user-123", 6)

    @pytest.mark.asyncio
    async def test_rate_app_accepts_valid_range(self, mock_db_conn):
        """rate_app should accept ratings 1-5."""
        mock_conn, mock_aiosqlite = mock_db_conn

        async def mock_execute(*args, **kwargs):
            cursor = AsyncMock()
            cursor.fetchone.return_value = None
            cursor.fetchall.return_value = []
            return cursor

        mock_aiosqlite.execute = mock_execute
        mock_aiosqlite.commit = AsyncMock()

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            # Test boundary values
            for rating_value in [1, 2, 3, 4, 5]:
                result = await service.rate_app(
                    "test-app", "user-123", rating_value
                )
                assert result.rating == rating_value

    @pytest.mark.asyncio
    async def test_rate_app_updates_app_average_rating(self, mock_db_conn):
        """rate_app should update app's average rating."""
        mock_conn, mock_aiosqlite = mock_db_conn

        call_count = [0]

        async def mock_execute(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            cursor = AsyncMock()
            if idx == 0:
                # No existing rating
                cursor.fetchone.return_value = None
            elif idx == 1:
                # INSERT
                pass
            elif idx == 2:
                # SELECT all ratings: avg = 4.0
                cursor.fetchall.return_value = [
                    {"rating": 3},
                    {"rating": 4},
                    {"rating": 5},
                ]
            else:
                # UPDATE app
                pass
            return cursor

        mock_aiosqlite.execute = mock_execute
        mock_aiosqlite.commit = AsyncMock()

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            await service.rate_app("test-app", "user-456", 5)

            # Should have called execute at least 4 times
            assert call_count[0] >= 4

    @pytest.mark.asyncio
    async def test_rate_app_logs_operation(self, mock_db_conn):
        """rate_app should log the rating operation."""
        mock_conn, mock_aiosqlite = mock_db_conn

        async def mock_execute(*args, **kwargs):
            cursor = AsyncMock()
            cursor.fetchone.return_value = None
            cursor.fetchall.return_value = [{"rating": 4}]
            return cursor

        mock_aiosqlite.execute = mock_execute
        mock_aiosqlite.commit = AsyncMock()

        with patch("services.marketplace_service.logger") as mock_logger:
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            await service.rate_app("test-app", "user-123", 4)

            mock_logger.info.assert_called_with(
                "App rated",
                app_id="test-app",
                user_id="user-123",
                rating=4,
            )


class TestGetUserRating:
    """Tests for get_user_rating method."""

    @pytest.mark.asyncio
    async def test_get_user_rating_returns_rating(self, mock_db_conn):
        """get_user_rating should return user's rating for an app."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"rating": 4}
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.get_user_rating("test-app", "user-123")

            assert result == 4

    @pytest.mark.asyncio
    async def test_get_user_rating_returns_none_when_not_found(
        self, mock_db_conn
    ):
        """get_user_rating should return None when no rating exists."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.get_user_rating("test-app", "user-999")

            assert result is None


class TestRatingIntegration:
    """Integration tests for rating functionality."""

    @pytest.mark.asyncio
    async def test_rate_app_returns_correct_timestamps(self, mock_db_conn):
        """rate_app should return correct timestamp strings."""
        mock_conn, mock_aiosqlite = mock_db_conn

        async def mock_execute(*args, **kwargs):
            cursor = AsyncMock()
            cursor.fetchone.return_value = None
            cursor.fetchall.return_value = [{"rating": 4}]
            return cursor

        mock_aiosqlite.execute = mock_execute
        mock_aiosqlite.commit = AsyncMock()

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.rate_app("test-app", "user-123", 4)

            # Timestamps should be ISO format strings
            assert isinstance(result.created_at, str)
            assert isinstance(result.updated_at, str)
            assert "T" in result.created_at
            assert "T" in result.updated_at

    @pytest.mark.asyncio
    async def test_rate_app_generates_unique_id(self, mock_db_conn):
        """rate_app should generate unique rating ID."""
        mock_conn, mock_aiosqlite = mock_db_conn

        async def mock_execute(*args, **kwargs):
            cursor = AsyncMock()
            cursor.fetchone.return_value = None
            cursor.fetchall.return_value = [{"rating": 3}]
            return cursor

        mock_aiosqlite.execute = mock_execute
        mock_aiosqlite.commit = AsyncMock()

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.rate_app("test-app", "user-123", 3)

            assert result.id.startswith("rating-")
            assert len(result.id) == 15  # "rating-" + 8 chars

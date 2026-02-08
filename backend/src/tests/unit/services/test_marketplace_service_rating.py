"""
Unit tests for services/marketplace_service.py - Rating operations.

Tests rate_app and get_user_rating methods.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.marketplace import AppRatingTable
from services.marketplace_service import MarketplaceService


@pytest.fixture
def mock_db_session():
    """Create mock database session with async context manager."""
    session = AsyncMock()
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = session
    context_manager.__aexit__.return_value = None
    return session, context_manager


@pytest.fixture
def mock_rating_table():
    """Create mock AppRatingTable row."""
    rating = MagicMock(spec=AppRatingTable)
    rating.id = "rating-abc123"
    rating.app_id = "test-app"
    rating.user_id = "user-123"
    rating.rating = 4
    rating.created_at = datetime(2024, 1, 15, tzinfo=UTC)
    rating.updated_at = datetime(2024, 1, 15, tzinfo=UTC)
    return rating


class TestRateApp:
    """Tests for rate_app method."""

    @pytest.mark.asyncio
    async def test_rate_app_creates_new_rating(self, mock_db_session):
        """rate_app should create a new rating when none exists."""
        session, context_manager = mock_db_session

        # Mock execute to handle all calls:
        # 1. Check for existing rating (returns None)
        # 2. Query all ratings for average calculation
        # 3. Update app's average rating
        mock_results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
            MagicMock(all=MagicMock(return_value=[(4,)])),
            MagicMock(),  # update app avg rating
        ]

        call_idx = [0]

        async def mock_execute(*args, **kwargs):
            idx = min(call_idx[0], len(mock_results) - 1)
            call_idx[0] += 1
            return mock_results[idx]

        session.execute = mock_execute
        session.add = MagicMock()
        session.flush = AsyncMock()

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.rate_app("test-app", "user-123", 4)

            assert result.app_id == "test-app"
            assert result.user_id == "user-123"
            assert result.rating == 4
            session.add.assert_called_once()
            mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_rate_app_updates_existing_rating(
        self, mock_db_session, mock_rating_table
    ):
        """rate_app should update existing rating."""
        session, context_manager = mock_db_session

        # First call returns existing rating
        # Subsequent calls for update and average calculation
        mock_results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_rating_table)),
            MagicMock(),  # update execute
            MagicMock(all=MagicMock(return_value=[(5,)])),  # ratings query
            MagicMock(),  # app update
        ]
        call_count = [0]

        async def mock_execute(*args, **kwargs):
            result = mock_results[min(call_count[0], len(mock_results) - 1)]
            call_count[0] += 1
            return result

        session.execute = mock_execute
        session.flush = AsyncMock()

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.rate_app("test-app", "user-123", 5)

            assert result.rating == 5
            assert result.id == "rating-abc123"

    @pytest.mark.asyncio
    async def test_rate_app_validates_rating_range(self, mock_db_session):
        """rate_app should raise ValueError for invalid rating."""
        session, context_manager = mock_db_session

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            # Rating too low
            with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
                await service.rate_app("test-app", "user-123", 0)

            # Rating too high
            with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
                await service.rate_app("test-app", "user-123", 6)

    @pytest.mark.asyncio
    async def test_rate_app_accepts_valid_range(self, mock_db_session):
        """rate_app should accept ratings 1-5."""
        session, context_manager = mock_db_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)
        session.add = MagicMock()
        session.flush = AsyncMock()

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            # Test boundary values
            for rating_value in [1, 2, 3, 4, 5]:
                result = await service.rate_app("test-app", "user-123", rating_value)
                assert result.rating == rating_value

    @pytest.mark.asyncio
    async def test_rate_app_updates_app_average_rating(self, mock_db_session):
        """rate_app should update app's average rating."""
        session, context_manager = mock_db_session

        # Setup multiple ratings for average calculation
        mock_results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
            MagicMock(all=MagicMock(return_value=[(3,), (4,), (5,)])),  # avg = 4.0
            MagicMock(),  # app update
        ]
        call_count = [0]

        async def mock_execute(stmt):
            result = mock_results[min(call_count[0], len(mock_results) - 1)]
            call_count[0] += 1
            return result

        session.execute = mock_execute
        session.add = MagicMock()
        session.flush = AsyncMock()

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            await service.rate_app("test-app", "user-456", 5)

            # Verify execute was called multiple times (including avg update)
            assert call_count[0] >= 3

    @pytest.mark.asyncio
    async def test_rate_app_logs_operation(self, mock_db_session):
        """rate_app should log the rating operation."""
        session, context_manager = mock_db_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.all.return_value = [(4,)]
        session.execute = AsyncMock(return_value=mock_result)
        session.add = MagicMock()
        session.flush = AsyncMock()

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            await service.rate_app("test-app", "user-123", 4)

            mock_logger.info.assert_called_with(
                "App rated", app_id="test-app", user_id="user-123", rating=4
            )


class TestGetUserRating:
    """Tests for get_user_rating method."""

    @pytest.mark.asyncio
    async def test_get_user_rating_returns_rating(self, mock_db_session):
        """get_user_rating should return user's rating for an app."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 4
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.get_user_rating("test-app", "user-123")

            assert result == 4

    @pytest.mark.asyncio
    async def test_get_user_rating_returns_none_when_not_found(self, mock_db_session):
        """get_user_rating should return None when no rating exists."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.get_user_rating("test-app", "user-999")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_rating_returns_none_for_zero(self, mock_db_session):
        """get_user_rating should return None for falsy values like 0."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 0
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.get_user_rating("test-app", "user-123")

            # 0 is falsy, so should return None
            assert result is None


class TestRatingIntegration:
    """Integration tests for rating functionality."""

    @pytest.mark.asyncio
    async def test_rate_app_returns_correct_timestamps(self, mock_db_session):
        """rate_app should return correct timestamp strings."""
        session, context_manager = mock_db_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.all.return_value = [(4,)]
        session.execute = AsyncMock(return_value=mock_result)
        session.add = MagicMock()
        session.flush = AsyncMock()

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.rate_app("test-app", "user-123", 4)

            # Timestamps should be ISO format strings
            assert isinstance(result.created_at, str)
            assert isinstance(result.updated_at, str)
            assert "T" in result.created_at
            assert "T" in result.updated_at

    @pytest.mark.asyncio
    async def test_rate_app_generates_unique_id(self, mock_db_session):
        """rate_app should generate unique rating ID."""
        session, context_manager = mock_db_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.all.return_value = [(3,)]
        session.execute = AsyncMock(return_value=mock_result)
        session.add = MagicMock()
        session.flush = AsyncMock()

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.rate_app("test-app", "user-123", 3)

            assert result.id.startswith("rating-")
            assert len(result.id) == 15  # "rating-" + 8 chars

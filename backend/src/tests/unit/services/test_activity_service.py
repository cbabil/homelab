"""
Unit tests for services/activity_service.py

Tests activity logging and querying functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from services.activity_service import ActivityService
from models.metrics import ActivityLog, ActivityType


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    return AsyncMock()


@pytest.fixture
def activity_service(mock_db_service):
    """Create ActivityService instance with mock db."""
    return ActivityService(mock_db_service)


class TestActivityServiceInit:
    """Tests for ActivityService initialization."""

    def test_init_stores_db_service(self, mock_db_service):
        """ActivityService should store db_service reference."""
        service = ActivityService(mock_db_service)
        assert service.db_service is mock_db_service

    def test_init_logs_message(self, mock_db_service):
        """ActivityService should log initialization."""
        with patch("services.activity_service.logger") as mock_logger:
            ActivityService(mock_db_service)
            mock_logger.info.assert_called_once_with("Activity service initialized")


class TestLogActivity:
    """Tests for log_activity method."""

    @pytest.mark.asyncio
    async def test_log_activity_success(self, activity_service, mock_db_service):
        """log_activity should create and save activity log."""
        mock_db_service.save_activity_log = AsyncMock()

        result = await activity_service.log_activity(
            activity_type=ActivityType.USER_LOGIN,
            message="User logged in",
            user_id="user-123"
        )

        assert result is not None
        assert result.activity_type == ActivityType.USER_LOGIN
        assert result.message == "User logged in"
        assert result.user_id == "user-123"
        assert result.id.startswith("act-")
        mock_db_service.save_activity_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_activity_with_all_fields(self, activity_service, mock_db_service):
        """log_activity should handle all optional fields."""
        mock_db_service.save_activity_log = AsyncMock()

        result = await activity_service.log_activity(
            activity_type=ActivityType.APP_INSTALLED,
            message="App installed",
            user_id="user-123",
            server_id="server-456",
            app_id="app-789",
            details={"version": "1.0.0"}
        )

        assert result.user_id == "user-123"
        assert result.server_id == "server-456"
        assert result.app_id == "app-789"
        assert result.details == {"version": "1.0.0"}

    @pytest.mark.asyncio
    async def test_log_activity_default_details(self, activity_service, mock_db_service):
        """log_activity should default details to empty dict."""
        mock_db_service.save_activity_log = AsyncMock()

        result = await activity_service.log_activity(
            activity_type=ActivityType.SERVER_ADDED,
            message="Server added"
        )

        assert result.details == {}

    @pytest.mark.asyncio
    async def test_log_activity_generates_unique_id(self, activity_service, mock_db_service):
        """log_activity should generate unique IDs."""
        mock_db_service.save_activity_log = AsyncMock()

        result1 = await activity_service.log_activity(
            activity_type=ActivityType.USER_LOGIN,
            message="Login 1"
        )
        result2 = await activity_service.log_activity(
            activity_type=ActivityType.USER_LOGIN,
            message="Login 2"
        )

        assert result1.id != result2.id

    @pytest.mark.asyncio
    async def test_log_activity_db_error(self, activity_service, mock_db_service):
        """log_activity should raise on database error."""
        mock_db_service.save_activity_log = AsyncMock(
            side_effect=Exception("DB error")
        )

        with pytest.raises(Exception) as exc_info:
            await activity_service.log_activity(
                activity_type=ActivityType.USER_LOGIN,
                message="Login"
            )
        assert "DB error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_log_activity_logs_success(self, activity_service, mock_db_service):
        """log_activity should log successful activity."""
        mock_db_service.save_activity_log = AsyncMock()

        with patch("services.activity_service.logger") as mock_logger:
            await activity_service.log_activity(
                activity_type=ActivityType.USER_LOGIN,
                message="User logged in"
            )
            mock_logger.info.assert_called()


class TestGetRecentActivities:
    """Tests for get_recent_activities method."""

    @pytest.mark.asyncio
    async def test_get_recent_activities_success(self, activity_service, mock_db_service):
        """get_recent_activities should return activities from db."""
        expected = [
            ActivityLog(
                id="act-1",
                activity_type=ActivityType.USER_LOGIN,
                message="Login",
                timestamp=datetime.now(UTC).isoformat()
            )
        ]
        mock_db_service.get_activity_logs = AsyncMock(return_value=expected)

        result = await activity_service.get_recent_activities()

        assert result == expected
        mock_db_service.get_activity_logs.assert_called_once_with(limit=20)

    @pytest.mark.asyncio
    async def test_get_recent_activities_custom_limit(self, activity_service, mock_db_service):
        """get_recent_activities should use custom limit."""
        mock_db_service.get_activity_logs = AsyncMock(return_value=[])

        await activity_service.get_recent_activities(limit=50)

        mock_db_service.get_activity_logs.assert_called_once_with(limit=50)

    @pytest.mark.asyncio
    async def test_get_recent_activities_db_error(self, activity_service, mock_db_service):
        """get_recent_activities should return empty list on error."""
        mock_db_service.get_activity_logs = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await activity_service.get_recent_activities()

        assert result == []


class TestGetActivities:
    """Tests for get_activities method."""

    @pytest.mark.asyncio
    async def test_get_activities_no_filters(self, activity_service, mock_db_service):
        """get_activities should call db with default params."""
        mock_db_service.get_activity_logs = AsyncMock(return_value=[])

        await activity_service.get_activities()

        mock_db_service.get_activity_logs.assert_called_once_with(
            activity_types=None,
            user_id=None,
            server_id=None,
            since=None,
            until=None,
            limit=100,
            offset=0
        )

    @pytest.mark.asyncio
    async def test_get_activities_with_type_filter(self, activity_service, mock_db_service):
        """get_activities should convert activity types to values."""
        mock_db_service.get_activity_logs = AsyncMock(return_value=[])

        await activity_service.get_activities(
            activity_types=[ActivityType.USER_LOGIN, ActivityType.USER_LOGOUT]
        )

        call_args = mock_db_service.get_activity_logs.call_args
        assert call_args.kwargs["activity_types"] == ["user_login", "user_logout"]

    @pytest.mark.asyncio
    async def test_get_activities_with_all_filters(self, activity_service, mock_db_service):
        """get_activities should pass all filters to db."""
        mock_db_service.get_activity_logs = AsyncMock(return_value=[])

        await activity_service.get_activities(
            activity_types=[ActivityType.SERVER_ADDED],
            user_id="user-123",
            server_id="server-456",
            since="2024-01-01T00:00:00",
            until="2024-12-31T23:59:59",
            limit=50,
            offset=10
        )

        mock_db_service.get_activity_logs.assert_called_once_with(
            activity_types=["server_added"],
            user_id="user-123",
            server_id="server-456",
            since="2024-01-01T00:00:00",
            until="2024-12-31T23:59:59",
            limit=50,
            offset=10
        )

    @pytest.mark.asyncio
    async def test_get_activities_db_error(self, activity_service, mock_db_service):
        """get_activities should return empty list on error."""
        mock_db_service.get_activity_logs = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await activity_service.get_activities()

        assert result == []


class TestGetActivityCount:
    """Tests for get_activity_count method."""

    @pytest.mark.asyncio
    async def test_get_activity_count_no_filters(self, activity_service, mock_db_service):
        """get_activity_count should call db with default params."""
        mock_db_service.count_activity_logs = AsyncMock(return_value=42)

        result = await activity_service.get_activity_count()

        assert result == 42
        mock_db_service.count_activity_logs.assert_called_once_with(
            activity_types=None,
            since=None
        )

    @pytest.mark.asyncio
    async def test_get_activity_count_with_type_filter(self, activity_service, mock_db_service):
        """get_activity_count should convert activity types to values."""
        mock_db_service.count_activity_logs = AsyncMock(return_value=10)

        await activity_service.get_activity_count(
            activity_types=[ActivityType.APP_INSTALLED]
        )

        call_args = mock_db_service.count_activity_logs.call_args
        assert call_args.kwargs["activity_types"] == ["app_installed"]

    @pytest.mark.asyncio
    async def test_get_activity_count_with_since(self, activity_service, mock_db_service):
        """get_activity_count should pass since filter."""
        mock_db_service.count_activity_logs = AsyncMock(return_value=5)

        await activity_service.get_activity_count(since="2024-01-01T00:00:00")

        mock_db_service.count_activity_logs.assert_called_once_with(
            activity_types=None,
            since="2024-01-01T00:00:00"
        )

    @pytest.mark.asyncio
    async def test_get_activity_count_db_error(self, activity_service, mock_db_service):
        """get_activity_count should return 0 on error."""
        mock_db_service.count_activity_logs = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await activity_service.get_activity_count()

        assert result == 0

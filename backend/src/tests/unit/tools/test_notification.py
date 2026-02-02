"""
Notification Tools Unit Tests

Tests for notification management tools.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from tools.notification.tools import NotificationTools
from models.notification import NotificationType


class TestNotificationToolsInit:
    """Tests for NotificationTools initialization."""

    def test_initialization(self):
        """Test NotificationTools is initialized correctly."""
        mock_notification_service = MagicMock()
        mock_auth_service = MagicMock()

        with patch('tools.notification.tools.logger'):
            tools = NotificationTools(mock_notification_service, mock_auth_service)

        assert tools.notification_service == mock_notification_service
        assert tools.auth_service == mock_auth_service

    def test_initialization_without_auth(self):
        """Test initialization without auth service."""
        mock_notification_service = MagicMock()

        with patch('tools.notification.tools.logger'):
            tools = NotificationTools(mock_notification_service)

        assert tools.auth_service is None


class TestGetUserContext:
    """Tests for _get_user_context method."""

    @pytest.fixture
    def tools(self):
        """Create NotificationTools instance."""
        with patch('tools.notification.tools.logger'):
            return NotificationTools(MagicMock())

    def test_get_user_context_with_meta(self, tools):
        """Test extracting user context from ctx.meta."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "role": "admin"}

        user_id, role = tools._get_user_context(ctx)

        assert user_id == "user-123"
        assert role == "admin"

    def test_get_user_context_without_meta(self, tools):
        """Test extracting user context when meta is None."""
        ctx = MagicMock()
        ctx.meta = None

        user_id, role = tools._get_user_context(ctx)

        assert user_id == ""
        assert role == "user"

    def test_get_user_context_default_role(self, tools):
        """Test default role when not specified."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123"}

        user_id, role = tools._get_user_context(ctx)

        assert role == "user"


class TestIsAdmin:
    """Tests for _is_admin method."""

    @pytest.fixture
    def tools(self):
        """Create NotificationTools instance."""
        with patch('tools.notification.tools.logger'):
            return NotificationTools(MagicMock())

    def test_is_admin_true(self, tools):
        """Test admin role check returns True."""
        assert tools._is_admin("admin") is True

    def test_is_admin_false(self, tools):
        """Test non-admin role check returns False."""
        assert tools._is_admin("user") is False
        assert tools._is_admin("guest") is False
        assert tools._is_admin("") is False


class TestListNotifications:
    """Tests for list_notifications tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock notification service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create NotificationTools instance."""
        with patch('tools.notification.tools.logger'):
            return NotificationTools(mock_service)

    @pytest.fixture
    def mock_ctx(self):
        """Create mock context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "role": "user"}
        return ctx

    @pytest.fixture
    def sample_result(self):
        """Create sample notification list result."""
        notification = MagicMock()
        notification.model_dump.return_value = {
            "id": "notif-1",
            "title": "Test",
            "message": "Test message"
        }
        result = MagicMock()
        result.notifications = [notification]
        result.total = 1
        result.unread_count = 1
        return result

    @pytest.mark.asyncio
    async def test_list_notifications_success(
        self, tools, mock_service, mock_ctx, sample_result
    ):
        """Test successfully listing notifications."""
        mock_service.list_notifications = AsyncMock(return_value=sample_result)

        result = await tools.list_notifications({}, mock_ctx)

        assert result["success"] is True
        assert len(result["data"]["notifications"]) == 1
        assert result["data"]["total"] == 1

    @pytest.mark.asyncio
    async def test_list_notifications_not_authenticated(self, tools, mock_service):
        """Test listing when not authenticated."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "", "role": "user"}

        result = await tools.list_notifications({}, ctx)

        assert result["success"] is False
        assert result["error"] == "AUTH_REQUIRED"

    @pytest.mark.asyncio
    async def test_list_notifications_with_read_filter_true(
        self, tools, mock_service, mock_ctx, sample_result
    ):
        """Test filtering by read=true."""
        mock_service.list_notifications = AsyncMock(return_value=sample_result)

        await tools.list_notifications({"read": True}, mock_ctx)

        call_kwargs = mock_service.list_notifications.call_args.kwargs
        assert call_kwargs["read_filter"] is True

    @pytest.mark.asyncio
    async def test_list_notifications_with_read_filter_string(
        self, tools, mock_service, mock_ctx, sample_result
    ):
        """Test filtering by read='true' string."""
        mock_service.list_notifications = AsyncMock(return_value=sample_result)

        await tools.list_notifications({"read": "true"}, mock_ctx)

        call_kwargs = mock_service.list_notifications.call_args.kwargs
        assert call_kwargs["read_filter"] is True

    @pytest.mark.asyncio
    async def test_list_notifications_with_type_filter(
        self, tools, mock_service, mock_ctx, sample_result
    ):
        """Test filtering by notification type."""
        mock_service.list_notifications = AsyncMock(return_value=sample_result)

        await tools.list_notifications({"type": "info"}, mock_ctx)

        call_kwargs = mock_service.list_notifications.call_args.kwargs
        assert call_kwargs["notification_type"] == NotificationType.INFO

    @pytest.mark.asyncio
    async def test_list_notifications_invalid_type(
        self, tools, mock_service, mock_ctx
    ):
        """Test with invalid notification type."""
        result = await tools.list_notifications({"type": "invalid"}, mock_ctx)

        assert result["success"] is False
        assert result["error"] == "INVALID_TYPE"

    @pytest.mark.asyncio
    async def test_list_notifications_with_pagination(
        self, tools, mock_service, mock_ctx, sample_result
    ):
        """Test with pagination parameters."""
        mock_service.list_notifications = AsyncMock(return_value=sample_result)

        await tools.list_notifications({"limit": 10, "offset": 20}, mock_ctx)

        call_kwargs = mock_service.list_notifications.call_args.kwargs
        assert call_kwargs["limit"] == 10
        assert call_kwargs["offset"] == 20

    @pytest.mark.asyncio
    async def test_list_notifications_exception(
        self, tools, mock_service, mock_ctx
    ):
        """Test handling exceptions."""
        mock_service.list_notifications = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await tools.list_notifications({}, mock_ctx)

        assert result["success"] is False
        assert result["error"] == "LIST_ERROR"


class TestGetNotification:
    """Tests for get_notification tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock notification service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create NotificationTools instance."""
        with patch('tools.notification.tools.logger'):
            return NotificationTools(mock_service)

    @pytest.fixture
    def mock_ctx(self):
        """Create mock context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "role": "user"}
        return ctx

    @pytest.mark.asyncio
    async def test_get_notification_success(self, tools, mock_service, mock_ctx):
        """Test successfully getting a notification."""
        notification = MagicMock()
        notification.user_id = "user-123"
        notification.model_dump.return_value = {"id": "notif-1", "title": "Test"}
        mock_service.get_notification = AsyncMock(return_value=notification)

        result = await tools.get_notification(
            {"notification_id": "notif-1"}, mock_ctx
        )

        assert result["success"] is True
        assert result["data"]["id"] == "notif-1"

    @pytest.mark.asyncio
    async def test_get_notification_missing_id(self, tools, mock_service, mock_ctx):
        """Test without notification_id."""
        result = await tools.get_notification({}, mock_ctx)

        assert result["success"] is False
        assert result["error"] == "MISSING_PARAM"

    @pytest.mark.asyncio
    async def test_get_notification_not_found(self, tools, mock_service, mock_ctx):
        """Test when notification doesn't exist."""
        mock_service.get_notification = AsyncMock(return_value=None)

        result = await tools.get_notification(
            {"notification_id": "notif-404"}, mock_ctx
        )

        assert result["success"] is False
        assert result["error"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_notification_permission_denied(
        self, tools, mock_service, mock_ctx
    ):
        """Test accessing another user's notification."""
        notification = MagicMock()
        notification.user_id = "other-user"
        mock_service.get_notification = AsyncMock(return_value=notification)

        result = await tools.get_notification(
            {"notification_id": "notif-1"}, mock_ctx
        )

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_get_notification_exception(self, tools, mock_service, mock_ctx):
        """Test handling exceptions."""
        mock_service.get_notification = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await tools.get_notification(
            {"notification_id": "notif-1"}, mock_ctx
        )

        assert result["success"] is False
        assert result["error"] == "GET_ERROR"


class TestCreateNotification:
    """Tests for create_notification tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock notification service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create NotificationTools instance."""
        with patch('tools.notification.tools.logger'):
            return NotificationTools(mock_service)

    @pytest.fixture
    def mock_admin_ctx(self):
        """Create admin context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "admin-123", "role": "admin"}
        return ctx

    @pytest.fixture
    def mock_user_ctx(self):
        """Create user context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "role": "user"}
        return ctx

    @pytest.mark.asyncio
    async def test_create_notification_admin_success(
        self, tools, mock_service, mock_admin_ctx
    ):
        """Test admin creating notification for another user."""
        notification = MagicMock()
        notification.model_dump.return_value = {"id": "notif-1", "title": "Test"}
        mock_service.create_notification = AsyncMock(return_value=notification)

        result = await tools.create_notification({
            "user_id": "other-user",
            "type": "info",
            "title": "Test",
            "message": "Test message"
        }, mock_admin_ctx)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_create_notification_user_self(
        self, tools, mock_service, mock_user_ctx
    ):
        """Test user creating notification for self."""
        notification = MagicMock()
        notification.model_dump.return_value = {"id": "notif-1", "title": "Test"}
        mock_service.create_notification = AsyncMock(return_value=notification)

        result = await tools.create_notification({
            "type": "info",
            "title": "Test",
            "message": "Test message"
        }, mock_user_ctx)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_create_notification_user_for_other_denied(
        self, tools, mock_service, mock_user_ctx
    ):
        """Test non-admin trying to create for another user."""
        result = await tools.create_notification({
            "user_id": "other-user",
            "type": "info",
            "title": "Test",
            "message": "Test message"
        }, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_create_notification_missing_params(
        self, tools, mock_service, mock_user_ctx
    ):
        """Test with missing required parameters."""
        result = await tools.create_notification({
            "type": "info"
            # missing title and message
        }, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "MISSING_PARAM"

    @pytest.mark.asyncio
    async def test_create_notification_invalid_type(
        self, tools, mock_service, mock_user_ctx
    ):
        """Test with invalid notification type."""
        result = await tools.create_notification({
            "type": "invalid",
            "title": "Test",
            "message": "Test message"
        }, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "INVALID_TYPE"

    @pytest.mark.asyncio
    async def test_create_notification_exception(
        self, tools, mock_service, mock_user_ctx
    ):
        """Test handling exceptions."""
        mock_service.create_notification = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await tools.create_notification({
            "type": "info",
            "title": "Test",
            "message": "Test message"
        }, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "CREATE_ERROR"


class TestMarkNotificationRead:
    """Tests for mark_notification_read tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock notification service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create NotificationTools instance."""
        with patch('tools.notification.tools.logger'):
            return NotificationTools(mock_service)

    @pytest.fixture
    def mock_ctx(self):
        """Create mock context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "role": "user"}
        return ctx

    @pytest.mark.asyncio
    async def test_mark_read_success(self, tools, mock_service, mock_ctx):
        """Test successfully marking as read."""
        mock_service.mark_as_read = AsyncMock(return_value=True)

        result = await tools.mark_notification_read(
            {"notification_id": "notif-1"}, mock_ctx
        )

        assert result["success"] is True
        assert result["data"]["updated"] is True

    @pytest.mark.asyncio
    async def test_mark_read_not_found(self, tools, mock_service, mock_ctx):
        """Test marking non-existent notification."""
        mock_service.mark_as_read = AsyncMock(return_value=False)

        result = await tools.mark_notification_read(
            {"notification_id": "notif-404"}, mock_ctx
        )

        assert result["success"] is True
        assert result["data"]["updated"] is False

    @pytest.mark.asyncio
    async def test_mark_read_missing_id(self, tools, mock_service, mock_ctx):
        """Test without notification_id."""
        result = await tools.mark_notification_read({}, mock_ctx)

        assert result["success"] is False
        assert result["error"] == "MISSING_PARAM"

    @pytest.mark.asyncio
    async def test_mark_read_exception(self, tools, mock_service, mock_ctx):
        """Test handling exceptions."""
        mock_service.mark_as_read = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await tools.mark_notification_read(
            {"notification_id": "notif-1"}, mock_ctx
        )

        assert result["success"] is False
        assert result["error"] == "UPDATE_ERROR"


class TestMarkAllNotificationsRead:
    """Tests for mark_all_notifications_read tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock notification service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create NotificationTools instance."""
        with patch('tools.notification.tools.logger'):
            return NotificationTools(mock_service)

    @pytest.fixture
    def mock_ctx(self):
        """Create mock context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "role": "user"}
        return ctx

    @pytest.mark.asyncio
    async def test_mark_all_read_success(self, tools, mock_service, mock_ctx):
        """Test successfully marking all as read."""
        mock_service.mark_all_as_read = AsyncMock(return_value=5)

        result = await tools.mark_all_notifications_read({}, mock_ctx)

        assert result["success"] is True
        assert result["data"]["count"] == 5

    @pytest.mark.asyncio
    async def test_mark_all_read_not_authenticated(self, tools, mock_service):
        """Test when not authenticated."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "", "role": "user"}

        result = await tools.mark_all_notifications_read({}, ctx)

        assert result["success"] is False
        assert result["error"] == "AUTH_REQUIRED"

    @pytest.mark.asyncio
    async def test_mark_all_read_exception(self, tools, mock_service, mock_ctx):
        """Test handling exceptions."""
        mock_service.mark_all_as_read = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await tools.mark_all_notifications_read({}, mock_ctx)

        assert result["success"] is False
        assert result["error"] == "UPDATE_ERROR"


class TestDismissNotification:
    """Tests for dismiss_notification tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock notification service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create NotificationTools instance."""
        with patch('tools.notification.tools.logger'):
            return NotificationTools(mock_service)

    @pytest.fixture
    def mock_ctx(self):
        """Create mock context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "role": "user"}
        return ctx

    @pytest.mark.asyncio
    async def test_dismiss_success(self, tools, mock_service, mock_ctx):
        """Test successfully dismissing a notification."""
        mock_service.dismiss_notification = AsyncMock(return_value=True)

        result = await tools.dismiss_notification(
            {"notification_id": "notif-1"}, mock_ctx
        )

        assert result["success"] is True
        assert result["data"]["dismissed"] is True

    @pytest.mark.asyncio
    async def test_dismiss_not_found(self, tools, mock_service, mock_ctx):
        """Test dismissing non-existent notification."""
        mock_service.dismiss_notification = AsyncMock(return_value=False)

        result = await tools.dismiss_notification(
            {"notification_id": "notif-404"}, mock_ctx
        )

        assert result["success"] is True
        assert result["data"]["dismissed"] is False

    @pytest.mark.asyncio
    async def test_dismiss_missing_id(self, tools, mock_service, mock_ctx):
        """Test without notification_id."""
        result = await tools.dismiss_notification({}, mock_ctx)

        assert result["success"] is False
        assert result["error"] == "MISSING_PARAM"

    @pytest.mark.asyncio
    async def test_dismiss_exception(self, tools, mock_service, mock_ctx):
        """Test handling exceptions."""
        mock_service.dismiss_notification = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await tools.dismiss_notification(
            {"notification_id": "notif-1"}, mock_ctx
        )

        assert result["success"] is False
        assert result["error"] == "DISMISS_ERROR"


class TestDismissAllNotifications:
    """Tests for dismiss_all_notifications tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock notification service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create NotificationTools instance."""
        with patch('tools.notification.tools.logger'):
            return NotificationTools(mock_service)

    @pytest.fixture
    def mock_ctx(self):
        """Create mock context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "role": "user"}
        return ctx

    @pytest.mark.asyncio
    async def test_dismiss_all_success(self, tools, mock_service, mock_ctx):
        """Test successfully dismissing all."""
        mock_service.dismiss_all = AsyncMock(return_value=10)

        result = await tools.dismiss_all_notifications({}, mock_ctx)

        assert result["success"] is True
        assert result["data"]["count"] == 10

    @pytest.mark.asyncio
    async def test_dismiss_all_not_authenticated(self, tools, mock_service):
        """Test when not authenticated."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "", "role": "user"}

        result = await tools.dismiss_all_notifications({}, ctx)

        assert result["success"] is False
        assert result["error"] == "AUTH_REQUIRED"

    @pytest.mark.asyncio
    async def test_dismiss_all_exception(self, tools, mock_service, mock_ctx):
        """Test handling exceptions."""
        mock_service.dismiss_all = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await tools.dismiss_all_notifications({}, mock_ctx)

        assert result["success"] is False
        assert result["error"] == "DISMISS_ERROR"


class TestGetUnreadCount:
    """Tests for get_unread_count tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock notification service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create NotificationTools instance."""
        with patch('tools.notification.tools.logger'):
            return NotificationTools(mock_service)

    @pytest.fixture
    def mock_ctx(self):
        """Create mock context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "role": "user"}
        return ctx

    @pytest.mark.asyncio
    async def test_get_unread_count_success(self, tools, mock_service, mock_ctx):
        """Test successfully getting unread count."""
        count_result = MagicMock()
        count_result.model_dump.return_value = {"unread_count": 5, "total": 10}
        count_result.unread_count = 5
        mock_service.get_unread_count = AsyncMock(return_value=count_result)

        result = await tools.get_unread_count({}, mock_ctx)

        assert result["success"] is True
        assert result["data"]["unread_count"] == 5

    @pytest.mark.asyncio
    async def test_get_unread_count_not_authenticated(self, tools, mock_service):
        """Test when not authenticated."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "", "role": "user"}

        result = await tools.get_unread_count({}, ctx)

        assert result["success"] is False
        assert result["error"] == "AUTH_REQUIRED"

    @pytest.mark.asyncio
    async def test_get_unread_count_exception(self, tools, mock_service, mock_ctx):
        """Test handling exceptions."""
        mock_service.get_unread_count = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await tools.get_unread_count({}, mock_ctx)

        assert result["success"] is False
        assert result["error"] == "COUNT_ERROR"

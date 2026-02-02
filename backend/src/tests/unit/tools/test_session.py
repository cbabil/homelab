"""
Session Tools Unit Tests

Tests for session management tools.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from tools.session.tools import SessionTools
from models.session import SessionStatus


class TestSessionToolsInit:
    """Tests for SessionTools initialization."""

    def test_initialization(self):
        """Test SessionTools is initialized correctly."""
        mock_session_service = MagicMock()
        mock_auth_service = MagicMock()

        with patch('tools.session.tools.logger'):
            tools = SessionTools(mock_session_service, mock_auth_service)

        assert tools.session_service == mock_session_service
        assert tools.auth_service == mock_auth_service

    def test_initialization_without_auth(self):
        """Test initialization without auth service."""
        mock_session_service = MagicMock()

        with patch('tools.session.tools.logger'):
            tools = SessionTools(mock_session_service)

        assert tools.auth_service is None


class TestGetUserContext:
    """Tests for _get_user_context method."""

    @pytest.fixture
    def tools(self):
        """Create SessionTools instance."""
        with patch('tools.session.tools.logger'):
            return SessionTools(MagicMock())

    def test_get_user_context_full(self, tools):
        """Test extracting full user context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "session_id": "sess-456", "role": "admin"}

        user_id, session_id, role = tools._get_user_context(ctx)

        assert user_id == "user-123"
        assert session_id == "sess-456"
        assert role == "admin"

    def test_get_user_context_defaults(self, tools):
        """Test default values when meta is None."""
        ctx = MagicMock()
        ctx.meta = None

        user_id, session_id, role = tools._get_user_context(ctx)

        assert user_id == ""
        assert session_id == ""
        assert role == "user"


class TestIsAdmin:
    """Tests for _is_admin method."""

    @pytest.fixture
    def tools(self):
        """Create SessionTools instance."""
        with patch('tools.session.tools.logger'):
            return SessionTools(MagicMock())

    def test_is_admin_true(self, tools):
        """Test admin role returns True."""
        assert tools._is_admin("admin") is True

    def test_is_admin_false(self, tools):
        """Test non-admin roles return False."""
        assert tools._is_admin("user") is False


class TestListSessions:
    """Tests for list_sessions tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock session service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create SessionTools instance."""
        with patch('tools.session.tools.logger'):
            return SessionTools(mock_service)

    @pytest.fixture
    def mock_user_ctx(self):
        """Create user context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "session_id": "sess-current", "role": "user"}
        return ctx

    @pytest.fixture
    def mock_admin_ctx(self):
        """Create admin context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "admin-123", "session_id": "sess-admin", "role": "admin"}
        return ctx

    @pytest.fixture
    def sample_sessions(self):
        """Create sample sessions."""
        sess1 = MagicMock()
        sess1.id = "sess-current"
        sess1.model_dump.return_value = {"id": "sess-current", "status": "active"}

        sess2 = MagicMock()
        sess2.id = "sess-other"
        sess2.model_dump.return_value = {"id": "sess-other", "status": "active"}
        return [sess1, sess2]

    @pytest.mark.asyncio
    async def test_list_sessions_success(
        self, tools, mock_service, mock_user_ctx, sample_sessions
    ):
        """Test successfully listing own sessions."""
        mock_service.list_sessions = AsyncMock(return_value=sample_sessions)

        result = await tools.list_sessions({}, mock_user_ctx)

        assert result["success"] is True
        assert len(result["data"]) == 2
        # First session should be marked as current
        assert result["data"][0]["is_current"] is True
        assert result["data"][1]["is_current"] is False

    @pytest.mark.asyncio
    async def test_list_sessions_admin_other_user(
        self, tools, mock_service, mock_admin_ctx, sample_sessions
    ):
        """Test admin listing another user's sessions."""
        mock_service.list_sessions = AsyncMock(return_value=sample_sessions)

        result = await tools.list_sessions(
            {"user_id": "other-user"}, mock_admin_ctx
        )

        assert result["success"] is True
        mock_service.list_sessions.assert_called_with(
            user_id="other-user", status=None
        )

    @pytest.mark.asyncio
    async def test_list_sessions_user_denied_other(
        self, tools, mock_service, mock_user_ctx
    ):
        """Test user cannot list another user's sessions."""
        result = await tools.list_sessions(
            {"user_id": "other-user"}, mock_user_ctx
        )

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_list_sessions_with_status_filter(
        self, tools, mock_service, mock_user_ctx, sample_sessions
    ):
        """Test listing with status filter."""
        mock_service.list_sessions = AsyncMock(return_value=sample_sessions)

        result = await tools.list_sessions(
            {"status": "active"}, mock_user_ctx
        )

        assert result["success"] is True
        mock_service.list_sessions.assert_called_with(
            user_id="user-123", status=SessionStatus.ACTIVE
        )

    @pytest.mark.asyncio
    async def test_list_sessions_exception(self, tools, mock_service, mock_user_ctx):
        """Test handling exceptions."""
        mock_service.list_sessions = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await tools.list_sessions({}, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "LIST_ERROR"


class TestGetSession:
    """Tests for get_session tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock session service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create SessionTools instance."""
        with patch('tools.session.tools.logger'):
            return SessionTools(mock_service)

    @pytest.fixture
    def mock_user_ctx(self):
        """Create user context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "session_id": "sess-current", "role": "user"}
        return ctx

    @pytest.fixture
    def mock_admin_ctx(self):
        """Create admin context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "admin-123", "role": "admin"}
        return ctx

    @pytest.mark.asyncio
    async def test_get_session_success(self, tools, mock_service, mock_user_ctx):
        """Test successfully getting own session."""
        session = MagicMock()
        session.user_id = "user-123"
        session.model_dump.return_value = {"id": "sess-1", "user_id": "user-123"}
        mock_service.get_session = AsyncMock(return_value=session)

        result = await tools.get_session({"session_id": "sess-1"}, mock_user_ctx)

        assert result["success"] is True
        assert result["data"]["id"] == "sess-1"

    @pytest.mark.asyncio
    async def test_get_session_missing_id(self, tools, mock_service, mock_user_ctx):
        """Test without session_id."""
        result = await tools.get_session({}, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "MISSING_PARAM"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, tools, mock_service, mock_user_ctx):
        """Test when session not found."""
        mock_service.get_session = AsyncMock(return_value=None)

        result = await tools.get_session({"session_id": "sess-404"}, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_session_permission_denied(
        self, tools, mock_service, mock_user_ctx
    ):
        """Test accessing another user's session."""
        session = MagicMock()
        session.user_id = "other-user"
        mock_service.get_session = AsyncMock(return_value=session)

        result = await tools.get_session({"session_id": "sess-1"}, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_get_session_admin_other_user(
        self, tools, mock_service, mock_admin_ctx
    ):
        """Test admin accessing another user's session."""
        session = MagicMock()
        session.user_id = "other-user"
        session.model_dump.return_value = {"id": "sess-1", "user_id": "other-user"}
        mock_service.get_session = AsyncMock(return_value=session)

        result = await tools.get_session({"session_id": "sess-1"}, mock_admin_ctx)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_session_exception(self, tools, mock_service, mock_user_ctx):
        """Test handling exceptions."""
        mock_service.get_session = AsyncMock(side_effect=Exception("Database error"))

        result = await tools.get_session({"session_id": "sess-1"}, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "GET_ERROR"


class TestUpdateSession:
    """Tests for update_session tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock session service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create SessionTools instance."""
        with patch('tools.session.tools.logger'):
            return SessionTools(mock_service)

    @pytest.fixture
    def mock_user_ctx(self):
        """Create user context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "session_id": "sess-current", "role": "user"}
        return ctx

    @pytest.fixture
    def mock_admin_ctx(self):
        """Create admin context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "admin-123", "role": "admin"}
        return ctx

    @pytest.mark.asyncio
    async def test_update_session_success(self, tools, mock_service, mock_user_ctx):
        """Test successfully updating own session."""
        session = MagicMock()
        session.user_id = "user-123"
        mock_service.get_session = AsyncMock(return_value=session)
        mock_service.update_session = AsyncMock(return_value=True)

        result = await tools.update_session({"session_id": "sess-1"}, mock_user_ctx)

        assert result["success"] is True
        assert result["data"]["updated"] is True

    @pytest.mark.asyncio
    async def test_update_session_missing_id(self, tools, mock_service, mock_user_ctx):
        """Test without session_id."""
        result = await tools.update_session({}, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "MISSING_PARAM"

    @pytest.mark.asyncio
    async def test_update_session_permission_denied(
        self, tools, mock_service, mock_user_ctx
    ):
        """Test updating another user's session."""
        session = MagicMock()
        session.user_id = "other-user"
        mock_service.get_session = AsyncMock(return_value=session)

        result = await tools.update_session({"session_id": "sess-1"}, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_update_session_not_found_for_user(
        self, tools, mock_service, mock_user_ctx
    ):
        """Test when session not found (for non-admin)."""
        mock_service.get_session = AsyncMock(return_value=None)

        result = await tools.update_session({"session_id": "sess-404"}, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_update_session_admin_skips_check(
        self, tools, mock_service, mock_admin_ctx
    ):
        """Test admin can update any session without permission check."""
        mock_service.update_session = AsyncMock(return_value=True)

        result = await tools.update_session({"session_id": "sess-1"}, mock_admin_ctx)

        assert result["success"] is True
        # Should not call get_session for permission check
        mock_service.get_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_session_exception(self, tools, mock_service, mock_admin_ctx):
        """Test handling exceptions."""
        mock_service.update_session = AsyncMock(side_effect=Exception("Database error"))

        result = await tools.update_session({"session_id": "sess-1"}, mock_admin_ctx)

        assert result["success"] is False
        assert result["error"] == "UPDATE_ERROR"


class TestDeleteSession:
    """Tests for delete_session tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock session service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create SessionTools instance."""
        with patch('tools.session.tools.logger'):
            return SessionTools(mock_service)

    @pytest.fixture
    def mock_user_ctx(self):
        """Create user context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "session_id": "sess-current", "role": "user"}
        return ctx

    @pytest.fixture
    def mock_admin_ctx(self):
        """Create admin context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "admin-123", "session_id": "sess-admin", "role": "admin"}
        return ctx

    @pytest.mark.asyncio
    async def test_delete_specific_session_success(
        self, tools, mock_service, mock_user_ctx
    ):
        """Test deleting specific own session."""
        session = MagicMock()
        session.user_id = "user-123"
        mock_service.get_session = AsyncMock(return_value=session)
        mock_service.delete_session = AsyncMock(return_value=1)

        result = await tools.delete_session({"session_id": "sess-1"}, mock_user_ctx)

        assert result["success"] is True
        assert result["data"]["count"] == 1

    @pytest.mark.asyncio
    async def test_delete_specific_session_not_found(
        self, tools, mock_service, mock_user_ctx
    ):
        """Test deleting non-existent session."""
        mock_service.get_session = AsyncMock(return_value=None)

        result = await tools.delete_session({"session_id": "sess-404"}, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_delete_specific_session_permission_denied(
        self, tools, mock_service, mock_user_ctx
    ):
        """Test deleting another user's session."""
        session = MagicMock()
        session.user_id = "other-user"
        mock_service.get_session = AsyncMock(return_value=session)

        result = await tools.delete_session({"session_id": "sess-1"}, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_delete_all_own_sessions(self, tools, mock_service, mock_user_ctx):
        """Test deleting all own sessions."""
        mock_service.delete_session = AsyncMock(return_value=3)

        result = await tools.delete_session({"all": True}, mock_user_ctx)

        assert result["success"] is True
        assert result["data"]["count"] == 3
        mock_service.delete_session.assert_called_with(
            user_id="user-123",
            terminated_by="user-123",
            exclude_session_id="sess-current"
        )

    @pytest.mark.asyncio
    async def test_delete_all_without_exclude_current(
        self, tools, mock_service, mock_user_ctx
    ):
        """Test deleting all sessions without excluding current."""
        mock_service.delete_session = AsyncMock(return_value=4)

        result = await tools.delete_session(
            {"all": True, "exclude_current": False}, mock_user_ctx
        )

        assert result["success"] is True
        mock_service.delete_session.assert_called_with(
            user_id="user-123",
            terminated_by="user-123",
            exclude_session_id=None
        )

    @pytest.mark.asyncio
    async def test_delete_by_user_id_admin(self, tools, mock_service, mock_admin_ctx):
        """Test admin deleting by user_id."""
        mock_service.delete_session = AsyncMock(return_value=5)

        result = await tools.delete_session(
            {"user_id": "target-user"}, mock_admin_ctx
        )

        assert result["success"] is True
        mock_service.delete_session.assert_called_with(
            user_id="target-user",
            terminated_by="admin-123",
            exclude_session_id="sess-admin"
        )

    @pytest.mark.asyncio
    async def test_delete_by_user_id_permission_denied(
        self, tools, mock_service, mock_user_ctx
    ):
        """Test non-admin cannot delete by user_id of another user."""
        result = await tools.delete_session(
            {"user_id": "other-user"}, mock_user_ctx
        )

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_delete_missing_params(self, tools, mock_service, mock_user_ctx):
        """Test without required parameters."""
        result = await tools.delete_session({}, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "MISSING_PARAM"

    @pytest.mark.asyncio
    async def test_delete_exception(self, tools, mock_service, mock_user_ctx):
        """Test handling exceptions."""
        mock_service.delete_session = AsyncMock(side_effect=Exception("Database error"))

        result = await tools.delete_session({"all": True}, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "DELETE_ERROR"


class TestCleanupExpiredSessions:
    """Tests for cleanup_expired_sessions tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock session service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create SessionTools instance."""
        with patch('tools.session.tools.logger'):
            return SessionTools(mock_service)

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
    async def test_cleanup_success(self, tools, mock_service, mock_admin_ctx):
        """Test successfully cleaning up expired sessions."""
        mock_service.cleanup_expired_sessions = AsyncMock(return_value=10)

        result = await tools.cleanup_expired_sessions({}, mock_admin_ctx)

        assert result["success"] is True
        assert result["data"]["count"] == 10

    @pytest.mark.asyncio
    async def test_cleanup_permission_denied(self, tools, mock_service, mock_user_ctx):
        """Test non-admin cannot cleanup."""
        result = await tools.cleanup_expired_sessions({}, mock_user_ctx)

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_cleanup_exception(self, tools, mock_service, mock_admin_ctx):
        """Test handling exceptions."""
        mock_service.cleanup_expired_sessions = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await tools.cleanup_expired_sessions({}, mock_admin_ctx)

        assert result["success"] is False
        assert result["error"] == "CLEANUP_ERROR"

"""
Retention Tools Unit Tests

Tests for data retention management tools.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from tools.retention.tools import RetentionTools
from models.retention import RetentionType


class TestRetentionToolsInit:
    """Tests for RetentionTools initialization."""

    def test_initialization_with_service(self):
        """Test RetentionTools with provided service."""
        mock_service = MagicMock()
        mock_auth = MagicMock()

        with patch('tools.retention.tools.logger'):
            tools = RetentionTools(mock_service, mock_auth)

        assert tools.retention_service == mock_service
        assert tools.auth_service == mock_auth

    def test_initialization_without_service(self):
        """Test RetentionTools creates default service."""
        with patch('tools.retention.tools.logger'):
            with patch('tools.retention.tools.RetentionService') as mock_svc_class:
                tools = RetentionTools()

        mock_svc_class.assert_called_once()
        assert tools.auth_service is None


class TestGetUserContext:
    """Tests for _get_user_context method."""

    @pytest.fixture
    def tools(self):
        """Create RetentionTools instance."""
        with patch('tools.retention.tools.logger'):
            return RetentionTools(MagicMock())

    def test_get_user_context_full(self, tools):
        """Test extracting full user context."""
        ctx = MagicMock()
        ctx.meta = {
            "user_id": "user-123",
            "session_id": "sess-456",
            "role": "admin",
            "token": "tok-789"
        }

        user_id, session_id, role, token = tools._get_user_context(ctx)

        assert user_id == "user-123"
        assert session_id == "sess-456"
        assert role == "admin"
        assert token == "tok-789"

    def test_get_user_context_defaults(self, tools):
        """Test default values when meta is None."""
        ctx = MagicMock()
        ctx.meta = None

        user_id, session_id, role, token = tools._get_user_context(ctx)

        assert user_id == ""
        assert session_id == ""
        assert role == "user"
        assert token == ""


class TestIsAdmin:
    """Tests for _is_admin method."""

    @pytest.fixture
    def tools(self):
        """Create RetentionTools instance."""
        with patch('tools.retention.tools.logger'):
            return RetentionTools(MagicMock())

    def test_is_admin_true(self, tools):
        """Test admin role returns True."""
        assert tools._is_admin("admin") is True

    def test_is_admin_false(self, tools):
        """Test non-admin roles return False."""
        assert tools._is_admin("user") is False
        assert tools._is_admin("") is False


class TestGetCsrfToken:
    """Tests for get_csrf_token tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock retention service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create RetentionTools instance."""
        with patch('tools.retention.tools.logger'):
            return RetentionTools(mock_service)

    @pytest.fixture
    def mock_admin_ctx(self):
        """Create admin context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "admin-123", "session_id": "sess-456", "role": "admin"}
        return ctx

    @pytest.mark.asyncio
    async def test_get_csrf_token_success(self, tools, mock_admin_ctx):
        """Test successfully generating CSRF token."""
        with patch('tools.retention.tools.csrf_service') as mock_csrf:
            mock_csrf.generate_token.return_value = "csrf-token-xyz"

            result = await tools.get_csrf_token({}, mock_admin_ctx)

        assert result["success"] is True
        assert result["data"]["csrf_token"] == "csrf-token-xyz"

    @pytest.mark.asyncio
    async def test_get_csrf_token_not_authenticated(self, tools):
        """Test when not authenticated."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "", "role": "admin"}

        result = await tools.get_csrf_token({}, ctx)

        assert result["success"] is False
        assert result["error"] == "AUTH_REQUIRED"

    @pytest.mark.asyncio
    async def test_get_csrf_token_not_admin(self, tools):
        """Test when not admin."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "role": "user"}

        result = await tools.get_csrf_token({}, ctx)

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_get_csrf_token_exception(self, tools, mock_admin_ctx):
        """Test handling exceptions."""
        with patch('tools.retention.tools.csrf_service') as mock_csrf:
            mock_csrf.generate_token.side_effect = Exception("Token generation failed")

            result = await tools.get_csrf_token({}, mock_admin_ctx)

        assert result["success"] is False
        assert result["error"] == "TOKEN_ERROR"


class TestPreviewRetentionCleanup:
    """Tests for preview_retention_cleanup tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock retention service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create RetentionTools instance."""
        with patch('tools.retention.tools.logger'):
            return RetentionTools(mock_service)

    @pytest.fixture
    def mock_admin_ctx(self):
        """Create admin context."""
        ctx = MagicMock()
        ctx.meta = {
            "user_id": "admin-123",
            "session_id": "sess-456",
            "role": "admin",
            "token": "tok-789"
        }
        return ctx

    @pytest.fixture
    def sample_preview(self):
        """Create sample preview result."""
        preview = MagicMock()
        preview.retention_type = RetentionType.AUDIT_LOGS
        preview.affected_records = 100
        preview.oldest_record_date = "2024-01-01T00:00:00Z"
        preview.newest_record_date = "2024-01-10T00:00:00Z"
        preview.estimated_space_freed_mb = 5.5
        preview.cutoff_date = "2024-01-15T00:00:00Z"
        return preview

    @pytest.mark.asyncio
    async def test_preview_cleanup_success(
        self, tools, mock_service, mock_admin_ctx, sample_preview
    ):
        """Test successfully previewing cleanup."""
        mock_service.preview_cleanup = AsyncMock(return_value=sample_preview)

        result = await tools.preview_retention_cleanup(
            {"retention_type": "audit_logs"}, mock_admin_ctx
        )

        assert result["success"] is True
        assert result["data"]["affected_records"] == 100
        assert result["data"]["estimated_space_freed_mb"] == 5.5

    @pytest.mark.asyncio
    async def test_preview_cleanup_not_authenticated(self, tools):
        """Test when not authenticated."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "", "role": "admin"}

        result = await tools.preview_retention_cleanup({}, ctx)

        assert result["success"] is False
        assert result["error"] == "AUTH_REQUIRED"

    @pytest.mark.asyncio
    async def test_preview_cleanup_not_admin(self, tools):
        """Test when not admin."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "role": "user"}

        result = await tools.preview_retention_cleanup({}, ctx)

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_preview_cleanup_invalid_type(self, tools, mock_admin_ctx):
        """Test with invalid retention type."""
        result = await tools.preview_retention_cleanup(
            {"retention_type": "invalid"}, mock_admin_ctx
        )

        assert result["success"] is False
        assert result["error"] == "INVALID_TYPE"

    @pytest.mark.asyncio
    async def test_preview_cleanup_default_type(
        self, tools, mock_service, mock_admin_ctx, sample_preview
    ):
        """Test default retention type is logs."""
        # Change sample_preview to match default "logs" which isn't a valid enum
        # so we need to test with a valid type
        mock_service.preview_cleanup = AsyncMock(return_value=sample_preview)

        # Default is "logs" but it's not a valid RetentionType
        result = await tools.preview_retention_cleanup({}, mock_admin_ctx)

        assert result["success"] is False
        assert result["error"] == "INVALID_TYPE"

    @pytest.mark.asyncio
    async def test_preview_cleanup_returns_none(
        self, tools, mock_service, mock_admin_ctx
    ):
        """Test when preview returns None."""
        mock_service.preview_cleanup = AsyncMock(return_value=None)

        result = await tools.preview_retention_cleanup(
            {"retention_type": "audit_logs"}, mock_admin_ctx
        )

        assert result["success"] is False
        assert result["error"] == "PREVIEW_ERROR"

    @pytest.mark.asyncio
    async def test_preview_cleanup_exception(self, tools, mock_service, mock_admin_ctx):
        """Test handling exceptions."""
        mock_service.preview_cleanup = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await tools.preview_retention_cleanup(
            {"retention_type": "audit_logs"}, mock_admin_ctx
        )

        assert result["success"] is False
        assert result["error"] == "PREVIEW_ERROR"


class TestPerformRetentionCleanup:
    """Tests for perform_retention_cleanup tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock retention service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create RetentionTools instance."""
        with patch('tools.retention.tools.logger'):
            return RetentionTools(mock_service)

    @pytest.fixture
    def mock_admin_ctx(self):
        """Create admin context."""
        ctx = MagicMock()
        ctx.meta = {
            "user_id": "admin-123",
            "session_id": "sess-456",
            "role": "admin",
            "token": "tok-789"
        }
        return ctx

    @pytest.fixture
    def sample_result(self):
        """Create sample cleanup result."""
        result = MagicMock()
        result.success = True
        result.operation_id = "op-123"
        result.retention_type = RetentionType.AUDIT_LOGS
        result.records_affected = 50
        result.space_freed_mb = 2.5
        result.duration_seconds = 1.5
        result.start_time = "2024-01-15T10:00:00Z"
        result.end_time = "2024-01-15T10:00:01Z"
        result.error_message = None
        return result

    @pytest.mark.asyncio
    async def test_cleanup_success(
        self, tools, mock_service, mock_admin_ctx, sample_result
    ):
        """Test successful cleanup."""
        mock_service.perform_cleanup = AsyncMock(return_value=sample_result)

        with patch('tools.retention.tools.csrf_service') as mock_csrf:
            mock_csrf.validate_token.return_value = (True, None)

            result = await tools.perform_retention_cleanup({
                "retention_type": "audit_logs",
                "csrf_token": "valid-token-12345678901234567890"
            }, mock_admin_ctx)

        assert result["success"] is True
        assert result["data"]["records_affected"] == 50
        assert result["data"]["space_freed_mb"] == 2.5

    @pytest.mark.asyncio
    async def test_cleanup_not_authenticated(self, tools):
        """Test when not authenticated."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "", "role": "admin"}

        result = await tools.perform_retention_cleanup({}, ctx)

        assert result["success"] is False
        assert result["error"] == "AUTH_REQUIRED"

    @pytest.mark.asyncio
    async def test_cleanup_not_admin(self, tools):
        """Test when not admin."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "role": "user"}

        result = await tools.perform_retention_cleanup({}, ctx)

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_cleanup_missing_csrf(self, tools, mock_admin_ctx):
        """Test without CSRF token."""
        result = await tools.perform_retention_cleanup(
            {"retention_type": "audit_logs"}, mock_admin_ctx
        )

        assert result["success"] is False
        assert result["error"] == "CSRF_REQUIRED"

    @pytest.mark.asyncio
    async def test_cleanup_invalid_csrf(self, tools, mock_admin_ctx):
        """Test with invalid CSRF token."""
        with patch('tools.retention.tools.csrf_service') as mock_csrf:
            mock_csrf.validate_token.return_value = (False, "Token expired")

            result = await tools.perform_retention_cleanup({
                "retention_type": "audit_logs",
                "csrf_token": "invalid-token-1234567890123456"
            }, mock_admin_ctx)

        assert result["success"] is False
        assert result["error"] == "CSRF_INVALID"

    @pytest.mark.asyncio
    async def test_cleanup_invalid_type(self, tools, mock_admin_ctx):
        """Test with invalid retention type."""
        with patch('tools.retention.tools.csrf_service') as mock_csrf:
            mock_csrf.validate_token.return_value = (True, None)

            result = await tools.perform_retention_cleanup({
                "retention_type": "invalid",
                "csrf_token": "valid-token-12345678901234567890"
            }, mock_admin_ctx)

        assert result["success"] is False
        assert result["error"] == "INVALID_TYPE"

    @pytest.mark.asyncio
    async def test_cleanup_returns_none(self, tools, mock_service, mock_admin_ctx):
        """Test when cleanup returns None."""
        mock_service.perform_cleanup = AsyncMock(return_value=None)

        with patch('tools.retention.tools.csrf_service') as mock_csrf:
            mock_csrf.validate_token.return_value = (True, None)

            result = await tools.perform_retention_cleanup({
                "retention_type": "audit_logs",
                "csrf_token": "valid-token-12345678901234567890"
            }, mock_admin_ctx)

        assert result["success"] is False
        assert result["error"] == "CLEANUP_ERROR"

    @pytest.mark.asyncio
    async def test_cleanup_result_failure(self, tools, mock_service, mock_admin_ctx):
        """Test when cleanup result indicates failure."""
        failed_result = MagicMock()
        failed_result.success = False
        failed_result.error_message = "Cleanup aborted"
        mock_service.perform_cleanup = AsyncMock(return_value=failed_result)

        with patch('tools.retention.tools.csrf_service') as mock_csrf:
            mock_csrf.validate_token.return_value = (True, None)

            result = await tools.perform_retention_cleanup({
                "retention_type": "audit_logs",
                "csrf_token": "valid-token-12345678901234567890"
            }, mock_admin_ctx)

        assert result["success"] is False
        assert "Cleanup aborted" in result["message"]

    @pytest.mark.asyncio
    async def test_cleanup_exception(self, tools, mock_service, mock_admin_ctx):
        """Test handling exceptions."""
        mock_service.perform_cleanup = AsyncMock(
            side_effect=Exception("Database error")
        )

        with patch('tools.retention.tools.csrf_service') as mock_csrf:
            mock_csrf.validate_token.return_value = (True, None)

            result = await tools.perform_retention_cleanup({
                "retention_type": "audit_logs",
                "csrf_token": "valid-token-12345678901234567890"
            }, mock_admin_ctx)

        assert result["success"] is False
        assert result["error"] == "CLEANUP_ERROR"


class TestGetRetentionSettings:
    """Tests for get_retention_settings tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock retention service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create RetentionTools instance."""
        with patch('tools.retention.tools.logger'):
            return RetentionTools(mock_service)

    @pytest.fixture
    def mock_admin_ctx(self):
        """Create admin context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "admin-123", "role": "admin"}
        return ctx

    @pytest.mark.asyncio
    async def test_get_settings_success(self, tools, mock_service, mock_admin_ctx):
        """Test successfully getting settings."""
        settings = MagicMock()
        settings.model_dump.return_value = {
            "log_retention": 30,
            "data_retention": 90
        }
        mock_service.get_retention_settings = AsyncMock(return_value=settings)

        result = await tools.get_retention_settings({}, mock_admin_ctx)

        assert result["success"] is True
        assert result["data"]["log_retention"] == 30

    @pytest.mark.asyncio
    async def test_get_settings_not_authenticated(self, tools):
        """Test when not authenticated."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "", "role": "admin"}

        result = await tools.get_retention_settings({}, ctx)

        assert result["success"] is False
        assert result["error"] == "AUTH_REQUIRED"

    @pytest.mark.asyncio
    async def test_get_settings_not_admin(self, tools):
        """Test when not admin."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "role": "user"}

        result = await tools.get_retention_settings({}, ctx)

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_get_settings_not_found(self, tools, mock_service, mock_admin_ctx):
        """Test when settings not found."""
        mock_service.get_retention_settings = AsyncMock(return_value=None)

        result = await tools.get_retention_settings({}, mock_admin_ctx)

        assert result["success"] is False
        assert result["error"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_settings_exception(self, tools, mock_service, mock_admin_ctx):
        """Test handling exceptions."""
        mock_service.get_retention_settings = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await tools.get_retention_settings({}, mock_admin_ctx)

        assert result["success"] is False
        assert result["error"] == "GET_ERROR"


class TestUpdateRetentionSettings:
    """Tests for update_retention_settings tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock retention service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create RetentionTools instance."""
        with patch('tools.retention.tools.logger'):
            return RetentionTools(mock_service)

    @pytest.fixture
    def mock_admin_ctx(self):
        """Create admin context."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "admin-123", "role": "admin"}
        return ctx

    @pytest.mark.asyncio
    async def test_update_settings_success(self, tools, mock_service, mock_admin_ctx):
        """Test successfully updating settings."""
        updated_settings = MagicMock()
        updated_settings.model_dump.return_value = {
            "log_retention": 60,
            "data_retention": 180
        }
        mock_service.update_retention_settings = AsyncMock(return_value=True)
        mock_service.get_retention_settings = AsyncMock(return_value=updated_settings)

        result = await tools.update_retention_settings({
            "log_retention": 60,
            "data_retention": 180
        }, mock_admin_ctx)

        assert result["success"] is True
        assert result["data"]["log_retention"] == 60

    @pytest.mark.asyncio
    async def test_update_settings_not_authenticated(self, tools):
        """Test when not authenticated."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "", "role": "admin"}

        result = await tools.update_retention_settings({}, ctx)

        assert result["success"] is False
        assert result["error"] == "AUTH_REQUIRED"

    @pytest.mark.asyncio
    async def test_update_settings_not_admin(self, tools):
        """Test when not admin."""
        ctx = MagicMock()
        ctx.meta = {"user_id": "user-123", "role": "user"}

        result = await tools.update_retention_settings({}, ctx)

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_update_settings_failed(self, tools, mock_service, mock_admin_ctx):
        """Test when update fails."""
        mock_service.update_retention_settings = AsyncMock(return_value=False)

        result = await tools.update_retention_settings({
            "log_retention": 60
        }, mock_admin_ctx)

        assert result["success"] is False
        assert result["error"] == "UPDATE_ERROR"

    @pytest.mark.asyncio
    async def test_update_settings_returns_fallback(
        self, tools, mock_service, mock_admin_ctx
    ):
        """Test fallback to input settings when get returns None."""
        mock_service.update_retention_settings = AsyncMock(return_value=True)
        mock_service.get_retention_settings = AsyncMock(return_value=None)

        result = await tools.update_retention_settings({
            "log_retention": 45
        }, mock_admin_ctx)

        assert result["success"] is True
        # Should use input settings as fallback
        assert result["data"]["log_retention"] == 45

    @pytest.mark.asyncio
    async def test_update_settings_exception(self, tools, mock_service, mock_admin_ctx):
        """Test handling exceptions."""
        mock_service.update_retention_settings = AsyncMock(
            side_effect=Exception("Validation error")
        )

        result = await tools.update_retention_settings({
            "log_retention": 60
        }, mock_admin_ctx)

        assert result["success"] is False
        assert result["error"] == "UPDATE_ERROR"

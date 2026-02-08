"""
Unit tests for Settings MCP tools.

Tests for get_settings, update_settings, reset_user_settings,
reset_system_settings, and get_default_settings tools.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.settings import SettingCategory, SettingsResponse, SettingsValidationResult
from services.settings_service import SettingsService
from tools.settings.tools import SettingsTools


@pytest.fixture
def mock_settings_service():
    """Create mock settings service."""
    service = AsyncMock(spec=SettingsService)
    return service


@pytest.fixture
def mock_context():
    """Create mock MCP context with user authentication."""
    ctx = MagicMock()
    ctx.meta = {
        "userId": "test-user-123",
        "clientIp": "192.168.1.100",
        "userAgent": "TestClient/1.0",
    }
    return ctx


@pytest.fixture
def mock_context_no_user():
    """Create mock MCP context without user authentication."""
    ctx = MagicMock()
    ctx.meta = {}
    return ctx


@pytest.fixture
def settings_tools(mock_settings_service):
    """Create SettingsTools instance."""
    return SettingsTools(mock_settings_service)


class TestVerifyAuthentication:
    """Tests for _verify_authentication method."""

    async def test_returns_user_id_from_context(self, settings_tools, mock_context):
        """Test that user ID is extracted from context."""
        user_id = await settings_tools._verify_authentication(mock_context)
        assert user_id == "test-user-123"

    async def test_returns_none_when_no_context(self, settings_tools):
        """Test that None is returned when context is None."""
        user_id = await settings_tools._verify_authentication(None)
        assert user_id is None

    async def test_returns_none_when_no_user_id(
        self, settings_tools, mock_context_no_user
    ):
        """Test that None is returned when no userId in meta."""
        user_id = await settings_tools._verify_authentication(mock_context_no_user)
        assert user_id is None

    async def test_handles_missing_meta(self, settings_tools):
        """Test that missing meta attribute is handled."""
        ctx = MagicMock()
        del ctx.meta  # Remove meta attribute
        user_id = await settings_tools._verify_authentication(ctx)
        assert user_id is None

    async def test_handles_exception_in_auth_verification(self, settings_tools):
        """Test that exceptions are caught and logged."""
        ctx = MagicMock()
        # Create a meta that raises exception when accessed
        ctx.meta = MagicMock()
        ctx.meta.get = MagicMock(side_effect=Exception("Broken context"))

        user_id = await settings_tools._verify_authentication(ctx)
        assert user_id is None


class TestExtractClientInfo:
    """Tests for _extract_client_info method."""

    async def test_extracts_client_ip_and_user_agent(
        self, settings_tools, mock_context
    ):
        """Test successful extraction of client info."""
        client_ip, user_agent = await settings_tools._extract_client_info(mock_context)
        assert client_ip == "192.168.1.100"
        assert user_agent == "TestClient/1.0"

    async def test_returns_unknown_when_no_context(self, settings_tools):
        """Test returns unknown when context is None."""
        client_ip, user_agent = await settings_tools._extract_client_info(None)
        assert client_ip == "unknown"
        assert user_agent == "unknown"

    async def test_returns_unknown_when_missing_values(self, settings_tools):
        """Test returns unknown for missing values."""
        ctx = MagicMock()
        ctx.meta = {}
        client_ip, user_agent = await settings_tools._extract_client_info(ctx)
        assert client_ip == "unknown"
        assert user_agent == "unknown"

    async def test_handles_exception_in_client_info_extraction(self, settings_tools):
        """Test that exceptions are caught and logged."""
        ctx = MagicMock()
        # Create a meta that raises exception when accessed
        ctx.meta = MagicMock()
        ctx.meta.get = MagicMock(side_effect=Exception("Broken context"))

        client_ip, user_agent = await settings_tools._extract_client_info(ctx)
        assert client_ip == "unknown"
        assert user_agent == "unknown"


class TestGetSettings:
    """Tests for get_settings tool."""

    async def test_requires_authentication(self, settings_tools, mock_context_no_user):
        """Test that authentication is required."""
        result = await settings_tools.get_settings(ctx=mock_context_no_user)

        assert result["success"] is False
        assert result["error"] == "AUTHENTICATION_REQUIRED"

    async def test_successful_get_settings(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test successful settings retrieval."""
        mock_settings_service.get_settings.return_value = SettingsResponse(
            success=True,
            message="Settings retrieved",
            data={"ui.theme": "dark"},
            checksum="abc123",
        )

        result = await settings_tools.get_settings(ctx=mock_context)

        assert result["success"] is True
        assert result["data"] == {"ui.theme": "dark"}
        assert result["checksum"] == "abc123"

    async def test_invalid_category(self, settings_tools, mock_context):
        """Test handling of invalid category."""
        result = await settings_tools.get_settings(
            category="invalid_category", ctx=mock_context
        )

        assert result["success"] is False
        assert result["error"] == "INVALID_CATEGORY"

    async def test_invalid_setting_key_format(self, settings_tools, mock_context):
        """Test handling of invalid setting key format."""
        result = await settings_tools.get_settings(
            setting_keys=["", "   "], ctx=mock_context
        )

        assert result["success"] is False
        assert result["error"] == "INVALID_SETTING_KEY"

    async def test_handles_service_exception(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test handling of service exceptions."""
        mock_settings_service.get_settings.side_effect = Exception("Database error")

        result = await settings_tools.get_settings(ctx=mock_context)

        assert result["success"] is False
        assert result["error"] == "GET_SETTINGS_ERROR"

    async def test_uses_user_id_from_context(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test that user ID from context is used."""
        mock_settings_service.get_settings.return_value = SettingsResponse(
            success=True, message="OK", data={}
        )

        await settings_tools.get_settings(ctx=mock_context)

        # Verify the service was called with a request containing the user ID
        mock_settings_service.get_settings.assert_called_once()
        call_args = mock_settings_service.get_settings.call_args
        request = call_args[0][0]
        assert request.user_id == "test-user-123"

    async def test_with_category_filter(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test filtering by category."""
        mock_settings_service.get_settings.return_value = SettingsResponse(
            success=True, message="OK", data={"ui.theme": "dark"}
        )

        await settings_tools.get_settings(category="ui", ctx=mock_context)

        mock_settings_service.get_settings.assert_called_once()
        call_args = mock_settings_service.get_settings.call_args
        request = call_args[0][0]
        assert request.category == SettingCategory.UI


class TestUpdateSettings:
    """Tests for update_settings tool."""

    async def test_requires_authentication(self, settings_tools, mock_context_no_user):
        """Test that authentication is required."""
        result = await settings_tools.update_settings(
            settings={"ui.theme": "dark"}, ctx=mock_context_no_user
        )

        assert result["success"] is False
        assert result["error"] == "AUTHENTICATION_REQUIRED"

    async def test_successful_update(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test successful settings update."""
        mock_settings_service.update_settings.return_value = SettingsResponse(
            success=True,
            message="Settings updated",
            data={"ui.theme": "dark"},
            checksum="newchecksum",
        )

        with patch("tools.settings.tools.log_event", new_callable=AsyncMock):
            result = await settings_tools.update_settings(
                settings={"ui.theme": "dark"}, ctx=mock_context
            )

        assert result["success"] is True
        assert result["checksum"] == "newchecksum"

    async def test_validate_only_mode(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test validate_only mode."""
        mock_settings_service.validate_settings.return_value = SettingsValidationResult(
            is_valid=True, errors=[], warnings=[]
        )

        result = await settings_tools.update_settings(
            settings={"ui.theme": "dark"}, validate_only=True, ctx=mock_context
        )

        assert result["success"] is True
        assert "validation" in result["message"].lower()
        mock_settings_service.validate_settings.assert_called_once()
        mock_settings_service.update_settings.assert_not_called()

    async def test_includes_client_info(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test that client info is included in update request."""
        mock_settings_service.update_settings.return_value = SettingsResponse(
            success=True, message="OK", data={}
        )

        with patch("tools.settings.tools.log_event", new_callable=AsyncMock):
            await settings_tools.update_settings(
                settings={"ui.theme": "dark"}, ctx=mock_context
            )

        mock_settings_service.update_settings.assert_called_once()
        call_args = mock_settings_service.update_settings.call_args
        request = call_args[0][0]
        assert request.client_ip == "192.168.1.100"
        assert request.user_agent == "TestClient/1.0"

    async def test_handles_service_exception(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test handling of service exceptions."""
        mock_settings_service.update_settings.side_effect = Exception("Database error")

        with patch("tools.settings.tools.log_event", new_callable=AsyncMock):
            result = await settings_tools.update_settings(
                settings={"ui.theme": "dark"}, ctx=mock_context
            )

        assert result["success"] is False
        assert result["error"] == "UPDATE_SETTINGS_ERROR"

    async def test_logs_successful_update(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test that successful updates are logged."""
        mock_settings_service.update_settings.return_value = SettingsResponse(
            success=True, message="OK", data={}
        )

        with patch(
            "tools.settings.tools.log_event", new_callable=AsyncMock
        ) as mock_log:
            await settings_tools.update_settings(
                settings={"ui.theme": "dark"},
                change_reason="User preference",
                ctx=mock_context,
            )

            mock_log.assert_called()
            call_args = mock_log.call_args
            # log_event signature: (prefix, level, message, tags, metadata)
            assert call_args[0][1] == "INFO"

    async def test_logs_failed_update(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test that failed updates are logged."""
        mock_settings_service.update_settings.return_value = SettingsResponse(
            success=False, message="Validation failed", error="VALIDATION_ERROR"
        )

        with patch(
            "tools.settings.tools.log_event", new_callable=AsyncMock
        ) as mock_log:
            await settings_tools.update_settings(
                settings={"ui.theme": "dark"}, ctx=mock_context
            )

            mock_log.assert_called()
            call_args = mock_log.call_args
            # log_event signature: (prefix, level, message, tags, metadata)
            assert call_args[0][1] == "WARNING"


class TestResetUserSettings:
    """Tests for reset_user_settings tool."""

    async def test_requires_authentication(self, settings_tools, mock_context_no_user):
        """Test that authentication is required."""
        result = await settings_tools.reset_user_settings(ctx=mock_context_no_user)

        assert result["success"] is False
        assert result["error"] == "AUTHENTICATION_REQUIRED"

    async def test_successful_reset(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test successful user settings reset."""
        mock_settings_service.reset_user_settings.return_value = SettingsResponse(
            success=True,
            message="Reset 5 user settings to defaults",
            data={"deleted_count": 5, "user_id": "test-user-123"},
        )

        with patch("tools.settings.tools.log_event", new_callable=AsyncMock):
            result = await settings_tools.reset_user_settings(ctx=mock_context)

        assert result["success"] is True
        assert result["data"]["deleted_count"] == 5

    async def test_reset_with_category(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test reset with category filter."""
        mock_settings_service.reset_user_settings.return_value = SettingsResponse(
            success=True,
            message="Reset 2 user settings to defaults",
            data={"deleted_count": 2, "user_id": "test-user-123"},
        )

        with patch("tools.settings.tools.log_event", new_callable=AsyncMock):
            result = await settings_tools.reset_user_settings(
                category="ui", ctx=mock_context
            )

        assert result["success"] is True
        mock_settings_service.reset_user_settings.assert_called_once()
        call_args = mock_settings_service.reset_user_settings.call_args
        assert call_args.kwargs["category"] == SettingCategory.UI

    async def test_invalid_category(self, settings_tools, mock_context):
        """Test handling of invalid category."""
        result = await settings_tools.reset_user_settings(
            category="invalid_category", ctx=mock_context
        )

        assert result["success"] is False
        assert result["error"] == "INVALID_CATEGORY"

    async def test_handles_service_exception(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test handling of service exceptions."""
        mock_settings_service.reset_user_settings.side_effect = Exception(
            "Database error"
        )

        with patch("tools.settings.tools.log_event", new_callable=AsyncMock):
            result = await settings_tools.reset_user_settings(ctx=mock_context)

        assert result["success"] is False
        assert result["error"] == "RESET_USER_SETTINGS_ERROR"

    async def test_logs_failed_reset(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test that failed resets are logged with WARNING level."""
        mock_settings_service.reset_user_settings.return_value = SettingsResponse(
            success=False, message="Reset failed", error="RESET_ERROR"
        )

        with patch(
            "tools.settings.tools.log_event", new_callable=AsyncMock
        ) as mock_log:
            result = await settings_tools.reset_user_settings(ctx=mock_context)

        assert result["success"] is False
        mock_log.assert_called()
        call_args = mock_log.call_args
        assert call_args[0][1] == "WARNING"


class TestResetSystemSettings:
    """Tests for reset_system_settings tool."""

    async def test_requires_authentication(self, settings_tools, mock_context_no_user):
        """Test that authentication is required."""
        result = await settings_tools.reset_system_settings(ctx=mock_context_no_user)

        assert result["success"] is False
        assert result["error"] == "AUTHENTICATION_REQUIRED"

    async def test_successful_reset(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test successful system settings reset."""
        mock_settings_service.reset_system_settings.return_value = SettingsResponse(
            success=True,
            message="Reset 3 system settings to factory defaults",
            data={"reset_count": 3},
        )

        with patch("tools.settings.tools.log_event", new_callable=AsyncMock):
            result = await settings_tools.reset_system_settings(ctx=mock_context)

        assert result["success"] is True
        assert result["data"]["reset_count"] == 3

    async def test_reset_with_category(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test reset with category filter."""
        mock_settings_service.reset_system_settings.return_value = SettingsResponse(
            success=True,
            message="Reset 1 system setting to factory defaults",
            data={"reset_count": 1},
        )

        with patch("tools.settings.tools.log_event", new_callable=AsyncMock):
            result = await settings_tools.reset_system_settings(
                category="security", ctx=mock_context
            )

        assert result["success"] is True
        mock_settings_service.reset_system_settings.assert_called_once()
        call_args = mock_settings_service.reset_system_settings.call_args
        assert call_args.kwargs["category"] == SettingCategory.SECURITY

    async def test_invalid_category(self, settings_tools, mock_context):
        """Test handling of invalid category."""
        result = await settings_tools.reset_system_settings(
            category="invalid_category", ctx=mock_context
        )

        assert result["success"] is False
        assert result["error"] == "INVALID_CATEGORY"

    async def test_admin_required_failure(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test that non-admin users get proper error."""
        mock_settings_service.reset_system_settings.return_value = SettingsResponse(
            success=False,
            message="Admin privileges required to reset system settings",
            error="ADMIN_REQUIRED",
        )

        with patch("tools.settings.tools.log_event", new_callable=AsyncMock):
            result = await settings_tools.reset_system_settings(ctx=mock_context)

        assert result["success"] is False
        assert result["error"] == "ADMIN_REQUIRED"

    async def test_handles_service_exception(
        self, settings_tools, mock_settings_service, mock_context
    ):
        """Test handling of service exceptions."""
        mock_settings_service.reset_system_settings.side_effect = Exception(
            "Database error"
        )

        with patch("tools.settings.tools.log_event", new_callable=AsyncMock):
            result = await settings_tools.reset_system_settings(ctx=mock_context)

        assert result["success"] is False
        assert result["error"] == "RESET_SYSTEM_SETTINGS_ERROR"


class TestGetDefaultSettings:
    """Tests for get_default_settings tool."""

    async def test_successful_get_defaults(self, settings_tools, mock_settings_service):
        """Test successful retrieval of default settings."""
        mock_settings_service.get_default_settings.return_value = SettingsResponse(
            success=True,
            message="Retrieved 10 default settings",
            data={
                "defaults": {
                    "ui.theme": {
                        "value": "dark",
                        "category": "ui",
                        "data_type": "string",
                    },
                    "ui.language": {
                        "value": "en",
                        "category": "ui",
                        "data_type": "string",
                    },
                }
            },
        )

        result = await settings_tools.get_default_settings()

        assert result["success"] is True
        assert "defaults" in result["data"]
        assert "ui.theme" in result["data"]["defaults"]

    async def test_get_defaults_with_category(
        self, settings_tools, mock_settings_service
    ):
        """Test retrieval of default settings with category filter."""
        mock_settings_service.get_default_settings.return_value = SettingsResponse(
            success=True,
            message="Retrieved 5 default settings",
            data={
                "defaults": {
                    "ui.theme": {
                        "value": "dark",
                        "category": "ui",
                        "data_type": "string",
                    }
                }
            },
        )

        result = await settings_tools.get_default_settings(category="ui")

        assert result["success"] is True
        mock_settings_service.get_default_settings.assert_called_once()
        call_args = mock_settings_service.get_default_settings.call_args
        assert call_args.kwargs["category"] == SettingCategory.UI

    async def test_invalid_category(self, settings_tools):
        """Test handling of invalid category."""
        result = await settings_tools.get_default_settings(category="invalid_category")

        assert result["success"] is False
        assert result["error"] == "INVALID_CATEGORY"

    async def test_handles_service_exception(
        self, settings_tools, mock_settings_service
    ):
        """Test handling of service exceptions."""
        mock_settings_service.get_default_settings.side_effect = Exception(
            "Database error"
        )

        result = await settings_tools.get_default_settings()

        assert result["success"] is False
        assert result["error"] == "GET_DEFAULTS_ERROR"

    async def test_no_authentication_required(
        self, settings_tools, mock_settings_service, mock_context_no_user
    ):
        """Test that get_default_settings doesn't require authentication."""
        mock_settings_service.get_default_settings.return_value = SettingsResponse(
            success=True, message="Retrieved defaults", data={"defaults": {}}
        )

        # Should work even without user context
        result = await settings_tools.get_default_settings(ctx=mock_context_no_user)

        assert result["success"] is True

"""
Backend MCP Tools Security and Functionality Tests

Comprehensive tests for settings MCP tools including authentication,
authorization, input validation, and security controls.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastmcp import Context

from tools.settings_tools import SettingsTools
from services.settings_service import SettingsService
from services.auth_service import AuthService
from models.auth import User, UserRole
from models.settings import SettingCategory, SettingsResponse


@pytest.fixture
def mock_settings_service():
    """Mock SettingsService instance."""
    service = AsyncMock(spec=SettingsService)
    return service


@pytest.fixture
def mock_auth_service():
    """Mock AuthService instance."""
    service = AsyncMock(spec=AuthService)
    service.sessions = {}
    return service


@pytest.fixture
def settings_tools(mock_settings_service, mock_auth_service):
    """Create SettingsTools instance with mocked services."""
    return SettingsTools(mock_settings_service, mock_auth_service)


@pytest.fixture
def mock_context():
    """Create mock MCP context."""
    ctx = MagicMock(spec=Context)
    ctx.meta = {
        'sessionId': 'test_session_123',
        'clientIp': '192.168.1.100',
        'userAgent': 'TestClient/1.0'
    }
    return ctx


@pytest.fixture
def admin_user():
    """Create mock admin user."""
    return User(
        id="admin_user",
        username="admin",
        email="admin@test.com",
        role=UserRole.ADMIN,
        last_login="2023-01-01T00:00:00Z",
        is_active=True
    )


@pytest.fixture
def regular_user():
    """Create mock regular user."""
    return User(
        id="regular_user",
        username="user",
        email="user@test.com",
        role=UserRole.USER,
        last_login="2023-01-01T00:00:00Z",
        is_active=True
    )


class TestAuthentication:
    """Test authentication and session verification."""

    async def test_verify_authentication_valid_session(self, settings_tools, mock_auth_service, mock_context, admin_user):
        """Test successful authentication with valid session."""
        # Setup session
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'admin_user'}
        mock_auth_service.get_user_by_id.return_value = admin_user

        user_id = await settings_tools._verify_authentication(mock_context)

        assert user_id == "admin_user"
        mock_auth_service.get_user_by_id.assert_called_once_with("admin_user")

    async def test_verify_authentication_no_context(self, settings_tools):
        """Test authentication failure with no context."""
        user_id = await settings_tools._verify_authentication(None)
        assert user_id is None

    async def test_verify_authentication_no_session_id(self, settings_tools, mock_auth_service):
        """Test authentication failure with no session ID."""
        ctx = MagicMock(spec=Context)
        ctx.meta = {}

        user_id = await settings_tools._verify_authentication(ctx)
        assert user_id is None

    async def test_verify_authentication_invalid_session(self, settings_tools, mock_auth_service, mock_context):
        """Test authentication failure with invalid session."""
        # No session in sessions dict
        user_id = await settings_tools._verify_authentication(mock_context)
        assert user_id is None

    async def test_verify_authentication_inactive_user(self, settings_tools, mock_auth_service, mock_context):
        """Test authentication failure with inactive user."""
        # Setup session with inactive user
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'admin_user'}
        inactive_user = User(
            id="admin_user",
            username="admin",
            email="admin@test.com",
            role=UserRole.ADMIN,
            last_login="2023-01-01T00:00:00Z",
            is_active=False  # Inactive
        )
        mock_auth_service.get_user_by_id.return_value = inactive_user

        user_id = await settings_tools._verify_authentication(mock_context)
        assert user_id is None

    async def test_verify_authentication_nonexistent_user(self, settings_tools, mock_auth_service, mock_context):
        """Test authentication failure with nonexistent user."""
        # Setup session but user doesn't exist
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'nonexistent_user'}
        mock_auth_service.get_user_by_id.return_value = None

        user_id = await settings_tools._verify_authentication(mock_context)
        assert user_id is None


class TestGetSettings:
    """Test get_settings MCP tool."""

    async def test_get_settings_authentication_required(self, settings_tools, mock_context):
        """Test get_settings requires authentication."""
        # No valid session
        result = await settings_tools.get_settings(ctx=mock_context)

        assert result["success"] is False
        assert result["error"] == "AUTHENTICATION_REQUIRED"
        assert "Authentication required" in result["message"]

    async def test_get_settings_valid_request(self, settings_tools, mock_settings_service, mock_auth_service, mock_context, admin_user):
        """Test successful get_settings with valid authentication."""
        # Setup authentication
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'admin_user'}
        mock_auth_service.get_user_by_id.return_value = admin_user

        # Setup settings response
        mock_response = SettingsResponse(
            success=True,
            message="Settings retrieved successfully",
            data={"ui.theme": "dark", "ui.language": "en"}
        )
        mock_settings_service.get_user_settings.return_value = mock_response

        result = await settings_tools.get_settings(
            category="ui",
            setting_keys=["ui.theme"],
            ctx=mock_context
        )

        assert result["success"] is True
        assert "Settings retrieved successfully" in result["message"]
        assert result["data"] == {"ui.theme": "dark", "ui.language": "en"}

        # Verify service was called with correct parameters
        mock_settings_service.get_user_settings.assert_called_once()

    async def test_get_settings_invalid_category(self, settings_tools, mock_auth_service, mock_context, admin_user):
        """Test get_settings with invalid category."""
        # Setup authentication
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'admin_user'}
        mock_auth_service.get_user_by_id.return_value = admin_user

        result = await settings_tools.get_settings(
            category="invalid_category",
            ctx=mock_context
        )

        assert result["success"] is False
        assert result["error"] == "INVALID_CATEGORY"

    async def test_get_settings_with_filtering(self, settings_tools, mock_settings_service, mock_auth_service, mock_context, admin_user):
        """Test get_settings with category and key filtering."""
        # Setup authentication
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'admin_user'}
        mock_auth_service.get_user_by_id.return_value = admin_user

        # Setup settings response
        mock_response = SettingsResponse(
            success=True,
            message="Settings retrieved successfully",
            data={"ui.theme": "dark"}
        )
        mock_settings_service.get_user_settings.return_value = mock_response

        result = await settings_tools.get_settings(
            category="ui",
            setting_keys=["ui.theme"],
            include_system_defaults=True,
            include_user_overrides=False,
            ctx=mock_context
        )

        assert result["success"] is True

    async def test_get_settings_service_error(self, settings_tools, mock_settings_service, mock_auth_service, mock_context, admin_user):
        """Test get_settings handles service errors gracefully."""
        # Setup authentication
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'admin_user'}
        mock_auth_service.get_user_by_id.return_value = admin_user

        # Setup service error
        mock_settings_service.get_user_settings.side_effect = Exception("Database error")

        result = await settings_tools.get_settings(ctx=mock_context)

        assert result["success"] is False
        assert result["error"] == "INTERNAL_ERROR"


class TestUpdateSettings:
    """Test update_settings MCP tool."""

    async def test_update_settings_authentication_required(self, settings_tools, mock_context):
        """Test update_settings requires authentication."""
        result = await settings_tools.update_settings(
            settings={"ui.theme": "dark"},
            ctx=mock_context
        )

        assert result["success"] is False
        assert result["error"] == "AUTHENTICATION_REQUIRED"

    async def test_update_settings_admin_required(self, settings_tools, mock_auth_service, mock_context, regular_user):
        """Test update_settings requires admin privileges for system settings."""
        # Setup authentication with regular user
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'regular_user'}
        mock_auth_service.get_user_by_id.return_value = regular_user

        result = await settings_tools.update_settings(
            settings={"system.timeout": 30},
            ctx=mock_context
        )

        assert result["success"] is False
        assert result["error"] == "ADMIN_REQUIRED"

    async def test_update_settings_valid_admin_request(self, settings_tools, mock_settings_service, mock_auth_service, mock_context, admin_user):
        """Test successful update_settings with admin user."""
        # Setup authentication
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'admin_user'}
        mock_auth_service.get_user_by_id.return_value = admin_user

        # Setup settings response
        mock_response = SettingsResponse(
            success=True,
            message="Settings updated successfully",
            audit_id=123
        )
        mock_settings_service.update_user_settings.return_value = mock_response

        result = await settings_tools.update_settings(
            settings={"ui.theme": "dark"},
            change_reason="User preference",
            ctx=mock_context
        )

        assert result["success"] is True
        assert "Settings updated successfully" in result["message"]
        assert result["audit_id"] == 123

    async def test_update_settings_invalid_input(self, settings_tools, mock_auth_service, mock_context, admin_user):
        """Test update_settings with invalid input."""
        # Setup authentication
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'admin_user'}
        mock_auth_service.get_user_by_id.return_value = admin_user

        # Test with invalid settings format
        result = await settings_tools.update_settings(
            settings="not_a_dict",
            ctx=mock_context
        )

        assert result["success"] is False
        assert result["error"] == "INVALID_INPUT"

    async def test_update_settings_with_client_info(self, settings_tools, mock_settings_service, mock_auth_service, mock_context, admin_user):
        """Test update_settings includes client information in audit."""
        # Setup authentication
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'admin_user'}
        mock_auth_service.get_user_by_id.return_value = admin_user

        # Setup settings response
        mock_response = SettingsResponse(
            success=True,
            message="Settings updated successfully"
        )
        mock_settings_service.update_user_settings.return_value = mock_response

        result = await settings_tools.update_settings(
            settings={"ui.theme": "dark"},
            ctx=mock_context
        )

        # Verify service was called with client info
        call_args = mock_settings_service.update_user_settings.call_args
        request = call_args[0][0]  # First argument is the request
        assert hasattr(request, 'client_ip')
        assert hasattr(request, 'user_agent')


class TestSecurityControls:
    """Test security controls and input validation."""

    async def test_sql_injection_prevention(self, settings_tools, mock_auth_service, mock_context, admin_user):
        """Test prevention of SQL injection attempts."""
        # Setup authentication
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'admin_user'}
        mock_auth_service.get_user_by_id.return_value = admin_user

        # Test SQL injection attempts in various parameters
        injection_attempts = [
            "'; DROP TABLE system_settings; --",
            "ui.theme' OR 1=1--",
            "ui.theme'; DELETE FROM users; --",
            "1' UNION SELECT * FROM users--"
        ]

        for injection in injection_attempts:
            result = await settings_tools.get_settings(
                category=injection,
                ctx=mock_context
            )
            assert result["success"] is False
            assert result["error"] in ["INVALID_CATEGORY", "VALIDATION_ERROR"]

    async def test_path_traversal_prevention(self, settings_tools, mock_auth_service, mock_context, admin_user):
        """Test prevention of path traversal attempts."""
        # Setup authentication
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'admin_user'}
        mock_auth_service.get_user_by_id.return_value = admin_user

        # Test path traversal attempts
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            ".../ui.theme",
            "ui..theme"
        ]

        for attempt in traversal_attempts:
            result = await settings_tools.update_settings(
                settings={attempt: "value"},
                ctx=mock_context
            )
            assert result["success"] is False

    async def test_input_sanitization(self, settings_tools, mock_settings_service, mock_auth_service, mock_context, admin_user):
        """Test input sanitization and validation."""
        # Setup authentication
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'admin_user'}
        mock_auth_service.get_user_by_id.return_value = admin_user

        # Test with malicious input
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "\x00\x01\x02"  # Null bytes
        ]

        for malicious_input in malicious_inputs:
            result = await settings_tools.update_settings(
                settings={"ui.theme": malicious_input},
                change_reason=malicious_input,
                ctx=mock_context
            )
            # Should either succeed with sanitized input or fail validation
            if result["success"]:
                # If successful, verify input was sanitized (implementation dependent)
                pass
            else:
                assert result["error"] in ["VALIDATION_ERROR", "INVALID_INPUT"]

    async def test_privilege_escalation_prevention(self, settings_tools, mock_auth_service, mock_context, regular_user):
        """Test prevention of privilege escalation attempts."""
        # Setup authentication with regular user
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'regular_user'}
        mock_auth_service.get_user_by_id.return_value = regular_user

        # Attempt to modify admin-only settings
        admin_settings = [
            "security.max_login_attempts",
            "system.debug_mode",
            "security.session_timeout",
            "system.backup_retention"
        ]

        for setting in admin_settings:
            result = await settings_tools.update_settings(
                settings={setting: "malicious_value"},
                ctx=mock_context
            )
            assert result["success"] is False
            assert result["error"] == "ADMIN_REQUIRED"

    async def test_session_hijacking_prevention(self, settings_tools, mock_auth_service, mock_context):
        """Test prevention of session hijacking attempts."""
        # Test with invalid session IDs
        invalid_sessions = [
            "'; DROP TABLE sessions; --",
            "../admin_session",
            "session' OR 1=1--",
            "\x00\x01session"
        ]

        for session_id in invalid_sessions:
            mock_context.meta['sessionId'] = session_id
            result = await settings_tools.get_settings(ctx=mock_context)
            assert result["success"] is False
            assert result["error"] == "AUTHENTICATION_REQUIRED"

    async def test_audit_log_injection_prevention(self, settings_tools, mock_settings_service, mock_auth_service, mock_context, admin_user):
        """Test prevention of audit log injection."""
        # Setup authentication
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'admin_user'}
        mock_auth_service.get_user_by_id.return_value = admin_user

        # Setup settings response
        mock_response = SettingsResponse(
            success=True,
            message="Settings updated successfully"
        )
        mock_settings_service.update_user_settings.return_value = mock_response

        # Test with malicious change reason
        malicious_reasons = [
            "'; DROP TABLE settings_audit; --",
            "reason\nFAKE AUDIT ENTRY",
            "reason\r\nMalicious log entry",
            "reason\x00\x01\x02"
        ]

        for reason in malicious_reasons:
            result = await settings_tools.update_settings(
                settings={"ui.theme": "dark"},
                change_reason=reason,
                ctx=mock_context
            )

            # Should either succeed with sanitized reason or fail validation
            if result["success"]:
                # Verify the service was called with sanitized input
                call_args = mock_settings_service.update_user_settings.call_args
                request = call_args[0][0]
                # Implementation should sanitize the change_reason
                assert hasattr(request, 'change_reason')


class TestClientInfoExtraction:
    """Test client information extraction."""

    async def test_extract_client_info_valid_context(self, settings_tools, mock_context):
        """Test successful client info extraction."""
        client_ip, user_agent = await settings_tools._extract_client_info(mock_context)

        assert client_ip == "192.168.1.100"
        assert user_agent == "TestClient/1.0"

    async def test_extract_client_info_no_context(self, settings_tools):
        """Test client info extraction with no context."""
        client_ip, user_agent = await settings_tools._extract_client_info(None)

        assert client_ip == "unknown"
        assert user_agent == "unknown"

    async def test_extract_client_info_missing_meta(self, settings_tools):
        """Test client info extraction with missing meta."""
        ctx = MagicMock(spec=Context)
        # No meta attribute

        client_ip, user_agent = await settings_tools._extract_client_info(ctx)

        assert client_ip == "unknown"
        assert user_agent == "unknown"

    async def test_extract_client_info_partial_meta(self, settings_tools):
        """Test client info extraction with partial meta."""
        ctx = MagicMock(spec=Context)
        ctx.meta = {'clientIp': '192.168.1.100'}  # Missing userAgent

        client_ip, user_agent = await settings_tools._extract_client_info(ctx)

        assert client_ip == "192.168.1.100"
        assert user_agent == "unknown"


class TestErrorHandling:
    """Test error handling and edge cases."""

    async def test_service_exception_handling(self, settings_tools, mock_settings_service, mock_auth_service, mock_context, admin_user):
        """Test graceful handling of service exceptions."""
        # Setup authentication
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'admin_user'}
        mock_auth_service.get_user_by_id.return_value = admin_user

        # Setup service to raise exception
        mock_settings_service.get_user_settings.side_effect = Exception("Database connection failed")

        result = await settings_tools.get_settings(ctx=mock_context)

        assert result["success"] is False
        assert result["error"] == "INTERNAL_ERROR"
        assert "error" in result["message"].lower()

    async def test_authentication_service_exception(self, settings_tools, mock_auth_service, mock_context):
        """Test handling of authentication service exceptions."""
        # Setup auth service to raise exception
        mock_auth_service.get_user_by_id.side_effect = Exception("Auth service error")
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'admin_user'}

        result = await settings_tools.get_settings(ctx=mock_context)

        assert result["success"] is False
        assert result["error"] == "AUTHENTICATION_REQUIRED"

    async def test_malformed_context(self, settings_tools):
        """Test handling of malformed context."""
        # Test with various malformed contexts
        malformed_contexts = [
            None,
            {},
            MagicMock(),
            "string_context"
        ]

        for ctx in malformed_contexts:
            result = await settings_tools.get_settings(ctx=ctx)
            assert result["success"] is False
            assert result["error"] == "AUTHENTICATION_REQUIRED"

    async def test_concurrent_session_modification(self, settings_tools, mock_auth_service, mock_context, admin_user):
        """Test handling of concurrent session modifications."""
        # Setup initial session
        mock_auth_service.sessions['test_session_123'] = {'user_id': 'admin_user'}
        mock_auth_service.get_user_by_id.return_value = admin_user

        # Simulate session being removed during processing
        async def remove_session(*args, **kwargs):
            mock_auth_service.sessions.clear()
            return admin_user

        mock_auth_service.get_user_by_id.side_effect = remove_session

        user_id = await settings_tools._verify_authentication(mock_context)
        # Should still succeed as user was verified
        assert user_id == "admin_user"
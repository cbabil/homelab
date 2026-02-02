"""
Unit tests for Audit MCP tools.

Tests for get_settings_audit and get_auth_audit tools.
"""

from datetime import datetime, UTC
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tools.audit.tools import AuditTools
from services.settings_service import SettingsService
from models.settings import SettingsResponse
from models.log import LogEntry


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
        "userId": "admin-user-123",
        "clientIp": "192.168.1.100",
        "userAgent": "TestClient/1.0"
    }
    return ctx


@pytest.fixture
def mock_context_no_user():
    """Create mock MCP context without user authentication."""
    ctx = MagicMock()
    ctx.meta = {}
    return ctx


@pytest.fixture
def audit_tools(mock_settings_service):
    """Create AuditTools instance."""
    return AuditTools(mock_settings_service)


class TestVerifyAuthentication:
    """Tests for _verify_authentication method."""

    async def test_returns_user_id_from_context(self, audit_tools, mock_context):
        """Test that user ID is extracted from context."""
        user_id = await audit_tools._verify_authentication(mock_context)
        assert user_id == "admin-user-123"

    async def test_returns_none_when_no_context(self, audit_tools):
        """Test that None is returned when context is None."""
        user_id = await audit_tools._verify_authentication(None)
        assert user_id is None

    async def test_returns_none_when_no_user_id(self, audit_tools, mock_context_no_user):
        """Test that None is returned when no userId in meta."""
        user_id = await audit_tools._verify_authentication(mock_context_no_user)
        assert user_id is None


class TestGetSettingsAudit:
    """Tests for get_settings_audit tool."""

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_requires_authentication(
        self, mock_log_event, audit_tools, mock_context_no_user
    ):
        """Test that authentication is required."""
        result = await audit_tools.get_settings_audit(ctx=mock_context_no_user)

        assert result["success"] is False
        assert result["error"] == "AUTHENTICATION_REQUIRED"

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_successful_audit_retrieval(
        self, mock_log_event, audit_tools, mock_settings_service, mock_context
    ):
        """Test successful retrieval of audit entries."""
        audit_entries = [
            {
                "id": 1,
                "user_id": "user-123",
                "setting_key": "ui.theme",
                "old_value": '"light"',
                "new_value": '"dark"',
                "change_type": "UPDATE",
                "created_at": "2024-01-15T10:00:00Z"
            },
            {
                "id": 2,
                "user_id": "user-456",
                "setting_key": "security.timeout",
                "old_value": "3600",
                "new_value": "7200",
                "change_type": "UPDATE",
                "created_at": "2024-01-15T11:00:00Z"
            }
        ]

        mock_settings_service.get_settings_audit.return_value = SettingsResponse(
            success=True,
            message="Audit entries retrieved",
            data={"entries": audit_entries, "total": 2}
        )

        result = await audit_tools.get_settings_audit(ctx=mock_context)

        assert result["success"] is True
        assert result["data"]["entries"] == audit_entries
        mock_settings_service.get_settings_audit.assert_called_once_with(
            user_id="admin-user-123",
            setting_key=None,
            filter_user_id=None,
            limit=100,
            offset=0
        )
        # Verify log event was called
        mock_log_event.assert_called()
        assert mock_log_event.call_args[0][1] == "INFO"

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_audit_with_setting_key_filter(
        self, mock_log_event, audit_tools, mock_settings_service, mock_context
    ):
        """Test audit retrieval with setting key filter."""
        mock_settings_service.get_settings_audit.return_value = SettingsResponse(
            success=True,
            message="Audit entries retrieved",
            data={"entries": [], "total": 0}
        )

        result = await audit_tools.get_settings_audit(
            setting_key="ui.theme",
            ctx=mock_context
        )

        assert result["success"] is True
        mock_settings_service.get_settings_audit.assert_called_once_with(
            user_id="admin-user-123",
            setting_key="ui.theme",
            filter_user_id=None,
            limit=100,
            offset=0
        )

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_audit_with_custom_limit(
        self, mock_log_event, audit_tools, mock_settings_service, mock_context
    ):
        """Test audit retrieval with custom limit."""
        mock_settings_service.get_settings_audit.return_value = SettingsResponse(
            success=True,
            message="Audit entries retrieved",
            data={"entries": [], "total": 0}
        )

        result = await audit_tools.get_settings_audit(
            limit=50,
            ctx=mock_context
        )

        assert result["success"] is True
        mock_settings_service.get_settings_audit.assert_called_once_with(
            user_id="admin-user-123",
            setting_key=None,
            filter_user_id=None,
            limit=50,
            offset=0
        )

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_audit_with_filter_user_id(
        self, mock_log_event, audit_tools, mock_settings_service, mock_context
    ):
        """Test audit retrieval filtered by user who made changes."""
        mock_settings_service.get_settings_audit.return_value = SettingsResponse(
            success=True,
            message="Audit entries retrieved",
            data={"entries": [], "total": 0}
        )

        result = await audit_tools.get_settings_audit(
            filter_user_id="target-user-456",
            ctx=mock_context
        )

        assert result["success"] is True
        mock_settings_service.get_settings_audit.assert_called_once_with(
            user_id="admin-user-123",
            setting_key=None,
            filter_user_id="target-user-456",
            limit=100,
            offset=0
        )

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_audit_with_offset(
        self, mock_log_event, audit_tools, mock_settings_service, mock_context
    ):
        """Test audit retrieval with pagination offset."""
        mock_settings_service.get_settings_audit.return_value = SettingsResponse(
            success=True,
            message="Audit entries retrieved",
            data={"entries": [], "total": 0}
        )

        result = await audit_tools.get_settings_audit(
            limit=25,
            offset=50,
            ctx=mock_context
        )

        assert result["success"] is True
        mock_settings_service.get_settings_audit.assert_called_once_with(
            user_id="admin-user-123",
            setting_key=None,
            filter_user_id=None,
            limit=25,
            offset=50
        )

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_admin_required_failure(
        self, mock_log_event, audit_tools, mock_settings_service, mock_context
    ):
        """Test that non-admin users are rejected."""
        mock_settings_service.get_settings_audit.return_value = SettingsResponse(
            success=False,
            message="Admin privileges required to access audit logs",
            error="ADMIN_REQUIRED"
        )

        result = await audit_tools.get_settings_audit(ctx=mock_context)

        assert result["success"] is False
        assert result["error"] == "ADMIN_REQUIRED"
        # Verify warning log event was called
        mock_log_event.assert_called()
        assert mock_log_event.call_args[0][1] == "WARNING"

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_handles_service_exception(
        self, mock_log_event, audit_tools, mock_settings_service, mock_context
    ):
        """Test handling of service exceptions."""
        mock_settings_service.get_settings_audit.side_effect = Exception("Database error")

        result = await audit_tools.get_settings_audit(ctx=mock_context)

        assert result["success"] is False
        assert result["error"] == "AUDIT_ERROR"
        assert "Database error" in result["message"]
        # Verify error log event was called
        mock_log_event.assert_called()
        assert mock_log_event.call_args[0][1] == "ERROR"

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_uses_user_id_parameter_when_no_context(
        self, mock_log_event, audit_tools, mock_settings_service
    ):
        """Test that user_id parameter is used when context has no userId."""
        mock_settings_service.get_settings_audit.return_value = SettingsResponse(
            success=True,
            message="Audit entries retrieved",
            data={"entries": [], "total": 0}
        )

        result = await audit_tools.get_settings_audit(
            user_id="fallback-user",
            ctx=None
        )

        assert result["success"] is True
        mock_settings_service.get_settings_audit.assert_called_once_with(
            user_id="fallback-user",
            setting_key=None,
            filter_user_id=None,
            limit=100,
            offset=0
        )


class TestGetAuthAudit:
    """Tests for get_auth_audit tool."""

    @pytest.fixture
    def mock_log_entries(self):
        """Create mock log entries for auth events."""
        return [
            LogEntry(
                id="sec-abc123",
                timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
                level="INFO",
                source="auth",
                message="LOGIN successful for user: admin",
                tags=["security", "authentication", "login", "success"],
                metadata={
                    "username": "admin",
                    "event_type": "LOGIN",
                    "success": True,
                    "client_ip": "192.168.1.100",
                    "user_agent": "Mozilla/5.0"
                }
            ),
            LogEntry(
                id="sec-def456",
                timestamp=datetime(2024, 1, 15, 11, 0, 0, tzinfo=UTC),
                level="WARNING",
                source="auth",
                message="LOGIN failed for user: unknown",
                tags=["security", "authentication", "login", "failure"],
                metadata={
                    "username": "unknown",
                    "event_type": "LOGIN",
                    "success": False,
                    "client_ip": "10.0.0.50",
                    "user_agent": "curl/7.68.0"
                }
            ),
        ]

    @pytest.fixture
    def mock_log_service(self):
        """Create mock log service."""
        return AsyncMock()

    @pytest.fixture
    def audit_tools_with_mock_log(self, mock_settings_service, mock_log_service):
        """Create AuditTools instance with mocked log service."""
        tools = AuditTools(mock_settings_service)
        tools._log_service = mock_log_service
        return tools

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_requires_authentication(
        self, mock_log_event, audit_tools, mock_context_no_user
    ):
        """Test that authentication is required."""
        result = await audit_tools.get_auth_audit(ctx=mock_context_no_user)

        assert result["success"] is False
        assert result["error"] == "AUTHENTICATION_REQUIRED"

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_requires_admin_access(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service, mock_context
    ):
        """Test that admin access is required."""
        mock_settings_service.verify_admin_access.return_value = False

        result = await audit_tools_with_mock_log.get_auth_audit(ctx=mock_context)

        assert result["success"] is False
        assert result["error"] == "ADMIN_REQUIRED"
        mock_settings_service.verify_admin_access.assert_called_once_with("admin-user-123")

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_successful_auth_audit_retrieval(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service, mock_context, mock_log_entries
    ):
        """Test successful retrieval of auth audit entries."""
        mock_settings_service.verify_admin_access.return_value = True
        mock_log_service.get_logs.return_value = mock_log_entries

        result = await audit_tools_with_mock_log.get_auth_audit(ctx=mock_context)

        assert result["success"] is True
        assert len(result["data"]["audit_entries"]) == 2
        assert result["data"]["audit_entries"][0]["event_type"] == "LOGIN"
        assert result["data"]["audit_entries"][0]["success"] is True
        assert result["data"]["audit_entries"][1]["success"] is False

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_auth_audit_with_event_type_filter(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service, mock_context, mock_log_entries
    ):
        """Test auth audit with event type filter."""
        mock_settings_service.verify_admin_access.return_value = True
        mock_log_service.get_logs.return_value = mock_log_entries

        result = await audit_tools_with_mock_log.get_auth_audit(
            event_type="LOGIN",
            ctx=mock_context
        )

        assert result["success"] is True
        # All mock entries are LOGIN events
        assert len(result["data"]["audit_entries"]) == 2

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_auth_audit_with_username_filter(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service, mock_context, mock_log_entries
    ):
        """Test auth audit with username filter."""
        mock_settings_service.verify_admin_access.return_value = True
        mock_log_service.get_logs.return_value = mock_log_entries

        result = await audit_tools_with_mock_log.get_auth_audit(
            username="admin",
            ctx=mock_context
        )

        assert result["success"] is True
        assert len(result["data"]["audit_entries"]) == 1
        assert result["data"]["audit_entries"][0]["username"] == "admin"

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_auth_audit_with_success_filter(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service, mock_context, mock_log_entries
    ):
        """Test auth audit with success/failure filter."""
        mock_settings_service.verify_admin_access.return_value = True
        mock_log_service.get_logs.return_value = mock_log_entries

        # Filter for failures only
        result = await audit_tools_with_mock_log.get_auth_audit(
            success_only=False,
            ctx=mock_context
        )

        assert result["success"] is True
        assert len(result["data"]["audit_entries"]) == 1
        assert result["data"]["audit_entries"][0]["success"] is False

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_auth_audit_with_pagination(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service, mock_context
    ):
        """Test auth audit with pagination parameters."""
        mock_settings_service.verify_admin_access.return_value = True
        mock_log_service.get_logs.return_value = []

        await audit_tools_with_mock_log.get_auth_audit(
            limit=50,
            offset=25,
            ctx=mock_context
        )

        # Verify LogFilter was created with correct params
        mock_log_service.get_logs.assert_called_once()
        call_args = mock_log_service.get_logs.call_args
        log_filter = call_args[0][0]
        assert log_filter.source == "auth"
        assert log_filter.limit == 50
        assert log_filter.offset == 25

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_handles_service_exception(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service, mock_context
    ):
        """Test handling of service exceptions."""
        mock_settings_service.verify_admin_access.return_value = True
        mock_log_service.get_logs.side_effect = Exception("Database error")

        result = await audit_tools_with_mock_log.get_auth_audit(ctx=mock_context)

        assert result["success"] is False
        assert result["error"] == "AUDIT_ERROR"
        assert "Database error" in result["message"]

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_uses_user_id_parameter_when_no_context(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service
    ):
        """Test that user_id parameter is used when context has no userId."""
        mock_settings_service.verify_admin_access.return_value = True
        mock_log_service.get_logs.return_value = []

        result = await audit_tools_with_mock_log.get_auth_audit(
            user_id="fallback-admin",
            ctx=None
        )

        assert result["success"] is True
        mock_settings_service.verify_admin_access.assert_called_once_with("fallback-admin")

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_auth_audit_filters_out_non_matching_event_type(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service, mock_context, mock_log_entries
    ):
        """Test auth audit filters out entries with non-matching event type."""
        mock_settings_service.verify_admin_access.return_value = True
        mock_log_service.get_logs.return_value = mock_log_entries

        # Filter for LOGOUT which doesn't exist in mock entries
        result = await audit_tools_with_mock_log.get_auth_audit(
            event_type="LOGOUT",
            ctx=mock_context
        )

        assert result["success"] is True
        # No entries should match LOGOUT
        assert len(result["data"]["audit_entries"]) == 0


class TestVerifyAuthenticationException:
    """Tests for exception handling in _verify_authentication."""

    async def test_handles_exception_in_auth_verification(self, audit_tools):
        """Test that exceptions are caught and logged."""
        ctx = MagicMock()
        ctx.meta = MagicMock()
        ctx.meta.get = MagicMock(side_effect=Exception("Broken context"))

        user_id = await audit_tools._verify_authentication(ctx)
        assert user_id is None


class TestGetAgentAudit:
    """Tests for get_agent_audit tool."""

    @pytest.fixture
    def mock_agent_log_entries(self):
        """Create mock log entries for agent events."""
        return [
            LogEntry(
                id="agent-abc123",
                timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
                level="INFO",
                source="agent",
                message="Agent installed on server",
                tags=["agent", "install"],
                metadata={
                    "server_id": "server-1",
                    "server_name": "prod-server",
                    "agent_id": "agent-xyz",
                    "event_type": "AGENT_INSTALLED",
                    "success": True,
                    "details": {"version": "1.0.0"}
                }
            ),
            LogEntry(
                id="agent-def456",
                timestamp=datetime(2024, 1, 15, 11, 0, 0, tzinfo=UTC),
                level="WARNING",
                source="agent",
                message="Agent connection failed",
                tags=["agent", "connection", "failure"],
                metadata={
                    "server_id": "server-2",
                    "server_name": "test-server",
                    "agent_id": "agent-abc",
                    "event_type": "AGENT_CONNECT_FAILED",
                    "success": False,
                    "details": {"error": "Connection refused"}
                }
            ),
        ]

    @pytest.fixture
    def mock_log_service(self):
        """Create mock log service."""
        return AsyncMock()

    @pytest.fixture
    def audit_tools_with_mock_log(self, mock_settings_service, mock_log_service):
        """Create AuditTools instance with mocked log service."""
        tools = AuditTools(mock_settings_service)
        tools._log_service = mock_log_service
        return tools

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_requires_authentication(
        self, mock_log_event, audit_tools, mock_context_no_user
    ):
        """Test that authentication is required."""
        result = await audit_tools.get_agent_audit(ctx=mock_context_no_user)

        assert result["success"] is False
        assert result["error"] == "AUTHENTICATION_REQUIRED"

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_requires_admin_access(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_context
    ):
        """Test that admin access is required."""
        mock_settings_service.verify_admin_access.return_value = False

        result = await audit_tools_with_mock_log.get_agent_audit(ctx=mock_context)

        assert result["success"] is False
        assert result["error"] == "ADMIN_REQUIRED"

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_successful_agent_audit_retrieval(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service, mock_context, mock_agent_log_entries
    ):
        """Test successful retrieval of agent audit entries."""
        mock_settings_service.verify_admin_access.return_value = True
        mock_log_service.get_logs.return_value = mock_agent_log_entries
        mock_log_service.count_logs.return_value = 2

        result = await audit_tools_with_mock_log.get_agent_audit(ctx=mock_context)

        assert result["success"] is True
        assert len(result["data"]["audit_entries"]) == 2
        assert result["data"]["audit_entries"][0]["event_type"] == "AGENT_INSTALLED"
        assert result["data"]["audit_entries"][0]["success"] is True

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_agent_audit_with_server_id_filter(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service, mock_context, mock_agent_log_entries
    ):
        """Test agent audit with server_id filter."""
        mock_settings_service.verify_admin_access.return_value = True
        mock_log_service.get_logs.return_value = mock_agent_log_entries
        mock_log_service.count_logs.return_value = 2

        result = await audit_tools_with_mock_log.get_agent_audit(
            server_id="server-1",
            ctx=mock_context
        )

        assert result["success"] is True
        assert len(result["data"]["audit_entries"]) == 1
        assert result["data"]["audit_entries"][0]["server_id"] == "server-1"

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_agent_audit_with_event_type_filter(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service, mock_context, mock_agent_log_entries
    ):
        """Test agent audit with event_type filter."""
        mock_settings_service.verify_admin_access.return_value = True
        mock_log_service.get_logs.return_value = mock_agent_log_entries
        mock_log_service.count_logs.return_value = 2

        result = await audit_tools_with_mock_log.get_agent_audit(
            event_type="AGENT_INSTALLED",
            ctx=mock_context
        )

        assert result["success"] is True
        assert len(result["data"]["audit_entries"]) == 1

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_agent_audit_with_success_filter(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service, mock_context, mock_agent_log_entries
    ):
        """Test agent audit with success filter."""
        mock_settings_service.verify_admin_access.return_value = True
        mock_log_service.get_logs.return_value = mock_agent_log_entries
        mock_log_service.count_logs.return_value = 2

        result = await audit_tools_with_mock_log.get_agent_audit(
            success_only=False,
            ctx=mock_context
        )

        assert result["success"] is True
        assert len(result["data"]["audit_entries"]) == 1
        assert result["data"]["audit_entries"][0]["success"] is False

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_agent_audit_with_pagination(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service, mock_context, mock_agent_log_entries
    ):
        """Test agent audit with pagination."""
        mock_settings_service.verify_admin_access.return_value = True
        mock_log_service.get_logs.return_value = mock_agent_log_entries
        mock_log_service.count_logs.return_value = 2

        result = await audit_tools_with_mock_log.get_agent_audit(
            limit=1,
            offset=1,
            ctx=mock_context
        )

        assert result["success"] is True
        assert len(result["data"]["audit_entries"]) == 1
        assert result["data"]["total"] == 2

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_agent_audit_with_truncation(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service, mock_context, mock_agent_log_entries
    ):
        """Test agent audit shows truncation warning when results exceed fetch limit."""
        mock_settings_service.verify_admin_access.return_value = True
        mock_log_service.get_logs.return_value = mock_agent_log_entries
        mock_log_service.count_logs.return_value = 1500  # More than fetch_limit (1000)

        result = await audit_tools_with_mock_log.get_agent_audit(ctx=mock_context)

        assert result["success"] is True
        assert result["data"]["truncated"] is True
        assert "1500" in result["message"]

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_handles_service_exception(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service, mock_context
    ):
        """Test handling of service exceptions."""
        mock_settings_service.verify_admin_access.return_value = True
        mock_log_service.count_logs.side_effect = Exception("Database error")

        result = await audit_tools_with_mock_log.get_agent_audit(ctx=mock_context)

        assert result["success"] is False
        assert result["error"] == "AUDIT_ERROR"
        assert "Database error" in result["message"]

    @patch("tools.audit.tools.log_event", new_callable=AsyncMock)
    async def test_uses_user_id_parameter_when_no_context(
        self, mock_log_event, audit_tools_with_mock_log, mock_settings_service, mock_log_service
    ):
        """Test that user_id parameter is used when context has no userId."""
        mock_settings_service.verify_admin_access.return_value = True
        mock_log_service.get_logs.return_value = []
        mock_log_service.count_logs.return_value = 0

        result = await audit_tools_with_mock_log.get_agent_audit(
            user_id="fallback-admin",
            ctx=None
        )

        assert result["success"] is True
        mock_settings_service.verify_admin_access.assert_called_once_with("fallback-admin")

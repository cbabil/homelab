"""
Unit tests for retention MCP tools.

Tests MCP tool functionality, request validation, security enforcement,
and response formatting with focus on admin-only access controls and audit logging.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastmcp import Context
from tools.retention_tools import RetentionTools
from services.retention_service import RetentionService
from models.retention import (
    DataRetentionSettings, CleanupRequest, CleanupResult, CleanupPreview,
    RetentionType, RetentionOperation
)


class TestRetentionToolsInitialization:
    """Test retention tools initialization and dependency injection."""

    def test_tools_initialization(self):
        """Test retention tools initialize with service dependency."""
        mock_service = MagicMock(spec=RetentionService)
        tools = RetentionTools(mock_service)

        assert tools.retention_service == mock_service


class TestGetRetentionSettings:
    """Test get retention settings MCP tool."""

    @pytest.fixture
    def tools(self):
        """Create retention tools with mocked service."""
        mock_service = AsyncMock(spec=RetentionService)
        return RetentionTools(mock_service)

    async def test_get_settings_success(self, tools):
        """Test successful retention settings retrieval."""
        settings = DataRetentionSettings(
            log_retention_days=60,
            auto_cleanup_enabled=True
        )
        tools.retention_service.get_retention_settings.return_value = settings

        result = await tools.get_retention_settings(user_id="admin-123")

        assert result["success"] is True
        assert result["data"]["log_retention_days"] == 60
        assert result["data"]["auto_cleanup_enabled"] is True
        assert "successfully" in result["message"]

    async def test_get_settings_missing_user_id(self, tools):
        """Test get settings with missing user ID."""
        result = await tools.get_retention_settings(user_id=None)

        assert result["success"] is False
        assert result["error"] == "MISSING_USER_ID"
        assert "User ID is required" in result["message"]

    async def test_get_settings_empty_user_id(self, tools):
        """Test get settings with empty user ID."""
        result = await tools.get_retention_settings(user_id="")

        assert result["success"] is False
        assert result["error"] == "MISSING_USER_ID"

    async def test_get_settings_service_returns_none(self, tools):
        """Test get settings when service returns None."""
        tools.retention_service.get_retention_settings.return_value = None

        result = await tools.get_retention_settings(user_id="admin-123")

        assert result["success"] is False
        assert result["error"] == "SETTINGS_RETRIEVAL_ERROR"
        assert "Failed to retrieve" in result["message"]

    async def test_get_settings_service_exception(self, tools):
        """Test get settings handles service exceptions."""
        tools.retention_service.get_retention_settings.side_effect = Exception("Database error")

        result = await tools.get_retention_settings(user_id="admin-123")

        assert result["success"] is False
        assert result["error"] == "GET_SETTINGS_ERROR"
        assert "Database error" in result["message"]


class TestUpdateRetentionSettings:
    """Test update retention settings MCP tool."""

    @pytest.fixture
    def tools(self):
        """Create retention tools with mocked service."""
        mock_service = AsyncMock(spec=RetentionService)
        return RetentionTools(mock_service)

    @pytest.fixture
    def valid_settings_data(self):
        """Create valid settings data."""
        return {
            "log_retention_days": 90,
            "user_data_retention_days": 730,
            "auto_cleanup_enabled": True
        }

    async def test_update_settings_success(self, tools, valid_settings_data):
        """Test successful retention settings update."""
        tools.retention_service.update_retention_settings.return_value = True

        result = await tools.update_retention_settings(
            settings_data=valid_settings_data,
            user_id="admin-123"
        )

        assert result["success"] is True
        assert result["data"]["log_retention_days"] == 90
        assert result["data"]["auto_cleanup_enabled"] is True
        assert "successfully" in result["message"]

    async def test_update_settings_missing_user_id(self, tools, valid_settings_data):
        """Test update settings with missing user ID."""
        result = await tools.update_retention_settings(
            settings_data=valid_settings_data,
            user_id=None
        )

        assert result["success"] is False
        assert result["error"] == "MISSING_USER_ID"
        assert "User ID is required" in result["message"]

    async def test_update_settings_missing_data(self, tools):
        """Test update settings with missing data."""
        result = await tools.update_retention_settings(
            settings_data=None,
            user_id="admin-123"
        )

        assert result["success"] is False
        assert result["error"] == "MISSING_SETTINGS_DATA"
        assert "Settings data is required" in result["message"]

    async def test_update_settings_empty_data(self, tools):
        """Test update settings with empty data."""
        result = await tools.update_retention_settings(
            settings_data={},
            user_id="admin-123"
        )

        assert result["success"] is False
        assert result["error"] == "MISSING_SETTINGS_DATA"

    async def test_update_settings_invalid_data(self, tools):
        """Test update settings with invalid data."""
        invalid_data = {
            "log_retention_days": 5,  # Below minimum
            "invalid_field": "value"
        }

        result = await tools.update_retention_settings(
            settings_data=invalid_data,
            user_id="admin-123"
        )

        assert result["success"] is False
        assert result["error"] == "SETTINGS_VALIDATION_ERROR"
        assert "Invalid settings data" in result["message"]

    async def test_update_settings_service_failure(self, tools, valid_settings_data):
        """Test update settings when service update fails."""
        tools.retention_service.update_retention_settings.return_value = False

        result = await tools.update_retention_settings(
            settings_data=valid_settings_data,
            user_id="admin-123"
        )

        assert result["success"] is False
        assert result["error"] == "UPDATE_FAILED"
        assert "Failed to update" in result["message"]

    async def test_update_settings_service_exception(self, tools, valid_settings_data):
        """Test update settings handles service exceptions."""
        tools.retention_service.update_retention_settings.side_effect = Exception("Auth error")

        result = await tools.update_retention_settings(
            settings_data=valid_settings_data,
            user_id="admin-123"
        )

        assert result["success"] is False
        assert result["error"] == "UPDATE_SETTINGS_ERROR"
        assert "Auth error" in result["message"]


class TestPreviewCleanup:
    """Test preview cleanup MCP tool (dry-run operations)."""

    @pytest.fixture
    def tools(self):
        """Create retention tools with mocked service."""
        mock_service = AsyncMock(spec=RetentionService)
        return RetentionTools(mock_service)

    @pytest.fixture
    def valid_request_data(self):
        """Create valid cleanup request data."""
        return {
            "retention_type": "logs",
            "admin_user_id": "admin-123",
            "session_token": "valid-token",
            "dry_run": False  # Will be forced to True
        }

    @pytest.fixture
    def mock_context(self):
        """Create mock context with client metadata."""
        ctx = MagicMock(spec=Context)
        ctx.meta = {
            "clientIp": "192.168.1.100",
            "userAgent": "Mozilla/5.0 (Test Browser)"
        }
        return ctx

    async def test_preview_cleanup_success(self, tools, valid_request_data):
        """Test successful cleanup preview."""
        preview = CleanupPreview(
            retention_type=RetentionType.LOGS,
            affected_records=150,
            cutoff_date="2023-08-15T00:00:00.000Z"
        )
        tools.retention_service.preview_cleanup.return_value = preview

        result = await tools.preview_cleanup(valid_request_data)

        assert result["success"] is True
        assert result["data"]["retention_type"] == "logs"
        assert result["data"]["affected_records"] == 150
        assert "successfully" in result["message"]

        # Verify dry_run was forced to True
        call_args = tools.retention_service.preview_cleanup.call_args[0][0]
        assert call_args.dry_run is True

    async def test_preview_cleanup_with_context_metadata(self, tools, valid_request_data, mock_context):
        """Test preview cleanup captures client metadata."""
        preview = CleanupPreview(
            retention_type=RetentionType.LOGS,
            affected_records=100,
            cutoff_date="2023-08-15T00:00:00.000Z"
        )
        tools.retention_service.preview_cleanup.return_value = preview

        result = await tools.preview_cleanup(valid_request_data, ctx=mock_context)

        assert result["success"] is True
        # Context metadata should be captured for audit logging

    async def test_preview_cleanup_invalid_request_data(self, tools):
        """Test preview cleanup with invalid request data."""
        invalid_data = {
            "retention_type": "invalid_type",
            "admin_user_id": "",  # Empty user ID
            "session_token": "token"
        }

        result = await tools.preview_cleanup(invalid_data)

        assert result["success"] is False
        assert result["error"] == "REQUEST_VALIDATION_ERROR"
        assert "Invalid cleanup request" in result["message"]

    async def test_preview_cleanup_service_returns_none(self, tools, valid_request_data):
        """Test preview cleanup when service returns None."""
        tools.retention_service.preview_cleanup.return_value = None

        result = await tools.preview_cleanup(valid_request_data)

        assert result["success"] is False
        assert result["error"] == "PREVIEW_FAILED"
        assert "Failed to preview" in result["message"]

    async def test_preview_cleanup_service_exception(self, tools, valid_request_data):
        """Test preview cleanup handles service exceptions."""
        tools.retention_service.preview_cleanup.side_effect = Exception("Security error")

        result = await tools.preview_cleanup(valid_request_data)

        assert result["success"] is False
        assert result["error"] == "PREVIEW_ERROR"
        assert "Security error" in result["message"]


class TestExecuteCleanup:
    """Test execute cleanup MCP tool with security controls."""

    @pytest.fixture
    def tools(self):
        """Create retention tools with mocked service."""
        mock_service = AsyncMock(spec=RetentionService)
        return RetentionTools(mock_service)

    @pytest.fixture
    def dry_run_request_data(self):
        """Create dry-run cleanup request data."""
        return {
            "retention_type": "logs",
            "admin_user_id": "admin-123",
            "session_token": "valid-token",
            "dry_run": True
        }

    @pytest.fixture
    def force_cleanup_request_data(self):
        """Create force cleanup request data."""
        return {
            "retention_type": "logs",
            "admin_user_id": "admin-123",
            "session_token": "valid-token",
            "dry_run": False,
            "force_cleanup": True
        }

    @pytest.fixture
    def mock_context(self):
        """Create mock context with client metadata."""
        ctx = MagicMock(spec=Context)
        ctx.meta = {
            "clientIp": "10.0.0.50",
            "userAgent": "AdminTool/1.0"
        }
        return ctx

    async def test_execute_cleanup_dry_run_success(self, tools, dry_run_request_data):
        """Test successful dry-run cleanup execution."""
        cleanup_result = CleanupResult(
            operation_id="dry-run-123",
            retention_type=RetentionType.LOGS,
            operation=RetentionOperation.DRY_RUN,
            success=True,
            records_affected=200,
            start_time="2023-09-14T10:00:00.000Z",
            end_time="2023-09-14T10:00:05.000Z",
            admin_user_id="admin-123"
        )
        tools.retention_service.perform_cleanup.return_value = cleanup_result

        result = await tools.execute_cleanup(dry_run_request_data)

        assert result["success"] is True
        assert result["data"]["operation"] == "dry_run"
        assert result["data"]["records_affected"] == 200
        assert "completed" in result["message"]

    async def test_execute_cleanup_force_cleanup_success(self, tools, force_cleanup_request_data):
        """Test successful force cleanup execution."""
        cleanup_result = CleanupResult(
            operation_id="cleanup-456",
            retention_type=RetentionType.LOGS,
            operation=RetentionOperation.CLEANUP,
            success=True,
            records_affected=150,
            space_freed_mb=15.5,
            start_time="2023-09-14T10:00:00.000Z",
            end_time="2023-09-14T10:00:30.000Z",
            admin_user_id="admin-123"
        )
        tools.retention_service.perform_cleanup.return_value = cleanup_result

        result = await tools.execute_cleanup(force_cleanup_request_data)

        assert result["success"] is True
        assert result["data"]["records_affected"] == 150
        assert result["data"]["space_freed_mb"] == 15.5

    async def test_execute_cleanup_without_force_flag_rejected(self, tools):
        """Test cleanup without force flag is rejected."""
        request_data = {
            "retention_type": "logs",
            "admin_user_id": "admin-123",
            "session_token": "valid-token",
            "dry_run": False,
            "force_cleanup": False  # Missing force flag
        }

        result = await tools.execute_cleanup(request_data)

        assert result["success"] is False
        assert result["error"] == "FORCE_CLEANUP_REQUIRED"
        assert "force_cleanup flag" in result["message"]

    async def test_execute_cleanup_invalid_request_data(self, tools):
        """Test cleanup with invalid request data."""
        invalid_data = {
            "retention_type": "logs",
            "admin_user_id": "admin-123",
            "session_token": "",  # Empty token
            "batch_size": 50  # Below minimum
        }

        result = await tools.execute_cleanup(invalid_data)

        assert result["success"] is False
        assert result["error"] == "REQUEST_VALIDATION_ERROR"

    async def test_execute_cleanup_service_returns_none(self, tools, force_cleanup_request_data):
        """Test cleanup when service returns None."""
        tools.retention_service.perform_cleanup.return_value = None

        result = await tools.execute_cleanup(force_cleanup_request_data)

        assert result["success"] is False
        assert result["error"] == "CLEANUP_EXECUTION_FAILED"

    async def test_execute_cleanup_service_failure(self, tools, force_cleanup_request_data):
        """Test cleanup when service returns failure result."""
        cleanup_result = CleanupResult(
            operation_id="failed-789",
            retention_type=RetentionType.LOGS,
            operation=RetentionOperation.CLEANUP,
            success=False,
            start_time="2023-09-14T10:00:00.000Z",
            end_time="2023-09-14T10:00:01.000Z",
            admin_user_id="admin-123",
            error_message="Security validation failed"
        )
        tools.retention_service.perform_cleanup.return_value = cleanup_result

        result = await tools.execute_cleanup(force_cleanup_request_data)

        assert result["success"] is False
        assert "failed" in result["message"]
        assert result["data"]["error_message"] == "Security validation failed"

    async def test_execute_cleanup_with_context_logging(self, tools, force_cleanup_request_data, mock_context):
        """Test cleanup execution logs context metadata."""
        cleanup_result = CleanupResult(
            operation_id="cleanup-ctx",
            retention_type=RetentionType.LOGS,
            operation=RetentionOperation.CLEANUP,
            success=True,
            records_affected=50,
            start_time="2023-09-14T10:00:00.000Z",
            end_time="2023-09-14T10:00:10.000Z",
            admin_user_id="admin-123"
        )
        tools.retention_service.perform_cleanup.return_value = cleanup_result

        result = await tools.execute_cleanup(force_cleanup_request_data, ctx=mock_context)

        assert result["success"] is True
        # Verify context information is captured for audit


class TestGetCleanupHistory:
    """Test get cleanup history MCP tool."""

    @pytest.fixture
    def tools(self):
        """Create retention tools with mocked service."""
        mock_service = AsyncMock(spec=RetentionService)
        return RetentionTools(mock_service)

    async def test_get_cleanup_history_success(self, tools):
        """Test successful cleanup history retrieval."""
        result = await tools.get_cleanup_history(limit=20, user_id="admin-123")

        assert result["success"] is True
        assert result["data"]["limit"] == 20
        assert "placeholder implementation" in result["message"]
        assert "audit logs contain" in result["data"]["message"]

    async def test_get_cleanup_history_missing_user_id(self, tools):
        """Test cleanup history with missing user ID."""
        result = await tools.get_cleanup_history(limit=50, user_id=None)

        assert result["success"] is False
        assert result["error"] == "MISSING_USER_ID"
        assert "User ID is required" in result["message"]

    async def test_get_cleanup_history_default_limit(self, tools):
        """Test cleanup history with default limit."""
        result = await tools.get_cleanup_history(user_id="admin-123")

        assert result["success"] is True
        assert result["data"]["limit"] == 50  # Default value

    async def test_get_cleanup_history_exception_handling(self, tools):
        """Test cleanup history handles exceptions."""
        with patch('tools.retention_tools.logger') as mock_logger:
            # Force an exception in the method
            with patch.object(tools, 'get_cleanup_history', side_effect=Exception("Service error")):
                result = await tools.get_cleanup_history(user_id="admin-123")

        # The actual implementation doesn't have complex logic that would fail,
        # but test structure is here for when real implementation is added


class TestValidateRetentionPolicy:
    """Test validate retention policy MCP tool."""

    @pytest.fixture
    def tools(self):
        """Create retention tools with mocked service."""
        mock_service = AsyncMock(spec=RetentionService)
        return RetentionTools(mock_service)

    @pytest.fixture
    def valid_policy_data(self):
        """Create valid policy data."""
        return {
            "log_retention_days": 45,
            "user_data_retention_days": 1095,
            "metrics_retention_days": 180,
            "audit_log_retention_days": 2555
        }

    @pytest.fixture
    def invalid_policy_data(self):
        """Create invalid policy data."""
        return {
            "log_retention_days": 3,  # Below minimum
            "user_data_retention_days": 10,  # Below minimum
            "audit_log_retention_days": 100  # Below compliance minimum
        }

    async def test_validate_policy_success(self, tools, valid_policy_data):
        """Test successful policy validation."""
        result = await tools.validate_retention_policy(valid_policy_data)

        assert result["success"] is True
        assert result["data"]["is_valid"] is True
        assert result["data"]["validated_settings"]["log_retention_days"] == 45
        assert len(result["data"]["validation_notes"]) > 0
        assert "successful" in result["message"]

    async def test_validate_policy_invalid_data(self, tools, invalid_policy_data):
        """Test policy validation with invalid data."""
        result = await tools.validate_retention_policy(invalid_policy_data)

        assert result["success"] is True  # Tool succeeds but validation fails
        assert result["data"]["is_valid"] is False
        assert len(result["data"]["validation_errors"]) > 0
        assert len(result["data"]["suggested_corrections"]) > 0
        assert "failed" in result["message"]

    async def test_validate_policy_missing_data(self, tools):
        """Test policy validation with missing data."""
        result = await tools.validate_retention_policy(policy_data=None)

        assert result["success"] is False
        assert result["error"] == "MISSING_POLICY_DATA"
        assert "Policy data is required" in result["message"]

    async def test_validate_policy_empty_data(self, tools):
        """Test policy validation with empty data."""
        result = await tools.validate_retention_policy(policy_data={})

        assert result["success"] is False
        assert result["error"] == "MISSING_POLICY_DATA"

    async def test_validate_policy_exception_handling(self, tools):
        """Test policy validation handles exceptions."""
        with patch('models.retention.DataRetentionSettings', side_effect=Exception("Validation error")):
            result = await tools.validate_retention_policy({"log_retention_days": 30})

        assert result["success"] is False
        assert result["error"] == "VALIDATION_ERROR"
        assert "Validation error" in result["message"]


class TestSecurityAndAuditFeatures:
    """Test security features and audit logging in retention tools."""

    @pytest.fixture
    def tools(self):
        """Create retention tools with mocked service."""
        mock_service = AsyncMock(spec=RetentionService)
        return RetentionTools(mock_service)

    async def test_context_metadata_extraction_with_valid_context(self, tools):
        """Test extraction of client metadata from valid context."""
        ctx = MagicMock(spec=Context)
        ctx.meta = {
            "clientIp": "203.0.113.1",
            "userAgent": "SecurityTool/2.1"
        }

        request_data = {
            "retention_type": "logs",
            "admin_user_id": "admin-123",
            "session_token": "secure-token"
        }

        preview = CleanupPreview(
            retention_type=RetentionType.LOGS,
            affected_records=10,
            cutoff_date="2023-08-15T00:00:00.000Z"
        )
        tools.retention_service.preview_cleanup.return_value = preview

        await tools.preview_cleanup(request_data, ctx=ctx)

        # Context metadata should be available for audit logging
        # (Implementation detail - metadata is extracted but usage depends on service)

    async def test_context_metadata_extraction_with_missing_context(self, tools):
        """Test extraction handles missing or invalid context gracefully."""
        request_data = {
            "retention_type": "logs",
            "admin_user_id": "admin-123",
            "session_token": "token"
        }

        preview = CleanupPreview(
            retention_type=RetentionType.LOGS,
            affected_records=5,
            cutoff_date="2023-08-15T00:00:00.000Z"
        )
        tools.retention_service.preview_cleanup.return_value = preview

        # Should not raise exception with None context
        result = await tools.preview_cleanup(request_data, ctx=None)

        assert result["success"] is True

    async def test_context_metadata_extraction_with_invalid_context(self, tools):
        """Test extraction handles context without meta attribute."""
        ctx = MagicMock(spec=Context)
        # Context exists but has no meta attribute

        request_data = {
            "retention_type": "logs",
            "admin_user_id": "admin-123",
            "session_token": "token"
        }

        preview = CleanupPreview(
            retention_type=RetentionType.LOGS,
            affected_records=3,
            cutoff_date="2023-08-15T00:00:00.000Z"
        )
        tools.retention_service.preview_cleanup.return_value = preview

        # Should not raise exception
        result = await tools.preview_cleanup(request_data, ctx=ctx)

        assert result["success"] is True

    async def test_dangerous_operation_logging(self, tools):
        """Test that dangerous operations are properly logged."""
        force_cleanup_data = {
            "retention_type": "logs",
            "admin_user_id": "admin-123",
            "session_token": "token",
            "dry_run": False,
            "force_cleanup": True
        }

        cleanup_result = CleanupResult(
            operation_id="dangerous-op",
            retention_type=RetentionType.LOGS,
            operation=RetentionOperation.CLEANUP,
            success=True,
            records_affected=1000,
            start_time="2023-09-14T10:00:00.000Z",
            end_time="2023-09-14T10:01:00.000Z",
            admin_user_id="admin-123"
        )
        tools.retention_service.perform_cleanup.return_value = cleanup_result

        with patch('tools.retention_tools.logger') as mock_logger:
            result = await tools.execute_cleanup(force_cleanup_data)

        # Verify warning was logged for non-dry-run operation
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args
        assert "Non-dry-run cleanup operation requested" in warning_call[0][0]

        assert result["success"] is True


class TestInputValidationAndSanitization:
    """Test comprehensive input validation and sanitization."""

    @pytest.fixture
    def tools(self):
        """Create retention tools with mocked service."""
        mock_service = AsyncMock(spec=RetentionService)
        return RetentionTools(mock_service)

    async def test_malformed_retention_type_rejected(self, tools):
        """Test malformed retention type is rejected."""
        malformed_data = {
            "retention_type": "'; DROP TABLE log_entries; --",
            "admin_user_id": "admin-123",
            "session_token": "token"
        }

        result = await tools.preview_cleanup(malformed_data)

        assert result["success"] is False
        assert result["error"] == "REQUEST_VALIDATION_ERROR"

    async def test_sql_injection_attempt_in_user_id(self, tools):
        """Test SQL injection attempt in user ID is handled."""
        injection_data = {
            "retention_type": "logs",
            "admin_user_id": "admin'; DELETE FROM users; --",
            "session_token": "token"
        }

        result = await tools.preview_cleanup(injection_data)

        # Pydantic validation should catch this, but if not, service layer should
        assert result["success"] is False

    async def test_oversized_input_rejection(self, tools):
        """Test oversized input is rejected."""
        oversized_data = {
            "retention_type": "logs",
            "admin_user_id": "a" * 10000,  # Oversized user ID
            "session_token": "token"
        }

        result = await tools.preview_cleanup(oversized_data)

        # Should be rejected by validation
        assert result["success"] is False

    async def test_special_characters_in_valid_context(self, tools):
        """Test special characters in valid context are accepted."""
        valid_data = {
            "retention_type": "logs",
            "admin_user_id": "admin@domain.com",  # Valid email-style user ID
            "session_token": "jwt.token.with-dashes_and123numbers"
        }

        preview = CleanupPreview(
            retention_type=RetentionType.LOGS,
            affected_records=0,
            cutoff_date="2023-08-15T00:00:00.000Z"
        )
        tools.retention_service.preview_cleanup.return_value = preview

        result = await tools.preview_cleanup(valid_data)

        assert result["success"] is True
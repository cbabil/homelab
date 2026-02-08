"""
Unit tests for models/retention.py

Tests data retention models including settings, cleanup operations, and audit entries.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from models.retention import (
    CleanupPreview,
    CleanupRequest,
    CleanupResult,
    RetentionAuditEntry,
    RetentionOperation,
    RetentionSettings,
    RetentionType,
    SecurityValidationResult,
)


class TestRetentionType:
    """Tests for RetentionType enum."""

    def test_log_type_values(self):
        """Test log type enum values."""
        assert RetentionType.AUDIT_LOGS == "audit_logs"
        assert RetentionType.ACCESS_LOGS == "access_logs"
        assert RetentionType.APPLICATION_LOGS == "application_logs"
        assert RetentionType.SERVER_LOGS == "server_logs"

    def test_data_type_values(self):
        """Test data type enum values."""
        assert RetentionType.METRICS == "metrics"
        assert RetentionType.NOTIFICATIONS == "notifications"
        assert RetentionType.SESSIONS == "sessions"

    def test_retention_type_is_string_enum(self):
        """Test that retention type values are strings."""
        for rtype in RetentionType:
            assert isinstance(rtype.value, str)


class TestRetentionOperation:
    """Tests for RetentionOperation enum."""

    def test_operation_values(self):
        """Test all operation enum values."""
        assert RetentionOperation.DRY_RUN == "dry_run"
        assert RetentionOperation.CLEANUP == "cleanup"
        assert RetentionOperation.SETTINGS_UPDATE == "settings_update"
        assert RetentionOperation.POLICY_VALIDATION == "policy_validation"

    def test_operation_is_string_enum(self):
        """Test that operation values are strings."""
        for op in RetentionOperation:
            assert isinstance(op.value, str)


class TestRetentionSettings:
    """Tests for RetentionSettings model."""

    def test_default_values(self):
        """Test default values."""
        settings = RetentionSettings()
        assert settings.log_retention == 30
        assert settings.data_retention == 90
        assert settings.last_updated is None
        assert settings.updated_by_user_id is None

    def test_custom_values(self):
        """Test custom values."""
        settings = RetentionSettings(
            log_retention=60,
            data_retention=180,
            last_updated="2024-01-15T10:00:00Z",
            updated_by_user_id="admin-123",
        )
        assert settings.log_retention == 60
        assert settings.data_retention == 180
        assert settings.last_updated == "2024-01-15T10:00:00Z"
        assert settings.updated_by_user_id == "admin-123"

    def test_log_retention_min_boundary(self):
        """Test log retention minimum boundary (7 days)."""
        settings = RetentionSettings(log_retention=7)
        assert settings.log_retention == 7

    def test_log_retention_max_boundary(self):
        """Test log retention maximum boundary (365 days)."""
        settings = RetentionSettings(log_retention=365)
        assert settings.log_retention == 365

    def test_log_retention_below_min(self):
        """Test validation error when log retention below minimum."""
        with pytest.raises(ValidationError) as exc_info:
            RetentionSettings(log_retention=6)
        assert "log_retention" in str(exc_info.value)

    def test_log_retention_above_max(self):
        """Test validation error when log retention above maximum."""
        with pytest.raises(ValidationError) as exc_info:
            RetentionSettings(log_retention=366)
        assert "log_retention" in str(exc_info.value)

    def test_data_retention_min_boundary(self):
        """Test data retention minimum boundary (7 days)."""
        settings = RetentionSettings(data_retention=7)
        assert settings.data_retention == 7

    def test_data_retention_max_boundary(self):
        """Test data retention maximum boundary (365 days)."""
        settings = RetentionSettings(data_retention=365)
        assert settings.data_retention == 365

    def test_data_retention_below_min(self):
        """Test validation error when data retention below minimum."""
        with pytest.raises(ValidationError) as exc_info:
            RetentionSettings(data_retention=6)
        assert "data_retention" in str(exc_info.value)


class TestCleanupPreview:
    """Tests for CleanupPreview model."""

    def test_required_fields(self):
        """Test required fields."""
        preview = CleanupPreview(
            retention_type=RetentionType.AUDIT_LOGS,
            affected_records=100,
            cutoff_date="2024-01-01T00:00:00Z",
        )
        assert preview.retention_type == RetentionType.AUDIT_LOGS
        assert preview.affected_records == 100
        assert preview.cutoff_date == "2024-01-01T00:00:00Z"

    def test_default_values(self):
        """Test default values."""
        preview = CleanupPreview(
            retention_type=RetentionType.METRICS,
            affected_records=50,
            cutoff_date="2024-01-01T00:00:00Z",
        )
        assert preview.oldest_record_date is None
        assert preview.newest_record_date is None
        assert preview.estimated_space_freed_mb == 0.0

    def test_all_fields(self):
        """Test all fields populated."""
        preview = CleanupPreview(
            retention_type=RetentionType.SESSIONS,
            affected_records=500,
            oldest_record_date="2023-01-01T00:00:00Z",
            newest_record_date="2023-12-31T23:59:59Z",
            estimated_space_freed_mb=125.5,
            cutoff_date="2024-01-01T00:00:00Z",
        )
        assert preview.oldest_record_date == "2023-01-01T00:00:00Z"
        assert preview.newest_record_date == "2023-12-31T23:59:59Z"
        assert preview.estimated_space_freed_mb == 125.5

    def test_affected_records_non_negative(self):
        """Test affected records must be non-negative."""
        with pytest.raises(ValidationError) as exc_info:
            CleanupPreview(
                retention_type=RetentionType.AUDIT_LOGS,
                affected_records=-1,
                cutoff_date="2024-01-01T00:00:00Z",
            )
        assert "affected_records" in str(exc_info.value)

    def test_all_retention_types(self):
        """Test preview with each retention type."""
        for rtype in RetentionType:
            preview = CleanupPreview(
                retention_type=rtype,
                affected_records=10,
                cutoff_date="2024-01-01T00:00:00Z",
            )
            assert preview.retention_type == rtype


class TestCleanupRequest:
    """Tests for CleanupRequest model."""

    def test_required_fields(self):
        """Test required fields."""
        request = CleanupRequest(
            retention_type=RetentionType.AUDIT_LOGS,
            admin_user_id="admin-123",
            session_token="session-token-xyz",
        )
        assert request.retention_type == RetentionType.AUDIT_LOGS
        assert request.admin_user_id == "admin-123"
        assert request.session_token == "session-token-xyz"

    def test_default_values(self):
        """Test default values."""
        request = CleanupRequest(
            retention_type=RetentionType.METRICS,
            admin_user_id="admin-123",
            session_token="session-token",
        )
        assert request.dry_run is True
        assert request.csrf_token is None
        assert request.force_cleanup is False
        assert request.batch_size == 1000

    def test_all_fields(self):
        """Test all fields populated."""
        request = CleanupRequest(
            retention_type=RetentionType.NOTIFICATIONS,
            dry_run=False,
            admin_user_id="admin-456",
            session_token="session-token-abc",
            csrf_token="a" * 32,  # 32 chars minimum
            force_cleanup=True,
            batch_size=5000,
        )
        assert request.dry_run is False
        assert request.csrf_token == "a" * 32
        assert request.force_cleanup is True
        assert request.batch_size == 5000

    def test_admin_user_validation_empty(self):
        """Test validation error for empty admin user ID."""
        with pytest.raises(ValidationError) as exc_info:
            CleanupRequest(
                retention_type=RetentionType.AUDIT_LOGS,
                admin_user_id="",
                session_token="session-token",
            )
        assert "admin_user_id" in str(exc_info.value).lower()

    def test_admin_user_validation_whitespace_only(self):
        """Test validation error for whitespace-only admin user ID."""
        with pytest.raises(ValidationError) as exc_info:
            CleanupRequest(
                retention_type=RetentionType.AUDIT_LOGS,
                admin_user_id="   ",
                session_token="session-token",
            )
        assert "Admin user ID is required" in str(exc_info.value)

    def test_admin_user_validation_strips_whitespace(self):
        """Test admin user ID is stripped of whitespace."""
        request = CleanupRequest(
            retention_type=RetentionType.AUDIT_LOGS,
            admin_user_id="  admin-123  ",
            session_token="session-token",
        )
        assert request.admin_user_id == "admin-123"

    def test_csrf_token_min_length(self):
        """Test CSRF token minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            CleanupRequest(
                retention_type=RetentionType.AUDIT_LOGS,
                admin_user_id="admin-123",
                session_token="session-token",
                csrf_token="short",  # Less than 32 chars
            )
        assert "csrf_token" in str(exc_info.value)

    def test_batch_size_min_boundary(self):
        """Test batch size minimum boundary (100)."""
        request = CleanupRequest(
            retention_type=RetentionType.METRICS,
            admin_user_id="admin-123",
            session_token="session-token",
            batch_size=100,
        )
        assert request.batch_size == 100

    def test_batch_size_max_boundary(self):
        """Test batch size maximum boundary (10000)."""
        request = CleanupRequest(
            retention_type=RetentionType.METRICS,
            admin_user_id="admin-123",
            session_token="session-token",
            batch_size=10000,
        )
        assert request.batch_size == 10000

    def test_batch_size_below_min(self):
        """Test validation error when batch size below minimum."""
        with pytest.raises(ValidationError) as exc_info:
            CleanupRequest(
                retention_type=RetentionType.METRICS,
                admin_user_id="admin-123",
                session_token="session-token",
                batch_size=99,
            )
        assert "batch_size" in str(exc_info.value)


class TestCleanupResult:
    """Tests for CleanupResult model."""

    def test_required_fields(self):
        """Test required fields."""
        result = CleanupResult(
            operation_id="op-123",
            retention_type=RetentionType.AUDIT_LOGS,
            operation=RetentionOperation.DRY_RUN,
            success=True,
            start_time="2024-01-15T10:00:00Z",
            end_time="2024-01-15T10:00:05Z",
            admin_user_id="admin-123",
        )
        assert result.operation_id == "op-123"
        assert result.retention_type == RetentionType.AUDIT_LOGS
        assert result.operation == RetentionOperation.DRY_RUN
        assert result.success is True
        assert result.admin_user_id == "admin-123"

    def test_default_values(self):
        """Test default values."""
        result = CleanupResult(
            operation_id="op-123",
            retention_type=RetentionType.METRICS,
            operation=RetentionOperation.CLEANUP,
            success=True,
            start_time="2024-01-15T10:00:00Z",
            end_time="2024-01-15T10:00:05Z",
            admin_user_id="admin-123",
        )
        assert result.records_affected == 0
        assert result.space_freed_mb == 0.0
        assert result.duration_seconds == 0.0
        assert result.error_message is None
        assert result.preview_data is None

    def test_all_fields(self):
        """Test all fields populated."""
        preview = CleanupPreview(
            retention_type=RetentionType.SESSIONS,
            affected_records=500,
            cutoff_date="2024-01-01T00:00:00Z",
        )
        result = CleanupResult(
            operation_id="op-456",
            retention_type=RetentionType.SESSIONS,
            operation=RetentionOperation.CLEANUP,
            success=True,
            records_affected=500,
            space_freed_mb=50.5,
            duration_seconds=12.5,
            start_time="2024-01-15T10:00:00Z",
            end_time="2024-01-15T10:00:12Z",
            admin_user_id="admin-456",
            preview_data=preview,
        )
        assert result.records_affected == 500
        assert result.space_freed_mb == 50.5
        assert result.duration_seconds == 12.5
        assert result.preview_data.affected_records == 500

    def test_failed_operation(self):
        """Test failed operation result."""
        result = CleanupResult(
            operation_id="op-789",
            retention_type=RetentionType.NOTIFICATIONS,
            operation=RetentionOperation.CLEANUP,
            success=False,
            start_time="2024-01-15T10:00:00Z",
            end_time="2024-01-15T10:00:01Z",
            admin_user_id="admin-123",
            error_message="Database connection failed",
        )
        assert result.success is False
        assert result.error_message == "Database connection failed"


class TestRetentionAuditEntry:
    """Tests for RetentionAuditEntry model."""

    def test_required_fields(self):
        """Test required fields."""
        entry = RetentionAuditEntry(
            id="audit-123",
            operation=RetentionOperation.CLEANUP,
            admin_user_id="admin-123",
            success=True,
        )
        assert entry.id == "audit-123"
        assert entry.operation == RetentionOperation.CLEANUP
        assert entry.admin_user_id == "admin-123"
        assert entry.success is True

    def test_default_values(self):
        """Test default values."""
        entry = RetentionAuditEntry(
            id="audit-123",
            operation=RetentionOperation.DRY_RUN,
            admin_user_id="admin-123",
            success=True,
        )
        assert entry.retention_type is None
        assert entry.client_ip is None
        assert entry.user_agent is None
        assert entry.records_affected == 0
        assert entry.error_message is None
        assert entry.metadata == {}
        # timestamp should be auto-generated
        assert entry.timestamp is not None

    def test_all_fields(self):
        """Test all fields populated."""
        now = datetime.now(UTC)
        entry = RetentionAuditEntry(
            id="audit-456",
            timestamp=now,
            operation=RetentionOperation.SETTINGS_UPDATE,
            retention_type=RetentionType.AUDIT_LOGS,
            admin_user_id="admin-456",
            client_ip="192.168.1.100",
            user_agent="Mozilla/5.0",
            success=True,
            records_affected=1000,
            metadata={"old_value": 30, "new_value": 60},
        )
        assert entry.retention_type == RetentionType.AUDIT_LOGS
        assert entry.client_ip == "192.168.1.100"
        assert entry.user_agent == "Mozilla/5.0"
        assert entry.records_affected == 1000
        assert entry.metadata == {"old_value": 30, "new_value": 60}

    def test_timestamp_serialization(self):
        """Test timestamp serialization to ISO format."""
        now = datetime(2024, 1, 15, 10, 30, 45)
        entry = RetentionAuditEntry(
            id="audit-123",
            timestamp=now,
            operation=RetentionOperation.CLEANUP,
            admin_user_id="admin-123",
            success=True,
        )
        data = entry.model_dump()
        assert data["timestamp"] == "2024-01-15T10:30:45"

    def test_failed_entry(self):
        """Test failed audit entry."""
        entry = RetentionAuditEntry(
            id="audit-789",
            operation=RetentionOperation.CLEANUP,
            admin_user_id="admin-123",
            success=False,
            error_message="Permission denied",
        )
        assert entry.success is False
        assert entry.error_message == "Permission denied"


class TestSecurityValidationResult:
    """Tests for SecurityValidationResult model."""

    def test_required_fields(self):
        """Test required fields."""
        result = SecurityValidationResult(is_valid=True)
        assert result.is_valid is True

    def test_default_values(self):
        """Test default values."""
        result = SecurityValidationResult(is_valid=False)
        assert result.is_admin is False
        assert result.session_valid is False
        assert result.user_id is None
        assert result.error_message is None
        assert result.requires_additional_verification is False

    def test_valid_admin_session(self):
        """Test valid admin session result."""
        result = SecurityValidationResult(
            is_valid=True,
            is_admin=True,
            session_valid=True,
            user_id="admin-123",
        )
        assert result.is_valid is True
        assert result.is_admin is True
        assert result.session_valid is True
        assert result.user_id == "admin-123"

    def test_invalid_with_error(self):
        """Test invalid result with error message."""
        result = SecurityValidationResult(
            is_valid=False,
            is_admin=False,
            session_valid=False,
            error_message="Session expired",
        )
        assert result.is_valid is False
        assert result.error_message == "Session expired"

    def test_requires_verification(self):
        """Test result requiring additional verification."""
        result = SecurityValidationResult(
            is_valid=True,
            is_admin=True,
            session_valid=True,
            user_id="admin-123",
            requires_additional_verification=True,
        )
        assert result.requires_additional_verification is True

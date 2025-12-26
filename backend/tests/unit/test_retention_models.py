"""
Unit tests for data retention models.

Tests comprehensive validation logic, business constraints, and security requirements
for all retention model classes with focus on edge cases and security boundaries.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from models.retention import (
    DataRetentionSettings, CleanupRequest, CleanupResult, CleanupPreview,
    RetentionAuditEntry, SecurityValidationResult, RetentionType, RetentionOperation
)


class TestDataRetentionSettings:
    """Test data retention settings model validation and constraints."""

    def test_default_settings_are_valid(self):
        """Test that default settings create valid configuration."""
        settings = DataRetentionSettings()

        assert settings.log_retention_days == 30
        assert settings.user_data_retention_days == 365
        assert settings.metrics_retention_days == 90
        assert settings.audit_log_retention_days == 2555  # 7 years for compliance
        assert not settings.auto_cleanup_enabled
        assert settings.cleanup_batch_size == 1000
        assert settings.last_updated is None
        assert settings.updated_by_user_id is None

    def test_valid_retention_periods(self):
        """Test valid retention period ranges."""
        # Test minimum valid values
        settings = DataRetentionSettings(
            log_retention_days=7,
            user_data_retention_days=30,
            metrics_retention_days=7,
            audit_log_retention_days=365,
            cleanup_batch_size=100
        )
        assert settings.log_retention_days == 7
        assert settings.user_data_retention_days == 30
        assert settings.audit_log_retention_days == 365

        # Test maximum valid values
        settings = DataRetentionSettings(
            log_retention_days=365,
            user_data_retention_days=3650,
            metrics_retention_days=730,
            audit_log_retention_days=3650,
            cleanup_batch_size=10000
        )
        assert settings.log_retention_days == 365
        assert settings.user_data_retention_days == 3650
        assert settings.cleanup_batch_size == 10000

    def test_log_retention_validation_boundaries(self):
        """Test log retention validation at boundaries."""
        # Test below minimum
        with pytest.raises(ValidationError) as exc_info:
            DataRetentionSettings(log_retention_days=6)
        assert "Log retention must be at least 7 days" in str(exc_info.value)

        # Test above maximum
        with pytest.raises(ValidationError) as exc_info:
            DataRetentionSettings(log_retention_days=366)
        assert "Log retention cannot exceed 365 days" in str(exc_info.value)

        # Test edge cases for boundaries
        settings_min = DataRetentionSettings(log_retention_days=7)
        assert settings_min.log_retention_days == 7

        settings_max = DataRetentionSettings(log_retention_days=365)
        assert settings_max.log_retention_days == 365

    def test_audit_log_retention_compliance_validation(self):
        """Test audit log retention meets compliance requirements."""
        # Test below compliance minimum
        with pytest.raises(ValidationError) as exc_info:
            DataRetentionSettings(audit_log_retention_days=364)
        assert "Audit logs must be retained for at least 1 year" in str(exc_info.value)

        # Test compliance minimum is accepted
        settings = DataRetentionSettings(audit_log_retention_days=365)
        assert settings.audit_log_retention_days == 365

    def test_batch_size_validation(self):
        """Test batch size validation for cleanup operations."""
        # Test below minimum
        with pytest.raises(ValidationError):
            DataRetentionSettings(cleanup_batch_size=99)

        # Test above maximum
        with pytest.raises(ValidationError):
            DataRetentionSettings(cleanup_batch_size=10001)

        # Test valid ranges
        settings = DataRetentionSettings(cleanup_batch_size=500)
        assert settings.cleanup_batch_size == 500

    def test_settings_with_user_tracking(self):
        """Test settings with user tracking metadata."""
        timestamp = "2023-09-14T10:30:00.000Z"
        user_id = "admin-user-123"

        settings = DataRetentionSettings(
            log_retention_days=60,
            last_updated=timestamp,
            updated_by_user_id=user_id
        )

        assert settings.last_updated == timestamp
        assert settings.updated_by_user_id == user_id


class TestCleanupRequest:
    """Test cleanup request model validation and security requirements."""

    def test_valid_cleanup_request(self):
        """Test creation of valid cleanup request."""
        request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="valid-token-abc",
            dry_run=True
        )

        assert request.retention_type == RetentionType.LOGS
        assert request.admin_user_id == "admin-123"
        assert request.session_token == "valid-token-abc"
        assert request.dry_run is True
        assert request.force_cleanup is False
        assert request.batch_size == 1000

    def test_admin_user_id_validation(self):
        """Test admin user ID validation requirements."""
        # Test empty string
        with pytest.raises(ValidationError) as exc_info:
            CleanupRequest(
                retention_type=RetentionType.LOGS,
                admin_user_id="",
                session_token="token"
            )
        assert "Admin user ID is required" in str(exc_info.value)

        # Test whitespace-only string
        with pytest.raises(ValidationError) as exc_info:
            CleanupRequest(
                retention_type=RetentionType.LOGS,
                admin_user_id="   ",
                session_token="token"
            )
        assert "Admin user ID is required" in str(exc_info.value)

        # Test valid user ID with whitespace trimming
        request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="  admin-123  ",
            session_token="token"
        )
        assert request.admin_user_id == "admin-123"

    def test_mandatory_dry_run_default(self):
        """Test that dry_run defaults to True for security."""
        request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="token"
        )
        assert request.dry_run is True

    def test_force_cleanup_security_flag(self):
        """Test force_cleanup flag for dangerous operations."""
        request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="token",
            dry_run=False,
            force_cleanup=True
        )

        assert request.dry_run is False
        assert request.force_cleanup is True

    def test_batch_size_validation(self):
        """Test batch size validation in cleanup requests."""
        # Test below minimum
        with pytest.raises(ValidationError):
            CleanupRequest(
                retention_type=RetentionType.LOGS,
                admin_user_id="admin-123",
                session_token="token",
                batch_size=99
            )

        # Test above maximum
        with pytest.raises(ValidationError):
            CleanupRequest(
                retention_type=RetentionType.LOGS,
                admin_user_id="admin-123",
                session_token="token",
                batch_size=10001
            )

        # Test valid batch size
        request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="token",
            batch_size=2000
        )
        assert request.batch_size == 2000


class TestCleanupPreview:
    """Test cleanup preview model for dry-run operations."""

    def test_valid_cleanup_preview(self):
        """Test creation of valid cleanup preview."""
        preview = CleanupPreview(
            retention_type=RetentionType.LOGS,
            affected_records=150,
            oldest_record_date="2023-01-01T00:00:00.000Z",
            newest_record_date="2023-08-01T00:00:00.000Z",
            estimated_space_freed_mb=15.5,
            cutoff_date="2023-08-15T00:00:00.000Z"
        )

        assert preview.retention_type == RetentionType.LOGS
        assert preview.affected_records == 150
        assert preview.estimated_space_freed_mb == 15.5

    def test_zero_records_preview(self):
        """Test preview with no records to delete."""
        preview = CleanupPreview(
            retention_type=RetentionType.LOGS,
            affected_records=0,
            cutoff_date="2023-08-15T00:00:00.000Z"
        )

        assert preview.affected_records == 0
        assert preview.estimated_space_freed_mb == 0.0
        assert preview.oldest_record_date is None
        assert preview.newest_record_date is None

    def test_negative_values_validation(self):
        """Test validation prevents negative values."""
        with pytest.raises(ValidationError):
            CleanupPreview(
                retention_type=RetentionType.LOGS,
                affected_records=-1,
                cutoff_date="2023-08-15T00:00:00.000Z"
            )

        with pytest.raises(ValidationError):
            CleanupPreview(
                retention_type=RetentionType.LOGS,
                affected_records=100,
                estimated_space_freed_mb=-5.0,
                cutoff_date="2023-08-15T00:00:00.000Z"
            )


class TestCleanupResult:
    """Test cleanup result model for operation tracking."""

    def test_successful_cleanup_result(self):
        """Test successful cleanup result creation."""
        result = CleanupResult(
            operation_id="cleanup-abc123",
            retention_type=RetentionType.LOGS,
            operation=RetentionOperation.CLEANUP,
            success=True,
            records_affected=250,
            space_freed_mb=25.6,
            duration_seconds=15.3,
            start_time="2023-09-14T10:00:00.000Z",
            end_time="2023-09-14T10:00:15.300Z",
            admin_user_id="admin-123"
        )

        assert result.success is True
        assert result.records_affected == 250
        assert result.space_freed_mb == 25.6
        assert result.error_message is None

    def test_failed_cleanup_result_with_error(self):
        """Test failed cleanup result with error message."""
        result = CleanupResult(
            operation_id="cleanup-failed-456",
            retention_type=RetentionType.LOGS,
            operation=RetentionOperation.CLEANUP,
            success=False,
            start_time="2023-09-14T10:00:00.000Z",
            end_time="2023-09-14T10:00:05.000Z",
            admin_user_id="admin-123",
            error_message="Database connection failed during cleanup"
        )

        assert result.success is False
        assert result.records_affected == 0
        assert result.error_message == "Database connection failed during cleanup"

    def test_dry_run_result_with_preview(self):
        """Test dry-run result including preview data."""
        preview = CleanupPreview(
            retention_type=RetentionType.LOGS,
            affected_records=100,
            cutoff_date="2023-08-15T00:00:00.000Z"
        )

        result = CleanupResult(
            operation_id="dry-run-789",
            retention_type=RetentionType.LOGS,
            operation=RetentionOperation.DRY_RUN,
            success=True,
            records_affected=100,
            start_time="2023-09-14T10:00:00.000Z",
            end_time="2023-09-14T10:00:02.000Z",
            admin_user_id="admin-123",
            preview_data=preview
        )

        assert result.operation == RetentionOperation.DRY_RUN
        assert result.preview_data is not None
        assert result.preview_data.affected_records == 100


class TestRetentionAuditEntry:
    """Test retention audit entry model for comprehensive logging."""

    def test_audit_entry_creation(self):
        """Test audit entry creation with all fields."""
        entry = RetentionAuditEntry(
            id="ret-abc123",
            operation=RetentionOperation.CLEANUP,
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            client_ip="192.168.1.100",
            user_agent="Mozilla/5.0...",
            success=True,
            records_affected=500,
            metadata={"operation_id": "cleanup-abc123", "batch_size": 1000}
        )

        assert entry.id == "ret-abc123"
        assert entry.operation == RetentionOperation.CLEANUP
        assert entry.client_ip == "192.168.1.100"
        assert entry.records_affected == 500
        assert "operation_id" in entry.metadata
        assert isinstance(entry.timestamp, datetime)

    def test_audit_entry_json_serialization(self):
        """Test audit entry can be serialized to JSON."""
        entry = RetentionAuditEntry(
            id="ret-test",
            operation=RetentionOperation.DRY_RUN,
            admin_user_id="admin-test",
            success=True
        )

        # Test that model can be dumped to dict (JSON serializable)
        entry_dict = entry.model_dump()
        assert "timestamp" in entry_dict
        assert isinstance(entry_dict["timestamp"], str)  # Should be ISO format string

    def test_audit_entry_with_error(self):
        """Test audit entry for failed operations."""
        entry = RetentionAuditEntry(
            id="ret-error",
            operation=RetentionOperation.CLEANUP,
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            success=False,
            error_message="Security validation failed: Invalid session token"
        )

        assert entry.success is False
        assert "Security validation failed" in entry.error_message
        assert entry.records_affected == 0  # Default for failed operations


class TestSecurityValidationResult:
    """Test security validation result model."""

    def test_valid_admin_result(self):
        """Test successful admin validation result."""
        result = SecurityValidationResult(
            is_valid=True,
            is_admin=True,
            session_valid=True,
            user_id="admin-123"
        )

        assert result.is_valid is True
        assert result.is_admin is True
        assert result.session_valid is True
        assert result.user_id == "admin-123"
        assert result.error_message is None
        assert result.requires_additional_verification is False

    def test_invalid_session_result(self):
        """Test failed session validation result."""
        result = SecurityValidationResult(
            is_valid=False,
            session_valid=False,
            error_message="Session token expired"
        )

        assert result.is_valid is False
        assert result.is_admin is False  # Default
        assert result.session_valid is False
        assert result.error_message == "Session token expired"

    def test_non_admin_user_result(self):
        """Test validation result for non-admin user."""
        result = SecurityValidationResult(
            is_valid=False,
            is_admin=False,
            session_valid=True,
            user_id="user-456",
            error_message="Admin privileges required for retention operations"
        )

        assert result.is_valid is False
        assert result.is_admin is False
        assert result.session_valid is True
        assert "Admin privileges required" in result.error_message

    def test_additional_verification_required(self):
        """Test result requiring additional verification for dangerous operations."""
        result = SecurityValidationResult(
            is_valid=True,
            is_admin=True,
            session_valid=True,
            user_id="admin-123",
            requires_additional_verification=True
        )

        assert result.requires_additional_verification is True


class TestRetentionTypeAndOperationEnums:
    """Test retention type and operation enums."""

    def test_retention_types(self):
        """Test all retention type values."""
        assert RetentionType.LOGS == "logs"
        assert RetentionType.USER_DATA == "user_data"
        assert RetentionType.METRICS == "metrics"
        assert RetentionType.AUDIT_LOGS == "audit_logs"

    def test_retention_operations(self):
        """Test all retention operation values."""
        assert RetentionOperation.DRY_RUN == "dry_run"
        assert RetentionOperation.CLEANUP == "cleanup"
        assert RetentionOperation.SETTINGS_UPDATE == "settings_update"
        assert RetentionOperation.POLICY_VALIDATION == "policy_validation"

    def test_enum_usage_in_models(self):
        """Test enum usage in model validation."""
        # Test valid enum value
        request = CleanupRequest(
            retention_type=RetentionType.METRICS,
            admin_user_id="admin",
            session_token="token"
        )
        assert request.retention_type == RetentionType.METRICS

        # Test invalid enum value should raise validation error
        with pytest.raises(ValidationError):
            CleanupRequest(
                retention_type="invalid_type",
                admin_user_id="admin",
                session_token="token"
            )
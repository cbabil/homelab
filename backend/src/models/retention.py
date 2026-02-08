"""
Data Retention Models

Defines data retention settings and operations with comprehensive security validation.
Implements mandatory security controls for data deletion operations.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_serializer, field_validator


class RetentionType(str, Enum):
    """Data retention type definitions."""

    # Log types
    AUDIT_LOGS = "audit_logs"
    ACCESS_LOGS = "access_logs"
    APPLICATION_LOGS = "application_logs"
    SERVER_LOGS = "server_logs"
    # Data types
    METRICS = "metrics"
    NOTIFICATIONS = "notifications"
    SESSIONS = "sessions"


class RetentionOperation(str, Enum):
    """Retention operation types for audit tracking."""

    DRY_RUN = "dry_run"
    CLEANUP = "cleanup"
    SETTINGS_UPDATE = "settings_update"
    POLICY_VALIDATION = "policy_validation"


class RetentionSettings(BaseModel):
    """Retention settings for logs and data."""

    log_retention: int = Field(
        default=30,
        ge=7,
        le=365,
        description="Log retention in days (7-365) - applies to all log types",
    )

    data_retention: int = Field(
        default=90,
        ge=7,
        le=365,
        description="Data retention in days (7-365) - applies to all data types",
    )

    last_updated: str | None = Field(default=None, description="Last update timestamp")

    updated_by_user_id: str | None = Field(
        default=None, description="User ID who last updated settings"
    )


class CleanupPreview(BaseModel):
    """Preview of cleanup operations for dry-run mode."""

    retention_type: RetentionType = Field(..., description="Type of data being cleaned")
    affected_records: int = Field(
        ..., ge=0, description="Number of records to be deleted"
    )
    oldest_record_date: str | None = Field(
        None, description="Oldest record that will be deleted"
    )
    newest_record_date: str | None = Field(
        None, description="Newest record that will be deleted"
    )
    estimated_space_freed_mb: float = Field(
        default=0.0, ge=0, description="Estimated disk space to be freed (MB)"
    )
    cutoff_date: str = Field(..., description="Cutoff date for deletion")


class CleanupRequest(BaseModel):
    """Request for cleanup operations with security validation."""

    retention_type: RetentionType = Field(..., description="Type of data to clean up")
    dry_run: bool = Field(
        default=True,
        description="Whether to perform dry-run (mandatory for first request)",
    )
    admin_user_id: str = Field(
        ..., min_length=1, description="Admin user requesting cleanup"
    )
    session_token: str = Field(
        ..., min_length=1, description="Session token for verification"
    )
    csrf_token: str | None = Field(
        None, min_length=32, description="CSRF token for destructive operations"
    )
    force_cleanup: bool = Field(
        default=False,
        description="Force cleanup even if risky (requires additional verification)",
    )
    batch_size: int | None = Field(
        default=1000, ge=100, le=10000, description="Batch size for cleanup"
    )

    @field_validator("admin_user_id")
    @classmethod
    def validate_admin_user(cls, value: str) -> str:
        """Ensure admin user ID is provided."""
        if not value or not value.strip():
            raise ValueError("Admin user ID is required for cleanup operations")
        return value.strip()


class CleanupResult(BaseModel):
    """Result of cleanup operations with comprehensive audit information."""

    operation_id: str = Field(..., description="Unique operation identifier")
    retention_type: RetentionType = Field(..., description="Type of data cleaned")
    operation: RetentionOperation = Field(
        ..., description="Type of operation performed"
    )
    success: bool = Field(..., description="Operation success status")
    records_affected: int = Field(
        default=0, ge=0, description="Number of records affected"
    )
    space_freed_mb: float = Field(
        default=0.0, ge=0, description="Disk space freed (MB)"
    )
    duration_seconds: float = Field(default=0.0, ge=0, description="Operation duration")
    start_time: str = Field(..., description="Operation start timestamp")
    end_time: str = Field(..., description="Operation end timestamp")
    admin_user_id: str = Field(..., description="Admin user who performed operation")
    error_message: str | None = Field(
        None, description="Error message if operation failed"
    )
    preview_data: CleanupPreview | None = Field(
        None, description="Preview data for dry-run operations"
    )


class RetentionAuditEntry(BaseModel):
    """Audit entry for retention operations."""

    id: str = Field(..., description="Unique audit entry identifier")

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Audit timestamp",
    )
    operation: RetentionOperation = Field(..., description="Type of operation")
    retention_type: RetentionType | None = Field(
        None, description="Type of data affected"
    )
    admin_user_id: str = Field(..., description="Admin user performing operation")
    client_ip: str | None = Field(None, description="Client IP address")
    user_agent: str | None = Field(None, description="User agent string")
    success: bool = Field(..., description="Operation success status")
    records_affected: int = Field(default=0, description="Number of records affected")
    error_message: str | None = Field(None, description="Error message if failed")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional audit metadata"
    )

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str:  # pylint: disable=no-self-use
        """Serialize timestamps as ISO 8601 strings."""
        return value.isoformat()


class SecurityValidationResult(BaseModel):
    """Result of security validation for retention operations."""

    is_valid: bool = Field(..., description="Validation result")
    is_admin: bool = Field(default=False, description="User has admin privileges")
    session_valid: bool = Field(default=False, description="Session token is valid")
    user_id: str | None = Field(None, description="Validated user ID")
    error_message: str | None = Field(None, description="Validation error message")
    requires_additional_verification: bool = Field(
        default=False, description="Operation requires additional verification"
    )

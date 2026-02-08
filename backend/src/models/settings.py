"""
Settings Models with Enhanced Security

Comprehensive settings management models with security validation,
audit trail protection, and runtime input sanitization.
"""

import hashlib
import json
import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

# Shared regex patterns for validators
_SETTING_KEY_RE = re.compile(r"^[a-zA-Z0-9._]+$")
_USER_ID_RE = re.compile(r"^[a-zA-Z0-9\-_]+$")


def _validate_setting_key_value(v: str) -> str:
    """Validate setting key format and prevent injection."""
    if not v or not v.strip():
        raise ValueError("Setting key cannot be empty")
    if not _SETTING_KEY_RE.match(v):
        raise ValueError(
            "Setting key can only contain alphanumeric characters, dots, and underscores"
        )
    if ".." in v or v.startswith(".") or v.endswith("."):
        raise ValueError("Invalid setting key format")
    return v.strip()


def _validate_user_id_value(v: str) -> str:
    """Validate user ID format and prevent injection."""
    if not v or not v.strip():
        raise ValueError("User ID cannot be empty")
    if not _USER_ID_RE.match(v):
        raise ValueError("Invalid user ID format")
    return v.strip()


class SettingCategory(str, Enum):
    """Setting category definitions matching frontend UserSettings structure."""

    UI = "ui"  # Theme, language, timezone
    SECURITY = "security"  # Session settings, 2FA, password policies
    SYSTEM = "system"  # Auto-refresh, debug mode, data retention
    APPLICATIONS = "applications"  # Docker status refresh settings
    SERVERS = "servers"  # SSH connection settings, MCP config
    NOTIFICATIONS = "notifications"  # Alert preferences


class SettingScope(str, Enum):
    """Setting scope definitions for permission control."""

    SYSTEM = "system"
    USER_OVERRIDABLE = "user_overridable"


class SettingDataType(str, Enum):
    """Setting data type definitions for validation."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


class ChangeType(str, Enum):
    """Audit trail change type definitions."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class SettingValue(BaseModel):
    """Secure setting value with runtime validation and sanitization."""

    raw_value: str = Field(..., description="JSON-encoded setting value")
    data_type: SettingDataType = Field(..., description="Data type for validation")

    @field_validator("raw_value")
    @classmethod
    def validate_json_format(cls, v):
        """Validate that raw_value is valid JSON."""
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError:
            raise ValueError("Setting value must be valid JSON") from None

    @model_validator(mode="after")
    def validate_value_matches_type(self):
        """Validate that JSON value matches declared data type."""
        if not self.raw_value or not self.data_type:
            return self

        try:
            parsed_value = json.loads(self.raw_value)

            if self.data_type == SettingDataType.STRING and not isinstance(
                parsed_value, str
            ):
                raise ValueError(
                    f"Value must be a string for data_type {self.data_type}"
                )
            elif self.data_type == SettingDataType.NUMBER and not isinstance(
                parsed_value, (int, float)
            ):
                raise ValueError(
                    f"Value must be a number for data_type {self.data_type}"
                )
            elif self.data_type == SettingDataType.BOOLEAN and not isinstance(
                parsed_value, bool
            ):
                raise ValueError(
                    f"Value must be a boolean for data_type {self.data_type}"
                )
            elif self.data_type == SettingDataType.OBJECT and not isinstance(
                parsed_value, dict
            ):
                raise ValueError(
                    f"Value must be an object for data_type {self.data_type}"
                )
            elif self.data_type == SettingDataType.ARRAY and not isinstance(
                parsed_value, list
            ):
                raise ValueError(
                    f"Value must be an array for data_type {self.data_type}"
                )

        except json.JSONDecodeError:
            raise ValueError("Setting value must be valid JSON") from None

        return self

    def get_parsed_value(self) -> Any:
        """Get the parsed Python value from JSON."""
        return json.loads(self.raw_value)

    def get_checksum(self) -> str:
        """Generate checksum for audit trail integrity protection."""
        return hashlib.sha256(self.raw_value.encode("utf-8")).hexdigest()


class SystemSetting(BaseModel):
    """System setting with comprehensive security validation."""

    id: int | None = Field(None, description="Database ID")
    setting_key: str = Field(
        ..., min_length=1, max_length=255, description="Hierarchical setting key"
    )
    setting_value: SettingValue = Field(..., description="Current setting value")
    default_value: SettingValue = Field(
        ..., description="Factory default value for reset"
    )
    category: SettingCategory = Field(..., description="Setting category")
    scope: SettingScope = Field(..., description="Setting scope for access control")
    data_type: SettingDataType = Field(..., description="Data type for validation")
    is_admin_only: bool = Field(default=True, description="Requires admin privileges")
    description: str | None = Field(
        None, max_length=1000, description="Human-readable description"
    )
    validation_rules: str | None = Field(None, description="JSON schema for validation")
    created_at: str | None = Field(None, description="Creation timestamp")
    updated_at: str | None = Field(None, description="Last update timestamp")
    updated_by: str | None = Field(None, description="User ID who last modified")
    version: int = Field(default=1, ge=1, description="Version for optimistic locking")

    @field_validator("setting_key")
    @classmethod
    def validate_setting_key(cls, v):
        return _validate_setting_key_value(v)

    @field_validator("validation_rules")
    @classmethod
    def validate_json_schema(cls, v):
        """Validate that validation_rules is valid JSON if provided."""
        if v is None:
            return v
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError:
            raise ValueError("Validation rules must be valid JSON") from None

    @model_validator(mode="after")
    def validate_consistency(self):
        """Validate consistency between fields."""
        if self.setting_value and self.data_type:
            # Ensure setting_value data_type matches the declared data_type
            if self.setting_value.data_type != self.data_type:
                raise ValueError(
                    "Setting value data type must match declared data type"
                )

        return self


class UserSetting(BaseModel):
    """User setting override with security validation."""

    id: int | None = Field(None, description="Database ID")
    user_id: str = Field(..., min_length=1, description="User ID")
    setting_key: str = Field(
        ..., min_length=1, max_length=255, description="Setting key"
    )
    setting_value: SettingValue = Field(
        ..., description="Setting value with validation"
    )
    category: SettingCategory = Field(..., description="Setting category")
    is_override: bool = Field(default=True, description="Is override of system default")
    created_at: str | None = Field(None, description="Creation timestamp")
    updated_at: str | None = Field(None, description="Last update timestamp")
    version: int = Field(default=1, ge=1, description="Version for optimistic locking")

    @field_validator("setting_key")
    @classmethod
    def validate_setting_key(cls, v):
        return _validate_setting_key_value(v)

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v):
        return _validate_user_id_value(v)


class SettingsAuditEntry(BaseModel):
    """Audit entry with integrity protection and enhanced security."""

    id: int | None = Field(None, description="Database ID")
    table_name: str = Field(..., description="Table that was modified")
    record_id: int = Field(..., description="ID of the modified record")
    user_id: str | None = Field(None, description="User who made the change")
    setting_key: str = Field(..., description="Setting key that changed")
    old_value: str | None = Field(None, description="Previous value")
    new_value: str = Field(..., description="New value")
    change_type: ChangeType = Field(..., description="Type of change")
    change_reason: str | None = Field(
        None, max_length=500, description="Reason for change"
    )
    client_ip: str | None = Field(None, description="Client IP address")
    user_agent: str | None = Field(None, description="Client user agent")
    created_at: str | None = Field(None, description="Audit timestamp")
    checksum: str | None = Field(None, description="Integrity checksum")

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v):
        """Validate table name to prevent injection."""
        allowed_tables = {"system_settings", "user_settings"}
        if v not in allowed_tables:
            raise ValueError(f"Invalid table name. Must be one of: {allowed_tables}")
        return v

    @field_validator("setting_key")
    @classmethod
    def validate_setting_key(cls, v):
        return _validate_setting_key_value(v)

    def generate_checksum(self) -> str:
        """Generate integrity checksum for audit entry."""
        data = f"{self.table_name}:{self.record_id}:{self.setting_key}:{self.old_value}:{self.new_value}:{self.change_type}:{self.created_at}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()


class SettingsRequest(BaseModel):
    """Request for settings operations with security validation."""

    user_id: str = Field(..., min_length=1, description="Requesting user ID")
    category: SettingCategory | None = Field(None, description="Filter by category")
    setting_keys: list[str] | None = Field(None, description="Specific setting keys")
    include_system_defaults: bool = Field(
        default=True, description="Include system defaults"
    )
    include_user_overrides: bool = Field(
        default=True, description="Include user overrides"
    )

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v):
        return _validate_user_id_value(v)

    @field_validator("setting_keys")
    @classmethod
    def validate_setting_keys(cls, v):
        """Validate setting keys format and prevent injection."""
        if not v:
            return v

        validated_keys = []
        for key in v:
            if not key or not key.strip():
                continue

            if not _SETTING_KEY_RE.match(key):
                raise ValueError(f"Invalid setting key format: {key}")

            validated_keys.append(key.strip())

        return validated_keys if validated_keys else None


class SettingsUpdateRequest(BaseModel):
    """Request for updating settings with security validation."""

    user_id: str = Field(..., min_length=1, description="Requesting user ID")
    settings: dict[str, Any] = Field(..., description="Settings to update")
    change_reason: str | None = Field(
        None, max_length=500, description="Reason for change"
    )
    client_ip: str | None = Field(None, description="Client IP address")
    user_agent: str | None = Field(None, description="Client user agent")

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v):
        return _validate_user_id_value(v)

    @field_validator("settings")
    @classmethod
    def validate_settings(cls, v):
        """Validate settings dictionary format."""
        if not v or not isinstance(v, dict):
            raise ValueError("Settings must be a non-empty dictionary")

        validated_settings = {}
        for key, value in v.items():
            if not _SETTING_KEY_RE.match(key):
                raise ValueError(f"Invalid setting key format: {key}")

            try:
                json.dumps(value)
                validated_settings[key] = value
            except (TypeError, ValueError):
                raise ValueError(
                    f"Setting value for {key} must be JSON serializable"
                ) from None

        return validated_settings


class SettingsResponse(BaseModel):
    """Response for settings operations with comprehensive data."""

    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: dict[str, Any] | None = Field(None, description="Response data")
    error: str | None = Field(None, description="Error code if failed")
    audit_id: int | None = Field(None, description="Audit entry ID")
    checksum: str | None = Field(None, description="Response integrity checksum")

    def generate_checksum(self) -> str:
        """Generate integrity checksum for response."""
        data_str = json.dumps(self.data, sort_keys=True) if self.data else ""
        content = f"{self.success}:{self.message}:{data_str}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


class SettingsValidationResult(BaseModel):
    """Result of settings validation with security details."""

    is_valid: bool = Field(..., description="Overall validation result")
    validated_settings: dict[str, Any] = Field(
        default_factory=dict, description="Successfully validated settings"
    )
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    security_violations: list[str] = Field(
        default_factory=list, description="Security violations detected"
    )
    admin_required: list[str] = Field(
        default_factory=list, description="Settings requiring admin privileges"
    )

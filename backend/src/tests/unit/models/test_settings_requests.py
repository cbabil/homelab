"""
Unit tests for models/settings.py - Request/Response models

Tests SettingsAuditEntry, SettingsRequest, SettingsUpdateRequest,
SettingsResponse, and SettingsValidationResult models.
"""

import pytest
from pydantic import ValidationError

from models.settings import (
    ChangeType,
    SettingsAuditEntry,
    SettingsRequest,
    SettingsUpdateRequest,
    SettingsResponse,
    SettingsValidationResult,
)


class TestSettingsAuditEntry:
    """Tests for SettingsAuditEntry model."""

    def test_required_fields(self):
        """Test required fields."""
        entry = SettingsAuditEntry(
            table_name="system_settings",
            record_id=1,
            setting_key="ui.theme",
            new_value='"dark"',
            change_type=ChangeType.UPDATE,
        )
        assert entry.table_name == "system_settings"
        assert entry.record_id == 1

    def test_invalid_table_name(self):
        """Test invalid table name."""
        with pytest.raises(ValidationError) as exc_info:
            SettingsAuditEntry(
                table_name="users",  # Invalid
                record_id=1,
                setting_key="ui.theme",
                new_value='"dark"',
                change_type=ChangeType.UPDATE,
            )
        assert "Invalid table name" in str(exc_info.value)

    def test_setting_key_empty(self):
        """Test empty setting key."""
        with pytest.raises(ValidationError) as exc_info:
            SettingsAuditEntry(
                table_name="system_settings",
                record_id=1,
                setting_key="",
                new_value='"dark"',
                change_type=ChangeType.UPDATE,
            )
        assert "Setting key cannot be empty" in str(exc_info.value)

    def test_setting_key_invalid_chars(self):
        """Test setting key with invalid characters."""
        with pytest.raises(ValidationError) as exc_info:
            SettingsAuditEntry(
                table_name="system_settings",
                record_id=1,
                setting_key="ui@theme",
                new_value='"dark"',
                change_type=ChangeType.UPDATE,
            )
        assert "alphanumeric" in str(exc_info.value)

    def test_generate_checksum(self):
        """Test checksum generation."""
        entry = SettingsAuditEntry(
            table_name="system_settings",
            record_id=1,
            setting_key="ui.theme",
            old_value='"light"',
            new_value='"dark"',
            change_type=ChangeType.UPDATE,
            created_at="2024-01-15T10:00:00Z",
        )
        checksum = entry.generate_checksum()
        assert isinstance(checksum, str)
        assert len(checksum) == 64


class TestSettingsRequest:
    """Tests for SettingsRequest model."""

    def test_required_fields(self):
        """Test required fields."""
        request = SettingsRequest(user_id="user-123")
        assert request.user_id == "user-123"
        assert request.include_system_defaults is True
        assert request.include_user_overrides is True

    def test_user_id_empty(self):
        """Test empty user ID."""
        with pytest.raises(ValidationError) as exc_info:
            SettingsRequest(user_id="   ")
        assert "User ID cannot be empty" in str(exc_info.value)

    def test_user_id_invalid_chars(self):
        """Test invalid user ID format."""
        with pytest.raises(ValidationError) as exc_info:
            SettingsRequest(user_id="user@invalid")
        assert "Invalid user ID" in str(exc_info.value)

    def test_setting_keys_none(self):
        """Test setting_keys None is accepted."""
        request = SettingsRequest(user_id="user-123", setting_keys=None)
        assert request.setting_keys is None

    def test_setting_keys_validation(self):
        """Test setting keys validation."""
        request = SettingsRequest(
            user_id="user-123",
            setting_keys=["ui.theme", "ui.language"],
        )
        assert request.setting_keys == ["ui.theme", "ui.language"]

    def test_setting_keys_invalid(self):
        """Test invalid setting keys."""
        with pytest.raises(ValidationError) as exc_info:
            SettingsRequest(
                user_id="user-123",
                setting_keys=["valid.key", "invalid@key"],
            )
        assert "Invalid setting key format" in str(exc_info.value)

    def test_setting_keys_empty_filtered(self):
        """Test empty setting keys are filtered."""
        request = SettingsRequest(
            user_id="user-123",
            setting_keys=["", "  ", "valid.key"],
        )
        assert request.setting_keys == ["valid.key"]

    def test_setting_keys_all_empty(self):
        """Test all empty setting keys returns None."""
        request = SettingsRequest(
            user_id="user-123",
            setting_keys=["", "  "],
        )
        assert request.setting_keys is None


class TestSettingsUpdateRequest:
    """Tests for SettingsUpdateRequest model."""

    def test_required_fields(self):
        """Test required fields."""
        request = SettingsUpdateRequest(
            user_id="user-123",
            settings={"ui.theme": "dark"},
        )
        assert request.user_id == "user-123"
        assert request.settings == {"ui.theme": "dark"}

    def test_user_id_empty(self):
        """Test empty user ID."""
        with pytest.raises(ValidationError) as exc_info:
            SettingsUpdateRequest(
                user_id="   ",
                settings={"ui.theme": "dark"},
            )
        assert "User ID cannot be empty" in str(exc_info.value)

    def test_user_id_invalid_chars(self):
        """Test invalid user ID format."""
        with pytest.raises(ValidationError) as exc_info:
            SettingsUpdateRequest(
                user_id="user@invalid",
                settings={"ui.theme": "dark"},
            )
        assert "Invalid user ID" in str(exc_info.value)

    def test_empty_settings(self):
        """Test empty settings dictionary."""
        with pytest.raises(ValidationError) as exc_info:
            SettingsUpdateRequest(user_id="user-123", settings={})
        assert "non-empty dictionary" in str(exc_info.value)

    def test_invalid_setting_key(self):
        """Test invalid setting key in settings."""
        with pytest.raises(ValidationError) as exc_info:
            SettingsUpdateRequest(
                user_id="user-123",
                settings={"invalid@key": "value"},
            )
        assert "Invalid setting key format" in str(exc_info.value)

    def test_non_serializable_value(self):
        """Test non-JSON-serializable value."""
        with pytest.raises(ValidationError) as exc_info:
            SettingsUpdateRequest(
                user_id="user-123",
                settings={"valid.key": object()},
            )
        assert "JSON serializable" in str(exc_info.value)


class TestSettingsResponse:
    """Tests for SettingsResponse model."""

    def test_required_fields(self):
        """Test required fields."""
        response = SettingsResponse(success=True, message="OK")
        assert response.success is True
        assert response.message == "OK"

    def test_generate_checksum(self):
        """Test checksum generation."""
        response = SettingsResponse(
            success=True,
            message="Settings retrieved",
            data={"ui.theme": "dark"},
        )
        checksum = response.generate_checksum()
        assert isinstance(checksum, str)
        assert len(checksum) == 64

    def test_generate_checksum_no_data(self):
        """Test checksum generation without data."""
        response = SettingsResponse(success=False, message="Error")
        checksum = response.generate_checksum()
        assert isinstance(checksum, str)


class TestSettingsValidationResult:
    """Tests for SettingsValidationResult model."""

    def test_required_fields(self):
        """Test required fields."""
        result = SettingsValidationResult(is_valid=True)
        assert result.is_valid is True

    def test_default_values(self):
        """Test default values."""
        result = SettingsValidationResult(is_valid=False)
        assert result.validated_settings == {}
        assert result.errors == []
        assert result.warnings == []
        assert result.security_violations == []
        assert result.admin_required == []

    def test_all_fields(self):
        """Test all fields populated."""
        result = SettingsValidationResult(
            is_valid=False,
            validated_settings={"ui.theme": "dark"},
            errors=["Invalid value for timeout"],
            warnings=["Setting will be deprecated"],
            security_violations=["Attempted path traversal"],
            admin_required=["security.mfa"],
        )
        assert result.validated_settings == {"ui.theme": "dark"}
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert len(result.security_violations) == 1
        assert len(result.admin_required) == 1

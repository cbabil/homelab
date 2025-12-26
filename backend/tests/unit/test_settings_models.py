"""
Unit Tests for Settings Models

Comprehensive tests for settings models including validation,
security constraints, and data integrity protection.
"""

import json
import pytest
from pydantic import ValidationError
from models.settings import (
    SystemSetting, UserSetting, SettingsAuditEntry, SettingValue,
    SettingsRequest, SettingsUpdateRequest, SettingsResponse,
    SettingsValidationResult, SettingCategory, SettingScope,
    SettingDataType, ChangeType
)


class TestSettingValue:
    """Test SettingValue model validation and security."""

    def test_valid_string_value(self):
        """Test valid string value creation."""
        value = SettingValue(
            raw_value='"test_string"',
            data_type=SettingDataType.STRING
        )
        assert value.get_parsed_value() == "test_string"
        assert len(value.get_checksum()) == 64  # SHA256 hex length

    def test_valid_number_value(self):
        """Test valid number value creation."""
        value = SettingValue(
            raw_value='42',
            data_type=SettingDataType.NUMBER
        )
        assert value.get_parsed_value() == 42

    def test_valid_boolean_value(self):
        """Test valid boolean value creation."""
        value = SettingValue(
            raw_value='true',
            data_type=SettingDataType.BOOLEAN
        )
        assert value.get_parsed_value() is True

    def test_valid_object_value(self):
        """Test valid object value creation."""
        obj = {"key": "value", "count": 42}
        value = SettingValue(
            raw_value=json.dumps(obj),
            data_type=SettingDataType.OBJECT
        )
        assert value.get_parsed_value() == obj

    def test_valid_array_value(self):
        """Test valid array value creation."""
        arr = ["item1", "item2", 42]
        value = SettingValue(
            raw_value=json.dumps(arr),
            data_type=SettingDataType.ARRAY
        )
        assert value.get_parsed_value() == arr

    def test_invalid_json_format(self):
        """Test invalid JSON format rejection."""
        with pytest.raises(ValidationError) as exc_info:
            SettingValue(
                raw_value='invalid_json',
                data_type=SettingDataType.STRING
            )
        assert "valid JSON" in str(exc_info.value)

    def test_type_mismatch_string(self):
        """Test type mismatch detection for string."""
        with pytest.raises(ValidationError) as exc_info:
            SettingValue(
                raw_value='42',  # Number value
                data_type=SettingDataType.STRING  # String type
            )
        assert "must be a string" in str(exc_info.value)

    def test_type_mismatch_number(self):
        """Test type mismatch detection for number."""
        with pytest.raises(ValidationError) as exc_info:
            SettingValue(
                raw_value='"string"',  # String value
                data_type=SettingDataType.NUMBER  # Number type
            )
        assert "must be a number" in str(exc_info.value)

    def test_type_mismatch_boolean(self):
        """Test type mismatch detection for boolean."""
        with pytest.raises(ValidationError) as exc_info:
            SettingValue(
                raw_value='"string"',  # String value
                data_type=SettingDataType.BOOLEAN  # Boolean type
            )
        assert "must be a boolean" in str(exc_info.value)

    def test_checksum_consistency(self):
        """Test checksum generation consistency."""
        value1 = SettingValue(
            raw_value='"test"',
            data_type=SettingDataType.STRING
        )
        value2 = SettingValue(
            raw_value='"test"',
            data_type=SettingDataType.STRING
        )
        assert value1.get_checksum() == value2.get_checksum()

    def test_checksum_uniqueness(self):
        """Test different values produce different checksums."""
        value1 = SettingValue(
            raw_value='"test1"',
            data_type=SettingDataType.STRING
        )
        value2 = SettingValue(
            raw_value='"test2"',
            data_type=SettingDataType.STRING
        )
        assert value1.get_checksum() != value2.get_checksum()


class TestSystemSetting:
    """Test SystemSetting model validation and security."""

    def test_valid_system_setting(self):
        """Test valid system setting creation."""
        setting_value = SettingValue(
            raw_value='"test_value"',
            data_type=SettingDataType.STRING
        )
        setting = SystemSetting(
            setting_key="ui.theme",
            setting_value=setting_value,
            category=SettingCategory.UI,
            scope=SettingScope.USER_OVERRIDABLE,
            data_type=SettingDataType.STRING,
            description="UI theme setting"
        )
        assert setting.setting_key == "ui.theme"
        assert setting.is_admin_only is True  # Default value

    def test_setting_key_validation_valid(self):
        """Test valid setting key formats."""
        valid_keys = [
            "ui.theme",
            "system.timeout",
            "security.max_attempts",
            "retention.log_days"
        ]
        for key in valid_keys:
            setting_value = SettingValue(
                raw_value='"test"',
                data_type=SettingDataType.STRING
            )
            setting = SystemSetting(
                setting_key=key,
                setting_value=setting_value,
                category=SettingCategory.UI,
                scope=SettingScope.USER_OVERRIDABLE,
                data_type=SettingDataType.STRING
            )
            assert setting.setting_key == key

    def test_setting_key_validation_invalid(self):
        """Test invalid setting key format rejection."""
        invalid_keys = [
            "",  # Empty
            "ui..theme",  # Double dots
            ".ui.theme",  # Leading dot
            "ui.theme.",  # Trailing dot
            "ui/theme",  # Invalid character
            "ui theme",  # Space
            "ui;theme",  # SQL injection attempt
            "ui'theme",  # SQL injection attempt
        ]

        setting_value = SettingValue(
            raw_value='"test"',
            data_type=SettingDataType.STRING
        )

        for key in invalid_keys:
            with pytest.raises(ValidationError):
                SystemSetting(
                    setting_key=key,
                    setting_value=setting_value,
                    category=SettingCategory.UI,
                    scope=SettingScope.USER_OVERRIDABLE,
                    data_type=SettingDataType.STRING
                )

    def test_data_type_consistency(self):
        """Test data type consistency between fields."""
        setting_value = SettingValue(
            raw_value='"test"',
            data_type=SettingDataType.STRING
        )

        # Valid - matching data types
        setting = SystemSetting(
            setting_key="ui.theme",
            setting_value=setting_value,
            category=SettingCategory.UI,
            scope=SettingScope.USER_OVERRIDABLE,
            data_type=SettingDataType.STRING
        )
        assert setting.data_type == setting.setting_value.data_type

    def test_data_type_mismatch(self):
        """Test data type mismatch rejection."""
        setting_value = SettingValue(
            raw_value='"test"',
            data_type=SettingDataType.STRING
        )

        with pytest.raises(ValidationError) as exc_info:
            SystemSetting(
                setting_key="ui.theme",
                setting_value=setting_value,
                category=SettingCategory.UI,
                scope=SettingScope.USER_OVERRIDABLE,
                data_type=SettingDataType.NUMBER  # Mismatch
            )
        assert "data type must match" in str(exc_info.value)

    def test_validation_rules_json(self):
        """Test validation rules JSON format."""
        setting_value = SettingValue(
            raw_value='"test"',
            data_type=SettingDataType.STRING
        )

        # Valid JSON
        setting = SystemSetting(
            setting_key="ui.theme",
            setting_value=setting_value,
            category=SettingCategory.UI,
            scope=SettingScope.USER_OVERRIDABLE,
            data_type=SettingDataType.STRING,
            validation_rules='{"pattern": "^[a-z]+$"}'
        )
        assert setting.validation_rules == '{"pattern": "^[a-z]+$"}'

    def test_validation_rules_invalid_json(self):
        """Test invalid validation rules JSON rejection."""
        setting_value = SettingValue(
            raw_value='"test"',
            data_type=SettingDataType.STRING
        )

        with pytest.raises(ValidationError) as exc_info:
            SystemSetting(
                setting_key="ui.theme",
                setting_value=setting_value,
                category=SettingCategory.UI,
                scope=SettingScope.USER_OVERRIDABLE,
                data_type=SettingDataType.STRING,
                validation_rules='invalid json'
            )
        assert "valid JSON" in str(exc_info.value)


class TestUserSetting:
    """Test UserSetting model validation and security."""

    def test_valid_user_setting(self):
        """Test valid user setting creation."""
        setting_value = SettingValue(
            raw_value='"dark"',
            data_type=SettingDataType.STRING
        )
        setting = UserSetting(
            user_id="user_123",
            setting_key="ui.theme",
            setting_value=setting_value,
            category=SettingCategory.UI
        )
        assert setting.user_id == "user_123"
        assert setting.is_override is True

    def test_user_id_validation_valid(self):
        """Test valid user ID formats."""
        valid_ids = [
            "user_123",
            "admin",
            "test-user",
            "user123",
            "uuid-1234-5678"
        ]

        setting_value = SettingValue(
            raw_value='"test"',
            data_type=SettingDataType.STRING
        )

        for user_id in valid_ids:
            setting = UserSetting(
                user_id=user_id,
                setting_key="ui.theme",
                setting_value=setting_value,
                category=SettingCategory.UI
            )
            assert setting.user_id == user_id

    def test_user_id_validation_invalid(self):
        """Test invalid user ID format rejection."""
        invalid_ids = [
            "",  # Empty
            "user/123",  # Invalid character
            "user;123",  # SQL injection attempt
            "user'123",  # SQL injection attempt
            "user 123",  # Space
        ]

        setting_value = SettingValue(
            raw_value='"test"',
            data_type=SettingDataType.STRING
        )

        for user_id in invalid_ids:
            with pytest.raises(ValidationError):
                UserSetting(
                    user_id=user_id,
                    setting_key="ui.theme",
                    setting_value=setting_value,
                    category=SettingCategory.UI
                )


class TestSettingsAuditEntry:
    """Test SettingsAuditEntry model validation and security."""

    def test_valid_audit_entry(self):
        """Test valid audit entry creation."""
        entry = SettingsAuditEntry(
            table_name="system_settings",
            record_id=1,
            user_id="admin",
            setting_key="ui.theme",
            old_value='"light"',
            new_value='"dark"',
            change_type=ChangeType.UPDATE,
            created_at="2023-01-01T00:00:00Z"
        )
        assert entry.table_name == "system_settings"
        checksum = entry.generate_checksum()
        assert len(checksum) == 64  # SHA256 hex length

    def test_table_name_validation(self):
        """Test table name validation."""
        # Valid table names
        valid_tables = ["system_settings", "user_settings"]
        for table in valid_tables:
            entry = SettingsAuditEntry(
                table_name=table,
                record_id=1,
                user_id="admin",
                setting_key="ui.theme",
                old_value='"light"',
                new_value='"dark"',
                change_type=ChangeType.UPDATE
            )
            assert entry.table_name == table

    def test_table_name_validation_invalid(self):
        """Test invalid table name rejection."""
        invalid_tables = [
            "invalid_table",
            "users; DROP TABLE users;",
            "",
            "system_settings' OR 1=1--"
        ]

        for table in invalid_tables:
            with pytest.raises(ValidationError):
                SettingsAuditEntry(
                    table_name=table,
                    record_id=1,
                    user_id="admin",
                    setting_key="ui.theme",
                    old_value='"light"',
                    new_value='"dark"',
                    change_type=ChangeType.UPDATE
                )

    def test_checksum_generation(self):
        """Test audit entry checksum generation."""
        entry = SettingsAuditEntry(
            table_name="system_settings",
            record_id=1,
            user_id="admin",
            setting_key="ui.theme",
            old_value='"light"',
            new_value='"dark"',
            change_type=ChangeType.UPDATE,
            created_at="2023-01-01T00:00:00Z"
        )

        checksum1 = entry.generate_checksum()
        checksum2 = entry.generate_checksum()
        assert checksum1 == checksum2  # Consistency

        # Different entry should have different checksum
        entry2 = SettingsAuditEntry(
            table_name="system_settings",
            record_id=2,  # Different record_id
            user_id="admin",
            setting_key="ui.theme",
            old_value='"light"',
            new_value='"dark"',
            change_type=ChangeType.UPDATE,
            created_at="2023-01-01T00:00:00Z"
        )

        assert entry.generate_checksum() != entry2.generate_checksum()


class TestSettingsRequest:
    """Test SettingsRequest model validation and security."""

    def test_valid_settings_request(self):
        """Test valid settings request creation."""
        request = SettingsRequest(
            user_id="user_123",
            category=SettingCategory.UI,
            setting_keys=["ui.theme", "ui.language"],
            include_system_defaults=True,
            include_user_overrides=True
        )
        assert request.user_id == "user_123"
        assert len(request.setting_keys) == 2

    def test_setting_keys_validation(self):
        """Test setting keys validation."""
        # Valid keys should pass
        valid_keys = ["ui.theme", "system.timeout", "security.max_attempts"]
        request = SettingsRequest(
            user_id="user_123",
            setting_keys=valid_keys
        )
        assert request.setting_keys == valid_keys

    def test_setting_keys_validation_invalid(self):
        """Test invalid setting keys rejection."""
        invalid_keys = ["ui/theme", "ui;DROP", "ui'theme"]

        with pytest.raises(ValidationError):
            SettingsRequest(
                user_id="user_123",
                setting_keys=invalid_keys
            )


class TestSettingsUpdateRequest:
    """Test SettingsUpdateRequest model validation and security."""

    def test_valid_update_request(self):
        """Test valid update request creation."""
        settings = {
            "ui.theme": "dark",
            "ui.language": "en",
            "system.timeout": 30
        }
        request = SettingsUpdateRequest(
            user_id="user_123",
            settings=settings,
            change_reason="User preference update"
        )
        assert request.user_id == "user_123"
        assert len(request.settings) == 3

    def test_settings_validation_json_serializable(self):
        """Test settings must be JSON serializable."""
        # Valid serializable values
        valid_settings = {
            "string_value": "test",
            "number_value": 42,
            "boolean_value": True,
            "object_value": {"key": "value"},
            "array_value": [1, 2, 3]
        }

        request = SettingsUpdateRequest(
            user_id="user_123",
            settings=valid_settings
        )
        assert len(request.settings) == 5

    def test_settings_validation_invalid_keys(self):
        """Test invalid setting keys rejection."""
        invalid_settings = {
            "ui/theme": "dark",  # Invalid character
            "ui;DROP": "value"   # SQL injection attempt
        }

        with pytest.raises(ValidationError):
            SettingsUpdateRequest(
                user_id="user_123",
                settings=invalid_settings
            )


class TestSettingsResponse:
    """Test SettingsResponse model validation and security."""

    def test_valid_response(self):
        """Test valid response creation."""
        response = SettingsResponse(
            success=True,
            message="Settings retrieved successfully",
            data={"ui.theme": "dark", "ui.language": "en"}
        )
        assert response.success is True
        checksum = response.generate_checksum()
        assert len(checksum) == 64

    def test_checksum_generation(self):
        """Test response checksum generation."""
        response = SettingsResponse(
            success=True,
            message="Test",
            data={"key": "value"}
        )

        checksum1 = response.generate_checksum()
        checksum2 = response.generate_checksum()
        assert checksum1 == checksum2  # Consistency

        # Different data should produce different checksum
        response2 = SettingsResponse(
            success=True,
            message="Test",
            data={"key": "different_value"}
        )
        assert response.generate_checksum() != response2.generate_checksum()


class TestSettingsValidationResult:
    """Test SettingsValidationResult model."""

    def test_valid_validation_result(self):
        """Test valid validation result creation."""
        result = SettingsValidationResult(
            is_valid=True,
            validated_settings={"ui.theme": "dark"},
            errors=["Error 1"],
            warnings=["Warning 1"],
            security_violations=["Violation 1"],
            admin_required=["ui.admin_setting"]
        )
        assert result.is_valid is True
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert len(result.security_violations) == 1
        assert len(result.admin_required) == 1

    def test_default_values(self):
        """Test default values for validation result."""
        result = SettingsValidationResult(is_valid=False)
        assert result.validated_settings == {}
        assert result.errors == []
        assert result.warnings == []
        assert result.security_violations == []
        assert result.admin_required == []
"""
Unit tests for models/settings.py - Core models

Tests settings enums, SettingValue, SystemSetting, and UserSetting models.
"""

import pytest
from pydantic import ValidationError

from models.settings import (
    ChangeType,
    SettingCategory,
    SettingDataType,
    SettingScope,
    SettingValue,
    SystemSetting,
    UserSetting,
)


class TestSettingCategory:
    """Tests for SettingCategory enum."""

    def test_category_values(self):
        """Test all category enum values."""
        assert SettingCategory.UI == "ui"
        assert SettingCategory.SECURITY == "security"
        assert SettingCategory.SYSTEM == "system"
        assert SettingCategory.APPLICATIONS == "applications"
        assert SettingCategory.SERVERS == "servers"
        assert SettingCategory.NOTIFICATIONS == "notifications"

    def test_category_is_string_enum(self):
        """Test that category values are strings."""
        for cat in SettingCategory:
            assert isinstance(cat.value, str)


class TestSettingScope:
    """Tests for SettingScope enum."""

    def test_scope_values(self):
        """Test all scope enum values."""
        assert SettingScope.SYSTEM == "system"
        assert SettingScope.USER_OVERRIDABLE == "user_overridable"


class TestSettingDataType:
    """Tests for SettingDataType enum."""

    def test_data_type_values(self):
        """Test all data type enum values."""
        assert SettingDataType.STRING == "string"
        assert SettingDataType.NUMBER == "number"
        assert SettingDataType.BOOLEAN == "boolean"
        assert SettingDataType.OBJECT == "object"
        assert SettingDataType.ARRAY == "array"


class TestChangeType:
    """Tests for ChangeType enum."""

    def test_change_type_values(self):
        """Test all change type enum values."""
        assert ChangeType.CREATE == "CREATE"
        assert ChangeType.UPDATE == "UPDATE"
        assert ChangeType.DELETE == "DELETE"


class TestSettingValue:
    """Tests for SettingValue model."""

    def test_string_value(self):
        """Test string value."""
        value = SettingValue(raw_value='"dark"', data_type=SettingDataType.STRING)
        assert value.get_parsed_value() == "dark"

    def test_number_value_int(self):
        """Test integer value."""
        value = SettingValue(raw_value="42", data_type=SettingDataType.NUMBER)
        assert value.get_parsed_value() == 42

    def test_number_value_float(self):
        """Test float value."""
        value = SettingValue(raw_value="3.14", data_type=SettingDataType.NUMBER)
        assert value.get_parsed_value() == 3.14

    def test_boolean_value_true(self):
        """Test boolean true value."""
        value = SettingValue(raw_value="true", data_type=SettingDataType.BOOLEAN)
        assert value.get_parsed_value() is True

    def test_boolean_value_false(self):
        """Test boolean false value."""
        value = SettingValue(raw_value="false", data_type=SettingDataType.BOOLEAN)
        assert value.get_parsed_value() is False

    def test_object_value(self):
        """Test object value."""
        value = SettingValue(
            raw_value='{"key": "value", "count": 5}', data_type=SettingDataType.OBJECT
        )
        assert value.get_parsed_value() == {"key": "value", "count": 5}

    def test_array_value(self):
        """Test array value."""
        value = SettingValue(raw_value="[1, 2, 3]", data_type=SettingDataType.ARRAY)
        assert value.get_parsed_value() == [1, 2, 3]

    def test_invalid_json(self):
        """Test invalid JSON raises error."""
        with pytest.raises(ValidationError) as exc_info:
            SettingValue(raw_value="not json", data_type=SettingDataType.STRING)
        assert "valid JSON" in str(exc_info.value)

    def test_type_mismatch_string(self):
        """Test type mismatch for string."""
        with pytest.raises(ValidationError) as exc_info:
            SettingValue(raw_value="123", data_type=SettingDataType.STRING)
        assert "must be a string" in str(exc_info.value)

    def test_type_mismatch_number(self):
        """Test type mismatch for number."""
        with pytest.raises(ValidationError) as exc_info:
            SettingValue(raw_value='"text"', data_type=SettingDataType.NUMBER)
        assert "must be a number" in str(exc_info.value)

    def test_type_mismatch_boolean(self):
        """Test type mismatch for boolean."""
        with pytest.raises(ValidationError) as exc_info:
            SettingValue(raw_value='"yes"', data_type=SettingDataType.BOOLEAN)
        assert "must be a boolean" in str(exc_info.value)

    def test_type_mismatch_object(self):
        """Test type mismatch for object."""
        with pytest.raises(ValidationError) as exc_info:
            SettingValue(raw_value="[1, 2]", data_type=SettingDataType.OBJECT)
        assert "must be an object" in str(exc_info.value)

    def test_type_mismatch_array(self):
        """Test type mismatch for array."""
        with pytest.raises(ValidationError) as exc_info:
            SettingValue(raw_value='{"key": "value"}', data_type=SettingDataType.ARRAY)
        assert "must be an array" in str(exc_info.value)

    def test_get_checksum(self):
        """Test checksum generation."""
        value = SettingValue(raw_value='"test"', data_type=SettingDataType.STRING)
        checksum = value.get_checksum()
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex


class TestSystemSetting:
    """Tests for SystemSetting model."""

    def test_setting_key_empty(self):
        """Test empty setting key."""
        with pytest.raises(ValidationError) as exc_info:
            SystemSetting(
                setting_key="",
                setting_value=SettingValue(
                    raw_value="true", data_type=SettingDataType.BOOLEAN
                ),
                default_value=SettingValue(
                    raw_value="true", data_type=SettingDataType.BOOLEAN
                ),
                category=SettingCategory.SYSTEM,
                scope=SettingScope.SYSTEM,
                data_type=SettingDataType.BOOLEAN,
            )
        assert "setting_key" in str(exc_info.value)

    def test_setting_key_whitespace_only(self):
        """Test whitespace-only setting key."""
        with pytest.raises(ValidationError) as exc_info:
            SystemSetting(
                setting_key="   ",
                setting_value=SettingValue(
                    raw_value="true", data_type=SettingDataType.BOOLEAN
                ),
                default_value=SettingValue(
                    raw_value="true", data_type=SettingDataType.BOOLEAN
                ),
                category=SettingCategory.SYSTEM,
                scope=SettingScope.SYSTEM,
                data_type=SettingDataType.BOOLEAN,
            )
        assert "Setting key cannot be empty" in str(exc_info.value)

    def test_setting_key_ends_with_dot(self):
        """Test setting key ending with dot."""
        with pytest.raises(ValidationError) as exc_info:
            SystemSetting(
                setting_key="test.setting.",
                setting_value=SettingValue(
                    raw_value="true", data_type=SettingDataType.BOOLEAN
                ),
                default_value=SettingValue(
                    raw_value="true", data_type=SettingDataType.BOOLEAN
                ),
                category=SettingCategory.SYSTEM,
                scope=SettingScope.SYSTEM,
                data_type=SettingDataType.BOOLEAN,
            )
        assert "Invalid setting key" in str(exc_info.value)

    def test_required_fields(self):
        """Test required fields."""
        setting = SystemSetting(
            setting_key="ui.theme",
            setting_value=SettingValue(
                raw_value='"dark"', data_type=SettingDataType.STRING
            ),
            default_value=SettingValue(
                raw_value='"light"', data_type=SettingDataType.STRING
            ),
            category=SettingCategory.UI,
            scope=SettingScope.USER_OVERRIDABLE,
            data_type=SettingDataType.STRING,
        )
        assert setting.setting_key == "ui.theme"
        assert setting.category == SettingCategory.UI

    def test_default_values(self):
        """Test default values."""
        setting = SystemSetting(
            setting_key="test.setting",
            setting_value=SettingValue(
                raw_value="true", data_type=SettingDataType.BOOLEAN
            ),
            default_value=SettingValue(
                raw_value="false", data_type=SettingDataType.BOOLEAN
            ),
            category=SettingCategory.SYSTEM,
            scope=SettingScope.SYSTEM,
            data_type=SettingDataType.BOOLEAN,
        )
        assert setting.id is None
        assert setting.is_admin_only is True
        assert setting.description is None
        assert setting.validation_rules is None
        assert setting.version == 1

    def test_setting_key_valid_dots(self):
        """Test valid setting key with dots."""
        setting = SystemSetting(
            setting_key="security.session.timeout",
            setting_value=SettingValue(
                raw_value="30", data_type=SettingDataType.NUMBER
            ),
            default_value=SettingValue(
                raw_value="30", data_type=SettingDataType.NUMBER
            ),
            category=SettingCategory.SECURITY,
            scope=SettingScope.SYSTEM,
            data_type=SettingDataType.NUMBER,
        )
        assert setting.setting_key == "security.session.timeout"

    def test_setting_key_valid_underscore(self):
        """Test valid setting key with underscores."""
        setting = SystemSetting(
            setting_key="system_debug_mode",
            setting_value=SettingValue(
                raw_value="false", data_type=SettingDataType.BOOLEAN
            ),
            default_value=SettingValue(
                raw_value="false", data_type=SettingDataType.BOOLEAN
            ),
            category=SettingCategory.SYSTEM,
            scope=SettingScope.SYSTEM,
            data_type=SettingDataType.BOOLEAN,
        )
        assert setting.setting_key == "system_debug_mode"

    def test_setting_key_invalid_chars(self):
        """Test invalid setting key with special chars."""
        with pytest.raises(ValidationError) as exc_info:
            SystemSetting(
                setting_key="test@setting",
                setting_value=SettingValue(
                    raw_value="true", data_type=SettingDataType.BOOLEAN
                ),
                default_value=SettingValue(
                    raw_value="true", data_type=SettingDataType.BOOLEAN
                ),
                category=SettingCategory.SYSTEM,
                scope=SettingScope.SYSTEM,
                data_type=SettingDataType.BOOLEAN,
            )
        assert "alphanumeric" in str(exc_info.value)

    def test_setting_key_path_traversal(self):
        """Test setting key with path traversal attempt."""
        with pytest.raises(ValidationError) as exc_info:
            SystemSetting(
                setting_key="test..setting",
                setting_value=SettingValue(
                    raw_value="true", data_type=SettingDataType.BOOLEAN
                ),
                default_value=SettingValue(
                    raw_value="true", data_type=SettingDataType.BOOLEAN
                ),
                category=SettingCategory.SYSTEM,
                scope=SettingScope.SYSTEM,
                data_type=SettingDataType.BOOLEAN,
            )
        assert "Invalid setting key" in str(exc_info.value)

    def test_setting_key_starts_with_dot(self):
        """Test setting key starting with dot."""
        with pytest.raises(ValidationError) as exc_info:
            SystemSetting(
                setting_key=".hidden",
                setting_value=SettingValue(
                    raw_value="true", data_type=SettingDataType.BOOLEAN
                ),
                default_value=SettingValue(
                    raw_value="true", data_type=SettingDataType.BOOLEAN
                ),
                category=SettingCategory.SYSTEM,
                scope=SettingScope.SYSTEM,
                data_type=SettingDataType.BOOLEAN,
            )
        assert "Invalid setting key" in str(exc_info.value)

    def test_data_type_mismatch(self):
        """Test data type mismatch between fields."""
        with pytest.raises(ValidationError) as exc_info:
            SystemSetting(
                setting_key="test.setting",
                setting_value=SettingValue(
                    raw_value="true", data_type=SettingDataType.BOOLEAN
                ),
                default_value=SettingValue(
                    raw_value="true", data_type=SettingDataType.BOOLEAN
                ),
                category=SettingCategory.SYSTEM,
                scope=SettingScope.SYSTEM,
                data_type=SettingDataType.STRING,
            )
        assert "data type must match" in str(exc_info.value)

    def test_validation_rules_none(self):
        """Test None validation rules are accepted."""
        setting = SystemSetting(
            setting_key="test.setting",
            setting_value=SettingValue(
                raw_value="50", data_type=SettingDataType.NUMBER
            ),
            default_value=SettingValue(
                raw_value="30", data_type=SettingDataType.NUMBER
            ),
            category=SettingCategory.SYSTEM,
            scope=SettingScope.SYSTEM,
            data_type=SettingDataType.NUMBER,
            validation_rules=None,
        )
        assert setting.validation_rules is None

    def test_validation_rules_valid_json(self):
        """Test valid JSON validation rules."""
        setting = SystemSetting(
            setting_key="test.setting",
            setting_value=SettingValue(
                raw_value="50", data_type=SettingDataType.NUMBER
            ),
            default_value=SettingValue(
                raw_value="30", data_type=SettingDataType.NUMBER
            ),
            category=SettingCategory.SYSTEM,
            scope=SettingScope.SYSTEM,
            data_type=SettingDataType.NUMBER,
            validation_rules='{"min": 1, "max": 100}',
        )
        assert setting.validation_rules == '{"min": 1, "max": 100}'

    def test_validation_rules_invalid_json(self):
        """Test invalid JSON validation rules."""
        with pytest.raises(ValidationError) as exc_info:
            SystemSetting(
                setting_key="test.setting",
                setting_value=SettingValue(
                    raw_value="50", data_type=SettingDataType.NUMBER
                ),
                default_value=SettingValue(
                    raw_value="30", data_type=SettingDataType.NUMBER
                ),
                category=SettingCategory.SYSTEM,
                scope=SettingScope.SYSTEM,
                data_type=SettingDataType.NUMBER,
                validation_rules="not json",
            )
        assert "Validation rules must be valid JSON" in str(exc_info.value)


class TestUserSetting:
    """Tests for UserSetting model."""

    def test_required_fields(self):
        """Test required fields."""
        setting = UserSetting(
            user_id="user-123",
            setting_key="ui.theme",
            setting_value=SettingValue(
                raw_value='"dark"', data_type=SettingDataType.STRING
            ),
            category=SettingCategory.UI,
        )
        assert setting.user_id == "user-123"
        assert setting.setting_key == "ui.theme"

    def test_user_id_validation_invalid(self):
        """Test invalid user ID format."""
        with pytest.raises(ValidationError) as exc_info:
            UserSetting(
                user_id="user@invalid",
                setting_key="ui.theme",
                setting_value=SettingValue(
                    raw_value='"dark"', data_type=SettingDataType.STRING
                ),
                category=SettingCategory.UI,
            )
        assert "Invalid user ID" in str(exc_info.value)

    def test_user_id_empty(self):
        """Test empty user ID."""
        with pytest.raises(ValidationError) as exc_info:
            UserSetting(
                user_id="   ",
                setting_key="ui.theme",
                setting_value=SettingValue(
                    raw_value='"dark"', data_type=SettingDataType.STRING
                ),
                category=SettingCategory.UI,
            )
        assert "User ID cannot be empty" in str(exc_info.value)

    def test_setting_key_empty(self):
        """Test empty setting key."""
        with pytest.raises(ValidationError) as exc_info:
            UserSetting(
                user_id="user-123",
                setting_key="",
                setting_value=SettingValue(
                    raw_value='"dark"', data_type=SettingDataType.STRING
                ),
                category=SettingCategory.UI,
            )
        assert "setting_key" in str(exc_info.value)

    def test_setting_key_whitespace_only(self):
        """Test whitespace-only setting key."""
        with pytest.raises(ValidationError) as exc_info:
            UserSetting(
                user_id="user-123",
                setting_key="   ",
                setting_value=SettingValue(
                    raw_value='"dark"', data_type=SettingDataType.STRING
                ),
                category=SettingCategory.UI,
            )
        assert "Setting key cannot be empty" in str(exc_info.value)

    def test_setting_key_invalid_chars(self):
        """Test setting key with invalid characters."""
        with pytest.raises(ValidationError) as exc_info:
            UserSetting(
                user_id="user-123",
                setting_key="ui@theme",
                setting_value=SettingValue(
                    raw_value='"dark"', data_type=SettingDataType.STRING
                ),
                category=SettingCategory.UI,
            )
        assert "alphanumeric" in str(exc_info.value)

    def test_setting_key_path_traversal(self):
        """Test setting key with path traversal."""
        with pytest.raises(ValidationError) as exc_info:
            UserSetting(
                user_id="user-123",
                setting_key="ui..theme",
                setting_value=SettingValue(
                    raw_value='"dark"', data_type=SettingDataType.STRING
                ),
                category=SettingCategory.UI,
            )
        assert "Invalid setting key" in str(exc_info.value)

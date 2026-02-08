"""
Unit tests for services/settings_service.py - Value validation.

Tests _validate_setting_value method with various scenarios.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.settings import (
    SettingCategory,
    SettingDataType,
    SettingScope,
    SettingValue,
    SystemSetting,
)
from services.settings_service import SettingsService


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    return MagicMock()


@pytest.fixture
def mock_connection():
    """Create mock database connection."""
    conn = AsyncMock()
    conn.execute = AsyncMock()
    conn.commit = AsyncMock()
    conn.rollback = AsyncMock()
    return conn


@pytest.fixture
def settings_service(mock_db_service, mock_connection):
    """Create SettingsService with mocked dependencies."""
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_connection
    mock_context_manager.__aexit__.return_value = None
    mock_db_service.get_connection = MagicMock(return_value=mock_context_manager)

    with patch("services.settings_service.logger"):
        return SettingsService(mock_db_service)


@pytest.fixture
def sample_system_setting():
    """Create sample system setting for testing."""
    return SystemSetting(
        id=1,
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
        is_admin_only=False,
        description="UI theme setting",
        validation_rules=None,
        version=1,
    )


class TestValidateSettingValue:
    """Tests for _validate_setting_value method."""

    @pytest.mark.asyncio
    async def test_validate_setting_value_success(
        self, settings_service, sample_system_setting
    ):
        """_validate_setting_value should validate correct values."""
        with patch("services.settings_service.logger"):
            result = await settings_service._validate_setting_value(
                "ui.theme", "dark", sample_system_setting
            )
        assert result is not None
        assert result.get_parsed_value() == "dark"

    @pytest.mark.asyncio
    async def test_validate_setting_value_fetches_system_setting(
        self, settings_service, sample_system_setting
    ):
        """_validate_setting_value should fetch system setting if not provided."""
        mock_get_system_setting = AsyncMock(return_value=sample_system_setting)
        with (
            patch("services.settings_service.logger"),
            patch.object(
                settings_service, "get_system_setting", mock_get_system_setting
            ),
        ):
            result = await settings_service._validate_setting_value("ui.theme", "dark")
        assert result is not None
        mock_get_system_setting.assert_called_once_with("ui.theme")

    @pytest.mark.asyncio
    async def test_validate_setting_value_not_found(self, settings_service):
        """_validate_setting_value should raise for unknown setting."""
        with (
            patch("services.settings_service.logger"),
            patch.object(
                settings_service,
                "get_system_setting",
                new_callable=AsyncMock,
                return_value=None,
            ),
            pytest.raises(ValueError, match="System setting not found"),
        ):
            await settings_service._validate_setting_value("unknown.key", "value")

    @pytest.mark.asyncio
    async def test_validate_setting_value_with_json_schema(self, settings_service):
        """_validate_setting_value should validate against JSON schema."""
        system_setting = SystemSetting(
            id=1,
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
            is_admin_only=False,
            validation_rules='{"enum": ["light", "dark"]}',
            version=1,
        )
        with patch("services.settings_service.logger"):
            result = await settings_service._validate_setting_value(
                "ui.theme", "dark", system_setting
            )
        assert result is not None

    @pytest.mark.asyncio
    async def test_validate_setting_value_json_schema_violation(self, settings_service):
        """_validate_setting_value should reject invalid JSON schema values."""
        system_setting = SystemSetting(
            id=1,
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
            is_admin_only=False,
            validation_rules='{"enum": ["light", "dark"]}',
            version=1,
        )
        with (
            patch("services.settings_service.logger"),
            pytest.raises(ValueError, match="Value validation failed"),
        ):
            await settings_service._validate_setting_value(
                "ui.theme", "invalid_theme", system_setting
            )

    @pytest.mark.asyncio
    async def test_validate_setting_value_handles_error(
        self, settings_service, sample_system_setting
    ):
        """_validate_setting_value should raise on error."""
        with (
            patch("services.settings_service.logger") as mock_logger,
            patch.object(
                settings_service,
                "get_system_setting",
                new_callable=AsyncMock,
                side_effect=Exception("DB error"),
            ),
            pytest.raises(Exception),
        ):
            await settings_service._validate_setting_value("ui.theme", "dark")
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_validate_setting_value_jsonschema_import_error(
        self, settings_service
    ):
        """_validate_setting_value should handle jsonschema ImportError."""
        system_setting = SystemSetting(
            id=1,
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
            is_admin_only=False,
            validation_rules='{"enum": ["light", "dark"]}',
            version=1,
        )

        # Mock the import to raise ImportError
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "jsonschema":
                raise ImportError("jsonschema not installed")
            return original_import(name, *args, **kwargs)

        with (
            patch("services.settings_service.logger") as mock_logger,
            patch.object(builtins, "__import__", mock_import),
        ):
            result = await settings_service._validate_setting_value(
                "ui.theme", "dark", system_setting
            )

        # Should succeed but log a warning
        assert result is not None
        mock_logger.warning.assert_called_with(
            "jsonschema not available for advanced validation"
        )


class TestTokenRotationSettingsValidation:
    """Tests for agent token rotation settings validation."""

    @pytest.fixture
    def token_rotation_days_setting(self):
        """Create token rotation days setting for testing."""
        return SystemSetting(
            id=1,
            setting_key="agent.token_rotation_days",
            setting_value=SettingValue(raw_value="7", data_type=SettingDataType.NUMBER),
            default_value=SettingValue(raw_value="7", data_type=SettingDataType.NUMBER),
            category=SettingCategory.SECURITY,
            scope=SettingScope.SYSTEM,
            data_type=SettingDataType.NUMBER,
            is_admin_only=True,
            description="Days before agent token rotation (1-365)",
            validation_rules='{"type": "integer", "minimum": 1, "maximum": 365}',
            version=1,
        )

    @pytest.fixture
    def token_grace_period_setting(self):
        """Create token grace period setting for testing."""
        return SystemSetting(
            id=2,
            setting_key="agent.token_grace_period_minutes",
            setting_value=SettingValue(raw_value="5", data_type=SettingDataType.NUMBER),
            default_value=SettingValue(raw_value="5", data_type=SettingDataType.NUMBER),
            category=SettingCategory.SECURITY,
            scope=SettingScope.SYSTEM,
            data_type=SettingDataType.NUMBER,
            is_admin_only=True,
            description="Minutes to accept old token during rotation (1-60)",
            validation_rules='{"type": "integer", "minimum": 1, "maximum": 60}',
            version=1,
        )

    @pytest.mark.asyncio
    async def test_validate_rotation_days_valid_value(
        self, settings_service, token_rotation_days_setting
    ):
        """Test valid token rotation days value."""
        with patch("services.settings_service.logger"):
            result = await settings_service._validate_setting_value(
                "agent.token_rotation_days", 7, token_rotation_days_setting
            )
        assert result is not None
        assert result.get_parsed_value() == 7

    @pytest.mark.asyncio
    async def test_validate_rotation_days_minimum(
        self, settings_service, token_rotation_days_setting
    ):
        """Test minimum valid token rotation days value (1)."""
        with patch("services.settings_service.logger"):
            result = await settings_service._validate_setting_value(
                "agent.token_rotation_days", 1, token_rotation_days_setting
            )
        assert result is not None
        assert result.get_parsed_value() == 1

    @pytest.mark.asyncio
    async def test_validate_rotation_days_maximum(
        self, settings_service, token_rotation_days_setting
    ):
        """Test maximum valid token rotation days value (365)."""
        with patch("services.settings_service.logger"):
            result = await settings_service._validate_setting_value(
                "agent.token_rotation_days", 365, token_rotation_days_setting
            )
        assert result is not None
        assert result.get_parsed_value() == 365

    @pytest.mark.asyncio
    async def test_validate_rotation_days_below_minimum(
        self, settings_service, token_rotation_days_setting
    ):
        """Test token rotation days below minimum (0) is rejected."""
        with (
            patch("services.settings_service.logger"),
            pytest.raises(ValueError, match="Value validation failed"),
        ):
            await settings_service._validate_setting_value(
                "agent.token_rotation_days", 0, token_rotation_days_setting
            )

    @pytest.mark.asyncio
    async def test_validate_rotation_days_above_maximum(
        self, settings_service, token_rotation_days_setting
    ):
        """Test token rotation days above maximum (366) is rejected."""
        with (
            patch("services.settings_service.logger"),
            pytest.raises(ValueError, match="Value validation failed"),
        ):
            await settings_service._validate_setting_value(
                "agent.token_rotation_days", 366, token_rotation_days_setting
            )

    @pytest.mark.asyncio
    async def test_validate_grace_period_valid_value(
        self, settings_service, token_grace_period_setting
    ):
        """Test valid token grace period value."""
        with patch("services.settings_service.logger"):
            result = await settings_service._validate_setting_value(
                "agent.token_grace_period_minutes", 5, token_grace_period_setting
            )
        assert result is not None
        assert result.get_parsed_value() == 5

    @pytest.mark.asyncio
    async def test_validate_grace_period_minimum(
        self, settings_service, token_grace_period_setting
    ):
        """Test minimum valid grace period value (1)."""
        with patch("services.settings_service.logger"):
            result = await settings_service._validate_setting_value(
                "agent.token_grace_period_minutes", 1, token_grace_period_setting
            )
        assert result is not None
        assert result.get_parsed_value() == 1

    @pytest.mark.asyncio
    async def test_validate_grace_period_maximum(
        self, settings_service, token_grace_period_setting
    ):
        """Test maximum valid grace period value (60)."""
        with patch("services.settings_service.logger"):
            result = await settings_service._validate_setting_value(
                "agent.token_grace_period_minutes", 60, token_grace_period_setting
            )
        assert result is not None
        assert result.get_parsed_value() == 60

    @pytest.mark.asyncio
    async def test_validate_grace_period_below_minimum(
        self, settings_service, token_grace_period_setting
    ):
        """Test grace period below minimum (0) is rejected."""
        with (
            patch("services.settings_service.logger"),
            pytest.raises(ValueError, match="Value validation failed"),
        ):
            await settings_service._validate_setting_value(
                "agent.token_grace_period_minutes", 0, token_grace_period_setting
            )

    @pytest.mark.asyncio
    async def test_validate_grace_period_above_maximum(
        self, settings_service, token_grace_period_setting
    ):
        """Test grace period above maximum (61) is rejected."""
        with (
            patch("services.settings_service.logger"),
            pytest.raises(ValueError, match="Value validation failed"),
        ):
            await settings_service._validate_setting_value(
                "agent.token_grace_period_minutes", 61, token_grace_period_setting
            )

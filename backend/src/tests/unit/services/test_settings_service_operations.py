"""Unit tests for services/settings_service.py - CRUD operations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.auth import User, UserRole
from models.settings import (
    SettingCategory,
    SettingDataType,
    SettingScope,
    SettingsRequest,
    SettingsUpdateRequest,
    SettingsValidationResult,
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
def admin_user():
    """Create admin user for testing."""
    return User(
        id="admin-123",
        username="admin",
        email="admin@example.com",
        role=UserRole.ADMIN,
        last_login="2024-01-15T10:00:00+00:00",
        is_active=True,
    )


@pytest.fixture
def regular_user():
    """Create regular user for testing."""
    return User(
        id="user-456",
        username="regular",
        email="user@example.com",
        role=UserRole.USER,
        last_login="2024-01-15T10:00:00+00:00",
        is_active=True,
    )


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


class TestGetSettings:
    """Tests for get_settings method."""

    @pytest.mark.asyncio
    async def test_get_settings_success(self, settings_service, mock_connection):
        """get_settings should return settings from database."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                {
                    "setting_key": "ui.theme",
                    "setting_value": '"dark"',
                    "category": "ui",
                    "scope": "user_overridable",
                    "data_type": "string",
                    "is_admin_only": 0,
                }
            ]
        )
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        request = SettingsRequest(
            user_id="user-123",
            include_system_defaults=True,
            include_user_overrides=False,
        )
        with patch("services.settings_service.logger"):
            result = await settings_service.get_settings(request)
        assert result.success is True
        assert "settings" in result.data
        assert "ui.theme" in result.data["settings"]

    @pytest.mark.asyncio
    async def test_get_settings_with_category_filter(
        self, settings_service, mock_connection
    ):
        """get_settings should filter by category."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        request = SettingsRequest(
            user_id="user-123",
            category=SettingCategory.UI,
            include_system_defaults=True,
            include_user_overrides=False,
        )
        with patch("services.settings_service.logger"):
            result = await settings_service.get_settings(request)
        assert result.success is True
        assert "ui" in mock_connection.execute.call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_settings_with_specific_keys(
        self, settings_service, mock_connection
    ):
        """get_settings should filter by specific keys."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        request = SettingsRequest(
            user_id="user-123",
            setting_keys=["ui.theme", "ui.language"],
            include_system_defaults=True,
            include_user_overrides=False,
        )
        with patch("services.settings_service.logger"):
            result = await settings_service.get_settings(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_get_settings_admin_only_excluded_for_regular_user(
        self, settings_service, mock_connection, mock_db_service, regular_user
    ):
        """get_settings should exclude admin-only settings for regular users."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                {
                    "setting_key": "security.admin_setting",
                    "setting_value": '"secret"',
                    "category": "security",
                    "scope": "system",
                    "data_type": "string",
                    "is_admin_only": 1,
                }
            ]
        )
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        mock_db_service.get_user_by_id = AsyncMock(return_value=regular_user)
        request = SettingsRequest(
            user_id="user-456",
            include_system_defaults=True,
            include_user_overrides=False,
        )
        with patch("services.settings_service.logger"):
            result = await settings_service.get_settings(request)
        assert result.success is True
        assert "security.admin_setting" not in result.data.get("settings", {})

    @pytest.mark.asyncio
    async def test_get_settings_includes_user_overrides(
        self, settings_service, mock_connection
    ):
        """get_settings should include user overrides."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            side_effect=[
                [
                    {
                        "setting_key": "ui.theme",
                        "setting_value": '"light"',
                        "category": "ui",
                        "scope": "user_overridable",
                        "data_type": "string",
                        "is_admin_only": 0,
                    }
                ],
                [
                    {
                        "setting_key": "ui.theme",
                        "setting_value": '"dark"',
                        "category": "ui",
                        "data_type": "string",
                    }
                ],
            ]
        )
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        request = SettingsRequest(
            user_id="user-123",
            include_system_defaults=True,
            include_user_overrides=True,
        )
        with patch("services.settings_service.logger"):
            result = await settings_service.get_settings(request)
        assert result.success is True
        assert result.data["settings"]["ui.theme"]["source"] == "user_override"

    @pytest.mark.asyncio
    async def test_get_settings_handles_error(self, settings_service, mock_connection):
        """get_settings should handle errors gracefully."""
        mock_connection.execute = AsyncMock(side_effect=Exception("DB error"))
        request = SettingsRequest(user_id="user-123")
        with patch("services.settings_service.logger") as mock_logger:
            result = await settings_service.get_settings(request)
        assert result.success is False
        assert result.error == "GET_SETTINGS_ERROR"
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_get_settings_has_checksum(self, settings_service, mock_connection):
        """get_settings should include response checksum."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        request = SettingsRequest(
            user_id="user-123",
            include_system_defaults=True,
            include_user_overrides=False,
        )
        with patch("services.settings_service.logger"):
            result = await settings_service.get_settings(request)
        assert result.success is True
        assert result.checksum is not None

    @pytest.mark.asyncio
    async def test_get_settings_handles_invalid_system_setting_value(
        self, settings_service, mock_connection
    ):
        """get_settings should warn on invalid system setting value."""
        mock_cursor = AsyncMock()
        # Return a setting with invalid JSON value
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                {
                    "setting_key": "ui.theme",
                    "setting_value": "not valid json",
                    "category": "ui",
                    "scope": "user_overridable",
                    "data_type": "string",
                    "is_admin_only": 0,
                }
            ]
        )
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        request = SettingsRequest(
            user_id="user-123",
            include_system_defaults=True,
            include_user_overrides=False,
        )
        with patch("services.settings_service.logger") as mock_logger:
            result = await settings_service.get_settings(request)
        assert result.success is True
        # The invalid setting should be skipped with a warning
        mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_get_settings_with_user_override_category_filter(
        self, settings_service, mock_connection
    ):
        """get_settings should filter user overrides by category."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            side_effect=[
                # System settings
                [
                    {
                        "setting_key": "ui.theme",
                        "setting_value": '"light"',
                        "category": "ui",
                        "scope": "user_overridable",
                        "data_type": "string",
                        "is_admin_only": 0,
                    }
                ],
                # User overrides
                [
                    {
                        "setting_key": "ui.theme",
                        "setting_value": '"dark"',
                        "category": "ui",
                        "data_type": "string",
                    }
                ],
            ]
        )
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        request = SettingsRequest(
            user_id="user-123",
            category=SettingCategory.UI,
            include_system_defaults=True,
            include_user_overrides=True,
        )
        with patch("services.settings_service.logger"):
            result = await settings_service.get_settings(request)
        assert result.success is True
        # Verify the user overrides query includes category filter
        calls = mock_connection.execute.call_args_list
        assert len(calls) == 2
        # Second call should have category in the params
        assert "ui" in calls[1][0][1]

    @pytest.mark.asyncio
    async def test_get_settings_with_user_override_setting_keys_filter(
        self, settings_service, mock_connection
    ):
        """get_settings should filter user overrides by setting keys."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            side_effect=[
                # System settings
                [
                    {
                        "setting_key": "ui.theme",
                        "setting_value": '"light"',
                        "category": "ui",
                        "scope": "user_overridable",
                        "data_type": "string",
                        "is_admin_only": 0,
                    }
                ],
                # User overrides
                [
                    {
                        "setting_key": "ui.theme",
                        "setting_value": '"dark"',
                        "category": "ui",
                        "data_type": "string",
                    }
                ],
            ]
        )
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        request = SettingsRequest(
            user_id="user-123",
            setting_keys=["ui.theme", "ui.language"],
            include_system_defaults=True,
            include_user_overrides=True,
        )
        with patch("services.settings_service.logger"):
            result = await settings_service.get_settings(request)
        assert result.success is True
        # Verify the user overrides query includes setting_keys
        calls = mock_connection.execute.call_args_list
        assert len(calls) == 2
        # Second call params should include setting keys
        params = calls[1][0][1]
        assert "ui.theme" in params
        assert "ui.language" in params

    @pytest.mark.asyncio
    async def test_get_settings_handles_invalid_user_setting_value(
        self, settings_service, mock_connection
    ):
        """get_settings should warn on invalid user setting value."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            side_effect=[
                # System settings
                [
                    {
                        "setting_key": "ui.theme",
                        "setting_value": '"light"',
                        "category": "ui",
                        "scope": "user_overridable",
                        "data_type": "string",
                        "is_admin_only": 0,
                    }
                ],
                # User overrides with invalid JSON
                [
                    {
                        "setting_key": "ui.theme",
                        "setting_value": "invalid json",
                        "category": "ui",
                        "data_type": "string",
                    }
                ],
            ]
        )
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        request = SettingsRequest(
            user_id="user-123",
            include_system_defaults=True,
            include_user_overrides=True,
        )
        with patch("services.settings_service.logger") as mock_logger:
            result = await settings_service.get_settings(request)
        assert result.success is True
        # The invalid setting should be skipped with a warning
        mock_logger.warning.assert_called()


class TestValidateSettings:
    """Tests for validate_settings method (error handling)."""

    @pytest.mark.asyncio
    async def test_validate_settings_unknown_setting(self, settings_service):
        """validate_settings should report error for unknown setting."""
        with (
            patch("services.settings_service.logger"),
            patch.object(
                settings_service,
                "get_system_setting",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            result = await settings_service.validate_settings(
                {"unknown.key": "value"}, "user-123"
            )
        assert result.is_valid is False
        assert any("Unknown setting" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_settings_admin_only_flagged(
        self, settings_service, sample_system_setting
    ):
        """validate_settings should flag admin-only settings."""
        # Make setting admin-only
        sample_system_setting.is_admin_only = True

        # Need to mock _validate_setting_value to return a valid SettingValue
        mock_validated = SettingValue(
            raw_value='"dark"', data_type=SettingDataType.STRING
        )

        with (
            patch("services.settings_service.logger"),
            patch.object(
                settings_service,
                "get_system_setting",
                new_callable=AsyncMock,
                return_value=sample_system_setting,
            ),
            patch.object(
                settings_service,
                "_validate_setting_value",
                new_callable=AsyncMock,
                return_value=mock_validated,
            ),
        ):
            result = await settings_service.validate_settings(
                {"ui.theme": "dark"}, "user-123"
            )
        assert result.is_valid is True
        assert "ui.theme" in result.admin_required

    @pytest.mark.asyncio
    async def test_validate_settings_validation_error(
        self, settings_service, sample_system_setting
    ):
        """validate_settings should report ValueError from validation."""
        with (
            patch("services.settings_service.logger"),
            patch.object(
                settings_service,
                "get_system_setting",
                new_callable=AsyncMock,
                return_value=sample_system_setting,
            ),
            patch.object(
                settings_service,
                "_validate_setting_value",
                new_callable=AsyncMock,
                side_effect=ValueError("Invalid value"),
            ),
        ):
            result = await settings_service.validate_settings(
                {"ui.theme": "bad"}, "user-123"
            )
        assert result.is_valid is False
        assert any("Validation error" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_settings_security_violation(
        self, settings_service, sample_system_setting
    ):
        """validate_settings should report security violations."""
        with (
            patch("services.settings_service.logger"),
            patch.object(
                settings_service,
                "get_system_setting",
                new_callable=AsyncMock,
                return_value=sample_system_setting,
            ),
            patch.object(
                settings_service,
                "_validate_setting_value",
                new_callable=AsyncMock,
                side_effect=RuntimeError("Security check failed"),
            ),
        ):
            result = await settings_service.validate_settings(
                {"ui.theme": "evil"}, "user-123"
            )
        assert result.is_valid is False
        assert any("Security violation" in e for e in result.security_violations)

    @pytest.mark.asyncio
    async def test_validate_settings_success(
        self, settings_service, sample_system_setting
    ):
        """validate_settings should return valid result for correct values."""
        mock_validated = SettingValue(
            raw_value='"dark"', data_type=SettingDataType.STRING
        )

        with (
            patch("services.settings_service.logger"),
            patch.object(
                settings_service,
                "get_system_setting",
                new_callable=AsyncMock,
                return_value=sample_system_setting,
            ),
            patch.object(
                settings_service,
                "_validate_setting_value",
                new_callable=AsyncMock,
                return_value=mock_validated,
            ),
        ):
            result = await settings_service.validate_settings(
                {"ui.theme": "dark"}, "user-123"
            )
        assert result.is_valid is True
        assert "ui.theme" in result.validated_settings
        assert len(result.errors) == 0
        assert len(result.security_violations) == 0

    @pytest.mark.asyncio
    async def test_validate_settings_handles_exception_gracefully(
        self, settings_service
    ):
        """validate_settings should return error response on outer exception."""
        with (
            patch("services.settings_service.logger"),
            patch.object(
                settings_service,
                "get_system_setting",
                new_callable=AsyncMock,
                side_effect=Exception("DB error"),
            ),
        ):
            result = await settings_service.validate_settings(
                {"ui.theme": "value"}, "user-123"
            )
        # The exception inside the loop is caught as a security violation
        assert result.is_valid is False
        assert any("Security violation" in e for e in result.security_violations)

    @pytest.mark.asyncio
    async def test_validate_settings_outer_exception(self, settings_service):
        """validate_settings should handle outer exceptions."""

        # Create an object that raises when iterated (hits the outer try block)
        class BrokenDict:
            def items(self):
                raise RuntimeError("Iteration failed")

        with patch("services.settings_service.logger") as mock_logger:
            result = await settings_service.validate_settings(BrokenDict(), "user-123")

        assert result.is_valid is False
        assert any("Validation system error" in e for e in result.errors)
        mock_logger.error.assert_called()


class TestUpdateSettings:
    """Tests for update_settings method."""

    @pytest.mark.asyncio
    async def test_update_settings_success(self, settings_service, mock_connection):
        """update_settings should update settings in database."""
        valid_result = SettingsValidationResult(
            is_valid=True, validated_settings={"ui.theme": "dark"}
        )
        mock_cursor = AsyncMock()
        mock_cursor.lastrowid = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        request = SettingsUpdateRequest(
            user_id="user-123", settings={"ui.theme": "dark"}
        )
        with (
            patch("services.settings_service.logger"),
            patch.object(
                settings_service,
                "validate_settings",
                new_callable=AsyncMock,
                return_value=valid_result,
            ),
            patch.object(
                settings_service,
                "_update_single_setting",
                new_callable=AsyncMock,
                return_value=1,
            ),
        ):
            result = await settings_service.update_settings(request)
        assert result.success is True
        assert "updated_settings" in result.data
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_settings_validation_failed(self, settings_service):
        """update_settings should reject invalid settings."""
        invalid_result = SettingsValidationResult(
            is_valid=False,
            errors=["Unknown setting: invalid.key"],
            security_violations=[],
        )
        request = SettingsUpdateRequest(
            user_id="user-123", settings={"invalid.key": "value"}
        )
        with (
            patch("services.settings_service.logger"),
            patch.object(
                settings_service,
                "validate_settings",
                new_callable=AsyncMock,
                return_value=invalid_result,
            ),
        ):
            result = await settings_service.update_settings(request)
        assert result.success is False
        assert result.error == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_update_settings_admin_required(
        self, settings_service, mock_db_service, regular_user
    ):
        """update_settings should reject admin-only settings for regular users."""
        valid_result = SettingsValidationResult(
            is_valid=True,
            validated_settings={"security.setting": "value"},
            admin_required=["security.setting"],
        )
        mock_db_service.get_user_by_id = AsyncMock(return_value=regular_user)
        request = SettingsUpdateRequest(
            user_id="user-456", settings={"security.setting": "value"}
        )
        with (
            patch("services.settings_service.logger"),
            patch.object(
                settings_service,
                "validate_settings",
                new_callable=AsyncMock,
                return_value=valid_result,
            ),
        ):
            result = await settings_service.update_settings(request)
        assert result.success is False
        assert result.error == "ADMIN_REQUIRED"

    @pytest.mark.asyncio
    async def test_update_settings_rollback_on_error(
        self, settings_service, mock_connection
    ):
        """update_settings should rollback on error."""
        valid_result = SettingsValidationResult(
            is_valid=True, validated_settings={"ui.theme": "dark"}
        )
        request = SettingsUpdateRequest(
            user_id="user-123", settings={"ui.theme": "dark"}
        )
        with (
            patch("services.settings_service.logger"),
            patch.object(
                settings_service,
                "validate_settings",
                new_callable=AsyncMock,
                return_value=valid_result,
            ),
            patch.object(
                settings_service,
                "_update_single_setting",
                new_callable=AsyncMock,
                side_effect=Exception("Update error"),
            ),
        ):
            result = await settings_service.update_settings(request)
        assert result.success is False
        mock_connection.rollback.assert_called()

    @pytest.mark.asyncio
    async def test_update_settings_has_checksum(
        self, settings_service, mock_connection
    ):
        """update_settings response should include checksum."""
        valid_result = SettingsValidationResult(
            is_valid=True, validated_settings={"ui.theme": "dark"}
        )
        mock_cursor = AsyncMock()
        mock_cursor.lastrowid = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        request = SettingsUpdateRequest(
            user_id="user-123", settings={"ui.theme": "dark"}
        )
        with (
            patch("services.settings_service.logger"),
            patch.object(
                settings_service,
                "validate_settings",
                new_callable=AsyncMock,
                return_value=valid_result,
            ),
            patch.object(
                settings_service,
                "_update_single_setting",
                new_callable=AsyncMock,
                return_value=1,
            ),
        ):
            result = await settings_service.update_settings(request)
        assert result.success is True
        assert result.checksum is not None

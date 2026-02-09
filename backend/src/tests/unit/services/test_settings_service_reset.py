"""Unit tests for services/settings_service.py - Reset and defaults operations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.auth import User, UserRole
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


class TestResetUserSettings:
    """Tests for reset_user_settings method."""

    @pytest.mark.asyncio
    async def test_reset_user_settings_success(self, settings_service, mock_connection):
        """reset_user_settings should delete user overrides."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                {"id": 1, "setting_key": "ui.theme", "setting_value": '"dark"'},
                {"id": 2, "setting_key": "ui.language", "setting_value": '"fr"'},
            ]
        )
        mock_cursor.lastrowid = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            result = await settings_service.reset_user_settings("user-123")
        assert result.success is True
        assert result.data["deleted_count"] == 2
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_user_settings_with_category(
        self, settings_service, mock_connection
    ):
        """reset_user_settings should filter by category."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                {"id": 1, "setting_key": "ui.theme", "setting_value": '"dark"'},
            ]
        )
        mock_cursor.lastrowid = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            result = await settings_service.reset_user_settings(
                "user-123", category=SettingCategory.UI
            )
        assert result.success is True
        execute_calls = mock_connection.execute.call_args_list
        assert any("category = ?" in str(call) for call in execute_calls)

    @pytest.mark.asyncio
    async def test_reset_user_settings_no_overrides(
        self, settings_service, mock_connection
    ):
        """reset_user_settings should handle no overrides gracefully."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_cursor.lastrowid = 0
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            result = await settings_service.reset_user_settings("user-123")
        assert result.success is True
        assert result.data["deleted_count"] == 0

    @pytest.mark.asyncio
    async def test_reset_user_settings_creates_audit_entries(
        self, settings_service, mock_connection
    ):
        """reset_user_settings should create audit entries for deletions."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                {"id": 1, "setting_key": "ui.theme", "setting_value": '"dark"'},
            ]
        )
        mock_cursor.lastrowid = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            await settings_service.reset_user_settings("user-123")
        assert mock_connection.execute.call_count >= 3

    @pytest.mark.asyncio
    async def test_reset_user_settings_rollback_on_error(
        self, settings_service, mock_connection
    ):
        """reset_user_settings should rollback on error."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                {"id": 1, "setting_key": "ui.theme", "setting_value": '"dark"'},
            ]
        )
        mock_connection.execute = AsyncMock(
            side_effect=[mock_cursor, Exception("DB error")]
        )
        with patch("services.settings_service.logger"):
            result = await settings_service.reset_user_settings("user-123")
        assert result.success is False
        mock_connection.rollback.assert_called()

    @pytest.mark.asyncio
    async def test_reset_user_settings_has_checksum(
        self, settings_service, mock_connection
    ):
        """reset_user_settings response should include checksum."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_cursor.lastrowid = 0
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            result = await settings_service.reset_user_settings("user-123")
        assert result.success is True
        assert result.checksum is not None


class TestResetSystemSettings:
    """Tests for reset_system_settings method."""

    @pytest.mark.asyncio
    async def test_reset_system_settings_admin_success(
        self, settings_service, mock_connection, mock_db_service, admin_user
    ):
        """reset_system_settings should reset settings for admin."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                {
                    "id": 1,
                    "setting_key": "ui.theme",
                    "setting_value": '"dark"',
                    "default_value": '"light"',
                }
            ]
        )
        mock_cursor.lastrowid = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            result = await settings_service.reset_system_settings("admin-123")
        assert result.success is True
        assert result.data["reset_count"] == 1
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_system_settings_non_admin_rejected(
        self, settings_service, mock_db_service, regular_user
    ):
        """reset_system_settings should reject non-admin users."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=regular_user)
        with patch("services.settings_service.logger"):
            result = await settings_service.reset_system_settings("user-456")
        assert result.success is False
        assert result.error == "ADMIN_REQUIRED"

    @pytest.mark.asyncio
    async def test_reset_system_settings_with_category(
        self, settings_service, mock_connection, mock_db_service, admin_user
    ):
        """reset_system_settings should filter by category."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_cursor.lastrowid = 0
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            await settings_service.reset_system_settings(
                "admin-123", category=SettingCategory.UI
            )
        call_args_list = mock_connection.execute.call_args_list
        select_call_found = any(
            "category = ?" in str(call[0][0])
            for call in call_args_list
            if len(call[0]) > 0
        )
        assert select_call_found, "Expected category filter in one of the execute calls"

    @pytest.mark.asyncio
    async def test_reset_system_settings_creates_audit(
        self, settings_service, mock_connection, mock_db_service, admin_user
    ):
        """reset_system_settings should create audit entries."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                {
                    "id": 1,
                    "setting_key": "ui.theme",
                    "setting_value": '"dark"',
                    "default_value": '"light"',
                }
            ]
        )
        mock_cursor.lastrowid = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            await settings_service.reset_system_settings("admin-123")
        assert mock_connection.execute.call_count >= 3

    @pytest.mark.asyncio
    async def test_reset_system_settings_rollback_on_error(
        self, settings_service, mock_connection, mock_db_service, admin_user
    ):
        """reset_system_settings should rollback on error."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                {
                    "id": 1,
                    "setting_key": "ui.theme",
                    "setting_value": '"dark"',
                    "default_value": '"light"',
                }
            ]
        )
        mock_connection.execute = AsyncMock(
            side_effect=[mock_cursor, mock_cursor, Exception("DB error")]
        )
        with patch("services.settings_service.logger"):
            result = await settings_service.reset_system_settings("admin-123")
        assert result.success is False
        mock_connection.rollback.assert_called()


class TestGetDefaultSettings:
    """Tests for get_default_settings method."""

    @pytest.mark.asyncio
    async def test_get_default_settings_success(
        self, settings_service, mock_connection
    ):
        """get_default_settings should return default values."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                {
                    "setting_key": "ui.theme",
                    "default_value": '"light"',
                    "category": "ui",
                    "data_type": "string",
                    "description": "UI theme",
                },
                {
                    "setting_key": "system.refresh_interval",
                    "default_value": "30",
                    "category": "system",
                    "data_type": "number",
                    "description": "Refresh interval",
                },
            ]
        )
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            result = await settings_service.get_default_settings()
        assert result.success is True
        assert "defaults" in result.data
        assert len(result.data["defaults"]) == 2
        assert result.data["defaults"]["ui.theme"]["value"] == "light"

    @pytest.mark.asyncio
    async def test_get_default_settings_with_category(
        self, settings_service, mock_connection
    ):
        """get_default_settings should filter by category."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            await settings_service.get_default_settings(category=SettingCategory.UI)
        call_args = mock_connection.execute.call_args
        assert "category = ?" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_default_settings_handles_invalid_value(
        self, settings_service, mock_connection
    ):
        """get_default_settings should skip invalid values."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                {
                    "setting_key": "ui.theme",
                    "default_value": "invalid json",
                    "category": "ui",
                    "data_type": "string",
                    "description": "UI theme",
                }
            ]
        )
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_schema.logger") as mock_logger:
            result = await settings_service.get_default_settings()
        assert result.success is True
        assert len(result.data["defaults"]) == 0
        mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_get_default_settings_handles_error(
        self, settings_service, mock_connection
    ):
        """get_default_settings should handle errors gracefully."""
        mock_connection.execute = AsyncMock(side_effect=Exception("DB error"))
        with patch("services.settings_schema.logger") as mock_logger:
            result = await settings_service.get_default_settings()
        assert result.success is False
        assert result.error == "GET_DEFAULTS_ERROR"
        mock_logger.error.assert_called()


class TestGetSettingsSchema:
    """Tests for get_settings_schema method."""

    @pytest.mark.asyncio
    async def test_get_settings_schema_success(self, settings_service, mock_connection):
        """get_settings_schema should return schema information."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                {
                    "setting_key": "ui.theme",
                    "category": "ui",
                    "scope": "user_overridable",
                    "data_type": "string",
                    "is_admin_only": 0,
                    "description": "UI theme",
                    "validation_rules": '{"enum": ["light", "dark"]}',
                }
            ]
        )
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            result = await settings_service.get_settings_schema()
        assert result.success is True
        assert "schema" in result.data
        assert "ui.theme" in result.data["schema"]
        schema_entry = result.data["schema"]["ui.theme"]
        assert schema_entry["category"] == "ui"
        assert schema_entry["validation_rules"]["enum"] == ["light", "dark"]

    @pytest.mark.asyncio
    async def test_get_settings_schema_no_validation_rules(
        self, settings_service, mock_connection
    ):
        """get_settings_schema should handle null validation rules."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[
                {
                    "setting_key": "ui.theme",
                    "category": "ui",
                    "scope": "user_overridable",
                    "data_type": "string",
                    "is_admin_only": 0,
                    "description": "UI theme",
                    "validation_rules": None,
                }
            ]
        )
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            result = await settings_service.get_settings_schema()
        assert result.success is True
        assert result.data["schema"]["ui.theme"]["validation_rules"] is None

    @pytest.mark.asyncio
    async def test_get_settings_schema_handles_error(
        self, settings_service, mock_connection
    ):
        """get_settings_schema should handle errors gracefully."""
        mock_connection.execute = AsyncMock(side_effect=Exception("DB error"))
        with patch("services.settings_schema.logger") as mock_logger:
            result = await settings_service.get_settings_schema()
        assert result.success is False
        assert result.error == "SCHEMA_ERROR"
        mock_logger.error.assert_called()

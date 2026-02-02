"""Unit tests for services/settings_service.py - Audit operations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.settings_service import SettingsService
from models.settings import (
    SettingCategory, SettingScope, SettingDataType,
    SettingValue, ChangeType, SystemSetting, UserSetting,
)
from models.auth import User, UserRole


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
        id="admin-123", username="admin", email="admin@example.com",
        role=UserRole.ADMIN, last_login="2024-01-15T10:00:00+00:00", is_active=True,
    )


@pytest.fixture
def regular_user():
    """Create regular user for testing."""
    return User(
        id="user-456", username="regular", email="user@example.com",
        role=UserRole.USER, last_login="2024-01-15T10:00:00+00:00", is_active=True,
    )


class TestCreateAuditEntry:
    """Tests for _create_audit_entry method."""

    @pytest.mark.asyncio
    async def test_create_audit_entry_success(self, settings_service, mock_connection):
        """_create_audit_entry should insert audit record."""
        mock_cursor = AsyncMock()
        mock_cursor.lastrowid = 42
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            result = await settings_service._create_audit_entry(
                mock_connection, "user_settings", 1, "user-123", "ui.theme",
                '"light"', '"dark"', ChangeType.UPDATE, "User preference",
                "192.168.1.1", "Mozilla/5.0",
            )
        assert result == 42
        mock_connection.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_audit_entry_with_checksum(self, settings_service, mock_connection):
        """_create_audit_entry should generate checksum."""
        mock_cursor = AsyncMock()
        mock_cursor.lastrowid = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger") as mock_logger:
            await settings_service._create_audit_entry(
                mock_connection, "user_settings", 1, "user-123", "ui.theme",
                '"light"', '"dark"', ChangeType.UPDATE,
            )
        mock_logger.debug.assert_called()
        assert "checksum" in mock_logger.debug.call_args[1]

    @pytest.mark.asyncio
    async def test_create_audit_entry_for_create_operation(self, settings_service, mock_connection):
        """_create_audit_entry should handle CREATE operation."""
        mock_cursor = AsyncMock()
        mock_cursor.lastrowid = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            result = await settings_service._create_audit_entry(
                mock_connection, "user_settings", 1, "user-123", "ui.theme",
                None, '"dark"', ChangeType.CREATE,
            )
        assert result == 1
        assert "CREATE" in mock_connection.execute.call_args[0][1]

    @pytest.mark.asyncio
    async def test_create_audit_entry_for_delete_operation(self, settings_service, mock_connection):
        """_create_audit_entry should handle DELETE operation."""
        mock_cursor = AsyncMock()
        mock_cursor.lastrowid = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            result = await settings_service._create_audit_entry(
                mock_connection, "user_settings", 1, "user-123", "ui.theme",
                '"dark"', '""', ChangeType.DELETE,
            )
        assert result == 1

    @pytest.mark.asyncio
    async def test_create_audit_entry_handles_error(self, settings_service, mock_connection):
        """_create_audit_entry should raise on error."""
        mock_connection.execute = AsyncMock(side_effect=Exception("DB error"))
        with (
            patch("services.settings_service.logger") as mock_logger,
            pytest.raises(Exception),
        ):
            await settings_service._create_audit_entry(
                mock_connection, "user_settings", 1, "user-123", "ui.theme",
                '"light"', '"dark"', ChangeType.UPDATE,
            )
        mock_logger.error.assert_called()


class TestGetSettingsAudit:
    """Tests for get_settings_audit method."""

    @pytest.mark.asyncio
    async def test_get_settings_audit_admin_success(
        self, settings_service, mock_connection, mock_db_service, admin_user
    ):
        """get_settings_audit should return audit entries for admin."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[{
            "id": 1, "table_name": "user_settings", "record_id": 1,
            "user_id": "user-123", "setting_key": "ui.theme",
            "old_value": '"light"', "new_value": '"dark"', "change_type": "UPDATE",
            "change_reason": "User preference", "client_ip": "192.168.1.1",
            "user_agent": "Mozilla/5.0", "created_at": "2024-01-15T10:00:00+00:00",
            "checksum": "abc123",
        }])
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            result = await settings_service.get_settings_audit("admin-123")
        assert result.success is True
        assert "audit_entries" in result.data
        assert len(result.data["audit_entries"]) == 1

    @pytest.mark.asyncio
    async def test_get_settings_audit_non_admin_rejected(
        self, settings_service, mock_db_service, regular_user
    ):
        """get_settings_audit should reject non-admin users."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=regular_user)
        with patch("services.settings_service.logger"):
            result = await settings_service.get_settings_audit("user-456")
        assert result.success is False
        assert result.error == "ADMIN_REQUIRED"

    @pytest.mark.asyncio
    async def test_get_settings_audit_with_setting_key_filter(
        self, settings_service, mock_connection, mock_db_service, admin_user
    ):
        """get_settings_audit should filter by setting key."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            await settings_service.get_settings_audit("admin-123", setting_key="ui.theme")
        assert "ui.theme" in mock_connection.execute.call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_settings_audit_with_user_filter(
        self, settings_service, mock_connection, mock_db_service, admin_user
    ):
        """get_settings_audit should filter by user ID."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            await settings_service.get_settings_audit("admin-123", filter_user_id="user-456")
        assert "user-456" in mock_connection.execute.call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_settings_audit_pagination(
        self, settings_service, mock_connection, mock_db_service, admin_user
    ):
        """get_settings_audit should support pagination."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with patch("services.settings_service.logger"):
            await settings_service.get_settings_audit("admin-123", limit=50, offset=100)
        params = mock_connection.execute.call_args[0][1]
        assert 50 in params
        assert 100 in params

    @pytest.mark.asyncio
    async def test_get_settings_audit_handles_error(
        self, settings_service, mock_connection, mock_db_service, admin_user
    ):
        """get_settings_audit should handle errors gracefully."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_connection.execute = AsyncMock(side_effect=Exception("DB error"))
        with patch("services.settings_service.logger") as mock_logger:
            result = await settings_service.get_settings_audit("admin-123")
        assert result.success is False
        assert result.error == "AUDIT_ERROR"
        mock_logger.error.assert_called()


def _make_system_setting(key="ui.theme", admin_only=False, validation=None):
    """Helper to create system setting for tests."""
    return SystemSetting(
        id=1, setting_key=key,
        setting_value=SettingValue(raw_value='"light"', data_type=SettingDataType.STRING),
        default_value=SettingValue(raw_value='"light"', data_type=SettingDataType.STRING),
        category=SettingCategory.UI, scope=SettingScope.USER_OVERRIDABLE,
        data_type=SettingDataType.STRING, is_admin_only=admin_only,
        validation_rules=validation, version=1,
    )


class TestUpdateSingleSetting:
    """Tests for _update_single_setting method."""

    @pytest.mark.asyncio
    async def test_update_single_setting_existing_user_setting(
        self, settings_service, mock_connection
    ):
        """_update_single_setting should update existing user setting."""
        system_setting = _make_system_setting()
        user_setting = UserSetting(
            id=1, user_id="user-123", setting_key="ui.theme",
            setting_value=SettingValue(raw_value='"light"', data_type=SettingDataType.STRING),
            category=SettingCategory.UI, is_override=True, version=1,
        )
        mock_cursor = AsyncMock()
        mock_cursor.lastrowid = 42
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with (
            patch("services.settings_service.logger"),
            patch.object(settings_service, "get_system_setting",
                        new_callable=AsyncMock, return_value=system_setting),
            patch.object(settings_service, "get_user_setting",
                        new_callable=AsyncMock, return_value=user_setting),
        ):
            result = await settings_service._update_single_setting(
                mock_connection, "user-123", "ui.theme", "dark",
            )
        assert result == 42
        assert mock_connection.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_update_single_setting_new_user_setting(
        self, settings_service, mock_connection
    ):
        """_update_single_setting should create new user setting."""
        system_setting = _make_system_setting()
        mock_cursor = AsyncMock()
        mock_cursor.lastrowid = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with (
            patch("services.settings_service.logger"),
            patch.object(settings_service, "get_system_setting",
                        new_callable=AsyncMock, return_value=system_setting),
            patch.object(settings_service, "get_user_setting",
                        new_callable=AsyncMock, return_value=None),
        ):
            result = await settings_service._update_single_setting(
                mock_connection, "user-123", "ui.theme", "dark",
            )
        assert result is not None
        assert mock_connection.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_update_single_setting_system_setting_not_found(
        self, settings_service, mock_connection
    ):
        """_update_single_setting should raise for unknown setting."""
        with (
            patch("services.settings_service.logger"),
            patch.object(settings_service, "get_system_setting",
                        new_callable=AsyncMock, return_value=None),
            pytest.raises(ValueError, match="System setting not found"),
        ):
            await settings_service._update_single_setting(
                mock_connection, "user-123", "unknown.key", "value",
            )

    @pytest.mark.asyncio
    async def test_update_single_setting_with_metadata(self, settings_service, mock_connection):
        """_update_single_setting should include client metadata in audit."""
        system_setting = _make_system_setting()
        mock_cursor = AsyncMock()
        mock_cursor.lastrowid = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)
        with (
            patch("services.settings_service.logger"),
            patch.object(settings_service, "get_system_setting",
                        new_callable=AsyncMock, return_value=system_setting),
            patch.object(settings_service, "get_user_setting",
                        new_callable=AsyncMock, return_value=None),
        ):
            await settings_service._update_single_setting(
                mock_connection, "user-123", "ui.theme", "dark",
                "User preference update", "192.168.1.1", "Mozilla/5.0",
            )
        assert mock_connection.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_update_single_setting_handles_error(self, settings_service, mock_connection):
        """_update_single_setting should raise on error."""
        system_setting = _make_system_setting()
        mock_connection.execute = AsyncMock(side_effect=Exception("DB error"))
        with (
            patch("services.settings_service.logger") as mock_logger,
            patch.object(settings_service, "get_system_setting",
                        new_callable=AsyncMock, return_value=system_setting),
            patch.object(settings_service, "get_user_setting",
                        new_callable=AsyncMock, return_value=None),
            pytest.raises(Exception),
        ):
            await settings_service._update_single_setting(
                mock_connection, "user-123", "ui.theme", "dark",
            )
        mock_logger.error.assert_called()

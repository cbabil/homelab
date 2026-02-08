"""
Unit tests for services/settings_service.py - Core operations.

Tests initialization, admin verification, and database connection handling.
"""

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
    # Create proper async context manager mock
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
        created_at="2024-01-01T00:00:00+00:00",
        updated_at="2024-01-01T00:00:00+00:00",
        updated_by=None,
        version=1,
    )


class TestSettingsServiceInit:
    """Tests for SettingsService initialization."""

    def test_init_stores_db_service(self, mock_db_service):
        """SettingsService should store database service reference."""
        with patch("services.settings_service.logger"):
            service = SettingsService(mock_db_service)
            assert service.db_service is mock_db_service

    def test_init_creates_default_db_service(self):
        """SettingsService should create default DatabaseService if not provided."""
        with (
            patch("services.settings_service.logger"),
            patch("services.settings_service.DatabaseService") as MockDB,
        ):
            MockDB.return_value = MagicMock()
            service = SettingsService()
            assert service.db_service is MockDB.return_value

    def test_init_logs_message(self, mock_db_service):
        """SettingsService should log initialization."""
        with patch("services.settings_service.logger") as mock_logger:
            SettingsService(mock_db_service)
            mock_logger.info.assert_called_with(
                "Settings service initialized with security controls"
            )


class TestGetConnection:
    """Tests for get_connection context manager."""

    @pytest.mark.asyncio
    async def test_get_connection_yields_connection(
        self, settings_service, mock_connection
    ):
        """get_connection should yield database connection."""
        async with settings_service.get_connection() as conn:
            assert conn is mock_connection

    @pytest.mark.asyncio
    async def test_get_connection_rolls_back_on_error(
        self, settings_service, mock_connection
    ):
        """get_connection should rollback on exception."""
        with pytest.raises(ValueError):
            async with settings_service.get_connection():
                raise ValueError("Test error")

        mock_connection.rollback.assert_called_once()


class TestVerifyAdminAccess:
    """Tests for verify_admin_access method."""

    @pytest.mark.asyncio
    async def test_verify_admin_access_admin_user(
        self, settings_service, mock_db_service, admin_user
    ):
        """verify_admin_access should return True for admin user."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=admin_user)

        with patch("services.settings_service.logger"):
            result = await settings_service.verify_admin_access("admin-123")

        assert result is True
        mock_db_service.get_user_by_id.assert_called_once_with("admin-123")

    @pytest.mark.asyncio
    async def test_verify_admin_access_regular_user(
        self, settings_service, mock_db_service, regular_user
    ):
        """verify_admin_access should return False for regular user."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=regular_user)

        with patch("services.settings_service.logger"):
            result = await settings_service.verify_admin_access("user-456")

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_admin_access_user_not_found(
        self, settings_service, mock_db_service
    ):
        """verify_admin_access should return False when user not found."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=None)

        with patch("services.settings_service.logger") as mock_logger:
            result = await settings_service.verify_admin_access("unknown")

        assert result is False
        mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_verify_admin_access_handles_exception(
        self, settings_service, mock_db_service
    ):
        """verify_admin_access should return False on exception."""
        mock_db_service.get_user_by_id = AsyncMock(side_effect=Exception("DB error"))

        with patch("services.settings_service.logger") as mock_logger:
            result = await settings_service.verify_admin_access("admin-123")

        assert result is False
        mock_logger.error.assert_called()


class TestGetSystemSetting:
    """Tests for get_system_setting method."""

    @pytest.mark.asyncio
    async def test_get_system_setting_found(self, settings_service, mock_connection):
        """get_system_setting should return setting from database."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(
            return_value={
                "id": 1,
                "setting_key": "ui.theme",
                "setting_value": '"dark"',
                "default_value": '"light"',
                "category": "ui",
                "scope": "user_overridable",
                "data_type": "string",
                "is_admin_only": 0,
                "description": "UI theme",
                "validation_rules": None,
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": "2024-01-01T00:00:00+00:00",
                "updated_by": None,
                "version": 1,
            }
        )
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.settings_service.logger"):
            result = await settings_service.get_system_setting("ui.theme")

        assert result is not None
        assert result.setting_key == "ui.theme"
        assert result.setting_value.get_parsed_value() == "dark"
        assert result.category == SettingCategory.UI

    @pytest.mark.asyncio
    async def test_get_system_setting_not_found(
        self, settings_service, mock_connection
    ):
        """get_system_setting should return None when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.settings_service.logger"):
            result = await settings_service.get_system_setting("nonexistent.key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_system_setting_handles_error(
        self, settings_service, mock_connection
    ):
        """get_system_setting should return None on error."""
        mock_connection.execute = AsyncMock(side_effect=Exception("DB error"))

        with patch("services.settings_service.logger") as mock_logger:
            result = await settings_service.get_system_setting("ui.theme")

        assert result is None
        mock_logger.error.assert_called()


class TestGetUserSetting:
    """Tests for get_user_setting method."""

    @pytest.mark.asyncio
    async def test_get_user_setting_found(
        self, settings_service, mock_connection, sample_system_setting
    ):
        """get_user_setting should return user setting from database."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(
            return_value={
                "id": 1,
                "user_id": "user-123",
                "setting_key": "ui.theme",
                "setting_value": '"dark"',
                "category": "ui",
                "is_override": 1,
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": "2024-01-01T00:00:00+00:00",
                "version": 1,
            }
        )
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with (
            patch("services.settings_service.logger"),
            patch.object(
                settings_service,
                "get_system_setting",
                new_callable=AsyncMock,
                return_value=sample_system_setting,
            ),
        ):
            result = await settings_service.get_user_setting("user-123", "ui.theme")

        assert result is not None
        assert result.user_id == "user-123"
        assert result.setting_key == "ui.theme"

    @pytest.mark.asyncio
    async def test_get_user_setting_not_found(self, settings_service, mock_connection):
        """get_user_setting should return None when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.settings_service.logger"):
            result = await settings_service.get_user_setting("user-123", "ui.theme")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_setting_no_system_setting(
        self, settings_service, mock_connection
    ):
        """get_user_setting should return None if no system setting exists."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(
            return_value={
                "id": 1,
                "user_id": "user-123",
                "setting_key": "ui.theme",
                "setting_value": '"dark"',
                "category": "ui",
                "is_override": 1,
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": "2024-01-01T00:00:00+00:00",
                "version": 1,
            }
        )
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with (
            patch("services.settings_service.logger") as mock_logger,
            patch.object(
                settings_service,
                "get_system_setting",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            result = await settings_service.get_user_setting("user-123", "ui.theme")

        assert result is None
        mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_get_user_setting_handles_error(
        self, settings_service, mock_connection
    ):
        """get_user_setting should return None on error."""
        mock_connection.execute = AsyncMock(side_effect=Exception("DB error"))

        with patch("services.settings_service.logger") as mock_logger:
            result = await settings_service.get_user_setting("user-123", "ui.theme")

        assert result is None
        mock_logger.error.assert_called()

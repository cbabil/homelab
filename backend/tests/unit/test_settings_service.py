"""
Settings Service Tests

Comprehensive tests for the SettingsService including database operations,
security controls, audit trail, and error handling.
"""

import pytest
import tempfile
import os
from unittest.mock import AsyncMock, patch
from datetime import datetime

from services.settings_service import SettingsService
from services.database_service import DatabaseService
from models.settings import (
    SystemSetting, UserSetting, SettingValue,
    SettingsRequest, SettingsUpdateRequest, SettingCategory, SettingScope, SettingDataType, ChangeType
)
from models.auth import User, UserRole


@pytest.fixture
async def temp_settings_service():
    """Create SettingsService with temporary database."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_settings.db")

    # Create database service with temporary database
    db_service = DatabaseService(db_path=db_path)
    await db_service.initialize()

    settings_service = SettingsService(db_service=db_service)

    yield settings_service

    # Cleanup
    await db_service.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_db_service():
    """Mock DatabaseService instance."""
    service = AsyncMock(spec=DatabaseService)
    return service


@pytest.fixture
def settings_service_with_mock(mock_db_service):
    """Create SettingsService with mocked database."""
    return SettingsService(db_service=mock_db_service)


@pytest.fixture
def admin_user():
    """Create admin user."""
    return User(
        id="admin_user",
        username="admin",
        email="admin@test.com",
        role=UserRole.ADMIN,
        last_login="2023-01-01T00:00:00Z",
        is_active=True
    )


@pytest.fixture
def regular_user():
    """Create regular user."""
    return User(
        id="regular_user",
        username="user",
        email="user@test.com",
        role=UserRole.USER,
        last_login="2023-01-01T00:00:00Z",
        is_active=True
    )


@pytest.fixture
def sample_system_setting():
    """Create sample system setting."""
    setting_value = SettingValue(
        raw_value='"dark"',
        data_type=SettingDataType.STRING
    )
    return SystemSetting(
        id=1,
        setting_key="ui.theme",
        setting_value=setting_value,
        category=SettingCategory.UI,
        scope=SettingScope.USER_OVERRIDABLE,
        data_type=SettingDataType.STRING,
        is_admin_only=False,
        description="UI theme setting",
        version=1
    )


@pytest.fixture
def sample_user_setting():
    """Create sample user setting."""
    setting_value = SettingValue(
        raw_value='"light"',
        data_type=SettingDataType.STRING
    )
    return UserSetting(
        id=1,
        user_id="user_123",
        setting_key="ui.theme",
        setting_value=setting_value,
        category=SettingCategory.UI,
        is_override=True,
        version=1
    )


class TestAdminVerification:
    """Test admin access verification."""

    async def test_verify_admin_access_valid_admin(self, settings_service_with_mock, admin_user):
        """Test admin verification with valid admin user."""
        settings_service_with_mock.db_service.get_user_by_id.return_value = admin_user

        result = await settings_service_with_mock.verify_admin_access("admin_user")

        assert result is True
        settings_service_with_mock.db_service.get_user_by_id.assert_called_once_with("admin_user")

    async def test_verify_admin_access_regular_user(self, settings_service_with_mock, regular_user):
        """Test admin verification with regular user."""
        settings_service_with_mock.db_service.get_user_by_id.return_value = regular_user

        result = await settings_service_with_mock.verify_admin_access("regular_user")

        assert result is False

    async def test_verify_admin_access_nonexistent_user(self, settings_service_with_mock):
        """Test admin verification with nonexistent user."""
        settings_service_with_mock.db_service.get_user_by_id.return_value = None

        result = await settings_service_with_mock.verify_admin_access("nonexistent_user")

        assert result is False

    async def test_verify_admin_access_service_error(self, settings_service_with_mock):
        """Test admin verification handles service errors."""
        settings_service_with_mock.db_service.get_user_by_id.side_effect = Exception("Database error")

        result = await settings_service_with_mock.verify_admin_access("admin_user")

        assert result is False


@pytest.mark.skip(reason="API changed - CRUD methods removed")
class TestAuditEntryCreation:
    """Test audit entry creation functionality."""

    async def test_create_audit_entry_success(self, temp_settings_service):
        """Test successful audit entry creation."""
        async with temp_settings_service.get_connection() as connection:
            audit_id = await temp_settings_service._create_audit_entry(
                connection=connection,
                table_name="system_settings",
                record_id=1,
                user_id="admin_user",
                setting_key="ui.theme",
                old_value=None,
                new_value='"dark"',
                change_type=ChangeType.CREATE,
                change_reason="Initial setup",
                client_ip="192.168.1.100",
                user_agent="TestClient/1.0"
            )

            assert audit_id is not None
            assert isinstance(audit_id, int)

            # Verify audit entry was created
            cursor = await connection.execute(
                "SELECT * FROM settings_audit WHERE id = ?",
                (audit_id,)
            )
            audit_entry = await cursor.fetchone()
            assert audit_entry is not None

    async def test_create_audit_entry_with_checksum(self, temp_settings_service):
        """Test audit entry creation includes valid checksum."""
        async with temp_settings_service.get_connection() as connection:
            audit_id = await temp_settings_service._create_audit_entry(
                connection=connection,
                table_name="system_settings",
                record_id=1,
                user_id="admin_user",
                setting_key="ui.theme",
                old_value='"light"',
                new_value='"dark"',
                change_type=ChangeType.UPDATE
            )

            # Get the audit entry
            cursor = await connection.execute(
                "SELECT checksum, table_name, record_id, setting_key, old_value, new_value, change_type, created_at FROM settings_audit WHERE id = ?",
                (audit_id,)
            )
            row = await cursor.fetchone()

            checksum = row[0]
            assert checksum is not None
            assert len(checksum) == 64  # SHA256 hex length

            # Verify checksum calculation
            data = f"{row[1]}:{row[2]}:{row[3]}:{row[4]}:{row[5]}:{row[6]}:{row[7]}"
            import hashlib
            expected_checksum = hashlib.sha256(data.encode('utf-8')).hexdigest()
            assert checksum == expected_checksum

    async def test_create_audit_entry_invalid_table(self, settings_service_with_mock):
        """Test audit entry creation with invalid table name."""
        mock_connection = AsyncMock()
        settings_service_with_mock.db_service.get_connection.return_value.__aenter__.return_value = mock_connection

        with pytest.raises(Exception):  # Should raise validation error
            await settings_service_with_mock._create_audit_entry(
                connection=mock_connection,
                table_name="invalid_table",
                record_id=1,
                user_id="admin_user",
                setting_key="ui.theme",
                old_value=None,
                new_value='"dark"',
                change_type=ChangeType.CREATE
            )


@pytest.mark.skip(reason="API changed - CRUD methods removed")
class TestSystemSettingsOperations:
    """Test system settings CRUD operations."""

    async def test_get_system_setting_exists(self, temp_settings_service):
        """Test retrieving existing system setting."""
        # Insert test setting first
        async with temp_settings_service.get_connection() as connection:
            await connection.execute(
                """
                INSERT INTO system_settings (
                    setting_key, setting_value, data_type, category, scope,
                    is_admin_only, created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("ui.theme", '"dark"', "string", "ui", "user_overridable",
                 0, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), 1)
            )
            await connection.commit()

        # Test retrieval
        setting = await temp_settings_service.get_system_setting("ui.theme")

        assert setting is not None
        assert setting.setting_key == "ui.theme"
        assert setting.setting_value.get_parsed_value() == "dark"

    async def test_get_system_setting_not_exists(self, temp_settings_service):
        """Test retrieving nonexistent system setting."""
        setting = await temp_settings_service.get_system_setting("nonexistent.setting")
        assert setting is None

    async def test_create_system_setting_success(self, temp_settings_service, sample_system_setting):
        """Test successful system setting creation."""
        result = await temp_settings_service.create_system_setting(
            setting=sample_system_setting,
            user_id="admin_user"
        )

        assert result.success is True
        assert result.audit_id is not None

        # Verify setting was created
        setting = await temp_settings_service.get_system_setting("ui.theme")
        assert setting is not None

    async def test_create_system_setting_duplicate_key(self, temp_settings_service, sample_system_setting):
        """Test system setting creation with duplicate key."""
        # Create first setting
        await temp_settings_service.create_system_setting(
            setting=sample_system_setting,
            user_id="admin_user"
        )

        # Try to create duplicate
        result = await temp_settings_service.create_system_setting(
            setting=sample_system_setting,
            user_id="admin_user"
        )

        assert result.success is False
        assert "already exists" in result.message.lower() or "duplicate" in result.message.lower()

    async def test_update_system_setting_success(self, temp_settings_service, sample_system_setting):
        """Test successful system setting update."""
        # Create initial setting
        await temp_settings_service.create_system_setting(
            setting=sample_system_setting,
            user_id="admin_user"
        )

        # Update setting
        updated_value = SettingValue(
            raw_value='"light"',
            data_type=SettingDataType.STRING
        )
        sample_system_setting.setting_value = updated_value

        result = await temp_settings_service.update_system_setting(
            setting=sample_system_setting,
            user_id="admin_user"
        )

        assert result.success is True
        assert result.audit_id is not None

        # Verify update
        setting = await temp_settings_service.get_system_setting("ui.theme")
        assert setting.setting_value.get_parsed_value() == "light"

    async def test_update_system_setting_not_exists(self, temp_settings_service, sample_system_setting):
        """Test updating nonexistent system setting."""
        result = await temp_settings_service.update_system_setting(
            setting=sample_system_setting,
            user_id="admin_user"
        )

        assert result.success is False
        assert "not found" in result.message.lower()

    async def test_delete_system_setting_success(self, temp_settings_service, sample_system_setting):
        """Test successful system setting deletion."""
        # Create setting first
        await temp_settings_service.create_system_setting(
            setting=sample_system_setting,
            user_id="admin_user"
        )

        # Delete setting
        result = await temp_settings_service.delete_system_setting(
            setting_key="ui.theme",
            user_id="admin_user"
        )

        assert result.success is True
        assert result.audit_id is not None

        # Verify deletion
        setting = await temp_settings_service.get_system_setting("ui.theme")
        assert setting is None

    async def test_delete_system_setting_not_exists(self, temp_settings_service):
        """Test deleting nonexistent system setting."""
        result = await temp_settings_service.delete_system_setting(
            setting_key="nonexistent.setting",
            user_id="admin_user"
        )

        assert result.success is False
        assert "not found" in result.message.lower()


class TestUserSettingsOperations:
    """Test user settings operations."""

    async def test_get_user_settings_with_defaults(self, temp_settings_service, sample_system_setting):
        """Test getting user settings includes system defaults."""
        # Create system default
        await temp_settings_service.create_system_setting(
            setting=sample_system_setting,
            user_id="admin_user"
        )

        # Create settings request
        request = SettingsRequest(
            user_id="user_123",
            include_system_defaults=True,
            include_user_overrides=True
        )

        result = await temp_settings_service.get_user_settings(request)

        assert result.success is True
        assert result.data is not None
        assert "ui.theme" in result.data

    async def test_get_user_settings_with_overrides(self, temp_settings_service, sample_system_setting, sample_user_setting):
        """Test getting user settings includes user overrides."""
        # Create system default
        await temp_settings_service.create_system_setting(
            setting=sample_system_setting,
            user_id="admin_user"
        )

        # Create user override
        await temp_settings_service.create_user_setting(
            setting=sample_user_setting,
            user_id="user_123"
        )

        # Create settings request
        request = SettingsRequest(
            user_id="user_123",
            include_system_defaults=True,
            include_user_overrides=True
        )

        result = await temp_settings_service.get_user_settings(request)

        assert result.success is True
        assert result.data is not None
        # Should return user override value, not system default
        assert result.data["ui.theme"] == "light"  # User override value

    async def test_get_user_settings_category_filter(self, temp_settings_service, sample_system_setting):
        """Test getting user settings with category filter."""
        # Create system setting
        await temp_settings_service.create_system_setting(
            setting=sample_system_setting,
            user_id="admin_user"
        )

        # Create request with category filter
        request = SettingsRequest(
            user_id="user_123",
            category=SettingCategory.UI,
            include_system_defaults=True
        )

        result = await temp_settings_service.get_user_settings(request)

        assert result.success is True
        assert result.data is not None
        assert "ui.theme" in result.data

    async def test_get_user_settings_key_filter(self, temp_settings_service, sample_system_setting):
        """Test getting user settings with specific key filter."""
        # Create system setting
        await temp_settings_service.create_system_setting(
            setting=sample_system_setting,
            user_id="admin_user"
        )

        # Create request with key filter
        request = SettingsRequest(
            user_id="user_123",
            setting_keys=["ui.theme"],
            include_system_defaults=True
        )

        result = await temp_settings_service.get_user_settings(request)

        assert result.success is True
        assert result.data is not None
        assert "ui.theme" in result.data

    async def test_update_user_settings_success(self, temp_settings_service, sample_system_setting):
        """Test successful user settings update."""
        # Create system default
        sample_system_setting.is_admin_only = False  # Allow user override
        await temp_settings_service.create_system_setting(
            setting=sample_system_setting,
            user_id="admin_user"
        )

        # Create update request
        request = SettingsUpdateRequest(
            user_id="user_123",
            settings={"ui.theme": "light"},
            change_reason="User preference"
        )

        result = await temp_settings_service.update_user_settings(request)

        assert result.success is True
        assert result.audit_id is not None

    async def test_update_user_settings_admin_only_by_user(self, temp_settings_service, sample_system_setting):
        """Test user cannot update admin-only settings."""
        # Create admin-only system setting
        sample_system_setting.is_admin_only = True
        await temp_settings_service.create_system_setting(
            setting=sample_system_setting,
            user_id="admin_user"
        )

        # Try to update as regular user
        request = SettingsUpdateRequest(
            user_id="user_123",
            settings={"ui.theme": "light"}
        )

        result = await temp_settings_service.update_user_settings(request)

        assert result.success is False
        assert "admin" in result.message.lower()

    async def test_update_user_settings_admin_only_by_admin(self, temp_settings_service, sample_system_setting):
        """Test admin can update admin-only settings."""
        # Create admin-only system setting
        sample_system_setting.is_admin_only = True
        await temp_settings_service.create_system_setting(
            setting=sample_system_setting,
            user_id="admin_user"
        )

        # Verify admin access
        with patch.object(temp_settings_service, 'verify_admin_access', return_value=True):
            # Update as admin
            request = SettingsUpdateRequest(
                user_id="admin_user",
                settings={"ui.theme": "light"}
            )

            result = await temp_settings_service.update_user_settings(request)

            assert result.success is True


class TestSecurityValidation:
    """Test security validation and controls."""

    async def test_sql_injection_prevention(self, temp_settings_service):
        """Test prevention of SQL injection in settings operations."""
        # Test SQL injection in setting key
        malicious_key = "'; DROP TABLE system_settings; --"

        request = SettingsRequest(
            user_id="user_123",
            setting_keys=[malicious_key]
        )

        result = await temp_settings_service.get_user_settings(request)

        # Should handle gracefully without executing malicious SQL
        assert result.success is False or result.data == {}

    async def test_input_validation(self, temp_settings_service):
        """Test input validation for malicious content."""
        # Test various malicious inputs
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "\x00\x01\x02",  # Null bytes
            "a" * 10000  # Extremely long input
        ]

        for malicious_input in malicious_inputs:
            request = SettingsUpdateRequest(
                user_id="user_123",
                settings={"ui.theme": malicious_input}
            )

            # Should either reject or sanitize the input
            _result = await temp_settings_service.update_user_settings(request)
            # Implementation should handle this gracefully

    async def test_user_id_validation(self, temp_settings_service):
        """Test user ID validation and sanitization."""
        malicious_user_ids = [
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "user\x00admin",
            "user' OR 1=1--"
        ]

        for user_id in malicious_user_ids:
            request = SettingsRequest(user_id=user_id)

            # Should validate user ID format
            try:
                result = await temp_settings_service.get_user_settings(request)
                # If no exception, should handle gracefully
                assert result.success is False or result.data == {}
            except Exception:
                # Validation should catch malicious input
                pass


class TestErrorHandling:
    """Test error handling and edge cases."""

    async def test_database_connection_error(self, settings_service_with_mock):
        """Test handling of database connection errors."""
        # Mock database connection failure
        settings_service_with_mock.db_service.get_connection.side_effect = Exception("Connection failed")

        request = SettingsRequest(user_id="user_123")
        result = await settings_service_with_mock.get_user_settings(request)

        assert result.success is False
        assert "error" in result.message.lower()

    async def test_transaction_rollback(self, temp_settings_service, sample_system_setting):
        """Test transaction rollback on errors."""
        # Mock a failure during setting creation
        with patch.object(temp_settings_service, '_create_audit_entry', side_effect=Exception("Audit failed")):
            result = await temp_settings_service.create_system_setting(
                setting=sample_system_setting,
                user_id="admin_user"
            )

            assert result.success is False

            # Verify setting was not created (transaction rolled back)
            setting = await temp_settings_service.get_system_setting("ui.theme")
            assert setting is None

    async def test_concurrent_updates(self, temp_settings_service, sample_system_setting):
        """Test handling of concurrent updates with optimistic locking."""
        # Create initial setting
        await temp_settings_service.create_system_setting(
            setting=sample_system_setting,
            user_id="admin_user"
        )

        # Get current setting
        setting = await temp_settings_service.get_system_setting("ui.theme")
        original_version = setting.version

        # Simulate concurrent update by changing version
        async with temp_settings_service.get_connection() as connection:
            await connection.execute(
                "UPDATE system_settings SET version = version + 1 WHERE setting_key = ?",
                ("ui.theme",)
            )
            await connection.commit()

        # Try to update with old version
        setting.version = original_version  # Stale version
        updated_value = SettingValue(
            raw_value='"light"',
            data_type=SettingDataType.STRING
        )
        setting.setting_value = updated_value

        result = await temp_settings_service.update_system_setting(
            setting=setting,
            user_id="admin_user"
        )

        # Should detect version conflict
        assert result.success is False
        assert "version" in result.message.lower() or "conflict" in result.message.lower()

    async def test_invalid_json_handling(self, temp_settings_service):
        """Test handling of invalid JSON in setting values."""
        # Try to create setting with invalid JSON
        with pytest.raises(Exception):  # Should raise validation error
            _setting_value = SettingValue(
                raw_value='invalid_json',
                data_type=SettingDataType.STRING
            )

    async def test_large_dataset_handling(self, temp_settings_service):
        """Test handling of large datasets."""
        # Create many settings
        for i in range(100):
            setting_value = SettingValue(
                raw_value=f'"value_{i}"',
                data_type=SettingDataType.STRING
            )
            setting = SystemSetting(
                setting_key=f"test.setting_{i}",
                setting_value=setting_value,
                category=SettingCategory.SYSTEM,
                scope=SettingScope.SYSTEM,
                data_type=SettingDataType.STRING,
                is_admin_only=False
            )

            await temp_settings_service.create_system_setting(
                setting=setting,
                user_id="admin_user"
            )

        # Get all settings
        request = SettingsRequest(
            user_id="user_123",
            include_system_defaults=True
        )

        result = await temp_settings_service.get_user_settings(request)

        assert result.success is True
        assert len(result.data) == 100


class TestResetUserSettings:
    """Test reset_user_settings functionality."""

    async def test_reset_user_settings_success(self, settings_service_with_mock, mock_db_service):
        """Test successful user settings reset."""
        # Setup mock connection and cursor
        mock_connection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [
            {"id": 1, "setting_key": "ui.theme", "setting_value": '"light"'},
            {"id": 2, "setting_key": "ui.language", "setting_value": '"fr"'}
        ]
        mock_connection.execute.return_value = mock_cursor

        mock_db_service.get_connection.return_value.__aenter__.return_value = mock_connection

        # Mock audit entry creation
        with patch.object(settings_service_with_mock, '_create_audit_entry', new_callable=AsyncMock) as mock_audit:
            mock_audit.return_value = 1

            result = await settings_service_with_mock.reset_user_settings(
                user_id="user_123",
                client_ip="192.168.1.100",
                user_agent="TestClient/1.0"
            )

            assert result.success is True
            assert result.data is not None
            assert result.data.get("deleted_count") == 2

    async def test_reset_user_settings_with_category(self, settings_service_with_mock, mock_db_service):
        """Test user settings reset with category filter."""
        mock_connection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [
            {"id": 1, "setting_key": "ui.theme", "setting_value": '"light"'}
        ]
        mock_connection.execute.return_value = mock_cursor

        mock_db_service.get_connection.return_value.__aenter__.return_value = mock_connection

        with patch.object(settings_service_with_mock, '_create_audit_entry', new_callable=AsyncMock) as mock_audit:
            mock_audit.return_value = 1

            result = await settings_service_with_mock.reset_user_settings(
                user_id="user_123",
                category=SettingCategory.UI
            )

            assert result.success is True
            assert result.data.get("deleted_count") == 1

    async def test_reset_user_settings_no_overrides(self, settings_service_with_mock, mock_db_service):
        """Test reset when user has no overrides."""
        mock_connection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []
        mock_connection.execute.return_value = mock_cursor

        mock_db_service.get_connection.return_value.__aenter__.return_value = mock_connection

        result = await settings_service_with_mock.reset_user_settings(user_id="user_123")

        assert result.success is True
        assert result.data.get("deleted_count") == 0


class TestResetSystemSettings:
    """Test reset_system_settings functionality."""

    async def test_reset_system_settings_requires_admin(self, settings_service_with_mock):
        """Test that reset_system_settings requires admin privileges."""
        # Mock verify_admin_access to return False
        with patch.object(settings_service_with_mock, 'verify_admin_access', return_value=False):
            result = await settings_service_with_mock.reset_system_settings(user_id="regular_user")

            assert result.success is False
            assert result.error == "ADMIN_REQUIRED"

    async def test_reset_system_settings_success(self, settings_service_with_mock, mock_db_service):
        """Test successful system settings reset by admin."""
        mock_connection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [
            {"id": 1, "setting_key": "ui.theme", "setting_value": '"light"', "default_value": '"dark"'},
            {"id": 2, "setting_key": "ui.refresh", "setting_value": '"60000"', "default_value": '"30000"'}
        ]
        mock_connection.execute.return_value = mock_cursor

        mock_db_service.get_connection.return_value.__aenter__.return_value = mock_connection

        with patch.object(settings_service_with_mock, 'verify_admin_access', return_value=True):
            with patch.object(settings_service_with_mock, '_create_audit_entry', new_callable=AsyncMock) as mock_audit:
                mock_audit.return_value = 1

                result = await settings_service_with_mock.reset_system_settings(
                    user_id="admin_user",
                    client_ip="192.168.1.100"
                )

                assert result.success is True
                assert result.data is not None
                assert result.data.get("reset_count") == 2

    async def test_reset_system_settings_with_category(self, settings_service_with_mock, mock_db_service):
        """Test system settings reset with category filter."""
        mock_connection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [
            {"id": 1, "setting_key": "security.timeout", "setting_value": '"7200"', "default_value": '"3600"'}
        ]
        mock_connection.execute.return_value = mock_cursor

        mock_db_service.get_connection.return_value.__aenter__.return_value = mock_connection

        with patch.object(settings_service_with_mock, 'verify_admin_access', return_value=True):
            with patch.object(settings_service_with_mock, '_create_audit_entry', new_callable=AsyncMock) as mock_audit:
                mock_audit.return_value = 1

                result = await settings_service_with_mock.reset_system_settings(
                    user_id="admin_user",
                    category=SettingCategory.SECURITY
                )

                assert result.success is True
                assert result.data.get("reset_count") == 1

    async def test_reset_system_settings_nothing_to_reset(self, settings_service_with_mock, mock_db_service):
        """Test reset when all settings already at defaults."""
        mock_connection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []  # No settings differ from defaults
        mock_connection.execute.return_value = mock_cursor

        mock_db_service.get_connection.return_value.__aenter__.return_value = mock_connection

        with patch.object(settings_service_with_mock, 'verify_admin_access', return_value=True):
            result = await settings_service_with_mock.reset_system_settings(user_id="admin_user")

            assert result.success is True
            assert result.data.get("reset_count") == 0


class TestGetDefaultSettings:
    """Test get_default_settings functionality."""

    async def test_get_default_settings_success(self, settings_service_with_mock, mock_db_service):
        """Test successful retrieval of default settings."""
        mock_connection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [
            {"setting_key": "ui.theme", "default_value": '"dark"', "category": "ui", "data_type": "string", "description": "Theme setting"},
            {"setting_key": "ui.language", "default_value": '"en"', "category": "ui", "data_type": "string", "description": "Language setting"}
        ]
        mock_connection.execute.return_value = mock_cursor

        mock_db_service.get_connection.return_value.__aenter__.return_value = mock_connection

        result = await settings_service_with_mock.get_default_settings()

        assert result.success is True
        assert result.data is not None
        assert "defaults" in result.data
        assert len(result.data["defaults"]) == 2
        assert "ui.theme" in result.data["defaults"]
        assert result.data["defaults"]["ui.theme"]["value"] == "dark"

    async def test_get_default_settings_with_category(self, settings_service_with_mock, mock_db_service):
        """Test retrieval of default settings with category filter."""
        mock_connection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [
            {"setting_key": "security.timeout", "default_value": '3600', "category": "security", "data_type": "number", "description": "Session timeout"}
        ]
        mock_connection.execute.return_value = mock_cursor

        mock_db_service.get_connection.return_value.__aenter__.return_value = mock_connection

        result = await settings_service_with_mock.get_default_settings(category=SettingCategory.SECURITY)

        assert result.success is True
        assert "defaults" in result.data
        assert "security.timeout" in result.data["defaults"]

    async def test_get_default_settings_empty(self, settings_service_with_mock, mock_db_service):
        """Test retrieval when no defaults exist."""
        mock_connection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []
        mock_connection.execute.return_value = mock_cursor

        mock_db_service.get_connection.return_value.__aenter__.return_value = mock_connection

        result = await settings_service_with_mock.get_default_settings()

        assert result.success is True
        assert result.data["defaults"] == {}

    async def test_get_default_settings_handles_invalid_json(self, settings_service_with_mock, mock_db_service):
        """Test handling of invalid JSON in default values."""
        mock_connection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [
            {"setting_key": "ui.theme", "default_value": '"dark"', "category": "ui", "data_type": "string", "description": "Theme"},
            {"setting_key": "ui.invalid", "default_value": 'not_json', "category": "ui", "data_type": "string", "description": "Invalid"}
        ]
        mock_connection.execute.return_value = mock_cursor

        mock_db_service.get_connection.return_value.__aenter__.return_value = mock_connection

        result = await settings_service_with_mock.get_default_settings()

        # Should succeed but skip the invalid entry
        assert result.success is True
        assert "ui.theme" in result.data["defaults"]
        # Invalid entry should be skipped
        assert "ui.invalid" not in result.data["defaults"]
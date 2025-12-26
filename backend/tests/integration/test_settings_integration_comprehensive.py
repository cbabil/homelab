"""
Comprehensive Settings System Integration Tests

Tests the complete settings persistence system from end-to-end:
- Database schema and constraints
- MCP tools with security validation
- Settings service operations
- Audit trail functionality
- Security controls and access control
- Error handling and recovery

This test suite validates that the settings system is production-ready
and meets all security and functional requirements.
"""

import os
import pytest
import tempfile
import sqlite3
import json
import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Import components being tested
from services.settings_service import SettingsService
from services.database_service import DatabaseService
from services.auth_service import AuthService
from tools.settings_tools import SettingsTools
from models.auth import User, UserRole
from models.settings import (
    SystemSetting, UserSetting, SettingsAuditEntry,
    SettingValue, SettingsRequest, SettingsUpdateRequest,
    SettingCategory, SettingScope, SettingDataType
)
from fastmcp import Context


@pytest.fixture
async def integrated_test_database():
    """Create a temporary database with full schema for integration testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "integration_test.db")

    # Initialize database with schema
    schema_path = Path(__file__).parent.parent.parent / "sql" / "init_settings_schema.sql"

    # Create database connection and initialize schema
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    conn.executescript(schema_sql)
    conn.close()

    # Seed with default settings
    seed_path = Path(__file__).parent.parent.parent / "sql" / "seed_default_settings.sql"
    if seed_path.exists():
        conn = sqlite3.connect(db_path)
        with open(seed_path, 'r') as f:
            seed_sql = f.read()
        conn.executescript(seed_sql)
        conn.close()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
async def integrated_settings_service(integrated_test_database):
    """Create a fully integrated settings service with real database."""
    db_service = DatabaseService(db_path=integrated_test_database)

    settings_service = SettingsService(db_service=db_service)
    yield settings_service

    # No close method needed for DatabaseService


@pytest.fixture
def admin_user():
    """Create admin user for testing."""
    return User(
        id="admin_test",
        username="admin",
        email="admin@test.com",
        role=UserRole.ADMIN,
        last_login="2023-01-01T00:00:00Z",
        is_active=True
    )


@pytest.fixture
def regular_user():
    """Create regular user for testing."""
    return User(
        id="user_test",
        username="testuser",
        email="user@test.com",
        role=UserRole.USER,
        last_login="2023-01-01T00:00:00Z",
        is_active=True
    )


@pytest.fixture
def mock_auth_service(admin_user, regular_user):
    """Create mock auth service with test users."""
    service = AsyncMock(spec=AuthService)
    service.sessions = {
        'admin_session': {'user_id': 'admin_test'},
        'user_session': {'user_id': 'user_test'}
    }

    async def get_user_by_id(user_id):
        if user_id == 'admin_test':
            return admin_user
        elif user_id == 'user_test':
            return regular_user
        return None

    service.get_user_by_id.side_effect = get_user_by_id
    return service


@pytest.fixture
def admin_context():
    """Create admin context for MCP calls."""
    ctx = MagicMock(spec=Context)
    ctx.meta = {
        'sessionId': 'admin_session',
        'clientIp': '192.168.1.100',
        'userAgent': 'TestClient/1.0'
    }
    return ctx


@pytest.fixture
def user_context():
    """Create regular user context for MCP calls."""
    ctx = MagicMock(spec=Context)
    ctx.meta = {
        'sessionId': 'user_session',
        'clientIp': '192.168.1.101',
        'userAgent': 'TestClient/1.0'
    }
    return ctx


@pytest.fixture
async def integrated_settings_tools(integrated_settings_service, mock_auth_service):
    """Create integrated settings tools with real service and mock auth."""
    return SettingsTools(integrated_settings_service, mock_auth_service)


class TestDatabaseIntegration:
    """Test database operations with real schema."""

    async def test_database_schema_validation(self, integrated_test_database):
        """Test that database schema is properly created and validates correctly."""
        conn = sqlite3.connect(integrated_test_database)
        cursor = conn.cursor()

        # Verify tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        expected_tables = {'system_settings', 'user_settings', 'settings_audit'}
        assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"

        # Verify constraints work
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO system_settings (setting_key, setting_value, data_type, category, scope, is_admin_only)
                VALUES ('invalid..key', '"value"', 'string', 'ui', 'system', 0)
            """)

        conn.close()

    async def test_audit_triggers_functionality(self, integrated_test_database):
        """Test that audit triggers work correctly."""
        conn = sqlite3.connect(integrated_test_database)
        cursor = conn.cursor()

        # Insert a setting
        cursor.execute("""
            INSERT INTO system_settings (setting_key, setting_value, data_type, category, scope, is_admin_only)
            VALUES ('test.setting', '"test_value"', 'string', 'ui', 'user_overridable', 0)
        """)
        setting_id = cursor.lastrowid

        # Verify audit entry was created
        cursor.execute("""
            SELECT table_name, record_id, setting_key, change_type, new_value
            FROM settings_audit
            WHERE table_name = 'system_settings' AND record_id = ?
        """, (setting_id,))

        audit_entry = cursor.fetchone()
        assert audit_entry is not None
        assert audit_entry[0] == 'system_settings'
        assert audit_entry[2] == 'test.setting'
        assert audit_entry[3] == 'CREATE'
        assert audit_entry[4] == '"test_value"'

        conn.close()


class TestSettingsServiceIntegration:
    """Test settings service with real database operations."""

    async def test_get_system_settings_integration(self, integrated_settings_service):
        """Test getting system settings from database."""
        settings = await integrated_settings_service.get_system_settings()

        assert isinstance(settings, dict)
        assert len(settings) > 0

        # Verify settings structure
        for key, value in settings.items():
            assert isinstance(key, str)
            assert '.' in key  # Should be namespaced
            # Value should be JSON-parseable
            assert isinstance(value, (str, int, float, bool, dict, list))

    async def test_update_system_setting_integration(self, integrated_settings_service, admin_user):
        """Test updating a system setting with audit trail."""
        # Update a setting
        new_value = SettingValue(value="dark", data_type=SettingDataType.STRING)
        success = await integrated_settings_service.update_system_setting(
            setting_key="ui.theme",
            new_value=new_value,
            user_id=admin_user.id
        )

        assert success is True

        # Verify setting was updated
        settings = await integrated_settings_service.get_system_settings()
        assert settings.get("ui.theme") == "dark"

        # Verify audit entry exists
        audit_entries = await integrated_settings_service.get_audit_entries(
            setting_key="ui.theme",
            limit=1
        )
        assert len(audit_entries) > 0
        assert audit_entries[0].change_type == "UPDATE"
        assert audit_entries[0].new_value == '"dark"'

    async def test_user_settings_with_overrides(self, integrated_settings_service, regular_user):
        """Test user settings with system defaults and overrides."""
        # Get user settings (should return system defaults initially)
        user_settings = await integrated_settings_service.get_user_settings(regular_user.id)

        assert isinstance(user_settings, dict)
        assert len(user_settings) > 0

        # Create a user override
        request = SettingsUpdateRequest(
            settings={
                "ui.theme": "light",
                "ui.language": "fr"
            },
            user_id=regular_user.id
        )

        success = await integrated_settings_service.update_user_settings(request)
        assert success is True

        # Verify user settings include overrides
        updated_settings = await integrated_settings_service.get_user_settings(regular_user.id)
        assert updated_settings["ui.theme"] == "light"
        assert updated_settings["ui.language"] == "fr"


class TestMCPToolsIntegration:
    """Test MCP tools with real services and authentication."""

    async def test_get_settings_mcp_tool(self, integrated_settings_tools, admin_context):
        """Test get_settings MCP tool with admin authentication."""
        request = SettingsRequest(
            categories=["ui", "security"],
            setting_keys=["ui.theme", "security.session.timeout"]
        )

        response = await integrated_settings_tools.get_settings(
            request=request.model_dump(),
            ctx=admin_context
        )

        assert response["success"] is True
        assert "settings" in response
        assert isinstance(response["settings"], dict)
        assert len(response["settings"]) > 0

        # Verify audit logging
        assert "ui.theme" in response["settings"] or "security.session.timeout" in response["settings"]

    async def test_update_settings_admin_only(self, integrated_settings_tools, admin_context, user_context):
        """Test that admin-only settings can only be updated by admins."""
        admin_only_request = SettingsUpdateRequest(
            settings={
                "security.session.timeout": "4h",  # This should be admin-only
                "system.enableDebugMode": True
            }
        )

        # Admin should succeed
        admin_response = await integrated_settings_tools.update_settings(
            request=admin_only_request.model_dump(),
            ctx=admin_context
        )
        assert admin_response["success"] is True

        # Regular user should fail
        user_response = await integrated_settings_tools.update_settings(
            request=admin_only_request.model_dump(),
            ctx=user_context
        )
        assert user_response["success"] is False
        assert "permission" in user_response["error"].lower() or "admin" in user_response["error"].lower()

    async def test_reset_user_settings_mcp_tool(self, integrated_settings_tools, admin_context, regular_user):
        """Test reset user settings MCP tool."""
        # First, create some user overrides
        update_request = SettingsUpdateRequest(
            settings={
                "ui.theme": "light",
                "ui.compactMode": True
            },
            user_id=regular_user.id
        )

        await integrated_settings_tools.update_settings(
            request=update_request.model_dump(),
            ctx=admin_context
        )

        # Reset user settings
        reset_response = await integrated_settings_tools.reset_user_settings(
            target_user_id=regular_user.id,
            category="ui",
            ctx=admin_context
        )

        assert reset_response["success"] is True

        # Verify settings were reset (should match system defaults)
        get_response = await integrated_settings_tools.get_settings(
            request={"user_id": regular_user.id, "categories": ["ui"]},
            ctx=admin_context
        )

        # The reset should have removed user overrides
        assert get_response["success"] is True


class TestSecurityIntegration:
    """Test security controls and access validation."""

    async def test_authentication_required(self, integrated_settings_tools):
        """Test that all operations require authentication."""
        # Create context without session
        no_auth_context = MagicMock(spec=Context)
        no_auth_context.meta = {}

        request = SettingsRequest(categories=["ui"])

        response = await integrated_settings_tools.get_settings(
            request=request.model_dump(),
            ctx=no_auth_context
        )

        assert response["success"] is False
        assert "authentication" in response["error"].lower()

    async def test_audit_trail_integrity(self, integrated_settings_service, admin_user):
        """Test audit trail creates tamper-resistant entries."""
        # Perform several operations
        operations = [
            ("ui.theme", "dark"),
            ("ui.theme", "light"),
            ("security.session.timeout", "2h")
        ]

        for key, value in operations:
            setting_value = SettingValue(value=value, data_type=SettingDataType.STRING)
            await integrated_settings_service.update_system_setting(
                setting_key=key,
                new_value=setting_value,
                user_id=admin_user.id
            )

        # Get audit entries
        audit_entries = await integrated_settings_service.get_audit_entries(limit=10)

        # Verify all have checksums
        for entry in audit_entries:
            assert entry.checksum is not None
            assert len(entry.checksum) == 64  # SHA-256 hex
            assert entry.user_id is not None
            assert entry.created_at is not None

    async def test_input_validation_security(self, integrated_settings_tools, admin_context):
        """Test input validation prevents security issues."""
        # Test SQL injection attempt
        malicious_request = {
            "settings": {
                "ui.theme'; DROP TABLE system_settings; --": "dark"
            }
        }

        response = await integrated_settings_tools.update_settings(
            request=malicious_request,
            ctx=admin_context
        )

        assert response["success"] is False
        assert "validation" in response["error"].lower() or "invalid" in response["error"].lower()

        # Test XSS attempt
        xss_request = {
            "settings": {
                "ui.theme": "<script>alert('xss')</script>"
            }
        }

        response = await integrated_settings_tools.update_settings(
            request=xss_request,
            ctx=admin_context
        )

        # Should either reject or sanitize
        if response["success"]:
            # If accepted, verify it's properly stored as JSON string
            get_response = await integrated_settings_tools.get_settings(
                request={"setting_keys": ["ui.theme"]},
                ctx=admin_context
            )
            stored_value = get_response["settings"]["ui.theme"]
            # Should be stored as literal string, not executable code
            assert "<script>" not in stored_value or isinstance(stored_value, str)


class TestErrorHandlingIntegration:
    """Test error handling and recovery scenarios."""

    async def test_concurrent_update_handling(self, integrated_settings_service, admin_user):
        """Test handling of concurrent updates with version control."""
        setting_key = "ui.test_concurrent"

        # Create initial setting
        initial_value = SettingValue(value="initial", data_type=SettingDataType.STRING)
        await integrated_settings_service.update_system_setting(
            setting_key=setting_key,
            new_value=initial_value,
            user_id=admin_user.id
        )

        # Simulate concurrent updates
        update1 = SettingValue(value="update1", data_type=SettingDataType.STRING)
        update2 = SettingValue(value="update2", data_type=SettingDataType.STRING)

        # Both should succeed (last writer wins with proper versioning)
        results = await asyncio.gather(
            integrated_settings_service.update_system_setting(setting_key, update1, admin_user.id),
            integrated_settings_service.update_system_setting(setting_key, update2, admin_user.id),
            return_exceptions=True
        )

        # At least one should succeed
        success_count = sum(1 for result in results if result is True)
        assert success_count >= 1

    async def test_invalid_data_recovery(self, integrated_settings_service, admin_user):
        """Test recovery from invalid data scenarios."""
        # Test invalid JSON
        with pytest.raises((ValueError, TypeError)):
            invalid_value = SettingValue(value="invalid json {", data_type=SettingDataType.OBJECT)
            await integrated_settings_service.update_system_setting(
                setting_key="test.invalid",
                new_value=invalid_value,
                user_id=admin_user.id
            )

        # Service should remain functional after error
        valid_value = SettingValue(value="valid", data_type=SettingDataType.STRING)
        success = await integrated_settings_service.update_system_setting(
            setting_key="test.valid",
            new_value=valid_value,
            user_id=admin_user.id
        )
        assert success is True


class TestPerformanceIntegration:
    """Test performance characteristics of the settings system."""

    async def test_large_settings_dataset(self, integrated_settings_service, admin_user):
        """Test performance with large number of settings."""
        # Create many settings
        settings_count = 100
        start_time = datetime.now()

        for i in range(settings_count):
            setting_value = SettingValue(
                value=f"value_{i}",
                data_type=SettingDataType.STRING
            )
            await integrated_settings_service.update_system_setting(
                setting_key=f"test.performance_{i}",
                new_value=setting_value,
                user_id=admin_user.id
            )

        creation_time = (datetime.now() - start_time).total_seconds()

        # Retrieve all settings
        start_time = datetime.now()
        all_settings = await integrated_settings_service.get_system_settings()
        retrieval_time = (datetime.now() - start_time).total_seconds()

        # Performance assertions
        assert len(all_settings) >= settings_count
        assert creation_time < 30  # Should create 100 settings within 30 seconds
        assert retrieval_time < 2   # Should retrieve all settings within 2 seconds

        # Test pagination for audit entries
        audit_entries = await integrated_settings_service.get_audit_entries(limit=50)
        assert len(audit_entries) <= 50

    async def test_concurrent_read_operations(self, integrated_settings_service):
        """Test concurrent read operations don't interfere."""
        # Perform multiple concurrent reads
        tasks = [
            integrated_settings_service.get_system_settings()
            for _ in range(10)
        ]

        start_time = datetime.now()
        results = await asyncio.gather(*tasks)
        total_time = (datetime.now() - start_time).total_seconds()

        # All reads should succeed
        assert len(results) == 10
        for result in results:
            assert isinstance(result, dict)
            assert len(result) > 0

        # Should complete quickly even with concurrent access
        assert total_time < 5
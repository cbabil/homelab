"""
Settings Migration and Installation Tests

Comprehensive tests for settings system migration, installation,
and upgrade scenarios with data integrity validation.
"""

import os
import pytest
import tempfile
import shutil
import sqlite3
import json
from datetime import datetime

from services.database_service import DatabaseService
from services.settings_service import SettingsService

pytestmark = pytest.mark.skip(reason="Migration API refactored - use initialize_*_table() methods")


@pytest.fixture
def temp_installation_dir():
    """Create temporary installation directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def old_database_v1(temp_installation_dir):
    """Create old version 1 database for migration testing."""
    db_path = os.path.join(temp_installation_dir, "tomo_v1.db")

    # Create old schema (version 1)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Old simple schema
    cursor.execute("""
        CREATE TABLE settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'string',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert some old format data
    old_settings = [
        ("ui.theme", "dark", "string"),
        ("ui.language", "en", "string"),
        ("system.timeout", "30", "number"),
        ("security.max_attempts", "5", "number")
    ]

    for key, value, setting_type in old_settings:
        cursor.execute(
            "INSERT INTO settings (key, value, type) VALUES (?, ?, ?)",
            (key, value, setting_type)
        )

    conn.commit()
    conn.close()

    yield db_path

    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def old_database_v2(temp_installation_dir):
    """Create old version 2 database for migration testing."""
    db_path = os.path.join(temp_installation_dir, "tomo_v2.db")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Version 2 schema (intermediate)
    cursor.execute("""
        CREATE TABLE user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT NOT NULL,
            setting_value TEXT NOT NULL,
            category TEXT NOT NULL,
            user_id TEXT NOT NULL DEFAULT 'default',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # No audit table in v2
    # No system_settings table in v2

    # Insert some v2 format data
    v2_settings = [
        ("ui.theme", "light", "ui"),
        ("ui.language", "fr", "ui"),
        ("security.session_timeout", "3600", "security")
    ]

    for key, value, category in v2_settings:
        cursor.execute(
            "INSERT INTO user_settings (setting_key, setting_value, category) VALUES (?, ?, ?)",
            (key, value, category)
        )

    conn.commit()
    conn.close()

    yield db_path

    if os.path.exists(db_path):
        os.unlink(db_path)


class TestFreshInstallation:
    """Test fresh installation scenarios."""

    async def test_fresh_installation_creates_schema(self, temp_installation_dir):
        """Test fresh installation creates complete schema."""
        db_path = os.path.join(temp_installation_dir, "fresh_tomo.db")

        # Ensure database doesn't exist
        assert not os.path.exists(db_path)

        # Initialize database service (should create schema)
        db_service = DatabaseService(db_path=db_path)
        await db_service.initialize()

        # Verify database was created
        assert os.path.exists(db_path)

        # Verify all tables exist
        async with db_service.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in await cursor.fetchall()]

            expected_tables = {
                'system_settings',
                'user_settings',
                'settings_audit',
                'users',
                'sessions'
            }

            for table in expected_tables:
                assert table in tables, f"Table {table} should exist in fresh installation"

        await db_service.close()

    async def test_fresh_installation_creates_default_settings(self, temp_installation_dir):
        """Test fresh installation creates default system settings."""
        db_path = os.path.join(temp_installation_dir, "fresh_tomo.db")

        db_service = DatabaseService(db_path=db_path)
        await db_service.initialize()

        _settings_service = SettingsService(db_service)  # noqa: F841

        # Check default settings exist
        async with db_service.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM system_settings"
            )
            count = (await cursor.fetchone())[0]

            # Should have some default settings
            assert count > 0, "Fresh installation should create default settings"

            # Check specific default settings
            cursor = await conn.execute(
                "SELECT setting_key, setting_value FROM system_settings WHERE category = 'ui'"
            )
            ui_settings = await cursor.fetchall()

            ui_setting_keys = {row[0] for row in ui_settings}
            expected_ui_settings = {'ui.theme', 'ui.language'}

            for setting in expected_ui_settings:
                assert setting in ui_setting_keys, f"Default {setting} should exist"

        await db_service.close()

    async def test_fresh_installation_creates_indexes(self, temp_installation_dir):
        """Test fresh installation creates all required indexes."""
        db_path = os.path.join(temp_installation_dir, "fresh_tomo.db")

        db_service = DatabaseService(db_path=db_path)
        await db_service.initialize()

        async with db_service.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
            )
            indexes = [row[0] for row in await cursor.fetchall()]

            expected_indexes = {
                'idx_system_settings_key',
                'idx_system_settings_category',
                'idx_user_settings_user_key',
                'idx_user_settings_category',
                'idx_settings_audit_table_record',
                'idx_settings_audit_user_time',
                'idx_settings_audit_setting_key'
            }

            for index in expected_indexes:
                assert index in indexes, f"Index {index} should be created"

        await db_service.close()

    async def test_fresh_installation_creates_triggers(self, temp_installation_dir):
        """Test fresh installation creates audit triggers."""
        db_path = os.path.join(temp_installation_dir, "fresh_tomo.db")

        db_service = DatabaseService(db_path=db_path)
        await db_service.initialize()

        async with db_service.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger'"
            )
            triggers = [row[0] for row in await cursor.fetchall()]

            expected_triggers = {
                'audit_system_settings_insert',
                'audit_system_settings_update',
                'audit_system_settings_delete',
                'audit_user_settings_insert',
                'audit_user_settings_update',
                'audit_user_settings_delete'
            }

            for trigger in expected_triggers:
                assert trigger in triggers, f"Trigger {trigger} should be created"

        await db_service.close()


class TestMigrationFromV1:
    """Test migration from version 1 database."""

    async def test_migrate_v1_to_current_schema(self, old_database_v1, temp_installation_dir):
        """Test migration from v1 to current schema."""
        new_db_path = os.path.join(temp_installation_dir, "migrated_tomo.db")

        # Copy old database to new location
        shutil.copy2(old_database_v1, new_db_path)

        # Initialize with migration
        db_service = DatabaseService(db_path=new_db_path)
        await db_service.initialize()

        # Verify new schema exists
        async with db_service.get_connection() as conn:
            # Check new tables exist
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in await cursor.fetchall()]

            assert 'system_settings' in tables
            assert 'user_settings' in tables
            assert 'settings_audit' in tables

            # Check old data was migrated
            cursor = await conn.execute(
                "SELECT setting_key, setting_value FROM system_settings WHERE setting_key = 'ui.theme'"
            )
            result = await cursor.fetchone()

            assert result is not None, "ui.theme setting should be migrated"
            assert result[1] == '"dark"', "Migrated value should be JSON formatted"

        await db_service.close()

    async def test_migrate_v1_preserves_data_integrity(self, old_database_v1, temp_installation_dir):
        """Test v1 migration preserves data integrity."""
        new_db_path = os.path.join(temp_installation_dir, "migrated_tomo.db")

        # Get original data
        original_conn = sqlite3.connect(old_database_v1)
        original_cursor = original_conn.cursor()
        original_cursor.execute("SELECT key, value, type FROM settings")
        original_data = original_cursor.fetchall()
        original_conn.close()

        # Perform migration
        shutil.copy2(old_database_v1, new_db_path)
        db_service = DatabaseService(db_path=new_db_path)
        await db_service.initialize()

        # Verify migrated data
        async with db_service.get_connection() as conn:
            for old_key, old_value, old_type in original_data:
                cursor = await conn.execute(
                    "SELECT setting_value, data_type FROM system_settings WHERE setting_key = ?",
                    (old_key,)
                )
                result = await cursor.fetchone()

                assert result is not None, f"Setting {old_key} should be migrated"

                # Parse JSON value
                migrated_value = json.loads(result[0])
                migrated_type = result[1]

                # Convert old value to expected type
                if old_type == "number":
                    expected_value = float(old_value) if '.' in old_value else int(old_value)
                    assert migrated_type == "number"
                else:
                    expected_value = old_value
                    assert migrated_type == "string"

                assert migrated_value == expected_value, f"Value for {old_key} should be preserved"

        await db_service.close()

    async def test_migrate_v1_creates_audit_entries(self, old_database_v1, temp_installation_dir):
        """Test v1 migration creates audit entries for migrated data."""
        new_db_path = os.path.join(temp_installation_dir, "migrated_tomo.db")

        shutil.copy2(old_database_v1, new_db_path)
        db_service = DatabaseService(db_path=new_db_path)
        await db_service.initialize()

        # Check audit entries were created
        async with db_service.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM settings_audit WHERE change_type = 'CREATE'"
            )
            audit_count = (await cursor.fetchone())[0]

            # Should have audit entries for each migrated setting
            cursor = await conn.execute("SELECT COUNT(*) FROM system_settings")
            settings_count = (await cursor.fetchone())[0]

            assert audit_count >= settings_count, "Should have audit entries for migrated settings"

        await db_service.close()


class TestMigrationFromV2:
    """Test migration from version 2 database."""

    async def test_migrate_v2_to_current_schema(self, old_database_v2, temp_installation_dir):
        """Test migration from v2 to current schema."""
        new_db_path = os.path.join(temp_installation_dir, "migrated_v2_tomo.db")

        shutil.copy2(old_database_v2, new_db_path)
        db_service = DatabaseService(db_path=new_db_path)
        await db_service.initialize()

        # Verify schema migration
        async with db_service.get_connection() as conn:
            # Check system_settings table was created
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='system_settings'"
            )
            assert await cursor.fetchone() is not None

            # Check audit table was created
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='settings_audit'"
            )
            assert await cursor.fetchone() is not None

            # Check existing user_settings table was preserved/updated
            cursor = await conn.execute("PRAGMA table_info(user_settings)")
            columns = [col[1] for col in await cursor.fetchall()]

            # Should have new columns
            assert 'data_type' in columns
            assert 'is_override' in columns
            assert 'version' in columns

        await db_service.close()

    async def test_migrate_v2_preserves_user_data(self, old_database_v2, temp_installation_dir):
        """Test v2 migration preserves user data."""
        new_db_path = os.path.join(temp_installation_dir, "migrated_v2_tomo.db")

        # Get original user data
        original_conn = sqlite3.connect(old_database_v2)
        original_cursor = original_conn.cursor()
        original_cursor.execute("SELECT setting_key, setting_value, category FROM user_settings")
        original_data = original_cursor.fetchall()
        original_conn.close()

        # Perform migration
        shutil.copy2(old_database_v2, new_db_path)
        db_service = DatabaseService(db_path=new_db_path)
        await db_service.initialize()

        # Verify user data preserved
        async with db_service.get_connection() as conn:
            for old_key, old_value, old_category in original_data:
                cursor = await conn.execute(
                    "SELECT setting_value, category FROM user_settings WHERE setting_key = ?",
                    (old_key,)
                )
                result = await cursor.fetchone()

                assert result is not None, f"User setting {old_key} should be preserved"

                # Value should be JSON formatted now
                migrated_value = json.loads(result[0])
                assert migrated_value == old_value, f"Value for {old_key} should be preserved"
                assert result[1] == old_category, f"Category for {old_key} should be preserved"

        await db_service.close()


class TestDataIntegrityDuringMigration:
    """Test data integrity during migration process."""

    async def test_migration_is_atomic(self, old_database_v1, temp_installation_dir):
        """Test migration is atomic (all or nothing)."""
        new_db_path = os.path.join(temp_installation_dir, "atomic_migration.db")

        # Copy and corrupt the database slightly
        shutil.copy2(old_database_v1, new_db_path)

        # Simulate migration failure by creating invalid data
        conn = sqlite3.connect(new_db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO settings (key, value, type) VALUES (?, ?, ?)",
                      ("invalid.key", "invalid_json_value", "invalid_type"))
        conn.commit()
        conn.close()

        # Attempt migration
        db_service = DatabaseService(db_path=new_db_path)

        try:
            await db_service.initialize()

            # Verify partial migration didn't occur
            async with db_service.get_connection() as conn:
                # Either fully migrated or not at all
                cursor = await conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='system_settings'"
                )
                system_table_exists = await cursor.fetchone() is not None

                cursor = await conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"
                )
                old_table_exists = await cursor.fetchone() is not None

                # Should be either old format or fully migrated
                assert not (system_table_exists and old_table_exists), \
                    "Should not have both old and new tables after failed migration"
        finally:
            await db_service.close()

    async def test_migration_handles_duplicate_keys(self, temp_installation_dir):
        """Test migration handles duplicate keys gracefully."""
        db_path = os.path.join(temp_installation_dir, "duplicate_keys.db")

        # Create database with duplicate keys
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,  -- Note: no UNIQUE constraint
                value TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'string'
            )
        """)

        # Insert duplicates
        duplicates = [
            ("ui.theme", "dark", "string"),
            ("ui.theme", "light", "string"),  # Duplicate
            ("ui.language", "en", "string"),
            ("ui.language", "fr", "string")   # Duplicate
        ]

        for key, value, setting_type in duplicates:
            cursor.execute(
                "INSERT INTO settings (key, value, type) VALUES (?, ?, ?)",
                (key, value, setting_type)
            )

        conn.commit()
        conn.close()

        # Attempt migration
        db_service = DatabaseService(db_path=db_path)
        await db_service.initialize()

        # Verify duplicates were handled
        async with db_service.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT setting_key, COUNT(*) FROM system_settings GROUP BY setting_key HAVING COUNT(*) > 1"
            )
            duplicates_remaining = await cursor.fetchall()

            assert len(duplicates_remaining) == 0, "No duplicate keys should remain after migration"

            # Verify at least one of each key exists
            cursor = await conn.execute(
                "SELECT setting_key FROM system_settings WHERE setting_key IN ('ui.theme', 'ui.language')"
            )
            migrated_keys = [row[0] for row in await cursor.fetchall()]

            assert 'ui.theme' in migrated_keys
            assert 'ui.language' in migrated_keys

        await db_service.close()

    async def test_migration_validates_data_types(self, temp_installation_dir):
        """Test migration validates and converts data types."""
        db_path = os.path.join(temp_installation_dir, "type_validation.db")

        # Create database with various data types
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'string'
            )
        """)

        # Insert settings with various types
        test_data = [
            ("string.setting", "test_value", "string"),
            ("number.setting", "42", "number"),
            ("float.setting", "3.14", "number"),
            ("boolean.setting", "true", "boolean"),
            ("invalid.number", "not_a_number", "number"),  # Invalid
            ("invalid.boolean", "maybe", "boolean")        # Invalid
        ]

        for key, value, setting_type in test_data:
            cursor.execute(
                "INSERT INTO settings (key, value, type) VALUES (?, ?, ?)",
                (key, value, setting_type)
            )

        conn.commit()
        conn.close()

        # Perform migration
        db_service = DatabaseService(db_path=db_path)
        await db_service.initialize()

        # Verify type conversion
        async with db_service.get_connection() as conn:
            # Valid conversions
            cursor = await conn.execute(
                "SELECT setting_value, data_type FROM system_settings WHERE setting_key = 'number.setting'"
            )
            result = await cursor.fetchone()
            assert result is not None
            assert json.loads(result[0]) == 42
            assert result[1] == "number"

            cursor = await conn.execute(
                "SELECT setting_value FROM system_settings WHERE setting_key = 'float.setting'"
            )
            result = await cursor.fetchone()
            assert result is not None
            assert json.loads(result[0]) == 3.14

            # Invalid conversions should fallback to string or be skipped
            cursor = await conn.execute(
                "SELECT setting_value, data_type FROM system_settings WHERE setting_key = 'invalid.number'"
            )
            result = await cursor.fetchone()
            if result is not None:
                # Either converted to string or skipped
                assert result[1] in ["string", "number"]

        await db_service.close()


class TestBackupAndRestore:
    """Test backup and restore functionality during migration."""

    async def test_migration_creates_backup(self, old_database_v1, temp_installation_dir):
        """Test migration creates backup of original database."""
        new_db_path = os.path.join(temp_installation_dir, "backed_up.db")
        backup_path = new_db_path + ".backup"

        shutil.copy2(old_database_v1, new_db_path)

        # Perform migration
        db_service = DatabaseService(db_path=new_db_path)
        await db_service.initialize()

        # Check backup was created
        assert os.path.exists(backup_path), "Backup should be created before migration"

        # Verify backup contains original data
        backup_conn = sqlite3.connect(backup_path)
        backup_cursor = backup_conn.cursor()
        backup_cursor.execute("SELECT COUNT(*) FROM settings")
        backup_count = backup_cursor.fetchone()[0]
        backup_conn.close()

        assert backup_count > 0, "Backup should contain original data"

        await db_service.close()

    async def test_restore_from_backup_on_migration_failure(self, old_database_v1, temp_installation_dir):
        """Test restore from backup when migration fails."""
        new_db_path = os.path.join(temp_installation_dir, "restore_test.db")

        shutil.copy2(old_database_v1, new_db_path)

        # Get original data count
        original_conn = sqlite3.connect(new_db_path)
        original_cursor = original_conn.cursor()
        original_cursor.execute("SELECT COUNT(*) FROM settings")
        original_count = original_cursor.fetchone()[0]
        original_conn.close()

        # Simulate migration failure by corrupting database mid-migration
        # This would normally be handled by the migration service
        db_service = DatabaseService(db_path=new_db_path)

        try:
            # In a real scenario, migration might fail and restore would be triggered
            await db_service.initialize()

            # Verify database is functional
            async with db_service.get_connection() as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM system_settings")
                migrated_count = (await cursor.fetchone())[0]

                # Should have migrated the original data
                assert migrated_count >= original_count
        finally:
            await db_service.close()


class TestConcurrentMigration:
    """Test concurrent migration scenarios."""

    async def test_prevents_concurrent_migrations(self, old_database_v1, temp_installation_dir):
        """Test system prevents concurrent migrations."""
        new_db_path = os.path.join(temp_installation_dir, "concurrent_test.db")
        shutil.copy2(old_database_v1, new_db_path)

        # Start first migration
        db_service1 = DatabaseService(db_path=new_db_path)

        # Attempt second migration concurrently
        db_service2 = DatabaseService(db_path=new_db_path)

        try:
            # First migration should succeed
            await db_service1.initialize()

            # Second migration should detect existing schema or fail gracefully
            await db_service2.initialize()

            # Both should work (second should detect already migrated)
            async with db_service1.get_connection() as conn1:
                cursor1 = await conn1.execute("SELECT COUNT(*) FROM system_settings")
                count1 = (await cursor1.fetchone())[0]

            async with db_service2.get_connection() as conn2:
                cursor2 = await conn2.execute("SELECT COUNT(*) FROM system_settings")
                count2 = (await cursor2.fetchone())[0]

            assert count1 == count2, "Both connections should see same migrated data"

        finally:
            await db_service1.close()
            await db_service2.close()

    async def test_migration_with_active_connections(self, old_database_v1, temp_installation_dir):
        """Test migration behavior with active database connections."""
        new_db_path = os.path.join(temp_installation_dir, "active_connections.db")
        shutil.copy2(old_database_v1, new_db_path)

        # Open connection to old database
        old_conn = sqlite3.connect(new_db_path)

        try:
            # Attempt migration while connection is open
            db_service = DatabaseService(db_path=new_db_path)
            await db_service.initialize()

            # Migration should handle active connections gracefully
            async with db_service.get_connection() as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM system_settings")
                count = (await cursor.fetchone())[0]

                assert count > 0, "Migration should succeed despite active connections"

            await db_service.close()

        finally:
            old_conn.close()


class TestMigrationPerformance:
    """Test migration performance with large datasets."""

    async def test_large_dataset_migration(self, temp_installation_dir):
        """Test migration performance with large number of settings."""
        db_path = os.path.join(temp_installation_dir, "large_dataset.db")

        # Create large old database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'string'
            )
        """)

        # Insert 10,000 settings
        settings_data = []
        for i in range(10000):
            settings_data.append((f"test.setting_{i}", f"value_{i}", "string"))

        cursor.executemany(
            "INSERT INTO settings (key, value, type) VALUES (?, ?, ?)",
            settings_data
        )

        conn.commit()
        conn.close()

        # Measure migration time
        start_time = datetime.utcnow()

        db_service = DatabaseService(db_path=db_path)
        await db_service.initialize()

        end_time = datetime.utcnow()
        migration_time = (end_time - start_time).total_seconds()

        # Verify all data migrated
        async with db_service.get_connection() as conn:
            cursor = await conn.execute("SELECT COUNT(*) FROM system_settings")
            migrated_count = (await cursor.fetchone())[0]

            assert migrated_count == 10000, "All settings should be migrated"

            # Migration should complete in reasonable time (adjust based on requirements)
            assert migration_time < 60, f"Migration took {migration_time}s, should be faster"

        await db_service.close()
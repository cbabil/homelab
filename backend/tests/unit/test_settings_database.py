"""
Database Schema and Integrity Tests for Settings System

Comprehensive tests for database schema, constraints, triggers,
audit trail functionality, and data integrity protection.
"""

import os
import pytest
import aiosqlite
import tempfile
import json
from datetime import datetime
from pathlib import Path


@pytest.fixture
async def temp_db():
    """Create temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_homelab.db")

    # Read and execute schema
    schema_path = Path(__file__).parent.parent.parent / "sql" / "init_settings_schema.sql"

    async with aiosqlite.connect(db_path) as connection:
        # Enable foreign keys
        await connection.execute("PRAGMA foreign_keys = ON")

        # Read and execute schema
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        # Execute the schema using executescript method for async
        await connection.executescript(schema_sql)

        await connection.commit()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestDatabaseSchema:
    """Test database schema creation and structure."""

    async def test_schema_creation(self, temp_db):
        """Test that all required tables are created with correct structure."""
        async with aiosqlite.connect(temp_db) as connection:
            # Check system_settings table
            cursor = await connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='system_settings'"
            )
            result = await cursor.fetchone()
            assert result is not None, "system_settings table should exist"

            # Check user_settings table
            cursor = await connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'"
            )
            result = await cursor.fetchone()
            assert result is not None, "user_settings table should exist"

            # Check settings_audit table
            cursor = await connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='settings_audit'"
            )
            result = await cursor.fetchone()
            assert result is not None, "settings_audit table should exist"

    async def test_system_settings_structure(self, temp_db):
        """Test system_settings table structure."""
        async with aiosqlite.connect(temp_db) as connection:
            cursor = await connection.execute("PRAGMA table_info(system_settings)")
            columns = await cursor.fetchall()

            column_names = [col[1] for col in columns]
            expected_columns = [
                'id', 'setting_key', 'setting_value', 'data_type', 'category',
                'scope', 'is_admin_only', 'description', 'validation_rules',
                'created_at', 'updated_at', 'updated_by', 'version'
            ]

            for col in expected_columns:
                assert col in column_names, f"Column {col} should exist in system_settings"

    async def test_user_settings_structure(self, temp_db):
        """Test user_settings table structure."""
        async with aiosqlite.connect(temp_db) as connection:
            cursor = await connection.execute("PRAGMA table_info(user_settings)")
            columns = await cursor.fetchall()

            column_names = [col[1] for col in columns]
            expected_columns = [
                'id', 'user_id', 'setting_key', 'setting_value', 'data_type',
                'category', 'is_override', 'created_at', 'updated_at', 'version'
            ]

            for col in expected_columns:
                assert col in column_names, f"Column {col} should exist in user_settings"

    async def test_settings_audit_structure(self, temp_db):
        """Test settings_audit table structure."""
        async with aiosqlite.connect(temp_db) as connection:
            cursor = await connection.execute("PRAGMA table_info(settings_audit)")
            columns = await cursor.fetchall()

            column_names = [col[1] for col in columns]
            expected_columns = [
                'id', 'table_name', 'record_id', 'user_id', 'setting_key',
                'old_value', 'new_value', 'change_type', 'change_reason',
                'client_ip', 'user_agent', 'created_at', 'checksum'
            ]

            for col in expected_columns:
                assert col in column_names, f"Column {col} should exist in settings_audit"

    async def test_primary_keys(self, temp_db):
        """Test primary key constraints."""
        async with aiosqlite.connect(temp_db) as connection:
            # Test system_settings primary key
            cursor = await connection.execute("PRAGMA table_info(system_settings)")
            columns = await cursor.fetchall()
            pk_columns = [col[1] for col in columns if col[5] == 1]  # pk column
            assert 'id' in pk_columns, "system_settings should have id as primary key"

            # Test user_settings primary key
            cursor = await connection.execute("PRAGMA table_info(user_settings)")
            columns = await cursor.fetchall()
            pk_columns = [col[1] for col in columns if col[5] == 1]
            assert 'id' in pk_columns, "user_settings should have id as primary key"

            # Test settings_audit primary key
            cursor = await connection.execute("PRAGMA table_info(settings_audit)")
            columns = await cursor.fetchall()
            pk_columns = [col[1] for col in columns if col[5] == 1]
            assert 'id' in pk_columns, "settings_audit should have id as primary key"

    async def test_indexes(self, temp_db):
        """Test that required indexes are created."""
        async with aiosqlite.connect(temp_db) as connection:
            cursor = await connection.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
            )
            indexes = await cursor.fetchall()
            index_names = [idx[0] for idx in indexes]

            expected_indexes = [
                'idx_system_settings_key',
                'idx_system_settings_category',
                'idx_user_settings_user_key',
                'idx_user_settings_category',
                'idx_settings_audit_table_record',
                'idx_settings_audit_user_time',
                'idx_settings_audit_setting_key'
            ]

            for idx in expected_indexes:
                assert idx in index_names, f"Index {idx} should exist"


class TestDatabaseConstraints:
    """Test database constraints and validation."""

    async def test_unique_constraints(self, temp_db):
        """Test unique constraints enforcement."""
        async with aiosqlite.connect(temp_db) as connection:
            await connection.execute("PRAGMA foreign_keys = ON")

            # Insert first setting
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

            # Try to insert duplicate setting_key - should fail
            with pytest.raises(aiosqlite.IntegrityError):
                await connection.execute(
                    """
                    INSERT INTO system_settings (
                        setting_key, setting_value, data_type, category, scope,
                        is_admin_only, created_at, updated_at, version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    ("ui.theme", '"light"', "string", "ui", "user_overridable",
                     0, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), 1)
                )

    async def test_check_constraints(self, temp_db):
        """Test CHECK constraints enforcement."""
        async with aiosqlite.connect(temp_db) as connection:
            await connection.execute("PRAGMA foreign_keys = ON")

            # Test invalid data_type
            with pytest.raises(aiosqlite.IntegrityError):
                await connection.execute(
                    """
                    INSERT INTO system_settings (
                        setting_key, setting_value, data_type, category, scope,
                        is_admin_only, created_at, updated_at, version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    ("ui.theme", '"dark"', "invalid_type", "ui", "user_overridable",
                     0, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), 1)
                )

            # Test invalid category
            with pytest.raises(aiosqlite.IntegrityError):
                await connection.execute(
                    """
                    INSERT INTO system_settings (
                        setting_key, setting_value, data_type, category, scope,
                        is_admin_only, created_at, updated_at, version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    ("ui.theme", '"dark"', "string", "invalid_category", "user_overridable",
                     0, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), 1)
                )

            # Test invalid scope
            with pytest.raises(aiosqlite.IntegrityError):
                await connection.execute(
                    """
                    INSERT INTO system_settings (
                        setting_key, setting_value, data_type, category, scope,
                        is_admin_only, created_at, updated_at, version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    ("ui.theme", '"dark"', "string", "ui", "invalid_scope",
                     0, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), 1)
                )

    async def test_not_null_constraints(self, temp_db):
        """Test NOT NULL constraints enforcement."""
        async with aiosqlite.connect(temp_db) as connection:
            await connection.execute("PRAGMA foreign_keys = ON")

            # Test missing required fields
            with pytest.raises(aiosqlite.IntegrityError):
                await connection.execute(
                    """
                    INSERT INTO system_settings (
                        setting_value, data_type, category, scope,
                        is_admin_only, created_at, updated_at, version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    ('"dark"', "string", "ui", "user_overridable",
                     0, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), 1)
                )

    async def test_version_constraint(self, temp_db):
        """Test version constraint (>= 1)."""
        async with aiosqlite.connect(temp_db) as connection:
            await connection.execute("PRAGMA foreign_keys = ON")

            # Test invalid version (< 1)
            with pytest.raises(aiosqlite.IntegrityError):
                await connection.execute(
                    """
                    INSERT INTO system_settings (
                        setting_key, setting_value, data_type, category, scope,
                        is_admin_only, created_at, updated_at, version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    ("ui.theme", '"dark"', "string", "ui", "user_overridable",
                     0, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), 0)
                )


class TestAuditTriggers:
    """Test audit trigger functionality."""

    async def test_insert_trigger(self, temp_db):
        """Test audit trigger on INSERT operations."""
        async with aiosqlite.connect(temp_db) as connection:
            await connection.execute("PRAGMA foreign_keys = ON")

            # Insert a new setting
            cursor = await connection.execute(
                """
                INSERT INTO system_settings (
                    setting_key, setting_value, data_type, category, scope,
                    is_admin_only, created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("ui.theme", '"dark"', "string", "ui", "user_overridable",
                 0, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), 1)
            )
            setting_id = cursor.lastrowid
            await connection.commit()

            # Check audit entry was created
            cursor = await connection.execute(
                """
                SELECT table_name, record_id, setting_key, new_value, change_type
                FROM settings_audit
                WHERE table_name = 'system_settings' AND record_id = ?
                """,
                (setting_id,)
            )
            audit_entry = await cursor.fetchone()

            assert audit_entry is not None, "Audit entry should be created"
            assert audit_entry[0] == "system_settings"
            assert audit_entry[1] == setting_id
            assert audit_entry[2] == "ui.theme"
            assert audit_entry[3] == '"dark"'
            assert audit_entry[4] == "CREATE"

    async def test_update_trigger(self, temp_db):
        """Test audit trigger on UPDATE operations."""
        async with aiosqlite.connect(temp_db) as connection:
            await connection.execute("PRAGMA foreign_keys = ON")

            # Insert initial setting
            cursor = await connection.execute(
                """
                INSERT INTO system_settings (
                    setting_key, setting_value, data_type, category, scope,
                    is_admin_only, created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("ui.theme", '"light"', "string", "ui", "user_overridable",
                 0, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), 1)
            )
            setting_id = cursor.lastrowid
            await connection.commit()

            # Update the setting
            await connection.execute(
                """
                UPDATE system_settings
                SET setting_value = ?, updated_at = ?, version = version + 1
                WHERE id = ?
                """,
                ('"dark"', datetime.utcnow().isoformat(), setting_id)
            )
            await connection.commit()

            # Check audit entries
            cursor = await connection.execute(
                """
                SELECT change_type, old_value, new_value
                FROM settings_audit
                WHERE table_name = 'system_settings' AND record_id = ?
                ORDER BY created_at
                """,
                (setting_id,)
            )
            audit_entries = await cursor.fetchall()

            assert len(audit_entries) == 2, "Should have CREATE and UPDATE audit entries"

            # Verify CREATE entry
            create_entry = audit_entries[0]
            assert create_entry[0] == "CREATE"
            assert create_entry[1] is None  # old_value should be NULL for CREATE
            assert create_entry[2] == '"light"'

            # Verify UPDATE entry
            update_entry = audit_entries[1]
            assert update_entry[0] == "UPDATE"
            assert update_entry[1] == '"light"'  # old_value
            assert update_entry[2] == '"dark"'   # new_value

    async def test_delete_trigger(self, temp_db):
        """Test audit trigger on DELETE operations."""
        async with aiosqlite.connect(temp_db) as connection:
            await connection.execute("PRAGMA foreign_keys = ON")

            # Insert setting
            cursor = await connection.execute(
                """
                INSERT INTO system_settings (
                    setting_key, setting_value, data_type, category, scope,
                    is_admin_only, created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("ui.theme", '"dark"', "string", "ui", "user_overridable",
                 0, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), 1)
            )
            setting_id = cursor.lastrowid
            await connection.commit()

            # Delete the setting
            await connection.execute(
                "DELETE FROM system_settings WHERE id = ?",
                (setting_id,)
            )
            await connection.commit()

            # Check audit entries
            cursor = await connection.execute(
                """
                SELECT change_type, old_value, new_value
                FROM settings_audit
                WHERE table_name = 'system_settings' AND record_id = ?
                ORDER BY created_at
                """,
                (setting_id,)
            )
            audit_entries = await cursor.fetchall()

            assert len(audit_entries) == 2, "Should have CREATE and DELETE audit entries"

            # Verify DELETE entry
            delete_entry = audit_entries[1]
            assert delete_entry[0] == "DELETE"
            assert delete_entry[1] == '"dark"'  # old_value
            assert delete_entry[2] is None      # new_value should be NULL for DELETE

    async def test_user_settings_triggers(self, temp_db):
        """Test audit triggers work for user_settings table."""
        async with aiosqlite.connect(temp_db) as connection:
            await connection.execute("PRAGMA foreign_keys = ON")

            # Insert user setting
            cursor = await connection.execute(
                """
                INSERT INTO user_settings (
                    user_id, setting_key, setting_value, data_type, category,
                    is_override, created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("user_123", "ui.theme", '"dark"', "string", "ui",
                 1, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), 1)
            )
            setting_id = cursor.lastrowid
            await connection.commit()

            # Check audit entry
            cursor = await connection.execute(
                """
                SELECT table_name, record_id, setting_key, change_type
                FROM settings_audit
                WHERE table_name = 'user_settings' AND record_id = ?
                """,
                (setting_id,)
            )
            audit_entry = await cursor.fetchone()

            assert audit_entry is not None, "Audit entry should be created for user_settings"
            assert audit_entry[0] == "user_settings"
            assert audit_entry[3] == "CREATE"


class TestDataIntegrity:
    """Test data integrity and consistency."""

    async def test_audit_checksum_integrity(self, temp_db):
        """Test audit entry checksum generation and integrity."""
        async with aiosqlite.connect(temp_db) as connection:
            await connection.execute("PRAGMA foreign_keys = ON")

            # Insert setting to trigger audit
            cursor = await connection.execute(
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

            # Get audit entry
            cursor = await connection.execute(
                """
                SELECT id, table_name, record_id, setting_key, old_value,
                       new_value, change_type, created_at, checksum
                FROM settings_audit
                WHERE table_name = 'system_settings'
                ORDER BY created_at DESC
                LIMIT 1
                """
            )
            audit_entry = await cursor.fetchone()

            assert audit_entry is not None, "Audit entry should exist"
            assert audit_entry[8] is not None, "Checksum should be generated"
            assert len(audit_entry[8]) == 64, "Checksum should be SHA256 hex (64 chars)"

            # Verify checksum calculation
            data = f"{audit_entry[1]}:{audit_entry[2]}:{audit_entry[3]}:{audit_entry[4]}:{audit_entry[5]}:{audit_entry[6]}:{audit_entry[7]}"
            import hashlib
            expected_checksum = hashlib.sha256(data.encode('utf-8')).hexdigest()
            assert audit_entry[8] == expected_checksum, "Checksum should match calculated value"

    async def test_concurrent_version_control(self, temp_db):
        """Test optimistic locking with version control."""
        async with aiosqlite.connect(temp_db) as connection:
            await connection.execute("PRAGMA foreign_keys = ON")

            # Insert initial setting
            cursor = await connection.execute(
                """
                INSERT INTO system_settings (
                    setting_key, setting_value, data_type, category, scope,
                    is_admin_only, created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("ui.theme", '"light"', "string", "ui", "user_overridable",
                 0, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), 1)
            )
            setting_id = cursor.lastrowid
            await connection.commit()

            # Simulate concurrent update - update with wrong version
            cursor = await connection.execute(
                """
                UPDATE system_settings
                SET setting_value = ?, updated_at = ?, version = version + 1
                WHERE id = ? AND version = ?
                """,
                ('"dark"', datetime.utcnow().isoformat(), setting_id, 999)  # Wrong version
            )
            assert cursor.rowcount == 0, "Update should fail with wrong version"

            # Update with correct version
            cursor = await connection.execute(
                """
                UPDATE system_settings
                SET setting_value = ?, updated_at = ?, version = version + 1
                WHERE id = ? AND version = ?
                """,
                ('"dark"', datetime.utcnow().isoformat(), setting_id, 1)  # Correct version
            )
            assert cursor.rowcount == 1, "Update should succeed with correct version"
            await connection.commit()

            # Verify version was incremented
            cursor = await connection.execute(
                "SELECT version FROM system_settings WHERE id = ?",
                (setting_id,)
            )
            result = await cursor.fetchone()
            assert result[0] == 2, "Version should be incremented"

    async def test_foreign_key_constraints(self, temp_db):
        """Test foreign key constraints if any exist."""
        async with aiosqlite.connect(temp_db) as connection:
            await connection.execute("PRAGMA foreign_keys = ON")

            # Verify foreign keys are enabled
            cursor = await connection.execute("PRAGMA foreign_keys")
            result = await cursor.fetchone()
            assert result[0] == 1, "Foreign keys should be enabled"

    async def test_data_consistency_after_operations(self, temp_db):
        """Test data consistency after multiple operations."""
        async with aiosqlite.connect(temp_db) as connection:
            await connection.execute("PRAGMA foreign_keys = ON")

            # Perform multiple operations
            operations = [
                ("INSERT", "ui.theme", '"light"'),
                ("UPDATE", "ui.theme", '"dark"'),
                ("INSERT", "ui.language", '"en"'),
                ("UPDATE", "ui.language", '"fr"'),
                ("DELETE", "ui.theme", None)
            ]

            setting_ids = {}

            for op_type, key, value in operations:
                if op_type == "INSERT":
                    cursor = await connection.execute(
                        """
                        INSERT INTO system_settings (
                            setting_key, setting_value, data_type, category, scope,
                            is_admin_only, created_at, updated_at, version
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (key, value, "string", "ui", "user_overridable",
                         0, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), 1)
                    )
                    setting_ids[key] = cursor.lastrowid

                elif op_type == "UPDATE":
                    await connection.execute(
                        """
                        UPDATE system_settings
                        SET setting_value = ?, updated_at = ?, version = version + 1
                        WHERE id = ?
                        """,
                        (value, datetime.utcnow().isoformat(), setting_ids[key])
                    )

                elif op_type == "DELETE":
                    await connection.execute(
                        "DELETE FROM system_settings WHERE id = ?",
                        (setting_ids[key],)
                    )

                await connection.commit()

            # Verify audit trail consistency
            cursor = await connection.execute(
                """
                SELECT table_name, record_id, setting_key, change_type, checksum
                FROM settings_audit
                ORDER BY created_at
                """
            )
            audit_entries = await cursor.fetchall()

            # Should have 5 audit entries (3 INSERTs, 2 UPDATEs, 1 DELETE)
            expected_count = 5
            assert len(audit_entries) == expected_count, f"Should have {expected_count} audit entries"

            # Verify all checksums are valid
            for entry in audit_entries:
                assert entry[4] is not None, "All audit entries should have checksums"
                assert len(entry[4]) == 64, "All checksums should be SHA256 hex"

            # Verify final state
            cursor = await connection.execute(
                "SELECT COUNT(*) FROM system_settings"
            )
            result = await cursor.fetchone()
            assert result[0] == 1, "Should have 1 remaining setting after delete"
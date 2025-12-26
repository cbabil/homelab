"""
Secure Settings Database Initialization

Comprehensive database initialization with security controls, integrity protection,
and validation addressing all identified vulnerabilities.
"""

import os
import json
import hashlib
import sqlite3
import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from services.database_service import DatabaseService
from services.settings_service import SettingsService
from models.auth import UserRole


logger = structlog.get_logger("settings_database_init")


class SettingsDatabaseInitializer:
    """Secure database initializer with comprehensive security controls."""

    def __init__(self, db_path: str = None):
        """Initialize with database path and security controls."""
        backend_root = Path(__file__).resolve().parents[2]
        resolved_path = Path(db_path) if db_path is not None else Path(os.getenv("DATA_DIRECTORY", "data"))
        if not resolved_path.is_absolute():
            resolved_path = (backend_root / resolved_path).resolve()

        self.db_path = str((resolved_path / "homelab.db").resolve())
        self.sql_dir = str((backend_root / "sql").resolve())
        self.db_service = DatabaseService(self.db_path)
        logger.info("Settings database initializer created", db_path=self.db_path)

    async def verify_prerequisites(self) -> Dict[str, Any]:
        """Verify database prerequisites and security requirements."""
        try:
            logger.info("Verifying database prerequisites")

            # Check if database file exists
            if not os.path.exists(self.db_path):
                return {
                    "success": False,
                    "message": "Database file does not exist",
                    "error": "DATABASE_NOT_FOUND"
                }

            # Verify database connection
            db_connected = await self.db_service.verify_database_connection()
            if not db_connected:
                return {
                    "success": False,
                    "message": "Cannot connect to database",
                    "error": "DATABASE_CONNECTION_FAILED"
                }

            # Check for existing settings tables
            async with self.db_service.get_connection() as conn:
                cursor = await conn.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name IN ('system_settings', 'user_settings', 'settings_audit')
                    """
                )
                existing_tables = [row[0] for row in await cursor.fetchall()]

            # Verify required SQL files exist
            required_files = ['init_settings_schema.sql', 'seed_default_settings.sql']
            missing_files = []
            for file in required_files:
                file_path = os.path.join(self.sql_dir, file)
                if not os.path.exists(file_path):
                    missing_files.append(file)

            return {
                "success": True,
                "message": "Prerequisites verified",
                "data": {
                    "database_exists": True,
                    "database_connected": True,
                    "existing_settings_tables": existing_tables,
                    "missing_sql_files": missing_files,
                    "settings_tables_exist": len(existing_tables) > 0
                }
            }

        except Exception as e:
            logger.error("Prerequisites verification failed", error=str(e))
            return {
                "success": False,
                "message": f"Prerequisites verification failed: {str(e)}",
                "error": "PREREQUISITES_ERROR"
            }

    async def execute_sql_file(self, filename: str, validate_only: bool = False) -> Dict[str, Any]:
        """Execute SQL file with security validation and integrity protection."""
        try:
            file_path = os.path.join(self.sql_dir, filename)

            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "message": f"SQL file not found: {filename}",
                    "error": "FILE_NOT_FOUND"
                }

            # Read and validate SQL content
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Basic SQL injection prevention - check for dangerous patterns
            dangerous_patterns = [
                'DROP TABLE', 'DELETE FROM sqlite_master', 'PRAGMA temp_store',
                'ATTACH DATABASE', 'DETACH DATABASE', '.read', '.import'
            ]

            sql_upper = sql_content.upper()
            for pattern in dangerous_patterns:
                if pattern in sql_upper:
                    logger.warning("Dangerous SQL pattern detected", pattern=pattern, file=filename)
                    return {
                        "success": False,
                        "message": f"Dangerous SQL pattern detected: {pattern}",
                        "error": "DANGEROUS_SQL_PATTERN"
                    }

            # Calculate content checksum for integrity
            content_hash = hashlib.sha256(sql_content.encode('utf-8')).hexdigest()

            if validate_only:
                return {
                    "success": True,
                    "message": f"SQL file validation successful: {filename}",
                    "data": {
                        "filename": filename,
                        "content_hash": content_hash,
                        "content_length": len(sql_content)
                    }
                }

            # Execute SQL with transaction safety using executescript for complex SQL
            async with self.db_service.get_connection() as conn:
                try:
                    # Use executescript which handles complex SQL with triggers, views, etc.
                    await conn.executescript(sql_content)

                    logger.info("SQL file executed successfully", filename=filename)

                    return {
                        "success": True,
                        "message": f"SQL file executed successfully: {filename}",
                        "data": {
                            "filename": filename,
                            "content_hash": content_hash
                        }
                    }

                except Exception as e:
                    logger.error("SQL execution failed",
                                filename=filename, error=str(e))
                    raise

        except Exception as e:
            logger.error("Failed to execute SQL file", filename=filename, error=str(e))
            return {
                "success": False,
                "message": f"Failed to execute SQL file {filename}: {str(e)}",
                "error": "SQL_EXECUTION_ERROR"
            }

    async def verify_schema_integrity(self) -> Dict[str, Any]:
        """Verify settings schema integrity and security constraints."""
        try:
            logger.info("Verifying settings schema integrity")

            async with self.db_service.get_connection() as conn:
                # Check system_settings table structure
                cursor = await conn.execute("PRAGMA table_info(system_settings)")
                system_columns = {row[1]: row[2] for row in await cursor.fetchall()}

                # Check user_settings table structure
                cursor = await conn.execute("PRAGMA table_info(user_settings)")
                user_columns = {row[1]: row[2] for row in await cursor.fetchall()}

                # Check settings_audit table structure
                cursor = await conn.execute("PRAGMA table_info(settings_audit)")
                audit_columns = {row[1]: row[2] for row in await cursor.fetchall()}

                # Verify required columns exist
                required_system_columns = {
                    'id', 'setting_key', 'setting_value', 'category', 'scope',
                    'data_type', 'is_admin_only', 'created_at', 'updated_at', 'version'
                }

                required_user_columns = {
                    'id', 'user_id', 'setting_key', 'setting_value', 'category',
                    'created_at', 'updated_at', 'version'
                }

                required_audit_columns = {
                    'id', 'table_name', 'record_id', 'user_id', 'setting_key',
                    'old_value', 'new_value', 'change_type', 'created_at', 'checksum'
                }

                missing_system = required_system_columns - set(system_columns.keys())
                missing_user = required_user_columns - set(user_columns.keys())
                missing_audit = required_audit_columns - set(audit_columns.keys())

                # Check constraints
                cursor = await conn.execute(
                    """
                    SELECT sql FROM sqlite_master
                    WHERE type='table' AND name='system_settings'
                    """
                )
                system_sql = (await cursor.fetchone())[0]
                has_constraints = 'CHECK' in system_sql

                # Check indexes
                cursor = await conn.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='index' AND tbl_name IN ('system_settings', 'user_settings', 'settings_audit')
                    """
                )
                indexes = [row[0] for row in await cursor.fetchall()]

                # Check triggers
                cursor = await conn.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='trigger' AND tbl_name IN ('system_settings', 'user_settings')
                    """
                )
                triggers = [row[0] for row in await cursor.fetchall()]

                schema_valid = (
                    len(missing_system) == 0 and
                    len(missing_user) == 0 and
                    len(missing_audit) == 0 and
                    has_constraints and
                    len(indexes) > 0 and
                    len(triggers) > 0
                )

                return {
                    "success": True,
                    "message": "Schema integrity verification completed",
                    "data": {
                        "schema_valid": schema_valid,
                        "system_settings": {
                            "columns": system_columns,
                            "missing_columns": list(missing_system)
                        },
                        "user_settings": {
                            "columns": user_columns,
                            "missing_columns": list(missing_user)
                        },
                        "settings_audit": {
                            "columns": audit_columns,
                            "missing_columns": list(missing_audit)
                        },
                        "has_constraints": has_constraints,
                        "indexes": indexes,
                        "triggers": triggers
                    }
                }

        except Exception as e:
            logger.error("Schema integrity verification failed", error=str(e))
            return {
                "success": False,
                "message": f"Schema integrity verification failed: {str(e)}",
                "error": "SCHEMA_VERIFICATION_ERROR"
            }

    async def seed_default_settings(self) -> Dict[str, Any]:
        """Seed default settings with validation and integrity protection."""
        try:
            logger.info("Seeding default settings")

            # First verify the seed file
            validation_result = await self.execute_sql_file('seed_default_settings.sql', validate_only=True)
            if not validation_result['success']:
                return validation_result

            # Execute the seed file
            execution_result = await self.execute_sql_file('seed_default_settings.sql')
            if not execution_result['success']:
                return execution_result

            # Verify seeded data
            async with self.db_service.get_connection() as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM system_settings")
                settings_count = (await cursor.fetchone())[0]

                cursor = await conn.execute("SELECT COUNT(*) FROM settings_audit")
                audit_count = (await cursor.fetchone())[0]

                # Check for critical default settings
                cursor = await conn.execute(
                    """
                    SELECT setting_key FROM system_settings
                    WHERE setting_key IN ('ui.theme_default', 'security.session_timeout_default', 'app.settings_schema_version')
                    """
                )
                critical_settings = [row[0] for row in await cursor.fetchall()]

            return {
                "success": True,
                "message": "Default settings seeded successfully",
                "data": {
                    "settings_count": settings_count,
                    "audit_entries": audit_count,
                    "critical_settings": critical_settings,
                    "seeding_completed": True
                }
            }

        except Exception as e:
            logger.error("Failed to seed default settings", error=str(e))
            return {
                "success": False,
                "message": f"Failed to seed default settings: {str(e)}",
                "error": "SEEDING_ERROR"
            }

    async def create_initialization_audit(self, admin_user_id: str,
                                        client_ip: str = "system",
                                        initialization_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create comprehensive audit trail for initialization process."""
        try:
            logger.info("Creating initialization audit trail", admin_user_id=admin_user_id)

            async with self.db_service.get_connection() as conn:
                # Create audit entry for the initialization process
                audit_data = {
                    "action": "settings_database_initialization",
                    "admin_user_id": admin_user_id,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "client_ip": client_ip,
                    "results": initialization_results or {}
                }

                audit_json = json.dumps(audit_data, sort_keys=True)
                checksum = hashlib.sha256(audit_json.encode('utf-8')).hexdigest()

                await conn.execute(
                    """
                    INSERT INTO settings_audit (
                        table_name, record_id, user_id, setting_key,
                        old_value, new_value, change_type, change_reason,
                        client_ip, user_agent, created_at, checksum
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        'system_settings', 0, admin_user_id, 'system.database_initialization',
                        None, audit_json, 'CREATE', 'Settings database initialization',
                        client_ip, 'settings_database_initializer', datetime.now(UTC).isoformat(), checksum
                    )
                )

                await conn.commit()

                return {
                    "success": True,
                    "message": "Initialization audit trail created",
                    "data": {
                        "audit_checksum": checksum,
                        "admin_user_id": admin_user_id,
                        "timestamp": audit_data["timestamp"]
                    }
                }

        except Exception as e:
            logger.error("Failed to create initialization audit", error=str(e))
            return {
                "success": False,
                "message": f"Failed to create initialization audit: {str(e)}",
                "error": "AUDIT_CREATION_ERROR"
            }

    async def initialize_database(self, admin_user_id: str,
                                force_reinitialize: bool = False,
                                client_ip: str = "system") -> Dict[str, Any]:
        """Complete secure database initialization with all security controls."""
        try:
            logger.info("Starting settings database initialization",
                       admin_user_id=admin_user_id, force=force_reinitialize)

            # Verify admin privileges
            user = await self.db_service.get_user_by_id(admin_user_id)
            if not user or user.role != UserRole.ADMIN:
                return {
                    "success": False,
                    "message": "Admin privileges required for database initialization",
                    "error": "ADMIN_REQUIRED"
                }

            initialization_steps = []

            # Step 1: Verify prerequisites
            prereq_result = await self.verify_prerequisites()
            initialization_steps.append({"step": "prerequisites", "result": prereq_result})

            if not prereq_result['success']:
                return {
                    "success": False,
                    "message": "Prerequisites check failed",
                    "data": {"steps": initialization_steps},
                    "error": "PREREQUISITES_FAILED"
                }

            # Check if settings tables already exist
            existing_tables = prereq_result['data']['existing_settings_tables']
            if existing_tables and not force_reinitialize:
                return {
                    "success": False,
                    "message": "Settings tables already exist. Use force_reinitialize=True to proceed.",
                    "data": {
                        "existing_tables": existing_tables,
                        "steps": initialization_steps
                    },
                    "error": "TABLES_ALREADY_EXIST"
                }

            # Step 2: Initialize schema
            schema_result = await self.execute_sql_file('init_settings_schema.sql')
            initialization_steps.append({"step": "schema_creation", "result": schema_result})

            if not schema_result['success']:
                return {
                    "success": False,
                    "message": "Schema creation failed",
                    "data": {"steps": initialization_steps},
                    "error": "SCHEMA_CREATION_FAILED"
                }

            # Step 3: Verify schema integrity
            integrity_result = await self.verify_schema_integrity()
            initialization_steps.append({"step": "schema_verification", "result": integrity_result})

            if not integrity_result['success'] or not integrity_result['data']['schema_valid']:
                return {
                    "success": False,
                    "message": "Schema integrity verification failed",
                    "data": {"steps": initialization_steps},
                    "error": "SCHEMA_INTEGRITY_FAILED"
                }

            # Step 4: Seed default settings
            seeding_result = await self.seed_default_settings()
            initialization_steps.append({"step": "default_seeding", "result": seeding_result})

            if not seeding_result['success']:
                return {
                    "success": False,
                    "message": "Default settings seeding failed",
                    "data": {"steps": initialization_steps},
                    "error": "SEEDING_FAILED"
                }

            # Step 5: Create initialization audit
            audit_result = await self.create_initialization_audit(
                admin_user_id, client_ip, {
                    "steps_completed": len(initialization_steps),
                    "force_reinitialize": force_reinitialize
                }
            )
            initialization_steps.append({"step": "audit_creation", "result": audit_result})

            logger.info("Settings database initialization completed successfully",
                       admin_user_id=admin_user_id, steps=len(initialization_steps))

            return {
                "success": True,
                "message": "Settings database initialization completed successfully",
                "data": {
                    "steps": initialization_steps,
                    "admin_user_id": admin_user_id,
                    "initialization_timestamp": datetime.now(UTC).isoformat(),
                    "force_reinitialize": force_reinitialize,
                    "schema_integrity": integrity_result['data'],
                    "settings_count": seeding_result['data']['settings_count'],
                    "audit_checksum": audit_result['data']['audit_checksum'] if audit_result['success'] else None
                }
            }

        except Exception as e:
            logger.error("Settings database initialization failed",
                        admin_user_id=admin_user_id, error=str(e))
            return {
                "success": False,
                "message": f"Settings database initialization failed: {str(e)}",
                "error": "INITIALIZATION_ERROR"
            }


async def main():
    """CLI entry point for manual database initialization."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python init_settings_database.py <admin_user_id> [force]")
        sys.exit(1)

    admin_user_id = sys.argv[1]
    force_reinitialize = len(sys.argv) > 2 and sys.argv[2].lower() == 'force'

    initializer = SettingsDatabaseInitializer()
    result = await initializer.initialize_database(admin_user_id, force_reinitialize, "cli")

    if result['success']:
        print(f"✅ {result['message']}")
        print(f"Steps completed: {len(result['data']['steps'])}")
        print(f"Settings count: {result['data']['settings_count']}")
    else:
        print(f"❌ {result['message']}")
        if 'data' in result and 'steps' in result['data']:
            print(f"Steps attempted: {len(result['data']['steps'])}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

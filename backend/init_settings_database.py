#!/usr/bin/env python3
"""
Settings Database Initialization Script

Handles both new installations and upgrades for the settings management system.
Provides comprehensive database setup with proper error handling and validation.
"""

import sqlite3
import json
import os
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database and SQL paths
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "homelab.db"
SQL_DIR = BASE_DIR / "sql"

SQL_FILES = {
    "schema": SQL_DIR / "init_settings_schema.sql",
    "defaults": SQL_DIR / "seed_default_settings.sql",
    "migration": SQL_DIR / "migrate_existing_installation.sql"
}


class SettingsDatabaseManager:
    """Manages settings database initialization and migration."""

    def __init__(self, db_path: str = str(DB_PATH)):
        """Initialize with database path."""
        self.db_path = db_path
        self.is_new_installation = not os.path.exists(db_path)

    def initialize(self) -> bool:
        """
        Initialize or upgrade the settings database.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.is_new_installation:
                logger.info("Detected new installation - creating complete database")
                return self._create_new_installation()
            else:
                logger.info("Detected existing installation - checking for upgrades")
                return self._upgrade_existing_installation()

        except Exception as e:
            logger.error(f"Failed to initialize settings database: {e}")
            return False

    def _create_new_installation(self) -> bool:
        """Create complete database for new installation."""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            # Create database and basic schema (if not from init_database.py)
            if not self._ensure_base_tables():
                return False

            # Create settings schema
            if not self._execute_sql_file(SQL_FILES["schema"])):
                return False

            # Populate default settings
            if not self._execute_sql_file(SQL_FILES["defaults"])):
                return False

            # Mark installation as complete
            self._mark_installation_complete()

            logger.info("New installation completed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to create new installation: {e}")
            return False

    def _upgrade_existing_installation(self) -> bool:
        """Upgrade existing installation with settings system."""
        try:
            # Check if upgrade is needed
            if not self._needs_upgrade():
                logger.info("Settings system already installed")
                return True

            logger.info("Upgrading existing installation with settings system")

            # Create backup before upgrade
            if not self._create_backup():
                logger.warning("Backup creation failed, continuing with caution")

            # Execute migration script
            if not self._execute_migration():
                return False

            logger.info("Existing installation upgraded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to upgrade existing installation: {e}")
            return False

    def _ensure_base_tables(self) -> bool:
        """Ensure base users and logs tables exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if base tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ('users', 'logs')
            """)
            existing_tables = {row[0] for row in cursor.fetchall()}

            conn.close()

            # If base tables don't exist, they should be created by init_database.py
            if not existing_tables:
                logger.warning("Base tables not found - ensure init_database.py runs first")
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to check base tables: {e}")
            return False

    def _needs_upgrade(self) -> bool:
        """Check if the database needs settings system upgrade."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if settings tables exist
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master
                WHERE type='table' AND name IN ('system_settings', 'user_settings')
            """)
            settings_tables_count = cursor.fetchone()[0]

            conn.close()

            # If settings tables don't exist, upgrade is needed
            return settings_tables_count == 0

        except Exception as e:
            logger.error(f"Failed to check upgrade status: {e}")
            return True  # Assume upgrade needed if check fails

    def _execute_sql_file(self, sql_file_path: Path) -> bool:
        """Execute SQL statements from file."""
        try:
            if not sql_file_path.exists():
                logger.error(f"SQL file not found: {sql_file_path}")
                return False

            with open(sql_file_path, 'r') as f:
                sql_content = f.read()

            conn = sqlite3.connect(self.db_path)

            try:
                # Execute SQL with proper transaction handling
                conn.executescript(sql_content)
                conn.commit()
                logger.info(f"Successfully executed {sql_file_path.name}")
                return True

            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to execute {sql_file_path.name}: {e}")
                return False

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Failed to read SQL file {sql_file_path}: {e}")
            return False

    def _execute_migration(self) -> bool:
        """Execute migration with special handling for SQLite .read commands."""
        try:
            if not SQL_FILES["migration"].exists():
                logger.error("Migration script not found")
                return False

            # For migration, we need to handle the .read commands manually
            # since Python sqlite3 doesn't support .read directive

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            try:
                # First execute the schema creation
                if not self._execute_sql_file(SQL_FILES["schema"]):
                    return False

                # Then execute the defaults population
                if not self._execute_sql_file(SQL_FILES["defaults"]):
                    return False

                # Finally, execute the migration-specific parts
                migration_sql = self._get_migration_only_sql()
                if migration_sql:
                    conn.executescript(migration_sql)
                    conn.commit()

                logger.info("Migration executed successfully")
                return True

            except Exception as e:
                conn.rollback()
                logger.error(f"Migration execution failed: {e}")
                return False

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Failed to execute migration: {e}")
            return False

    def _get_migration_only_sql(self) -> Optional[str]:
        """Extract migration-specific SQL (excluding .read commands)."""
        try:
            with open(SQL_FILES["migration"], 'r') as f:
                content = f.read()

            # Filter out .read commands and extract migration-specific SQL
            lines = content.split('\n')
            migration_sql_lines = []
            skip_section = False

            for line in lines:
                # Skip .read commands
                if line.strip().startswith('.read'):
                    continue

                # Include migration-specific sections
                if 'MIGRATE EXISTING USER PREFERENCES' in line:
                    skip_section = False
                elif 'CREATE SETTINGS MANAGEMENT SCHEMA' in line:
                    skip_section = True
                elif 'POPULATE DEFAULT SETTINGS' in line:
                    skip_section = True
                elif not skip_section and line.strip():
                    migration_sql_lines.append(line)

            return '\n'.join(migration_sql_lines) if migration_sql_lines else None

        except Exception as e:
            logger.error(f"Failed to extract migration SQL: {e}")
            return None

    def _create_backup(self) -> bool:
        """Create backup of existing database."""
        try:
            backup_path = f"{self.db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # SQLite backup
            source_conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(backup_path)

            source_conn.backup(backup_conn)

            source_conn.close()
            backup_conn.close()

            logger.info(f"Database backup created: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False

    def _mark_installation_complete(self) -> bool:
        """Mark the installation as complete in system settings."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Generate installation ID
            installation_id = str(uuid.uuid4())

            # Update installation markers
            cursor.execute("""
                UPDATE system_settings
                SET setting_value = ?, updated_at = datetime('now')
                WHERE setting_key = 'app.installation_id'
            """, (f'"{installation_id}"',))

            cursor.execute("""
                UPDATE system_settings
                SET setting_value = 'true', updated_at = datetime('now')
                WHERE setting_key = 'app.first_run_completed'
            """)

            conn.commit()
            conn.close()

            logger.info(f"Installation marked complete with ID: {installation_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to mark installation complete: {e}")
            return False

    def verify_installation(self) -> Dict[str, Any]:
        """Verify the settings database installation."""
        verification_result = {
            "success": False,
            "errors": [],
            "warnings": [],
            "stats": {}
        }

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check required tables
            required_tables = ['system_settings', 'user_settings', 'settings_audit']
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ({})
            """.format(','.join(f'"{table}"' for table in required_tables)))

            existing_tables = {row[0] for row in cursor.fetchall()}
            missing_tables = set(required_tables) - existing_tables

            if missing_tables:
                verification_result["errors"].extend([
                    f"Missing table: {table}" for table in missing_tables
                ])

            # Check system settings count
            cursor.execute("SELECT COUNT(*) FROM system_settings")
            settings_count = cursor.fetchone()[0]
            verification_result["stats"]["system_settings_count"] = settings_count

            if settings_count < 20:  # We expect ~25 default settings
                verification_result["warnings"].append(
                    f"Low system settings count: {settings_count} (expected ~25)"
                )

            # Check for migration markers
            cursor.execute("""
                SELECT setting_value FROM system_settings
                WHERE setting_key = 'app.first_run_completed'
            """)
            setup_complete = cursor.fetchone()

            if setup_complete and setup_complete[0] == 'true':
                verification_result["stats"]["setup_completed"] = True
            else:
                verification_result["warnings"].append("Setup not marked as complete")

            # Check audit trail
            cursor.execute("SELECT COUNT(*) FROM settings_audit")
            audit_count = cursor.fetchone()[0]
            verification_result["stats"]["audit_entries_count"] = audit_count

            conn.close()

            # Overall success determination
            verification_result["success"] = len(verification_result["errors"]) == 0

        except Exception as e:
            verification_result["errors"].append(f"Verification failed: {e}")

        return verification_result


def main():
    """Main entry point for settings database initialization."""
    print("Settings Database Initialization")
    print("=" * 50)

    # Initialize manager
    manager = SettingsDatabaseManager()

    # Run initialization
    success = manager.initialize()

    if success:
        print("\nVerifying installation...")
        verification = manager.verify_installation()

        if verification["success"]:
            print("✅ Settings database initialized successfully!")
            print(f"📊 Statistics: {verification['stats']}")

            if verification["warnings"]:
                print("\n⚠️  Warnings:")
                for warning in verification["warnings"]:
                    print(f"   • {warning}")
        else:
            print("❌ Installation verification failed!")
            for error in verification["errors"]:
                print(f"   • {error}")
            return 1
    else:
        print("❌ Settings database initialization failed!")
        return 1

    print(f"\nDatabase location: {DB_PATH}")
    print("Initialization complete!")
    return 0


if __name__ == "__main__":
    exit(main())
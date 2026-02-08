"""System Database Service.

Database operations for system info and component versions.
"""

from datetime import UTC, datetime
from typing import Any

import structlog

from .base import ALLOWED_SYSTEM_INFO_COLUMNS, DatabaseConnection

logger = structlog.get_logger("database.system")


class SystemDatabaseService:
    """Database operations for system info and component version management."""

    def __init__(self, connection: DatabaseConnection):
        """Initialize with database connection.

        Args:
            connection: DatabaseConnection instance.
        """
        self._conn = connection

    # ========== System Info Methods ==========

    async def get_system_info(self) -> dict[str, Any] | None:
        """Get system info (single row table).

        Returns:
            Dictionary with system info fields, or None if not found.
        """
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    """SELECT id, app_name, is_setup, setup_completed_at,
                              setup_by_user_id, installation_id,
                              license_type, license_key, license_expires_at,
                              created_at, updated_at
                       FROM system_info WHERE id = 1"""
                )
                row = await cursor.fetchone()

                if not row:
                    logger.debug("System info not found")
                    return None

                return {
                    "id": row["id"],
                    "app_name": row["app_name"],
                    "is_setup": bool(row["is_setup"]),
                    "setup_completed_at": row["setup_completed_at"],
                    "setup_by_user_id": row["setup_by_user_id"],
                    "installation_id": row["installation_id"],
                    "license_type": row["license_type"],
                    "license_key": row["license_key"],
                    "license_expires_at": row["license_expires_at"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }

        except Exception as e:
            logger.error("Failed to get system info", error=str(e))
            return None

    async def is_system_setup(self) -> bool:
        """Check if system has completed initial setup.

        Returns:
            True if system is set up (is_setup = 1), False otherwise.
        """
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT is_setup FROM system_info WHERE id = 1"
                )
                row = await cursor.fetchone()

                if not row:
                    logger.debug("System info not found, assuming not setup")
                    return False

                is_setup = bool(row["is_setup"])
                logger.debug("System setup check", is_setup=is_setup)
                return is_setup

        except Exception as e:
            logger.error("Failed to check system setup status", error=str(e))
            return False

    async def mark_system_setup_complete(self, user_id: str) -> bool:
        """Mark system as setup complete after admin creation.

        Args:
            user_id: The ID of the user who completed the setup.

        Returns:
            True if successful, False otherwise.
        """
        try:
            now = datetime.now(UTC).isoformat()

            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    """UPDATE system_info
                       SET is_setup = 1, setup_completed_at = ?, setup_by_user_id = ?
                       WHERE id = 1""",
                    (now, user_id),
                )
                await conn.commit()

                if cursor.rowcount == 0:
                    logger.warning("System info row not found for setup completion")
                    return False

                logger.info(
                    "System marked as setup complete", user_id=user_id, completed_at=now
                )
                return True

        except Exception as e:
            logger.error(
                "Failed to mark system setup complete", user_id=user_id, error=str(e)
            )
            return False

    async def update_system_info(self, **kwargs) -> bool:
        """Update system info fields.

        Args:
            **kwargs: Fields to update (must be in ALLOWED_SYSTEM_INFO_COLUMNS).

        Returns:
            True if successful, False otherwise.
        """
        try:
            updates = []
            values = []
            for key, value in kwargs.items():
                if value is not None:
                    if key not in ALLOWED_SYSTEM_INFO_COLUMNS:
                        logger.warning(
                            "Rejected invalid column in update_system_info", column=key
                        )
                        raise ValueError(f"Invalid column name: {key}")
                    updates.append(f"{key} = ?")
                    values.append(value)

            if not updates:
                return True

            query = f"UPDATE system_info SET {', '.join(updates)} WHERE id = 1"

            async with self._conn.get_connection() as conn:
                await conn.execute(query, values)
                await conn.commit()

            logger.debug("Updated system info", fields=list(kwargs.keys()))
            return True

        except Exception as e:
            logger.error("Failed to update system info", error=str(e))
            return False

    async def verify_database_connection(self) -> bool:
        """Verify database connection and table existence."""
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute("PRAGMA table_info(users)")
                columns = await cursor.fetchall()

                required_columns = {
                    "id",
                    "username",
                    "email",
                    "password_hash",
                    "role",
                    "is_active",
                }
                existing_columns = {col["name"] for col in columns}

                if not required_columns.issubset(existing_columns):
                    missing = required_columns - existing_columns
                    logger.error(
                        "Missing required columns in users table", missing=list(missing)
                    )
                    return False

                cursor = await conn.execute("SELECT COUNT(*) as count FROM users")
                result = await cursor.fetchone()
                user_count = result["count"]

                logger.info("Database connection verified", user_count=user_count)
                return True

        except Exception as e:
            logger.error("Database connection verification failed", error=str(e))
            return False

    # ========== Component Versions Methods ==========

    async def get_component_versions(self) -> list[dict[str, Any]]:
        """Get all component versions.

        Returns:
            List of component version dictionaries.
        """
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM component_versions ORDER BY component"
                )
                rows = await cursor.fetchall()

            return [
                {
                    "component": row["component"],
                    "version": row["version"],
                    "updated_at": row["updated_at"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]

        except Exception as e:
            logger.error("Failed to get component versions", error=str(e))
            return []

    async def get_component_version(self, component: str) -> dict[str, Any] | None:
        """Get version for a specific component.

        Args:
            component: Component name ('backend', 'frontend', 'api').

        Returns:
            Dictionary with component version data, or None if not found.
        """
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM component_versions WHERE component = ?", (component,)
                )
                row = await cursor.fetchone()

            if not row:
                return None

            return {
                "component": row["component"],
                "version": row["version"],
                "updated_at": row["updated_at"],
                "created_at": row["created_at"],
            }

        except Exception as e:
            logger.error(
                "Failed to get component version", component=component, error=str(e)
            )
            return None

    async def update_component_version(self, component: str, version: str) -> bool:
        """Update a component's version.

        Args:
            component: Component name ('backend', 'frontend', 'api').
            version: New version string.

        Returns:
            True if successful, False otherwise.
        """
        try:
            async with self._conn.get_connection() as conn:
                await conn.execute(
                    "UPDATE component_versions SET version = ? WHERE component = ?",
                    (version, component),
                )
                await conn.commit()

            logger.info(
                "Component version updated", component=component, version=version
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to update component version", component=component, error=str(e)
            )
            return False

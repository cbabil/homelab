"""Export Database Service.

Database operations for backup import and export.
"""

from typing import Any, Dict, List

import structlog

from .base import DatabaseConnection

logger = structlog.get_logger("database.export")


class ExportDatabaseService:
    """Database operations for import and export."""

    def __init__(self, connection: DatabaseConnection):
        """Initialize with database connection.

        Args:
            connection: DatabaseConnection instance.
        """
        self._conn = connection

    async def export_users(self) -> List[Dict[str, Any]]:
        """Export all users for backup."""
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT id, username, email, role, is_active, created_at FROM users"
                )
                rows = await cursor.fetchall()

            return [dict(row) for row in rows]
        except Exception as e:
            logger.error("Failed to export users", error=str(e))
            return []

    async def export_servers(self) -> List[Dict[str, Any]]:
        """Export all servers for backup (including encrypted credentials)."""
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute("SELECT * FROM servers")
                rows = await cursor.fetchall()

            return [dict(row) for row in rows]
        except Exception as e:
            logger.error("Failed to export servers", error=str(e))
            return []

    async def export_settings(self) -> Dict[str, Any]:
        """Export settings for backup."""
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute("SELECT key, value FROM settings")
                rows = await cursor.fetchall()

            return {row["key"]: row["value"] for row in rows}
        except Exception as e:
            logger.error("Failed to export settings", error=str(e))
            return {}

    async def import_users(
        self, users: List[Dict[str, Any]], overwrite: bool = False
    ) -> None:
        """Import users from backup."""
        try:
            async with self._conn.get_connection() as conn:
                for user in users:
                    if overwrite:
                        await conn.execute(
                            "DELETE FROM users WHERE id = ?", (user["id"],)
                        )
                    await conn.execute(
                        """INSERT OR IGNORE INTO users
                           (id, username, email, role, is_active, created_at)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            user["id"],
                            user["username"],
                            user.get("email"),
                            user.get("role", "user"),
                            user.get("is_active", 1),
                            user.get("created_at"),
                        ),
                    )
                await conn.commit()
            logger.info("Imported users", count=len(users))
        except Exception as e:
            logger.error("Failed to import users", error=str(e))
            raise

    async def import_servers(
        self, servers: List[Dict[str, Any]], overwrite: bool = False
    ) -> None:
        """Import servers from backup."""
        try:
            async with self._conn.get_connection() as conn:
                for server in servers:
                    if overwrite:
                        await conn.execute(
                            "DELETE FROM servers WHERE id = ?", (server["id"],)
                        )
                    await conn.execute(
                        """INSERT OR IGNORE INTO servers
                           (id, name, host, port, username, auth_type, credentials, status)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            server["id"],
                            server["name"],
                            server["host"],
                            server.get("port", 22),
                            server.get("username"),
                            server.get("auth_type"),
                            server.get("credentials"),
                            server.get("status", "unknown"),
                        ),
                    )
                await conn.commit()
            logger.info("Imported servers", count=len(servers))
        except Exception as e:
            logger.error("Failed to import servers", error=str(e))
            raise

    async def import_settings(
        self, settings: Dict[str, Any], overwrite: bool = False
    ) -> None:
        """Import settings from backup."""
        try:
            async with self._conn.get_connection() as conn:
                for key, value in settings.items():
                    if overwrite:
                        await conn.execute(
                            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                            (key, value),
                        )
                    else:
                        await conn.execute(
                            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                            (key, value),
                        )
                await conn.commit()
            logger.info("Imported settings", count=len(settings))
        except Exception as e:
            logger.error("Failed to import settings", error=str(e))
            raise

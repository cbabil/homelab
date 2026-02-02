"""App Database Service.

Database operations for app installations.
"""

import json
from typing import List, Optional

import structlog

from models.app_catalog import InstalledApp, InstallationStatus
from .base import (
    DatabaseConnection,
    ALLOWED_INSTALLATION_COLUMNS,
)

logger = structlog.get_logger("database.app")


class AppDatabaseService:
    """Database operations for app installation management."""

    def __init__(self, connection: DatabaseConnection):
        """Initialize with database connection.

        Args:
            connection: DatabaseConnection instance.
        """
        self._conn = connection

    # ========== Installation Methods ==========

    async def create_installation(
        self,
        id: str,
        server_id: str,
        app_id: str,
        container_name: str,
        status: str,
        config: dict,
        installed_at: str,
    ) -> Optional[InstalledApp]:
        """Create a new installation record."""
        try:
            config_json = json.dumps(config) if config else "{}"
            async with self._conn.get_connection() as conn:
                await conn.execute(
                    """INSERT INTO installed_apps
                       (id, server_id, app_id, container_name, status, config, installed_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        id,
                        server_id,
                        app_id,
                        container_name,
                        status,
                        config_json,
                        installed_at,
                    ),
                )
                await conn.commit()

            return InstalledApp(
                id=id,
                server_id=server_id,
                app_id=app_id,
                container_name=container_name,
                status=InstallationStatus(status),
                config=config,
                installed_at=installed_at,
            )
        except Exception as e:
            logger.error("Failed to create installation", error=str(e))
            return None

    async def update_installation(self, install_id: str, **kwargs) -> bool:
        """Update installation record."""
        try:
            updates = []
            values = []
            for key, value in kwargs.items():
                if value is not None:
                    if key not in ALLOWED_INSTALLATION_COLUMNS:
                        logger.warning(
                            "Rejected invalid column in update_installation", column=key
                        )
                        raise ValueError(f"Invalid column name: {key}")
                    updates.append(f"{key} = ?")
                    values.append(value)

            if not updates:
                return True

            values.append(install_id)
            query = f"UPDATE installed_apps SET {', '.join(updates)} WHERE id = ?"

            async with self._conn.get_connection() as conn:
                await conn.execute(query, values)
                await conn.commit()
            return True
        except Exception as e:
            logger.error("Failed to update installation", error=str(e))
            return False

    async def get_installation(
        self, server_id: str, app_id: str
    ) -> Optional[InstalledApp]:
        """Get installation by server and app ID.

        Handles ID mismatch: marketplace apps use 'casaos-X' prefix,
        but catalog uses 'X'. Tries both variants.
        """
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    """SELECT * FROM installed_apps
                       WHERE server_id = ? AND app_id = ?""",
                    (server_id, app_id),
                )
                row = await cursor.fetchone()

                if not row and not app_id.startswith("casaos-"):
                    cursor = await conn.execute(
                        """SELECT * FROM installed_apps
                           WHERE server_id = ? AND app_id = ?""",
                        (server_id, f"casaos-{app_id}"),
                    )
                    row = await cursor.fetchone()

            if not row:
                return None

            config = json.loads(row["config"]) if row["config"] else {}
            return InstalledApp(
                id=row["id"],
                server_id=row["server_id"],
                app_id=row["app_id"],
                container_id=row["container_id"],
                container_name=row["container_name"],
                status=InstallationStatus(row["status"]),
                config=config,
                installed_at=row["installed_at"],
                started_at=row["started_at"],
                error_message=row["error_message"],
            )
        except Exception as e:
            logger.error("Failed to get installation", error=str(e))
            return None

    async def get_installation_by_id(self, install_id: str) -> Optional[InstalledApp]:
        """Get installation by installation ID (for status polling)."""
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    """SELECT * FROM installed_apps WHERE id = ?""", (install_id,)
                )
                row = await cursor.fetchone()

            if not row:
                return None

            config = json.loads(row["config"]) if row["config"] else {}
            row_keys = row.keys()

            step_durations = None
            if "step_durations" in row_keys and row["step_durations"]:
                step_durations = json.loads(row["step_durations"])
            networks = None
            if "networks" in row_keys and row["networks"]:
                networks = json.loads(row["networks"])
            named_volumes = None
            if "named_volumes" in row_keys and row["named_volumes"]:
                named_volumes = json.loads(row["named_volumes"])
            bind_mounts = None
            if "bind_mounts" in row_keys and row["bind_mounts"]:
                bind_mounts = json.loads(row["bind_mounts"])

            return InstalledApp(
                id=row["id"],
                server_id=row["server_id"],
                app_id=row["app_id"],
                container_id=row["container_id"],
                container_name=row["container_name"],
                status=InstallationStatus(row["status"]),
                config=config,
                installed_at=row["installed_at"],
                started_at=row["started_at"],
                error_message=row["error_message"],
                step_durations=step_durations,
                step_started_at=row["step_started_at"]
                if "step_started_at" in row_keys
                else None,
                networks=networks,
                named_volumes=named_volumes,
                bind_mounts=bind_mounts,
            )
        except Exception as e:
            logger.error("Failed to get installation by id", error=str(e))
            return None

    async def get_installations(self, server_id: str) -> List[InstalledApp]:
        """Get all installations for a server."""
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    """SELECT * FROM installed_apps WHERE server_id = ?""", (server_id,)
                )
                rows = await cursor.fetchall()

            return [
                InstalledApp(
                    id=row["id"],
                    server_id=row["server_id"],
                    app_id=row["app_id"],
                    container_id=row["container_id"],
                    container_name=row["container_name"],
                    status=InstallationStatus(row["status"]),
                    config=json.loads(row["config"]) if row["config"] else {},
                    installed_at=row["installed_at"],
                    started_at=row["started_at"],
                    error_message=row["error_message"],
                )
                for row in rows
            ]
        except Exception as e:
            logger.error("Failed to get installations", error=str(e))
            return []

    async def get_all_installations(self) -> List[InstalledApp]:
        """Get all installations across all servers."""
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute("""SELECT * FROM installed_apps""")
                rows = await cursor.fetchall()

            result = []
            for row in rows:
                row_keys = row.keys()

                step_durations = None
                if "step_durations" in row_keys and row["step_durations"]:
                    step_durations = json.loads(row["step_durations"])
                networks = None
                if "networks" in row_keys and row["networks"]:
                    networks = json.loads(row["networks"])
                named_volumes = None
                if "named_volumes" in row_keys and row["named_volumes"]:
                    named_volumes = json.loads(row["named_volumes"])
                bind_mounts = None
                if "bind_mounts" in row_keys and row["bind_mounts"]:
                    bind_mounts = json.loads(row["bind_mounts"])

                result.append(
                    InstalledApp(
                        id=row["id"],
                        server_id=row["server_id"],
                        app_id=row["app_id"],
                        container_id=row["container_id"],
                        container_name=row["container_name"],
                        status=InstallationStatus(row["status"]),
                        config=json.loads(row["config"]) if row["config"] else {},
                        installed_at=row["installed_at"],
                        started_at=row["started_at"],
                        error_message=row["error_message"],
                        step_durations=step_durations,
                        step_started_at=row["step_started_at"]
                        if "step_started_at" in row_keys
                        else None,
                        networks=networks,
                        named_volumes=named_volumes,
                        bind_mounts=bind_mounts,
                    )
                )
            return result
        except Exception as e:
            logger.error("Failed to get all installations", error=str(e))
            return []

    async def delete_installation(self, server_id: str, app_id: str) -> bool:
        """Delete installation record."""
        try:
            async with self._conn.get_connection() as conn:
                await conn.execute(
                    """DELETE FROM installed_apps WHERE server_id = ? AND app_id = ?""",
                    (server_id, app_id),
                )
                await conn.commit()
            return True
        except Exception as e:
            logger.error("Failed to delete installation", error=str(e))
            return False

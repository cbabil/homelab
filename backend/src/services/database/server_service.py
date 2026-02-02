"""Server Database Service.

Database operations for server management.
"""

import json
from datetime import UTC, datetime
from typing import List, Optional

import structlog

from models.server import ServerConnection, AuthType, ServerStatus, SystemInfo
from .base import DatabaseConnection, ALLOWED_SERVER_COLUMNS

logger = structlog.get_logger("database.server")


class ServerDatabaseService:
    """Database operations for server management."""

    def __init__(self, connection: DatabaseConnection):
        """Initialize with database connection.

        Args:
            connection: DatabaseConnection instance.
        """
        self._conn = connection

    async def create_server(
        self,
        id: str,
        name: str,
        host: str,
        port: int,
        username: str,
        auth_type: str,
        encrypted_credentials: str,
    ) -> Optional[ServerConnection]:
        """Create a new server in the database."""
        try:
            now = datetime.now(UTC).isoformat()

            async with self._conn.get_connection() as conn:
                await conn.execute(
                    """INSERT INTO servers
                       (id, name, host, port, username, auth_type, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (id, name, host, port, username, auth_type, "disconnected", now),
                )

                await conn.execute(
                    """INSERT INTO server_credentials
                       (server_id, encrypted_data, created_at, updated_at)
                       VALUES (?, ?, ?, ?)""",
                    (id, encrypted_credentials, now, now),
                )

                await conn.commit()

            return ServerConnection(
                id=id,
                name=name,
                host=host,
                port=port,
                username=username,
                auth_type=AuthType(auth_type),
                status=ServerStatus.DISCONNECTED,
                created_at=now,
            )
        except Exception as e:
            logger.error("Failed to create server", error=str(e))
            return None

    async def get_server_by_connection(
        self, host: str, port: int, username: str
    ) -> Optional[ServerConnection]:
        """Get server by connection details (host, port, username)."""
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM servers WHERE host = ? AND port = ? AND username = ?",
                    (host, port, username),
                )
                row = await cursor.fetchone()

            if not row:
                return None

            system_info = None
            if row["system_info"]:
                try:
                    system_info = SystemInfo(**json.loads(row["system_info"]))
                except (json.JSONDecodeError, TypeError):
                    pass

            return ServerConnection(
                id=row["id"],
                name=row["name"],
                host=row["host"],
                port=row["port"],
                username=row["username"],
                auth_type=AuthType(row["auth_type"]),
                status=ServerStatus(row["status"]),
                created_at=row["created_at"],
                last_connected=row["last_connected"],
                system_info=system_info,
                docker_installed=bool(row["docker_installed"] or 0),
                system_info_updated_at=row["system_info_updated_at"],
            )
        except Exception as e:
            logger.error("Failed to get server by connection", error=str(e))
            return None

    async def get_server_by_id(self, server_id: str) -> Optional[ServerConnection]:
        """Get server by ID."""
        try:
            logger.info("get_server_by_id called", server_id=server_id)
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM servers WHERE id = ?", (server_id,)
                )
                row = await cursor.fetchone()
                logger.info(
                    "get_server_by_id query result",
                    server_id=server_id,
                    row_found=row is not None,
                    row_keys=list(row.keys()) if row else None,
                )

            if not row:
                return None

            system_info = None
            if row["system_info"]:
                try:
                    system_info = SystemInfo(**json.loads(row["system_info"]))
                except (json.JSONDecodeError, TypeError):
                    pass

            return ServerConnection(
                id=row["id"],
                name=row["name"],
                host=row["host"],
                port=row["port"],
                username=row["username"],
                auth_type=AuthType(row["auth_type"]),
                status=ServerStatus(row["status"]),
                created_at=row["created_at"],
                last_connected=row["last_connected"],
                system_info=system_info,
                docker_installed=bool(row["docker_installed"] or 0),
                system_info_updated_at=row["system_info_updated_at"],
            )
        except Exception as e:
            import traceback

            logger.error(
                "Failed to get server", error=str(e), traceback=traceback.format_exc()
            )
            return None

    async def get_all_servers_from_db(self) -> List[ServerConnection]:
        """Get all servers from database."""

        def parse_server_row(row) -> ServerConnection:
            system_info = None
            if row["system_info"]:
                try:
                    system_info = SystemInfo(**json.loads(row["system_info"]))
                except (json.JSONDecodeError, TypeError):
                    pass

            return ServerConnection(
                id=row["id"],
                name=row["name"],
                host=row["host"],
                port=row["port"],
                username=row["username"],
                auth_type=AuthType(row["auth_type"]),
                status=ServerStatus(row["status"]),
                created_at=row["created_at"],
                last_connected=row["last_connected"],
                system_info=system_info,
                docker_installed=bool(row["docker_installed"] or 0),
                system_info_updated_at=row["system_info_updated_at"],
            )

        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute("SELECT * FROM servers")
                rows = await cursor.fetchall()

            return [parse_server_row(row) for row in rows]
        except Exception as e:
            logger.error("Failed to get servers", error=str(e))
            return []

    async def get_server_credentials(self, server_id: str) -> Optional[str]:
        """Get encrypted credentials for a server."""
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT encrypted_data FROM server_credentials WHERE server_id = ?",
                    (server_id,),
                )
                row = await cursor.fetchone()
            return row["encrypted_data"] if row else None
        except Exception as e:
            logger.error("Failed to get credentials", error=str(e))
            return None

    async def update_server_credentials(
        self, server_id: str, encrypted_credentials: str
    ) -> bool:
        """Update credentials for a server."""
        try:
            now = datetime.now(UTC).isoformat()
            async with self._conn.get_connection() as conn:
                await conn.execute(
                    """UPDATE server_credentials
                       SET encrypted_data = ?, updated_at = ?
                       WHERE server_id = ?""",
                    (encrypted_credentials, now, server_id),
                )
                await conn.commit()
            return True
        except Exception as e:
            logger.error("Failed to update credentials", error=str(e))
            return False

    async def update_server(self, server_id: str, **kwargs) -> bool:
        """Update server in database."""
        try:
            updates = []
            values = []
            for key, value in kwargs.items():
                if value is not None:
                    if key not in ALLOWED_SERVER_COLUMNS:
                        logger.warning(
                            "Rejected invalid column in update_server", column=key
                        )
                        raise ValueError(f"Invalid column name: {key}")
                    updates.append(f"{key} = ?")
                    values.append(value)

            if not updates:
                return True

            values.append(server_id)
            query = f"UPDATE servers SET {', '.join(updates)} WHERE id = ?"

            async with self._conn.get_connection() as conn:
                await conn.execute(query, values)
                await conn.commit()
            return True
        except Exception as e:
            logger.error("Failed to update server", error=str(e))
            return False

    async def delete_server(self, server_id: str) -> bool:
        """Delete server from database."""
        try:
            async with self._conn.get_connection() as conn:
                await conn.execute("DELETE FROM servers WHERE id = ?", (server_id,))
                await conn.commit()
            return True
        except Exception as e:
            logger.error("Failed to delete server", error=str(e))
            return False

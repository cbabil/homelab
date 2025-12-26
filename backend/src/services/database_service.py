"""
Database Service for User Management

Provides async database operations for user authentication and management.
Handles user queries, password verification, and session management with the SQLite database.
"""

import json
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite
import sqlite3
import structlog

from models.auth import User, UserRole
from models.preparation import ServerPreparation, PreparationLog, PreparationStatus, PreparationStep
from models.app_catalog import InstalledApp, InstallationStatus

logger = structlog.get_logger("database_service")


class DatabaseService:
    """Async database service for user management operations."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        data_directory: str | Path | None = None,
    ):
        """Initialize database service with path to homelab.db."""

        backend_root = Path(__file__).resolve().parents[2]

        if db_path is not None and data_directory is not None:
            raise ValueError("Provide either db_path or data_directory, not both")

        if db_path is not None:
            resolved_path = Path(db_path)
            if not resolved_path.is_absolute():
                resolved_path = (backend_root / resolved_path).resolve()
        else:
            directory = Path(data_directory if data_directory is not None else os.getenv("DATA_DIRECTORY", "data"))
            if not directory.is_absolute():
                directory = (backend_root / directory).resolve()
            resolved_path = directory / "homelab.db"

        self.db_path = str(resolved_path)
        logger.info("Database service initialized", db_path=self.db_path)

    @asynccontextmanager
    async def get_connection(self):
        """Get async database connection with automatic cleanup."""
        async with aiosqlite.connect(self.db_path) as connection:
            # Enable row factory for dict-like access
            connection.row_factory = aiosqlite.Row
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username from database."""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    """
                    SELECT id, username, email, role, created_at, last_login, is_active, preferences_json
                    FROM users
                    WHERE username = ? AND is_active = 1
                    """,
                    (username,)
                )
                row = await cursor.fetchone()

                if not row:
                    logger.debug("User not found", username=username)
                    return None

                # Parse preferences JSON
                preferences = {}
                if row['preferences_json']:
                    try:
                        preferences = json.loads(row['preferences_json'])
                    except json.JSONDecodeError:
                        logger.warning("Invalid preferences JSON for user", username=username)
                        preferences = {}

                # Create User model
                user = User(
                    id=row['id'],
                    username=row['username'],
                    email=row['email'],
                    role=UserRole(row['role']),
                    last_login=row['last_login'] or datetime.now(UTC).isoformat(),
                    is_active=bool(row['is_active']),
                    preferences=preferences
                )

                logger.debug("User retrieved successfully", username=username, user_id=user.id)
                return user

        except Exception as e:
            logger.error("Failed to get user by username", username=username, error=str(e))
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID from database."""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    """
                    SELECT id, username, email, role, created_at, last_login, is_active, preferences_json
                    FROM users
                    WHERE id = ? AND is_active = 1
                    """,
                    (user_id,)
                )
                row = await cursor.fetchone()

                if not row:
                    logger.debug("User not found", user_id=user_id)
                    return None

                # Parse preferences JSON
                preferences = {}
                if row['preferences_json']:
                    try:
                        preferences = json.loads(row['preferences_json'])
                    except json.JSONDecodeError:
                        logger.warning("Invalid preferences JSON for user", user_id=user_id)
                        preferences = {}

                # Create User model
                user = User(
                    id=row['id'],
                    username=row['username'],
                    email=row['email'],
                    role=UserRole(row['role']),
                    last_login=row['last_login'] or datetime.now(UTC).isoformat(),
                    is_active=bool(row['is_active']),
                    preferences=preferences
                )

                logger.debug("User retrieved successfully", user_id=user_id, username=user.username)
                return user

        except Exception as e:
            logger.error("Failed to get user by ID", user_id=user_id, error=str(e))
            return None

    async def get_user_password_hash(self, username: str) -> Optional[str]:
        """Get user's password hash from database."""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT password_hash FROM users WHERE username = ? AND is_active = 1",
                    (username,)
                )
                row = await cursor.fetchone()

                if row:
                    logger.debug("Password hash retrieved for user", username=username)
                    return row['password_hash']
                else:
                    logger.debug("No password hash found for user", username=username)
                    return None

        except Exception as e:
            logger.error("Failed to get password hash", username=username, error=str(e))
            return None

    async def update_user_last_login(self, username: str, timestamp: Optional[str] = None) -> bool:
        """Update user's last login timestamp."""
        if timestamp is None:
            timestamp = datetime.now(UTC).isoformat()

        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    "UPDATE users SET last_login = ? WHERE username = ?",
                    (timestamp, username)
                )
                await conn.commit()

                logger.debug("Updated last login for user", username=username, timestamp=timestamp)
                return True

        except Exception as e:
            logger.error("Failed to update last login", username=username, error=str(e))
            return False

    async def get_all_users(self) -> List[User]:
        """Get all active users from database."""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    """
                    SELECT id, username, email, role, created_at, last_login, is_active, preferences_json
                    FROM users
                    WHERE is_active = 1
                    ORDER BY username
                    """
                )
                rows = await cursor.fetchall()

                users = []
                for row in rows:
                    # Parse preferences JSON
                    preferences = {}
                    if row['preferences_json']:
                        try:
                            preferences = json.loads(row['preferences_json'])
                        except json.JSONDecodeError:
                            preferences = {}

                    user = User(
                        id=row['id'],
                        username=row['username'],
                        email=row['email'],
                        role=UserRole(row['role']),
                        last_login=row['last_login'] or datetime.now(UTC).isoformat(),
                        is_active=bool(row['is_active']),
                        preferences=preferences
                    )
                    users.append(user)

                logger.debug("Retrieved all users", count=len(users))
                return users

        except Exception as e:
            logger.error("Failed to get all users", error=str(e))
            return []

    async def create_user(self, username: str, email: str, password_hash: str,
                         role: UserRole = UserRole.USER,
                         preferences: Optional[Dict[str, Any]] = None) -> Optional[User]:
        """Create a new user in the database."""
        try:
            import uuid
            user_id = str(uuid.uuid4())
            now = datetime.now(UTC).isoformat()
            preferences_json = json.dumps(preferences or {})

            async with self.get_connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO users (id, username, email, password_hash, role, created_at, is_active, preferences_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, username, email, password_hash, role.value, now, True, preferences_json)
                )
                await conn.commit()

                user = User(
                    id=user_id,
                    username=username,
                    email=email,
                    role=role,
                    last_login=now,
                    is_active=True,
                    preferences=preferences or {}
                )

                logger.info("Created new user", username=username, user_id=user_id, role=role.value)
                return user

        except Exception as e:
            logger.error("Failed to create user", username=username, error=str(e))
            return None

    async def verify_database_connection(self) -> bool:
        """Verify database connection and table existence."""
        try:
            async with self.get_connection() as conn:
                # Check if users table exists and has expected columns
                cursor = await conn.execute("PRAGMA table_info(users)")
                columns = await cursor.fetchall()

                required_columns = {'id', 'username', 'email', 'password_hash', 'role', 'is_active'}
                existing_columns = {col['name'] for col in columns}

                if not required_columns.issubset(existing_columns):
                    missing = required_columns - existing_columns
                    logger.error("Missing required columns in users table", missing=list(missing))
                    return False

                # Test a simple query
                cursor = await conn.execute("SELECT COUNT(*) as count FROM users")
                result = await cursor.fetchone()
                user_count = result['count']

                logger.info("Database connection verified", user_count=user_count)
                return True

        except Exception as e:
            logger.error("Database connection verification failed", error=str(e))
            return False

    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences in database."""
        try:
            preferences_json = json.dumps(preferences)

            async with self.get_connection() as conn:
                await conn.execute(
                    "UPDATE users SET preferences_json = ? WHERE id = ?",
                    (preferences_json, user_id)
                )
                await conn.commit()

                logger.debug("Updated user preferences", user_id=user_id)
                return True

        except Exception as e:
            logger.error("Failed to update user preferences", user_id=user_id, error=str(e))
            return False

    async def get_log_entries_count_before_date(self, cutoff_date: str) -> int:
        """Get count of log entries before specified date for retention operations."""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT COUNT(*) as count FROM log_entries WHERE timestamp < ?",
                    (cutoff_date,)
                )
                result = await cursor.fetchone()
                return result['count'] if result else 0

        except Exception as e:
            logger.error("Failed to count log entries", cutoff_date=cutoff_date, error=str(e))
            return 0

    async def delete_log_entries_before_date(self, cutoff_date: str, batch_size: int = 1000) -> int:
        """Delete log entries before specified date in batches."""
        total_deleted = 0

        try:
            async with self.get_connection() as conn:
                await conn.execute("BEGIN IMMEDIATE")

                try:
                    while True:
                        cursor = await conn.execute(
                            "DELETE FROM log_entries WHERE timestamp < ? LIMIT ?",
                            (cutoff_date, batch_size)
                        )

                        deleted_count = cursor.rowcount
                        total_deleted += deleted_count

                        logger.debug("Deleted batch of log entries",
                                   batch_size=deleted_count, total=total_deleted)

                        if deleted_count < batch_size:
                            break

                    await conn.commit()
                    logger.info("Successfully deleted log entries", total=total_deleted)
                    return total_deleted

                except Exception as e:
                    await conn.rollback()
                    logger.error("Log deletion failed, rolled back", error=str(e))
                    raise

        except Exception as e:
            logger.error("Failed to delete log entries", error=str(e))
            raise

    async def create_server(
        self,
        id: str,
        name: str,
        host: str,
        port: int,
        username: str,
        auth_type: str,
        encrypted_credentials: str
    ) -> Optional["ServerConnection"]:
        """Create a new server in the database."""
        from datetime import datetime, UTC
        from models.server import ServerConnection, AuthType, ServerStatus

        try:
            now = datetime.now(UTC).isoformat()

            async with self.get_connection() as conn:
                await conn.execute(
                    """INSERT INTO servers (id, name, host, port, username, auth_type, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (id, name, host, port, username, auth_type, "disconnected", now)
                )

                await conn.execute(
                    """INSERT INTO server_credentials (server_id, encrypted_data, created_at, updated_at)
                       VALUES (?, ?, ?, ?)""",
                    (id, encrypted_credentials, now, now)
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
                created_at=now
            )
        except Exception as e:
            logger.error("Failed to create server", error=str(e))
            return None

    async def get_server_by_id(self, server_id: str) -> Optional["ServerConnection"]:
        """Get server by ID."""
        from models.server import ServerConnection, AuthType, ServerStatus

        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM servers WHERE id = ?", (server_id,)
                )
                row = await cursor.fetchone()

            if not row:
                return None

            return ServerConnection(
                id=row["id"],
                name=row["name"],
                host=row["host"],
                port=row["port"],
                username=row["username"],
                auth_type=AuthType(row["auth_type"]),
                status=ServerStatus(row["status"]),
                created_at=row["created_at"],
                last_connected=row["last_connected"]
            )
        except Exception as e:
            logger.error("Failed to get server", error=str(e))
            return None

    async def get_all_servers_from_db(self) -> list:
        """Get all servers from database."""
        from models.server import ServerConnection, AuthType, ServerStatus

        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute("SELECT * FROM servers")
                rows = await cursor.fetchall()

            return [
                ServerConnection(
                    id=row["id"],
                    name=row["name"],
                    host=row["host"],
                    port=row["port"],
                    username=row["username"],
                    auth_type=AuthType(row["auth_type"]),
                    status=ServerStatus(row["status"]),
                    created_at=row["created_at"],
                    last_connected=row["last_connected"]
                )
                for row in rows
            ]
        except Exception as e:
            logger.error("Failed to get servers", error=str(e))
            return []

    async def get_server_credentials(self, server_id: str) -> Optional[str]:
        """Get encrypted credentials for a server."""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT encrypted_data FROM server_credentials WHERE server_id = ?",
                    (server_id,)
                )
                row = await cursor.fetchone()
            return row["encrypted_data"] if row else None
        except Exception as e:
            logger.error("Failed to get credentials", error=str(e))
            return None

    async def update_server(self, server_id: str, **kwargs) -> bool:
        """Update server in database."""
        try:
            updates = []
            values = []
            for key, value in kwargs.items():
                if value is not None:
                    updates.append(f"{key} = ?")
                    values.append(value)

            if not updates:
                return True

            values.append(server_id)
            query = f"UPDATE servers SET {', '.join(updates)} WHERE id = ?"

            async with self.get_connection() as conn:
                await conn.execute(query, values)
                await conn.commit()
            return True
        except Exception as e:
            logger.error("Failed to update server", error=str(e))
            return False

    async def delete_server(self, server_id: str) -> bool:
        """Delete server from database."""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    "DELETE FROM servers WHERE id = ?", (server_id,)
                )
                await conn.commit()
            return True
        except Exception as e:
            logger.error("Failed to delete server", error=str(e))
            return False

    async def create_preparation(
        self,
        id: str,
        server_id: str,
        status: str,
        started_at: str
    ) -> Optional[ServerPreparation]:
        """Create a new preparation record."""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    """INSERT INTO server_preparations (id, server_id, status, started_at)
                       VALUES (?, ?, ?, ?)""",
                    (id, server_id, status, started_at)
                )
                await conn.commit()

            return ServerPreparation(
                id=id,
                server_id=server_id,
                status=PreparationStatus(status),
                started_at=started_at
            )
        except Exception as e:
            logger.error("Failed to create preparation", error=str(e))
            return None

    async def update_preparation(self, prep_id: str, **kwargs) -> bool:
        """Update preparation record."""
        try:
            updates = []
            values = []
            for key, value in kwargs.items():
                if value is not None:
                    updates.append(f"{key} = ?")
                    values.append(value)

            if not updates:
                return True

            values.append(prep_id)
            query = f"UPDATE server_preparations SET {', '.join(updates)} WHERE id = ?"

            async with self.get_connection() as conn:
                await conn.execute(query, values)
                await conn.commit()
            return True
        except Exception as e:
            logger.error("Failed to update preparation", error=str(e))
            return False

    async def add_preparation_log(
        self,
        id: str,
        server_id: str,
        preparation_id: str,
        step: str,
        status: str,
        message: str,
        timestamp: str,
        output: str = None,
        error: str = None
    ) -> bool:
        """Add preparation log entry."""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    """INSERT INTO preparation_logs
                       (id, server_id, preparation_id, step, status, message, output, error, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (id, server_id, preparation_id, step, status, message, output, error, timestamp)
                )
                await conn.commit()
            return True
        except Exception as e:
            logger.error("Failed to add preparation log", error=str(e))
            return False

    async def get_preparation(self, server_id: str) -> Optional[ServerPreparation]:
        """Get latest preparation for a server."""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    """SELECT * FROM server_preparations
                       WHERE server_id = ? ORDER BY started_at DESC LIMIT 1""",
                    (server_id,)
                )
                row = await cursor.fetchone()

            if not row:
                return None

            return ServerPreparation(
                id=row["id"],
                server_id=row["server_id"],
                status=PreparationStatus(row["status"]),
                current_step=PreparationStep(row["current_step"]) if row["current_step"] else None,
                detected_os=row["detected_os"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                error_message=row["error_message"]
            )
        except Exception as e:
            logger.error("Failed to get preparation", error=str(e))
            return None

    async def get_preparation_logs(self, server_id: str) -> list:
        """Get all preparation logs for a server."""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    """SELECT * FROM preparation_logs
                       WHERE server_id = ? ORDER BY timestamp ASC""",
                    (server_id,)
                )
                rows = await cursor.fetchall()

            return [
                PreparationLog(
                    id=row["id"],
                    server_id=row["server_id"],
                    step=PreparationStep(row["step"]),
                    status=PreparationStatus(row["status"]),
                    message=row["message"],
                    output=row["output"],
                    error=row["error"],
                    timestamp=row["timestamp"]
                )
                for row in rows
            ]
        except Exception as e:
            logger.error("Failed to get preparation logs", error=str(e))
            return []

    async def create_installation(
        self,
        id: str,
        server_id: str,
        app_id: str,
        container_name: str,
        status: str,
        config: dict,
        installed_at: str
    ) -> Optional[InstalledApp]:
        """Create a new installation record."""
        try:
            config_json = json.dumps(config) if config else "{}"
            async with self.get_connection() as conn:
                await conn.execute(
                    """INSERT INTO installed_apps
                       (id, server_id, app_id, container_name, status, config, installed_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (id, server_id, app_id, container_name, status, config_json, installed_at)
                )
                await conn.commit()

            return InstalledApp(
                id=id,
                server_id=server_id,
                app_id=app_id,
                container_name=container_name,
                status=InstallationStatus(status),
                config=config,
                installed_at=installed_at
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
                    updates.append(f"{key} = ?")
                    values.append(value)

            if not updates:
                return True

            values.append(install_id)
            query = f"UPDATE installed_apps SET {', '.join(updates)} WHERE id = ?"

            async with self.get_connection() as conn:
                await conn.execute(query, values)
                await conn.commit()
            return True
        except Exception as e:
            logger.error("Failed to update installation", error=str(e))
            return False

    async def get_installation(self, server_id: str, app_id: str) -> Optional[InstalledApp]:
        """Get installation by server and app ID."""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    """SELECT * FROM installed_apps
                       WHERE server_id = ? AND app_id = ?""",
                    (server_id, app_id)
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
                error_message=row["error_message"]
            )
        except Exception as e:
            logger.error("Failed to get installation", error=str(e))
            return None

    async def get_installations(self, server_id: str) -> list:
        """Get all installations for a server."""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    """SELECT * FROM installed_apps WHERE server_id = ?""",
                    (server_id,)
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
                    error_message=row["error_message"]
                )
                for row in rows
            ]
        except Exception as e:
            logger.error("Failed to get installations", error=str(e))
            return []

    async def delete_installation(self, server_id: str, app_id: str) -> bool:
        """Delete installation record."""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    """DELETE FROM installed_apps WHERE server_id = ? AND app_id = ?""",
                    (server_id, app_id)
                )
                await conn.commit()
            return True
        except Exception as e:
            logger.error("Failed to delete installation", error=str(e))
            return False

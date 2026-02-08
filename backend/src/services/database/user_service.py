"""User Database Service.

Database operations for user authentication and management.
"""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from models.auth import User, UserRole

from .base import DatabaseConnection

logger = structlog.get_logger("database.user")


class UserDatabaseService:
    """Database operations for user management."""

    def __init__(self, connection: DatabaseConnection):
        """Initialize with database connection.

        Args:
            connection: DatabaseConnection instance.
        """
        self._conn = connection

    async def get_user(
        self, user_id: str | None = None, username: str | None = None
    ) -> User | None:
        """Get user from database by ID or username.

        Args:
            user_id: User's unique ID.
            username: User's username.

        Returns:
            User object if found, None otherwise.

        Raises:
            ValueError: If neither user_id nor username is provided.
        """
        if not user_id and not username:
            raise ValueError("Either user_id or username must be provided")

        try:
            async with self._conn.get_connection() as conn:
                if user_id:
                    cursor = await conn.execute(
                        """SELECT id, username, email, role, created_at, last_login,
                                  password_changed_at, is_active, preferences_json, avatar
                           FROM users
                           WHERE id = ? AND is_active = 1""",
                        (user_id,),
                    )
                else:
                    cursor = await conn.execute(
                        """SELECT id, username, email, role, created_at, last_login,
                                  password_changed_at, is_active, preferences_json, avatar
                           FROM users
                           WHERE username = ? AND is_active = 1""",
                        (username,),
                    )

                row = await cursor.fetchone()

                if not row:
                    logger.debug("User not found", user_id=user_id, username=username)
                    return None

                preferences = {}
                if row["preferences_json"]:
                    try:
                        preferences = json.loads(row["preferences_json"])
                    except json.JSONDecodeError:
                        logger.warning(
                            "Invalid preferences JSON for user",
                            user_id=user_id,
                            username=username,
                        )
                        preferences = {}

                user = User(
                    id=row["id"],
                    username=row["username"],
                    email=row["email"],
                    role=UserRole(row["role"]),
                    last_login=row["last_login"] or datetime.now(UTC).isoformat(),
                    password_changed_at=row["password_changed_at"],
                    is_active=bool(row["is_active"]),
                    preferences=preferences,
                    avatar=row["avatar"],
                    created_at=row["created_at"],
                )

                logger.debug(
                    "User retrieved successfully",
                    user_id=user.id,
                    username=user.username,
                )
                return user

        except Exception as e:
            logger.error(
                "Failed to get user", user_id=user_id, username=username, error=str(e)
            )
            return None

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username. Wrapper for get_user()."""
        return await self.get_user(username=username)

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID. Wrapper for get_user()."""
        return await self.get_user(user_id=user_id)

    async def get_user_password_hash(self, username: str) -> str | None:
        """Get user's password hash from database."""
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT password_hash FROM users WHERE username = ? AND is_active = 1",
                    (username,),
                )
                row = await cursor.fetchone()

                if row:
                    logger.debug("Password hash retrieved for user", username=username)
                    return row["password_hash"]
                else:
                    logger.debug("No password hash found for user", username=username)
                    return None

        except Exception as e:
            logger.error("Failed to get password hash", username=username, error=str(e))
            return None

    async def update_user_last_login(
        self, username: str, timestamp: str | None = None
    ) -> bool:
        """Update user's last login timestamp."""
        if timestamp is None:
            timestamp = datetime.now(UTC).isoformat()

        try:
            async with self._conn.get_connection() as conn:
                await conn.execute(
                    "UPDATE users SET last_login = ? WHERE username = ?",
                    (timestamp, username),
                )
                await conn.commit()

                logger.debug(
                    "Updated last login for user",
                    username=username,
                    timestamp=timestamp,
                )
                return True

        except Exception as e:
            logger.error("Failed to update last login", username=username, error=str(e))
            return False

    async def get_all_users(self) -> list[User]:
        """Get all active users from database."""
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    """SELECT id, username, email, role, created_at, last_login,
                              is_active, preferences_json
                       FROM users
                       WHERE is_active = 1
                       ORDER BY username"""
                )
                rows = await cursor.fetchall()

                users = []
                for row in rows:
                    preferences = {}
                    if row["preferences_json"]:
                        try:
                            preferences = json.loads(row["preferences_json"])
                        except json.JSONDecodeError:
                            preferences = {}

                    user = User(
                        id=row["id"],
                        username=row["username"],
                        email=row["email"],
                        role=UserRole(row["role"]),
                        last_login=row["last_login"] or datetime.now(UTC).isoformat(),
                        is_active=bool(row["is_active"]),
                        preferences=preferences,
                    )
                    users.append(user)

                logger.debug("Retrieved all users", count=len(users))
                return users

        except Exception as e:
            logger.error("Failed to get all users", error=str(e))
            return []

    async def create_user(
        self,
        username: str,
        password_hash: str,
        email: str = "",
        role: UserRole = UserRole.USER,
        preferences: dict[str, Any] | None = None,
    ) -> User | None:
        """Create a new user in the database. Email is optional."""
        try:
            user_id = str(uuid.uuid4())
            now = datetime.now(UTC).isoformat()
            preferences_json = json.dumps(preferences or {})

            async with self._conn.get_connection() as conn:
                await conn.execute(
                    """INSERT INTO users
                       (id, username, email, password_hash, role, created_at,
                        password_changed_at, is_active, preferences_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        user_id,
                        username,
                        email,
                        password_hash,
                        role.value,
                        now,
                        now,
                        True,
                        preferences_json,
                    ),
                )
                await conn.commit()

                user = User(
                    id=user_id,
                    username=username,
                    email=email,
                    role=role,
                    last_login=now,
                    password_changed_at=now,
                    is_active=True,
                    preferences=preferences or {},
                )

                logger.info(
                    "Created new user",
                    username=username,
                    user_id=user_id,
                    role=role.value,
                )
                return user

        except Exception as e:
            logger.error("Failed to create user", username=username, error=str(e))
            return None

    async def update_user_password(self, username: str, password_hash: str) -> bool:
        """Update user's password and set password_changed_at timestamp."""
        try:
            now = datetime.now(UTC).isoformat()

            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    """UPDATE users
                       SET password_hash = ?, password_changed_at = ?
                       WHERE username = ? AND is_active = 1""",
                    (password_hash, now, username),
                )
                await conn.commit()

                if cursor.rowcount == 0:
                    logger.warning(
                        "User not found for password update", username=username
                    )
                    return False

                logger.info("User password updated", username=username)
                return True

        except Exception as e:
            logger.error(
                "Failed to update user password", username=username, error=str(e)
            )
            return False

    async def has_admin_user(self) -> bool:
        """Check if any active admin user exists in the database."""
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT COUNT(*) as count FROM users WHERE role = ? AND is_active = 1",
                    ("admin",),
                )
                row = await cursor.fetchone()
                exists = (row["count"] if row else 0) > 0
                logger.debug("Admin user existence check", exists=exists)
                return exists
        except Exception as e:
            logger.error("Failed to check admin existence", error=str(e))
            return False

    async def update_user_preferences(
        self, user_id: str, preferences: dict[str, Any]
    ) -> bool:
        """Update user preferences in database."""
        try:
            preferences_json = json.dumps(preferences)

            async with self._conn.get_connection() as conn:
                await conn.execute(
                    "UPDATE users SET preferences_json = ? WHERE id = ?",
                    (preferences_json, user_id),
                )
                await conn.commit()

                logger.debug("Updated user preferences", user_id=user_id)
                return True

        except Exception as e:
            logger.error(
                "Failed to update user preferences", user_id=user_id, error=str(e)
            )
            return False

    async def update_user_avatar(self, user_id: str, avatar: str | None) -> bool:
        """Update user avatar in database.

        Args:
            user_id: User ID to update.
            avatar: Base64 data URL of avatar image, or None to remove.

        Returns:
            True if successful, False otherwise.
        """
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    "UPDATE users SET avatar = ? WHERE id = ?", (avatar, user_id)
                )
                await conn.commit()

                if cursor.rowcount == 0:
                    logger.warning("User not found for avatar update", user_id=user_id)
                    return False

                logger.info(
                    "Updated user avatar",
                    user_id=user_id,
                    has_avatar=avatar is not None,
                )
                return True

        except Exception as e:
            logger.error("Failed to update user avatar", user_id=user_id, error=str(e))
            return False

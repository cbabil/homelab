"""Session Database Service.

Database operations for account locks and login security.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog

from .base import DatabaseConnection

logger = structlog.get_logger("database.session")


class SessionDatabaseService:
    """Database operations for session and account security management."""

    def __init__(self, connection: DatabaseConnection):
        """Initialize with database connection.

        Args:
            connection: DatabaseConnection instance.
        """
        self._conn = connection

    async def is_account_locked(
        self, identifier: str, identifier_type: str = "username"
    ) -> tuple[bool, dict[str, Any] | None]:
        """Check if an account or IP is currently locked.

        Args:
            identifier: Username or IP address to check.
            identifier_type: Either 'username' or 'ip'.

        Returns:
            Tuple of (is_locked, lock_info dict or None).
        """
        try:
            now = datetime.now(UTC).isoformat()

            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    """SELECT * FROM account_locks
                       WHERE identifier = ? AND identifier_type = ?
                       AND locked_at IS NOT NULL
                       AND unlocked_at IS NULL
                       AND (lock_expires_at IS NULL OR lock_expires_at > ?)""",
                    (identifier, identifier_type, now),
                )
                row = await cursor.fetchone()

            if not row:
                return False, None

            lock_info = {
                "id": row["id"],
                "identifier": row["identifier"],
                "identifier_type": row["identifier_type"],
                "attempt_count": row["attempt_count"],
                "locked_at": row["locked_at"],
                "lock_expires_at": row["lock_expires_at"],
                "ip_address": row["ip_address"],
                "reason": row["reason"],
            }

            return True, lock_info

        except Exception as e:
            logger.error(
                "Failed to check account lock", identifier=identifier, error=str(e)
            )
            return False, None

    async def record_failed_login_attempt(
        self,
        identifier: str,
        identifier_type: str = "username",
        ip_address: str | None = None,
        user_agent: str | None = None,
        max_attempts: int = 5,
        lock_duration_minutes: int = 15,
    ) -> tuple[bool, int, str | None]:
        """Record a failed login attempt and lock if threshold reached.

        Args:
            identifier: Username or IP address.
            identifier_type: Either 'username' or 'ip'.
            ip_address: IP address of the attempt.
            user_agent: User agent string.
            max_attempts: Number of attempts before locking.
            lock_duration_minutes: How long to lock (0 for permanent).

        Returns:
            Tuple of (is_now_locked, attempt_count, lock_expires_at or None).
        """
        try:
            now = datetime.now(UTC)
            now_str = now.isoformat()

            lock_expires_at = None
            if lock_duration_minutes > 0:
                lock_expires_at = (
                    now + timedelta(minutes=lock_duration_minutes)
                ).isoformat()

            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    """SELECT * FROM account_locks
                       WHERE identifier = ? AND identifier_type = ?""",
                    (identifier, identifier_type),
                )
                existing = await cursor.fetchone()

                if existing:
                    new_count = existing["attempt_count"] + 1

                    if existing["locked_at"] and not existing["unlocked_at"]:
                        if (
                            not existing["lock_expires_at"]
                            or existing["lock_expires_at"] > now_str
                        ):
                            return True, new_count, existing["lock_expires_at"]

                    should_lock = new_count >= max_attempts
                    locked_at = now_str if should_lock else None
                    new_lock_expires = lock_expires_at if should_lock else None

                    await conn.execute(
                        """UPDATE account_locks SET
                           attempt_count = ?,
                           last_attempt_at = ?,
                           ip_address = COALESCE(?, ip_address),
                           user_agent = COALESCE(?, user_agent),
                           locked_at = COALESCE(?, locked_at),
                           lock_expires_at = COALESCE(?, lock_expires_at),
                           unlocked_at = NULL,
                           unlocked_by = NULL
                           WHERE identifier = ? AND identifier_type = ?""",
                        (
                            new_count,
                            now_str,
                            ip_address,
                            user_agent,
                            locked_at,
                            new_lock_expires,
                            identifier,
                            identifier_type,
                        ),
                    )
                    await conn.commit()

                    logger.info(
                        "Recorded failed login attempt",
                        identifier=identifier,
                        identifier_type=identifier_type,
                        attempt_count=new_count,
                        is_locked=should_lock,
                    )

                    return should_lock, new_count, new_lock_expires

                else:
                    record_id = str(uuid.uuid4())
                    should_lock = max_attempts <= 1

                    await conn.execute(
                        """INSERT INTO account_locks
                           (id, identifier, identifier_type, attempt_count,
                            first_attempt_at, last_attempt_at, ip_address, user_agent,
                            locked_at, lock_expires_at, reason)
                           VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?, 'too_many_attempts')""",
                        (
                            record_id,
                            identifier,
                            identifier_type,
                            now_str,
                            now_str,
                            ip_address,
                            user_agent,
                            now_str if should_lock else None,
                            lock_expires_at if should_lock else None,
                        ),
                    )
                    await conn.commit()

                    logger.info(
                        "Created failed login attempt record",
                        identifier=identifier,
                        identifier_type=identifier_type,
                    )

                    return should_lock, 1, lock_expires_at if should_lock else None

        except Exception as e:
            logger.error(
                "Failed to record failed login attempt",
                identifier=identifier,
                error=str(e),
            )
            return False, 0, None

    async def clear_failed_attempts(
        self, identifier: str, identifier_type: str = "username"
    ) -> bool:
        """Clear failed login attempts after successful login.

        Args:
            identifier: Username or IP address.
            identifier_type: Either 'username' or 'ip'.

        Returns:
            True if successful.
        """
        try:
            async with self._conn.get_connection() as conn:
                await conn.execute(
                    """DELETE FROM account_locks
                       WHERE identifier = ? AND identifier_type = ?
                       AND locked_at IS NULL""",
                    (identifier, identifier_type),
                )
                await conn.commit()

            logger.debug("Cleared failed attempts", identifier=identifier)
            return True

        except Exception as e:
            logger.error(
                "Failed to clear failed attempts", identifier=identifier, error=str(e)
            )
            return False

    async def get_locked_accounts(
        self, include_expired: bool = False, include_unlocked: bool = False
    ) -> list[dict[str, Any]]:
        """Get all locked accounts.

        Args:
            include_expired: Include locks that have expired.
            include_unlocked: Include accounts that were manually unlocked.

        Returns:
            List of locked account records.
        """
        try:
            now = datetime.now(UTC).isoformat()

            query = "SELECT * FROM account_locks WHERE locked_at IS NOT NULL"
            params: list[Any] = []

            if not include_unlocked:
                query += " AND unlocked_at IS NULL"

            if not include_expired:
                query += " AND (lock_expires_at IS NULL OR lock_expires_at > ?)"
                params.append(now)

            query += " ORDER BY locked_at DESC"

            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()

            return [
                {
                    "id": row["id"],
                    "identifier": row["identifier"],
                    "identifier_type": row["identifier_type"],
                    "attempt_count": row["attempt_count"],
                    "first_attempt_at": row["first_attempt_at"],
                    "last_attempt_at": row["last_attempt_at"],
                    "locked_at": row["locked_at"],
                    "lock_expires_at": row["lock_expires_at"],
                    "ip_address": row["ip_address"],
                    "user_agent": row["user_agent"],
                    "reason": row["reason"],
                    "unlocked_at": row["unlocked_at"],
                    "unlocked_by": row["unlocked_by"],
                    "notes": row["notes"],
                }
                for row in rows
            ]

        except Exception as e:
            logger.error("Failed to get locked accounts", error=str(e))
            return []

    async def unlock_account(
        self, lock_id: str, unlocked_by: str, notes: str | None = None
    ) -> bool:
        """Unlock a locked account.

        Args:
            lock_id: ID of the lock record to unlock.
            unlocked_by: Username or ID of admin who unlocked.
            notes: Optional notes about why it was unlocked.

        Returns:
            True if successful.
        """
        try:
            now = datetime.now(UTC).isoformat()

            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    """UPDATE account_locks SET
                       unlocked_at = ?,
                       unlocked_by = ?,
                       notes = COALESCE(?, notes),
                       attempt_count = 0
                       WHERE id = ?""",
                    (now, unlocked_by, notes, lock_id),
                )
                await conn.commit()

                if cursor.rowcount == 0:
                    logger.warning("Lock record not found", lock_id=lock_id)
                    return False

            logger.info("Account unlocked", lock_id=lock_id, unlocked_by=unlocked_by)
            return True

        except Exception as e:
            logger.error("Failed to unlock account", lock_id=lock_id, error=str(e))
            return False

    async def lock_account(
        self,
        lock_id: str,
        locked_by: str,
        notes: str | None = None,
        lock_duration_minutes: int = 15,
    ) -> bool:
        """Lock an account (re-lock after unlock or extend lock).

        Args:
            lock_id: ID of the lock record to re-lock.
            locked_by: Username or ID of admin who locked.
            notes: Optional notes about why it was locked.
            lock_duration_minutes: How long to lock the account.

        Returns:
            True if successful.
        """
        try:
            now = datetime.now(UTC)
            lock_expires_at = (
                now + timedelta(minutes=lock_duration_minutes)
            ).isoformat()

            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    """UPDATE account_locks SET
                       locked_at = ?,
                       lock_expires_at = ?,
                       unlocked_at = NULL,
                       unlocked_by = NULL,
                       notes = COALESCE(?, notes)
                       WHERE id = ?""",
                    (now.isoformat(), lock_expires_at, notes, lock_id),
                )
                await conn.commit()

                if cursor.rowcount == 0:
                    logger.warning(
                        "Lock record not found for manual lock", lock_id=lock_id
                    )
                    return False

            logger.info(
                "Account manually locked",
                lock_id=lock_id,
                locked_by=locked_by,
                expires_at=lock_expires_at,
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to manually lock account", lock_id=lock_id, error=str(e)
            )
            return False

    async def get_lock_by_id(self, lock_id: str) -> dict[str, Any] | None:
        """Get a lock record by ID.

        Args:
            lock_id: ID of the lock record.

        Returns:
            Lock record dict or None.
        """
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM account_locks WHERE id = ?", (lock_id,)
                )
                row = await cursor.fetchone()

            if not row:
                return None

            return {
                "id": row["id"],
                "identifier": row["identifier"],
                "identifier_type": row["identifier_type"],
                "attempt_count": row["attempt_count"],
                "first_attempt_at": row["first_attempt_at"],
                "last_attempt_at": row["last_attempt_at"],
                "locked_at": row["locked_at"],
                "lock_expires_at": row["lock_expires_at"],
                "ip_address": row["ip_address"],
                "user_agent": row["user_agent"],
                "reason": row["reason"],
                "unlocked_at": row["unlocked_at"],
                "unlocked_by": row["unlocked_by"],
                "notes": row["notes"],
            }

        except Exception as e:
            logger.error("Failed to get lock by ID", lock_id=lock_id, error=str(e))
            return None

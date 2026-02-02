"""
Session Service

Handles session CRUD operations for persistent session management.
"""

import uuid
from datetime import datetime, timedelta, UTC
from typing import Optional, List
import structlog
from models.session import Session, SessionStatus, SessionListResponse
from services.database_service import DatabaseService

logger = structlog.get_logger("session_service")

# Default idle timeout in seconds (15 minutes) - used if setting not found
DEFAULT_IDLE_TIMEOUT_SECONDS = 900


class SessionService:
    """Service for managing user sessions."""

    def __init__(self, db_service: Optional[DatabaseService] = None):
        """Initialize session service.

        Args:
            db_service: Database service instance.
        """
        self.db_service = db_service or DatabaseService()
        logger.info("Session service initialized")

    async def get_idle_timeout_seconds(self) -> int:
        """Get idle timeout from settings.

        Returns:
            Idle timeout in seconds.
        """
        try:
            async with self.db_service.get_connection() as conn:
                conn.row_factory = self._dict_factory
                cursor = await conn.execute(
                    "SELECT setting_value FROM system_settings WHERE setting_key = ?",
                    ("security.session_idle_timeout",)
                )
                row = await cursor.fetchone()

            if row and row["setting_value"]:
                return int(row["setting_value"])
        except Exception as e:
            logger.warning("Failed to get idle timeout from settings", error=str(e))

        return DEFAULT_IDLE_TIMEOUT_SECONDS

    async def mark_idle_sessions(self) -> int:
        """Mark sessions as idle if inactive beyond timeout.

        Returns:
            Number of sessions marked as idle.
        """
        idle_timeout = await self.get_idle_timeout_seconds()
        idle_threshold = datetime.now(UTC) - timedelta(seconds=idle_timeout)

        async with self.db_service.get_connection() as conn:
            cursor = await conn.execute(
                """
                UPDATE sessions
                SET status = ?
                WHERE status = ? AND last_activity < ?
                """,
                (
                    SessionStatus.IDLE.value,
                    SessionStatus.ACTIVE.value,
                    idle_threshold.isoformat()
                )
            )
            await conn.commit()
            count = cursor.rowcount

        if count > 0:
            logger.info("Sessions marked as idle", count=count, idle_timeout_seconds=idle_timeout)

        return count

    async def create_session(
        self,
        user_id: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Session:
        """Create a new session.

        Args:
            user_id: User ID for the session.
            expires_at: When the session expires.
            ip_address: Client IP address.
            user_agent: Client user agent string.

        Returns:
            Created Session object.
        """
        session_id = f"sess_{uuid.uuid4().hex[:16]}"
        now = datetime.now(UTC)

        async with self.db_service.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO sessions (id, user_id, ip_address, user_agent, created_at, expires_at, last_activity, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    user_id,
                    ip_address,
                    user_agent,
                    now.isoformat(),
                    expires_at.isoformat(),
                    now.isoformat(),
                    SessionStatus.ACTIVE.value
                )
            )
            await conn.commit()

        logger.info("Session created", session_id=session_id, user_id=user_id)

        return Session(
            id=session_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
            expires_at=expires_at,
            last_activity=now,
            status=SessionStatus.ACTIVE
        )

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID.

        Args:
            session_id: Session ID to retrieve.

        Returns:
            Session object if found, None otherwise.
        """
        async with self.db_service.get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = await conn.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (session_id,)
            )
            row = await cursor.fetchone()

        if not row:
            return None

        return self._row_to_session(row)

    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None
    ) -> List[SessionListResponse]:
        """List sessions with optional filters.

        Automatically marks inactive sessions as idle before returning.

        Args:
            user_id: Filter by user ID.
            status: Filter by status.

        Returns:
            List of SessionListResponse objects.
        """
        # Auto-detect and mark idle sessions before listing
        await self.mark_idle_sessions()
        # Also cleanup expired sessions
        await self.cleanup_expired_sessions()

        query = """
            SELECT s.*, u.username
            FROM sessions s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE 1=1
        """
        params = []

        if user_id:
            query += " AND s.user_id = ?"
            params.append(user_id)

        if status:
            query += " AND s.status = ?"
            params.append(status.value)

        query += " ORDER BY s.last_activity DESC"

        async with self.db_service.get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

        return [
            SessionListResponse(
                id=row["id"],
                user_id=row["user_id"],
                username=row.get("username"),
                ip_address=row["ip_address"],
                user_agent=row["user_agent"],
                created_at=row["created_at"],
                expires_at=row["expires_at"],
                last_activity=row["last_activity"],
                status=row["status"]
            )
            for row in rows
        ]

    async def update_session(self, session_id: str) -> bool:
        """Update session last_activity to now.

        Args:
            session_id: Session ID to update.

        Returns:
            True if updated, False otherwise.
        """
        now = datetime.now(UTC)

        async with self.db_service.get_connection() as conn:
            cursor = await conn.execute(
                """
                UPDATE sessions
                SET last_activity = ?, status = ?
                WHERE id = ? AND status IN (?, ?)
                """,
                (
                    now.isoformat(),
                    SessionStatus.ACTIVE.value,
                    session_id,
                    SessionStatus.ACTIVE.value,
                    SessionStatus.IDLE.value
                )
            )
            await conn.commit()
            updated = cursor.rowcount > 0

        if updated:
            logger.debug("Session updated", session_id=session_id)
        return updated

    async def delete_session(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        terminated_by: str = "system",
        exclude_session_id: Optional[str] = None
    ) -> int:
        """Soft-delete (terminate) sessions.

        Args:
            session_id: Specific session to terminate.
            user_id: Terminate all sessions for user.
            terminated_by: User ID who terminated or 'system'.
            exclude_session_id: Session to exclude (keep current session).

        Returns:
            Number of sessions terminated.
        """
        now = datetime.now(UTC)

        if session_id:
            # Delete specific session
            query = """
                UPDATE sessions
                SET status = ?, terminated_at = ?, terminated_by = ?
                WHERE id = ? AND status IN (?, ?)
            """
            params = (
                SessionStatus.TERMINATED.value,
                now.isoformat(),
                terminated_by,
                session_id,
                SessionStatus.ACTIVE.value,
                SessionStatus.IDLE.value
            )
        elif user_id:
            # Delete all sessions for user
            if exclude_session_id:
                query = """
                    UPDATE sessions
                    SET status = ?, terminated_at = ?, terminated_by = ?
                    WHERE user_id = ? AND id != ? AND status IN (?, ?)
                """
                params = (
                    SessionStatus.TERMINATED.value,
                    now.isoformat(),
                    terminated_by,
                    user_id,
                    exclude_session_id,
                    SessionStatus.ACTIVE.value,
                    SessionStatus.IDLE.value
                )
            else:
                query = """
                    UPDATE sessions
                    SET status = ?, terminated_at = ?, terminated_by = ?
                    WHERE user_id = ? AND status IN (?, ?)
                """
                params = (
                    SessionStatus.TERMINATED.value,
                    now.isoformat(),
                    terminated_by,
                    user_id,
                    SessionStatus.ACTIVE.value,
                    SessionStatus.IDLE.value
                )
        else:
            logger.warning("delete_session called without session_id or user_id")
            return 0

        async with self.db_service.get_connection() as conn:
            cursor = await conn.execute(query, params)
            await conn.commit()
            count = cursor.rowcount

        logger.info("Sessions terminated", count=count, terminated_by=terminated_by)
        return count

    async def cleanup_expired_sessions(self) -> int:
        """Mark expired sessions based on expires_at.

        Returns:
            Number of sessions marked as expired.
        """
        now = datetime.now(UTC)

        async with self.db_service.get_connection() as conn:
            cursor = await conn.execute(
                """
                UPDATE sessions
                SET status = ?, terminated_at = ?, terminated_by = ?
                WHERE expires_at < ? AND status IN (?, ?)
                """,
                (
                    SessionStatus.EXPIRED.value,
                    now.isoformat(),
                    "system",
                    now.isoformat(),
                    SessionStatus.ACTIVE.value,
                    SessionStatus.IDLE.value
                )
            )
            await conn.commit()
            count = cursor.rowcount

        logger.info("Expired sessions cleaned up", count=count)
        return count

    async def validate_session(self, session_id: str) -> Optional[Session]:
        """Validate a session is active and not expired.

        Args:
            session_id: Session ID to validate.

        Returns:
            Session if valid, None otherwise.
        """
        session = await self.get_session(session_id)

        if not session:
            return None

        # Check if expired
        if session.expires_at < datetime.now(UTC):
            # Mark as expired
            await self.delete_session(session_id=session_id, terminated_by="system")
            return None

        # Check status
        if session.status not in (SessionStatus.ACTIVE, SessionStatus.IDLE):
            return None

        return session

    def _dict_factory(self, cursor, row):
        """Convert row to dictionary."""
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def _row_to_session(self, row: dict) -> Session:
        """Convert database row to Session model."""
        return Session(
            id=row["id"],
            user_id=row["user_id"],
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            last_activity=datetime.fromisoformat(row["last_activity"]),
            status=SessionStatus(row["status"]),
            terminated_at=datetime.fromisoformat(row["terminated_at"]) if row["terminated_at"] else None,
            terminated_by=row["terminated_by"]
        )

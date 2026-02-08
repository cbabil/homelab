"""
Notification Service

Handles notification CRUD operations for persistent notification management.
"""

import json
import uuid
from datetime import UTC, datetime

import structlog

from models.notification import (
    Notification,
    NotificationCountResponse,
    NotificationListResponse,
    NotificationListResult,
    NotificationType,
)
from services.database_service import DatabaseService

logger = structlog.get_logger("notification_service")


class NotificationService:
    """Service for managing user notifications."""

    def __init__(self, db_service: DatabaseService | None = None):
        """Initialize notification service.

        Args:
            db_service: Database service instance.
        """
        self.db_service = db_service or DatabaseService()
        logger.info("Notification service initialized")

    async def create_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        source: str | None = None,
        metadata: dict | None = None,
        expires_at: datetime | None = None,
    ) -> Notification:
        """Create a new notification.

        Args:
            user_id: User ID for the notification.
            notification_type: Type of notification.
            title: Notification title.
            message: Notification message.
            source: Source of the notification (e.g., 'server', 'app', 'system').
            metadata: Additional data as JSON.
            expires_at: Optional expiration time.

        Returns:
            Created Notification object.
        """
        notification_id = f"notif_{uuid.uuid4().hex[:16]}"
        now = datetime.now(UTC)
        metadata_json = json.dumps(metadata) if metadata else None

        async with self.db_service.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO notifications (id, user_id, type, title, message, read, created_at, source, metadata, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    notification_id,
                    user_id,
                    notification_type.value,
                    title,
                    message,
                    0,
                    now.isoformat(),
                    source,
                    metadata_json,
                    expires_at.isoformat() if expires_at else None,
                ),
            )
            await conn.commit()

        logger.info(
            "Notification created",
            notification_id=notification_id,
            user_id=user_id,
            type=notification_type.value,
        )

        return Notification(
            id=notification_id,
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            read=False,
            created_at=now,
            source=source,
            metadata=metadata,
            expires_at=expires_at,
        )

    async def get_notification(self, notification_id: str) -> Notification | None:
        """Get a notification by ID.

        Args:
            notification_id: Notification ID to retrieve.

        Returns:
            Notification object if found, None otherwise.
        """
        async with self.db_service.get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = await conn.execute(
                "SELECT * FROM notifications WHERE id = ?", (notification_id,)
            )
            row = await cursor.fetchone()

        if not row:
            return None

        return self._row_to_notification(row)

    async def list_notifications(
        self,
        user_id: str,
        read_filter: bool | None = None,
        notification_type: NotificationType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> NotificationListResult:
        """List notifications for a user with optional filters.

        Automatically cleans up expired notifications before returning.

        Args:
            user_id: User ID to get notifications for.
            read_filter: Filter by read status (True=read, False=unread, None=all).
            notification_type: Filter by notification type.
            limit: Maximum number of notifications to return.
            offset: Number of notifications to skip.

        Returns:
            NotificationListResult with notifications and counts.
        """
        await self.cleanup_expired_notifications(user_id)

        query = """
            SELECT * FROM notifications
            WHERE user_id = ? AND dismissed_at IS NULL
        """
        params: list = [user_id]

        if read_filter is not None:
            query += " AND read = ?"
            params.append(1 if read_filter else 0)

        if notification_type:
            query += " AND type = ?"
            params.append(notification_type.value)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        async with self.db_service.get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

            count_cursor = await conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN read = 0 THEN 1 ELSE 0 END) as unread_count
                FROM notifications
                WHERE user_id = ? AND dismissed_at IS NULL
                """,
                (user_id,),
            )
            count_row = await count_cursor.fetchone()

        notifications = [
            NotificationListResponse(
                id=row["id"],
                user_id=row["user_id"],
                type=row["type"],
                title=row["title"],
                message=row["message"],
                read=bool(row["read"]),
                created_at=row["created_at"],
                read_at=row["read_at"],
                source=row["source"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            )
            for row in rows
        ]

        return NotificationListResult(
            notifications=notifications,
            total=count_row["total"] or 0,
            unread_count=count_row["unread_count"] or 0,
        )

    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read.

        Args:
            notification_id: Notification ID to mark as read.
            user_id: User ID (for authorization).

        Returns:
            True if updated, False otherwise.
        """
        now = datetime.now(UTC)

        async with self.db_service.get_connection() as conn:
            cursor = await conn.execute(
                """
                UPDATE notifications
                SET read = 1, read_at = ?
                WHERE id = ? AND user_id = ? AND read = 0
                """,
                (now.isoformat(), notification_id, user_id),
            )
            await conn.commit()
            updated = cursor.rowcount > 0

        if updated:
            logger.debug("Notification marked as read", notification_id=notification_id)
        return updated

    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user.

        Args:
            user_id: User ID.

        Returns:
            Number of notifications marked as read.
        """
        now = datetime.now(UTC)

        async with self.db_service.get_connection() as conn:
            cursor = await conn.execute(
                """
                UPDATE notifications
                SET read = 1, read_at = ?
                WHERE user_id = ? AND read = 0 AND dismissed_at IS NULL
                """,
                (now.isoformat(), user_id),
            )
            await conn.commit()
            count = cursor.rowcount

        logger.info("All notifications marked as read", user_id=user_id, count=count)
        return count

    async def dismiss_notification(self, notification_id: str, user_id: str) -> bool:
        """Dismiss (soft-delete) a notification.

        Args:
            notification_id: Notification ID to dismiss.
            user_id: User ID (for authorization).

        Returns:
            True if dismissed, False otherwise.
        """
        now = datetime.now(UTC)

        async with self.db_service.get_connection() as conn:
            cursor = await conn.execute(
                """
                UPDATE notifications
                SET dismissed_at = ?
                WHERE id = ? AND user_id = ? AND dismissed_at IS NULL
                """,
                (now.isoformat(), notification_id, user_id),
            )
            await conn.commit()
            dismissed = cursor.rowcount > 0

        if dismissed:
            logger.debug("Notification dismissed", notification_id=notification_id)
        return dismissed

    async def dismiss_all(self, user_id: str) -> int:
        """Dismiss all notifications for a user.

        Args:
            user_id: User ID.

        Returns:
            Number of notifications dismissed.
        """
        now = datetime.now(UTC)

        async with self.db_service.get_connection() as conn:
            cursor = await conn.execute(
                """
                UPDATE notifications
                SET dismissed_at = ?
                WHERE user_id = ? AND dismissed_at IS NULL
                """,
                (now.isoformat(), user_id),
            )
            await conn.commit()
            count = cursor.rowcount

        logger.info("All notifications dismissed", user_id=user_id, count=count)
        return count

    async def get_unread_count(self, user_id: str) -> NotificationCountResponse:
        """Get unread notification count for a user.

        Args:
            user_id: User ID.

        Returns:
            NotificationCountResponse with counts.
        """
        async with self.db_service.get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = await conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN read = 0 THEN 1 ELSE 0 END) as unread_count
                FROM notifications
                WHERE user_id = ? AND dismissed_at IS NULL
                """,
                (user_id,),
            )
            row = await cursor.fetchone()

        return NotificationCountResponse(
            unread_count=row["unread_count"] or 0, total=row["total"] or 0
        )

    async def cleanup_expired_notifications(self, user_id: str | None = None) -> int:
        """Dismiss expired notifications.

        Args:
            user_id: Optional user ID to limit cleanup.

        Returns:
            Number of notifications dismissed.
        """
        now = datetime.now(UTC)

        query = """
            UPDATE notifications
            SET dismissed_at = ?
            WHERE expires_at IS NOT NULL
            AND expires_at < ?
            AND dismissed_at IS NULL
        """
        params = [now.isoformat(), now.isoformat()]

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        async with self.db_service.get_connection() as conn:
            cursor = await conn.execute(query, params)
            await conn.commit()
            count = cursor.rowcount

        if count > 0:
            logger.info("Expired notifications cleaned up", count=count)
        return count

    async def delete_old_notifications(self, days: int = 30) -> int:
        """Permanently delete old dismissed notifications.

        Args:
            days: Delete notifications dismissed more than this many days ago.

        Returns:
            Number of notifications deleted.
        """
        async with self.db_service.get_connection() as conn:
            cursor = await conn.execute(
                """
                DELETE FROM notifications
                WHERE dismissed_at IS NOT NULL
                AND datetime(dismissed_at) < datetime('now', ?)
                """,
                (f"-{days} days",),
            )
            await conn.commit()
            count = cursor.rowcount

        if count > 0:
            logger.info("Old notifications deleted", count=count, days=days)
        return count

    def _dict_factory(self, cursor, row):
        """Convert row to dictionary."""
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def _row_to_notification(self, row: dict) -> Notification:
        """Convert database row to Notification model."""
        return Notification(
            id=row["id"],
            user_id=row["user_id"],
            type=NotificationType(row["type"]),
            title=row["title"],
            message=row["message"],
            read=bool(row["read"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            read_at=(
                datetime.fromisoformat(row["read_at"]) if row["read_at"] else None
            ),
            dismissed_at=(
                datetime.fromisoformat(row["dismissed_at"])
                if row["dismissed_at"]
                else None
            ),
            expires_at=(
                datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None
            ),
            source=row["source"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
        )

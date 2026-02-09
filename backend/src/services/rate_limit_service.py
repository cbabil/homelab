"""
Rate Limit Service

Database-backed rate limiting for authentication endpoints.
Persists rate limit events to survive server restarts.
"""

from datetime import UTC, datetime, timedelta

import structlog

from services.database_service import DatabaseService

logger = structlog.get_logger("rate_limit_service")


class RateLimitService:
    """Database-backed rate limiter with sliding window."""

    def __init__(self, db_service: DatabaseService):
        """Initialize with database service.

        Args:
            db_service: DatabaseService instance for persistence.
        """
        self.db_service = db_service

    async def is_allowed(
        self,
        category: str,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        """Check if a request is allowed and record it if so.

        Args:
            category: Event category (e.g. 'login', 'password_change').
            key: Identifier (e.g. IP address, 'username:ip').
            max_requests: Maximum requests allowed in window.
            window_seconds: Time window in seconds.

        Returns:
            True if request is allowed, False if rate limited.
        """
        count = await self.get_count(category, key, window_seconds)

        if count >= max_requests:
            logger.warning(
                "Rate limit exceeded",
                category=category,
                key=key,
                count=count,
                max_requests=max_requests,
            )
            return False

        await self.record(category, key)
        return True

    async def record(self, category: str, key: str) -> None:
        """Record a rate limit event.

        Args:
            category: Event category.
            key: Identifier.
        """
        now = datetime.now(UTC).isoformat()
        async with self.db_service.get_connection() as conn:
            await conn.execute(
                "INSERT INTO rate_limit_events "
                "(category, key, created_at) VALUES (?, ?, ?)",
                (category, key, now),
            )
            await conn.commit()

    async def get_count(
        self, category: str, key: str, window_seconds: int
    ) -> int:
        """Get event count within the time window.

        Args:
            category: Event category.
            key: Identifier.
            window_seconds: Time window in seconds.

        Returns:
            Number of events in the window.
        """
        window_start = (
            datetime.now(UTC) - timedelta(seconds=window_seconds)
        ).isoformat()

        async with self.db_service.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM rate_limit_events "
                "WHERE category = ? AND key = ? "
                "AND created_at > ?",
                (category, key, window_start),
            )
            row = await cursor.fetchone()

        return row[0] if row else 0

    async def reset(self, category: str, key: str) -> None:
        """Reset rate limit for a key by removing its events.

        Args:
            category: Event category.
            key: Identifier.
        """
        async with self.db_service.get_connection() as conn:
            await conn.execute(
                "DELETE FROM rate_limit_events WHERE category = ? AND key = ?",
                (category, key),
            )
            await conn.commit()
        logger.debug("Rate limit reset", category=category, key=key)

    async def cleanup_expired(self, max_window_seconds: int = 3600) -> int:
        """Remove events older than the maximum window.

        Args:
            max_window_seconds: Maximum window to retain (default 1 hour).

        Returns:
            Number of events deleted.
        """
        cutoff = (
            datetime.now(UTC) - timedelta(seconds=max_window_seconds)
        ).isoformat()

        async with self.db_service.get_connection() as conn:
            cursor = await conn.execute(
                "DELETE FROM rate_limit_events WHERE created_at < ?",
                (cutoff,),
            )
            await conn.commit()
            count = cursor.rowcount

        if count > 0:
            logger.debug("Cleaned up expired rate limit events", count=count)
        return count

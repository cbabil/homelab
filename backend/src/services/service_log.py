"""Log Service.

Provides CRUD operations for log entries using raw aiosqlite.
Handles log creation, retrieval, filtering, and database persistence.
"""

import uuid

import structlog

from models.log import LogEntry, LogFilter
from services.database.base import DatabaseConnection

logger = structlog.get_logger("service_log")


class LogService:
    """Service for managing log entries in the database."""

    def __init__(self, connection: DatabaseConnection) -> None:
        self._conn = connection

    async def create_log_entry(self, log_entry: LogEntry) -> LogEntry:
        """Create a new log entry in the database."""
        try:
            if not log_entry.id:
                log_entry = log_entry.model_copy(
                    update={"id": f"log-{uuid.uuid4().hex[:8]}"}
                )

            params = log_entry.to_insert_params()

            async with self._conn.get_connection() as conn:
                await conn.execute(
                    """INSERT INTO log_entries
                       (id, timestamp, level, source, message, tags, extra_data)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        params["id"],
                        params["timestamp"],
                        params["level"],
                        params["source"],
                        params["message"],
                        params["tags"],
                        params["extra_data"],
                    ),
                )
                await conn.commit()

                # Re-fetch to get the created_at default
                cursor = await conn.execute(
                    "SELECT * FROM log_entries WHERE id = ?", (params["id"],)
                )
                row = await cursor.fetchone()
                if row:
                    log_entry = LogEntry.from_row(row)

            logger.info("Log entry created", log_id=log_entry.id, level=log_entry.level)
            return log_entry

        except Exception as e:
            logger.error("Failed to create log entry", error=str(e))
            raise

    async def get_logs(self, filters: LogFilter | None = None) -> list[LogEntry]:
        """Retrieve logs with optional filtering."""
        try:
            sql = "SELECT * FROM log_entries"
            conditions: list[str] = []
            params: list[str | int] = []

            if filters:
                if filters.level:
                    conditions.append("level = ?")
                    params.append(filters.level)
                if filters.source:
                    conditions.append("source = ?")
                    params.append(filters.source)

            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

            sql += " ORDER BY timestamp DESC"

            limit = filters.limit if filters and filters.limit else 100
            offset = filters.offset if filters and filters.offset else 0
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

            logs = [LogEntry.from_row(row) for row in rows]
            logger.info("Logs retrieved", count=len(logs), filters=filters)
            return logs

        except Exception as e:
            logger.error("Failed to retrieve logs", error=str(e))
            raise

    async def get_log_by_id(self, log_id: str) -> LogEntry | None:
        """Retrieve a specific log entry by ID."""
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM log_entries WHERE id = ?", (log_id,)
                )
                row = await cursor.fetchone()

            if row:
                log_entry = LogEntry.from_row(row)
                logger.info("Log entry retrieved", log_id=log_id)
                return log_entry

            logger.info("Log entry not found", log_id=log_id)
            return None

        except Exception as e:
            logger.error("Failed to retrieve log entry", log_id=log_id, error=str(e))
            raise

    async def count_logs(self, filters: LogFilter | None = None) -> int:
        """Count logs with optional filtering (without limit/offset)."""
        try:
            sql = "SELECT COUNT(*) FROM log_entries"
            conditions: list[str] = []
            params: list[str] = []

            if filters:
                if filters.level:
                    conditions.append("level = ?")
                    params.append(filters.level)
                if filters.source:
                    conditions.append("source = ?")
                    params.append(filters.source)

            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                row = await cursor.fetchone()
                count = row[0] if row else 0

            logger.debug("Log count retrieved", count=count, filters=filters)
            return count

        except Exception as e:
            logger.error("Failed to count logs", error=str(e))
            raise

    async def purge_logs(self) -> int:
        """Delete all log entries from the database."""
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM log_entries")
                row = await cursor.fetchone()
                total = row[0] if row else 0

                await conn.execute("DELETE FROM log_entries")
                await conn.commit()

            logger.info("All logs purged", deleted=total)
            return total

        except Exception as e:
            logger.error("Failed to purge logs", error=str(e))
            raise

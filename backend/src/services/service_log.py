"""
Log Service

Provides CRUD operations for log entries using SQLAlchemy and SQLite.
Handles log creation, retrieval, filtering, and database persistence.
"""

import uuid

import structlog
from sqlalchemy import delete, desc, func, select
from sqlalchemy.exc import SQLAlchemyError

from database.connection import db_manager
from init_db.schema_logs import initialize_logs_database
from models.log import LogEntry, LogEntryTable, LogFilter

logger = structlog.get_logger("service_log")


class LogService:
    """Service for managing log entries in the database."""

    def __init__(self):
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure database is initialized."""
        if not self._initialized:
            await initialize_logs_database()
            self._initialized = True

    async def create_log_entry(self, log_entry: LogEntry) -> LogEntry:
        """Create a new log entry in the database."""
        await self._ensure_initialized()

        try:
            # Generate ID if not provided
            if not log_entry.id:
                log_entry.id = f"log-{uuid.uuid4().hex[:8]}"

            table_entry = log_entry.to_table_model()

            async with db_manager.get_session() as session:
                session.add(table_entry)
                await session.flush()  # Get the created_at timestamp
                await session.refresh(table_entry)

                result = LogEntry.from_table_model(table_entry)

            logger.info("Log entry created", log_id=result.id, level=result.level)
            return result

        except SQLAlchemyError as e:
            logger.error("Failed to create log entry", error=str(e))
            raise

    async def get_logs(self, filters: LogFilter | None = None) -> list[LogEntry]:
        """Retrieve logs with optional filtering."""
        await self._ensure_initialized()

        try:
            async with db_manager.get_session() as session:
                query = select(LogEntryTable).order_by(desc(LogEntryTable.timestamp))

                # Apply filters
                if filters:
                    if filters.level:
                        query = query.where(LogEntryTable.level == filters.level)
                    if filters.source:
                        query = query.where(LogEntryTable.source == filters.source)
                    if filters.limit:
                        query = query.limit(filters.limit)
                    if filters.offset:
                        query = query.offset(filters.offset)
                else:
                    query = query.limit(100)  # Default limit

                result = await session.execute(query)
                table_entries = result.scalars().all()

                logs = [LogEntry.from_table_model(entry) for entry in table_entries]

            logger.info("Logs retrieved", count=len(logs), filters=filters)
            return logs

        except SQLAlchemyError as e:
            logger.error("Failed to retrieve logs", error=str(e))
            raise

    async def get_log_by_id(self, log_id: str) -> LogEntry | None:
        """Retrieve a specific log entry by ID."""
        await self._ensure_initialized()

        try:
            async with db_manager.get_session() as session:
                query = select(LogEntryTable).where(LogEntryTable.id == log_id)
                result = await session.execute(query)
                table_entry = result.scalar_one_or_none()

                if table_entry:
                    log_entry = LogEntry.from_table_model(table_entry)
                    logger.info("Log entry retrieved", log_id=log_id)
                    return log_entry
                else:
                    logger.info("Log entry not found", log_id=log_id)
                    return None

        except SQLAlchemyError as e:
            logger.error("Failed to retrieve log entry", log_id=log_id, error=str(e))
            raise

    async def count_logs(self, filters: LogFilter | None = None) -> int:
        """Count logs with optional filtering (without limit/offset)."""
        await self._ensure_initialized()

        try:
            async with db_manager.get_session() as session:
                query = select(func.count()).select_from(LogEntryTable)

                if filters:
                    if filters.level:
                        query = query.where(LogEntryTable.level == filters.level)
                    if filters.source:
                        query = query.where(LogEntryTable.source == filters.source)

                result = await session.execute(query)
                count = result.scalar_one()

            logger.debug("Log count retrieved", count=count, filters=filters)
            return count

        except SQLAlchemyError as e:
            logger.error("Failed to count logs", error=str(e))
            raise

    async def purge_logs(self) -> int:
        """Delete all log entries from the database."""
        await self._ensure_initialized()

        try:
            async with db_manager.get_session() as session:
                count_result = await session.execute(
                    select(func.count()).select_from(LogEntryTable)
                )
                total = count_result.scalar_one()

                await session.execute(delete(LogEntryTable))
                await session.commit()

            logger.info("All logs purged", deleted=total)
            return total
        except SQLAlchemyError as e:
            logger.error("Failed to purge logs", error=str(e))
            raise


# Global service instance
log_service = LogService()

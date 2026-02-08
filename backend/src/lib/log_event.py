"""Event Logging Utility.

Provides a shared log_event function for recording structured events
to the database. Placed in lib/ to avoid layer violations.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from models.log import LogEntry
from services.service_log import log_service

logger = structlog.get_logger("log_event")


async def log_event(
    source: str,
    level: str,
    message: str,
    tags: list[str],
    metadata: dict[str, Any] = None,
) -> None:
    """Log an event to the database.

    Args:
        source: Short source identifier (e.g., "srv", "app", "dkr")
        level: Log level (INFO, WARNING, ERROR)
        message: Log message
        tags: List of tags for categorization
        metadata: Optional metadata dictionary
    """
    try:
        entry = LogEntry(
            id=f"{source}-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(UTC),
            level=level,
            source=source,
            message=message,
            tags=tags,
            metadata=metadata or {},
        )
        await log_service.create_log_entry(entry)
    except Exception as e:
        logger.error("Failed to create log entry", error=str(e), source=source)

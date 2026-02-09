"""Event Logging Utility.

Provides a shared log_event function for recording structured events
to the database. Placed in lib/ to avoid layer violations.

Call ``init_log_event(log_service)`` once at startup (after the factory
creates services) so that all callers of ``log_event()`` write to the DB.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from models.log import LogEntry

logger = structlog.get_logger("log_event")

# Module-level reference set at startup via init_log_event()
_log_service: Any = None


def init_log_event(log_service: Any) -> None:
    """Wire the module to the application's LogService instance."""
    global _log_service  # noqa: PLW0603
    _log_service = log_service


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
    if _log_service is None:
        logger.warning("log_event called before init_log_event", source=source)
        return
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
        await _log_service.create_log_entry(entry)
    except Exception as e:
        logger.error("Failed to create log entry", error=str(e), source=source)

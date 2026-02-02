"""Common utilities shared across tool modules."""

from datetime import datetime, UTC
from typing import Any, Dict, List
import uuid

import structlog
from models.log import LogEntry
from services.service_log import log_service


logger = structlog.get_logger("tools_common")


async def log_event(
    source: str,
    level: str,
    message: str,
    tags: List[str],
    metadata: Dict[str, Any] = None
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
            metadata=metadata or {}
        )
        await log_service.create_log_entry(entry)
    except Exception as e:
        logger.error("Failed to create log entry", error=str(e), source=source)

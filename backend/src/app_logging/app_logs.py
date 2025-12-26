"""Helpers for application-related log entries."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Dict, Any
import uuid

from models.log import LogEntry

APPLICATION_LOG_TAGS = ["application", "catalog"]


def build_empty_search_log(filters: Dict[str, Any]) -> LogEntry:
    """Construct a log entry for searches that return no applications."""

    return LogEntry(
        id=f"app-{uuid.uuid4().hex[:8]}",
        timestamp=datetime.now(UTC),
        level="info",
        source="application_catalog",
        message="Application search returned no results",
        tags=APPLICATION_LOG_TAGS,
        metadata={
            "filters": filters,
        },
        created_at=None,
    )

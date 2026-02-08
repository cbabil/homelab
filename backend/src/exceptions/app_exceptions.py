"""Application-related exceptions."""

from __future__ import annotations

from typing import Any


class ApplicationLogWriteError(Exception):
    """Raised when writing an application catalog log entry fails."""

    def __init__(self, filters: dict[str, Any], original_exception: Exception) -> None:
        message = (
            "Failed to write application catalog log entry "
            f"for filters={filters!r}: {original_exception}"
        )
        super().__init__(message)
        self.filters = filters
        self.original_exception = original_exception

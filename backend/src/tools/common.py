"""Common utilities shared across tool modules.

Re-exports log_event from lib.log_event for backward compatibility.
New code should import directly from lib.log_event.
"""

import structlog

from lib.log_event import log_event  # noqa: F401

logger = structlog.get_logger("tools.common")


def safe_error_message(error: Exception, context: str = "Operation") -> str:
    """Return a generic error message for clients, logging the real error.

    Prevents leaking internal details (stack traces, DB errors, file paths)
    to API consumers while preserving full diagnostics in server logs.
    """
    logger.error(
        f"{context} failed",
        error=str(error),
        error_type=type(error).__name__,
    )
    return f"{context} failed. Check server logs for details."

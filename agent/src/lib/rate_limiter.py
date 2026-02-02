"""Command execution rate limiting.

Provides rate limiting to prevent abuse of command execution.
"""

import threading
import time
from typing import List, Tuple


class CommandRateLimiter:
    """Rate limiter for command execution to prevent abuse (thread-safe)."""

    def __init__(
        self,
        max_commands_per_minute: int = 30,
        max_concurrent: int = 5,
    ) -> None:
        """Initialize rate limiter.

        Args:
            max_commands_per_minute: Maximum commands allowed per minute.
            max_concurrent: Maximum concurrent command executions.
        """
        self._max_per_minute = max_commands_per_minute
        self._max_concurrent = max_concurrent
        self._command_times: List[float] = []
        self._concurrent_count = 0
        self._lock = threading.Lock()

    def acquire(self) -> Tuple[bool, str]:
        """Attempt to acquire permission to execute a command (thread-safe).

        Returns:
            Tuple of (allowed, error_message).
        """
        with self._lock:
            now = time.time()

            # Check concurrent limit
            if self._concurrent_count >= self._max_concurrent:
                return (
                    False,
                    f"Too many concurrent commands (max {self._max_concurrent})",
                )

            # Clean old entries
            cutoff = now - 60
            self._command_times = [t for t in self._command_times if t > cutoff]

            # Check per-minute limit
            if len(self._command_times) >= self._max_per_minute:
                return (False, f"Rate limit exceeded ({self._max_per_minute}/min)")

            # Record this command
            self._command_times.append(now)
            self._concurrent_count += 1
            return (True, "")

    def release(self) -> None:
        """Release a command slot after execution completes (thread-safe)."""
        with self._lock:
            self._concurrent_count = max(0, self._concurrent_count - 1)


# Global command rate limiter
_command_rate_limiter = CommandRateLimiter()


def acquire_command_slot() -> Tuple[bool, str]:
    """Acquire permission to execute a command."""
    return _command_rate_limiter.acquire()


def release_command_slot() -> None:
    """Release a command slot after execution."""
    _command_rate_limiter.release()

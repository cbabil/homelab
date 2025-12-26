"""
Rate Limiter

Simple in-memory rate limiting for auth endpoints.
"""

import time
from collections import defaultdict
from typing import Dict, List
import structlog

logger = structlog.get_logger("rate_limiter")


class RateLimiter:
    """In-memory rate limiter with sliding window."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed for given key.

        Args:
            key: Identifier (e.g., IP address, user ID)

        Returns:
            True if request is allowed, False if rate limited
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        self.requests[key] = [
            ts for ts in self.requests[key]
            if ts > window_start
        ]

        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            logger.warning("Rate limit exceeded", key=key)
            return False

        # Record request
        self.requests[key].append(now)
        return True

    def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        self.requests[key] = []

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key."""
        now = time.time()
        window_start = now - self.window_seconds

        current = len([
            ts for ts in self.requests[key]
            if ts > window_start
        ])

        return max(0, self.max_requests - current)

"""Message replay protection.

Provides protection against replay attacks using nonces and timestamps.
"""

import secrets
import time
from typing import Dict, Set, Tuple


class ReplayProtection:
    """Provides replay attack protection for messages."""

    # Time window for accepting messages (5 minutes)
    FRESHNESS_WINDOW_SECONDS = 300
    # Maximum nonces to remember (prevent memory exhaustion)
    MAX_NONCES = 10000
    # Clock skew tolerance (allow messages this many seconds in future)
    CLOCK_SKEW_TOLERANCE_SECONDS = 30

    def __init__(self) -> None:
        """Initialize replay protection."""
        self._seen_nonces: Set[str] = set()
        self._nonce_timestamps: Dict[str, float] = {}

    def generate_nonce(self) -> str:
        """Generate a new nonce for a message."""
        return secrets.token_hex(16)

    def validate_message(
        self, timestamp: float, nonce: str, max_age: float | None = None
    ) -> Tuple[bool, str]:
        """Validate a message is fresh and not replayed.

        Args:
            timestamp: Message timestamp (Unix epoch).
            nonce: Unique message nonce.
            max_age: Maximum age in seconds (default: FRESHNESS_WINDOW_SECONDS).

        Returns:
            Tuple of (is_valid, error_message).
        """
        max_age = max_age or self.FRESHNESS_WINDOW_SECONDS
        now = time.time()

        # Check timestamp freshness
        age = now - timestamp
        if age > max_age:
            return (False, f"Message too old: {age:.1f}s > {max_age}s")

        if age < -self.CLOCK_SKEW_TOLERANCE_SECONDS:
            return (False, "Message timestamp in future")

        # Check for replay
        if nonce in self._seen_nonces:
            return (False, "Duplicate nonce - possible replay attack")

        # Add nonce to seen set
        self._seen_nonces.add(nonce)
        self._nonce_timestamps[nonce] = now

        # Cleanup old nonces
        self._cleanup_old_nonces()

        return (True, "")

    def _cleanup_old_nonces(self) -> None:
        """Remove expired nonces to prevent memory growth."""
        if len(self._seen_nonces) < self.MAX_NONCES // 2:
            return

        now = time.time()
        expired = [
            nonce
            for nonce, ts in self._nonce_timestamps.items()
            if now - ts > self.FRESHNESS_WINDOW_SECONDS * 2
        ]

        for nonce in expired:
            self._seen_nonces.discard(nonce)
            self._nonce_timestamps.pop(nonce, None)


# Global replay protection instance
_replay_protection = ReplayProtection()


def validate_message_freshness(timestamp: float, nonce: str) -> Tuple[bool, str]:
    """Validate a message is fresh and not replayed."""
    return _replay_protection.validate_message(timestamp, nonce)


def generate_nonce() -> str:
    """Generate a nonce for outgoing messages."""
    return _replay_protection.generate_nonce()

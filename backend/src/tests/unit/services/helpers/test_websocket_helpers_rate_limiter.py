"""
Unit tests for ConnectionRateLimiter in services/helpers/websocket_helpers.py

Tests rate limiting functionality for WebSocket agent connections.
"""

import time
import pytest
from unittest.mock import patch

from services.helpers.websocket_helpers import (
    ConnectionRateLimiter,
    RateLimitEntry,
    ws_rate_limiter,
)


class TestRateLimitEntry:
    """Tests for RateLimitEntry dataclass."""

    def test_default_values(self):
        """RateLimitEntry should have correct default values."""
        entry = RateLimitEntry()
        assert entry.attempts == 0
        assert entry.first_attempt == 0.0
        assert entry.last_attempt == 0.0
        assert entry.blocked_until == 0.0

    def test_custom_values(self):
        """RateLimitEntry should accept custom values."""
        entry = RateLimitEntry(
            attempts=5, first_attempt=100.0, last_attempt=150.0, blocked_until=200.0
        )
        assert entry.attempts == 5
        assert entry.first_attempt == 100.0
        assert entry.last_attempt == 150.0
        assert entry.blocked_until == 200.0


class TestConnectionRateLimiterInit:
    """Tests for ConnectionRateLimiter initialization."""

    def test_default_values(self):
        """ConnectionRateLimiter should use correct default values."""
        limiter = ConnectionRateLimiter()
        assert limiter._max_attempts == 5
        assert limiter._window_seconds == 60.0
        assert limiter._base_block_seconds == 30.0
        assert limiter._max_block_seconds == 3600.0

    def test_custom_values(self):
        """ConnectionRateLimiter should accept custom values."""
        limiter = ConnectionRateLimiter(
            max_attempts=10,
            window_seconds=120.0,
            base_block_seconds=60.0,
            max_block_seconds=7200.0,
        )
        assert limiter._max_attempts == 10
        assert limiter._window_seconds == 120.0
        assert limiter._base_block_seconds == 60.0
        assert limiter._max_block_seconds == 7200.0

    def test_empty_clients_dict(self):
        """ConnectionRateLimiter should start with empty clients dict."""
        limiter = ConnectionRateLimiter()
        assert len(limiter._clients) == 0
        assert len(limiter._failure_counts) == 0


class TestConnectionRateLimiterIsAllowed:
    """Tests for ConnectionRateLimiter.is_allowed method."""

    def test_new_client_allowed(self):
        """is_allowed should return True for new client."""
        limiter = ConnectionRateLimiter()
        assert limiter.is_allowed("192.168.1.1") is True

    def test_blocked_client_not_allowed(self):
        """is_allowed should return False for blocked client."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"
        # Manually block the client
        limiter._clients[client_ip].blocked_until = time.time() + 100

        with patch("services.helpers.websocket_helpers.logger"):
            assert limiter.is_allowed(client_ip) is False

    def test_block_expired_allowed(self):
        """is_allowed should return True when block has expired."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"
        # Set block that has expired
        limiter._clients[client_ip].blocked_until = time.time() - 10
        limiter._clients[client_ip].first_attempt = time.time()

        assert limiter.is_allowed(client_ip) is True

    def test_window_reset(self):
        """is_allowed should reset attempts when window expires."""
        limiter = ConnectionRateLimiter(window_seconds=60.0)
        client_ip = "192.168.1.1"

        # Set up attempts from old window
        limiter._clients[client_ip].attempts = 4
        limiter._clients[client_ip].first_attempt = time.time() - 120  # 2 minutes ago

        result = limiter.is_allowed(client_ip)

        assert result is True
        assert limiter._clients[client_ip].attempts == 0

    def test_max_attempts_exceeded(self):
        """is_allowed should block client when max attempts exceeded."""
        limiter = ConnectionRateLimiter(max_attempts=5, base_block_seconds=30.0)
        client_ip = "192.168.1.1"

        limiter._clients[client_ip].attempts = 5
        limiter._clients[client_ip].first_attempt = time.time()

        with patch("services.helpers.websocket_helpers.logger"):
            result = limiter.is_allowed(client_ip)

        assert result is False
        assert limiter._clients[client_ip].blocked_until > time.time()

    def test_exponential_backoff(self):
        """is_allowed should apply exponential backoff on repeated failures."""
        limiter = ConnectionRateLimiter(
            max_attempts=5, base_block_seconds=30.0, max_block_seconds=3600.0
        )
        client_ip = "192.168.1.1"

        # First block: 30 seconds
        limiter._clients[client_ip].attempts = 5
        limiter._clients[client_ip].first_attempt = time.time()

        with patch("services.helpers.websocket_helpers.logger"):
            limiter.is_allowed(client_ip)

        assert limiter._failure_counts[client_ip] == 1

        # Reset for second violation
        limiter._clients[client_ip].blocked_until = 0
        limiter._clients[client_ip].attempts = 5
        limiter._clients[client_ip].first_attempt = time.time()

        with patch("services.helpers.websocket_helpers.logger"):
            limiter.is_allowed(client_ip)

        assert limiter._failure_counts[client_ip] == 2

    def test_max_block_duration_cap(self):
        """is_allowed should cap block duration at max_block_seconds."""
        limiter = ConnectionRateLimiter(
            max_attempts=5, base_block_seconds=1000.0, max_block_seconds=100.0
        )
        client_ip = "192.168.1.1"

        limiter._failure_counts[client_ip] = 10  # Would be 1000 * 2^10 without cap
        limiter._clients[client_ip].attempts = 5
        limiter._clients[client_ip].first_attempt = time.time()

        now = time.time()
        with patch("services.helpers.websocket_helpers.logger"):
            limiter.is_allowed(client_ip)

        # Block should be capped at ~100 seconds (allow small timing tolerance)
        block_duration = limiter._clients[client_ip].blocked_until - now
        assert block_duration <= 100.1

    def test_logs_warning_when_blocked(self):
        """is_allowed should log warning when client is blocked."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"
        limiter._clients[client_ip].blocked_until = time.time() + 100

        with patch("services.helpers.websocket_helpers.logger") as mock_logger:
            limiter.is_allowed(client_ip)
            mock_logger.warning.assert_called()

    def test_logs_warning_when_rate_limited(self):
        """is_allowed should log warning when client is rate limited."""
        limiter = ConnectionRateLimiter(max_attempts=5)
        client_ip = "192.168.1.1"
        limiter._clients[client_ip].attempts = 5
        limiter._clients[client_ip].first_attempt = time.time()

        with patch("services.helpers.websocket_helpers.logger") as mock_logger:
            limiter.is_allowed(client_ip)
            mock_logger.warning.assert_called()


class TestConnectionRateLimiterRecordAttempt:
    """Tests for ConnectionRateLimiter.record_attempt method."""

    def test_first_attempt_sets_time(self):
        """record_attempt should set first_attempt on first attempt."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"

        before = time.time()
        limiter.record_attempt(client_ip)
        after = time.time()

        assert before <= limiter._clients[client_ip].first_attempt <= after
        assert limiter._clients[client_ip].attempts == 1

    def test_subsequent_attempt_no_reset(self):
        """record_attempt should not reset first_attempt on subsequent attempts."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"

        initial_time = time.time() - 30
        limiter._clients[client_ip].first_attempt = initial_time

        limiter.record_attempt(client_ip)

        assert limiter._clients[client_ip].first_attempt == initial_time

    def test_increments_attempts(self):
        """record_attempt should increment attempt count."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"

        limiter.record_attempt(client_ip)
        assert limiter._clients[client_ip].attempts == 1

        limiter.record_attempt(client_ip)
        assert limiter._clients[client_ip].attempts == 2

    def test_updates_last_attempt(self):
        """record_attempt should update last_attempt time."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"

        before = time.time()
        limiter.record_attempt(client_ip)
        after = time.time()

        assert before <= limiter._clients[client_ip].last_attempt <= after


class TestConnectionRateLimiterRecordSuccess:
    """Tests for ConnectionRateLimiter.record_success method."""

    def test_clears_failure_count(self):
        """record_success should clear failure count."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"

        limiter._failure_counts[client_ip] = 5

        limiter.record_success(client_ip)

        assert client_ip not in limiter._failure_counts

    def test_clears_client_entry(self):
        """record_success should clear client entry."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"

        limiter._clients[client_ip].attempts = 3
        limiter._clients[client_ip].first_attempt = time.time()

        limiter.record_success(client_ip)

        assert client_ip not in limiter._clients

    def test_handles_unknown_client(self):
        """record_success should handle unknown client gracefully."""
        limiter = ConnectionRateLimiter()
        # Should not raise exception
        limiter.record_success("unknown-ip")


class TestConnectionRateLimiterRecordFailure:
    """Tests for ConnectionRateLimiter.record_failure method."""

    def test_calls_record_attempt(self):
        """record_failure should call record_attempt."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"

        limiter.record_failure(client_ip)

        assert limiter._clients[client_ip].attempts == 1


class TestConnectionRateLimiterCleanupExpired:
    """Tests for ConnectionRateLimiter.cleanup_expired method."""

    def test_removes_expired_entries(self):
        """cleanup_expired should remove expired entries."""
        limiter = ConnectionRateLimiter(window_seconds=60.0)
        client_ip = "192.168.1.1"

        # Set up an expired entry
        limiter._clients[client_ip].blocked_until = time.time() - 10
        limiter._clients[client_ip].last_attempt = time.time() - 200  # Past 2x window
        limiter._failure_counts[client_ip] = 1

        count = limiter.cleanup_expired()

        assert count == 1
        assert client_ip not in limiter._clients
        assert client_ip not in limiter._failure_counts

    def test_keeps_active_entries(self):
        """cleanup_expired should keep active entries."""
        limiter = ConnectionRateLimiter(window_seconds=60.0)
        client_ip = "192.168.1.1"

        # Set up an active entry
        limiter._clients[client_ip].blocked_until = 0
        limiter._clients[client_ip].last_attempt = time.time()  # Recent

        count = limiter.cleanup_expired()

        assert count == 0
        assert client_ip in limiter._clients

    def test_keeps_blocked_entries(self):
        """cleanup_expired should keep currently blocked entries."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"

        # Set up a blocked entry
        limiter._clients[client_ip].blocked_until = time.time() + 100
        limiter._clients[client_ip].last_attempt = time.time() - 200

        count = limiter.cleanup_expired()

        assert count == 0
        assert client_ip in limiter._clients

    def test_returns_cleanup_count(self):
        """cleanup_expired should return count of cleaned entries."""
        limiter = ConnectionRateLimiter(window_seconds=60.0)

        # Add multiple expired entries
        for i in range(3):
            ip = f"192.168.1.{i}"
            limiter._clients[ip].blocked_until = time.time() - 10
            limiter._clients[ip].last_attempt = time.time() - 200

        count = limiter.cleanup_expired()

        assert count == 3


class TestGlobalRateLimiter:
    """Tests for global ws_rate_limiter instance."""

    def test_ws_rate_limiter_exists(self):
        """ws_rate_limiter should be a ConnectionRateLimiter instance."""
        assert isinstance(ws_rate_limiter, ConnectionRateLimiter)

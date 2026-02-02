"""
Unit tests for lib/rate_limiter.py

Tests in-memory rate limiting with sliding window.
"""

import time
import pytest
from unittest.mock import patch

from lib.rate_limiter import RateLimiter


class TestRateLimiterInit:
    """Tests for RateLimiter initialization."""

    def test_init_default_values(self):
        """RateLimiter should have default values."""
        limiter = RateLimiter()
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 60

    def test_init_custom_max_requests(self):
        """RateLimiter should accept custom max_requests."""
        limiter = RateLimiter(max_requests=5)
        assert limiter.max_requests == 5

    def test_init_custom_window_seconds(self):
        """RateLimiter should accept custom window_seconds."""
        limiter = RateLimiter(window_seconds=30)
        assert limiter.window_seconds == 30

    def test_init_custom_both_params(self):
        """RateLimiter should accept both custom params."""
        limiter = RateLimiter(max_requests=20, window_seconds=120)
        assert limiter.max_requests == 20
        assert limiter.window_seconds == 120

    def test_init_requests_empty(self):
        """RateLimiter should start with empty requests dict."""
        limiter = RateLimiter()
        assert len(limiter.requests) == 0


class TestIsAllowed:
    """Tests for is_allowed method."""

    def test_first_request_allowed(self):
        """First request should always be allowed."""
        limiter = RateLimiter(max_requests=5)
        assert limiter.is_allowed("user1") is True

    def test_requests_within_limit_allowed(self):
        """Requests within limit should be allowed."""
        limiter = RateLimiter(max_requests=5)
        for _ in range(5):
            assert limiter.is_allowed("user1") is True

    def test_request_exceeds_limit_blocked(self):
        """Request exceeding limit should be blocked."""
        limiter = RateLimiter(max_requests=3)
        for _ in range(3):
            limiter.is_allowed("user1")
        assert limiter.is_allowed("user1") is False

    def test_different_keys_independent(self):
        """Different keys should have independent limits."""
        limiter = RateLimiter(max_requests=2)
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        assert limiter.is_allowed("user1") is False
        assert limiter.is_allowed("user2") is True

    def test_old_requests_cleaned(self):
        """Old requests outside window should be cleaned."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        assert limiter.is_allowed("user1") is False

        # Wait for window to pass
        time.sleep(1.1)
        assert limiter.is_allowed("user1") is True

    def test_sliding_window_behavior(self):
        """Sliding window should work correctly."""
        limiter = RateLimiter(max_requests=3, window_seconds=2)

        # Make 3 requests at t=0
        for _ in range(3):
            assert limiter.is_allowed("user1") is True

        # 4th request should be blocked
        assert limiter.is_allowed("user1") is False

        # Wait 1 second (not full window)
        time.sleep(1)
        # Still should be blocked (sliding window)
        assert limiter.is_allowed("user1") is False

        # Wait another 1.1 seconds (total > 2s, window passed for first requests)
        time.sleep(1.1)
        # Now should be allowed
        assert limiter.is_allowed("user1") is True

    def test_records_request_timestamp(self):
        """is_allowed should record request timestamps."""
        limiter = RateLimiter(max_requests=5)
        limiter.is_allowed("user1")
        assert len(limiter.requests["user1"]) == 1

    def test_max_requests_zero(self):
        """max_requests=0 should block all requests."""
        limiter = RateLimiter(max_requests=0)
        assert limiter.is_allowed("user1") is False

    def test_logs_rate_limit_exceeded(self):
        """is_allowed should log when rate limit exceeded."""
        limiter = RateLimiter(max_requests=1)
        limiter.is_allowed("user1")
        with patch("lib.rate_limiter.logger.warning") as mock_warning:
            limiter.is_allowed("user1")
            mock_warning.assert_called_once()


class TestReset:
    """Tests for reset method."""

    def test_reset_clears_requests(self):
        """reset should clear all requests for a key."""
        limiter = RateLimiter(max_requests=3)
        for _ in range(3):
            limiter.is_allowed("user1")
        assert limiter.is_allowed("user1") is False

        limiter.reset("user1")
        assert limiter.is_allowed("user1") is True

    def test_reset_only_affects_specified_key(self):
        """reset should only affect the specified key."""
        limiter = RateLimiter(max_requests=2)
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        limiter.is_allowed("user2")
        limiter.is_allowed("user2")

        limiter.reset("user1")
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user2") is False

    def test_reset_nonexistent_key(self):
        """reset should handle nonexistent key gracefully."""
        limiter = RateLimiter()
        limiter.reset("nonexistent")  # Should not raise
        assert len(limiter.requests["nonexistent"]) == 0


class TestGetRemaining:
    """Tests for get_remaining method."""

    def test_get_remaining_initial(self):
        """get_remaining should return max_requests initially."""
        limiter = RateLimiter(max_requests=10)
        assert limiter.get_remaining("user1") == 10

    def test_get_remaining_after_requests(self):
        """get_remaining should decrease after requests."""
        limiter = RateLimiter(max_requests=5)
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        assert limiter.get_remaining("user1") == 3

    def test_get_remaining_at_limit(self):
        """get_remaining should return 0 at limit."""
        limiter = RateLimiter(max_requests=2)
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        assert limiter.get_remaining("user1") == 0

    def test_get_remaining_excludes_old_requests(self):
        """get_remaining should exclude old requests outside window."""
        limiter = RateLimiter(max_requests=3, window_seconds=1)
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        assert limiter.get_remaining("user1") == 1

        time.sleep(1.1)
        assert limiter.get_remaining("user1") == 3

    def test_get_remaining_never_negative(self):
        """get_remaining should never return negative values."""
        limiter = RateLimiter(max_requests=1)
        # Manually add more requests than limit
        limiter.requests["user1"] = [time.time() for _ in range(5)]
        assert limiter.get_remaining("user1") == 0

    def test_get_remaining_different_keys(self):
        """get_remaining should be independent for different keys."""
        limiter = RateLimiter(max_requests=5)
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        limiter.is_allowed("user2")

        assert limiter.get_remaining("user1") == 3
        assert limiter.get_remaining("user2") == 4


class TestIntegration:
    """Integration tests for RateLimiter."""

    def test_auth_rate_limiting_scenario(self):
        """Test realistic auth rate limiting scenario."""
        # 5 login attempts per 10 seconds
        limiter = RateLimiter(max_requests=5, window_seconds=10)

        # Simulate failed login attempts
        for attempt in range(5):
            allowed = limiter.is_allowed("192.168.1.100")
            assert allowed is True

        # 6th attempt should be blocked
        assert limiter.is_allowed("192.168.1.100") is False
        assert limiter.get_remaining("192.168.1.100") == 0

    def test_multiple_users_scenario(self):
        """Test with multiple users."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        users = ["user1", "user2", "user3"]

        for user in users:
            for _ in range(3):
                assert limiter.is_allowed(user) is True
            assert limiter.is_allowed(user) is False

    def test_reset_after_blocking(self):
        """Test reset after user is blocked."""
        limiter = RateLimiter(max_requests=3)
        ip = "10.0.0.1"

        for _ in range(3):
            limiter.is_allowed(ip)
        assert limiter.is_allowed(ip) is False

        # Admin resets the rate limit
        limiter.reset(ip)

        # User can now make requests again
        assert limiter.is_allowed(ip) is True
        assert limiter.get_remaining(ip) == 2

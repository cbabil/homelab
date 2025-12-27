"""Tests for security utilities."""
import pytest
import time
from lib.security import (
    validate_server_input,
    validate_app_config,
    constant_time_compare,
    sanitize_log_message
)
from lib.rate_limiter import RateLimiter


class TestInputValidation:
    """Tests for input validation."""

    def test_validate_server_hostname_valid(self):
        """Should accept valid hostname."""
        result = validate_server_input(host="server.example.com", port=22)
        assert result["valid"] is True

    def test_validate_server_hostname_invalid(self):
        """Should reject invalid hostname with shell chars."""
        result = validate_server_input(host="server;rm -rf /", port=22)
        assert result["valid"] is False
        assert "invalid" in result["error"].lower()

    def test_validate_server_ip_valid(self):
        """Should accept valid IP address."""
        result = validate_server_input(host="192.168.1.100", port=22)
        assert result["valid"] is True

    def test_validate_server_port_range(self):
        """Should reject invalid port numbers."""
        result = validate_server_input(host="server.local", port=99999)
        assert result["valid"] is False

    def test_validate_app_config_safe(self):
        """Should accept safe app config."""
        config = {"env": {"DB_HOST": "localhost"}, "ports": {"80": 8080}}
        result = validate_app_config(config)
        assert result["valid"] is True

    def test_validate_app_config_dangerous_env(self):
        """Should reject dangerous environment values."""
        config = {"env": {"CMD": "$(rm -rf /)"}}
        result = validate_app_config(config)
        assert result["valid"] is False


class TestConstantTimeCompare:
    """Tests for constant-time comparison."""

    def test_constant_time_compare_equal(self):
        """Should return True for equal strings."""
        assert constant_time_compare("password123", "password123") is True

    def test_constant_time_compare_not_equal(self):
        """Should return False for different strings."""
        assert constant_time_compare("password123", "password456") is False

    def test_constant_time_compare_timing(self):
        """Should take similar time regardless of input."""
        # This is a basic timing check
        start = time.perf_counter()
        constant_time_compare("a" * 1000, "b" * 1000)
        time1 = time.perf_counter() - start

        start = time.perf_counter()
        constant_time_compare("a" * 1000, "a" * 999 + "b")
        time2 = time.perf_counter() - start

        # Times should be within 10x of each other (loose bound for test stability)
        assert time1 < time2 * 10 and time2 < time1 * 10


class TestRateLimiter:
    """Tests for rate limiting."""

    def test_rate_limiter_allows_initial(self):
        """Should allow initial requests."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        assert limiter.is_allowed("user1") is True

    def test_rate_limiter_blocks_excess(self):
        """Should block after exceeding limit."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is False

    def test_rate_limiter_per_key(self):
        """Should track limits per key."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is False
        assert limiter.is_allowed("user2") is True  # Different key


class TestLogSanitization:
    """Tests for log sanitization."""

    def test_sanitize_removes_password(self):
        """Should mask password in log messages."""
        msg = "Login attempt with password=secret123"
        sanitized = sanitize_log_message(msg)
        assert "secret123" not in sanitized
        assert "***" in sanitized

    def test_sanitize_removes_token(self):
        """Should mask tokens in log messages."""
        msg = "Auth token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz"
        sanitized = sanitize_log_message(msg)
        assert "eyJ" not in sanitized

"""Tests for security utilities."""

import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock
from lib.security import (
    validate_server_input,
    validate_app_config,
    constant_time_compare,
    sanitize_log_message,
    validate_username,
    validate_password_strength,
    validate_password_length_policy,
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

    def test_rate_limiter_reset(self):
        """Should reset rate limit for a key."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is False

        limiter.reset("user1")
        assert limiter.is_allowed("user1") is True  # Allowed again

    def test_rate_limiter_get_remaining(self):
        """Should return correct remaining count."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        assert limiter.get_remaining("user1") == 5

        limiter.is_allowed("user1")
        assert limiter.get_remaining("user1") == 4

        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        assert limiter.get_remaining("user1") == 2

    def test_rate_limiter_get_remaining_at_limit(self):
        """Should return 0 when at limit."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")

        assert limiter.get_remaining("user1") == 0


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


class TestValidateServerInputEdgeCases:
    """Additional edge case tests for server input validation."""

    def test_validate_server_empty_host(self):
        """Should reject empty host."""
        result = validate_server_input(host="", port=22)
        assert result["valid"] is False
        assert "Host is required" in result["error"]

    def test_validate_server_invalid_hostname_format(self):
        """Should reject invalid hostname format."""
        result = validate_server_input(host="-invalid", port=22)
        assert result["valid"] is False
        assert "Invalid hostname format" in result["error"]

    def test_validate_server_path_traversal(self):
        """Should reject path traversal in hostname."""
        result = validate_server_input(host="server/../etc", port=22)
        assert result["valid"] is False

    def test_validate_server_port_zero(self):
        """Should reject port 0."""
        result = validate_server_input(host="server.local", port=0)
        assert result["valid"] is False

    def test_validate_server_port_negative(self):
        """Should reject negative port."""
        result = validate_server_input(host="server.local", port=-1)
        assert result["valid"] is False


class TestValidateAppConfigEdgeCases:
    """Additional edge case tests for app config validation."""

    def test_validate_app_config_invalid_env_var_type(self):
        """Should reject non-string env var types."""
        config = {"env": {123: "value"}}
        result = validate_app_config(config)
        assert result["valid"] is False
        assert "Invalid env var type" in result["error"]

    def test_validate_app_config_invalid_port_value(self):
        """Should reject invalid port values."""
        config = {"ports": {"80": 99999}}
        result = validate_app_config(config)
        assert result["valid"] is False
        assert "Invalid port mapping" in result["error"]

    def test_validate_app_config_non_numeric_port(self):
        """Should reject non-numeric port format."""
        config = {"ports": {"abc": "def"}}
        result = validate_app_config(config)
        assert result["valid"] is False
        assert "Invalid port format" in result["error"]

    def test_validate_app_config_empty(self):
        """Should accept empty config."""
        result = validate_app_config({})
        assert result["valid"] is True


class TestValidateUsername:
    """Tests for username validation."""

    def test_validate_username_valid(self):
        """Should accept valid username."""
        result = validate_username("john_doe")
        assert result["valid"] is True

    def test_validate_username_empty(self):
        """Should reject empty username."""
        result = validate_username("")
        assert result["valid"] is False
        assert "required" in result["error"]

    def test_validate_username_too_short(self):
        """Should reject username shorter than 3 chars."""
        result = validate_username("ab")
        assert result["valid"] is False
        assert "3-32 characters" in result["error"]

    def test_validate_username_too_long(self):
        """Should reject username longer than 32 chars."""
        result = validate_username("a" * 33)
        assert result["valid"] is False
        assert "3-32 characters" in result["error"]

    def test_validate_username_starts_with_number(self):
        """Should reject username starting with number."""
        result = validate_username("1user")
        assert result["valid"] is False
        assert "start with letter" in result["error"]

    def test_validate_username_invalid_chars(self):
        """Should reject username with invalid characters."""
        result = validate_username("user@name")
        assert result["valid"] is False

    def test_validate_username_with_hyphen(self):
        """Should accept username with hyphen."""
        result = validate_username("john-doe")
        assert result["valid"] is True


class TestValidatePasswordStrength:
    """Tests for legacy password strength validation."""

    def test_validate_password_strength_valid(self):
        """Should accept strong password."""
        result = validate_password_strength("Str0ngP@ss")
        assert result["valid"] is True

    def test_validate_password_strength_too_short(self):
        """Should reject password shorter than 8 chars."""
        result = validate_password_strength("Abc1!")
        assert result["valid"] is False
        assert any("8 characters" in e for e in result["errors"])

    def test_validate_password_strength_no_uppercase(self):
        """Should reject password without uppercase."""
        result = validate_password_strength("password123")
        assert result["valid"] is False
        assert any("uppercase" in e for e in result["errors"])

    def test_validate_password_strength_no_lowercase(self):
        """Should reject password without lowercase."""
        result = validate_password_strength("PASSWORD123")
        assert result["valid"] is False
        assert any("lowercase" in e for e in result["errors"])

    def test_validate_password_strength_no_digit(self):
        """Should reject password without digit."""
        result = validate_password_strength("Passworddd")
        assert result["valid"] is False
        assert any("digit" in e for e in result["errors"])


class TestValidatePasswordLengthPolicy:
    """Tests for NIST-compliant password validation."""

    @pytest.fixture
    def mock_blocklist_service(self):
        """Create mock blocklist service."""
        service = MagicMock()
        service.validate_password = AsyncMock(
            return_value={"valid": True, "errors": [], "warnings": [], "checks": {}}
        )
        return service

    @pytest.mark.asyncio
    async def test_length_policy_mode_valid(self, mock_blocklist_service):
        """Should accept long password in length policy mode."""
        with patch(
            "services.password_blocklist_service.get_blocklist_service",
            return_value=mock_blocklist_service,
        ):
            result = await validate_password_length_policy(
                password="thisisaverylongpassword123",
                length_policy_mode=True,
                min_length=15,
            )
            assert result["valid"] is True
            assert result["mode"] == "length_policy"

    @pytest.mark.asyncio
    async def test_length_policy_mode_too_short(self):
        """Should reject short password in length policy mode."""
        result = await validate_password_length_policy(
            password="short",
            length_policy_mode=True,
            min_length=15,
            check_blocklist=False,
        )
        assert result["valid"] is False
        assert any("15 characters" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_length_policy_mode_too_long(self):
        """Should reject password exceeding max length."""
        result = await validate_password_length_policy(
            password="a" * 200,
            length_policy_mode=True,
            max_length=128,
            check_blocklist=False,
        )
        assert result["valid"] is False
        assert any("128 characters" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_legacy_mode_valid(self, mock_blocklist_service):
        """Should accept password meeting legacy requirements."""
        with patch(
            "services.password_blocklist_service.get_blocklist_service",
            return_value=mock_blocklist_service,
        ):
            result = await validate_password_length_policy(
                password="Str0ng!Pass",
                length_policy_mode=False,
                min_length=8,
            )
            assert result["valid"] is True
            assert result["mode"] == "legacy"

    @pytest.mark.asyncio
    async def test_legacy_mode_no_uppercase(self):
        """Should reject password without uppercase in legacy mode."""
        result = await validate_password_length_policy(
            password="lowercase123!",
            length_policy_mode=False,
            min_length=8,
            check_blocklist=False,
            require_uppercase=True,
        )
        assert result["valid"] is False
        assert result["checks"]["has_uppercase"] is False

    @pytest.mark.asyncio
    async def test_legacy_mode_no_lowercase(self):
        """Should reject password without lowercase in legacy mode."""
        result = await validate_password_length_policy(
            password="UPPERCASE123!",
            length_policy_mode=False,
            min_length=8,
            check_blocklist=False,
            require_lowercase=True,
        )
        assert result["valid"] is False
        assert result["checks"]["has_lowercase"] is False

    @pytest.mark.asyncio
    async def test_legacy_mode_no_number(self):
        """Should reject password without number in legacy mode."""
        result = await validate_password_length_policy(
            password="NoNumbers!Here",
            length_policy_mode=False,
            min_length=8,
            check_blocklist=False,
            require_numbers=True,
        )
        assert result["valid"] is False
        assert result["checks"]["has_number"] is False

    @pytest.mark.asyncio
    async def test_legacy_mode_no_special(self):
        """Should reject password without special char in legacy mode."""
        result = await validate_password_length_policy(
            password="NoSpecial123",
            length_policy_mode=False,
            min_length=8,
            check_blocklist=False,
            require_special=True,
        )
        assert result["valid"] is False
        assert result["checks"]["has_special"] is False

    @pytest.mark.asyncio
    async def test_blocklist_check_in_length_policy_mode(self, mock_blocklist_service):
        """Should check blocklist in length policy mode."""
        mock_blocklist_service.validate_password.return_value = {
            "valid": False,
            "errors": ["Password is too common"],
            "warnings": [],
            "checks": {"blocklist": False},
        }
        with patch(
            "services.password_blocklist_service.get_blocklist_service",
            return_value=mock_blocklist_service,
        ):
            result = await validate_password_length_policy(
                password="thisisaverylongpassword123",
                length_policy_mode=True,
                check_blocklist=True,
            )
            assert "Password is too common" in result["errors"]

    @pytest.mark.asyncio
    async def test_blocklist_check_in_legacy_mode(self, mock_blocklist_service):
        """Should add blocklist errors as warnings in legacy mode."""
        mock_blocklist_service.validate_password.return_value = {
            "valid": False,
            "errors": ["Password found in breach"],
            "warnings": [],
            "checks": {"hibp": False},
        }
        with patch(
            "services.password_blocklist_service.get_blocklist_service",
            return_value=mock_blocklist_service,
        ):
            result = await validate_password_length_policy(
                password="Str0ng!Pass",
                length_policy_mode=False,
                min_length=8,
                check_blocklist=True,
            )
            # In legacy mode, blocklist errors become warnings
            assert "Password found in breach" in result["warnings"]

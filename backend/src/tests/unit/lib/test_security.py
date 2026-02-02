"""
Unit tests for lib/security.py

Tests input validation, constant-time operations, log sanitization,
and NIST SP 800-63B-4 compliant password validation.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from lib.security import (
    DANGEROUS_PATTERNS,
    SENSITIVE_PATTERNS,
    validate_server_input,
    validate_app_config,
    constant_time_compare,
    sanitize_log_message,
    validate_username,
    validate_password_strength,
    validate_password_length_policy,
)


class TestConstants:
    """Tests for security constants."""

    def test_dangerous_patterns_defined(self):
        """DANGEROUS_PATTERNS should be defined."""
        assert isinstance(DANGEROUS_PATTERNS, list)
        assert len(DANGEROUS_PATTERNS) > 0

    def test_dangerous_patterns_has_shell_metacharacters(self):
        """DANGEROUS_PATTERNS should include shell metacharacters."""
        assert any(";" in p or "|" in p for p in DANGEROUS_PATTERNS)

    def test_dangerous_patterns_has_path_traversal(self):
        """DANGEROUS_PATTERNS should include path traversal."""
        # Pattern is regex r'\.\.' which matches '..'
        assert any("\\." in p for p in DANGEROUS_PATTERNS)

    def test_sensitive_patterns_defined(self):
        """SENSITIVE_PATTERNS should be defined."""
        assert isinstance(SENSITIVE_PATTERNS, list)
        assert len(SENSITIVE_PATTERNS) > 0


class TestValidateServerInput:
    """Tests for validate_server_input function."""

    def test_valid_hostname(self):
        """Should accept valid hostname."""
        result = validate_server_input(host="server.example.com", port=22)
        assert result["valid"] is True

    def test_valid_simple_hostname(self):
        """Should accept simple hostname without domain."""
        result = validate_server_input(host="myserver", port=22)
        assert result["valid"] is True

    def test_valid_ipv4(self):
        """Should accept valid IPv4 address."""
        result = validate_server_input(host="192.168.1.100", port=22)
        assert result["valid"] is True

    def test_valid_ipv6(self):
        """Should accept valid IPv6 address."""
        result = validate_server_input(host="::1", port=22)
        assert result["valid"] is True

    def test_empty_host(self):
        """Should reject empty host."""
        result = validate_server_input(host="", port=22)
        assert result["valid"] is False
        assert "required" in result["error"].lower()

    def test_host_with_shell_chars(self):
        """Should reject host with shell metacharacters."""
        result = validate_server_input(host="server;rm -rf /", port=22)
        assert result["valid"] is False
        assert "invalid" in result["error"].lower()

    def test_host_with_pipe(self):
        """Should reject host with pipe character."""
        result = validate_server_input(host="server|cat /etc/passwd", port=22)
        assert result["valid"] is False

    def test_host_with_command_substitution(self):
        """Should reject host with command substitution."""
        result = validate_server_input(host="$(whoami)", port=22)
        assert result["valid"] is False

    def test_host_with_backticks(self):
        """Should reject host with backticks."""
        result = validate_server_input(host="`whoami`", port=22)
        assert result["valid"] is False

    def test_host_path_traversal(self):
        """Should reject host with path traversal."""
        result = validate_server_input(host="../../../etc/passwd", port=22)
        assert result["valid"] is False

    def test_port_valid_min(self):
        """Should accept minimum valid port."""
        result = validate_server_input(host="server.local", port=1)
        assert result["valid"] is True

    def test_port_valid_max(self):
        """Should accept maximum valid port."""
        result = validate_server_input(host="server.local", port=65535)
        assert result["valid"] is True

    def test_port_too_low(self):
        """Should reject port below 1."""
        result = validate_server_input(host="server.local", port=0)
        assert result["valid"] is False
        assert "port" in result["error"].lower()

    def test_port_too_high(self):
        """Should reject port above 65535."""
        result = validate_server_input(host="server.local", port=65536)
        assert result["valid"] is False

    def test_multiple_errors(self):
        """Should report multiple errors."""
        result = validate_server_input(host="", port=0)
        assert result["valid"] is False
        # Multiple errors joined by semicolon
        assert ";" in result["error"]

    def test_invalid_hostname_format(self):
        """Should reject hostname with invalid format."""
        # Hostname starting with hyphen - passes dangerous char check but fails pattern
        result = validate_server_input(host="-invalid-hostname", port=22)
        assert result["valid"] is False
        assert "hostname" in result["error"].lower()


class TestValidateAppConfig:
    """Tests for validate_app_config function."""

    def test_valid_config(self):
        """Should accept valid app config."""
        config = {
            "env": {"DB_HOST": "localhost", "DB_PORT": "5432"},
            "ports": {"80": 8080, "443": 8443}
        }
        result = validate_app_config(config)
        assert result["valid"] is True

    def test_empty_config(self):
        """Should accept empty config."""
        result = validate_app_config({})
        assert result["valid"] is True

    def test_config_no_env_or_ports(self):
        """Should accept config without env or ports."""
        result = validate_app_config({"name": "myapp"})
        assert result["valid"] is True

    def test_dangerous_env_value(self):
        """Should reject dangerous env value."""
        config = {"env": {"CMD": "$(rm -rf /)"}}
        result = validate_app_config(config)
        assert result["valid"] is False
        assert "dangerous" in result["error"].lower()

    def test_env_with_semicolon(self):
        """Should reject env value with semicolon."""
        config = {"env": {"CMD": "ls; rm -rf /"}}
        result = validate_app_config(config)
        assert result["valid"] is False

    def test_invalid_env_type(self):
        """Should reject non-string env value."""
        config = {"env": {"PORT": 8080}}  # int instead of string
        result = validate_app_config(config)
        assert result["valid"] is False
        assert "type" in result["error"].lower()

    def test_valid_port_mapping(self):
        """Should accept valid port mapping."""
        config = {"ports": {"80": 8080}}
        result = validate_app_config(config)
        assert result["valid"] is True

    def test_invalid_port_mapping_too_high(self):
        """Should reject port mapping above 65535."""
        config = {"ports": {"80": 99999}}
        result = validate_app_config(config)
        assert result["valid"] is False
        assert "port" in result["error"].lower()

    def test_invalid_port_format(self):
        """Should reject invalid port format."""
        config = {"ports": {"abc": "def"}}
        result = validate_app_config(config)
        assert result["valid"] is False


class TestConstantTimeCompare:
    """Tests for constant_time_compare function."""

    def test_equal_strings(self):
        """Should return True for equal strings."""
        assert constant_time_compare("password123", "password123") is True

    def test_not_equal_strings(self):
        """Should return False for different strings."""
        assert constant_time_compare("password123", "password456") is False

    def test_empty_strings(self):
        """Should handle empty strings."""
        assert constant_time_compare("", "") is True
        assert constant_time_compare("", "a") is False

    def test_different_lengths(self):
        """Should handle strings of different lengths."""
        assert constant_time_compare("short", "longer_string") is False

    def test_unicode_strings(self):
        """Should handle unicode strings."""
        assert constant_time_compare("пароль", "пароль") is True
        assert constant_time_compare("пароль", "password") is False


class TestSanitizeLogMessage:
    """Tests for sanitize_log_message function."""

    def test_sanitize_password(self):
        """Should mask password in log message."""
        msg = "Login with password=secret123"
        result = sanitize_log_message(msg)
        assert "secret123" not in result
        assert "password=***" in result

    def test_sanitize_token(self):
        """Should mask token in log message."""
        msg = "Using token: abc123xyz"
        result = sanitize_log_message(msg)
        assert "abc123xyz" not in result.lower() or "token=***" in result

    def test_sanitize_jwt(self):
        """Should mask JWT in log message."""
        msg = "Auth: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature"
        result = sanitize_log_message(msg)
        assert "eyJ" not in result
        assert "***JWT***" in result

    def test_sanitize_key(self):
        """Should mask key in log message."""
        msg = "API key=secret_api_key_here"
        result = sanitize_log_message(msg)
        assert "secret_api_key" not in result

    def test_sanitize_secret(self):
        """Should mask secret in log message."""
        msg = "Using secret: my_secret_value"
        result = sanitize_log_message(msg)
        assert "my_secret_value" not in result

    def test_sanitize_case_insensitive(self):
        """Should be case insensitive."""
        msg = "PASSWORD=SECRET"
        result = sanitize_log_message(msg)
        assert "SECRET" not in result

    def test_sanitize_preserves_safe_content(self):
        """Should preserve non-sensitive content."""
        msg = "User john logged in from 192.168.1.1"
        result = sanitize_log_message(msg)
        assert result == msg

    def test_sanitize_multiple_patterns(self):
        """Should sanitize multiple sensitive patterns."""
        msg = "password=pass1 and token=tok1"
        result = sanitize_log_message(msg)
        assert "pass1" not in result
        assert "tok1" not in result


class TestValidateUsername:
    """Tests for validate_username function."""

    def test_valid_username(self):
        """Should accept valid username."""
        result = validate_username("john_doe")
        assert result["valid"] is True

    def test_username_with_hyphen(self):
        """Should accept username with hyphen."""
        result = validate_username("john-doe")
        assert result["valid"] is True

    def test_username_with_numbers(self):
        """Should accept username with numbers."""
        result = validate_username("john123")
        assert result["valid"] is True

    def test_empty_username(self):
        """Should reject empty username."""
        result = validate_username("")
        assert result["valid"] is False
        assert "required" in result["error"].lower()

    def test_username_too_short(self):
        """Should reject username shorter than 3 chars."""
        result = validate_username("ab")
        assert result["valid"] is False
        assert "3-32" in result["error"]

    def test_username_too_long(self):
        """Should reject username longer than 32 chars."""
        result = validate_username("a" * 33)
        assert result["valid"] is False
        assert "3-32" in result["error"]

    def test_username_starts_with_number(self):
        """Should reject username starting with number."""
        result = validate_username("1john")
        assert result["valid"] is False
        assert "start with letter" in result["error"]

    def test_username_starts_with_underscore(self):
        """Should reject username starting with underscore."""
        result = validate_username("_john")
        assert result["valid"] is False

    def test_username_special_chars(self):
        """Should reject username with special chars."""
        result = validate_username("john@doe")
        assert result["valid"] is False


class TestValidatePasswordStrength:
    """Tests for validate_password_strength function (legacy mode)."""

    def test_valid_password(self):
        """Should accept valid password."""
        result = validate_password_strength("Password123")
        assert result["valid"] is True

    def test_password_too_short(self):
        """Should reject password shorter than 8 chars."""
        result = validate_password_strength("Pass1")
        assert result["valid"] is False
        assert any("8 characters" in e for e in result["errors"])

    def test_password_no_uppercase(self):
        """Should reject password without uppercase."""
        result = validate_password_strength("password123")
        assert result["valid"] is False
        assert any("uppercase" in e.lower() for e in result["errors"])

    def test_password_no_lowercase(self):
        """Should reject password without lowercase."""
        result = validate_password_strength("PASSWORD123")
        assert result["valid"] is False
        assert any("lowercase" in e.lower() for e in result["errors"])

    def test_password_no_digit(self):
        """Should reject password without digit."""
        result = validate_password_strength("PasswordAbc")
        assert result["valid"] is False
        assert any("digit" in e.lower() for e in result["errors"])

    def test_password_multiple_errors(self):
        """Should report multiple errors."""
        result = validate_password_strength("abc")
        assert result["valid"] is False
        assert len(result["errors"]) > 1


class TestValidatePasswordLengthPolicy:
    """Tests for validate_password_length_policy function (async, NIST mode)."""

    @pytest.fixture
    def mock_blocklist_service(self):
        """Mock the blocklist service."""
        mock_service = MagicMock()
        mock_service.validate_password = AsyncMock(return_value={
            "valid": True,
            "errors": [],
            "warnings": [],
            "checks": {"not_common": True, "not_sequential": True}
        })
        return mock_service

    @pytest.mark.asyncio
    async def test_valid_password_length_policy_mode(self, mock_blocklist_service):
        """Should accept valid password in length_policy mode."""
        with patch("services.password_blocklist_service.get_blocklist_service", return_value=mock_blocklist_service):
            result = await validate_password_length_policy(
                password="this_is_a_very_long_secure_password",
                length_policy_mode=True,
                min_length=15
            )
            assert result["valid"] is True
            assert result["mode"] == "length_policy"

    @pytest.mark.asyncio
    async def test_password_too_short_length_policy(self, mock_blocklist_service):
        """Should reject password shorter than min_length."""
        with patch("services.password_blocklist_service.get_blocklist_service", return_value=mock_blocklist_service):
            result = await validate_password_length_policy(
                password="short",
                length_policy_mode=True,
                min_length=15
            )
            assert result["valid"] is False
            assert any("15 characters" in e for e in result["errors"])
            assert result["checks"]["min_length"] is False

    @pytest.mark.asyncio
    async def test_password_too_long(self, mock_blocklist_service):
        """Should reject password longer than max_length."""
        with patch("services.password_blocklist_service.get_blocklist_service", return_value=mock_blocklist_service):
            result = await validate_password_length_policy(
                password="a" * 150,
                max_length=128
            )
            assert result["valid"] is False
            assert any("128 characters" in e for e in result["errors"])
            assert result["checks"]["max_length"] is False

    @pytest.mark.asyncio
    async def test_legacy_mode_requires_uppercase(self, mock_blocklist_service):
        """Should require uppercase in legacy mode."""
        with patch("services.password_blocklist_service.get_blocklist_service", return_value=mock_blocklist_service):
            result = await validate_password_length_policy(
                password="password123!@#abc",
                length_policy_mode=False,
                min_length=8,
                require_uppercase=True
            )
            assert result["valid"] is False
            assert result["mode"] == "legacy"
            assert result["checks"]["has_uppercase"] is False

    @pytest.mark.asyncio
    async def test_legacy_mode_requires_lowercase(self, mock_blocklist_service):
        """Should require lowercase in legacy mode."""
        with patch("services.password_blocklist_service.get_blocklist_service", return_value=mock_blocklist_service):
            result = await validate_password_length_policy(
                password="PASSWORD123!@#",
                length_policy_mode=False,
                min_length=8,
                require_lowercase=True
            )
            assert result["valid"] is False
            assert result["checks"]["has_lowercase"] is False

    @pytest.mark.asyncio
    async def test_legacy_mode_requires_number(self, mock_blocklist_service):
        """Should require number in legacy mode."""
        with patch("services.password_blocklist_service.get_blocklist_service", return_value=mock_blocklist_service):
            result = await validate_password_length_policy(
                password="PasswordABC!@#",
                length_policy_mode=False,
                min_length=8,
                require_numbers=True
            )
            assert result["valid"] is False
            assert result["checks"]["has_number"] is False

    @pytest.mark.asyncio
    async def test_legacy_mode_requires_special(self, mock_blocklist_service):
        """Should require special char in legacy mode."""
        with patch("services.password_blocklist_service.get_blocklist_service", return_value=mock_blocklist_service):
            result = await validate_password_length_policy(
                password="PasswordABC123",
                length_policy_mode=False,
                min_length=8,
                require_special=True
            )
            assert result["valid"] is False
            assert result["checks"]["has_special"] is False

    @pytest.mark.asyncio
    async def test_legacy_mode_valid_password(self, mock_blocklist_service):
        """Should accept valid password in legacy mode."""
        with patch("services.password_blocklist_service.get_blocklist_service", return_value=mock_blocklist_service):
            result = await validate_password_length_policy(
                password="Password123!@#",
                length_policy_mode=False,
                min_length=8
            )
            assert result["valid"] is True
            assert result["mode"] == "legacy"

    @pytest.mark.asyncio
    async def test_blocklist_check_in_length_policy_mode(self):
        """Should check blocklist in length_policy mode."""
        mock_service = MagicMock()
        mock_service.validate_password = AsyncMock(return_value={
            "valid": False,
            "errors": ["Password is too common"],
            "warnings": [],
            "checks": {"not_common": False}
        })
        with patch("services.password_blocklist_service.get_blocklist_service", return_value=mock_service):
            result = await validate_password_length_policy(
                password="a_very_long_password_here",
                length_policy_mode=True,
                check_blocklist=True
            )
            assert result["valid"] is False
            assert "too common" in str(result["errors"]).lower()

    @pytest.mark.asyncio
    async def test_unicode_support(self, mock_blocklist_service):
        """Should support unicode passwords."""
        with patch("services.password_blocklist_service.get_blocklist_service", return_value=mock_blocklist_service):
            result = await validate_password_length_policy(
                password="пароль_is_очень_secure_123",
                length_policy_mode=True,
                min_length=15
            )
            assert result["checks"]["unicode_support"] is True

    @pytest.mark.asyncio
    async def test_no_blocklist_check(self, mock_blocklist_service):
        """Should skip blocklist when check_blocklist=False."""
        with patch("services.password_blocklist_service.get_blocklist_service") as mock_get:
            result = await validate_password_length_policy(
                password="a_very_long_password_here",
                length_policy_mode=True,
                check_blocklist=False
            )
            # Blocklist service should not be called
            mock_get.assert_not_called()
            assert result["valid"] is True

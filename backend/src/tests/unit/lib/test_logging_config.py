"""
Unit tests for lib/logging_config.py

Tests structured logging configuration and sensitive data filtering.
"""

import os
import logging
import pytest
from unittest.mock import patch, MagicMock
import structlog

from lib.logging_config import setup_logging, _filter_sensitive_data


@pytest.fixture
def clean_env():
    """Fixture to save and restore environment variables."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_default_level(self, clean_env):
        """setup_logging should use INFO level by default."""
        os.environ.pop("MCP_LOG_LEVEL", None)
        with patch("logging.basicConfig") as mock_config:
            setup_logging()
            mock_config.assert_called_once()
            call_kwargs = mock_config.call_args[1]
            assert call_kwargs["level"] == logging.INFO

    def test_setup_logging_custom_level_debug(self, clean_env):
        """setup_logging should respect DEBUG log level from env."""
        os.environ["MCP_LOG_LEVEL"] = "DEBUG"
        with patch("logging.basicConfig") as mock_config:
            setup_logging()
            call_kwargs = mock_config.call_args[1]
            assert call_kwargs["level"] == logging.DEBUG

    def test_setup_logging_custom_level_warning(self, clean_env):
        """setup_logging should respect WARNING log level from env."""
        os.environ["MCP_LOG_LEVEL"] = "WARNING"
        with patch("logging.basicConfig") as mock_config:
            setup_logging()
            call_kwargs = mock_config.call_args[1]
            assert call_kwargs["level"] == logging.WARNING

    def test_setup_logging_custom_level_error(self, clean_env):
        """setup_logging should respect ERROR log level from env."""
        os.environ["MCP_LOG_LEVEL"] = "ERROR"
        with patch("logging.basicConfig") as mock_config:
            setup_logging()
            call_kwargs = mock_config.call_args[1]
            assert call_kwargs["level"] == logging.ERROR

    def test_setup_logging_level_case_insensitive(self, clean_env):
        """setup_logging should handle lowercase log level."""
        os.environ["MCP_LOG_LEVEL"] = "debug"
        with patch("logging.basicConfig") as mock_config:
            setup_logging()
            call_kwargs = mock_config.call_args[1]
            assert call_kwargs["level"] == logging.DEBUG

    def test_setup_logging_configures_structlog(self, clean_env):
        """setup_logging should configure structlog."""
        with patch("structlog.configure") as mock_configure:
            setup_logging()
            mock_configure.assert_called_once()


class TestFilterSensitiveData:
    """Tests for _filter_sensitive_data function."""

    def test_filter_password(self):
        """_filter_sensitive_data should redact password."""
        event_dict = {"message": "test", "password": "secret123"}
        result = _filter_sensitive_data(None, "info", event_dict)
        assert result["password"] == "[REDACTED]"
        assert result["message"] == "test"

    def test_filter_private_key(self):
        """_filter_sensitive_data should redact private_key."""
        event_dict = {"message": "test", "private_key": "-----BEGIN RSA-----"}
        result = _filter_sensitive_data(None, "info", event_dict)
        assert result["private_key"] == "[REDACTED]"

    def test_filter_credentials(self):
        """_filter_sensitive_data should redact credentials."""
        event_dict = {"message": "test", "credentials": {"user": "pass"}}
        result = _filter_sensitive_data(None, "info", event_dict)
        assert result["credentials"] == "[REDACTED]"

    def test_filter_token(self):
        """_filter_sensitive_data should redact token."""
        event_dict = {"message": "test", "token": "jwt_token_here"}
        result = _filter_sensitive_data(None, "info", event_dict)
        assert result["token"] == "[REDACTED]"

    def test_filter_multiple_sensitive_keys(self):
        """_filter_sensitive_data should redact multiple sensitive keys."""
        event_dict = {
            "message": "test",
            "password": "pass1",
            "token": "token1",
            "credentials": "creds1"
        }
        result = _filter_sensitive_data(None, "info", event_dict)
        assert result["password"] == "[REDACTED]"
        assert result["token"] == "[REDACTED]"
        assert result["credentials"] == "[REDACTED]"

    def test_filter_preserves_non_sensitive(self):
        """_filter_sensitive_data should preserve non-sensitive data."""
        event_dict = {
            "message": "test message",
            "user_id": "user123",
            "action": "login",
            "timestamp": "2024-01-15"
        }
        result = _filter_sensitive_data(None, "info", event_dict)
        assert result["message"] == "test message"
        assert result["user_id"] == "user123"
        assert result["action"] == "login"
        assert result["timestamp"] == "2024-01-15"

    def test_filter_no_sensitive_data(self):
        """_filter_sensitive_data should handle dict without sensitive data."""
        event_dict = {"message": "safe", "count": 42}
        result = _filter_sensitive_data(None, "info", event_dict)
        assert result == {"message": "safe", "count": 42}

    def test_filter_empty_dict(self):
        """_filter_sensitive_data should handle empty dictionary."""
        event_dict = {}
        result = _filter_sensitive_data(None, "info", event_dict)
        assert result == {}

    def test_filter_returns_event_dict(self):
        """_filter_sensitive_data should return the modified event_dict."""
        event_dict = {"key": "value"}
        result = _filter_sensitive_data(None, "info", event_dict)
        assert result is event_dict

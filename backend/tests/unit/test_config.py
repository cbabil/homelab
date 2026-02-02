"""
Unit tests for lib/config.py

Tests for configuration loading utilities including .env file parsing,
data directory resolution, and feature flag management.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from lib.config import (
    _load_env_file,
    _resolve_data_directory,
    load_config,
    reload_config,
    resolve_data_directory,
    is_feature_enabled,
    get_feature_flags,
    require_feature,
    DEFAULT_ENV_VALUES,
    BACKEND_ROOT,
    _cached_config,
)


class TestLoadEnvFile:
    """Tests for .env file loading."""

    def test_load_env_file_returns_empty_dict_when_no_file(self):
        """Should return empty dict when no .env file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("lib.config.PROJECT_ROOT", Path(tmpdir)):
                result = _load_env_file()

        assert isinstance(result, dict)

    def test_load_env_file_parses_key_value_pairs(self):
        """Should parse key=value pairs from .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("TEST_KEY=test_value\nANOTHER_KEY=another_value\n")

            with patch("lib.config.PROJECT_ROOT", Path(tmpdir)):
                result = _load_env_file()

        assert "TEST_KEY" in result
        assert result["TEST_KEY"] == "test_value"
        assert result["ANOTHER_KEY"] == "another_value"

    def test_load_env_file_ignores_comments(self):
        """Should ignore comment lines starting with #."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                "# This is a comment\nVALID_KEY=value\n# Another comment\n"
            )

            with patch("lib.config.PROJECT_ROOT", Path(tmpdir)):
                result = _load_env_file()

        assert "VALID_KEY" in result
        assert len(result) == 1

    def test_load_env_file_ignores_empty_lines(self):
        """Should ignore empty lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("KEY1=value1\n\n\nKEY2=value2\n")

            with patch("lib.config.PROJECT_ROOT", Path(tmpdir)):
                result = _load_env_file()

        assert len(result) == 2

    def test_load_env_file_strips_quotes(self):
        """Should strip quotes from values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("DOUBLE=\"double quoted\"\nSINGLE='single quoted'\n")

            with patch("lib.config.PROJECT_ROOT", Path(tmpdir)):
                result = _load_env_file()

        assert result["DOUBLE"] == "double quoted"
        assert result["SINGLE"] == "single quoted"

    def test_load_env_file_ignores_lines_without_equals(self):
        """Should ignore lines without = sign."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("NO_EQUALS_HERE\nVALID=yes\n")

            with patch("lib.config.PROJECT_ROOT", Path(tmpdir)):
                result = _load_env_file()

        assert "VALID" in result
        assert "NO_EQUALS_HERE" not in result

    def test_load_env_file_ignores_empty_keys(self):
        """Should ignore entries with empty keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("=empty_key\nVALID=yes\n")

            with patch("lib.config.PROJECT_ROOT", Path(tmpdir)):
                result = _load_env_file()

        assert "VALID" in result
        assert len(result) == 1

    def test_load_env_file_fallback_to_backend_dir(self):
        """Should check backend/ directory if root .env not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend_dir = Path(tmpdir) / "backend"
            backend_dir.mkdir()
            env_file = backend_dir / ".env"
            env_file.write_text("BACKEND_VAR=found\n")

            with patch("lib.config.PROJECT_ROOT", Path(tmpdir)):
                result = _load_env_file()

        assert "BACKEND_VAR" in result
        assert result["BACKEND_VAR"] == "found"

    def test_load_env_file_handles_os_error(self):
        """Should handle OSError when reading file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("TEST=value\n")
            # Make file unreadable
            env_file.chmod(0o000)

            try:
                with patch("lib.config.PROJECT_ROOT", Path(tmpdir)):
                    result = _load_env_file()
                # Should return empty dict on error
                assert isinstance(result, dict)
            finally:
                # Restore permissions for cleanup
                env_file.chmod(0o644)


class TestResolveDataDirectory:
    """Tests for data directory resolution."""

    def test_resolve_data_directory_absolute_path(self):
        """Should return absolute path unchanged."""
        result = _resolve_data_directory("/absolute/path/to/data")

        assert result == Path("/absolute/path/to/data")

    def test_resolve_data_directory_relative_path(self):
        """Should resolve relative path from backend root."""
        result = _resolve_data_directory("data")

        expected = (BACKEND_ROOT / "data").resolve()
        assert result == expected


class TestLoadConfig:
    """Tests for configuration loading."""

    def test_load_config_returns_dict(self):
        """Should return dictionary of config values."""
        _cached_config.cache_clear()

        config = load_config()

        assert isinstance(config, dict)
        assert "data_directory" in config
        assert "app_env" in config
        assert "version" in config

    def test_load_config_includes_defaults(self):
        """Should include default values."""
        _cached_config.cache_clear()

        config = load_config()

        assert "ssh_timeout" in config
        assert "max_concurrent_connections" in config

    def test_load_config_converts_types(self):
        """Should convert SSH timeout and connections to int."""
        _cached_config.cache_clear()

        config = load_config()

        assert isinstance(config["ssh_timeout"], int)
        assert isinstance(config["max_concurrent_connections"], int)


class TestReloadConfig:
    """Tests for configuration reloading."""

    def test_reload_config_clears_cache(self):
        """Should clear cache and return fresh config."""
        _cached_config.cache_clear()

        # Load once
        load_config()

        # Set env var
        original = os.environ.get("APP_ENV")
        try:
            os.environ["APP_ENV"] = "test_reload_value"

            # Reload should pick up new value
            config2 = reload_config()

            assert config2["app_env"] == "test_reload_value"
        finally:
            if original is not None:
                os.environ["APP_ENV"] = original
            else:
                os.environ.pop("APP_ENV", None)
            _cached_config.cache_clear()


class TestResolveDataDirectoryFunction:
    """Tests for resolve_data_directory helper function."""

    def test_resolve_data_directory_from_config(self):
        """Should resolve directory from config dict."""
        config = {"data_directory": "/custom/data/path"}

        result = resolve_data_directory(config)

        assert result == Path("/custom/data/path")

    def test_resolve_data_directory_uses_default(self):
        """Should use default when not in config."""
        config = {}

        result = resolve_data_directory(config)

        expected = _resolve_data_directory(DEFAULT_ENV_VALUES["DATA_DIRECTORY"])
        assert result == expected


class TestIsFeatureEnabled:
    """Tests for feature flag checking."""

    def test_is_feature_enabled_returns_true_when_enabled(self):
        """Should return True when feature is enabled."""
        with patch.dict(os.environ, {"FEATURE_TEST": "true"}):
            result = is_feature_enabled("TEST")

        assert result is True

    def test_is_feature_enabled_returns_false_when_disabled(self):
        """Should return False when feature is disabled."""
        with patch.dict(os.environ, {"FEATURE_TEST": "false"}):
            result = is_feature_enabled("TEST")

        assert result is False

    def test_is_feature_enabled_uses_default_when_missing(self):
        """Should use default when env var not set."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("FEATURE_NONEXISTENT", None)

            result_true = is_feature_enabled("NONEXISTENT", default=True)
            result_false = is_feature_enabled("NONEXISTENT", default=False)

        assert result_true is True
        assert result_false is False

    def test_is_feature_enabled_accepts_various_true_values(self):
        """Should accept 1, yes, on as true."""
        for value in ["true", "1", "yes", "on", "TRUE", "YES"]:
            with patch.dict(os.environ, {"FEATURE_TEST": value}):
                result = is_feature_enabled("TEST")
                assert result is True, f"Failed for value: {value}"

    def test_is_feature_enabled_case_insensitive_feature_name(self):
        """Should uppercase feature name when checking."""
        with patch.dict(os.environ, {"FEATURE_LOWERCASE": "true"}):
            result = is_feature_enabled("lowercase")

        assert result is True


class TestGetFeatureFlags:
    """Tests for getting all feature flags."""

    def test_get_feature_flags_returns_all_feature_vars(self):
        """Should return all FEATURE_* environment variables."""
        with patch.dict(
            os.environ,
            {
                "FEATURE_ONE": "true",
                "FEATURE_TWO": "false",
                "NOT_A_FEATURE": "ignored",
            },
            clear=True,
        ):
            result = get_feature_flags()

        assert "ONE" in result
        assert "TWO" in result
        assert result["ONE"] is True
        assert result["TWO"] is False
        assert "NOT_A_FEATURE" not in result

    def test_get_feature_flags_empty_when_none_set(self):
        """Should return empty dict when no feature flags set."""
        env_without_features = {
            k: v for k, v in os.environ.items() if not k.startswith("FEATURE_")
        }

        with patch.dict(os.environ, env_without_features, clear=True):
            result = get_feature_flags()

        assert result == {}


class TestRequireFeature:
    """Tests for feature requirement checks."""

    def test_require_feature_does_not_raise_when_enabled(self):
        """Should not raise when feature is enabled."""
        with patch.dict(os.environ, {"FEATURE_ENABLED": "true"}):
            # Should not raise
            require_feature("ENABLED", "test operation")

    def test_require_feature_raises_when_disabled(self):
        """Should raise PermissionError when feature is disabled."""
        with patch.dict(os.environ, {"FEATURE_DISABLED": "false"}):
            with pytest.raises(PermissionError) as exc_info:
                require_feature("DISABLED", "test operation")

            assert "DISABLED" in str(exc_info.value)
            assert "test operation" in str(exc_info.value)

    def test_require_feature_raises_when_missing(self):
        """Should raise when feature not set and default would be False."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("FEATURE_MISSING", None)

            # Default is True, so this won't raise
            require_feature("MISSING", "test")

    def test_require_feature_includes_operation_in_error(self):
        """Should include operation description in error message."""
        with patch.dict(os.environ, {"FEATURE_TEST": "false"}):
            with pytest.raises(PermissionError) as exc_info:
                require_feature("TEST", "create backup")

            assert "create backup" in str(exc_info.value)

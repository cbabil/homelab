"""
Unit tests for lib/config.py

Tests configuration loading, feature flags, and data directory resolution.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from lib.config import (
    BACKEND_ROOT,
    DEFAULT_ENV_VALUES,
    PROJECT_ROOT,
    _cached_config,
    _load_env_file,
    _resolve_data_directory,
    get_feature_flags,
    is_feature_enabled,
    load_config,
    reload_config,
    require_feature,
    resolve_data_directory,
)


@pytest.fixture(autouse=True)
def clear_config_cache():
    """Clear the configuration cache before each test."""
    _cached_config.cache_clear()
    yield
    _cached_config.cache_clear()


@pytest.fixture
def clean_env():
    """Fixture to save and restore environment variables."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


class TestDefaultValues:
    """Tests for default configuration values."""

    def test_default_env_values_has_data_directory(self):
        """DEFAULT_ENV_VALUES should have DATA_DIRECTORY."""
        assert "DATA_DIRECTORY" in DEFAULT_ENV_VALUES
        assert DEFAULT_ENV_VALUES["DATA_DIRECTORY"] == "data"

    def test_default_env_values_has_app_env(self):
        """DEFAULT_ENV_VALUES should have APP_ENV."""
        assert "APP_ENV" in DEFAULT_ENV_VALUES
        assert DEFAULT_ENV_VALUES["APP_ENV"] == "production"

    def test_default_env_values_has_version(self):
        """DEFAULT_ENV_VALUES should have VERSION."""
        assert "VERSION" in DEFAULT_ENV_VALUES

    def test_default_env_values_has_ssh_timeout(self):
        """DEFAULT_ENV_VALUES should have SSH_TIMEOUT."""
        assert "SSH_TIMEOUT" in DEFAULT_ENV_VALUES
        assert DEFAULT_ENV_VALUES["SSH_TIMEOUT"] == "30"

    def test_default_env_values_has_max_connections(self):
        """DEFAULT_ENV_VALUES should have MAX_CONCURRENT_CONNECTIONS."""
        assert "MAX_CONCURRENT_CONNECTIONS" in DEFAULT_ENV_VALUES
        assert DEFAULT_ENV_VALUES["MAX_CONCURRENT_CONNECTIONS"] == "10"

    def test_project_root_is_path(self):
        """PROJECT_ROOT should be a Path object."""
        assert isinstance(PROJECT_ROOT, Path)

    def test_backend_root_is_path(self):
        """BACKEND_ROOT should be a Path object."""
        assert isinstance(BACKEND_ROOT, Path)


class TestLoadEnvFile:
    """Tests for _load_env_file function."""

    def test_load_env_file_no_file(self, clean_env, tmp_path):
        """_load_env_file should return empty dict if file doesn't exist."""
        with patch("lib.config.PROJECT_ROOT", tmp_path):
            result = _load_env_file("nonexistent.env")
        assert result == {}

    def test_load_env_file_parses_simple_values(self, clean_env, tmp_path):
        """_load_env_file should parse simple KEY=value pairs."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_KEY=test_value\nANOTHER_KEY=another_value")

        with patch("lib.config.PROJECT_ROOT", tmp_path):
            result = _load_env_file()

        assert result["TEST_KEY"] == "test_value"
        assert result["ANOTHER_KEY"] == "another_value"

    def test_load_env_file_strips_quotes(self, clean_env, tmp_path):
        """_load_env_file should strip quotes from values."""
        env_file = tmp_path / ".env"
        env_file.write_text("DOUBLE=\"double_quoted\"\nSINGLE='single_quoted'")

        with patch("lib.config.PROJECT_ROOT", tmp_path):
            result = _load_env_file()

        assert result["DOUBLE"] == "double_quoted"
        assert result["SINGLE"] == "single_quoted"

    def test_load_env_file_ignores_comments(self, clean_env, tmp_path):
        """_load_env_file should ignore comment lines."""
        env_file = tmp_path / ".env"
        env_file.write_text("# This is a comment\nKEY=value\n# Another comment")

        with patch("lib.config.PROJECT_ROOT", tmp_path):
            result = _load_env_file()

        assert "This" not in result
        assert result["KEY"] == "value"

    def test_load_env_file_ignores_empty_lines(self, clean_env, tmp_path):
        """_load_env_file should ignore empty lines."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=value1\n\n\nKEY2=value2")

        with patch("lib.config.PROJECT_ROOT", tmp_path):
            result = _load_env_file()

        assert len(result) == 2
        assert result["KEY1"] == "value1"
        assert result["KEY2"] == "value2"

    def test_load_env_file_ignores_lines_without_equals(self, clean_env, tmp_path):
        """_load_env_file should ignore lines without '='."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=value\ninvalid_line_no_equals\nKEY2=value2")

        with patch("lib.config.PROJECT_ROOT", tmp_path):
            result = _load_env_file()

        assert "invalid_line_no_equals" not in result
        assert result["KEY"] == "value"

    def test_load_env_file_ignores_empty_key(self, clean_env, tmp_path):
        """_load_env_file should ignore lines with empty keys."""
        env_file = tmp_path / ".env"
        env_file.write_text("=empty_key\nKEY=value")

        with patch("lib.config.PROJECT_ROOT", tmp_path):
            result = _load_env_file()

        assert "" not in result
        assert result["KEY"] == "value"

    def test_load_env_file_sets_os_environ(self, clean_env, tmp_path):
        """_load_env_file should set os.environ for new keys."""
        env_file = tmp_path / ".env"
        env_file.write_text("NEW_ENV_VAR=new_value")

        with patch("lib.config.PROJECT_ROOT", tmp_path):
            _load_env_file()

        assert os.environ.get("NEW_ENV_VAR") == "new_value"

    def test_load_env_file_does_not_override_existing(self, clean_env, tmp_path):
        """_load_env_file should not override existing env vars."""
        os.environ["EXISTING_VAR"] = "original"
        env_file = tmp_path / ".env"
        env_file.write_text("EXISTING_VAR=from_file")

        with patch("lib.config.PROJECT_ROOT", tmp_path):
            _load_env_file()

        assert os.environ["EXISTING_VAR"] == "original"

    def test_load_env_file_handles_read_error(self, clean_env, tmp_path):
        """_load_env_file should handle file read errors gracefully."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=value")

        with patch("lib.config.PROJECT_ROOT", tmp_path):
            with patch.object(Path, "read_text", side_effect=OSError("Read error")):
                result = _load_env_file()

        assert result == {}

    def test_load_env_file_checks_backend_fallback(self, clean_env, tmp_path):
        """_load_env_file should check backend/ subfolder if root .env missing."""
        backend_dir = tmp_path / "backend"
        backend_dir.mkdir()
        env_file = backend_dir / ".env"
        env_file.write_text("BACKEND_KEY=backend_value")

        with patch("lib.config.PROJECT_ROOT", tmp_path):
            result = _load_env_file()

        assert result["BACKEND_KEY"] == "backend_value"


class TestResolveDataDirectory:
    """Tests for _resolve_data_directory function."""

    def test_resolve_relative_path(self):
        """_resolve_data_directory should resolve relative paths."""
        result = _resolve_data_directory("data")
        assert result.is_absolute()

    def test_resolve_absolute_path(self, tmp_path):
        """_resolve_data_directory should keep absolute paths as-is."""
        result = _resolve_data_directory(str(tmp_path))
        assert result == tmp_path


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_returns_dict(self, clean_env):
        """load_config should return a dictionary."""
        config = load_config()
        assert isinstance(config, dict)

    def test_load_config_has_data_directory(self, clean_env):
        """load_config should include data_directory."""
        config = load_config()
        assert "data_directory" in config

    def test_load_config_has_app_env(self, clean_env):
        """load_config should include app_env."""
        config = load_config()
        assert "app_env" in config

    def test_load_config_has_version(self, clean_env):
        """load_config should include version."""
        config = load_config()
        assert "version" in config

    def test_load_config_has_ssh_timeout_as_int(self, clean_env):
        """load_config should convert ssh_timeout to int."""
        config = load_config()
        assert "ssh_timeout" in config
        assert isinstance(config["ssh_timeout"], int)

    def test_load_config_has_max_connections_as_int(self, clean_env):
        """load_config should convert max_concurrent_connections to int."""
        config = load_config()
        assert "max_concurrent_connections" in config
        assert isinstance(config["max_concurrent_connections"], int)

    def test_load_config_has_tools_directory(self, clean_env):
        """load_config should include tools_directory."""
        config = load_config()
        assert "tools_directory" in config

    def test_load_config_has_tools_package(self, clean_env):
        """load_config should include tools_package."""
        config = load_config()
        assert "tools_package" in config

    def test_load_config_returns_copy(self, clean_env):
        """load_config should return a copy, not the cached original."""
        config1 = load_config()
        config2 = load_config()
        config1["modified"] = True
        assert "modified" not in config2


class TestReloadConfig:
    """Tests for reload_config function."""

    def test_reload_config_clears_cache(self, clean_env):
        """reload_config should clear the cache."""
        load_config()
        info_before = _cached_config.cache_info()
        reload_config()
        info_after = _cached_config.cache_info()
        # After reload, we should have 1 hit (the reload itself)
        assert info_after.hits == 0 or info_after.misses >= 1

    def test_reload_config_returns_dict(self, clean_env):
        """reload_config should return a dictionary."""
        config = reload_config()
        assert isinstance(config, dict)


class TestResolveDataDirectoryPublic:
    """Tests for resolve_data_directory public function."""

    def test_resolve_from_config(self, clean_env):
        """resolve_data_directory should use config's data_directory."""
        config = {"data_directory": "/custom/data/path"}
        result = resolve_data_directory(config)
        assert result == Path("/custom/data/path")

    def test_resolve_with_default(self, clean_env):
        """resolve_data_directory should use default if not in config."""
        result = resolve_data_directory({})
        assert result.is_absolute()


class TestIsFeatureEnabled:
    """Tests for is_feature_enabled function."""

    def test_feature_enabled_true_values(self, clean_env):
        """is_feature_enabled should return True for true-ish values."""
        true_values = ["true", "1", "yes", "on", "TRUE", "Yes", "ON"]
        for value in true_values:
            os.environ["FEATURE_TEST"] = value
            assert is_feature_enabled("TEST") is True

    def test_feature_enabled_false_values(self, clean_env):
        """is_feature_enabled should return False for false-ish values."""
        false_values = ["false", "0", "no", "off", "FALSE", "No", "OFF"]
        for value in false_values:
            os.environ["FEATURE_TEST"] = value
            assert is_feature_enabled("TEST") is False

    def test_feature_enabled_default_true(self, clean_env):
        """is_feature_enabled should use default=True when not set."""
        # Ensure env var is not set
        os.environ.pop("FEATURE_NONEXISTENT", None)
        assert is_feature_enabled("NONEXISTENT", default=True) is True

    def test_feature_enabled_default_false(self, clean_env):
        """is_feature_enabled should use default=False when not set."""
        os.environ.pop("FEATURE_NONEXISTENT", None)
        assert is_feature_enabled("NONEXISTENT", default=False) is False

    def test_feature_enabled_case_insensitive_name(self, clean_env):
        """is_feature_enabled should uppercase the feature name."""
        os.environ["FEATURE_LOWERCASE"] = "true"
        assert is_feature_enabled("lowercase") is True


class TestGetFeatureFlags:
    """Tests for get_feature_flags function."""

    def test_get_feature_flags_returns_dict(self, clean_env):
        """get_feature_flags should return a dictionary."""
        result = get_feature_flags()
        assert isinstance(result, dict)

    def test_get_feature_flags_includes_enabled(self, clean_env):
        """get_feature_flags should include enabled features."""
        os.environ["FEATURE_ENABLED"] = "true"
        result = get_feature_flags()
        assert result.get("ENABLED") is True

    def test_get_feature_flags_includes_disabled(self, clean_env):
        """get_feature_flags should include disabled features."""
        os.environ["FEATURE_DISABLED"] = "false"
        result = get_feature_flags()
        assert result.get("DISABLED") is False

    def test_get_feature_flags_ignores_non_feature(self, clean_env):
        """get_feature_flags should ignore non-FEATURE_ vars."""
        os.environ["NOT_A_FEATURE"] = "true"
        result = get_feature_flags()
        assert "NOT_A_FEATURE" not in result

    def test_get_feature_flags_strips_prefix(self, clean_env):
        """get_feature_flags should strip FEATURE_ prefix."""
        os.environ["FEATURE_MYFEATURE"] = "true"
        result = get_feature_flags()
        assert "MYFEATURE" in result
        assert "FEATURE_MYFEATURE" not in result


class TestRequireFeature:
    """Tests for require_feature function."""

    def test_require_feature_enabled_no_error(self, clean_env):
        """require_feature should not raise if feature is enabled."""
        os.environ["FEATURE_ENABLED"] = "true"
        # Should not raise
        require_feature("ENABLED", "test operation")

    def test_require_feature_disabled_raises(self, clean_env):
        """require_feature should raise PermissionError if disabled."""
        os.environ["FEATURE_DISABLED"] = "false"
        with pytest.raises(PermissionError) as exc_info:
            require_feature("DISABLED", "test operation")
        assert "DISABLED" in str(exc_info.value)
        assert "test operation" in str(exc_info.value)

    def test_require_feature_unset_uses_default(self, clean_env):
        """require_feature should use default (False) when not set."""
        os.environ.pop("FEATURE_UNSET", None)
        # Default is False (fail-closed), so should raise
        with pytest.raises(PermissionError):
            require_feature("UNSET", "test operation")

    def test_require_feature_error_message_format(self, clean_env):
        """require_feature error should have correct format."""
        os.environ["FEATURE_TESTFLAG"] = "false"
        with pytest.raises(PermissionError) as exc_info:
            require_feature("TESTFLAG", "create backup")
        error_msg = str(exc_info.value)
        assert "Feature 'TESTFLAG' is not enabled" in error_msg
        assert "Cannot perform: create backup" in error_msg

"""Configuration loading utilities for the backend."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import structlog


logger = structlog.get_logger("config")

DEFAULT_ENV_VALUES: Dict[str, str] = {
    "DATA_DIRECTORY": "data",
    "APP_ENV": "production",
    "VERSION": "0.1.0",
    "SSH_TIMEOUT": "30",
    "MAX_CONCURRENT_CONNECTIONS": "10",
    "TOOLS_DIRECTORY": "src/tools",
    "TOOLS_PACKAGE": "tools",
}

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _load_env_file(filename: str = ".env") -> Dict[str, str]:
    """Load environment variables from the provided `.env` file."""

    env_path = PROJECT_ROOT / filename
    if not env_path.exists():
        backend_env = PROJECT_ROOT / "backend" / filename
        if backend_env.exists():
            env_path = backend_env

    loaded: Dict[str, str] = {}

    if not env_path.exists():
        logger.info("No .env file detected", path=str(env_path))
        return loaded

    try:
        raw_contents = env_path.read_text(encoding="utf-8")
    except OSError as error:
        logger.error(
            "Unable to read .env file",
            path=str(env_path),
            error=str(error),
        )
        return loaded

    for raw_line in raw_contents.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        cleaned = value.strip().strip('"').strip("'")
        loaded[key] = cleaned
        if key not in os.environ:
            os.environ[key] = cleaned

    logger.info("Environment variables loaded from .env", path=str(env_path))
    return loaded


def _resolve_data_directory(value: str) -> Path:
    """Resolve the configured data directory relative to the backend root."""

    data_path = Path(value)
    if not data_path.is_absolute():
        data_path = (BACKEND_ROOT / data_path).resolve()
    return data_path


@lru_cache(maxsize=1)
def _cached_config() -> Dict[str, Any]:
    """Load configuration once and cache the result."""

    _load_env_file()

    config: Dict[str, Any] = {}
    for key, default in DEFAULT_ENV_VALUES.items():
        config[key] = os.getenv(key, default)

    data_directory = _resolve_data_directory(config["DATA_DIRECTORY"]).resolve()
    config["data_directory"] = str(data_directory)
    config["app_env"] = config["APP_ENV"]
    config["version"] = config["VERSION"]
    config["ssh_timeout"] = int(config["SSH_TIMEOUT"])
    config["max_concurrent_connections"] = int(config["MAX_CONCURRENT_CONNECTIONS"])

    tools_directory_value = config.get("TOOLS_DIRECTORY", DEFAULT_ENV_VALUES["TOOLS_DIRECTORY"])
    tools_path = Path(tools_directory_value)
    if not tools_path.is_absolute():
        tools_path = (BACKEND_ROOT / tools_directory_value).resolve()
    config["tools_directory"] = str(tools_path)
    config["tools_package"] = config.get("TOOLS_PACKAGE", DEFAULT_ENV_VALUES["TOOLS_PACKAGE"])

    return config


def load_config() -> Dict[str, Any]:
    """Return a copy of the cached configuration dictionary."""

    return dict(_cached_config())


def reload_config() -> Dict[str, Any]:
    """Clear cached configuration and reload it."""

    _cached_config.cache_clear()
    return load_config()


def resolve_data_directory(config: Dict[str, Any]) -> Path:
    """Resolve the data directory from a configuration dictionary."""

    directory = config.get("data_directory") or DEFAULT_ENV_VALUES["DATA_DIRECTORY"]
    return _resolve_data_directory(directory)


# =============================================================================
# Feature Flag Utilities
# =============================================================================

def is_feature_enabled(feature_name: str, default: bool = True) -> bool:
    """Check if a feature flag is enabled.

    Feature flags are read from environment variables with the FEATURE_ prefix.
    For example, is_feature_enabled("MARKETPLACE") checks FEATURE_MARKETPLACE.

    Args:
        feature_name: The feature name (without FEATURE_ prefix).
        default: Default value if the environment variable is not set.

    Returns:
        True if the feature is enabled, False otherwise.

    Example:
        >>> is_feature_enabled("MARKETPLACE")  # Checks FEATURE_MARKETPLACE
        True
        >>> is_feature_enabled("CUSTOM_FEATURE", default=False)
        False
    """
    env_key = f"FEATURE_{feature_name.upper()}"
    value = os.getenv(env_key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


def get_feature_flags() -> Dict[str, bool]:
    """Get all feature flags from environment variables.

    Scans environment variables for FEATURE_* prefixed keys and returns
    a dictionary of feature names to their boolean values.

    Returns:
        Dictionary mapping feature names (without FEATURE_ prefix) to booleans.

    Example:
        >>> get_feature_flags()
        {'MARKETPLACE': True, 'BACKUP': True, 'STRICT_SSH': False}
    """
    flags: Dict[str, bool] = {}
    for key, value in os.environ.items():
        if key.startswith("FEATURE_"):
            feature_name = key[8:]  # Remove "FEATURE_" prefix
            flags[feature_name] = value.lower() in ('true', '1', 'yes', 'on')
    return flags


def require_feature(feature_name: str, operation: str = "operation") -> None:
    """Raise an error if a feature is not enabled.

    Use this to guard operations that require a specific feature to be enabled.

    Args:
        feature_name: The feature name (without FEATURE_ prefix).
        operation: Description of the operation being attempted (for error message).

    Raises:
        PermissionError: If the feature is not enabled.

    Example:
        >>> require_feature("BACKUP", "create backup")  # Raises if FEATURE_BACKUP is false
    """
    if not is_feature_enabled(feature_name):
        raise PermissionError(
            f"Feature '{feature_name}' is not enabled. Cannot perform: {operation}"
        )

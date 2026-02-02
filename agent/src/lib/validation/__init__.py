"""Command and Docker parameter validation.

Provides security validation for shell commands and Docker container parameters.

This package validates:
- Shell commands against a security allowlist
- Docker run commands for dangerous flags
- Docker container parameters for privilege escalation
- Volume mounts for sensitive paths
"""

from .constants import (
    BLOCKED_DOCKER_PARAMS,
    BLOCKED_DOCKER_RUN_FLAGS,
    BLOCKED_VOLUME_PATTERNS,
    PROTECTED_PATHS,
)
from .volume_validation import validate_volume_mount, validate_volume_path
from .docker_validation import validate_docker_params, validate_docker_run_command
from .command_validation import (
    CommandAllowlistEntry,
    CommandValidator,
    COMMAND_ALLOWLIST,
    validate_command,
)

# Backward compatibility alias for tests
_validate_volume_mount = validate_volume_mount

__all__ = [
    # Constants
    "BLOCKED_DOCKER_PARAMS",
    "BLOCKED_DOCKER_RUN_FLAGS",
    "BLOCKED_VOLUME_PATTERNS",
    "PROTECTED_PATHS",
    # Volume validation
    "validate_volume_mount",
    "validate_volume_path",
    "_validate_volume_mount",  # Backward compat alias
    # Docker validation
    "validate_docker_params",
    "validate_docker_run_command",
    # Command validation
    "CommandAllowlistEntry",
    "CommandValidator",
    "COMMAND_ALLOWLIST",
    "validate_command",
]

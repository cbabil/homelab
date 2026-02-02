"""Security utilities for the agent.

This module re-exports all security components from src/lib for backwards
compatibility. New code should import directly from src/lib.

Provides command allowlisting, input validation, and security controls
to prevent arbitrary code execution and privilege escalation.
"""

# Re-export all security components from lib modules
try:
    from .lib.encryption import TokenEncryption, encrypt_token, decrypt_token
    from .lib.permissions import (
        PermissionLevel,
        METHOD_PERMISSIONS,
        get_method_permission,
    )
    from .lib.rate_limiter import (
        CommandRateLimiter,
        acquire_command_slot,
        release_command_slot,
    )
    from .lib.redact import redact_sensitive_data, SENSITIVE_KEYS
    from .lib.replay import ReplayProtection, validate_message_freshness, generate_nonce
    from .lib.validation import (
        CommandValidator,
        CommandAllowlistEntry,
        COMMAND_ALLOWLIST,
        validate_command,
        validate_docker_params,
        BLOCKED_DOCKER_PARAMS,
        PROTECTED_PATHS,
    )
except ImportError:
    from lib.encryption import TokenEncryption, encrypt_token, decrypt_token
    from lib.permissions import (
        PermissionLevel,
        METHOD_PERMISSIONS,
        get_method_permission,
    )
    from lib.rate_limiter import (
        CommandRateLimiter,
        acquire_command_slot,
        release_command_slot,
    )
    from lib.redact import redact_sensitive_data, SENSITIVE_KEYS
    from lib.replay import ReplayProtection, validate_message_freshness, generate_nonce
    from lib.validation import (
        CommandValidator,
        CommandAllowlistEntry,
        COMMAND_ALLOWLIST,
        validate_command,
        validate_docker_params,
        BLOCKED_DOCKER_PARAMS,
        PROTECTED_PATHS,
    )

__all__ = [
    # Encryption
    "TokenEncryption",
    "encrypt_token",
    "decrypt_token",
    # Permissions
    "PermissionLevel",
    "METHOD_PERMISSIONS",
    "get_method_permission",
    # Rate limiting
    "CommandRateLimiter",
    "acquire_command_slot",
    "release_command_slot",
    # Redaction
    "redact_sensitive_data",
    "SENSITIVE_KEYS",
    # Replay protection
    "ReplayProtection",
    "validate_message_freshness",
    "generate_nonce",
    # Validation
    "CommandValidator",
    "CommandAllowlistEntry",
    "COMMAND_ALLOWLIST",
    "validate_command",
    "validate_docker_params",
    "BLOCKED_DOCKER_PARAMS",
    "PROTECTED_PATHS",
]

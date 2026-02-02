"""Common utilities library for the agent.

This package contains reusable components:
- audit: Structured audit logging for security events
- encryption: Token encryption at rest
- permissions: RPC method permission levels
- rate_limiter: Command execution rate limiting
- redact: Sensitive data redaction for logging
- replay: Message replay protection
- validation: Command and Docker parameter validation
"""

from .audit import (
    AuditLogger,
    AuditEntry,
    AuditAction,
    get_audit_logger,
    set_audit_logger,
)
from .encryption import TokenEncryption, encrypt_token, decrypt_token
from .permissions import PermissionLevel, METHOD_PERMISSIONS, get_method_permission
from .rate_limiter import CommandRateLimiter, acquire_command_slot, release_command_slot
from .redact import redact_sensitive_data, SENSITIVE_KEYS
from .replay import ReplayProtection, validate_message_freshness, generate_nonce
from .validation import (
    CommandValidator,
    CommandAllowlistEntry,
    COMMAND_ALLOWLIST,
    validate_command,
    validate_docker_params,
    validate_docker_run_command,
    BLOCKED_DOCKER_PARAMS,
    BLOCKED_DOCKER_RUN_FLAGS,
    BLOCKED_VOLUME_PATTERNS,
    PROTECTED_PATHS,
)

__all__ = [
    # Audit
    "AuditLogger",
    "AuditEntry",
    "AuditAction",
    "get_audit_logger",
    "set_audit_logger",
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
    "validate_docker_run_command",
    "BLOCKED_DOCKER_PARAMS",
    "BLOCKED_DOCKER_RUN_FLAGS",
    "BLOCKED_VOLUME_PATTERNS",
    "PROTECTED_PATHS",
]

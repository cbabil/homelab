"""
Security Utilities

Input validation, constant-time operations, and log sanitization.
"""

import re
import hmac
import ipaddress
from typing import Dict, Any
import structlog

logger = structlog.get_logger("security")

# Dangerous patterns for shell injection
DANGEROUS_PATTERNS = [
    r'[;&|`$()]',  # Shell metacharacters
    r'\.\.',  # Path traversal
    r'[\x00-\x1f]',  # Control characters
]

# Patterns to sanitize in logs
SENSITIVE_PATTERNS = [
    (r'password[=:]\s*\S+', 'password=***'),
    (r'token[=:]\s*\S+', 'token=***'),
    (r'key[=:]\s*\S+', 'key=***'),
    (r'secret[=:]\s*\S+', 'secret=***'),
    (r'eyJ[A-Za-z0-9_-]*\.?[A-Za-z0-9_-]*\.?[A-Za-z0-9_-]*', '***JWT***'),
]


def validate_server_input(host: str, port: int) -> Dict[str, Any]:
    """Validate server connection parameters."""
    errors = []

    # Validate host
    if not host:
        errors.append("Host is required")
    else:
        # Check for dangerous characters
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, host):
                errors.append(f"Invalid characters in hostname")
                break

        # Validate as IP or hostname
        if not errors:
            try:
                ipaddress.ip_address(host)
            except ValueError:
                # Not an IP, validate as hostname
                hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
                if not re.match(hostname_pattern, host):
                    errors.append("Invalid hostname format")

    # Validate port
    if not isinstance(port, int) or port < 1 or port > 65535:
        errors.append("Port must be between 1 and 65535")

    if errors:
        return {"valid": False, "error": "; ".join(errors)}
    return {"valid": True}


def validate_app_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate app deployment configuration."""
    errors = []

    # Validate environment variables
    env_vars = config.get("env", {})
    for key, value in env_vars.items():
        if not isinstance(key, str) or not isinstance(value, str):
            errors.append(f"Invalid env var type for {key}")
            continue

        # Check for command injection in values
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, str(value)):
                errors.append(f"Dangerous characters in env var {key}")
                break

    # Validate port mappings
    ports = config.get("ports", {})
    for container_port, host_port in ports.items():
        try:
            cp = int(container_port)
            hp = int(host_port)
            if cp < 1 or cp > 65535 or hp < 1 or hp > 65535:
                errors.append(f"Invalid port mapping: {container_port}:{host_port}")
        except (ValueError, TypeError):
            errors.append(f"Invalid port format: {container_port}:{host_port}")

    if errors:
        return {"valid": False, "error": "; ".join(errors)}
    return {"valid": True}


def constant_time_compare(a: str, b: str) -> bool:
    """
    Compare two strings in constant time to prevent timing attacks.
    Used for password/token comparison.
    """
    return hmac.compare_digest(a.encode('utf-8'), b.encode('utf-8'))


def sanitize_log_message(message: str) -> str:
    """Remove sensitive data from log messages."""
    result = message
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def validate_username(username: str) -> Dict[str, Any]:
    """Validate username format."""
    if not username:
        return {"valid": False, "error": "Username is required"}

    if len(username) < 3 or len(username) > 32:
        return {"valid": False, "error": "Username must be 3-32 characters"}

    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', username):
        return {"valid": False, "error": "Username must start with letter and contain only alphanumeric, underscore, hyphen"}

    return {"valid": True}


def validate_password_strength(password: str) -> Dict[str, Any]:
    """Check password meets minimum requirements."""
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters")

    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain uppercase letter")

    if not re.search(r'[a-z]', password):
        errors.append("Password must contain lowercase letter")

    if not re.search(r'[0-9]', password):
        errors.append("Password must contain digit")

    if errors:
        return {"valid": False, "errors": errors}
    return {"valid": True}

"""
Security Utilities

Input validation, constant-time operations, and log sanitization.
Includes NIST SP 800-63B-4 compliant password validation.
"""

import re
import hmac
import ipaddress
from typing import Dict, Any, List
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
                errors.append("Invalid characters in hostname")
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
    """Check password meets minimum requirements (legacy mode)."""
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


async def validate_password_length_policy(
    password: str,
    username: str = "",
    length_policy_mode: bool = True,
    min_length: int = 15,
    max_length: int = 128,
    check_blocklist: bool = True,
    check_hibp: bool = False,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_numbers: bool = True,
    require_special: bool = True
) -> Dict[str, Any]:
    """
    Modern password validation (SP 800-63B-4 compliant).

    In length_policy mode:
    - Enforces minimum length (15+ chars for password-only auth)
    - Checks against blocklist of common/compromised passwords
    - Checks for sequential/repetitive patterns
    - Does NOT enforce complexity rules (uppercase, numbers, special chars)

    In legacy mode:
    - Uses traditional complexity requirements
    - Shorter minimum length allowed

    Args:
        password: The password to validate
        username: Username for context-specific checking
        length_policy_mode: If True, use length_policy guidelines (length + blocklist only)
        min_length: Minimum password length (15 for length_policy, 8 for legacy)
        max_length: Maximum password length (recommended at least 64)
        check_blocklist: Check against common password blocklist
        check_hibp: Check Have I Been Pwned API (requires network)
        require_uppercase: Require uppercase letter (legacy mode only)
        require_lowercase: Require lowercase letter (legacy mode only)
        require_numbers: Require number (legacy mode only)
        require_special: Require special character (legacy mode only)

    Returns:
        Dict with:
        - valid: bool
        - errors: List of error strings
        - warnings: List of warning strings
        - mode: 'length_policy' or 'legacy'
        - checks: Dict of individual check results
    """
    from services.password_blocklist_service import get_blocklist_service

    errors: List[str] = []
    warnings: List[str] = []
    checks: Dict[str, Any] = {}

    # Length validation (common to both modes)
    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters")
        checks["min_length"] = False
    else:
        checks["min_length"] = True

    if len(password) > max_length:
        errors.append(f"Password must be at most {max_length} characters")
        checks["max_length"] = False
    else:
        checks["max_length"] = True

    # Unicode support - allow all printable Unicode
    # NIST requires support for Unicode characters
    checks["unicode_support"] = True

    if length_policy_mode:
        # MODERN MODE: Length + blocklist, no complexity rules
        if check_blocklist:
            blocklist_service = get_blocklist_service(enable_hibp=check_hibp)
            blocklist_result = await blocklist_service.validate_password(
                password=password,
                username=username,
                check_blocklist=True,
                check_hibp=check_hibp
            )
            checks.update(blocklist_result.get("checks", {}))
            errors.extend(blocklist_result.get("errors", []))
            warnings.extend(blocklist_result.get("warnings", []))

    else:
        # LEGACY MODE: Traditional complexity requirements
        if require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
            checks["has_uppercase"] = False
        else:
            checks["has_uppercase"] = True

        if require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
            checks["has_lowercase"] = False
        else:
            checks["has_lowercase"] = True

        if require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
            checks["has_number"] = False
        else:
            checks["has_number"] = True

        if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>\-_=+\[\]\\;\'`~]', password):
            errors.append("Password must contain at least one special character")
            checks["has_special"] = False
        else:
            checks["has_special"] = True

        # Still check blocklist in legacy mode if enabled
        if check_blocklist:
            blocklist_service = get_blocklist_service(enable_hibp=check_hibp)
            blocklist_result = await blocklist_service.validate_password(
                password=password,
                username=username,
                check_blocklist=True,
                check_hibp=check_hibp
            )
            # Add blocklist errors as warnings in legacy mode
            warnings.extend(blocklist_result.get("errors", []))
            checks["blocklist_checks"] = blocklist_result.get("checks", {})

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "mode": "length_policy" if length_policy_mode else "legacy",
        "checks": checks
    }

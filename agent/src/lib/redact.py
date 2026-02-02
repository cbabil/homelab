"""Sensitive data redaction for logging.

Provides utilities to redact sensitive information before logging.
"""

from typing import Any, Dict, Set

# Sensitive keys that should be redacted in logs
SENSITIVE_KEYS: Set[str] = {
    "token",
    "password",
    "secret",
    "key",
    "api_key",
    "apikey",
    "auth",
    "credential",
    "private",
}


def redact_sensitive_data(data: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
    """Redact sensitive values from a dictionary for logging.

    Args:
        data: Dictionary to redact.
        depth: Current recursion depth (to prevent infinite loops).

    Returns:
        Dictionary with sensitive values replaced by "[REDACTED]".
    """
    if depth > 10:
        return {"_error": "max_depth_exceeded"}

    result: Dict[str, Any] = {}
    for key, value in data.items():
        key_lower = key.lower()

        # Check if key contains sensitive word
        is_sensitive = any(s in key_lower for s in SENSITIVE_KEYS)

        if is_sensitive:
            result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = redact_sensitive_data(value, depth + 1)
        elif isinstance(value, list):
            result[key] = [
                redact_sensitive_data(v, depth + 1) if isinstance(v, dict) else v
                for v in value
            ]
        else:
            result[key] = value

    return result

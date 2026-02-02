# Task 03: Update Backend Password Validation

## Overview

Update the password validation logic in `backend/src/lib/security.py` to support NIST SP 800-63B-4 compliance with dual-mode operation.

## File to Modify

`backend/src/lib/security.py`

## Requirements

1. Add new `validate_password_nist()` function
2. Support both NIST mode and legacy mode
3. Integrate with blocklist service
4. Keep existing `validate_password_strength()` for backward compatibility (deprecated)

## Current Implementation

```python
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
```

## New Implementation

```python
from typing import Dict, Any, Optional
from ..services.password_blocklist_service import blocklist_service


async def validate_password_nist(
    password: str,
    username: str = "",
    nist_mode: bool = True,
    min_length: int = 15,
    max_length: int = 128,
    check_blocklist: bool = True,
    check_hibp: bool = False,
    legacy_rules: Optional[Dict[str, bool]] = None
) -> Dict[str, Any]:
    """
    Validate password per NIST SP 800-63B-4 guidelines.

    Args:
        password: The password to validate
        username: Username for context-specific checking
        nist_mode: If True, use NIST rules (length + blocklist)
                   If False, use legacy complexity rules
        min_length: Minimum password length (15 for NIST, configurable for legacy)
        max_length: Maximum password length (NIST requires at least 64)
        check_blocklist: Whether to check against password blocklist
        check_hibp: Whether to check Have I Been Pwned API
        legacy_rules: For legacy mode, dict with:
                      - require_uppercase: bool
                      - require_lowercase: bool
                      - require_numbers: bool
                      - require_special: bool

    Returns:
        {
            "valid": bool,
            "errors": list[str],
            "warnings": list[str],
            "nist_compliant": bool,
            "blocklist_result": dict or None
        }
    """
    errors = []
    warnings = []
    blocklist_result = None

    # Length validation (both modes)
    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters")

    if len(password) > max_length:
        errors.append(f"Password must be at most {max_length} characters")

    if nist_mode:
        # NIST Mode: Length + blocklist, NO complexity rules

        # Blocklist check
        if check_blocklist:
            blocklist_result = await blocklist_service.check_password(
                password=password,
                username=username,
                check_hibp=check_hibp
            )
            if blocklist_result["blocked"]:
                errors.append(blocklist_result["reason"])

        # Check for sequential patterns (NIST requirement)
        if blocklist_service.check_sequential_pattern(password):
            if "sequential" not in str(blocklist_result):
                errors.append("Password contains sequential characters (e.g., 1234, abcd)")

        # Check for repetitive patterns (NIST requirement)
        if blocklist_service.check_repetitive_pattern(password):
            if "repetitive" not in str(blocklist_result):
                errors.append("Password contains repetitive characters (e.g., aaaa)")

        # Provide helpful feedback for short passwords
        if len(password) >= 8 and len(password) < 15:
            warnings.append("Consider using a longer passphrase for better security")

    else:
        # Legacy Mode: Apply complexity rules from settings
        if legacy_rules:
            if legacy_rules.get("require_uppercase") and not re.search(r'[A-Z]', password):
                errors.append("Password must contain at least one uppercase letter")

            if legacy_rules.get("require_lowercase") and not re.search(r'[a-z]', password):
                errors.append("Password must contain at least one lowercase letter")

            if legacy_rules.get("require_numbers") and not re.search(r'[0-9]', password):
                errors.append("Password must contain at least one digit")

            if legacy_rules.get("require_special") and not re.search(r'[!@#$%^&*(),.?":{}|<>\-_=+\[\]\\;\'`~]', password):
                errors.append("Password must contain at least one special character")

        # Optional blocklist check in legacy mode
        if check_blocklist:
            blocklist_result = await blocklist_service.check_password(
                password=password,
                username=username,
                check_hibp=check_hibp
            )
            if blocklist_result["blocked"]:
                warnings.append(f"Warning: {blocklist_result['reason']}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "nist_compliant": nist_mode and len(errors) == 0,
        "blocklist_result": blocklist_result
    }


# Keep for backward compatibility (deprecated)
def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Check password meets minimum requirements.

    DEPRECATED: Use validate_password_nist() for NIST-compliant validation.
    """
    import warnings
    warnings.warn(
        "validate_password_strength is deprecated, use validate_password_nist instead",
        DeprecationWarning,
        stacklevel=2
    )

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
```

## Integration with Settings

The validation function should be called with settings from the database:

```python
# In auth_service.py or similar
async def validate_new_password(password: str, username: str) -> Dict[str, Any]:
    """Validate password using current security settings."""
    settings = await get_security_settings()

    nist_mode = settings.get("security.nist_compliance_mode", False)
    min_length = settings.get("security.password_min_length", 15 if nist_mode else 8)
    check_blocklist = settings.get("security.enable_blocklist_check", True)
    check_hibp = settings.get("security.enable_hibp_api_check", False)

    legacy_rules = None
    if not nist_mode:
        legacy_rules = {
            "require_uppercase": settings.get("security.password_require_uppercase", True),
            "require_lowercase": True,  # Always required in legacy mode
            "require_numbers": settings.get("security.password_require_numbers", True),
            "require_special": settings.get("security.password_require_special_chars", True),
        }

    return await validate_password_nist(
        password=password,
        username=username,
        nist_mode=nist_mode,
        min_length=min_length,
        check_blocklist=check_blocklist,
        check_hibp=check_hibp,
        legacy_rules=legacy_rules
    )
```

## Dependencies

- Task 01: Blocklist service must be created first
- Task 05: Database settings must be added

## Acceptance Criteria

- [ ] `validate_password_nist()` function exists and is async
- [ ] NIST mode accepts passwords with only length requirement (15+ chars)
- [ ] NIST mode rejects passwords on blocklist
- [ ] NIST mode rejects sequential/repetitive patterns
- [ ] Legacy mode enforces complexity rules when configured
- [ ] Old `validate_password_strength()` shows deprecation warning
- [ ] Function integrates with settings from database

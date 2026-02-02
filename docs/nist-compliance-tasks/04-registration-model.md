# Task 04: Update Registration Validation Model

## Overview

Update the `RegistrationCredentials` Pydantic model in `backend/src/models/auth.py` to remove hardcoded complexity requirements and delegate NIST validation to the service layer.

## File to Modify

`backend/src/models/auth.py`

## Requirements

1. Remove hardcoded complexity requirements from `@field_validator`
2. Keep basic validation (length bounds)
3. Move detailed NIST/legacy validation to service layer
4. Maintain backward compatibility

## Current Implementation

```python
class RegistrationCredentials(BaseModel):
    """Registration credentials for new user creation."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=12, max_length=128, description="Password")
    confirm_password: str = Field(..., description="Password confirmation")
    role: Optional[UserRole] = Field(UserRole.USER, description="User role")
    accept_terms: bool = Field(..., description="Terms acceptance")

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters')
        if len(v) > 128:
            raise ValueError('Password must be at most 128 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>\-_=+\[\]\\;\'`~]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    @model_validator(mode="after")
    def passwords_match(cls, values: "RegistrationCredentials") -> "RegistrationCredentials":
        """Validate password confirmation matches."""
        if values.password != values.confirm_password:
            raise ValueError('Passwords do not match')
        return values
```

## New Implementation

```python
class RegistrationCredentials(BaseModel):
    """
    Registration credentials for new user creation.

    Note: Password complexity validation is performed at the service layer
    based on current security settings (NIST mode vs legacy mode).
    This model only validates basic constraints.
    """
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    confirm_password: str = Field(..., description="Password confirmation")
    role: Optional[UserRole] = Field(UserRole.USER, description="User role")
    accept_terms: bool = Field(..., description="Terms acceptance")

    @field_validator('password')
    @classmethod
    def validate_password_basic(cls, v: str) -> str:
        """
        Basic password validation - length bounds only.

        Detailed validation (NIST or legacy complexity rules) is performed
        at the service layer where security settings are available.
        """
        # Minimum 8 to allow some flexibility - actual min depends on settings
        # NIST mode: 15 minimum
        # Legacy mode: Configurable (6-32)
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')

        # NIST requires at least 64 max, we allow 128
        if len(v) > 128:
            raise ValueError('Password exceeds maximum length of 128 characters')

        # Unicode is allowed per NIST guidelines
        # No ASCII-only restriction

        return v

    @model_validator(mode="after")
    def passwords_match(cls, values: "RegistrationCredentials") -> "RegistrationCredentials":
        """Validate password confirmation matches."""
        if values.password != values.confirm_password:
            raise ValueError('Passwords do not match')
        return values
```

## Service Layer Integration

The registration service must call the NIST validation:

```python
# In auth_service.py or registration endpoint
async def register_user(credentials: RegistrationCredentials) -> User:
    """Register a new user with NIST-compliant password validation."""

    # Pydantic already validated basic constraints
    # Now validate against current security settings
    validation_result = await validate_new_password(
        password=credentials.password,
        username=credentials.username
    )

    if not validation_result["valid"]:
        raise HTTPException(
            status_code=400,
            detail="; ".join(validation_result["errors"])
        )

    # Show warnings but don't block
    for warning in validation_result.get("warnings", []):
        logger.warning("Password warning during registration",
                      username=credentials.username,
                      warning=warning)

    # Proceed with registration...
```

## Dependencies

- Task 03: `validate_password_nist()` must exist

## Acceptance Criteria

- [ ] Pydantic validator only checks length bounds (8-128)
- [ ] No hardcoded complexity requirements (uppercase, numbers, special)
- [ ] Unicode characters are allowed in passwords
- [ ] Passwords match validation remains
- [ ] Detailed validation happens at service layer
- [ ] Existing API contracts unchanged (errors still returned properly)

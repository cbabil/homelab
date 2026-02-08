"""
Authentication Data Models

Defines authentication and user management data models using Pydantic.
Matches frontend TypeScript interfaces for consistency.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr, Field, model_validator


class UserRole(str, Enum):
    """User role definitions."""

    ADMIN = "admin"
    USER = "user"


class TokenType(str, Enum):
    """Authentication token types."""

    JWT = "JWT"
    BEARER = "Bearer"


class User(BaseModel):
    """User model representing authenticated user data."""

    id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(
        ..., description="User email address"
    )  # Allow local domains for tomo
    role: UserRole = Field(default=UserRole.USER, description="User role")
    last_login: str = Field(..., description="Last login timestamp")
    password_changed_at: str | None = Field(
        None, description="Password last changed timestamp"
    )
    is_active: bool = Field(default=True, description="Account active status")
    preferences: dict[str, Any] | None = Field(None, description="User preferences")
    avatar: str | None = Field(None, description="User avatar as base64 data URL")
    created_at: str | None = Field(None, description="Account creation timestamp")
    updated_at: str | None = Field(None, description="Account last updated timestamp")


class LoginCredentials(BaseModel):
    """Login credentials for authentication."""

    username: str = Field(..., min_length=3, description="Username")
    password: str = Field(..., min_length=1, description="Password")
    remember_me: bool | None = Field(False, description="Remember login")


class RegistrationCredentials(BaseModel):
    """Registration credentials for new user creation.

    Password validation is done at the service layer using settings to support
    both NIST SP 800-63B-4 mode and legacy complexity mode.
    Basic length validation is kept here for safety.
    """

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    confirm_password: str = Field(..., description="Password confirmation")
    role: UserRole | None = Field(UserRole.USER, description="User role")
    accept_terms: bool = Field(..., description="Terms acceptance")

    # Note: Password length validation is handled by Field(min_length=8, max_length=128)
    # Complexity requirements are validated at service layer for NIST SP 800-63B-4 compliance
    # In NIST mode, complexity rules SHALL NOT be imposed

    @model_validator(mode="after")
    def passwords_match(self) -> "RegistrationCredentials":
        """Validate password confirmation matches."""
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class SessionActivity(BaseModel):
    """Session activity tracking."""

    last_activity: str = Field(..., description="Last activity timestamp")
    is_idle: bool = Field(..., description="Session idle status")
    idle_duration: int = Field(..., description="Idle duration in milliseconds")
    activity_count: int = Field(..., description="Activity event count")


class SessionWarning(BaseModel):
    """Session warning state."""

    is_showing: bool = Field(..., description="Warning display status")
    minutes_remaining: int = Field(..., description="Minutes until expiry")
    warning_level: str = Field(..., description="Warning severity level")


class AuthState(BaseModel):
    """Enhanced authentication state with session management."""

    user: User | None = Field(None, description="Authenticated user")
    is_authenticated: bool = Field(..., description="Authentication status")
    is_loading: bool = Field(..., description="Loading state")
    error: str | None = Field(None, description="Authentication error")
    session_expiry: str | None = Field(None, description="Session expiry time")
    activity: SessionActivity | None = Field(None, description="Session activity")
    warning: SessionWarning | None = Field(None, description="Session warning")
    token_type: TokenType | None = Field(None, description="Token type")
    token_expiry: str | None = Field(None, description="Token expiry time")


class LoginResponse(BaseModel):
    """Login response from authentication API."""

    user: User = Field(..., description="Authenticated user data")
    token: str = Field(..., description="Authentication token")
    refresh_token: str | None = Field(None, description="Refresh token")
    expires_in: int = Field(..., description="Token expiry time in seconds")
    session_id: str | None = Field(None, description="Session identifier")
    token_type: TokenType | None = Field(TokenType.JWT, description="Token type")

"""
Authentication Data Models

Defines authentication and user management data models using Pydantic.
Matches frontend TypeScript interfaces for consistency.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, model_validator


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
    email: EmailStr = Field(..., description="User email address")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    last_login: str = Field(..., description="Last login timestamp")
    is_active: bool = Field(default=True, description="Account active status")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")


class LoginCredentials(BaseModel):
    """Login credentials for authentication."""
    username: str = Field(..., min_length=3, description="Username")
    password: str = Field(..., min_length=1, description="Password")
    remember_me: Optional[bool] = Field(False, description="Remember login")


class RegistrationCredentials(BaseModel):
    """Registration credentials for new user creation."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=12, description="Password")
    confirm_password: str = Field(..., description="Password confirmation")
    role: Optional[UserRole] = Field(UserRole.USER, description="User role")
    accept_terms: bool = Field(..., description="Terms acceptance")

    @model_validator(mode="after")
    def passwords_match(cls, values: "RegistrationCredentials") -> "RegistrationCredentials":
        """Validate password confirmation matches."""
        if values.password != values.confirm_password:
            raise ValueError('Passwords do not match')
        return values


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
    user: Optional[User] = Field(None, description="Authenticated user")
    is_authenticated: bool = Field(..., description="Authentication status")
    is_loading: bool = Field(..., description="Loading state")
    error: Optional[str] = Field(None, description="Authentication error")
    session_expiry: Optional[str] = Field(None, description="Session expiry time")
    activity: Optional[SessionActivity] = Field(None, description="Session activity")
    warning: Optional[SessionWarning] = Field(None, description="Session warning")
    token_type: Optional[TokenType] = Field(None, description="Token type")
    token_expiry: Optional[str] = Field(None, description="Token expiry time")


class LoginResponse(BaseModel):
    """Login response from authentication API."""
    user: User = Field(..., description="Authenticated user data")
    token: str = Field(..., description="Authentication token")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    expires_in: int = Field(..., description="Token expiry time in seconds")
    session_id: Optional[str] = Field(None, description="Session identifier")
    token_type: Optional[TokenType] = Field(TokenType.JWT, description="Token type")

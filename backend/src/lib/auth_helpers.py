"""
Authentication Helper Utilities

Provides utility functions for password hashing, JWT operations, and user management.
Supports secure authentication operations for the tomo system.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
import structlog

from models.auth import User

logger = structlog.get_logger("auth_helpers")

# bcrypt cost factor - must match CLI (cli/src/lib/admin.ts)
BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """Hash password using bcrypt, return as string for database storage."""
    hashed_bytes = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    )
    return hashed_bytes.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash. Handle both string and bytes formats."""
    if isinstance(hashed, str):
        hashed_bytes = hashed.encode("utf-8")
    else:
        hashed_bytes = hashed
    return bcrypt.checkpw(password.encode("utf-8"), hashed_bytes)


def generate_jwt_token(
    user: User,
    secret: str,
    algorithm: str = "HS256",
    expiry_hours: int = 24,
    session_id: str | None = None,
) -> str:
    """Generate JWT token for user.

    Args:
        user: User object to generate token for.
        secret: JWT secret key.
        algorithm: JWT signing algorithm.
        expiry_hours: Token expiry in hours.
        session_id: Optional session ID to bind token to.
    """
    payload = {
        "jti": str(uuid.uuid4()),
        "user_id": user.id,
        "username": user.username,
        "role": user.role.value,
        "exp": datetime.now(UTC) + timedelta(hours=expiry_hours),
        "iat": datetime.now(UTC),
        "iss": "tomo",
    }
    if session_id:
        payload["session_id"] = session_id

    return jwt.encode(payload, secret, algorithm=algorithm)


def validate_jwt_token(
    token: str, secret: str, algorithm: str = "HS256"
) -> dict[str, Any] | None:
    """Validate and decode JWT token."""
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        return None


def create_session_data(user_id: str, expiry_hours: int = 24) -> dict[str, Any]:
    """Create session data dictionary."""
    return {
        "user_id": user_id,
        "created_at": datetime.now(UTC).isoformat(),
        "last_activity": datetime.now(UTC).isoformat(),
        "expires_at": (datetime.now(UTC) + timedelta(hours=expiry_hours)).isoformat(),
    }


def generate_session_id() -> str:
    """Generate unique session identifier."""
    return str(uuid.uuid4())

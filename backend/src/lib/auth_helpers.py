"""
Authentication Helper Utilities

Provides utility functions for password hashing, JWT operations, and user management.
Supports secure authentication operations for the homelab system.
"""

import jwt
import bcrypt
import uuid
from datetime import UTC, datetime, timedelta
from typing import Dict, Any, Optional
import structlog
from models.auth import User, UserRole


logger = structlog.get_logger("auth_helpers")


def hash_password(password: str) -> str:
    """Hash password using bcrypt, return as string for database storage."""
    hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed_bytes.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash. Handle both string and bytes formats."""
    if isinstance(hashed, str):
        hashed_bytes = hashed.encode("utf-8")
    else:
        hashed_bytes = hashed
    return bcrypt.checkpw(password.encode("utf-8"), hashed_bytes)


def generate_jwt_token(user: User, secret: str, algorithm: str = "HS256", 
                      expiry_hours: int = 24) -> str:
    """Generate JWT token for user."""
    payload = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role.value,
        "exp": datetime.now(UTC) + timedelta(hours=expiry_hours),
        "iat": datetime.now(UTC),
        "iss": "homelab-assistant"
    }
    
    return jwt.encode(payload, secret, algorithm=algorithm)


def validate_jwt_token(token: str, secret: str, algorithm: str = "HS256") -> Optional[Dict[str, Any]]:
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


def create_session_data(user_id: str, expiry_hours: int = 24) -> Dict[str, Any]:
    """Create session data dictionary."""
    return {
        "user_id": user_id,
        "created_at": datetime.now(UTC).isoformat(),
        "last_activity": datetime.now(UTC).isoformat(),
        "expires_at": (datetime.now(UTC) + timedelta(hours=expiry_hours)).isoformat()
    }


def generate_session_id() -> str:
    """Generate unique session identifier."""
    return str(uuid.uuid4())


def create_default_admin() -> User:
    """Create default admin user for initial access."""
    return User(
        id=str(uuid.uuid4()),
        username="admin",
        email="admin@homelab.dev",
        role=UserRole.ADMIN,
        last_login=datetime.now(UTC).isoformat(),
        is_active=True,
        preferences={
            "theme": "dark",
            "language": "en",
            "notifications": True
        }
    )
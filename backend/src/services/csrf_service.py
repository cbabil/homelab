"""
CSRF Protection Service

Provides CSRF token generation and validation for destructive operations.
Tokens are stored server-side with user session association and expiration.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import structlog

logger = structlog.get_logger("csrf_service")

# In-memory token storage (in production, use Redis or database)
# Format: { token_hash: { user_id, session_id, expires_at, used } }
_csrf_tokens: dict[str, dict] = {}

# Token configuration
TOKEN_LENGTH = 64  # 64 hex chars = 256 bits of entropy
TOKEN_EXPIRY_MINUTES = 60  # 1 hour
MAX_TOKENS_PER_USER = 5


class CSRFService:
    """Service for CSRF token management."""

    def __init__(self):
        """Initialize CSRF service."""
        logger.info("CSRF service initialized")

    def _hash_token(self, token: str) -> str:
        """Hash a token for storage comparison."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _cleanup_expired_tokens(self):
        """Remove expired tokens from storage."""
        now = datetime.now(UTC)
        expired_keys = [
            key
            for key, data in _csrf_tokens.items()
            if datetime.fromisoformat(data["expires_at"]) < now
        ]
        for key in expired_keys:
            del _csrf_tokens[key]

        if expired_keys:
            logger.debug("Cleaned up expired CSRF tokens", count=len(expired_keys))

    def _cleanup_user_tokens(self, user_id: str):
        """Limit tokens per user to prevent memory exhaustion."""
        user_tokens = [
            (key, data)
            for key, data in _csrf_tokens.items()
            if data["user_id"] == user_id
        ]

        # Sort by creation time (newest first based on expiry)
        user_tokens.sort(key=lambda x: x[1]["expires_at"], reverse=True)

        # Remove oldest tokens if over limit
        if len(user_tokens) > MAX_TOKENS_PER_USER:
            for key, _ in user_tokens[MAX_TOKENS_PER_USER:]:
                del _csrf_tokens[key]
            logger.debug("Cleaned up excess user tokens", user_id=user_id)

    def generate_token(self, user_id: str, session_id: str) -> str:
        """Generate a new CSRF token for a user session.

        Args:
            user_id: User ID requesting the token.
            session_id: Current session ID.

        Returns:
            New CSRF token.
        """
        self._cleanup_expired_tokens()
        self._cleanup_user_tokens(user_id)

        # Generate cryptographically secure token
        token = secrets.token_hex(TOKEN_LENGTH // 2)
        token_hash = self._hash_token(token)

        # Store token metadata
        expires_at = datetime.now(UTC) + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
        _csrf_tokens[token_hash] = {
            "user_id": user_id,
            "session_id": session_id,
            "expires_at": expires_at.isoformat(),
            "used": False,
        }

        logger.info(
            "CSRF token generated",
            user_id=user_id,
            expires_in_minutes=TOKEN_EXPIRY_MINUTES,
        )
        return token

    def validate_token(
        self, token: str, user_id: str, session_id: str, consume: bool = True
    ) -> tuple[bool, str | None]:
        """Validate a CSRF token.

        Args:
            token: CSRF token to validate.
            user_id: Expected user ID.
            session_id: Expected session ID.
            consume: Whether to consume (invalidate) the token on successful validation.

        Returns:
            Tuple of (is_valid, error_message).
        """
        self._cleanup_expired_tokens()

        if not token or len(token) < 32:
            logger.warning("Invalid CSRF token format", user_id=user_id)
            return False, "Invalid token format"

        token_hash = self._hash_token(token)
        token_data = _csrf_tokens.get(token_hash)

        if not token_data:
            logger.warning("CSRF token not found", user_id=user_id)
            return False, "Token not found or expired"

        # Check expiration
        if datetime.fromisoformat(token_data["expires_at"]) < datetime.now(UTC):
            del _csrf_tokens[token_hash]
            logger.warning("CSRF token expired", user_id=user_id)
            return False, "Token expired"

        # Check if already used (for single-use tokens)
        if token_data["used"]:
            logger.warning("CSRF token already used", user_id=user_id)
            return False, "Token already used"

        # Verify user and session match
        if token_data["user_id"] != user_id:
            logger.warning(
                "CSRF token user mismatch",
                expected=token_data["user_id"],
                actual=user_id,
            )
            return False, "Token does not belong to this user"

        if token_data["session_id"] != session_id:
            logger.warning("CSRF token session mismatch", user_id=user_id)
            return False, "Token does not belong to this session"

        # Mark as used if consuming
        if consume:
            _csrf_tokens[token_hash]["used"] = True
            logger.info("CSRF token validated and consumed", user_id=user_id)
        else:
            logger.info("CSRF token validated (not consumed)", user_id=user_id)

        return True, None

    def revoke_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user (e.g., on logout).

        Args:
            user_id: User ID whose tokens to revoke.

        Returns:
            Number of tokens revoked.
        """
        keys_to_delete = [
            key for key, data in _csrf_tokens.items() if data["user_id"] == user_id
        ]

        for key in keys_to_delete:
            del _csrf_tokens[key]

        if keys_to_delete:
            logger.info(
                "User CSRF tokens revoked", user_id=user_id, count=len(keys_to_delete)
            )

        return len(keys_to_delete)


# Singleton instance
csrf_service = CSRFService()

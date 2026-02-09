"""
CSRF Protection Service

Provides CSRF token generation and validation for destructive operations.
Tokens are persisted to database so they survive server restarts.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import structlog

from services.database_service import DatabaseService

logger = structlog.get_logger("csrf_service")

# Token configuration
TOKEN_LENGTH = 64  # 64 hex chars = 256 bits of entropy
TOKEN_EXPIRY_MINUTES = 60  # 1 hour
MAX_TOKENS_PER_USER = 5


class CSRFService:
    """Service for CSRF token management with database persistence."""

    def __init__(self, db_service: DatabaseService | None = None):
        """Initialize CSRF service.

        Args:
            db_service: Database service for persistent storage.
        """
        self.db_service = db_service
        logger.info("CSRF service initialized", persistent=db_service is not None)

    def _hash_token(self, token: str) -> str:
        """Hash a token for storage comparison."""
        return hashlib.sha256(token.encode()).hexdigest()

    async def _cleanup_expired_tokens(self) -> None:
        """Remove expired tokens from database."""
        if not self.db_service:
            return

        now = datetime.now(UTC).isoformat()
        async with self.db_service.get_connection() as conn:
            cursor = await conn.execute(
                "DELETE FROM csrf_tokens WHERE expires_at < ?", (now,)
            )
            await conn.commit()
            count = cursor.rowcount

        if count > 0:
            logger.debug("Cleaned up expired CSRF tokens", count=count)

    async def _cleanup_user_tokens(self, user_id: str) -> None:
        """Limit tokens per user to prevent exhaustion."""
        if not self.db_service:
            return

        async with self.db_service.get_connection() as conn:
            # Count tokens for user
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM csrf_tokens WHERE user_id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
            count = row[0] if row else 0

            if count >= MAX_TOKENS_PER_USER:
                # Delete oldest tokens, keeping only the newest ones
                await conn.execute(
                    """DELETE FROM csrf_tokens WHERE token_hash IN (
                        SELECT token_hash FROM csrf_tokens
                        WHERE user_id = ?
                        ORDER BY created_at ASC
                        LIMIT ?
                    )""",
                    (user_id, count - MAX_TOKENS_PER_USER + 1),
                )
                await conn.commit()
                logger.debug("Cleaned up excess user tokens", user_id=user_id)

    async def generate_token(self, user_id: str, session_id: str) -> str:
        """Generate a new CSRF token for a user session.

        Args:
            user_id: User ID requesting the token.
            session_id: Current session ID.

        Returns:
            New CSRF token.
        """
        await self._cleanup_expired_tokens()
        await self._cleanup_user_tokens(user_id)

        # Generate cryptographically secure token
        token = secrets.token_hex(TOKEN_LENGTH // 2)
        token_hash = self._hash_token(token)

        # Store token in database
        expires_at = datetime.now(UTC) + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
        now = datetime.now(UTC).isoformat()

        if self.db_service:
            async with self.db_service.get_connection() as conn:
                await conn.execute(
                    """INSERT INTO csrf_tokens
                    (token_hash, user_id, session_id, expires_at, used, created_at)
                    VALUES (?, ?, ?, ?, 0, ?)""",
                    (token_hash, user_id, session_id, expires_at.isoformat(), now),
                )
                await conn.commit()

        logger.info(
            "CSRF token generated",
            user_id=user_id,
            expires_in_minutes=TOKEN_EXPIRY_MINUTES,
        )
        return token

    async def validate_token(
        self, token: str, user_id: str, session_id: str, consume: bool = True
    ) -> tuple[bool, str | None]:
        """Validate a CSRF token.

        Args:
            token: CSRF token to validate.
            user_id: Expected user ID.
            session_id: Expected session ID.
            consume: Whether to consume the token on successful validation.

        Returns:
            Tuple of (is_valid, error_message).
        """
        await self._cleanup_expired_tokens()

        if not token or len(token) < 32:
            logger.warning("Invalid CSRF token format", user_id=user_id)
            return False, "Invalid token format"

        if not self.db_service:
            logger.warning("CSRF service has no database", user_id=user_id)
            return False, "Token storage unavailable"

        token_hash = self._hash_token(token)

        async with self.db_service.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT user_id, session_id, expires_at, used "
                "FROM csrf_tokens WHERE token_hash = ?",
                (token_hash,),
            )
            row = await cursor.fetchone()

        if not row:
            logger.warning("CSRF token not found", user_id=user_id)
            return False, "Token not found or expired"

        db_user_id, db_session_id, db_expires_at, db_used = row

        # Check expiration
        if datetime.fromisoformat(db_expires_at) < datetime.now(UTC):
            async with self.db_service.get_connection() as conn:
                await conn.execute(
                    "DELETE FROM csrf_tokens WHERE token_hash = ?",
                    (token_hash,),
                )
                await conn.commit()
            logger.warning("CSRF token expired", user_id=user_id)
            return False, "Token expired"

        # Check if already used
        if db_used:
            logger.warning("CSRF token already used", user_id=user_id)
            return False, "Token already used"

        # Verify user and session match
        if db_user_id != user_id:
            logger.warning(
                "CSRF token user mismatch",
                expected=db_user_id,
                actual=user_id,
            )
            return False, "Token does not belong to this user"

        if db_session_id != session_id:
            logger.warning("CSRF token session mismatch", user_id=user_id)
            return False, "Token does not belong to this session"

        # Mark as used if consuming
        if consume:
            async with self.db_service.get_connection() as conn:
                await conn.execute(
                    "UPDATE csrf_tokens SET used = 1 WHERE token_hash = ?",
                    (token_hash,),
                )
                await conn.commit()
            logger.info("CSRF token validated and consumed", user_id=user_id)
        else:
            logger.info("CSRF token validated (not consumed)", user_id=user_id)

        return True, None

    async def revoke_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user (e.g., on logout).

        Args:
            user_id: User ID whose tokens to revoke.

        Returns:
            Number of tokens revoked.
        """
        if not self.db_service:
            return 0

        async with self.db_service.get_connection() as conn:
            cursor = await conn.execute(
                "DELETE FROM csrf_tokens WHERE user_id = ?", (user_id,)
            )
            await conn.commit()
            count = cursor.rowcount

        if count > 0:
            logger.info(
                "User CSRF tokens revoked", user_id=user_id, count=count
            )

        return count

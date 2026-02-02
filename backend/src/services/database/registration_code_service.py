"""Registration Code Database Service.

Database operations for agent registration codes.
"""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Optional
from uuid import uuid4

import structlog

from models.agent import RegistrationCode

from .base import DatabaseConnection

logger = structlog.get_logger("database.registration_code")


def constant_time_compare(val1: str, val2: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks.

    Args:
        val1: First string.
        val2: Second string.

    Returns:
        True if strings are equal, False otherwise.
    """
    return hmac.compare_digest(val1.encode(), val2.encode())


def hash_code(code: str) -> str:
    """Create a hash of the registration code for secure storage.

    Args:
        code: Registration code.

    Returns:
        SHA-256 hash of the code.
    """
    # Normalize: remove dashes and convert to uppercase
    normalized = code.replace("-", "").upper()
    return hashlib.sha256(normalized.encode()).hexdigest()


class RegistrationCodeDatabaseService:
    """Database operations for agent registration codes."""

    def __init__(self, connection: DatabaseConnection):
        """Initialize with database connection.

        Args:
            connection: DatabaseConnection instance.
        """
        self._conn = connection

    async def create(self, agent_id: str, expiry_minutes: int = 5) -> RegistrationCode:
        """Create a registration code for an agent.

        Args:
            agent_id: Agent identifier to associate with code.
            expiry_minutes: Minutes until code expires (default 5).

        Returns:
            Created RegistrationCode model.
        """
        code_id = str(uuid4())
        # Use 8 bytes (64 bits of entropy) for security against brute force
        # Format: XXXX-XXXX-XXXX-XXXX (16 hex chars with dashes for readability)
        raw_code = secrets.token_hex(8).upper()
        code = f"{raw_code[:4]}-{raw_code[4:8]}-{raw_code[8:12]}-{raw_code[12:]}"
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=expiry_minutes)

        async with self._conn.get_connection() as conn:
            await conn.execute(
                """INSERT INTO agent_registration_codes
                   (id, agent_id, code, expires_at, used, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    code_id,
                    agent_id,
                    code,
                    expires_at.isoformat(),
                    False,
                    now.isoformat(),
                ),
            )
            await conn.commit()

        logger.info(
            "Registration code created",
            code_id=code_id,
            agent_id=agent_id,
            expires_at=expires_at.isoformat(),
        )

        return RegistrationCode(
            id=code_id,
            agent_id=agent_id,
            code=code,
            expires_at=expires_at,
            used=False,
            created_at=now,
        )

    async def get_by_code(self, code: str) -> Optional[RegistrationCode]:
        """Get a registration code by its value.

        Args:
            code: Registration code string.

        Returns:
            RegistrationCode model or None if not found.
        """
        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM agent_registration_codes WHERE code = ?", (code,)
            )
            row = await cursor.fetchone()

        if not row:
            return None

        return RegistrationCode(
            id=row["id"],
            agent_id=row["agent_id"],
            code=row["code"],
            expires_at=datetime.fromisoformat(row["expires_at"]),
            used=bool(row["used"]),
            created_at=(
                datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
            ),
        )

    async def mark_used(self, code_id: str) -> None:
        """Mark a registration code as used.

        Args:
            code_id: Registration code identifier.
        """
        async with self._conn.get_connection() as conn:
            await conn.execute(
                "UPDATE agent_registration_codes SET used = ? WHERE id = ?",
                (True, code_id),
            )
            await conn.commit()

        logger.info("Registration code marked as used", code_id=code_id)

    async def cleanup_expired(self) -> int:
        """Delete expired registration codes.

        Returns:
            Number of codes deleted.
        """
        now = datetime.now(UTC).isoformat()

        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                "DELETE FROM agent_registration_codes WHERE expires_at < ?", (now,)
            )
            await conn.commit()
            deleted_count = cursor.rowcount

        if deleted_count > 0:
            logger.info("Expired registration codes cleaned up", count=deleted_count)

        return deleted_count

    async def delete_by_agent(self, agent_id: str) -> int:
        """Delete all registration codes for an agent.

        Args:
            agent_id: Agent identifier.

        Returns:
            Number of codes deleted.
        """
        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                "DELETE FROM agent_registration_codes WHERE agent_id = ?", (agent_id,)
            )
            await conn.commit()

        return cursor.rowcount

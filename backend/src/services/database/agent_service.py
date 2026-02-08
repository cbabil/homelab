"""Agent Database Service.

Database operations for agents and registration codes.
"""

import json
from datetime import UTC, datetime
from uuid import uuid4

import structlog

from models.agent import (
    Agent,
    AgentConfig,
    AgentCreate,
    AgentStatus,
    AgentUpdate,
    RegistrationCode,
)

from .base import ALLOWED_AGENT_COLUMNS, DatabaseConnection
from .registration_code_service import RegistrationCodeDatabaseService

logger = structlog.get_logger("database.agent")


class AgentDatabaseService:
    """Database operations for agent management."""

    def __init__(self, connection: DatabaseConnection):
        """Initialize with database connection.

        Args:
            connection: DatabaseConnection instance.
        """
        self._conn = connection
        self._registration_codes = RegistrationCodeDatabaseService(connection)

    def _row_to_agent(self, row) -> Agent:
        """Convert database row to Agent model."""
        config = None
        if row["config"]:
            try:
                config_data = json.loads(row["config"])
                config = AgentConfig(**config_data)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to parse agent config", agent_id=row["id"])

        # Handle token rotation fields (may not exist in older schemas)
        pending_token_hash = (
            row["pending_token_hash"] if "pending_token_hash" in row else None
        )
        token_issued_at = None
        token_expires_at = None
        if "token_issued_at" in row and row["token_issued_at"]:
            token_issued_at = datetime.fromisoformat(row["token_issued_at"])
        if "token_expires_at" in row and row["token_expires_at"]:
            token_expires_at = datetime.fromisoformat(row["token_expires_at"])

        return Agent(
            id=row["id"],
            server_id=row["server_id"],
            token_hash=row["token_hash"],
            version=row["version"],
            status=AgentStatus(row["status"]) if row["status"] else AgentStatus.PENDING,
            last_seen=datetime.fromisoformat(row["last_seen"])
            if row["last_seen"]
            else None,
            registered_at=datetime.fromisoformat(row["registered_at"])
            if row["registered_at"]
            else None,
            config=config,
            created_at=datetime.fromisoformat(row["created_at"])
            if row["created_at"]
            else None,
            updated_at=datetime.fromisoformat(row["updated_at"])
            if row["updated_at"]
            else None,
            pending_token_hash=pending_token_hash,
            token_issued_at=token_issued_at,
            token_expires_at=token_expires_at,
        )

    async def create_agent(self, data: AgentCreate) -> Agent:
        """Create a new agent record."""
        agent_id = str(uuid4())
        now = datetime.now(UTC).isoformat()

        async with self._conn.get_connection() as conn:
            await conn.execute(
                """INSERT INTO agents
                   (id, server_id, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (agent_id, data.server_id, AgentStatus.PENDING.value, now, now),
            )
            await conn.commit()

            cursor = await conn.execute(
                "SELECT * FROM agents WHERE id = ?", (agent_id,)
            )
            row = await cursor.fetchone()

        logger.info("Agent created", agent_id=agent_id, server_id=data.server_id)
        return self._row_to_agent(row)

    async def get_agent(self, agent_id: str) -> Agent | None:
        """Get agent by ID."""
        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM agents WHERE id = ?", (agent_id,)
            )
            row = await cursor.fetchone()

        return self._row_to_agent(row) if row else None

    async def get_agent_by_server(self, server_id: str) -> Agent | None:
        """Get agent by associated server ID."""
        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM agents WHERE server_id = ?", (server_id,)
            )
            row = await cursor.fetchone()

        return self._row_to_agent(row) if row else None

    async def list_all_agents(self) -> list[Agent]:
        """List all agents."""
        async with self._conn.get_connection() as conn:
            cursor = await conn.execute("SELECT * FROM agents ORDER BY created_at DESC")
            rows = await cursor.fetchall()

        return [self._row_to_agent(row) for row in rows]

    async def get_agent_by_token_hash(self, token_hash: str) -> Agent | None:
        """Get agent by authentication token hash."""
        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM agents WHERE token_hash = ?", (token_hash,)
            )
            row = await cursor.fetchone()

        return self._row_to_agent(row) if row else None

    async def get_agent_by_pending_token_hash(self, token_hash: str) -> Agent | None:
        """Get agent by pending token hash (during rotation)."""
        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM agents WHERE pending_token_hash = ?", (token_hash,)
            )
            row = await cursor.fetchone()

        return self._row_to_agent(row) if row else None

    async def get_agents_with_expiring_tokens(self, before: datetime) -> list[Agent]:
        """Get agents whose tokens expire before the given datetime.

        Used by the rotation scheduler to find agents needing token rotation.

        Args:
            before: Find agents with token_expires_at before this time.

        Returns:
            List of agents needing token rotation.
        """
        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                """SELECT * FROM agents
                   WHERE token_expires_at IS NOT NULL
                   AND token_expires_at < ?
                   AND token_hash IS NOT NULL
                   AND pending_token_hash IS NULL
                   ORDER BY token_expires_at ASC""",
                (before.isoformat(),),
            )
            rows = await cursor.fetchall()

        return [self._row_to_agent(row) for row in rows]

    async def update_agent(self, agent_id: str, data: AgentUpdate) -> Agent | None:
        """Update an agent record."""
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            return await self.get_agent(agent_id)

        # Validate columns against whitelist (SQL injection prevention)
        invalid = set(updates.keys()) - ALLOWED_AGENT_COLUMNS
        if invalid:
            logger.warning(
                "Rejected invalid agent update columns",
                agent_id=agent_id,
                invalid_columns=sorted(invalid),
            )
            raise ValueError(f"Invalid update columns: {sorted(invalid)}")

        updates["updated_at"] = datetime.now(UTC).isoformat()
        self._serialize_update_fields(updates)

        set_clause = ", ".join(f"{key} = ?" for key in updates)
        values = list(updates.values()) + [agent_id]

        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                f"UPDATE agents SET {set_clause} WHERE id = ?",  # noqa: S608
                values,
            )
            await conn.commit()

            if cursor.rowcount == 0:
                logger.warning("Agent not found for update", agent_id=agent_id)
                return None

            cursor = await conn.execute(
                "SELECT * FROM agents WHERE id = ?", (agent_id,)
            )
            row = await cursor.fetchone()

        logger.info("Agent updated", agent_id=agent_id, fields=list(updates.keys()))
        return self._row_to_agent(row)

    def _serialize_update_fields(self, updates: dict) -> None:
        """Serialize special fields for database storage."""
        if "status" in updates and updates["status"] is not None:
            status = updates["status"]
            if hasattr(status, "value"):
                updates["status"] = status.value
            # else it's already a string
        if "config" in updates and updates["config"] is not None:
            config = updates["config"]
            if isinstance(config, dict):
                updates["config"] = json.dumps(config)
            elif hasattr(config, "model_dump_json"):
                updates["config"] = config.model_dump_json()
            elif isinstance(config, str):
                pass  # already a JSON string

        # Serialize datetime fields
        datetime_fields = [
            "last_seen",
            "registered_at",
            "token_issued_at",
            "token_expires_at",
        ]
        for field in datetime_fields:
            if field in updates and updates[field] is not None:
                value = updates[field]
                if hasattr(value, "isoformat"):
                    updates[field] = value.isoformat()

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent record."""
        async with self._conn.get_connection() as conn:
            await conn.execute(
                "DELETE FROM agent_registration_codes WHERE agent_id = ?", (agent_id,)
            )
            cursor = await conn.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
            await conn.commit()

            if cursor.rowcount == 0:
                logger.warning("Agent not found for deletion", agent_id=agent_id)
                return False

        logger.info("Agent deleted", agent_id=agent_id)
        return True

    async def create_registration_code(
        self, agent_id: str, expiry_minutes: int = 5
    ) -> RegistrationCode:
        """Create a registration code for an agent."""
        return await self._registration_codes.create(agent_id, expiry_minutes)

    async def get_registration_code(self, code: str) -> RegistrationCode | None:
        """Get a registration code by its value."""
        return await self._registration_codes.get_by_code(code)

    async def mark_code_used(self, code_id: str) -> None:
        """Mark a registration code as used."""
        await self._registration_codes.mark_used(code_id)

    async def cleanup_expired_codes(self) -> int:
        """Delete expired registration codes."""
        return await self._registration_codes.cleanup_expired()

"""
Agent Token Rotation

Handles token rotation lifecycle: initiation, completion, cancellation,
expiry checking, and automatic rotation scheduling.
"""

import asyncio
import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import structlog

if TYPE_CHECKING:
    from services.database import AgentDatabaseService
    from services.settings_service import SettingsService

from models.agent import Agent, AgentUpdate

logger = structlog.get_logger("agent_rotation")


@runtime_checkable
class _AgentServiceProtocol(Protocol):
    """Interface that the host class must provide for AgentRotationMixin."""

    settings_service: "SettingsService"

    def get_agent_db(self) -> "AgentDatabaseService": ...

    def _hash_token(self, token: str) -> str: ...

    async def _get_server_name(self, server_id: str) -> str: ...

    async def _log_agent_event(
        self,
        event_type: str,
        level: str,
        message: str,
        server_id: str,
        server_name: str = "",
        agent_id: str = "",
        success: bool = True,
        details: dict = None,
    ) -> None: ...

    async def get_token_rotation_settings(self) -> tuple[int, int]: ...


class AgentRotationMixin:
    """Mixin providing token rotation methods for AgentService.

    The host class must satisfy ``_AgentServiceProtocol``.
    """

    def _init_rotation_state(self) -> None:
        """Initialize rotation scheduler state. Call from __init__."""
        self._rotation_task: asyncio.Task | None = None
        self._rotation_running = False
        self._rotation_check_interval = 3600  # Default: 1 hour
        self._rotation_callback: Callable | None = None

    async def initiate_rotation(
        self: _AgentServiceProtocol, agent_id: str
    ) -> str | None:
        """Initiate token rotation by generating a pending token.

        Creates a new token and stores its hash in pending_token_hash.
        The agent can then use either the current or pending token.
        Rotation completes when agent uses the new token or manually.

        Args:
            agent_id: Agent identifier to rotate token for.

        Returns:
            New token (plaintext) if successful, None otherwise.
        """
        agent_db = self.get_agent_db()
        agent = await agent_db.get_agent(agent_id)

        if not agent:
            logger.warning("Rotation failed: agent not found", agent_id=agent_id)
            return None

        if not agent.token_hash:
            logger.warning("Rotation failed: agent has no token", agent_id=agent_id)
            return None

        if agent.pending_token_hash:
            logger.warning(
                "Rotation already in progress",
                agent_id=agent_id,
            )
            return None

        # Generate new token
        new_token = secrets.token_urlsafe(32)
        pending_hash = self._hash_token(new_token)

        update_data = AgentUpdate(pending_token_hash=pending_hash)
        await agent_db.update_agent(agent_id, update_data)

        logger.info("Token rotation initiated", agent_id=agent_id)

        server_name = await self._get_server_name(agent.server_id)
        await self._log_agent_event(
            event_type="AGENT_TOKEN_ROTATION_STARTED",
            level="INFO",
            message=f"Token rotation initiated for agent on {server_name}",
            server_id=agent.server_id,
            server_name=server_name,
            agent_id=agent_id,
            success=True,
        )

        return new_token

    async def complete_rotation(self: _AgentServiceProtocol, agent_id: str) -> bool:
        """Complete token rotation by promoting pending token to current.

        Called when agent acknowledges rotation or uses the new token.
        Sets new expiry based on rotation settings.

        Args:
            agent_id: Agent identifier.

        Returns:
            True if rotation completed, False otherwise.
        """
        agent_db = self.get_agent_db()
        agent = await agent_db.get_agent(agent_id)

        if not agent:
            logger.warning(
                "Complete rotation failed: agent not found", agent_id=agent_id
            )
            return False

        if not agent.pending_token_hash:
            logger.warning(
                "Complete rotation failed: no pending token", agent_id=agent_id
            )
            return False

        # Get rotation settings for new expiry
        rotation_days, _ = await self.get_token_rotation_settings()
        now = datetime.now(UTC)
        new_expires_at = now + timedelta(days=rotation_days)

        # Promote pending to current
        update_data = AgentUpdate(
            token_hash=agent.pending_token_hash,
            pending_token_hash=None,
            token_issued_at=now,
            token_expires_at=new_expires_at,
        )
        await agent_db.update_agent(agent_id, update_data)

        logger.info(
            "Token rotation completed",
            agent_id=agent_id,
            expires_at=new_expires_at.isoformat(),
        )

        server_name = await self._get_server_name(agent.server_id)
        await self._log_agent_event(
            event_type="AGENT_TOKEN_ROTATION_COMPLETED",
            level="INFO",
            message=f"Token rotation completed for agent on {server_name}",
            server_id=agent.server_id,
            server_name=server_name,
            agent_id=agent_id,
            success=True,
        )

        return True

    async def cancel_rotation(self: _AgentServiceProtocol, agent_id: str) -> bool:
        """Cancel pending token rotation.

        Called when rotation fails or times out. Clears pending_token_hash
        without affecting the current token.

        Args:
            agent_id: Agent identifier.

        Returns:
            True if cancellation successful, False otherwise.
        """
        agent_db = self.get_agent_db()
        agent = await agent_db.get_agent(agent_id)

        if not agent:
            logger.warning("Cancel rotation failed: agent not found", agent_id=agent_id)
            return False

        update_data = AgentUpdate(pending_token_hash=None)
        await agent_db.update_agent(agent_id, update_data)

        logger.warning("Token rotation cancelled", agent_id=agent_id)

        server_name = await self._get_server_name(agent.server_id)
        await self._log_agent_event(
            event_type="AGENT_TOKEN_ROTATION_CANCELLED",
            level="WARNING",
            message=f"Token rotation cancelled for agent on {server_name}",
            server_id=agent.server_id,
            server_name=server_name,
            agent_id=agent_id,
            success=False,
        )

        return True

    async def get_agents_needing_rotation(
        self: _AgentServiceProtocol,
    ) -> list[Agent]:
        """Get agents whose tokens have expired and need rotation.

        Returns:
            List of agents with expired tokens (no pending rotation in progress).
        """
        agent_db = self.get_agent_db()
        now = datetime.now(UTC)
        return await agent_db.get_agents_with_expiring_tokens(now)

    # -------------------------------------------------------------------------
    # Automatic Token Rotation Scheduler
    # -------------------------------------------------------------------------

    def set_rotation_callback(self, callback: Callable) -> None:
        """Set the callback function to execute rotation for an agent.

        The callback should be an async function that takes (agent_id, new_token,
        grace_period_seconds) and sends the rotation request to the agent.

        Args:
            callback: Async function to send rotation to agent.
        """
        self._rotation_callback = callback
        logger.debug("Rotation callback set")

    async def start_rotation_scheduler(
        self,
        check_interval: int = 3600,
    ) -> None:
        """Start the automatic token rotation scheduler.

        Periodically checks for agents with expired tokens and initiates rotation.

        Args:
            check_interval: Seconds between rotation checks (default: 1 hour).
        """
        if self._rotation_running:
            logger.warning("Rotation scheduler already running")
            return

        self._rotation_check_interval = check_interval
        self._rotation_running = True
        self._rotation_task = asyncio.create_task(self._rotation_scheduler_loop())
        logger.info(
            "Rotation scheduler started",
            check_interval_seconds=check_interval,
        )

    async def stop_rotation_scheduler(self) -> None:
        """Stop the automatic token rotation scheduler."""
        self._rotation_running = False

        if self._rotation_task:
            self._rotation_task.cancel()
            try:
                await self._rotation_task
            except asyncio.CancelledError:
                pass
            self._rotation_task = None

        logger.info("Rotation scheduler stopped")

    async def _rotation_scheduler_loop(self) -> None:
        """Background loop that periodically checks for token expiry."""
        while self._rotation_running:
            try:
                await self.check_token_expiry()
            except Exception as e:
                logger.error("Rotation check failed", error=str(e))

            # Sleep until next check
            try:
                await asyncio.sleep(self._rotation_check_interval)
            except asyncio.CancelledError:
                break

    async def check_token_expiry(self: _AgentServiceProtocol) -> int:
        """Check for agents needing token rotation and initiate rotation.

        This is called periodically by the scheduler or can be called manually.

        Returns:
            Number of agents for which rotation was initiated.
        """
        agents = await self.get_agents_needing_rotation()

        if not agents:
            logger.debug("No agents need token rotation")
            return 0

        rotated_count = 0
        _, grace_minutes = await self.get_token_rotation_settings()
        grace_seconds = grace_minutes * 60

        for agent in agents:
            try:
                # Skip if no callback set (can't send to agent)
                if not self._rotation_callback:
                    logger.warning(
                        "No rotation callback set, skipping agent",
                        agent_id=agent.id,
                    )
                    continue

                # Initiate rotation
                new_token = await self.initiate_rotation(agent.id)
                if not new_token:
                    logger.error(
                        "Failed to initiate rotation",
                        agent_id=agent.id,
                    )
                    continue

                # Send to agent via callback
                try:
                    success = await self._rotation_callback(
                        agent.id, new_token, grace_seconds
                    )
                    if success:
                        rotated_count += 1
                        logger.info(
                            "Auto-rotation initiated",
                            agent_id=agent.id,
                            server_id=agent.server_id,
                        )
                    else:
                        # Cancel rotation if send failed
                        await self.cancel_rotation(agent.id)
                        logger.warning(
                            "Auto-rotation send failed, cancelled",
                            agent_id=agent.id,
                        )
                except Exception as e:
                    await self.cancel_rotation(agent.id)
                    logger.error(
                        "Auto-rotation callback error",
                        agent_id=agent.id,
                        error=str(e),
                    )

            except Exception as e:
                logger.error(
                    "Auto-rotation error for agent",
                    agent_id=agent.id,
                    error=str(e),
                )

        logger.info(
            "Token expiry check completed",
            agents_checked=len(agents),
            rotations_initiated=rotated_count,
        )
        return rotated_count

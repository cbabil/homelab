"""Agent Lifecycle Manager.

Handles agent health monitoring, version management, auto-updates, and graceful
shutdown coordination. Works with AgentManager for active connection tracking.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Callable, Optional

import structlog

from models.agent import (
    AgentConfig,
    AgentHeartbeat,
    AgentShutdownRequest,
    AgentStatus,
    AgentUpdate,
    AgentVersionInfo,
)
from services.database import AgentDatabaseService
from tools.common import log_event

logger = structlog.get_logger("agent_lifecycle")

# Current agent version - update when releasing new agent versions
CURRENT_AGENT_VERSION = "1.0.0"


class AgentLifecycleManager:
    """Manages agent lifecycle including health, updates, and shutdown.

    Provides heartbeat tracking, stale connection detection, version
    management, and graceful shutdown coordination.
    """

    def __init__(
        self,
        agent_db: AgentDatabaseService,
        default_config: Optional[AgentConfig] = None,
    ):
        """Initialize lifecycle manager.

        Args:
            agent_db: Database service for agent persistence.
            default_config: Default agent configuration (for timeouts).
        """
        self._agent_db = agent_db
        self._config = default_config or AgentConfig()
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._shutdown_handlers: list[Callable] = []
        self._last_heartbeats: dict[str, datetime] = {}
        self._running = False

    def set_config(self, config: AgentConfig) -> None:
        """Update lifecycle configuration.

        Args:
            config: New agent configuration.
        """
        self._config = config
        logger.debug(
            "Lifecycle config updated",
            heartbeat_interval=config.heartbeat_interval,
            heartbeat_timeout=config.heartbeat_timeout,
        )

    def register_shutdown_handler(self, handler: Callable) -> None:
        """Register a handler for agent shutdown events.

        Args:
            handler: Async callable(agent_id, reason, restart) -> None.
        """
        self._shutdown_handlers.append(handler)
        logger.debug("Shutdown handler registered")

    async def start(self) -> None:
        """Start the lifecycle manager background tasks."""
        if self._running:
            logger.warning("Lifecycle manager already running")
            return

        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor_loop())
        logger.info("Agent lifecycle manager started")

    async def stop(self) -> None:
        """Stop the lifecycle manager and cleanup."""
        self._running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

        self._last_heartbeats.clear()
        logger.info("Agent lifecycle manager stopped")

    async def record_heartbeat(self, heartbeat: AgentHeartbeat) -> None:
        """Record a heartbeat from an agent.

        Updates last_seen timestamp and stores heartbeat data.

        Args:
            heartbeat: Heartbeat data from agent.
        """
        agent_id = heartbeat.agent_id
        self._last_heartbeats[agent_id] = heartbeat.timestamp

        # Update agent last_seen in database
        update = AgentUpdate(last_seen=heartbeat.timestamp)
        await self._agent_db.update_agent(agent_id, update)

        logger.debug(
            "Heartbeat recorded",
            agent_id=agent_id,
            cpu=heartbeat.cpu_percent,
            memory=heartbeat.memory_percent,
        )

    async def handle_shutdown(self, request: AgentShutdownRequest) -> None:
        """Handle graceful shutdown request from agent.

        Updates agent status and notifies registered handlers.

        Args:
            request: Shutdown request details.
        """
        agent_id = request.agent_id

        # Update status to disconnected (or pending if restarting)
        new_status = (
            AgentStatus.PENDING if request.restart else AgentStatus.DISCONNECTED
        )
        update = AgentUpdate(status=new_status, last_seen=datetime.now(UTC))
        await self._agent_db.update_agent(agent_id, update)

        # Remove from heartbeat tracking
        self._last_heartbeats.pop(agent_id, None)

        logger.info(
            "Agent shutdown handled",
            agent_id=agent_id,
            reason=request.reason,
            will_restart=request.restart,
        )

        # Notify handlers
        for handler in self._shutdown_handlers:
            try:
                await handler(agent_id, request.reason, request.restart)
            except Exception as e:
                logger.error(
                    "Shutdown handler error",
                    agent_id=agent_id,
                    error=str(e),
                )

    def check_version(self, agent_version: str) -> AgentVersionInfo:
        """Check if an agent version needs updating.

        Args:
            agent_version: Current agent version string.

        Returns:
            Version info with update availability.
        """
        update_available = self._compare_versions(agent_version, CURRENT_AGENT_VERSION)

        return AgentVersionInfo(
            current_version=agent_version,
            latest_version=CURRENT_AGENT_VERSION,
            update_available=update_available,
            release_notes=self._get_release_notes() if update_available else None,
            update_url=self._get_update_url() if update_available else None,
        )

    async def trigger_update(self, agent_id: str) -> bool:
        """Mark an agent for update on next connection.

        Args:
            agent_id: Agent to mark for update.

        Returns:
            True if successfully marked, False otherwise.
        """
        update = AgentUpdate(status=AgentStatus.UPDATING)
        agent = await self._agent_db.update_agent(agent_id, update)

        if agent:
            logger.info("Agent marked for update", agent_id=agent_id)
            await log_event(
                "agent",
                "INFO",
                f"Agent update triggered: {agent_id}",
                ["agent", "lifecycle"],
                {
                    "event_type": "AGENT_UPDATED",
                    "agent_id": agent_id,
                    "server_id": agent.server_id,
                    "success": True,
                },
            )
            return True

        logger.warning("Failed to mark agent for update", agent_id=agent_id)
        return False

    async def get_stale_agents(self) -> list[str]:
        """Get list of agents that have missed heartbeats.

        Returns:
            List of stale agent IDs.
        """
        stale_agents = []
        timeout = timedelta(seconds=self._config.heartbeat_timeout)
        now = datetime.now(UTC)

        for agent_id, last_seen in self._last_heartbeats.items():
            if now - last_seen > timeout:
                stale_agents.append(agent_id)

        return stale_agents

    def is_agent_stale(self, agent_id: str) -> bool:
        """Check if a specific agent is stale.

        Args:
            agent_id: Agent to check.

        Returns:
            True if agent is stale or unknown.
        """
        last_seen = self._last_heartbeats.get(agent_id)
        if not last_seen:
            return True

        timeout = timedelta(seconds=self._config.heartbeat_timeout)
        return datetime.now(UTC) - last_seen > timeout

    def register_agent_connection(self, agent_id: str) -> None:
        """Register a newly connected agent for heartbeat tracking.

        Args:
            agent_id: Agent that just connected.
        """
        self._last_heartbeats[agent_id] = datetime.now(UTC)
        logger.debug("Agent registered for heartbeat tracking", agent_id=agent_id)

    def unregister_agent_connection(self, agent_id: str) -> None:
        """Remove agent from heartbeat tracking.

        Args:
            agent_id: Agent that disconnected.
        """
        self._last_heartbeats.pop(agent_id, None)
        logger.debug("Agent removed from heartbeat tracking", agent_id=agent_id)

    async def _heartbeat_monitor_loop(self) -> None:
        """Background task to monitor agent heartbeats."""
        logger.info("Heartbeat monitor started")

        while self._running:
            try:
                await asyncio.sleep(self._config.heartbeat_interval)
                await self._check_stale_agents()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Heartbeat monitor error", error=str(e))
                await asyncio.sleep(5)

        logger.info("Heartbeat monitor stopped")

    async def _check_stale_agents(self) -> None:
        """Check for and handle stale agent connections."""
        stale_agents = await self.get_stale_agents()

        for agent_id in stale_agents:
            logger.warning("Agent is stale", agent_id=agent_id)

            # Update status to disconnected
            update = AgentUpdate(status=AgentStatus.DISCONNECTED)
            await self._agent_db.update_agent(agent_id, update)

            # Remove from tracking
            self._last_heartbeats.pop(agent_id, None)

    def _compare_versions(self, current: str, latest: str) -> bool:
        """Compare version strings to determine if update needed.

        Args:
            current: Current version (e.g., "1.0.0").
            latest: Latest version (e.g., "1.1.0").

        Returns:
            True if latest > current.
        """
        try:
            current_parts = [int(p) for p in current.split(".")]
            latest_parts = [int(p) for p in latest.split(".")]

            # Pad to same length
            max_len = max(len(current_parts), len(latest_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            latest_parts.extend([0] * (max_len - len(latest_parts)))

            return latest_parts > current_parts
        except (ValueError, AttributeError):
            logger.warning(
                "Invalid version format",
                current=current,
                latest=latest,
            )
            return False

    def _get_release_notes(self) -> str:
        """Get release notes for the latest version.

        Returns:
            Release notes string.
        """
        # TODO: Fetch from release notes file or API
        return f"Update to version {CURRENT_AGENT_VERSION}"

    def _get_update_url(self) -> str:
        """Get download URL for the latest agent version.

        Returns:
            Download URL string.
        """
        # TODO: Configure via settings
        return f"https://github.com/tomo/agent/releases/v{CURRENT_AGENT_VERSION}"

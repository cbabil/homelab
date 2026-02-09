"""Agent Service.

High-level service for agent lifecycle management including creation,
registration, token validation, and revocation.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Optional

import structlog

from lib.log_event import log_event

if TYPE_CHECKING:
    from services.database import AgentDatabaseService

from models.agent import (
    Agent,
    AgentConfig,
    AgentCreate,
    AgentRegistrationResponse,
    AgentStatus,
    AgentUpdate,
    RegistrationCode,
)
from services.agent_rotation import AgentRotationMixin
from services.database_service import DatabaseService
from services.settings_service import SettingsService

logger = structlog.get_logger("agent_service")


class AgentService(AgentRotationMixin):
    """Service for managing agent lifecycle operations.

    Handles agent creation, registration code generation, token-based
    authentication, and agent revocation.
    """

    def __init__(
        self,
        db_service: DatabaseService | None = None,
        settings_service: SettingsService | None = None,
        agent_db: Optional["AgentDatabaseService"] = None,
    ):
        """Initialize agent service with database and settings dependencies.

        Args:
            db_service: Database service for agent persistence.
            settings_service: Settings service for agent configuration.
            agent_db: Agent database service (injected for efficiency).
        """
        self.db_service = db_service or DatabaseService()
        self.settings_service = settings_service or SettingsService(
            db_service=self.db_service
        )
        # Store injected agent_db or create lazily on first use
        self._agent_db = agent_db

        # Initialize rotation scheduler state (from AgentRotationMixin)
        self._init_rotation_state()

        logger.info("Agent service initialized")

    def get_agent_db(self) -> "AgentDatabaseService":
        """Get or create the agent database service.

        Returns:
            AgentDatabaseService instance.
        """
        if self._agent_db is None:
            # Lazy initialization for backward compatibility
            from services.database import AgentDatabaseService, DatabaseConnection

            db_conn = DatabaseConnection(db_path=self.db_service.db_path)
            self._agent_db = AgentDatabaseService(db_conn)
        return self._agent_db

    def _hash_token(self, token: str) -> str:
        """Hash a token using SHA256.

        Args:
            token: Plain text token to hash.

        Returns:
            Hexadecimal SHA256 hash of the token.
        """
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

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
    ) -> None:
        """Log an agent lifecycle event to the audit system.

        Args:
            event_type: Type of event (AGENT_INSTALLED, AGENT_CONNECTED, etc.)
            level: Log level (INFO, WARNING, ERROR)
            message: Human-readable message
            server_id: Server identifier
            server_name: Server display name
            agent_id: Agent identifier (if available)
            success: Whether the operation succeeded
            details: Additional event-specific details
        """
        await log_event(
            "agent",
            level,
            message,
            ["agent", "lifecycle"],
            {
                "event_type": event_type,
                "server_id": server_id,
                "server_name": server_name,
                "agent_id": agent_id,
                "success": success,
                "details": details or {},
            },
        )

    async def _get_server_name(self, server_id: str) -> str:
        """Get server name from server ID for audit logging.

        Args:
            server_id: Server identifier.

        Returns:
            Server name if found, otherwise the server_id as fallback.
        """
        try:
            server = await self.db_service.get_server_by_id(server_id)
            if server and server.name:
                return server.name
        except Exception as e:
            logger.warning(
                "Failed to get server name for audit", server_id=server_id, error=str(e)
            )
        return server_id  # Fallback to ID if name not available

    async def _get_agent_config(self) -> AgentConfig:
        """Get agent configuration from settings.

        Retrieves agent-related settings and constructs an AgentConfig.
        Falls back to defaults if settings are unavailable.

        Returns:
            AgentConfig with current settings.
        """
        config = AgentConfig()

        try:
            # Get individual agent settings
            metrics_setting = await self.settings_service.get_system_setting(
                "agent.metrics_interval"
            )
            if metrics_setting and metrics_setting.setting_value:
                value = metrics_setting.setting_value.get_parsed_value()
                config.metrics_interval = value

            health_setting = await self.settings_service.get_system_setting(
                "agent.health_interval"
            )
            if health_setting and health_setting.setting_value:
                value = health_setting.setting_value.get_parsed_value()
                config.health_interval = value

            reconnect_setting = await self.settings_service.get_system_setting(
                "agent.reconnect_timeout"
            )
            if reconnect_setting and reconnect_setting.setting_value:
                value = reconnect_setting.setting_value.get_parsed_value()
                config.reconnect_timeout = value

            logger.debug(
                "Agent config loaded from settings",
                metrics_interval=config.metrics_interval,
                health_interval=config.health_interval,
                reconnect_timeout=config.reconnect_timeout,
            )

        except Exception as e:
            logger.warning(
                "Failed to load agent config from settings, using defaults",
                error=str(e),
            )

        return config

    async def get_token_rotation_settings(self) -> tuple[int, int]:
        """Get token rotation settings from database.

        Returns:
            Tuple of (rotation_days, grace_period_minutes).
        """
        rotation_days = 7  # Default
        grace_minutes = 5  # Default

        try:
            rotation_setting = await self.settings_service.get_system_setting(
                "agent.token_rotation_days"
            )
            if rotation_setting and rotation_setting.setting_value:
                rotation_days = rotation_setting.setting_value.get_parsed_value()

            grace_setting = await self.settings_service.get_system_setting(
                "agent.token_grace_period_minutes"
            )
            if grace_setting and grace_setting.setting_value:
                grace_minutes = grace_setting.setting_value.get_parsed_value()

        except Exception as e:
            logger.warning(
                "Failed to load token rotation settings, using defaults",
                error=str(e),
            )

        return rotation_days, grace_minutes

    async def create_agent(self, server_id: str) -> tuple[Agent, RegistrationCode]:
        """Create a new agent and registration code for a server.

        If an agent already exists for the server, it is deleted first
        to ensure a fresh start.

        Args:
            server_id: Server identifier to associate with agent.

        Returns:
            Tuple of (Agent, RegistrationCode) for the new agent.

        Raises:
            Exception: If agent creation fails.
        """
        logger.info("Creating agent for server", server_id=server_id)

        # Delete existing agent if one exists for this server
        existing_agent = await self.get_agent_by_server(server_id)
        if existing_agent:
            logger.info(
                "Deleting existing agent for server",
                agent_id=existing_agent.id,
                server_id=server_id,
            )
            await self.delete_agent(existing_agent.id)

        # Create new agent
        agent_data = AgentCreate(server_id=server_id)

        agent_db = self.get_agent_db()

        agent = await agent_db.create_agent(agent_data)
        registration_code = await agent_db.create_registration_code(agent.id)

        logger.info(
            "Agent created with registration code",
            agent_id=agent.id,
            server_id=server_id,
            expires_at=registration_code.expires_at.isoformat(),
        )

        server_name = await self._get_server_name(server_id)
        await self._log_agent_event(
            event_type="AGENT_INSTALLED",
            level="INFO",
            message=f"Agent installed for server {server_name}",
            server_id=server_id,
            server_name=server_name,
            agent_id=agent.id,
            success=True,
        )

        return agent, registration_code

    async def validate_registration_code(self, code: str) -> RegistrationCode | None:
        """Validate a registration code.

        Checks if the code exists, has not been used, and has not expired.

        Args:
            code: Registration code string to validate.

        Returns:
            RegistrationCode if valid, None otherwise.
        """
        agent_db = self.get_agent_db()

        registration = await agent_db.get_registration_code(code)
        if not registration:
            logger.debug("Registration code not found", code=code[:4] + "****")
            return None

        if registration.used:
            logger.debug(
                "Registration code already used",
                code_id=registration.id,
            )
            return None

        now = datetime.now(UTC)
        if registration.expires_at < now:
            logger.debug(
                "Registration code expired",
                code_id=registration.id,
                expired_at=registration.expires_at.isoformat(),
            )
            return None

        logger.debug("Registration code valid", code_id=registration.id)
        return registration

    async def complete_registration(
        self, code: str, agent_version: str
    ) -> AgentRegistrationResponse | None:
        """Complete agent registration using a registration code.

        Validates the code, generates an authentication token, updates
        the agent record, and marks the code as used.

        Args:
            code: Registration code for authentication.
            agent_version: Version string of the agent software.

        Returns:
            AgentRegistrationResponse with token and config if successful,
            None if registration fails.
        """
        registration = await self.validate_registration_code(code)
        if not registration:
            logger.warning("Registration failed: invalid code")
            return None

        agent_db = self.get_agent_db()

        # Generate authentication token
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)

        # Get agent configuration
        config = await self._get_agent_config()

        # Get token rotation settings
        rotation_days, _ = await self.get_token_rotation_settings()

        # Update agent with token and registration info
        now = datetime.now(UTC)
        token_expires_at = now + timedelta(days=rotation_days)

        update_data = AgentUpdate(
            token_hash=token_hash,
            version=agent_version,
            status=AgentStatus.CONNECTED,
            registered_at=now,
            last_seen=now,
            config=config,
            token_issued_at=now,
            token_expires_at=token_expires_at,
        )

        agent = await agent_db.update_agent(registration.agent_id, update_data)
        if not agent:
            logger.error(
                "Registration failed: could not update agent",
                agent_id=registration.agent_id,
            )
            return None

        # Mark registration code as used
        await agent_db.mark_code_used(registration.id)

        logger.info(
            "Agent registration completed",
            agent_id=agent.id,
            version=agent_version,
        )

        # Log agent registered event for audit trail
        server_name = await self._get_server_name(agent.server_id)
        await self._log_agent_event(
            "AGENT_REGISTERED",
            "INFO",
            f"Agent registered for server {server_name}",
            server_id=agent.server_id,
            server_name=server_name,
            agent_id=agent.id,
            success=True,
            details={"version": agent_version},
        )

        return AgentRegistrationResponse(
            agent_id=agent.id,
            server_id=agent.server_id,
            token=token,
            config=config,
        )

    async def validate_token(self, token: str) -> Agent | None:
        """Validate an agent authentication token.

        Hashes the provided token and looks up the agent by token hash.
        During token rotation, also checks pending_token_hash and auto-completes
        rotation if the agent uses the new token.
        DISCONNECTED agents are allowed to authenticate - they are reconnecting.

        Args:
            token: Plain text authentication token.

        Returns:
            Agent if token is valid, None otherwise.
        """
        token_hash = self._hash_token(token)
        agent_db = self.get_agent_db()

        # Check current token
        agent = await agent_db.get_agent_by_token_hash(token_hash)
        if agent:
            logger.debug(
                "Token validated", agent_id=agent.id, status=agent.status.value
            )
            return agent

        # Check pending token (during rotation)
        agent = await agent_db.get_agent_by_pending_token_hash(token_hash)
        if agent:
            # Agent is using new token, complete rotation
            logger.info(
                "Agent using new token, completing rotation",
                agent_id=agent.id,
            )
            await self.complete_rotation(agent.id)
            # Refresh agent data after rotation
            agent = await agent_db.get_agent(agent.id)
            return agent

        logger.debug("Token validation failed: agent not found")
        return None

    async def revoke_agent_token(self, agent_id: str) -> bool:
        """Revoke agent token by clearing it and setting disconnected status.

        Args:
            agent_id: Agent identifier to revoke.

        Returns:
            True if revocation successful, False otherwise.
        """
        agent_db = self.get_agent_db()

        update_data = AgentUpdate(
            token_hash=None,
            status=AgentStatus.DISCONNECTED,
        )

        agent = await agent_db.update_agent(agent_id, update_data)
        if not agent:
            logger.warning("Revocation failed: agent not found", agent_id=agent_id)
            return False

        logger.info("Agent revoked", agent_id=agent_id)

        server_name = await self._get_server_name(agent.server_id)
        await self._log_agent_event(
            event_type="AGENT_REVOKED",
            level="WARNING",
            message=f"Agent token revoked for server {server_name}",
            server_id=agent.server_id,
            server_name=server_name,
            agent_id=agent_id,
            success=True,
        )

        return True

    async def get_agent_by_server(self, server_id: str) -> Agent | None:
        """Get agent associated with a server.

        Args:
            server_id: Server identifier.

        Returns:
            Agent if found, None otherwise.
        """
        agent_db = self.get_agent_db()

        return await agent_db.get_agent_by_server(server_id)

    async def list_all_agents(self) -> list[Agent]:
        """List all agents.

        Returns:
            List of all agents.
        """
        agent_db = self.get_agent_db()

        return await agent_db.list_all_agents()

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent record.

        Args:
            agent_id: Agent identifier to delete.

        Returns:
            True if deletion successful, False otherwise.
        """
        agent_db = self.get_agent_db()

        # Get agent info before deletion for logging
        agent = await agent_db.get_agent(agent_id)
        server_id = agent.server_id if agent else ""

        result = await agent_db.delete_agent(agent_id)
        if result:
            logger.info("Agent deleted", agent_id=agent_id)

            server_name = (
                await self._get_server_name(server_id) if server_id else server_id
            )
            await self._log_agent_event(
                event_type="AGENT_UNINSTALLED",
                level="INFO",
                message=f"Agent uninstalled from server {server_name}",
                server_id=server_id,
                server_name=server_name,
                agent_id=agent_id,
                success=True,
            )
        else:
            logger.warning("Agent deletion failed", agent_id=agent_id)
        return result

    async def register_agent(
        self, code: str, version: str | None = None
    ) -> tuple[str, str, AgentConfig, str] | None:
        """Register an agent using a registration code (WebSocket API).

        Args:
            code: Registration code for authentication.
            version: Optional agent version string.

        Returns:
            Tuple of (agent_id, token, config, server_id) if successful, None otherwise.
        """
        result = await self.complete_registration(code, version or "unknown")
        if not result:
            return None

        # Note: AGENT_REGISTERED is logged in complete_registration()
        return (result.agent_id, result.token, result.config, result.server_id)

    async def authenticate_agent(
        self, token: str, version: str | None = None
    ) -> tuple[str, AgentConfig, str] | None:
        """Authenticate an agent using a token (WebSocket API).

        Args:
            token: Authentication token.
            version: Optional agent version string (for updating last seen).

        Returns:
            Tuple of (agent_id, config, server_id) if successful, None otherwise.
        """
        agent = await self.validate_token(token)
        if not agent:
            return None

        # Update last seen and optionally version
        agent_db = self.get_agent_db()

        update_data = AgentUpdate(last_seen=datetime.now(UTC))
        if version:
            update_data.version = version

        await agent_db.update_agent(agent.id, update_data)

        config = await self._get_agent_config()
        return (agent.id, config, agent.server_id)

    async def reset_stale_agent_statuses(self) -> int:
        """Reset stale CONNECTED and PENDING agents on startup.

        Called during server startup to ensure database status matches reality.
        WebSocket connections don't persist across server restarts, so any
        agent showing as CONNECTED is stale and should be reset.
        PENDING agents older than 10 minutes are also reset as they likely
        represent failed installation attempts.

        Returns:
            Number of agents that were reset.
        """
        agent_db = self.get_agent_db()

        agents = await agent_db.list_all_agents()
        reset_count = 0
        now = datetime.now(UTC)
        pending_timeout = timedelta(minutes=10)

        for agent in agents:
            should_reset = False
            reason = ""

            if agent.status == AgentStatus.CONNECTED:
                should_reset = True
                reason = "stale connected status"
            elif agent.status == AgentStatus.PENDING:
                # Reset PENDING agents older than 10 minutes
                created_at = agent.registered_at or agent.last_seen
                if created_at and (now - created_at) > pending_timeout:
                    should_reset = True
                    reason = "stale pending status (>10 min)"
                elif not created_at:
                    # No timestamp, assume stale
                    should_reset = True
                    reason = "stale pending status (no timestamp)"

            if should_reset:
                update = AgentUpdate(status=AgentStatus.DISCONNECTED)
                await agent_db.update_agent(agent.id, update)
                reset_count += 1
                logger.info(
                    "Reset stale agent status to DISCONNECTED",
                    agent_id=agent.id,
                    server_id=agent.server_id,
                    reason=reason,
                )

        if reset_count > 0:
            logger.info(
                "Startup cleanup: reset stale agent statuses",
                reset_count=reset_count,
            )

        return reset_count

    # Token rotation methods are provided by AgentRotationMixin:
    # initiate_rotation, complete_rotation, cancel_rotation,
    # get_agents_needing_rotation, set_rotation_callback,
    # start_rotation_scheduler, stop_rotation_scheduler,
    # check_token_expiry

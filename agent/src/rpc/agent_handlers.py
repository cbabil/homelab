"""Agent-specific RPC method handlers.

This module provides built-in RPC handlers for:
- Configuration updates from the server
- Agent metrics reporting
- Token rotation
"""

import logging
import time
from datetime import datetime, timezone
from typing import Callable

try:
    import psutil
except ImportError:
    psutil = None

try:
    from .. import __version__
    from ..config import AgentConfig, AgentState, load_state, save_state, update_config
    from .handler import RPCHandler
except ImportError:
    __version__ = "1.0.0"
    from config import AgentConfig, AgentState, load_state, save_state, update_config
    from rpc.handler import RPCHandler

logger = logging.getLogger(__name__)


def create_config_update_handler(
    get_config: Callable[[], AgentConfig],
    set_config: Callable[[AgentConfig], None],
) -> Callable:
    """Create a config update handler with access to agent config.

    Args:
        get_config: Function to get current config.
        set_config: Function to update config.

    Returns:
        Handler function for config.update RPC method.
    """

    def handle_config_update(**kwargs) -> dict:
        """Handle config update from server."""
        current = get_config()
        updated = update_config(current, kwargs)
        set_config(updated)
        logger.info("Config updated: %s", kwargs)
        return {"status": "ok"}

    return handle_config_update


def create_metrics_handler(
    get_agent_id: Callable[[], str | None],
) -> Callable:
    """Create a metrics handler with access to agent state.

    Args:
        get_agent_id: Function to get current agent ID.

    Returns:
        Handler function for metrics.get RPC method.
    """

    def handle_metrics_get() -> dict:
        """Handle metrics request from server."""
        metrics = {
            "agent_id": get_agent_id(),
            "version": __version__,
            "status": "connected",
            "timestamp": time.time(),
        }

        # Add system metrics if psutil is available
        if psutil:
            try:
                metrics["cpu_percent"] = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory()
                metrics["memory"] = {
                    "total": mem.total,
                    "available": mem.available,
                    "percent": mem.percent,
                }
                disk = psutil.disk_usage("/")
                metrics["disk"] = {
                    "total": disk.total,
                    "free": disk.free,
                    "percent": disk.percent,
                }
            except Exception as e:
                logger.warning("Failed to collect system metrics: %s", e)

        return metrics

    return handle_metrics_get


def create_rotate_token_handler() -> Callable:
    """Create a token rotation handler.

    Returns:
        Handler function for agent.rotate_token RPC method.
    """

    def handle_rotate_token(new_token: str, grace_period_seconds: int = 300) -> dict:
        """Handle token rotation request from server.

        Saves the new token to the state file. The server will accept
        both old and new tokens during the grace period.

        Args:
            new_token: The new authentication token to save.
            grace_period_seconds: Time in seconds the old token remains valid.

        Returns:
            Status dict indicating success or failure.
        """
        try:
            # Load current state to preserve agent_id and server_url
            current_state = load_state()
            if not current_state:
                logger.error("Cannot rotate token: no existing state found")
                return {"status": "error", "error": "No existing state"}

            # Create new state with the new token
            new_state = AgentState(
                agent_id=current_state.agent_id,
                token=new_token,
                server_url=current_state.server_url,
                registered_at=current_state.registered_at,
            )

            # Save new state (token will be encrypted)
            save_state(new_state)

            logger.info(
                "Token rotated successfully, grace period: %d seconds",
                grace_period_seconds,
            )

            return {
                "status": "ok",
                "rotated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error("Token rotation failed: %s", e)
            return {"status": "error", "error": str(e)}

    return handle_rotate_token


def setup_agent_handlers(
    rpc_handler: RPCHandler,
    get_config: Callable[[], AgentConfig],
    set_config: Callable[[AgentConfig], None],
    get_agent_id: Callable[[], str | None],
) -> None:
    """Set up all agent-specific RPC handlers.

    Args:
        rpc_handler: The RPC handler to register methods with.
        get_config: Function to get current config.
        set_config: Function to update config.
        get_agent_id: Function to get current agent ID.
    """
    rpc_handler.register(
        "config.update",
        create_config_update_handler(get_config, set_config),
    )
    rpc_handler.register(
        "metrics.get",
        create_metrics_handler(get_agent_id),
    )
    rpc_handler.register(
        "agent.rotate_token",
        create_rotate_token_handler(),
    )

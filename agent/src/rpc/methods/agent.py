"""Agent RPC methods."""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional

try:
    from ... import __version__
except ImportError:
    __version__ = "1.0.0"

logger = logging.getLogger(__name__)


class AgentMethods:
    """Agent management methods."""

    def __init__(
        self,
        get_agent_id: Callable[[], Optional[str]],
        shutdown: Callable,
    ):
        """Initialize agent methods.

        Args:
            get_agent_id: Function to get current agent ID.
            shutdown: Async function to trigger shutdown.
        """
        self._get_agent_id = get_agent_id
        self._shutdown = shutdown

    def ping(self) -> Dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "ok",
            "version": __version__,
            "agent_id": self._get_agent_id(),
        }

    def update(self, version: str) -> Dict[str, str]:
        """Trigger agent update."""
        from .docker_client import get_client

        image = f"ghcr.io/tomo/agent:{version}"

        logger.info(f"Updating agent to {version}")

        try:
            client = get_client()

            logger.info(f"Pulling {image}")
            client.images.pull("ghcr.io/tomo/agent", tag=version)

            logger.info("Update pulled, initiating restart...")

            asyncio.get_running_loop().call_later(
                1.0, lambda: asyncio.create_task(self._shutdown())
            )

            return {"status": "updating", "version": version}

        except Exception as e:
            logger.error(f"Update failed: {e}")
            return {"status": "error", "message": str(e)}


def create_agent_methods(
    get_agent_id: Callable[[], Optional[str]],
    shutdown: Callable,
) -> AgentMethods:
    """Create AgentMethods instance with callbacks.

    Args:
        get_agent_id: Function to get current agent ID.
        shutdown: Async function to trigger shutdown.

    Returns:
        Configured AgentMethods instance.
    """
    return AgentMethods(
        get_agent_id=get_agent_id,
        shutdown=shutdown,
    )

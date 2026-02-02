"""Agent authentication and registration."""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional, Tuple

try:
    from . import __version__
    from .config import AgentConfig, AgentState, load_state, save_state
except ImportError:
    __version__ = "1.0.0"
    from config import AgentConfig, AgentState, load_state, save_state

logger = logging.getLogger(__name__)


async def authenticate(
    websocket: Any,  # websockets.ClientConnection
    config: AgentConfig,
) -> Tuple[Optional[str], Optional[AgentConfig]]:
    """Authenticate with the server."""
    state = load_state()

    if state:
        return await _authenticate_with_token(websocket, state)

    if config.register_code:
        return await _register_with_code(websocket, config)

    logger.error("No token or registration code available")
    return None, None


async def _authenticate_with_token(
    websocket: Any,  # websockets.ClientConnection
    state: AgentState,
) -> Tuple[Optional[str], Optional[AgentConfig]]:
    """Authenticate using existing token."""
    await websocket.send(
        json.dumps(
            {
                "type": "authenticate",
                "token": state.token,
                "version": __version__,
            }
        )
    )

    response = json.loads(await websocket.recv())

    if response.get("type") == "authenticated":
        logger.info(f"Authenticated as agent {response['agent_id']}")
        config = AgentConfig(**response.get("config", {}))
        return response["agent_id"], config

    logger.error(f"Authentication failed: {response.get('error')}")
    return None, None


async def _register_with_code(
    websocket: Any,  # websockets.ClientConnection
    config: AgentConfig,
) -> Tuple[Optional[str], Optional[AgentConfig]]:
    """Register using registration code."""
    await websocket.send(
        json.dumps(
            {
                "type": "register",
                "code": config.register_code,
                "version": __version__,
            }
        )
    )

    response = json.loads(await websocket.recv())

    if response.get("type") == "registered":
        agent_id = response["agent_id"]
        token = response["token"]

        state = AgentState(
            agent_id=agent_id,
            token=token,
            server_url=config.server_url,
            registered_at=datetime.now(timezone.utc).isoformat(),
        )
        save_state(state)

        logger.info(f"Registered as agent {agent_id}")
        updated_config = AgentConfig(**response.get("config", {}))
        return agent_id, updated_config

    logger.error(f"Registration failed: {response.get('error')}")
    return None, None

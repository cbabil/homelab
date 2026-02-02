"""WebSocket connection management for the agent."""

import asyncio
import json
import logging
import os
import ssl
from typing import Any, Optional, Tuple

import certifi
import websockets
from websockets.exceptions import ConnectionClosed

try:
    from .auth import authenticate
    from .config import AgentConfig, load_state, update_config
    from .rpc.handler import RPCHandler
    from .lib.replay import validate_message_freshness
except ImportError:
    from auth import authenticate
    from config import AgentConfig, load_state, update_config
    from rpc.handler import RPCHandler
    from lib.replay import validate_message_freshness

logger = logging.getLogger(__name__)


def create_ssl_context() -> ssl.SSLContext:
    """Create SSL context with proper certificate validation.

    Uses system CA certificates with fallback to certifi bundle.
    In development mode (TOMO_DEV=1), allows self-signed certificates.
    """
    # Development mode - allow self-signed certs
    if os.environ.get("TOMO_DEV") == "1":
        logger.warning("Development mode: TLS certificate verification disabled")
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    # Production mode - strict certificate validation
    ctx = ssl.create_default_context(cafile=certifi.where())
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    # Disable older TLS versions
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


async def establish_connection(
    config: AgentConfig,
) -> Tuple[Optional[Any], Optional[str], Optional[AgentConfig]]:
    """Establish WebSocket connection and authenticate.

    Returns:
        Tuple of (websocket, agent_id, updated_config) on success,
        or (None, None, None) on failure.
    """
    state = load_state()
    server_url = state.server_url if state else config.server_url

    if not server_url:
        logger.error("No server URL configured")
        return None, None, None

    ws: Optional[Any] = None  # websockets.ClientConnection
    try:
        logger.info("Connecting to %s", server_url)

        # Use TLS for secure connections
        ssl_context = None
        if server_url.startswith("wss://"):
            ssl_context = create_ssl_context()

        ws = await websockets.connect(server_url, ssl=ssl_context)

        try:
            agent_id, auth_config = await authenticate(ws, config)
            if not agent_id:
                return None, None, None

            updated_config = None
            if auth_config:
                updated_config = update_config(config, auth_config.model_dump())

            logger.info("Connected as agent %s", agent_id)
            result_ws = ws
            ws = None  # Don't close on success
            return result_ws, agent_id, updated_config
        except Exception as e:
            logger.error("Authentication failed: %s", e)
            return None, None, None
    except Exception as e:
        logger.error("Connection failed: %s", e)
        return None, None, None
    finally:
        if ws is not None:
            await ws.close()


async def run_message_loop(websocket: Any, rpc_handler: RPCHandler) -> None:
    """Handle incoming WebSocket messages."""
    try:
        async for message in websocket:
            await _handle_message(message, websocket, rpc_handler)
    except ConnectionClosed:
        logger.info("Connection closed by server")
    except Exception as e:
        logger.error("Message loop error: %s", e)


async def _handle_message(
    message: str, websocket: Any, rpc_handler: RPCHandler
) -> None:
    """Process a single incoming message.

    Validates message freshness and replay protection before processing.
    """
    try:
        request = json.loads(message)

        # Check for replay protection fields (optional but recommended)
        timestamp = request.get("timestamp")
        nonce = request.get("nonce")

        if timestamp is not None and nonce is not None:
            is_valid, error_msg = validate_message_freshness(timestamp, nonce)
            if not is_valid:
                logger.warning(
                    "Message rejected: %s",
                    error_msg,
                    extra={"method": request.get("method")},
                )
                # Send error response for replay attacks
                if request.get("id"):
                    await websocket.send(
                        json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "error": {"code": -32600, "message": error_msg},
                                "id": request.get("id"),
                            }
                        )
                    )
                return

        response = await rpc_handler.handle(request)
        if response:
            await websocket.send(json.dumps(response))
    except json.JSONDecodeError:
        logger.error("Invalid JSON received: %s", message[:100])
    except Exception as e:
        logger.exception("Error handling message: %s", e)


async def close_websocket(websocket: Optional[Any]) -> None:
    """Close WebSocket connection with timeout."""
    if not websocket:
        return
    try:
        await asyncio.wait_for(websocket.close(), timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("WebSocket close timed out")
    except Exception as e:
        logger.error("Error closing websocket: %s", e)

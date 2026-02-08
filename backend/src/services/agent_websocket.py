"""Agent WebSocket handler for registration and authentication."""

import asyncio
from typing import TYPE_CHECKING

import structlog
from starlette.websockets import WebSocket, WebSocketDisconnect

from lib.log_event import log_event
from services.helpers.websocket_helpers import (
    close_websocket,
    get_client_info,
    message_loop,
    send_authenticated,
    send_error,
    send_registered,
    ws_rate_limiter,
)

if TYPE_CHECKING:
    from services.agent_manager import AgentManager
    from services.agent_service import AgentService

logger = structlog.get_logger("agent_websocket")

WS_CLOSE_AUTH_FAILED = 4001
WS_CLOSE_NORMAL = 1000
WS_AUTH_TIMEOUT_SECONDS = 30.0  # Timeout for initial authentication message


class AgentWebSocketHandler:
    """Handler for agent WebSocket connections."""

    def __init__(self, agent_service: "AgentService", agent_manager: "AgentManager"):
        """Initialize the WebSocket handler."""
        self._agent_service = agent_service
        self._agent_manager = agent_manager

    async def handle_connection(self, websocket: WebSocket) -> None:
        """Handle a WebSocket connection from an agent."""
        await websocket.accept()
        client_info = get_client_info(websocket)
        client_ip = client_info.get("client_host", "unknown")
        logger.info("Agent WebSocket connection accepted", **client_info)

        # Check rate limiting before processing
        if not ws_rate_limiter.is_allowed(client_ip):
            logger.warning("Connection rejected due to rate limiting", **client_info)
            await send_error(
                websocket, "Too many connection attempts. Try again later."
            )
            await close_websocket(websocket, WS_CLOSE_AUTH_FAILED)
            return

        agent_id: str | None = None
        server_id: str | None = None

        try:
            result = await self._authenticate_connection(websocket, client_ip)
            if not result:
                ws_rate_limiter.record_failure(client_ip)
                return
            agent_id, server_id = result
            ws_rate_limiter.record_success(client_ip)
            await self._agent_manager.register_connection(
                agent_id, websocket, server_id
            )
            logger.info("Agent connection registered", agent_id=agent_id, **client_info)
            await message_loop(websocket, agent_id, self._agent_manager)
        except WebSocketDisconnect:
            logger.info("Agent disconnected", agent_id=agent_id, **client_info)
        except Exception as e:
            logger.error(
                "Agent connection error",
                agent_id=agent_id,
                error=str(e),
                error_type=type(e).__name__,
                **client_info,
            )
        finally:
            if agent_id:
                await self._agent_manager.unregister_connection(agent_id)
                logger.info("Agent connection unregistered", agent_id=agent_id)
                await log_event(
                    "agent",
                    "WARNING",
                    f"Agent disconnected: {agent_id}",
                    ["agent", "lifecycle"],
                    {
                        "event_type": "AGENT_DISCONNECTED",
                        "server_id": server_id,
                        "agent_id": agent_id,
                        "success": True,
                        "details": {"reason": "connection_closed"},
                    },
                )
            await close_websocket(websocket, WS_CLOSE_NORMAL)

    async def _authenticate_connection(
        self, websocket: WebSocket, client_ip: str = "unknown"
    ) -> tuple[str, str] | None:
        """Authenticate the agent connection.

        Waits for an authentication message with a timeout to prevent
        denial-of-service attacks from connections that never authenticate.

        Args:
            websocket: The WebSocket connection.
            client_ip: Client IP for rate limiting tracking.
        """
        try:
            # Apply timeout to prevent DoS from hanging connections
            message = await asyncio.wait_for(
                websocket.receive_json(), timeout=WS_AUTH_TIMEOUT_SECONDS
            )
        except TimeoutError:
            logger.warning(
                "Authentication timeout - client did not send auth message",
                timeout_seconds=WS_AUTH_TIMEOUT_SECONDS,
            )
            await send_error(websocket, "Authentication timeout")
            await close_websocket(websocket, WS_CLOSE_AUTH_FAILED)
            return None
        except Exception as e:
            logger.warning("Failed to receive auth message", error=str(e))
            await send_error(websocket, "Invalid message format")
            await close_websocket(websocket, WS_CLOSE_AUTH_FAILED)
            return None

        msg_type = message.get("type")
        if msg_type == "register":
            return await self._handle_registration(websocket, message)
        elif msg_type == "authenticate":
            return await self._handle_authentication(websocket, message)
        logger.warning("Unknown auth message type", msg_type=msg_type)
        await self._close_with_error(websocket, f"Unknown message type: {msg_type}")
        return None

    async def _handle_registration(
        self, ws: WebSocket, msg: dict
    ) -> tuple[str, str] | None:
        """Handle registration with a registration code."""
        code, version = msg.get("code"), msg.get("version")
        if not code:
            logger.warning("Registration attempted without code")
            await self._close_with_error(ws, "Registration code required")
            return None
        logger.info(
            "Agent registration attempt", code=code[:3] + "***", version=version
        )
        result = await self._agent_service.register_agent(code, version)
        if not result:
            logger.warning("Registration failed", code=code[:3] + "***")
            await self._close_with_error(ws, "Invalid or expired registration code")
            return None
        agent_id, token, config, server_id = result
        await send_registered(ws, agent_id, token, config)
        logger.info("Agent registered successfully", agent_id=agent_id, version=version)
        return agent_id, server_id

    async def _handle_authentication(
        self, ws: WebSocket, msg: dict
    ) -> tuple[str, str] | None:
        """Handle authentication with an existing token."""
        token, version = msg.get("token"), msg.get("version")
        if not token:
            logger.warning("Authentication attempted without token")
            await self._close_with_error(ws, "Authentication token required")
            return None
        logger.info("Agent authentication attempt", version=version)
        result = await self._agent_service.authenticate_agent(token, version)
        if not result:
            logger.warning("Authentication failed")
            await self._close_with_error(ws, "Invalid authentication token")
            return None
        agent_id, config, server_id = result
        await send_authenticated(ws, agent_id, config)
        logger.info(
            "Agent authenticated successfully", agent_id=agent_id, version=version
        )
        await log_event(
            "agent",
            "INFO",
            f"Agent connected: {agent_id}",
            ["agent", "lifecycle"],
            {
                "event_type": "AGENT_CONNECTED",
                "server_id": server_id,
                "agent_id": agent_id,
                "success": True,
            },
        )
        return agent_id, server_id

    async def _close_with_error(self, websocket: WebSocket, error_msg: str) -> None:
        """Send error and close the connection."""
        await send_error(websocket, error_msg)
        await close_websocket(websocket, WS_CLOSE_AUTH_FAILED)

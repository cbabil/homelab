"""WebSocket helper functions for agent connection handling."""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict

import structlog
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

if TYPE_CHECKING:
    from services.agent_manager import AgentManager

logger = structlog.get_logger("agent_websocket")


@dataclass
class RateLimitEntry:
    """Track rate limit state for a client."""

    attempts: int = 0
    first_attempt: float = 0.0
    last_attempt: float = 0.0
    blocked_until: float = 0.0


class ConnectionRateLimiter:
    """Rate limiter for WebSocket authentication attempts.

    Implements a sliding window rate limit with exponential backoff
    after repeated failures.
    """

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: float = 60.0,
        base_block_seconds: float = 30.0,
        max_block_seconds: float = 3600.0,
    ):
        """Initialize rate limiter.

        Args:
            max_attempts: Maximum attempts allowed in the window.
            window_seconds: Time window for counting attempts.
            base_block_seconds: Initial block duration after exceeding limit.
            max_block_seconds: Maximum block duration (1 hour default).
        """
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds
        self._base_block_seconds = base_block_seconds
        self._max_block_seconds = max_block_seconds
        self._clients: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._failure_counts: Dict[str, int] = defaultdict(int)

    def is_allowed(self, client_ip: str) -> bool:
        """Check if a client is allowed to attempt authentication.

        Args:
            client_ip: Client IP address.

        Returns:
            True if allowed, False if rate limited.
        """
        now = time.time()
        entry = self._clients[client_ip]

        # Check if currently blocked
        if entry.blocked_until > now:
            logger.warning(
                "Rate limited client attempted connection",
                client_ip=client_ip,
                blocked_until=entry.blocked_until,
                remaining_seconds=round(entry.blocked_until - now, 1),
            )
            return False

        # Reset window if expired
        if now - entry.first_attempt > self._window_seconds:
            entry.attempts = 0
            entry.first_attempt = now

        # Check attempt count
        if entry.attempts >= self._max_attempts:
            # Apply exponential backoff based on failure count
            failures = self._failure_counts[client_ip]
            block_duration = min(
                self._base_block_seconds * (2**failures), self._max_block_seconds
            )
            entry.blocked_until = now + block_duration
            self._failure_counts[client_ip] = failures + 1
            logger.warning(
                "Client rate limited",
                client_ip=client_ip,
                block_duration_seconds=block_duration,
                failure_count=failures + 1,
            )
            return False

        return True

    def record_attempt(self, client_ip: str) -> None:
        """Record an authentication attempt.

        Args:
            client_ip: Client IP address.
        """
        now = time.time()
        entry = self._clients[client_ip]
        if entry.first_attempt == 0:
            entry.first_attempt = now
        entry.attempts += 1
        entry.last_attempt = now

    def record_success(self, client_ip: str) -> None:
        """Record a successful authentication, resetting failure count.

        Args:
            client_ip: Client IP address.
        """
        # Reset failure count on success
        if client_ip in self._failure_counts:
            del self._failure_counts[client_ip]
        if client_ip in self._clients:
            del self._clients[client_ip]

    def record_failure(self, client_ip: str) -> None:
        """Record a failed authentication attempt.

        Args:
            client_ip: Client IP address.
        """
        self.record_attempt(client_ip)

    def cleanup_expired(self) -> int:
        """Remove expired entries to prevent memory growth.

        Returns:
            Number of entries cleaned up.
        """
        now = time.time()
        expired = [
            ip
            for ip, entry in self._clients.items()
            if (
                entry.blocked_until < now
                and now - entry.last_attempt > self._window_seconds * 2
            )
        ]
        for ip in expired:
            del self._clients[ip]
            if ip in self._failure_counts:
                del self._failure_counts[ip]
        return len(expired)


# Global rate limiter instance for WebSocket connections
ws_rate_limiter = ConnectionRateLimiter()


MAX_CONSECUTIVE_ERRORS = 5  # Disconnect after this many consecutive errors


async def message_loop(
    websocket: WebSocket, agent_id: str, agent_manager: "AgentManager"
) -> None:
    """Process messages from the agent in a loop until disconnect.

    Tracks consecutive errors and disconnects if threshold exceeded
    to prevent infinite error loops from masking serious issues.
    """
    consecutive_errors = 0

    while True:
        try:
            message = await websocket.receive_text()
            await agent_manager.handle_message(agent_id, message)
            # Reset error count on successful message processing
            consecutive_errors = 0
        except WebSocketDisconnect:
            raise
        except Exception as e:
            consecutive_errors += 1
            logger.warning(
                "Error processing agent message",
                agent_id=agent_id,
                error=str(e),
                error_type=type(e).__name__,
                consecutive_errors=consecutive_errors,
            )

            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                logger.error(
                    "Too many consecutive errors, disconnecting agent",
                    agent_id=agent_id,
                    error_count=consecutive_errors,
                )
                # Raise to trigger disconnect handling
                raise RuntimeError(
                    f"Disconnected after {consecutive_errors} consecutive errors"
                )


async def send_error(websocket: WebSocket, message: str) -> None:
    """Send an error message to the agent."""
    try:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json({"error": message})
    except Exception as e:
        logger.debug("Failed to send error message", error=str(e))


async def send_registered(
    websocket: WebSocket, agent_id: str, token: str, config: Any
) -> None:
    """Send registration success response."""
    response = {
        "type": "registered",
        "agent_id": agent_id,
        "token": token,
        "config": config.model_dump() if hasattr(config, "model_dump") else config,
    }
    await websocket.send_json(response)


async def send_authenticated(websocket: WebSocket, agent_id: str, config: Any) -> None:
    """Send authentication success response."""
    response = {
        "type": "authenticated",
        "agent_id": agent_id,
        "config": config.model_dump() if hasattr(config, "model_dump") else config,
    }
    await websocket.send_json(response)


async def close_websocket(websocket: WebSocket, code: int) -> None:
    """Close the WebSocket connection safely."""
    try:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code=code)
    except Exception as e:
        logger.debug("Error closing WebSocket", error=str(e))


def get_client_info(websocket: WebSocket) -> dict:
    """Extract client host and port from the WebSocket."""
    client = websocket.client
    return {
        "client_host": client.host if client else "unknown",
        "client_port": client.port if client else 0,
    }

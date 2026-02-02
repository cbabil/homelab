"""Tomo Agent class.

This module provides the Agent class that handles:
- WebSocket connection to the tomo server
- Authentication via token or registration code
- JSON-RPC 2.0 message handling
- Automatic reconnection with exponential backoff
- Background metrics and health reporting
"""

import asyncio
import logging
import random
from typing import Any, Optional

try:
    from .collectors import HealthReporter, MetricsCollector
    from .config import AgentConfig, load_config
    from .connection import close_websocket, establish_connection, run_message_loop
    from .handler_setup import setup_all_handlers
    from .rpc.handler import RPCHandler
except ImportError:
    from collectors import HealthReporter, MetricsCollector
    from config import AgentConfig, load_config
    from connection import close_websocket, establish_connection, run_message_loop
    from handler_setup import setup_all_handlers
    from rpc.handler import RPCHandler

logger = logging.getLogger(__name__)


class Agent:
    """Main agent class for tomo server communication."""

    def __init__(self) -> None:
        """Initialize the agent with configuration and RPC handler."""
        self._config = load_config()
        self._config_lock = asyncio.Lock()
        self.agent_id: Optional[str] = None
        self.websocket: Optional[Any] = None  # websockets.ClientConnection
        self.rpc_handler = RPCHandler()
        self.running = True
        self._metrics_collector: Optional[MetricsCollector] = None
        self._health_reporter: Optional[HealthReporter] = None
        self._setup_handlers()

    @property
    def config(self) -> AgentConfig:
        """Get current agent configuration."""
        return self._config

    @config.setter
    def config(self, value: AgentConfig) -> None:
        """Set agent configuration (use set_config_async for thread-safe updates)."""
        self._config = value

    async def set_config_async(self, value: AgentConfig) -> None:
        """Thread-safe configuration update."""
        async with self._config_lock:
            self._config = value

    def _setup_handlers(self) -> None:
        """Set up RPC method handlers."""
        setup_all_handlers(
            self.rpc_handler,
            get_config=lambda: self.config,
            set_config=lambda c: setattr(self, "config", c),
            get_agent_id=lambda: self.agent_id,
            shutdown=self.shutdown,
        )

    async def connect(self) -> bool:
        """Connect to the tomo server."""
        ws, agent_id, updated_config = await establish_connection(self.config)

        if not ws or not agent_id:
            return False

        self.websocket = ws
        self.agent_id = agent_id
        if updated_config:
            self.config = updated_config

        return True

    async def run(self) -> None:
        """Main run loop with reconnection logic."""
        backoff = 1
        max_backoff = 60

        while self.running:
            if await self.connect():
                backoff = 1
                await self._start_collectors()
                await run_message_loop(self.websocket, self.rpc_handler)
                await self._stop_collectors()

            if not self.running:
                break

            # Add jitter to prevent thundering herd on reconnect
            jitter = random.uniform(0, backoff * 0.2)
            delay = backoff + jitter
            logger.info("Reconnecting in %.1fs...", delay)
            await asyncio.sleep(delay)
            backoff = min(backoff * 2, max_backoff)

    async def _start_collectors(self) -> None:
        """Start background collectors after successful connection."""
        self._metrics_collector = MetricsCollector(
            get_interval=lambda: self.config.metrics_interval,
            get_websocket=lambda: self.websocket,
        )
        self._health_reporter = HealthReporter(
            get_interval=lambda: self.config.health_interval,
            get_websocket=lambda: self.websocket,
        )
        await self._metrics_collector.start()
        await self._health_reporter.start()

    async def _stop_collectors(self) -> None:
        """Stop background collectors."""
        if self._metrics_collector:
            await self._metrics_collector.stop()
            self._metrics_collector = None
        if self._health_reporter:
            await self._health_reporter.stop()
            self._health_reporter = None

    async def shutdown(self) -> None:
        """Graceful shutdown of the agent with timeout."""
        logger.info("Shutting down...")
        self.running = False
        await self._stop_collectors()
        await close_websocket(self.websocket)

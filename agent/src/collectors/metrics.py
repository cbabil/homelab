"""Metrics collection and push."""

import asyncio
import json
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and pushes metrics to server."""

    def __init__(
        self,
        get_interval: Callable[[], int],
        get_websocket: Callable[[], Optional[Any]],
    ):
        """Initialize metrics collector with callbacks.

        Args:
            get_interval: Callback to get collection interval in seconds.
            get_websocket: Callback to get current websocket connection.
        """
        self._get_interval = get_interval
        self._get_websocket = get_websocket
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start metrics collection."""
        self._task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collector started")

    async def stop(self) -> None:
        """Stop metrics collection."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collector stopped")

    async def _collection_loop(self) -> None:
        """Main collection loop."""
        # Import here to avoid circular imports
        try:
            from ..rpc.methods.system import SystemMethods
        except ImportError:
            from rpc.methods.system import SystemMethods

        system = SystemMethods()

        while True:
            try:
                interval = self._get_interval()
                await asyncio.sleep(interval)

                websocket = self._get_websocket()
                if not websocket:
                    continue

                metrics = system.get_metrics()

                notification = {
                    "jsonrpc": "2.0",
                    "method": "metrics.update",
                    "params": metrics,
                }

                await websocket.send(json.dumps(notification))
                logger.debug(f"Metrics pushed: CPU={metrics['cpu']}%")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")

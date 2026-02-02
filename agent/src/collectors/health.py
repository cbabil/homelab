"""Health status reporting."""

import asyncio
import json
import logging
import time
from typing import Any, Callable, Optional

try:
    from .. import __version__
except ImportError:
    __version__ = "1.0.0"

logger = logging.getLogger(__name__)

_start_time = time.time()


class HealthReporter:
    """Reports agent health status to server."""

    def __init__(
        self,
        get_interval: Callable[[], int],
        get_websocket: Callable[[], Optional[Any]],
    ):
        """Initialize health reporter with callbacks.

        Args:
            get_interval: Callback to get reporting interval in seconds.
            get_websocket: Callback to get current websocket connection.
        """
        self._get_interval = get_interval
        self._get_websocket = get_websocket
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start health reporting."""
        self._task = asyncio.create_task(self._report_loop())
        logger.info("Health reporter started")

    async def stop(self) -> None:
        """Stop health reporting."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Health reporter stopped")

    async def _report_loop(self) -> None:
        """Main reporting loop."""
        while True:
            try:
                interval = self._get_interval()
                await asyncio.sleep(interval)

                websocket = self._get_websocket()
                if not websocket:
                    continue

                uptime = int(time.time() - _start_time)

                notification = {
                    "jsonrpc": "2.0",
                    "method": "health.status",
                    "params": {
                        "status": "healthy",
                        "uptime": uptime,
                        "version": __version__,
                    },
                }

                await websocket.send(json.dumps(notification))
                logger.debug(f"Health reported: uptime={uptime}s")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Health reporting error: {e}")

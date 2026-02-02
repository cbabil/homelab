"""Tomo Agent main entry point."""

import asyncio
import logging
import signal

try:
    from . import __version__
    from .agent import Agent
except ImportError:
    __version__ = "1.0.0"
    from agent import Agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Main entry point."""
    logger.info(f"Tomo Agent v{__version__} starting")

    agent = Agent()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(agent.shutdown()))

    await agent.run()
    logger.info("Agent stopped")


if __name__ == "__main__":
    asyncio.run(main())

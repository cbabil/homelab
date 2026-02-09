"""Shared constants for agent tools package."""

import os

AGENT_TAGS = ["agent", "infrastructure"]
AGENT_CONTAINER_NAME = "tomo-agent"
AGENT_IMAGE_NAME = "tomo-agent:latest"


def get_server_url() -> str:
    """Get the server URL from environment or default.

    Returns:
        Server URL for agent connections.
    """
    return os.getenv("SERVER_URL", "http://localhost:8000")

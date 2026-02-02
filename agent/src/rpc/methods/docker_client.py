"""Shared Docker client for RPC methods."""

import logging
import threading
from typing import Optional

import docker

logger = logging.getLogger(__name__)

_client: Optional[docker.DockerClient] = None
_client_lock = threading.Lock()


def get_client() -> docker.DockerClient:
    """Get or create Docker client (thread-safe singleton).

    Returns:
        The Docker client instance (singleton).
    """
    global _client
    if _client is None:
        with _client_lock:
            # Double-check after acquiring lock
            if _client is None:
                _client = docker.from_env()
    return _client


def reset_client() -> None:
    """Reset the Docker client (for testing purposes)."""
    global _client
    with _client_lock:
        _client = None

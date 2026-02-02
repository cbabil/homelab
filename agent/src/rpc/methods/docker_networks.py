"""Docker network RPC methods."""

import logging
from typing import Any, Dict, List

try:
    from .docker_client import get_client
except ImportError:
    from rpc.methods.docker_client import get_client

logger = logging.getLogger(__name__)


class NetworkMethods:
    """RPC methods for Docker network operations."""

    def list(self) -> List[Dict[str, Any]]:
        """List Docker networks.

        Returns:
            List of network information dictionaries.
        """
        client = get_client()
        networks = client.networks.list()
        return [
            {
                "id": n.short_id,
                "name": n.name,
                "driver": n.attrs.get("Driver", "bridge"),
            }
            for n in networks
        ]

    def create(self, name: str, driver: str = "bridge") -> Dict[str, str]:
        """Create a network.

        Args:
            name: Network name.
            driver: Network driver (default: "bridge").

        Returns:
            Created network information dictionary.
        """
        client = get_client()
        network = client.networks.create(name=name, driver=driver)
        return {"id": network.short_id, "name": network.name}

    def remove(self, name: str) -> Dict[str, str]:
        """Remove a network.

        Args:
            name: Network name or ID.

        Returns:
            Status dictionary.
        """
        client = get_client()
        network = client.networks.get(name)
        network.remove()
        return {"status": "removed"}

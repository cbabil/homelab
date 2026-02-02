"""Docker volume RPC methods."""

import logging
from typing import Any, Dict, List

try:
    from .docker_client import get_client
except ImportError:
    from rpc.methods.docker_client import get_client

logger = logging.getLogger(__name__)


class VolumeMethods:
    """RPC methods for Docker volume operations."""

    def list(self) -> List[Dict[str, Any]]:
        """List Docker volumes.

        Returns:
            List of volume information dictionaries.
        """
        client = get_client()
        volumes = client.volumes.list()
        return [
            {
                "name": v.name,
                "driver": v.attrs.get("Driver", "local"),
                "mountpoint": v.attrs.get("Mountpoint", ""),
            }
            for v in volumes
        ]

    def create(self, name: str, driver: str = "local") -> Dict[str, str]:
        """Create a volume.

        Args:
            name: Volume name.
            driver: Volume driver (default: "local").

        Returns:
            Created volume information dictionary.
        """
        client = get_client()
        volume = client.volumes.create(name=name, driver=driver)
        return {"name": volume.name, "driver": volume.attrs.get("Driver", driver)}

    def remove(self, name: str, force: bool = False) -> Dict[str, str]:
        """Remove a volume.

        Args:
            name: Volume name.
            force: Force removal.

        Returns:
            Status dictionary.
        """
        client = get_client()
        volume = client.volumes.get(name)
        volume.remove(force=force)
        return {"status": "removed"}

    def prune(self, filter: str = None) -> Dict[str, Any]:
        """Remove unused volumes.

        Args:
            filter: Optional filter string (e.g., "label=container=myapp")

        Returns:
            Prune result with space reclaimed.
        """
        client = get_client()
        filters = {}
        if filter:
            # Parse filter string like "label=container=myapp"
            if filter.startswith("label="):
                filters["label"] = [filter[6:]]
        result = client.volumes.prune(filters=filters if filters else None)
        return {
            "deleted": result.get("VolumesDeleted") or [],
            "space_reclaimed": result.get("SpaceReclaimed", 0),
        }

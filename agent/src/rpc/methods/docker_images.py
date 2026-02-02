"""Docker image RPC methods."""

import logging
from typing import Any, Dict, List

try:
    from .docker_client import get_client
except ImportError:
    from rpc.methods.docker_client import get_client

logger = logging.getLogger(__name__)


class ImageMethods:
    """RPC methods for Docker image operations."""

    def list(self) -> List[Dict[str, Any]]:
        """List Docker images.

        Returns:
            List of image information dictionaries.
        """
        client = get_client()
        images = client.images.list()
        return [
            {
                "id": img.short_id,
                "tags": img.tags,
                "size": img.attrs.get("Size", 0),
            }
            for img in images
        ]

    def pull(self, image: str, tag: str = "latest") -> Dict[str, Any]:
        """Pull an image from a registry.

        Args:
            image: Image name to pull.
            tag: Image tag (default: "latest").

        Returns:
            Pulled image information dictionary.
        """
        client = get_client()
        img = client.images.pull(image, tag=tag)
        return {"id": img.short_id, "tags": img.tags}

    def remove(self, image: str, force: bool = False) -> Dict[str, str]:
        """Remove an image.

        Args:
            image: Image name or ID.
            force: Force removal.

        Returns:
            Status dictionary.
        """
        client = get_client()
        client.images.remove(image, force=force)
        return {"status": "removed"}

    def prune(self) -> Dict[str, Any]:
        """Remove unused images.

        Returns:
            Prune result with space reclaimed.
        """
        client = get_client()
        result = client.images.prune()
        return {
            "deleted": result.get("ImagesDeleted") or [],
            "space_reclaimed": result.get("SpaceReclaimed", 0),
        }

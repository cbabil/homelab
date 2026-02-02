"""Volume mount validation.

Validates Docker volume mount specifications for security.
"""

import os
from typing import Tuple

from .constants import BLOCKED_VOLUME_PATTERNS, PROTECTED_PATHS


def validate_volume_mount(volume_spec: str) -> bool:
    """Validate a volume mount specification.

    Args:
        volume_spec: Volume spec like "/host:/container:ro"

    Returns:
        True if the mount is allowed.
    """
    parts = volume_spec.split(":")
    if len(parts) < 2:
        return True  # Named volume, allowed

    host_path = parts[0]

    # Check for docker socket
    if host_path in ["/var/run/docker.sock", "/run/docker.sock"]:
        return False

    # Normalize path
    host_path = os.path.normpath(host_path)

    # Check for blocked paths
    for blocked in BLOCKED_VOLUME_PATTERNS:
        if host_path == blocked.rstrip("/") or host_path.startswith(blocked):
            # Allow if explicitly read-only and not docker socket
            if len(parts) >= 3 and parts[2] == "ro":
                # Still block some paths even read-only
                if host_path.startswith("/proc") or host_path.startswith("/sys"):
                    return False
                continue
            return False

    return True


def validate_volume_path(host_path: str, mode: str = "rw") -> Tuple[bool, str]:
    """Validate a host path for volume mounting.

    Args:
        host_path: The host path to validate.
        mode: Mount mode ("rw" or "ro").

    Returns:
        Tuple of (is_valid, error_message).
    """
    host_path = os.path.normpath(host_path)

    # Block Docker socket mount
    if host_path in ["/var/run/docker.sock", "/run/docker.sock"]:
        return (False, "Mounting Docker socket is not allowed")

    # Check for protected paths with write access
    if mode == "rw":
        for protected in PROTECTED_PATHS:
            if host_path == protected or host_path.startswith(protected + "/"):
                return (False, f"Write access to {host_path} is not allowed")

    return (True, "")

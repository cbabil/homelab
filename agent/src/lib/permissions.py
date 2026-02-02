"""Permission levels for RPC methods.

Defines the permission model for controlling access to agent methods.
"""

from enum import Enum
from typing import Dict


class PermissionLevel(str, Enum):
    """Permission levels for RPC methods."""

    READ = "read"  # Read-only operations (info, status, logs)
    EXECUTE = "execute"  # Container management (start, stop, restart)
    ADMIN = "admin"  # Dangerous operations (exec, volume mounts)


# Method permission mapping
METHOD_PERMISSIONS: Dict[str, PermissionLevel] = {
    # System methods
    "system.info": PermissionLevel.READ,
    "system.get_metrics": PermissionLevel.READ,
    "system.exec": PermissionLevel.ADMIN,  # Restricted - uses allowlist
    # Docker read methods
    "docker.containers.list": PermissionLevel.READ,
    "docker.containers.get": PermissionLevel.READ,
    "docker.containers.logs": PermissionLevel.READ,
    "docker.images.list": PermissionLevel.READ,
    # Docker execute methods
    "docker.containers.start": PermissionLevel.EXECUTE,
    "docker.containers.stop": PermissionLevel.EXECUTE,
    "docker.containers.restart": PermissionLevel.EXECUTE,
    "docker.containers.remove": PermissionLevel.EXECUTE,
    "docker.containers.run": PermissionLevel.ADMIN,  # Restricted
    "docker.images.pull": PermissionLevel.EXECUTE,
    "docker.images.remove": PermissionLevel.EXECUTE,
    # Agent methods
    "agent.ping": PermissionLevel.READ,
    "agent.update": PermissionLevel.ADMIN,
    "agent.restart": PermissionLevel.ADMIN,
    "config.update": PermissionLevel.ADMIN,
}


def get_method_permission(method: str) -> PermissionLevel:
    """Get the permission level required for an RPC method.

    Args:
        method: The RPC method name.

    Returns:
        Required permission level (defaults to ADMIN for unknown methods).
    """
    return METHOD_PERMISSIONS.get(method, PermissionLevel.ADMIN)

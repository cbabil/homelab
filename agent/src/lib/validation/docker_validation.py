"""Docker command and parameter validation.

Validates Docker run commands and container parameters for security.
"""

import logging
import os
import shlex
from typing import Any, Dict, Tuple

from .constants import BLOCKED_DOCKER_PARAMS, BLOCKED_DOCKER_RUN_FLAGS, PROTECTED_PATHS
from .volume_validation import validate_volume_mount

logger = logging.getLogger(__name__)


def validate_docker_run_command(command: str) -> Tuple[bool, str]:
    """Validate docker run command for dangerous flags.

    Args:
        command: The docker run command string.

    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        tokens = shlex.split(command)
    except ValueError as e:
        return (False, f"Invalid command syntax: {e}")

    for i, token in enumerate(tokens):
        token_lower = token.lower()

        # Check blocked flags
        for blocked in BLOCKED_DOCKER_RUN_FLAGS:
            if token_lower == blocked or token_lower.startswith(
                blocked.split("=")[0] + "="
            ):
                if blocked.split("=")[0] in token_lower:
                    if "=" in token:
                        _, value = token.split("=", 1)
                        blocked_value = (
                            blocked.split("=")[1] if "=" in blocked else None
                        )
                        if blocked_value and value.upper() == blocked_value:
                            return (False, f"Blocked flag: {token}")
                    elif token_lower == blocked:
                        return (False, f"Blocked flag: {token}")

        # Check for --privileged
        if token_lower == "--privileged":
            return (False, "Privileged mode is not allowed")

        # Check for dangerous capability additions
        if token_lower.startswith("--cap-add="):
            cap = token.split("=", 1)[1].upper()
            if cap in {"ALL", "SYS_ADMIN", "SYS_PTRACE", "SYS_RAWIO", "NET_ADMIN"}:
                return (False, f"Capability {cap} is not allowed")

        # Check for host namespace flags
        for ns in ["--pid=", "--network=", "--ipc=", "--userns=", "--uts="]:
            if token_lower.startswith(ns) and token_lower.endswith("host"):
                return (False, f"Host namespace mode is not allowed: {token}")

        # Check volume mounts
        if token_lower.startswith("-v=") or token_lower.startswith("--volume="):
            volume_spec = token.split("=", 1)[1]
            if not validate_volume_mount(volume_spec):
                return (False, f"Blocked volume mount: {volume_spec}")

        if token in ["-v", "--volume"] and i + 1 < len(tokens):
            volume_spec = tokens[i + 1]
            if not validate_volume_mount(volume_spec):
                return (False, f"Blocked volume mount: {volume_spec}")

        # Check for device mounts
        if token_lower.startswith("--device="):
            return (False, "Device mounts are not allowed")

        # Check security options
        if token_lower.startswith("--security-opt="):
            opt = token.split("=", 1)[1].lower()
            if "unconfined" in opt or "disabled" in opt:
                return (False, f"Insecure security option: {token}")

    return (True, "")


def validate_docker_params(params: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate Docker container parameters for security.

    Args:
        params: Container creation parameters.

    Returns:
        Tuple of (is_valid, error_message).
    """
    # Check for privileged mode
    if params.get("privileged"):
        return (False, "Privileged containers are not allowed")

    # Check capabilities
    cap_add = params.get("cap_add", [])
    for blocked in BLOCKED_DOCKER_PARAMS["cap_add"]:
        if blocked in cap_add:
            return (False, f"Capability {blocked} is not allowed")

    # Check namespace sharing
    for ns_param in ["pid_mode", "network_mode", "ipc_mode", "userns_mode"]:
        if params.get(ns_param) == "host":
            return (False, f"{ns_param}=host is not allowed")

    # Validate volume mounts
    volumes = params.get("volumes", {})
    for host_path, mount_config in volumes.items():
        host_path = os.path.normpath(host_path)

        mode = (
            mount_config.get("mode", "rw") if isinstance(mount_config, dict) else "rw"
        )
        if mode == "rw":
            for protected in PROTECTED_PATHS:
                if host_path == protected or host_path.startswith(protected + "/"):
                    return (False, f"Write access to {host_path} is not allowed")

        if host_path in ["/var/run/docker.sock", "/run/docker.sock"]:
            return (False, "Mounting Docker socket is not allowed")

    return (True, "")

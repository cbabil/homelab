"""
Docker Command Builders

Builds docker commands and parses docker output.
"""

import re
import shlex
from typing import Any

from models.marketplace import DockerConfig


def build_run_command(
    docker: DockerConfig,
    container_name: str,
    config: dict[str, Any],
    restart_policy: str = None,
) -> str:
    """Build docker run command for an app.

    Args:
        docker: Docker configuration from app definition
        container_name: Name for the container
        config: User-provided configuration overrides
        restart_policy: Override restart policy (default: use docker config)

    Returns:
        Complete docker run command string
    """
    parts = ["docker run -d"]

    # Container name
    parts.append(f"--name {shlex.quote(container_name)}")

    # Restart policy - use override or default from config
    policy = restart_policy if restart_policy is not None else docker.restart_policy
    parts.append(f"--restart {shlex.quote(policy)}")

    # Port mappings
    for port in docker.ports:
        host_port = config.get("ports", {}).get(str(port.container), port.host)
        parts.append(
            f"-p {shlex.quote(f'{host_port}:{port.container}/{port.protocol}')}"
        )

    # Volume mappings
    for volume in docker.volumes:
        host_path = config.get("volumes", {}).get(
            volume.container_path, volume.host_path
        )
        ro = ":ro" if volume.readonly else ""
        parts.append(f"-v {shlex.quote(f'{host_path}:{volume.container_path}{ro}')}")

    # Environment variables from config
    for key, value in config.get("env", {}).items():
        parts.append(f"-e {shlex.quote(f'{key}={value}')}")

    # Network mode
    if docker.network_mode:
        parts.append(f"--network {shlex.quote(docker.network_mode)}")

    # Privileged mode
    if docker.privileged:
        parts.append("--privileged")

    # Capabilities
    for cap in docker.capabilities:
        parts.append(f"--cap-add {shlex.quote(cap)}")

    # Image
    parts.append(shlex.quote(docker.image))

    return " ".join(parts)


def parse_pull_progress(line: str, layer_progress: dict) -> int:
    """Parse docker pull output line and return overall progress percentage.

    Docker pull output looks like:
    - "abc123: Pulling fs layer"
    - "abc123: Downloading [====>    ] 10MB/100MB"
    - "abc123: Download complete"
    - "abc123: Pull complete"

    Args:
        line: Single line of docker pull output
        layer_progress: Dict tracking progress per layer (modified in place)

    Returns:
        Overall progress as integer 0-100
    """
    try:
        # Match downloading progress
        download_match = re.match(
            r"^([a-f0-9]+): Downloading.*?(\d+(?:\.\d+)?)\s*[MKG]?B?/(\d+(?:\.\d+)?)\s*[MKG]?B",
            line,
        )
        if download_match:
            layer_id = download_match.group(1)
            current = float(download_match.group(2))
            total = float(download_match.group(3))
            if total > 0:
                layer_progress[layer_id] = min(100, int((current / total) * 100))

        # Match extracting progress
        extract_match = re.match(
            r"^([a-f0-9]+): Extracting.*?(\d+(?:\.\d+)?)\s*[MKG]?B?/(\d+(?:\.\d+)?)\s*[MKG]?B",
            line,
        )
        if extract_match:
            layer_id = extract_match.group(1)
            current = float(extract_match.group(2))
            total = float(extract_match.group(3))
            if total > 0:
                # Extracting counts as 50-100% for the layer
                layer_progress[layer_id] = 50 + min(50, int((current / total) * 50))

        # Match completed states
        complete_match = re.match(
            r"^([a-f0-9]+): (Download complete|Pull complete|Already exists)", line
        )
        if complete_match:
            layer_id = complete_match.group(1)
            layer_progress[layer_id] = 100

        # Match pulling layer (started)
        pulling_match = re.match(r"^([a-f0-9]+): Pulling fs layer", line)
        if pulling_match:
            layer_id = pulling_match.group(1)
            if layer_id not in layer_progress:
                layer_progress[layer_id] = 0

        # Calculate overall progress
        if layer_progress:
            return int(sum(layer_progress.values()) / len(layer_progress))
        return 0

    except Exception:
        return 0


def parse_container_inspect(stdout: str) -> dict[str, Any]:
    """Parse docker inspect JSON output.

    Args:
        stdout: Raw docker inspect output

    Returns:
        Dict with networks, named_volumes, and bind_mounts
    """
    import json

    result = {"networks": [], "named_volumes": [], "bind_mounts": []}

    try:
        container_info = json.loads(stdout)
        if not container_info:
            return result

        info = container_info[0]

        # Get networks
        network_settings = info.get("NetworkSettings", {}).get("Networks", {})
        result["networks"] = list(network_settings.keys())

        # Get mounts
        for mount in info.get("Mounts", []):
            mount_type = mount.get("Type", "")
            if mount_type == "volume":
                result["named_volumes"].append(
                    {
                        "name": mount.get("Name", ""),
                        "destination": mount.get("Destination", ""),
                        "mode": mount.get("Mode", "rw"),
                    }
                )
            elif mount_type == "bind":
                result["bind_mounts"].append(
                    {
                        "source": mount.get("Source", ""),
                        "destination": mount.get("Destination", ""),
                        "mode": mount.get("Mode", "rw"),
                    }
                )

    except Exception as e:
        import structlog

        structlog.get_logger("docker_commands").debug(
            "Failed to parse container inspect output", error=str(e)
        )

    return result

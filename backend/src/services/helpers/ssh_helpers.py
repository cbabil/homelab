"""
SSH Service Helper Functions

Contains helper methods for SSH operations to maintain 100-line file limit.
Separated from main SSH service for better organization.
"""

import asyncio
import io
from typing import Any

import paramiko
import structlog

logger = structlog.get_logger("ssh_helpers")


async def connect_password(
    client: paramiko.SSHClient,
    host: str,
    port: int,
    username: str,
    credentials: dict,
    config: dict,
) -> None:
    """Connect using password authentication."""
    await asyncio.to_thread(
        client.connect,
        hostname=host,
        port=port,
        username=username,
        password=credentials.get("password"),
        **config,
    )


async def connect_key(
    client: paramiko.SSHClient,
    host: str,
    port: int,
    username: str,
    credentials: dict,
    config: dict,
) -> None:
    """Connect using SSH key authentication."""
    private_key_data = credentials.get("private_key", "")
    passphrase = credentials.get("passphrase")

    # Try different key types (Ed25519, RSA, ECDSA)
    key_classes = [
        paramiko.Ed25519Key,
        paramiko.RSAKey,
        paramiko.ECDSAKey,
    ]

    private_key = None
    last_error = None

    for key_class in key_classes:
        try:
            # Create fresh StringIO for each attempt (StringIO gets consumed after read)
            key_file = io.StringIO(private_key_data)
            private_key = key_class.from_private_key(key_file, password=passphrase)
            logger.info(f"Loaded SSH key as {key_class.__name__}")
            break
        except Exception as e:
            last_error = e
            logger.debug(f"Key type {key_class.__name__} failed: {e}")
            continue

    if private_key is None:
        logger.error("Could not parse private key", last_error=str(last_error))
        raise ValueError(
            f"Could not parse private key with any supported format: {last_error}"
        )

    await asyncio.to_thread(
        client.connect,
        hostname=host,
        port=port,
        username=username,
        pkey=private_key,
        **config,
    )


async def get_system_info(client: paramiko.SSHClient) -> dict[str, Any]:
    """Gather basic system information from connected client."""
    # Check docker version - simple and reliable
    docker_cmd = 'command -v docker >/dev/null 2>&1 && docker --version | cut -d" " -f3 | tr -d "," || echo "Not installed"'
    # Check if tomo-agent container is running (use docker inspect for reliability)
    agent_cmd = 'docker inspect tomo-agent --format "{{.State.Running}}" 2>/dev/null | grep -q true && echo "running" || echo "not running"'
    # Get agent version from container label
    agent_version_cmd = 'docker inspect tomo-agent --format "{{index .Config.Labels \\"version\\"}}" 2>/dev/null || echo ""'
    commands = {
        "os": "cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"'",
        "kernel": "uname -r",
        "architecture": "uname -m",
        "docker_version": docker_cmd,
        "agent_status": agent_cmd,
        "agent_version": agent_version_cmd,
    }

    system_info = {}

    for key, command in commands.items():
        try:
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode().strip()
            system_info[key] = output
        except Exception as e:
            logger.warning(f"Failed to get {key}", error=str(e))
            system_info[key] = "Unknown"

    return system_info

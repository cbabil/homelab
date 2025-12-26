"""
SSH Service Helper Functions

Contains helper methods for SSH operations to maintain 100-line file limit.
Separated from main SSH service for better organization.
"""

import paramiko
import asyncio
import io
from typing import Dict, Any
import structlog


logger = structlog.get_logger("ssh_helpers")


async def connect_password(
    client: paramiko.SSHClient,
    host: str,
    port: int,
    username: str,
    credentials: dict,
    config: dict
) -> None:
    """Connect using password authentication."""
    await asyncio.to_thread(
        client.connect,
        hostname=host,
        port=port,
        username=username,
        password=credentials.get('password'),
        **config
    )


async def connect_key(
    client: paramiko.SSHClient,
    host: str,
    port: int,
    username: str,
    credentials: dict,
    config: dict
) -> None:
    """Connect using SSH key authentication."""
    private_key_data = credentials.get('private_key', '')
    passphrase = credentials.get('passphrase')
    
    # Parse private key from string
    private_key = paramiko.RSAKey.from_private_key(
        io.StringIO(private_key_data),
        password=passphrase
    )
    
    await asyncio.to_thread(
        client.connect,
        hostname=host,
        port=port,
        username=username,
        pkey=private_key,
        **config
    )


async def get_system_info(client: paramiko.SSHClient) -> Dict[str, Any]:
    """Gather basic system information from connected client."""
    commands = {
        'os': 'cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d \'\"\'',
        'kernel': 'uname -r',
        'architecture': 'uname -m',
        'uptime': 'uptime -p'
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
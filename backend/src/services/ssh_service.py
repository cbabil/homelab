"""
SSH Service Module

Provides secure SSH connection management using paramiko.
Implements security-first SSH practices as per architectural decisions.
"""

import paramiko
import asyncio
import io
from typing import Dict, Optional, Tuple, Any
import structlog
from lib.encryption import CredentialManager


logger = structlog.get_logger("ssh_service")


class SSHService:
    """Manages secure SSH connections to remote servers."""
    
    def __init__(self):
        """Initialize SSH service with secure defaults."""
        self.connections: Dict[str, paramiko.SSHClient] = {}
        self.connection_configs = {
            'timeout': 30,
            'auth_timeout': 10,
            'banner_timeout': 30,
            'compress': True
        }
        logger.info("SSH service initialized")
    
    def create_ssh_client(self) -> paramiko.SSHClient:
        """Create a securely configured SSH client."""
        client = paramiko.SSHClient()
        
        # Security: Use AutoAddPolicy for development, RejectPolicy for production
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Configure client transport settings
        client.get_transport = lambda: self._configure_transport(client.get_transport())
        
        return client
    
    def _configure_transport(self, transport) -> paramiko.Transport:
        """Configure SSH transport with security settings."""
        if transport:
            transport.set_keepalive(30)
        return transport
    
    async def test_connection(
        self,
        host: str,
        port: int,
        username: str,
        auth_type: str,
        credentials: dict
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        Test SSH connection and return system info if successful.
        
        Args:
            host: Server hostname or IP address
            port: SSH port number
            username: SSH username
            auth_type: Authentication type ('password' or 'key')
            credentials: Authentication credentials
            
        Returns:
            Tuple of (success, message, system_info)
        """
        from services.ssh_helpers import connect_password, connect_key, get_system_info
        
        client = self.create_ssh_client()
        
        try:
            logger.info("Testing SSH connection", host=host, port=port, username=username)
            
            if auth_type == 'password':
                await connect_password(client, host, port, username, credentials, self.connection_configs)
            elif auth_type == 'key':
                await connect_key(client, host, port, username, credentials, self.connection_configs)
            else:
                raise ValueError(f"Unsupported auth type: {auth_type}")
            
            # Get basic system information
            system_info = await get_system_info(client)
            
            client.close()
            
            logger.info("SSH connection test successful", host=host)
            return True, "Connection successful", system_info
            
        except Exception as e:
            logger.error("SSH connection failed", host=host, error=str(e))
            client.close()
            return False, str(e), None

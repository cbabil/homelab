"""
Server Management Service

Handles server connection management with database persistence and encryption.
"""

from typing import Dict, Any, List, Optional
import structlog
from models.server import ServerConnection, ServerStatus, AuthType
from services.database_service import DatabaseService
from lib.encryption import CredentialManager


logger = structlog.get_logger("server_service")


class ServerService:
    """Service for managing server connections with database persistence."""

    def __init__(self, db_service: DatabaseService = None):
        """Initialize server service with database and encryption."""
        self.db_service = db_service
        try:
            self.credential_manager = CredentialManager()
        except ValueError:
            logger.warning("Credential manager not initialized - encryption disabled")
            self.credential_manager = None
        logger.info("Server service initialized")

    async def add_server(
        self,
        server_id: str,
        name: str,
        host: str,
        port: int,
        username: str,
        auth_type: str,
        credentials: Dict[str, str]
    ) -> Optional[ServerConnection]:
        """Add new server with encrypted credentials."""
        try:
            encrypted_creds = ""
            if self.credential_manager and credentials:
                encrypted_creds = self.credential_manager.encrypt_credentials(credentials)

            server = await self.db_service.create_server(
                id=server_id,
                name=name,
                host=host,
                port=port,
                username=username,
                auth_type=auth_type,
                encrypted_credentials=encrypted_creds
            )

            logger.info("Server added", server_id=server_id, name=name)
            return server
        except Exception as e:
            logger.error("Failed to add server", error=str(e))
            return None

    async def get_server(self, server_id: str) -> Optional[ServerConnection]:
        """Get server by ID."""
        return await self.db_service.get_server_by_id(server_id)

    async def get_all_servers(self) -> List[ServerConnection]:
        """Get all servers."""
        return await self.db_service.get_all_servers_from_db()

    async def get_credentials(self, server_id: str) -> Optional[Dict[str, str]]:
        """Get decrypted credentials for a server."""
        try:
            encrypted = await self.db_service.get_server_credentials(server_id)
            if not encrypted or not self.credential_manager:
                return None
            return self.credential_manager.decrypt_credentials(encrypted)
        except Exception as e:
            logger.error("Failed to get credentials", error=str(e))
            return None

    async def update_server(
        self,
        server_id: str,
        name: str = None,
        host: str = None,
        port: int = None,
        username: str = None
    ) -> bool:
        """Update server configuration."""
        return await self.db_service.update_server(
            server_id=server_id,
            name=name,
            host=host,
            port=port,
            username=username
        )

    async def update_server_status(self, server_id: str, status: ServerStatus) -> bool:
        """Update server connection status."""
        return await self.db_service.update_server(
            server_id=server_id,
            status=status.value
        )

    async def delete_server(self, server_id: str) -> bool:
        """Delete server and its credentials."""
        return await self.db_service.delete_server(server_id)

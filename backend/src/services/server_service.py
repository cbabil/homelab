"""
Server Management Service

Handles server connection management with database persistence and encryption.
"""

from typing import Any

import structlog

from lib.encryption import CredentialManager
from models.server import ServerConnection, ServerStatus
from services.database_service import DatabaseService

logger = structlog.get_logger("server_service")


class ServerService:
    """Service for managing server connections with database persistence."""

    def __init__(self, db_service: DatabaseService = None):
        """Initialize server service with database and encryption."""
        self.db_service = db_service
        try:
            self.credential_manager = CredentialManager()
        except (ValueError, OSError) as e:
            logger.warning("Credential manager unavailable", error=str(e))
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
        credentials: dict[str, str],
    ) -> ServerConnection | None:
        """Add new server with encrypted credentials."""
        try:
            encrypted_creds = ""
            if credentials and self.credential_manager:
                encrypted_creds = self.credential_manager.encrypt_credentials(
                    credentials
                )

            server = await self.db_service.create_server(
                id=server_id,
                name=name,
                host=host,
                port=port,
                username=username,
                auth_type=auth_type,
                encrypted_credentials=encrypted_creds,
            )

            if server:
                logger.info("Server added", server_id=server_id, name=name)
            return server
        except Exception as e:
            logger.error("Failed to add server", error=str(e))
            return None

    async def get_server(self, server_id: str) -> ServerConnection | None:
        """Get server by ID."""
        logger.info("get_server called", server_id=server_id)
        result = await self.db_service.get_server_by_id(server_id)
        logger.info("get_server result", server_id=server_id, found=result is not None)
        return result

    async def get_server_by_connection(
        self, host: str, port: int, username: str
    ) -> ServerConnection | None:
        """Get server by connection details (host, port, username)."""
        return await self.db_service.get_server_by_connection(host, port, username)

    async def get_all_servers(self) -> list[ServerConnection]:
        """Get all servers."""
        return await self.db_service.get_all_servers_from_db()

    async def get_credentials(self, server_id: str) -> dict[str, str] | None:
        """Get decrypted credentials for a server."""
        try:
            if not self.credential_manager:
                return None
            encrypted = await self.db_service.get_server_credentials(server_id)
            if not encrypted:
                return None
            return self.credential_manager.decrypt_credentials(encrypted)
        except Exception as e:
            logger.error("Failed to get credentials", error=str(e))
            return None

    async def update_credentials(
        self, server_id: str, credentials: dict[str, str]
    ) -> bool:
        """Update server credentials."""
        try:
            if not self.credential_manager:
                logger.error("Credential manager unavailable")
                return False
            encrypted = self.credential_manager.encrypt_credentials(credentials)
            return await self.db_service.update_server_credentials(server_id, encrypted)
        except Exception as e:
            logger.error("Failed to update credentials", error=str(e))
            return False

    async def update_server(
        self,
        server_id: str,
        name: str = None,
        host: str = None,
        port: int = None,
        username: str = None,
        auth_type: str = None,
    ) -> bool:
        """Update server configuration."""
        return await self.db_service.update_server(
            server_id=server_id,
            name=name,
            host=host,
            port=port,
            username=username,
            auth_type=auth_type,
        )

    async def update_server_status(self, server_id: str, status: ServerStatus) -> bool:
        """Update server connection status."""
        return await self.db_service.update_server(
            server_id=server_id, status=status.value
        )

    async def delete_server(self, server_id: str) -> bool:
        """Delete server and its credentials."""
        return await self.db_service.delete_server(server_id)

    async def update_server_system_info(
        self, server_id: str, system_info: dict[str, Any]
    ) -> bool:
        """Update server system information and Docker status."""
        import json
        from datetime import UTC, datetime

        try:
            # Determine if Docker is installed
            docker_version = system_info.get("docker_version", "")
            docker_installed = bool(
                docker_version
                and docker_version.lower() not in ("not installed", "n/a", "")
            )

            # Store system_info as JSON
            system_info_json = json.dumps(system_info)
            updated_at = datetime.now(UTC).isoformat()

            success = await self.db_service.update_server(
                server_id=server_id,
                system_info=system_info_json,
                docker_installed=1 if docker_installed else 0,
                system_info_updated_at=updated_at,
            )

            if success:
                agent_status = system_info.get("agent_status", "unknown")
                agent_version = system_info.get("agent_version", "")
                logger.info(
                    "Server system info updated",
                    server_id=server_id,
                    docker_installed=docker_installed,
                    docker_version=docker_version,
                    agent_status=agent_status,
                    agent_version=agent_version or "n/a",
                )
            return success
        except Exception as e:
            logger.error("Failed to update system info", error=str(e))
            return False

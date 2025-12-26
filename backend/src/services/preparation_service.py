"""
Server Preparation Service

Handles automated Docker installation on remote servers.
Supports Ubuntu, Debian, RHEL, Rocky, and Fedora.
"""

import uuid
from datetime import datetime, UTC
from typing import Dict, Any, Optional
import structlog
from models.preparation import (
    PreparationStatus, PreparationStep, PreparationLog,
    ServerPreparation, PREPARATION_STEPS
)

logger = structlog.get_logger("preparation_service")


# OS-specific Docker installation commands
DOCKER_COMMANDS = {
    "ubuntu": {
        "update_packages": "sudo apt-get update -y",
        "install_dependencies": "sudo apt-get install -y ca-certificates curl gnupg",
        "install_docker": """
            sudo install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            sudo chmod a+r /etc/apt/keyrings/docker.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt-get update -y
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        """,
        "start_docker": "sudo systemctl enable docker && sudo systemctl start docker",
        "configure_user": "sudo usermod -aG docker $USER",
        "verify_docker": "docker --version && docker compose version"
    },
    "debian": {
        "update_packages": "sudo apt-get update -y",
        "install_dependencies": "sudo apt-get install -y ca-certificates curl gnupg",
        "install_docker": """
            sudo install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            sudo chmod a+r /etc/apt/keyrings/docker.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt-get update -y
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        """,
        "start_docker": "sudo systemctl enable docker && sudo systemctl start docker",
        "configure_user": "sudo usermod -aG docker $USER",
        "verify_docker": "docker --version && docker compose version"
    },
    "rhel": {
        "update_packages": "sudo dnf update -y",
        "install_dependencies": "sudo dnf install -y yum-utils",
        "install_docker": """
            sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        """,
        "start_docker": "sudo systemctl enable docker && sudo systemctl start docker",
        "configure_user": "sudo usermod -aG docker $USER",
        "verify_docker": "docker --version && docker compose version"
    },
    "fedora": {
        "update_packages": "sudo dnf update -y",
        "install_dependencies": "sudo dnf install -y dnf-plugins-core",
        "install_docker": """
            sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
            sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        """,
        "start_docker": "sudo systemctl enable docker && sudo systemctl start docker",
        "configure_user": "sudo usermod -aG docker $USER",
        "verify_docker": "docker --version && docker compose version"
    }
}


class PreparationService:
    """Service for preparing servers with Docker."""

    def __init__(self, ssh_service, server_service, db_service):
        """Initialize preparation service."""
        self.ssh_service = ssh_service
        self.server_service = server_service
        self.db_service = db_service
        logger.info("Preparation service initialized")

    def _detect_os_type(self, os_release: str) -> str:
        """Detect OS type from release string."""
        os_lower = os_release.lower()
        if "ubuntu" in os_lower:
            return "ubuntu"
        elif "debian" in os_lower:
            return "debian"
        elif "rocky" in os_lower or "centos" in os_lower or "rhel" in os_lower or "red hat" in os_lower:
            return "rhel"
        elif "fedora" in os_lower:
            return "fedora"
        else:
            return "unknown"

    def _get_docker_commands(self, os_type: str) -> Dict[str, str]:
        """Get Docker installation commands for OS type."""
        return DOCKER_COMMANDS.get(os_type, DOCKER_COMMANDS["ubuntu"])

    async def start_preparation(self, server_id: str) -> Optional[ServerPreparation]:
        """Start server preparation workflow."""
        try:
            server = await self.server_service.get_server(server_id)
            if not server:
                logger.error("Server not found", server_id=server_id)
                return None

            prep_id = f"prep-{uuid.uuid4().hex[:8]}"
            now = datetime.now(UTC).isoformat()

            preparation = await self.db_service.create_preparation(
                id=prep_id,
                server_id=server_id,
                status=PreparationStatus.PENDING.value,
                started_at=now
            )

            logger.info("Preparation started", prep_id=prep_id, server_id=server_id)
            return preparation

        except Exception as e:
            logger.error("Failed to start preparation", error=str(e))
            return None

    async def get_preparation_status(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get current preparation status for a server."""
        try:
            prep = await self.db_service.get_preparation(server_id)
            if not prep:
                return None

            logs = await self.db_service.get_preparation_logs(server_id)

            return {
                "id": prep.id,
                "server_id": server_id,
                "status": prep.status,
                "current_step": prep.current_step,
                "detected_os": prep.detected_os,
                "started_at": prep.started_at,
                "completed_at": prep.completed_at,
                "error_message": prep.error_message,
                "logs": [log.model_dump() for log in logs]
            }
        except Exception as e:
            logger.error("Failed to get status", error=str(e))
            return None

"""
Docker Tools

Provides Docker installation and management capabilities for remote servers.
"""

import uuid
from datetime import datetime, UTC
from typing import Dict, Any, Optional
import structlog
from models.server import ServerStatus
from services.ssh_service import SSHService
from services.server_service import ServerService
from services.database_service import DatabaseService
from tools.common import log_event


logger = structlog.get_logger("docker_tools")


# System app ID for Docker installation tracking
SYSTEM_DOCKER_APP_ID = "system-docker"

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
    },
    "alpine": {
        "update_packages": "sudo apk update",
        "install_dependencies": "sudo apk add --no-cache curl",
        "install_docker": "sudo apk add --no-cache docker docker-cli docker-compose",
        "start_docker": "sudo rc-update add docker boot && sudo service docker start",
        "configure_user": "sudo addgroup $USER docker",
        "verify_docker": "docker --version && docker compose version"
    },
    "arch": {
        "update_packages": "sudo pacman -Syu --noconfirm",
        "install_dependencies": "sudo pacman -S --noconfirm curl",
        "install_docker": "sudo pacman -S --noconfirm docker docker-compose",
        "start_docker": "sudo systemctl enable docker && sudo systemctl start docker",
        "configure_user": "sudo usermod -aG docker $USER",
        "verify_docker": "docker --version && docker compose version"
    }
}

# List of supported OS types
SUPPORTED_OS_TYPES = list(DOCKER_COMMANDS.keys())


def _detect_os_type(os_info: str) -> str:
    """Detect OS type from OS release string."""
    os_lower = os_info.lower()
    if "ubuntu" in os_lower:
        return "ubuntu"
    elif "debian" in os_lower:
        return "debian"
    elif "rocky" in os_lower or "centos" in os_lower or "rhel" in os_lower or "red hat" in os_lower:
        return "rhel"
    elif "fedora" in os_lower:
        return "fedora"
    elif "alpine" in os_lower:
        return "alpine"
    elif "arch" in os_lower or "manjaro" in os_lower:
        return "arch"
    return "unknown"


def _build_docker_install_script(os_type: str) -> Optional[str]:
    """Build Docker installation script for the given OS type."""
    if os_type not in DOCKER_COMMANDS:
        return None

    commands = DOCKER_COMMANDS[os_type]

    script_parts = [
        "set -e",
        f"# Update packages ({os_type})",
        commands["update_packages"],
        "# Install dependencies",
        commands["install_dependencies"],
        "# Install Docker",
        commands["install_docker"],
        "# Start Docker",
        commands["start_docker"],
        "# Configure user",
        commands["configure_user"],
        "# Verify installation",
        commands["verify_docker"]
    ]

    return "\n".join(script_parts)


# OS-specific Docker update commands
DOCKER_UPDATE_COMMANDS = {
    "ubuntu": """
        sudo apt-get update -y
        sudo apt-get upgrade -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        sudo systemctl restart docker
        docker --version && docker compose version
    """,
    "debian": """
        sudo apt-get update -y
        sudo apt-get upgrade -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        sudo systemctl restart docker
        docker --version && docker compose version
    """,
    "rhel": """
        sudo dnf update -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        sudo systemctl restart docker
        docker --version && docker compose version
    """,
    "fedora": """
        sudo dnf update -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        sudo systemctl restart docker
        docker --version && docker compose version
    """,
    "alpine": """
        sudo apk update
        sudo apk upgrade docker docker-cli docker-compose
        sudo service docker restart
        docker --version && docker compose version
    """,
    "arch": """
        sudo pacman -Syu --noconfirm docker docker-compose
        sudo systemctl restart docker
        docker --version && docker compose version
    """
}

# OS-specific Docker removal commands
DOCKER_REMOVE_COMMANDS = {
    "ubuntu": """
        sudo systemctl stop docker || true
        sudo apt-get purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin || true
        sudo rm -rf /var/lib/docker /var/lib/containerd
        sudo rm -f /etc/apt/sources.list.d/docker.list
        sudo rm -f /etc/apt/keyrings/docker.gpg
    """,
    "debian": """
        sudo systemctl stop docker || true
        sudo apt-get purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin || true
        sudo rm -rf /var/lib/docker /var/lib/containerd
        sudo rm -f /etc/apt/sources.list.d/docker.list
        sudo rm -f /etc/apt/keyrings/docker.gpg
    """,
    "rhel": """
        sudo systemctl stop docker || true
        sudo dnf remove -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin || true
        sudo rm -rf /var/lib/docker /var/lib/containerd
    """,
    "fedora": """
        sudo systemctl stop docker || true
        sudo dnf remove -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin || true
        sudo rm -rf /var/lib/docker /var/lib/containerd
    """,
    "alpine": """
        sudo service docker stop || true
        sudo apk del docker docker-cli docker-compose || true
        sudo rm -rf /var/lib/docker
    """,
    "arch": """
        sudo systemctl stop docker || true
        sudo pacman -Rns --noconfirm docker docker-compose || true
        sudo rm -rf /var/lib/docker
    """
}


DOCKER_TAGS = ["docker", "infrastructure"]


class DockerTools:
    """Docker management tools for the MCP server."""

    def __init__(
        self,
        ssh_service: SSHService,
        server_service: ServerService,
        database_service: DatabaseService
    ):
        """Initialize Docker tools."""
        self.ssh_service = ssh_service
        self.server_service = server_service
        self.db_service = database_service
        logger.info("Docker tools initialized")

    async def install_docker(
        self,
        server_id: str = None,
        host: str = None,
        port: int = None,
        username: str = None,
        auth_type: str = None,
        password: str = None,
        private_key: str = None,
        tracked: bool = False
    ) -> Dict[str, Any]:
        """
        Install Docker on a remote server.

        Can be called two ways:
        1. With server_id: Uses saved server credentials
        2. With direct params: Uses provided host/port/username/credentials

        Args:
            server_id: ID of saved server (optional)
            host: Server hostname (required if no server_id)
            port: SSH port (required if no server_id)
            username: SSH username (required if no server_id)
            auth_type: 'password' or 'key' (required if no server_id)
            password: SSH password (if auth_type='password')
            private_key: SSH private key (if auth_type='key')
            tracked: If True, starts async installation with progress tracking.
                     Use get_docker_install_status to monitor. Requires server_id.

        Returns:
            Dict with success status. If tracked=True, includes installation_id.
        """
        from lib.security import validate_server_input

        try:
            # Handle tracked installation (async with progress monitoring)
            if tracked:
                if not server_id:
                    return {
                        "success": False,
                        "message": "server_id is required for tracked installation",
                        "error": "MISSING_SERVER_ID"
                    }

                install_id = f"docker-{uuid.uuid4().hex[:8]}"
                installation = await self.db_service.create_installation(
                    id=install_id,
                    server_id=server_id,
                    app_id=SYSTEM_DOCKER_APP_ID,
                    container_name="system-docker",
                    status="pending",
                    config={"install_type": "docker", "detected_os": None},
                    installed_at=datetime.now(UTC).isoformat()
                )

                if not installation:
                    await log_event("docker", "ERROR", f"Docker installation failed to start: {server_id}", DOCKER_TAGS, {
                        "server_id": server_id
                    })
                    return {
                        "success": False,
                        "message": "Failed to start Docker installation",
                        "error": "INSTALL_START_FAILED"
                    }

                await log_event("docker", "INFO", f"Docker installation started: {server_id}", DOCKER_TAGS, {
                    "server_id": server_id,
                    "installation_id": installation.id
                })
                logger.info("Docker installation started", server_id=server_id, install_id=installation.id)
                return {
                    "success": True,
                    "data": {"installation_id": installation.id, "server_id": server_id},
                    "message": "Docker installation started (use get_docker_install_status to monitor)"
                }

            # Synchronous installation (one-shot)
            # Determine if using saved server or direct credentials
            server_name = None
            if server_id:
                # Use saved server
                server = await self.server_service.get_server(server_id)
                if not server:
                    return {
                        "success": False,
                        "message": "Server not found",
                        "error": "SERVER_NOT_FOUND"
                    }

                server_name = server.name
                credentials = await self.server_service.get_credentials(server_id)
                if not credentials:
                    return {
                        "success": False,
                        "message": "Credentials not found",
                        "error": "CREDENTIALS_NOT_FOUND"
                    }

                host = server.host
                port = server.port
                username = server.username
                auth_type = server.auth_type.value
                os_info = server.system_info.os if server.system_info else ""

                # Set status to preparing
                await self.server_service.update_server_status(server_id, ServerStatus.PREPARING)
            else:
                # Use direct credentials
                if not all([host, port, username, auth_type]):
                    return {
                        "success": False,
                        "message": "Missing required parameters: host, port, username, auth_type",
                        "error": "MISSING_PARAMETERS"
                    }

                # Validate inputs
                validation = validate_server_input(host, port)
                if not validation.get("valid"):
                    return {
                        "success": False,
                        "message": validation.get("error", "Invalid input"),
                        "error": "VALIDATION_ERROR"
                    }

                # Build credentials dict
                credentials = {}
                if auth_type == "password":
                    if not password:
                        return {
                            "success": False,
                            "message": "Password is required",
                            "error": "MISSING_CREDENTIALS"
                        }
                    credentials["password"] = password
                elif auth_type == "key":
                    if not private_key:
                        return {
                            "success": False,
                            "message": "Private key is required",
                            "error": "MISSING_CREDENTIALS"
                        }
                    credentials["private_key"] = private_key
                else:
                    return {
                        "success": False,
                        "message": f"Invalid auth type: {auth_type}",
                        "error": "INVALID_AUTH_TYPE"
                    }

                # Test connection to get OS info
                test_success, _, system_info = await self.ssh_service.test_connection(
                    host=host,
                    port=port,
                    username=username,
                    auth_type=auth_type,
                    credentials=credentials
                )

                if not test_success:
                    return {
                        "success": False,
                        "message": "Failed to connect to server",
                        "error": "CONNECTION_FAILED"
                    }

                os_info = system_info.get("os", "") if system_info else ""

            logger.info("Installing Docker", host=host, port=port)

            # Detect OS type
            os_type = _detect_os_type(os_info)

            if os_type == "unknown":
                if server_id:
                    await self.server_service.update_server_status(server_id, ServerStatus.ERROR)
                return {
                    "success": False,
                    "message": f"Unsupported OS: {os_info or 'unknown'}. Supported: {', '.join(SUPPORTED_OS_TYPES)}",
                    "error": "UNSUPPORTED_OS"
                }

            # Build OS-specific install script
            install_script = _build_docker_install_script(os_type)
            if not install_script:
                if server_id:
                    await self.server_service.update_server_status(server_id, ServerStatus.ERROR)
                return {
                    "success": False,
                    "message": f"No Docker commands available for OS: {os_type}",
                    "error": "UNSUPPORTED_OS"
                }

            logger.info("Using OS-specific Docker install", os_type=os_type, host=host)

            # Execute installation via SSH
            success, output = await self.ssh_service.execute_command(
                host=host,
                port=port,
                username=username,
                auth_type=auth_type,
                credentials=credentials,
                command=install_script,
                timeout=300  # 5 minutes for Docker installation
            )

            if success:
                # Re-test connection to get updated system_info
                test_success, _, system_info = await self.ssh_service.test_connection(
                    host=host,
                    port=port,
                    username=username,
                    auth_type=auth_type,
                    credentials=credentials
                )

                if server_id:
                    if test_success and system_info:
                        await self.server_service.update_server_system_info(server_id, system_info)
                    await self.server_service.update_server_status(server_id, ServerStatus.CONNECTED)

                display_name = server_name or host
                await log_event("docker", "INFO", f"Docker installed on server: {display_name}", DOCKER_TAGS, {
                    "host": host,
                    "port": port,
                    "server_id": server_id,
                    "server_name": server_name
                })

                return {
                    "success": True,
                    "data": {"output": output, "system_info": system_info},
                    "message": "Docker installed successfully"
                }
            else:
                if server_id:
                    await self.server_service.update_server_status(server_id, ServerStatus.ERROR)

                display_name = server_name or host
                await log_event("docker", "ERROR", f"Docker installation failed on server: {display_name}", DOCKER_TAGS, {
                    "host": host,
                    "error": output,
                    "server_id": server_id,
                    "server_name": server_name
                })

                return {
                    "success": False,
                    "message": f"Docker installation failed: {output}",
                    "error": "DOCKER_INSTALL_FAILED"
                }

        except Exception as e:
            logger.error("Docker installation error", error=str(e))
            if server_id:
                await self.server_service.update_server_status(server_id, ServerStatus.ERROR)
            return {
                "success": False,
                "message": f"Docker installation failed: {str(e)}",
                "error": "DOCKER_INSTALL_ERROR"
            }

    async def get_docker_install_status(self, server_id: str) -> Dict[str, Any]:
        """Get current Docker installation status for a server.

        Args:
            server_id: ID of the server

        Returns:
            Dict with installation status and config
        """
        try:
            installation = await self.db_service.get_installation(server_id, SYSTEM_DOCKER_APP_ID)

            if not installation:
                return {
                    "success": False,
                    "message": "No Docker installation found for server",
                    "error": "INSTALL_NOT_FOUND"
                }

            return {
                "success": True,
                "data": {
                    "id": installation.id,
                    "server_id": installation.server_id,
                    "status": installation.status.value,
                    "config": installation.config,
                    "installed_at": installation.installed_at,
                    "started_at": installation.started_at,
                    "error_message": installation.error_message
                },
                "message": "Installation status retrieved"
            }
        except Exception as e:
            logger.error("Get Docker install status error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get status: {str(e)}",
                "error": "GET_STATUS_ERROR"
            }

    async def remove_docker(self, server_id: str) -> Dict[str, Any]:
        """Remove Docker from a server.

        Stops Docker service, removes packages, and cleans up data directories.

        Args:
            server_id: ID of the server to remove Docker from

        Returns:
            Dict with success status and output
        """
        try:
            server = await self.server_service.get_server(server_id)
            if not server:
                return {
                    "success": False,
                    "message": "Server not found",
                    "error": "SERVER_NOT_FOUND"
                }

            credentials = await self.server_service.get_credentials(server_id)
            if not credentials:
                return {
                    "success": False,
                    "message": "Credentials not found",
                    "error": "CREDENTIALS_NOT_FOUND"
                }

            os_info = server.system_info.os if server.system_info else ""
            os_type = _detect_os_type(os_info)

            if os_type == "unknown" or os_type not in DOCKER_REMOVE_COMMANDS:
                return {
                    "success": False,
                    "message": f"Unsupported OS for Docker removal: {os_info or 'unknown'}",
                    "error": "UNSUPPORTED_OS"
                }

            remove_script = DOCKER_REMOVE_COMMANDS[os_type]
            logger.info("Removing Docker", server_id=server_id, os_type=os_type)

            success, output = await self.ssh_service.execute_command(
                host=server.host,
                port=server.port,
                username=server.username,
                auth_type=server.auth_type.value,
                credentials=credentials,
                command=remove_script,
                timeout=120
            )

            if success:
                # Update system info to reflect Docker removal
                test_success, _, system_info = await self.ssh_service.test_connection(
                    host=server.host,
                    port=server.port,
                    username=server.username,
                    auth_type=server.auth_type.value,
                    credentials=credentials
                )

                if test_success and system_info:
                    await self.server_service.update_server_system_info(server_id, system_info)

                await log_event("docker", "INFO", f"Docker removed from server: {server.name}", DOCKER_TAGS, {
                    "server_id": server_id,
                    "host": server.host
                })

                return {
                    "success": True,
                    "data": {"output": output},
                    "message": "Docker removed successfully"
                }
            else:
                await log_event("docker", "ERROR", f"Docker removal failed on server: {server.name}", DOCKER_TAGS, {
                    "server_id": server_id,
                    "error": output
                })

                return {
                    "success": False,
                    "message": f"Docker removal failed: {output}",
                    "error": "DOCKER_REMOVE_FAILED"
                }

        except Exception as e:
            logger.error("Docker removal error", error=str(e))
            return {
                "success": False,
                "message": f"Docker removal failed: {str(e)}",
                "error": "DOCKER_REMOVE_ERROR"
            }

    async def update_docker(self, server_id: str) -> Dict[str, Any]:
        """Update Docker to the latest version on a server.

        Updates Docker packages and restarts the Docker service.

        Args:
            server_id: ID of the server to update Docker on

        Returns:
            Dict with success status and new version info
        """
        try:
            server = await self.server_service.get_server(server_id)
            if not server:
                return {
                    "success": False,
                    "message": "Server not found",
                    "error": "SERVER_NOT_FOUND"
                }

            credentials = await self.server_service.get_credentials(server_id)
            if not credentials:
                return {
                    "success": False,
                    "message": "Credentials not found",
                    "error": "CREDENTIALS_NOT_FOUND"
                }

            os_info = server.system_info.os if server.system_info else ""
            os_type = _detect_os_type(os_info)

            if os_type == "unknown" or os_type not in DOCKER_UPDATE_COMMANDS:
                return {
                    "success": False,
                    "message": f"Unsupported OS for Docker update: {os_info or 'unknown'}",
                    "error": "UNSUPPORTED_OS"
                }

            update_script = DOCKER_UPDATE_COMMANDS[os_type]
            logger.info("Updating Docker", server_id=server_id, os_type=os_type)

            success, output = await self.ssh_service.execute_command(
                host=server.host,
                port=server.port,
                username=server.username,
                auth_type=server.auth_type.value,
                credentials=credentials,
                command=update_script,
                timeout=300
            )

            if success:
                # Update system info with new Docker version
                test_success, _, system_info = await self.ssh_service.test_connection(
                    host=server.host,
                    port=server.port,
                    username=server.username,
                    auth_type=server.auth_type.value,
                    credentials=credentials
                )

                if test_success and system_info:
                    await self.server_service.update_server_system_info(server_id, system_info)

                await log_event("docker", "INFO", f"Docker updated on: {server.name}", DOCKER_TAGS, {
                    "server_id": server_id,
                    "host": server.host,
                    "docker_version": system_info.get("docker_version") if system_info else None
                })

                return {
                    "success": True,
                    "data": {"output": output, "system_info": system_info},
                    "message": "Docker updated successfully"
                }
            else:
                await log_event("docker", "ERROR", f"Docker update failed: {server.name}", DOCKER_TAGS, {
                    "server_id": server_id,
                    "error": output
                })

                return {
                    "success": False,
                    "message": f"Docker update failed: {output}",
                    "error": "DOCKER_UPDATE_FAILED"
                }

        except Exception as e:
            logger.error("Docker update error", error=str(e))
            return {
                "success": False,
                "message": f"Docker update failed: {str(e)}",
                "error": "DOCKER_UPDATE_ERROR"
            }

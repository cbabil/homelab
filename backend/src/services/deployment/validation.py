"""
Deployment Validation

Preflight checks and configuration validation for deployments.
"""

from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger("deployment.validation")


class DeploymentValidator:
    """Validates deployment configuration and server readiness."""

    def __init__(self, ssh_executor, marketplace_service, server_service):
        """Initialize validator.

        Args:
            ssh_executor: SSH executor for running checks
            marketplace_service: For getting app definitions
            server_service: For getting server info
        """
        self.ssh = ssh_executor
        self.marketplace_service = marketplace_service
        self.server_service = server_service

    async def validate_config(self, app_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate deployment configuration against app definition.

        Args:
            app_id: App to validate against
            config: User-provided configuration

        Returns:
            Dict with valid, errors, and warnings
        """
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        try:
            app = await self.marketplace_service.get_app(app_id)
            if not app:
                validation["valid"] = False
                validation["errors"].append(f"App '{app_id}' not found")
                return validation

            # Validate required environment variables
            for env_var in app.docker.environment:
                if env_var.required:
                    provided_value = config.get("env", {}).get(env_var.name)
                    if not provided_value and not env_var.default:
                        validation["valid"] = False
                        validation["errors"].append(
                            f"Required env var '{env_var.name}' not provided"
                        )

            # Validate port mappings
            config_ports = config.get("ports", {})
            app_ports = {str(p.container): p.host for p in app.docker.ports}

            for container_port, host_port in config_ports.items():
                if container_port not in app_ports:
                    validation["warnings"].append(
                        f"Port {container_port} not in app definition"
                    )

                # Validate port number range
                try:
                    port_num = int(host_port)
                    if port_num < 1 or port_num > 65535:
                        validation["valid"] = False
                        validation["errors"].append(f"Invalid port number: {host_port}")
                except ValueError:
                    validation["valid"] = False
                    validation["errors"].append(f"Invalid port value: {host_port}")

            # Validate volume paths
            for container_path, host_path in config.get("volumes", {}).items():
                if not host_path:
                    validation["valid"] = False
                    validation["errors"].append(
                        f"Empty host path for volume {container_path}"
                    )
                elif not host_path.startswith("/"):
                    validation["warnings"].append(
                        f"Volume path '{host_path}' is not absolute"
                    )

            return validation

        except Exception as e:
            logger.error("Config validation failed", error=str(e))
            validation["valid"] = False
            validation["errors"].append(str(e))
            return validation

    async def run_preflight_checks(
        self,
        server_id: str,
        app_id: str,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Run pre-flight validation before deployment.

        Args:
            server_id: Target server
            app_id: App to deploy
            config: User-provided configuration

        Returns:
            Dict with passed, checks, and can_proceed
        """
        config = config or {}
        checks = []
        all_passed = True

        try:
            app = await self.marketplace_service.get_app(app_id)
            server = await self.server_service.get_server(server_id)

            if not app or not server:
                return {
                    "passed": False,
                    "checks": [{
                        "name": "resources",
                        "passed": False,
                        "message": "App or server not found"
                    }],
                    "can_proceed": False
                }

            # Check 1: Docker running
            docker_check = await self._check_docker_running(server_id)
            checks.append(docker_check)
            if not docker_check["passed"]:
                all_passed = False

            # Check 2: Disk space
            min_storage = None
            if app.requirements:
                min_storage = getattr(app.requirements, 'min_storage', None)
            disk_check = await self._check_disk_space(server_id, min_storage)
            checks.append(disk_check)
            if not disk_check["passed"]:
                all_passed = False

            # Check 3: Port availability
            ports = [p.host for p in app.docker.ports]
            custom_ports = [
                config.get("ports", {}).get(str(p.container), p.host)
                for p in app.docker.ports
            ]
            port_check = await self._check_ports_available(
                server_id, custom_ports or ports
            )
            checks.append(port_check)
            if not port_check["passed"]:
                all_passed = False

            # Check 4: Architecture compatibility
            supported_archs = []
            if app.requirements:
                supported_archs = getattr(app.requirements, 'architectures', [])
            arch_check = await self._check_architecture(server_id, supported_archs)
            checks.append(arch_check)
            if not arch_check["passed"]:
                all_passed = False

            return {
                "passed": all_passed,
                "checks": checks,
                "can_proceed": all_passed
            }

        except Exception as e:
            logger.error("Preflight checks failed", error=str(e))
            return {
                "passed": False,
                "checks": [{"name": "error", "passed": False, "message": str(e)}],
                "can_proceed": False
            }

    async def _check_docker_running(self, server_id: str) -> Dict[str, Any]:
        """Check if Docker daemon is running."""
        cmd = "docker info > /dev/null 2>&1 && echo 'running' || echo 'not running'"
        exit_code, stdout, _ = await self.ssh.execute(server_id, cmd)

        running = exit_code == 0 and "running" in stdout
        return {
            "name": "docker_running",
            "passed": running,
            "message": "Docker is running" if running else "Docker daemon is not running"
        }

    async def _check_disk_space(
        self, server_id: str, min_mb: Optional[int]
    ) -> Dict[str, Any]:
        """Check available disk space."""
        cmd = "df -m / | tail -1 | awk '{print $4}'"
        exit_code, stdout, _ = await self.ssh.execute(server_id, cmd)

        if exit_code != 0:
            return {
                "name": "disk_space",
                "passed": False,
                "message": "Could not check disk space"
            }

        try:
            available_mb = int(stdout.strip())
            required_mb = min_mb or 1024  # Default 1GB minimum
            passed = available_mb >= required_mb

            return {
                "name": "disk_space",
                "passed": passed,
                "message": (
                    f"{available_mb}MB available" if passed
                    else f"Need {required_mb}MB, only {available_mb}MB available"
                ),
                "available_mb": available_mb,
                "required_mb": required_mb
            }
        except ValueError:
            return {
                "name": "disk_space",
                "passed": False,
                "message": "Could not parse disk space"
            }

    async def _check_ports_available(
        self, server_id: str, ports: List[int]
    ) -> Dict[str, Any]:
        """Check if required ports are available."""
        if not ports:
            return {
                "name": "port_availability",
                "passed": True,
                "message": "No ports to check"
            }

        unavailable = []
        for port in ports:
            if port is None:
                continue
            cmd = f"ss -tuln | grep ':{port} ' || echo 'available'"
            exit_code, stdout, _ = await self.ssh.execute(server_id, cmd)
            if "available" not in stdout:
                unavailable.append(port)

        passed = len(unavailable) == 0
        return {
            "name": "port_availability",
            "passed": passed,
            "message": (
                "All ports available" if passed
                else f"Ports in use: {unavailable}"
            ),
            "unavailable_ports": unavailable
        }

    async def _check_architecture(
        self, server_id: str, supported: List[str]
    ) -> Dict[str, Any]:
        """Check if server architecture is supported."""
        cmd = "uname -m"
        exit_code, stdout, _ = await self.ssh.execute(server_id, cmd)

        if exit_code != 0:
            return {
                "name": "architecture",
                "passed": False,
                "message": "Could not determine architecture"
            }

        arch = stdout.strip().lower()
        # Map common arch names
        arch_map = {"x86_64": "amd64", "aarch64": "arm64", "armv7l": "arm/v7"}
        normalized = arch_map.get(arch, arch)

        passed = not supported or normalized in [a.lower() for a in supported]
        return {
            "name": "architecture",
            "passed": passed,
            "message": (
                f"Architecture {normalized} supported" if passed
                else f"Architecture {normalized} not in {supported}"
            ),
            "server_arch": normalized,
            "supported_archs": supported
        }

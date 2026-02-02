"""Docker container RPC methods."""

import logging
from typing import Any, Dict, List, Optional

try:
    from .docker_client import get_client
    from ..errors import ContainerBlockedError, DockerOperationError
    from ...security import validate_docker_params, redact_sensitive_data
except ImportError:
    from rpc.methods.docker_client import get_client
    from rpc.errors import ContainerBlockedError, DockerOperationError
    from security import validate_docker_params, redact_sensitive_data

logger = logging.getLogger(__name__)


class ContainerMethods:
    """RPC methods for Docker container operations."""

    def list(self, all: bool = False) -> List[Dict[str, Any]]:
        """List Docker containers."""
        client = get_client()
        containers = client.containers.list(all=all)
        return [
            {
                "id": c.short_id,
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else c.image.short_id,
            }
            for c in containers
        ]

    def run(
        self,
        image: str,
        name: Optional[str] = None,
        ports: Optional[Dict[str, Any]] = None,
        env: Optional[Dict[str, str]] = None,
        volumes: Optional[List[Dict[str, str]]] = None,
        network: Optional[str] = None,
        network_mode: Optional[str] = None,
        restart_policy: Optional[str] = None,
        privileged: bool = False,
        capabilities: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Run a new container.

        Validates container parameters against security policy before creation.
        Blocks privileged containers, dangerous capabilities, and protected
        volume mounts.

        Args:
            image: Docker image to run
            name: Container name
            ports: Port mappings {host_port: "container_port/protocol"}
            env: Environment variables
            volumes: Volume mounts [{host: path, container: path, mode: rw/ro}]
            network: Docker network name
            network_mode: Docker network mode
            restart_policy: Restart policy string (e.g., "unless-stopped")
            privileged: Run in privileged mode
            capabilities: Additional Linux capabilities
        """
        # Convert volumes from list format to Docker format
        docker_volumes = {}
        if volumes:
            for vol in volumes:
                host_path = vol.get("host", "")
                container_path = vol.get("container", "")
                mode = vol.get("mode", "rw")
                if host_path and container_path:
                    docker_volumes[host_path] = {"bind": container_path, "mode": mode}

        # Build params dict for validation
        params = {
            "volumes": docker_volumes,
            "privileged": privileged,
            "cap_add": capabilities or [],
            **kwargs,
        }

        # Validate against security policy
        is_valid, error_msg = validate_docker_params(params)
        if not is_valid:
            logger.warning(
                "Container creation blocked by security policy",
                extra={"name": name, "reason": error_msg},
            )
            raise ContainerBlockedError(error_msg, image=image, name=name or "")

        # Log container creation (redact env vars which may contain secrets)
        log_params = redact_sensitive_data({"env": env, "volumes": docker_volumes})
        logger.info(f"Creating container {name} from {image}", extra=log_params)

        # Convert ports from our format to Docker format
        # Our format: {host_port: "container_port/protocol"}
        # Docker format: {"container_port/protocol": host_port}
        docker_ports = {}
        if ports:
            for host_port, container_spec in ports.items():
                docker_ports[container_spec] = int(host_port)

        # Convert restart policy string to Docker format
        docker_restart = None
        if restart_policy and restart_policy != "no":
            policy_parts = restart_policy.split(":")
            docker_restart = {"Name": policy_parts[0]}
            if len(policy_parts) > 1:
                docker_restart["MaximumRetryCount"] = int(policy_parts[1])

        client = get_client()
        try:
            container = client.containers.run(
                image,
                name=name,
                ports=docker_ports if docker_ports else None,
                environment=env if env else None,
                volumes=docker_volumes if docker_volumes else None,
                network=network,
                network_mode=network_mode,
                restart_policy=docker_restart,
                privileged=privileged,
                cap_add=capabilities if capabilities else None,
                detach=True,
            )
            return {
                "id": container.short_id,
                "name": container.name,
                "container_id": container.id,
            }
        except Exception as e:
            # Log the actual Docker error for debugging
            logger.error(
                f"Docker container.run failed: {e}",
                extra={
                    "image": image,
                    "name": name,
                    "ports": docker_ports,
                    "volumes": docker_volumes,
                    "restart_policy": docker_restart,
                },
            )
            raise DockerOperationError(str(e), operation="container.run")

    def start(self, container: str) -> Dict[str, str]:
        """Start a container."""
        c = get_client().containers.get(container)
        c.start()
        return {"status": "started"}

    def stop(self, container: str, timeout: int = 10) -> Dict[str, str]:
        """Stop a container."""
        c = get_client().containers.get(container)
        c.stop(timeout=timeout)
        return {"status": "stopped"}

    def remove(self, container: str, force: bool = False) -> Dict[str, str]:
        """Remove a container."""
        c = get_client().containers.get(container)
        c.remove(force=force)
        return {"status": "removed"}

    def restart(self, container: str) -> Dict[str, str]:
        """Restart a container."""
        c = get_client().containers.get(container)
        c.restart()
        return {"status": "restarted"}

    def logs(
        self, container: str, tail: int = 100, follow: bool = False
    ) -> Dict[str, str]:
        """Get container logs."""
        c = get_client().containers.get(container)
        logs = c.logs(tail=tail, follow=False)
        return {"logs": logs.decode("utf-8", errors="replace")}

    def inspect(self, container: str) -> Dict[str, Any]:
        """Inspect a container."""
        return get_client().containers.get(container).attrs

    def update(
        self, container: str, restart_policy: Optional[str] = None
    ) -> Dict[str, str]:
        """Update container configuration.

        Args:
            container: Container name or ID
            restart_policy: Restart policy (e.g., "unless-stopped", "always")
        """
        c = get_client().containers.get(container)
        update_args = {}

        if restart_policy:
            # Docker API expects {"Name": policy, "MaximumRetryCount": n}
            policy_parts = restart_policy.split(":")
            policy_name = policy_parts[0]
            max_retries = int(policy_parts[1]) if len(policy_parts) > 1 else 0
            update_args["restart_policy"] = {
                "Name": policy_name,
                "MaximumRetryCount": max_retries,
            }

        if update_args:
            c.update(**update_args)

        return {"status": "updated"}

    def status(self, container: str, include_logs: bool = False) -> Dict[str, Any]:
        """Get container status including health and restart count.

        Args:
            container: Container name or ID
            include_logs: Whether to include recent logs

        Returns:
            Dict with status, health, restart_count, and optionally logs
        """
        c = get_client().containers.get(container)
        c.reload()  # Refresh state

        attrs = c.attrs
        state = attrs.get("State", {})
        health = state.get("Health", {})

        result = {
            "status": state.get("Status", "unknown"),
            "health": health.get("Status", "none") if health else "none",
            "restart_count": attrs.get("RestartCount", 0),
            "running": state.get("Running", False),
            "started_at": state.get("StartedAt"),
            "finished_at": state.get("FinishedAt"),
        }

        if include_logs:
            try:
                logs = c.logs(tail=50, timestamps=False)
                result["logs"] = logs.decode("utf-8", errors="replace")[-500:]
            except Exception:
                result["logs"] = ""

        return result

    def stats(self, container: str) -> Dict[str, Any]:
        """Get container resource statistics."""
        c = get_client().containers.get(container)
        stats = c.stats(stream=False)
        return {
            "cpu_percent": self._calc_cpu_percent(stats),
            "memory_usage": stats.get("memory_stats", {}).get("usage", 0),
            "memory_limit": stats.get("memory_stats", {}).get("limit", 0),
        }

    def _calc_cpu_percent(self, stats: Dict[str, Any]) -> float:
        """Calculate CPU usage percentage from stats."""
        cpu_stats = stats.get("cpu_stats", {})
        precpu_stats = stats.get("precpu_stats", {})
        cpu_usage = cpu_stats.get("cpu_usage", {})
        precpu_usage = precpu_stats.get("cpu_usage", {})
        cpu_delta = cpu_usage.get("total_usage", 0) - precpu_usage.get("total_usage", 0)
        system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get(
            "system_cpu_usage", 0
        )
        cpu_count = len(cpu_usage.get("percpu_usage", [])) or 1
        if system_delta > 0 and cpu_delta > 0:
            return (cpu_delta / system_delta) * cpu_count * 100.0
        return 0.0

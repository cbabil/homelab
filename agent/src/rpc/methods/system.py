"""System RPC methods."""

import logging
import os
import platform
import re
import shlex
import subprocess
from typing import Any, Dict, List, Optional, Tuple

import psutil

# Shell metacharacters that require shell=True
SHELL_METACHARACTERS = re.compile(r"[|;&`$()<>]|>>|<<|2>&1|>/dev/null")

# Patterns that may contain sensitive data in commands
SENSITIVE_COMMAND_PATTERNS = re.compile(
    r"(-e\s+\S*(?:PASSWORD|SECRET|KEY|TOKEN|CREDENTIAL)\S*=)\S+|"
    r"(--env\s+\S*(?:PASSWORD|SECRET|KEY|TOKEN|CREDENTIAL)\S*=)\S+",
    re.IGNORECASE,
)


def _redact_command_for_logging(command: str) -> str:
    """Redact sensitive parts of a command for safe logging.

    Args:
        command: The command string.

    Returns:
        Command with sensitive values redacted.
    """
    # Redact sensitive environment variable values
    redacted = SENSITIVE_COMMAND_PATTERNS.sub(r"\1[REDACTED]", command)
    # Truncate to reasonable length
    if len(redacted) > 100:
        return redacted[:100] + "..."
    return redacted

try:
    from .docker_client import get_client
    from ...security import validate_command, acquire_command_slot, release_command_slot
except ImportError:
    from rpc.methods.docker_client import get_client
    from security import validate_command, acquire_command_slot, release_command_slot

logger = logging.getLogger(__name__)


def _prepare_command(command: str) -> Tuple[List[str] | str, bool]:
    """Prepare command for execution, determining if shell is needed.

    Args:
        command: The command string to prepare.

    Returns:
        Tuple of (command_args, use_shell) where command_args is either
        a list (for shell=False) or string (for shell=True).
    """
    # Check if command requires shell features
    if SHELL_METACHARACTERS.search(command):
        # Command needs shell - return as string with shell=True
        return command, True

    # No shell metacharacters - safe to use shell=False with shlex.split
    try:
        args = shlex.split(command)
        return args, False
    except ValueError:
        # Malformed command - let it fail with shell=True for better error
        return command, True


class SystemMethods:
    """System information and command methods."""

    def info(self) -> Dict[str, Any]:
        """Get system information."""
        docker_version = "unknown"
        try:
            client = get_client()
            docker_version = client.version().get("Version", "unknown")
        except Exception:
            pass

        return {
            "os": self._get_os_info(),
            "kernel": platform.release(),
            "arch": platform.machine(),
            "hostname": platform.node(),
            "docker_version": docker_version,
        }

    def exec(self, command: str, timeout: Optional[int] = 60) -> Dict[str, Any]:
        """Execute a system command.

        Commands are validated against a security allowlist. Only specific
        safe commands needed for deployment operations are permitted.
        Rate limiting is enforced to prevent abuse.

        Args:
            command: Shell command to execute (must be in allowlist).
            timeout: Maximum execution time in seconds.

        Returns:
            Dict with stdout, stderr, and exit_code.
        """
        # Validate command against security allowlist
        is_valid, error_msg = validate_command(command, timeout or 60)
        if not is_valid:
            logger.warning(
                "Command rejected by security policy: %s",
                _redact_command_for_logging(command),
                extra={"reason": error_msg},
            )
            return {
                "stdout": "",
                "stderr": f"Command not allowed: {error_msg}",
                "exit_code": -1,
                "security_blocked": True,
            }

        # Check rate limit
        allowed, rate_error = acquire_command_slot()
        if not allowed:
            logger.warning(
                "Command rate limited: %s",
                _redact_command_for_logging(command),
                extra={"reason": rate_error},
            )
            return {
                "stdout": "",
                "stderr": f"Rate limit: {rate_error}",
                "exit_code": -1,
                "rate_limited": True,
            }

        try:
            # Prepare command - use shell=False when possible for safety
            cmd_args, use_shell = _prepare_command(command)

            result = subprocess.run(
                cmd_args,
                shell=use_shell,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            logger.info(
                "Executed allowed command: %s (shell=%s)",
                _redact_command_for_logging(command),
                use_shell,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "exit_code": -1,
            }
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {
                "stdout": "",
                "stderr": "Command execution failed",  # Don't leak internal errors
                "exit_code": -1,
            }
        finally:
            release_command_slot()

    def preflight_check(
        self, min_disk_gb: int = 3, min_memory_mb: int = 256
    ) -> Dict[str, Any]:
        """Run pre-flight checks before deployment.

        Args:
            min_disk_gb: Minimum required disk space in GB
            min_memory_mb: Minimum required free memory in MB

        Returns:
            Dict with success status and details about resources
        """
        errors = []
        warnings = []

        # Check Docker daemon
        docker_ok = False
        docker_version = "unknown"
        try:
            client = get_client()
            version_info = client.version()
            docker_version = version_info.get("Version", "unknown")
            client.ping()
            docker_ok = True
        except Exception as e:
            errors.append(f"Docker daemon not responding: {e}")

        # Check disk space
        disk_path = "/host" if os.path.exists("/host") else "/"
        disk = psutil.disk_usage(disk_path)
        free_disk_gb = disk.free / (1024**3)
        if free_disk_gb < min_disk_gb:
            errors.append(f"Only {free_disk_gb:.1f}GB free, need {min_disk_gb}GB")

        # Check memory
        memory = psutil.virtual_memory()
        free_memory_mb = memory.available / (1024**2)
        if free_memory_mb < min_memory_mb:
            errors.append(f"Only {free_memory_mb:.0f}MB free, need {min_memory_mb}MB")

        # Return results
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "docker": {"ok": docker_ok, "version": docker_version},
            "disk": {
                "free_gb": round(free_disk_gb, 1),
                "total_gb": round(disk.total / (1024**3), 1),
            },
            "memory": {
                "free_mb": round(free_memory_mb),
                "total_mb": round(memory.total / (1024**2)),
            },
        }

    # Allowed writable paths for volume preparation (security boundary)
    ALLOWED_DATA_PATHS = ["/DATA", "/opt/tomo"]

    def prepare_volumes(
        self, volumes: list, default_uid: int = 1000, default_gid: int = 1000
    ) -> Dict[str, Any]:
        """Prepare host directories for volume mounts.

        Creates directories and sets ownership so containers can write to them.
        Only paths under allowed directories can be prepared (security).

        Args:
            volumes: List of volume dicts with 'host' path and optional 'uid'/'gid'
            default_uid: Default UID if not specified per volume
            default_gid: Default GID if not specified per volume

        Returns:
            Dict with success status and details per volume
        """
        results = []
        errors = []

        # Determine host filesystem prefix (agent runs in container with / mounted at /host)
        host_prefix = "/host" if os.path.exists("/host") else ""

        for vol in volumes:
            host_path = vol.get("host", "")
            if not host_path:
                continue

            # Skip named volumes (no leading /)
            if not host_path.startswith("/"):
                results.append(
                    {"path": host_path, "status": "skipped", "reason": "named volume"}
                )
                continue

            # Security check: only allow paths under approved directories
            path_allowed = any(
                host_path.startswith(allowed) for allowed in self.ALLOWED_DATA_PATHS
            )
            if not path_allowed:
                logger.warning(
                    f"Volume path not in allowed directories: {host_path}. "
                    f"Allowed: {self.ALLOWED_DATA_PATHS}"
                )
                results.append(
                    {
                        "path": host_path,
                        "status": "skipped",
                        "reason": f"not in allowed paths: {self.ALLOWED_DATA_PATHS}",
                    }
                )
                continue

            # Get ownership - use volume-specific or defaults
            uid = vol.get("uid", default_uid)
            gid = vol.get("gid", default_gid)

            # Map to host filesystem
            full_path = f"{host_prefix}{host_path}"

            try:
                # Create directory if not exists
                os.makedirs(full_path, mode=0o755, exist_ok=True)

                # Set ownership
                os.chown(full_path, uid, gid)

                # Also recursively set ownership for existing contents
                for root, dirs, files in os.walk(full_path):
                    for d in dirs:
                        try:
                            os.chown(os.path.join(root, d), uid, gid)
                        except OSError:
                            pass
                    for f in files:
                        try:
                            os.chown(os.path.join(root, f), uid, gid)
                        except OSError:
                            pass

                logger.info(f"Prepared volume: {host_path} (uid={uid}, gid={gid})")
                results.append(
                    {
                        "path": host_path,
                        "status": "ok",
                        "uid": uid,
                        "gid": gid,
                    }
                )

            except PermissionError as e:
                logger.error(f"Permission denied preparing {host_path}: {e}")
                errors.append(f"Permission denied: {host_path}")
                results.append(
                    {"path": host_path, "status": "error", "error": "permission denied"}
                )

            except Exception as e:
                logger.error(f"Error preparing volume {host_path}: {e}")
                errors.append(f"Failed to prepare {host_path}: {str(e)}")
                results.append({"path": host_path, "status": "error", "error": str(e)})

        return {
            "success": len(errors) == 0,
            "results": results,
            "errors": errors,
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/host" if os.path.exists("/host") else "/")

        running = 0
        stopped = 0
        try:
            client = get_client()
            for c in client.containers.list(all=True):
                if c.status == "running":
                    running += 1
                else:
                    stopped += 1
        except Exception:
            pass

        return {
            "cpu": cpu_percent,
            "memory": {
                "used": memory.used,
                "total": memory.total,
                "percent": memory.percent,
            },
            "disk": {
                "used": disk.used,
                "total": disk.total,
                "percent": disk.percent,
            },
            "containers": {
                "running": running,
                "stopped": stopped,
            },
        }

    def _get_os_info(self) -> str:
        """Get OS information."""
        os_release_paths = ["/host/etc/os-release", "/etc/os-release"]

        for path in os_release_paths:
            try:
                with open(path) as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            return line.split("=", 1)[1].strip().strip('"')
            except FileNotFoundError:
                continue

        return f"{platform.system()} {platform.release()}"

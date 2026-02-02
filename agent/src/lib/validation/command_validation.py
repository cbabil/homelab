"""Command allowlist and validation.

Validates shell commands against a security allowlist.
"""

import logging
import re
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from .docker_validation import validate_docker_run_command

logger = logging.getLogger(__name__)


@dataclass
class CommandAllowlistEntry:
    """Entry in the command allowlist."""

    pattern: str  # Regex pattern for the command
    description: str  # Human-readable description
    max_timeout: int = 300  # Maximum allowed timeout in seconds
    validator: Optional[Callable[[str], Tuple[bool, str]]] = None


# Allowlist of commands that can be executed via system.exec
COMMAND_ALLOWLIST: List[CommandAllowlistEntry] = [
    # Docker commands (read-only info)
    CommandAllowlistEntry(
        pattern=r"^docker\s+ps(\s+--format\s+'[^']*')?(\s+--filter\s+\S+)*(\s+-a)?\s*$",
        description="List running containers",
    ),
    CommandAllowlistEntry(
        pattern=r"^docker\s+images(\s+--format\s+'[^']*')?\s*$",
        description="List images",
    ),
    CommandAllowlistEntry(
        pattern=r"^docker\s+version\s*$",
        description="Get Docker version",
    ),
    CommandAllowlistEntry(
        pattern=r"^docker\s+info\s*$",
        description="Get Docker info",
    ),
    # Docker pull for deployment
    CommandAllowlistEntry(
        pattern=r"^docker\s+pull\s+[\w./:@-]+\s*$",
        description="Pull Docker image",
        max_timeout=600,
    ),
    # Docker run for deployment - with additional validation
    CommandAllowlistEntry(
        pattern=r"^docker\s+run\s+-d\s+.+$",
        description="Run Docker container (detached)",
        max_timeout=300,
        validator=validate_docker_run_command,
    ),
    # Docker container management
    CommandAllowlistEntry(
        pattern=r"^docker\s+(stop|start|restart|kill)\s+[\w-]+(\s+--time\s+\d+)?\s*$",
        description="Start/stop Docker container",
        max_timeout=120,
    ),
    CommandAllowlistEntry(
        pattern=r"^docker\s+rm(\s+-f)?\s+[\w-]+\s*$",
        description="Remove Docker container",
        max_timeout=60,
    ),
    # Container inspection and logs
    CommandAllowlistEntry(
        pattern=r"^docker\s+inspect\s+[\w./:@-]+(\s+--format\s+.+)?(\s+2>/dev/null)?\s*$",
        description="Inspect container or image",
        max_timeout=30,
    ),
    CommandAllowlistEntry(
        pattern=r"^docker\s+logs\s+(--tail\s+\d+\s+)?[\w-]+\s*$",
        description="Get container logs",
    ),
    # Docker update
    CommandAllowlistEntry(
        pattern=r"^docker\s+update\s+--restart\s+\S+\s+[\w-]+\s*$",
        description="Update container restart policy",
        max_timeout=30,
    ),
    # Docker image inspect
    CommandAllowlistEntry(
        pattern=r"^docker\s+image\s+inspect\s+[\w./:@-]+(\s+>\s*/dev/null\s+2>&1)?\s*$",
        description="Check if Docker image exists",
        max_timeout=10,
    ),
    # Docker exec for health checks
    CommandAllowlistEntry(
        pattern=r"^docker\s+exec\s+[\w-]+\s+(curl|wget|nc|cat|ls|echo|ping|nslookup)\s+[^;&|`$]+$",
        description="Execute command in container (safe commands)",
        max_timeout=30,
    ),
    # Pre-flight checks
    CommandAllowlistEntry(
        pattern=r"^(df|free|docker\s+info|docker\s+ps)\s+[^;&|`$]*$",
        description="System pre-flight checks",
        max_timeout=30,
    ),
    # Mkdir for deployment directories
    CommandAllowlistEntry(
        pattern=r"^mkdir\s+-p\s+/(DATA|opt/tomo)/[\w/.@-]+\s*$",
        description="Create deployment directories",
        max_timeout=10,
    ),
    # System info
    CommandAllowlistEntry(
        pattern=r"^uname\s+-[a-z]+\s*$",
        description="Get system info",
    ),
    CommandAllowlistEntry(
        pattern=r"^hostname\s*$",
        description="Get hostname",
    ),
    CommandAllowlistEntry(
        pattern=r"^uptime\s*$",
        description="Get uptime",
    ),
    CommandAllowlistEntry(
        pattern=r"^df\s+-h\s*$",
        description="Get disk usage",
    ),
    CommandAllowlistEntry(
        pattern=r"^free\s+-[hm]\s*$",
        description="Get memory usage",
    ),
    # Deployment job status
    CommandAllowlistEntry(
        pattern=r"^cat\s+/tmp/pull-job-[a-f0-9-]+/(status|output|progress)\s*$",
        description="Check pull job status",
        max_timeout=10,
    ),
    CommandAllowlistEntry(
        pattern=r"^rm\s+-rf\s+/tmp/pull-job-[a-f0-9-]+\s*$",
        description="Cleanup pull job directory",
        max_timeout=10,
    ),
]


class CommandValidator:
    """Validates commands against the allowlist."""

    def __init__(self, allowlist: List[CommandAllowlistEntry] | None = None) -> None:
        """Initialize with allowlist."""
        self._allowlist = allowlist or COMMAND_ALLOWLIST
        self._compiled_patterns = [
            (re.compile(entry.pattern), entry) for entry in self._allowlist
        ]

    def validate(self, command: str, timeout: int = 60) -> Tuple[bool, str]:
        """Validate a command against the allowlist.

        Args:
            command: The command to validate.
            timeout: Requested timeout in seconds.

        Returns:
            Tuple of (is_valid, error_message).
        """
        command = " ".join(command.split())

        for pattern, entry in self._compiled_patterns:
            if pattern.match(command):
                if timeout > entry.max_timeout:
                    return (
                        False,
                        f"Timeout {timeout}s exceeds maximum {entry.max_timeout}s for this command",
                    )
                if entry.validator:
                    is_valid, error = entry.validator(command)
                    if not is_valid:
                        logger.warning(f"Command failed validation: {error}")
                        return (False, error)
                logger.debug(f"Command allowed: {entry.description}")
                return (True, "")

        logger.warning(f"Command rejected - not in allowlist: {command[:50]}...")
        return (False, "Command not in allowlist")


# Global validator instance
_command_validator = CommandValidator()


def validate_command(command: str, timeout: int = 60) -> Tuple[bool, str]:
    """Validate a command against the security allowlist.

    Args:
        command: Shell command to validate.
        timeout: Requested timeout.

    Returns:
        Tuple of (is_valid, error_message).
    """
    return _command_validator.validate(command, timeout)

# Agent Validation Refactoring - Implementation Plan

## Prerequisites

Before starting:
- [ ] Read the [Refactoring Plan](validation-refactor-plan.md)
- [ ] Ensure all tests pass: `cd agent && pytest tests/`
- [ ] Create a feature branch: `git checkout -b refactor/agent-validation-split`

---

## Phase 1: Create Package Structure

### Step 1.1: Create validation package directory

```bash
mkdir -p agent/src/lib/validation
touch agent/src/lib/validation/__init__.py
```

### Step 1.2: Create empty module files

```bash
touch agent/src/lib/validation/constants.py
touch agent/src/lib/validation/volume_validation.py
touch agent/src/lib/validation/docker_validation.py
touch agent/src/lib/validation/command_validation.py
```

---

## Phase 2: Extract Constants Module

### Step 2.1: Create `constants.py`

Extract from `validation.py` lines 27-61 and 358-383:

```python
# agent/src/lib/validation/constants.py
"""Security constants for validation.

Defines blocked Docker flags, volume patterns, and protected paths.
"""

from typing import Any, Dict, List, Set

# Blocked docker run flags that could lead to privilege escalation
BLOCKED_DOCKER_RUN_FLAGS: Set[str] = {
    "--privileged",
    "--cap-add=ALL",
    "--cap-add=SYS_ADMIN",
    "--cap-add=SYS_PTRACE",
    "--cap-add=SYS_RAWIO",
    "--cap-add=NET_ADMIN",
    "--cap-add=NET_RAW",
    "--pid=host",
    "--network=host",
    "--ipc=host",
    "--userns=host",
    "--uts=host",
    "--security-opt=apparmor=unconfined",
    "--security-opt=seccomp=unconfined",
    "--device=/dev/",
}

# Blocked volume mount patterns
BLOCKED_VOLUME_PATTERNS: List[str] = [
    "/var/run/docker.sock",
    "/run/docker.sock",
    "/etc/",
    "/var/",
    "/usr/",
    "/bin/",
    "/sbin/",
    "/lib/",
    "/root/",
    "/home/",
    "/boot/",
    "/proc/",
    "/sys/",
    "/dev/",
]

# Volume paths that should never be mounted read-write
PROTECTED_PATHS: List[str] = [
    "/",
    "/etc",
    "/var",
    "/usr",
    "/bin",
    "/sbin",
    "/lib",
    "/root",
    "/home",
    "/boot",
    "/proc",
    "/sys",
    "/dev",
]

# Dangerous Docker parameters that should be blocked
BLOCKED_DOCKER_PARAMS: Dict[str, Any] = {
    "privileged": True,
    "cap_add": ["ALL", "SYS_ADMIN", "SYS_PTRACE", "SYS_RAWIO"],
    "pid_mode": "host",
    "network_mode": "host",
    "ipc_mode": "host",
    "userns_mode": "host",
}
```

### Step 2.2: Verify constants extraction

```bash
cd agent && python -c "from src.lib.validation.constants import *; print('OK')"
```

---

## Phase 3: Extract Volume Validation

### Step 3.1: Create `volume_validation.py`

Extract from `validation.py` lines 140-173:

```python
# agent/src/lib/validation/volume_validation.py
"""Volume mount validation.

Validates Docker volume mount specifications for security.
"""

import os
from typing import Tuple

from .constants import BLOCKED_VOLUME_PATTERNS, PROTECTED_PATHS


def validate_volume_mount(volume_spec: str) -> bool:
    """Validate a volume mount specification.

    Args:
        volume_spec: Volume spec like "/host:/container:ro"

    Returns:
        True if the mount is allowed.
    """
    parts = volume_spec.split(":")
    if len(parts) < 2:
        return True  # Named volume, allowed

    host_path = parts[0]

    # Check for docker socket
    if host_path in ["/var/run/docker.sock", "/run/docker.sock"]:
        return False

    # Normalize path
    host_path = os.path.normpath(host_path)

    # Check for blocked paths
    for blocked in BLOCKED_VOLUME_PATTERNS:
        if host_path == blocked.rstrip("/") or host_path.startswith(blocked):
            # Allow if explicitly read-only and not docker socket
            if len(parts) >= 3 and parts[2] == "ro":
                # Still block some paths even read-only
                if host_path.startswith("/proc") or host_path.startswith("/sys"):
                    return False
                continue
            return False

    return True


def validate_volume_path(host_path: str, mode: str = "rw") -> Tuple[bool, str]:
    """Validate a host path for volume mounting.

    Args:
        host_path: The host path to validate.
        mode: Mount mode ("rw" or "ro").

    Returns:
        Tuple of (is_valid, error_message).
    """
    host_path = os.path.normpath(host_path)

    # Block Docker socket mount
    if host_path in ["/var/run/docker.sock", "/run/docker.sock"]:
        return (False, "Mounting Docker socket is not allowed")

    # Check for protected paths with write access
    if mode == "rw":
        for protected in PROTECTED_PATHS:
            if host_path == protected or host_path.startswith(protected + "/"):
                return (False, f"Write access to {host_path} is not allowed")

    return (True, "")
```

### Step 3.2: Verify volume validation

```bash
cd agent && python -c "from src.lib.validation.volume_validation import *; print('OK')"
```

---

## Phase 4: Extract Docker Validation

### Step 4.1: Create `docker_validation.py`

Extract from `validation.py` lines 64-137 and 386-429:

```python
# agent/src/lib/validation/docker_validation.py
"""Docker command and parameter validation.

Validates Docker run commands and container parameters for security.
"""

import logging
import os
import shlex
from typing import Any, Dict, Tuple

from .constants import BLOCKED_DOCKER_PARAMS, BLOCKED_DOCKER_RUN_FLAGS, PROTECTED_PATHS
from .volume_validation import validate_volume_mount

logger = logging.getLogger(__name__)


def validate_docker_run_command(command: str) -> Tuple[bool, str]:
    """Validate docker run command for dangerous flags.

    Args:
        command: The docker run command string.

    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        tokens = shlex.split(command)
    except ValueError as e:
        return (False, f"Invalid command syntax: {e}")

    for i, token in enumerate(tokens):
        token_lower = token.lower()

        # Check blocked flags
        for blocked in BLOCKED_DOCKER_RUN_FLAGS:
            if token_lower == blocked or token_lower.startswith(
                blocked.split("=")[0] + "="
            ):
                if blocked.split("=")[0] in token_lower:
                    if "=" in token:
                        _, value = token.split("=", 1)
                        blocked_value = (
                            blocked.split("=")[1] if "=" in blocked else None
                        )
                        if blocked_value and value.upper() == blocked_value:
                            return (False, f"Blocked flag: {token}")
                    elif token_lower == blocked:
                        return (False, f"Blocked flag: {token}")

        # Check for --privileged
        if token_lower == "--privileged":
            return (False, "Privileged mode is not allowed")

        # Check for dangerous capability additions
        if token_lower.startswith("--cap-add="):
            cap = token.split("=", 1)[1].upper()
            if cap in {"ALL", "SYS_ADMIN", "SYS_PTRACE", "SYS_RAWIO", "NET_ADMIN"}:
                return (False, f"Capability {cap} is not allowed")

        # Check for host namespace flags
        for ns in ["--pid=", "--network=", "--ipc=", "--userns=", "--uts="]:
            if token_lower.startswith(ns) and token_lower.endswith("host"):
                return (False, f"Host namespace mode is not allowed: {token}")

        # Check volume mounts
        if token_lower.startswith("-v=") or token_lower.startswith("--volume="):
            volume_spec = token.split("=", 1)[1]
            if not validate_volume_mount(volume_spec):
                return (False, f"Blocked volume mount: {volume_spec}")

        if token in ["-v", "--volume"] and i + 1 < len(tokens):
            volume_spec = tokens[i + 1]
            if not validate_volume_mount(volume_spec):
                return (False, f"Blocked volume mount: {volume_spec}")

        # Check for device mounts
        if token_lower.startswith("--device="):
            return (False, "Device mounts are not allowed")

        # Check security options
        if token_lower.startswith("--security-opt="):
            opt = token.split("=", 1)[1].lower()
            if "unconfined" in opt or "disabled" in opt:
                return (False, f"Insecure security option: {token}")

    return (True, "")


def validate_docker_params(params: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate Docker container parameters for security.

    Args:
        params: Container creation parameters.

    Returns:
        Tuple of (is_valid, error_message).
    """
    # Check for privileged mode
    if params.get("privileged"):
        return (False, "Privileged containers are not allowed")

    # Check capabilities
    cap_add = params.get("cap_add", [])
    for blocked in BLOCKED_DOCKER_PARAMS["cap_add"]:
        if blocked in cap_add:
            return (False, f"Capability {blocked} is not allowed")

    # Check namespace sharing
    for ns_param in ["pid_mode", "network_mode", "ipc_mode", "userns_mode"]:
        if params.get(ns_param) == "host":
            return (False, f"{ns_param}=host is not allowed")

    # Validate volume mounts
    volumes = params.get("volumes", {})
    for host_path, mount_config in volumes.items():
        host_path = os.path.normpath(host_path)

        mode = (
            mount_config.get("mode", "rw") if isinstance(mount_config, dict) else "rw"
        )
        if mode == "rw":
            for protected in PROTECTED_PATHS:
                if host_path == protected or host_path.startswith(protected + "/"):
                    return (False, f"Write access to {host_path} is not allowed")

        if host_path in ["/var/run/docker.sock", "/run/docker.sock"]:
            return (False, "Mounting Docker socket is not allowed")

    return (True, "")
```

### Step 4.2: Verify docker validation

```bash
cd agent && python -c "from src.lib.validation.docker_validation import *; print('OK')"
```

---

## Phase 5: Extract Command Validation

### Step 5.1: Create `command_validation.py`

Extract from `validation.py` lines 16-24, 176-355:

```python
# agent/src/lib/validation/command_validation.py
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
                        f"Timeout {timeout}s exceeds maximum {entry.max_timeout}s",
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
```

### Step 5.2: Verify command validation

```bash
cd agent && python -c "from src.lib.validation.command_validation import *; print('OK')"
```

---

## Phase 6: Create Package __init__.py

### Step 6.1: Create `validation/__init__.py`

```python
# agent/src/lib/validation/__init__.py
"""Command and Docker parameter validation.

Provides security validation for shell commands and Docker container parameters.

This package validates:
- Shell commands against a security allowlist
- Docker run commands for dangerous flags
- Docker container parameters for privilege escalation
- Volume mounts for sensitive paths
"""

from .constants import (
    BLOCKED_DOCKER_PARAMS,
    BLOCKED_DOCKER_RUN_FLAGS,
    BLOCKED_VOLUME_PATTERNS,
    PROTECTED_PATHS,
)
from .volume_validation import validate_volume_mount, validate_volume_path
from .docker_validation import validate_docker_params, validate_docker_run_command
from .command_validation import (
    CommandAllowlistEntry,
    CommandValidator,
    COMMAND_ALLOWLIST,
    validate_command,
)

__all__ = [
    # Constants
    "BLOCKED_DOCKER_PARAMS",
    "BLOCKED_DOCKER_RUN_FLAGS",
    "BLOCKED_VOLUME_PATTERNS",
    "PROTECTED_PATHS",
    # Volume validation
    "validate_volume_mount",
    "validate_volume_path",
    # Docker validation
    "validate_docker_params",
    "validate_docker_run_command",
    # Command validation
    "CommandAllowlistEntry",
    "CommandValidator",
    "COMMAND_ALLOWLIST",
    "validate_command",
]
```

---

## Phase 7: Update Parent __init__.py

### Step 7.1: Update `lib/__init__.py`

Change the validation imports from:

```python
from .validation import (...)
```

To:

```python
from .validation import (
    CommandValidator,
    CommandAllowlistEntry,
    COMMAND_ALLOWLIST,
    validate_command,
    validate_docker_params,
    validate_docker_run_command,
    BLOCKED_DOCKER_PARAMS,
    BLOCKED_DOCKER_RUN_FLAGS,
    BLOCKED_VOLUME_PATTERNS,
    PROTECTED_PATHS,
)
```

The import path remains the same (`.validation`) but now imports from the package.

---

## Phase 8: Remove Old File

### Step 8.1: Delete original validation.py

```bash
rm agent/src/lib/validation.py
```

**Note**: Only do this after all tests pass!

---

## Phase 9: Update Tests

### Step 9.1: Update test imports (if needed)

Most tests import from `lib.validation` or `lib`, which will continue to work. Check for any direct file imports.

### Step 9.2: Run full test suite

```bash
cd agent && pytest tests/ -v
```

### Step 9.3: Run with coverage

```bash
cd agent && pytest tests/ --cov=src/lib/validation --cov-report=term-missing
```

---

## Phase 10: Verification

### Step 10.1: Verify all imports work

```bash
cd agent && python -c "
from lib.validation import (
    CommandValidator,
    CommandAllowlistEntry,
    COMMAND_ALLOWLIST,
    validate_command,
    validate_docker_params,
    validate_docker_run_command,
    BLOCKED_DOCKER_PARAMS,
    BLOCKED_DOCKER_RUN_FLAGS,
    BLOCKED_VOLUME_PATTERNS,
    PROTECTED_PATHS,
)
print('All imports successful!')
"
```

### Step 10.2: Verify file line counts

```bash
wc -l agent/src/lib/validation/*.py
```

Expected output:
```
  ~60 constants.py
  ~70 volume_validation.py
 ~120 docker_validation.py
 ~180 command_validation.py
  ~40 __init__.py
 ~470 total
```

### Step 10.3: Check for circular imports

```bash
cd agent && python -c "
import sys
sys.path.insert(0, 'src')
from lib import validation
print('No circular imports!')
"
```

---

## Rollback Plan

If issues arise:

1. Restore original file from git:
   ```bash
   git checkout HEAD -- agent/src/lib/validation.py
   ```

2. Remove new package:
   ```bash
   rm -rf agent/src/lib/validation/
   ```

3. Revert lib/__init__.py changes:
   ```bash
   git checkout HEAD -- agent/src/lib/__init__.py
   ```

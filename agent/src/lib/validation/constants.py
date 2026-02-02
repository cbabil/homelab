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

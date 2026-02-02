"""JSON-RPC 2.0 error codes and custom exceptions."""

from dataclasses import dataclass, field
from typing import Any


# Standard JSON-RPC 2.0 error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# Custom error codes for agent operations
SECURITY_ERROR = -32001
RATE_LIMIT_ERROR = -32002
DOCKER_ERROR = -32003
CONTAINER_BLOCKED = -32004
COMMAND_BLOCKED = -32005


@dataclass
class RPCError(Exception):
    """JSON-RPC error exception."""

    code: int
    message: str
    data: Any = field(default=None)

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.data:
            return f"RPCError({self.code}): {self.message} - {self.data}"
        return f"RPCError({self.code}): {self.message}"


class AgentError(Exception):
    """Base exception for agent operations."""

    def __init__(self, message: str, code: int = INTERNAL_ERROR):
        super().__init__(message)
        self.message = message
        self.code = code


class SecurityError(AgentError):
    """Raised when an operation is blocked by security policy."""

    def __init__(self, message: str):
        super().__init__(message, SECURITY_ERROR)


class RateLimitError(AgentError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str):
        super().__init__(message, RATE_LIMIT_ERROR)


class DockerOperationError(AgentError):
    """Raised for Docker operation failures."""

    def __init__(self, message: str, operation: str = ""):
        self.operation = operation
        super().__init__(message, DOCKER_ERROR)


class ContainerBlockedError(SecurityError):
    """Raised when container creation is blocked by security policy."""

    def __init__(self, message: str, image: str = "", name: str = ""):
        self.image = image
        self.name = name
        super().__init__(message)
        self.code = CONTAINER_BLOCKED


class CommandBlockedError(SecurityError):
    """Raised when command execution is blocked by security policy."""

    def __init__(self, message: str, command: str = ""):
        self.command = command[:50] if command else ""  # Truncate for safety
        super().__init__(message)
        self.code = COMMAND_BLOCKED

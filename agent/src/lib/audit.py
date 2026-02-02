"""Audit logging for RPC operations.

Provides structured audit logging for security-sensitive operations.
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger("audit")


class AuditAction(str, Enum):
    """Types of auditable actions."""

    RPC_CALL = "rpc_call"
    RPC_SUCCESS = "rpc_success"
    RPC_ERROR = "rpc_error"
    AUTH_ATTEMPT = "auth_attempt"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    CONFIG_UPDATE = "config_update"
    COMMAND_EXEC = "command_exec"
    COMMAND_BLOCKED = "command_blocked"
    CONTAINER_CREATE = "container_create"
    CONTAINER_BLOCKED = "container_blocked"
    RATE_LIMITED = "rate_limited"


@dataclass
class AuditEntry:
    """Structured audit log entry."""

    action: AuditAction
    method: Optional[str] = None
    request_id: Optional[Any] = None
    agent_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    duration_ms: Optional[float] = None
    success: bool = True
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    details: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        result = {
            "action": self.action.value,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "success": self.success,
        }
        if self.method:
            result["method"] = self.method
        if self.request_id is not None:
            result["request_id"] = self.request_id
        if self.agent_id:
            result["agent_id"] = self.agent_id
        if self.duration_ms is not None:
            result["duration_ms"] = round(self.duration_ms, 2)
        if self.error_code is not None:
            result["error_code"] = self.error_code
        if self.error_message:
            result["error_message"] = self.error_message
        if self.details:
            result["details"] = self.details
        return result


class AuditLogger:
    """Handles structured audit logging."""

    def __init__(self, agent_id_getter: Optional[callable] = None):
        """Initialize audit logger.

        Args:
            agent_id_getter: Optional function to get current agent ID.
        """
        self._get_agent_id = agent_id_getter

    def log(self, entry: AuditEntry) -> None:
        """Log an audit entry."""
        if self._get_agent_id and not entry.agent_id:
            entry.agent_id = self._get_agent_id()
        logger.info(json.dumps(entry.to_dict()))

    def rpc_call(
        self,
        method: str,
        request_id: Any = None,
        params: Optional[dict] = None,
    ) -> str:
        """Log RPC call start, returns trace_id for correlation."""
        entry = AuditEntry(
            action=AuditAction.RPC_CALL,
            method=method,
            request_id=request_id,
            details={"params_keys": list(params.keys()) if params else []},
        )
        self.log(entry)
        return entry.trace_id

    def rpc_success(
        self,
        method: str,
        request_id: Any,
        trace_id: str,
        duration_ms: float,
    ) -> None:
        """Log successful RPC completion."""
        entry = AuditEntry(
            action=AuditAction.RPC_SUCCESS,
            method=method,
            request_id=request_id,
            trace_id=trace_id,
            duration_ms=duration_ms,
            success=True,
        )
        self.log(entry)

    def rpc_error(
        self,
        method: str,
        request_id: Any,
        trace_id: str,
        duration_ms: float,
        error_code: int,
        error_message: str,
    ) -> None:
        """Log RPC error."""
        entry = AuditEntry(
            action=AuditAction.RPC_ERROR,
            method=method,
            request_id=request_id,
            trace_id=trace_id,
            duration_ms=duration_ms,
            success=False,
            error_code=error_code,
            error_message=error_message,
        )
        self.log(entry)

    def command_blocked(
        self,
        command: str,
        reason: str,
    ) -> None:
        """Log blocked command execution."""
        # Truncate command for safety
        safe_command = command[:100] + "..." if len(command) > 100 else command
        entry = AuditEntry(
            action=AuditAction.COMMAND_BLOCKED,
            success=False,
            error_message=reason,
            details={"command": safe_command},
        )
        self.log(entry)

    def container_blocked(
        self,
        image: str,
        name: Optional[str],
        reason: str,
    ) -> None:
        """Log blocked container creation."""
        entry = AuditEntry(
            action=AuditAction.CONTAINER_BLOCKED,
            success=False,
            error_message=reason,
            details={"image": image, "name": name},
        )
        self.log(entry)

    def rate_limited(
        self,
        method: str,
        reason: str,
    ) -> None:
        """Log rate limiting event."""
        entry = AuditEntry(
            action=AuditAction.RATE_LIMITED,
            method=method,
            success=False,
            error_message=reason,
        )
        self.log(entry)

    def config_update(
        self,
        changes: dict,
    ) -> None:
        """Log configuration update."""
        entry = AuditEntry(
            action=AuditAction.CONFIG_UPDATE,
            details={"changed_keys": list(changes.keys())},
        )
        self.log(entry)

    def auth_attempt(self, auth_type: str) -> str:
        """Log authentication attempt, returns trace_id."""
        entry = AuditEntry(
            action=AuditAction.AUTH_ATTEMPT,
            details={"auth_type": auth_type},
        )
        self.log(entry)
        return entry.trace_id

    def auth_success(self, trace_id: str, agent_id: str) -> None:
        """Log successful authentication."""
        entry = AuditEntry(
            action=AuditAction.AUTH_SUCCESS,
            trace_id=trace_id,
            agent_id=agent_id,
        )
        self.log(entry)

    def auth_failure(self, trace_id: str, reason: str) -> None:
        """Log failed authentication."""
        entry = AuditEntry(
            action=AuditAction.AUTH_FAILURE,
            trace_id=trace_id,
            success=False,
            error_message=reason,
        )
        self.log(entry)


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def set_audit_logger(audit_logger: AuditLogger) -> None:
    """Set the global audit logger."""
    global _audit_logger
    _audit_logger = audit_logger

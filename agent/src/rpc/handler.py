"""JSON-RPC request handler."""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional, Set

try:
    from ..lib.permissions import get_method_permission, PermissionLevel
except ImportError:
    from lib.permissions import get_method_permission, PermissionLevel

logger = logging.getLogger(__name__)


class RPCError(Exception):
    """JSON-RPC error."""

    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class RPCHandler:
    """Handles JSON-RPC method dispatch with permission checking."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    PERMISSION_DENIED = -32001  # Custom code for permission errors

    def __init__(self, allowed_permissions: Optional[Set[PermissionLevel]] = None):
        """Initialize RPC handler.

        Args:
            allowed_permissions: Set of allowed permission levels. If None,
                                all permissions are allowed (for backwards
                                compatibility during transition).
        """
        self._methods: Dict[str, Callable] = {}
        # Default to allowing all permissions; configure for security
        self._allowed_permissions = allowed_permissions or {
            PermissionLevel.READ,
            PermissionLevel.EXECUTE,
            PermissionLevel.ADMIN,
        }

    def register(self, name: str, handler: Callable) -> None:
        """Register a method handler."""
        self._methods[name] = handler

    def register_module(self, prefix: str, module: object) -> None:
        """Register all public methods from a module with a prefix."""
        for name in dir(module):
            if name.startswith("_"):
                continue
            attr = getattr(module, name)
            if callable(attr):
                self._methods[f"{prefix}.{name}"] = attr

    def set_allowed_permissions(self, permissions: Set[PermissionLevel]) -> None:
        """Update allowed permission levels.

        Args:
            permissions: New set of allowed permission levels.
        """
        self._allowed_permissions = permissions
        logger.info(
            "Updated allowed permissions",
            extra={"permissions": [p.value for p in permissions]},
        )

    async def handle(self, request: dict) -> Optional[dict]:
        """Handle a JSON-RPC request with permission checking."""
        request_id = request.get("id")
        is_notification = request_id is None

        try:
            method = request.get("method")
            if not method:
                raise RPCError(self.INVALID_REQUEST, "Missing method")

            if method not in self._methods:
                raise RPCError(self.METHOD_NOT_FOUND, f"Method not found: {method}")

            # Check permission level for this method
            required_permission = get_method_permission(method)
            if required_permission not in self._allowed_permissions:
                logger.warning(
                    "Permission denied for method",
                    extra={
                        "method": method,
                        "required": required_permission.value,
                        "allowed": [p.value for p in self._allowed_permissions],
                    },
                )
                raise RPCError(
                    self.PERMISSION_DENIED,
                    f"Permission denied: requires {required_permission.value}",
                )

            params = request.get("params", {})
            handler = self._methods[method]

            if asyncio.iscoroutinefunction(handler):
                if isinstance(params, dict):
                    result = await handler(**params)
                else:
                    result = await handler(*params)
            else:
                if isinstance(params, dict):
                    result = handler(**params)
                else:
                    result = handler(*params)

            if is_notification:
                return None

            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id,
            }

        except RPCError as e:
            if is_notification:
                logger.error(f"Notification error: {e.message}")
                return None
            return {
                "jsonrpc": "2.0",
                "error": {"code": e.code, "message": e.message, "data": e.data},
                "id": request_id,
            }
        except Exception:
            # Log full error for debugging but sanitize for client
            logger.exception(f"Internal error handling {request.get('method')}")
            if is_notification:
                return None
            # Don't leak internal error details to client
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": self.INTERNAL_ERROR,
                    "message": "Internal server error",
                },
                "id": request_id,
            }

"""JSON-RPC 2.0 response builders."""

from typing import Any, Dict


def success_response(request_id: Any, result: Any) -> dict:
    """Build a JSON-RPC success response."""
    return {"jsonrpc": "2.0", "result": result, "id": request_id}


def error_response(
    request_id: Any,
    code: int,
    message: str,
    data: Any = None,
) -> dict:
    """Build a JSON-RPC error response."""
    error: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "error": error, "id": request_id}

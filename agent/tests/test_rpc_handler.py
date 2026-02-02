"""Tests for RPC handler module.

Tests JSON-RPC request handling, method registration, and permission checking.
"""

import pytest

from rpc.handler import RPCHandler, RPCError
from lib.permissions import PermissionLevel


class TestRPCHandler:
    """Tests for RPCHandler class."""

    def test_register_method(self):
        """Should register a method handler."""
        handler = RPCHandler()

        def my_method():
            return {"result": "test"}

        handler.register("my.method", my_method)

        assert "my.method" in handler._methods

    def test_register_module(self):
        """Should register all public methods from a module."""
        handler = RPCHandler()

        class TestModule:
            def public_method(self):
                return "public"

            def another_public(self):
                return "another"

            def _private_method(self):
                return "private"

        handler.register_module("test", TestModule())

        assert "test.public_method" in handler._methods
        assert "test.another_public" in handler._methods
        assert "test._private_method" not in handler._methods

    @pytest.mark.asyncio
    async def test_handle_valid_request(self):
        """Should handle valid JSON-RPC request."""
        handler = RPCHandler()

        def add_numbers(a, b):
            return a + b

        handler.register("math.add", add_numbers)

        request = {
            "jsonrpc": "2.0",
            "method": "math.add",
            "params": {"a": 5, "b": 3},
            "id": 1,
        }

        response = await handler.handle(request)

        assert response["jsonrpc"] == "2.0"
        assert response["result"] == 8
        assert response["id"] == 1

    @pytest.mark.asyncio
    async def test_handle_notification(self):
        """Should return None for notifications (no id)."""
        handler = RPCHandler()

        def log_event(message):
            pass  # Just logs

        handler.register("log.event", log_event)

        request = {
            "jsonrpc": "2.0",
            "method": "log.event",
            "params": {"message": "test"},
            # No id - this is a notification
        }

        response = await handler.handle(request)

        assert response is None

    @pytest.mark.asyncio
    async def test_handle_missing_method(self):
        """Should return error for missing method."""
        handler = RPCHandler()

        request = {
            "jsonrpc": "2.0",
            "method": "nonexistent.method",
            "id": 1,
        }

        response = await handler.handle(request)

        assert response["error"]["code"] == RPCHandler.METHOD_NOT_FOUND
        assert "not found" in response["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_handle_invalid_request_no_method(self):
        """Should return error when method is missing."""
        handler = RPCHandler()

        request = {
            "jsonrpc": "2.0",
            "params": {},
            "id": 1,
        }

        response = await handler.handle(request)

        assert response["error"]["code"] == RPCHandler.INVALID_REQUEST

    @pytest.mark.asyncio
    async def test_handle_async_method(self):
        """Should handle async method handlers."""
        handler = RPCHandler()

        async def async_method():
            return {"async": True}

        handler.register("async.test", async_method)

        request = {
            "jsonrpc": "2.0",
            "method": "async.test",
            "params": {},
            "id": 1,
        }

        response = await handler.handle(request)

        assert response["result"] == {"async": True}

    @pytest.mark.asyncio
    async def test_handle_list_params(self):
        """Should handle positional parameters as list."""
        handler = RPCHandler()

        def concat(*args):
            return "".join(args)

        handler.register("string.concat", concat)

        request = {
            "jsonrpc": "2.0",
            "method": "string.concat",
            "params": ["hello", " ", "world"],
            "id": 1,
        }

        response = await handler.handle(request)

        assert response["result"] == "hello world"

    @pytest.mark.asyncio
    async def test_handle_internal_error(self):
        """Should return internal error for exceptions."""
        handler = RPCHandler()

        def failing_method():
            raise ValueError("Something went wrong")

        handler.register("fail.method", failing_method)

        request = {
            "jsonrpc": "2.0",
            "method": "fail.method",
            "params": {},
            "id": 1,
        }

        response = await handler.handle(request)

        assert response["error"]["code"] == RPCHandler.INTERNAL_ERROR
        # Should not leak internal error details
        assert "Internal server error" in response["error"]["message"]
        assert "Something went wrong" not in response["error"]["message"]


class TestRPCHandlerPermissions:
    """Tests for RPC handler permission checking."""

    @pytest.mark.asyncio
    async def test_allows_permitted_method(self):
        """Should allow method with permitted permission level."""
        handler = RPCHandler(allowed_permissions={PermissionLevel.READ})

        def read_method():
            return {"data": "value"}

        handler.register(
            "system.info", read_method
        )  # READ permission in METHOD_PERMISSIONS

        request = {
            "jsonrpc": "2.0",
            "method": "system.info",
            "params": {},
            "id": 1,
        }

        response = await handler.handle(request)

        assert "result" in response
        assert response["result"] == {"data": "value"}

    @pytest.mark.asyncio
    async def test_denies_unpermitted_method(self):
        """Should deny method without permitted permission level."""
        handler = RPCHandler(allowed_permissions={PermissionLevel.READ})

        def admin_method():
            return {"admin": True}

        # system.exec requires ADMIN permission
        handler.register("system.exec", admin_method)

        request = {
            "jsonrpc": "2.0",
            "method": "system.exec",
            "params": {},
            "id": 1,
        }

        response = await handler.handle(request)

        assert "error" in response
        assert response["error"]["code"] == RPCHandler.PERMISSION_DENIED
        assert "permission denied" in response["error"]["message"].lower()

    def test_set_allowed_permissions(self):
        """Should update allowed permissions."""
        handler = RPCHandler()

        # Initially all permissions allowed
        assert PermissionLevel.ADMIN in handler._allowed_permissions

        # Restrict to READ only
        handler.set_allowed_permissions({PermissionLevel.READ})

        assert handler._allowed_permissions == {PermissionLevel.READ}

    @pytest.mark.asyncio
    async def test_unknown_method_requires_admin(self):
        """Unknown methods should default to requiring ADMIN permission."""
        handler = RPCHandler(allowed_permissions={PermissionLevel.READ})

        def unknown_handler():
            return {"data": "secret"}

        handler.register("unknown.dangerous", unknown_handler)

        request = {
            "jsonrpc": "2.0",
            "method": "unknown.dangerous",
            "params": {},
            "id": 1,
        }

        response = await handler.handle(request)

        # Should be denied since unknown defaults to ADMIN
        assert "error" in response
        assert response["error"]["code"] == RPCHandler.PERMISSION_DENIED


class TestRPCError:
    """Tests for RPCError exception."""

    def test_rpc_error_attributes(self):
        """Should store error attributes correctly."""
        error = RPCError(
            code=-32600, message="Invalid request", data={"field": "method"}
        )

        assert error.code == -32600
        assert error.message == "Invalid request"
        assert error.data == {"field": "method"}

    def test_rpc_error_str(self):
        """Should have message as string representation."""
        error = RPCError(code=-32600, message="Invalid request")

        assert str(error) == "Invalid request"

"""Tests for RPC error codes and exception.

Tests JSON-RPC 2.0 error handling.
"""

from rpc.errors import (
    RPCError,
    PARSE_ERROR,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)


class TestErrorCodes:
    """Tests for JSON-RPC error codes."""

    def test_parse_error_code(self):
        """Should have correct parse error code."""
        assert PARSE_ERROR == -32700

    def test_invalid_request_code(self):
        """Should have correct invalid request code."""
        assert INVALID_REQUEST == -32600

    def test_method_not_found_code(self):
        """Should have correct method not found code."""
        assert METHOD_NOT_FOUND == -32601

    def test_invalid_params_code(self):
        """Should have correct invalid params code."""
        assert INVALID_PARAMS == -32602

    def test_internal_error_code(self):
        """Should have correct internal error code."""
        assert INTERNAL_ERROR == -32603


class TestRPCError:
    """Tests for RPCError exception."""

    def test_creates_error_with_code_and_message(self):
        """Should create error with code and message."""
        error = RPCError(code=-32600, message="Invalid Request")

        assert error.code == -32600
        assert error.message == "Invalid Request"
        assert error.data is None

    def test_creates_error_with_data(self):
        """Should create error with optional data."""
        error = RPCError(
            code=-32602,
            message="Invalid params",
            data={"param": "missing_field"},
        )

        assert error.code == -32602
        assert error.message == "Invalid params"
        assert error.data == {"param": "missing_field"}

    def test_str_without_data(self):
        """Should format string without data."""
        error = RPCError(code=-32601, message="Method not found")

        assert str(error) == "RPCError(-32601): Method not found"

    def test_str_with_data(self):
        """Should format string with data."""
        error = RPCError(
            code=-32602,
            message="Invalid params",
            data="field 'name' required",
        )

        result = str(error)
        assert "RPCError(-32602)" in result
        assert "Invalid params" in result
        assert "field 'name' required" in result

    def test_is_exception(self):
        """Should be an exception."""
        error = RPCError(code=-32603, message="Internal error")

        assert isinstance(error, Exception)

    def test_can_be_raised(self):
        """Should be raisable as exception."""
        try:
            raise RPCError(code=-32700, message="Parse error")
        except RPCError as e:
            assert e.code == -32700
            assert e.message == "Parse error"

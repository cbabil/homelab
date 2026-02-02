"""Tests for RPC response builders.

Tests JSON-RPC 2.0 response construction.
"""

from rpc.responses import success_response, error_response


class TestSuccessResponse:
    """Tests for success_response builder."""

    def test_builds_basic_response(self):
        """Should build basic success response."""
        response = success_response(request_id=1, result="ok")

        assert response == {
            "jsonrpc": "2.0",
            "result": "ok",
            "id": 1,
        }

    def test_includes_jsonrpc_version(self):
        """Should always include JSON-RPC version."""
        response = success_response(request_id=1, result={})

        assert response["jsonrpc"] == "2.0"

    def test_handles_dict_result(self):
        """Should handle dictionary results."""
        result = {"containers": [{"id": "abc123", "name": "test"}]}
        response = success_response(request_id="req-1", result=result)

        assert response["result"] == result

    def test_handles_list_result(self):
        """Should handle list results."""
        result = [1, 2, 3]
        response = success_response(request_id=42, result=result)

        assert response["result"] == result

    def test_handles_none_result(self):
        """Should handle None result."""
        response = success_response(request_id=1, result=None)

        assert response["result"] is None

    def test_handles_string_request_id(self):
        """Should handle string request IDs."""
        response = success_response(request_id="uuid-123", result="done")

        assert response["id"] == "uuid-123"

    def test_handles_null_request_id(self):
        """Should handle null request ID."""
        response = success_response(request_id=None, result="ok")

        assert response["id"] is None


class TestErrorResponse:
    """Tests for error_response builder."""

    def test_builds_basic_error_response(self):
        """Should build basic error response."""
        response = error_response(
            request_id=1,
            code=-32600,
            message="Invalid Request",
        )

        assert response == {
            "jsonrpc": "2.0",
            "error": {
                "code": -32600,
                "message": "Invalid Request",
            },
            "id": 1,
        }

    def test_includes_jsonrpc_version(self):
        """Should always include JSON-RPC version."""
        response = error_response(request_id=1, code=-32603, message="Error")

        assert response["jsonrpc"] == "2.0"

    def test_includes_data_when_provided(self):
        """Should include data field when provided."""
        response = error_response(
            request_id=1,
            code=-32602,
            message="Invalid params",
            data={"missing": ["field1", "field2"]},
        )

        assert response["error"]["data"] == {"missing": ["field1", "field2"]}

    def test_omits_data_when_none(self):
        """Should not include data field when None."""
        response = error_response(
            request_id=1,
            code=-32601,
            message="Method not found",
            data=None,
        )

        assert "data" not in response["error"]

    def test_handles_string_data(self):
        """Should handle string data."""
        response = error_response(
            request_id=1,
            code=-32700,
            message="Parse error",
            data="Unexpected token at position 42",
        )

        assert response["error"]["data"] == "Unexpected token at position 42"

    def test_handles_string_request_id(self):
        """Should handle string request IDs."""
        response = error_response(
            request_id="req-abc",
            code=-32603,
            message="Internal error",
        )

        assert response["id"] == "req-abc"

    def test_handles_null_request_id(self):
        """Should handle null request ID for notifications."""
        response = error_response(
            request_id=None,
            code=-32600,
            message="Invalid Request",
        )

        assert response["id"] is None

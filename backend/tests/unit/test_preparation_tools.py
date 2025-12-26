"""Tests for preparation MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from tools.preparation_tools import PreparationTools
from models.preparation import PreparationStatus, PreparationStep


@pytest.fixture
def mock_prep_service():
    """Create mock preparation service."""
    svc = MagicMock()
    svc.start_preparation = AsyncMock()
    svc.get_preparation_status = AsyncMock()
    svc.execute_preparation = AsyncMock()
    return svc


@pytest.fixture
def prep_tools(mock_prep_service):
    """Create preparation tools with mock."""
    return PreparationTools(mock_prep_service)


class TestPrepareServer:
    """Tests for prepare_server tool."""

    @pytest.mark.asyncio
    async def test_prepare_server_success(self, prep_tools, mock_prep_service):
        """Should start preparation successfully."""
        mock_prep_service.start_preparation.return_value = MagicMock(id="prep-123")

        result = await prep_tools.prepare_server(server_id="server-456")

        assert result["success"] is True
        assert "prep-123" in str(result["data"])

    @pytest.mark.asyncio
    async def test_prepare_server_not_found(self, prep_tools, mock_prep_service):
        """Should return error if server not found."""
        mock_prep_service.start_preparation.return_value = None

        result = await prep_tools.prepare_server(server_id="nonexistent")

        assert result["success"] is False
        assert result["error"] == "PREPARATION_START_FAILED"


class TestGetPreparationStatus:
    """Tests for get_preparation_status tool."""

    @pytest.mark.asyncio
    async def test_get_status_success(self, prep_tools, mock_prep_service):
        """Should return preparation status."""
        mock_prep_service.get_preparation_status.return_value = {
            "id": "prep-123",
            "status": "in_progress",
            "current_step": "install_docker",
            "logs": []
        }

        result = await prep_tools.get_preparation_status(server_id="server-456")

        assert result["success"] is True
        assert result["data"]["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, prep_tools, mock_prep_service):
        """Should return error if no preparation found."""
        mock_prep_service.get_preparation_status.return_value = None

        result = await prep_tools.get_preparation_status(server_id="server-456")

        assert result["success"] is False
        assert result["error"] == "PREPARATION_NOT_FOUND"

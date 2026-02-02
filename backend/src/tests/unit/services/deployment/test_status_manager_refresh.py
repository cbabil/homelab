"""
Unit tests for services/deployment/status.py - Refresh functionality

Tests for refresh_installation_status method.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_ssh_executor():
    """Create mock SSH executor."""
    executor = MagicMock()
    executor.execute = AsyncMock(return_value=(0, "running", ""))
    return executor


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    service = MagicMock()
    service.get_installation_by_id = AsyncMock(return_value=None)
    service.update_installation = AsyncMock()
    return service


@pytest.fixture
def mock_server_service():
    """Create mock server service."""
    return MagicMock()


@pytest.fixture
def mock_marketplace_service():
    """Create mock marketplace service."""
    return MagicMock()


@pytest.fixture
def sample_installation():
    """Create sample installation mock."""
    inst = MagicMock()
    inst.id = "inst-123"
    inst.app_id = "app-1"
    inst.server_id = "server-1"
    inst.container_name = "test-container"
    inst.container_id = "abc123def456"
    inst.status = "running"
    inst.installed_at = "2024-01-01T00:00:00Z"
    inst.started_at = "2024-01-01T00:01:00Z"
    inst.error_message = None
    return inst


@pytest.fixture
def status_manager(
    mock_ssh_executor,
    mock_db_service,
    mock_server_service,
    mock_marketplace_service
):
    """Create StatusManager instance with mocked dependencies."""
    from services.deployment.status import StatusManager
    return StatusManager(
        ssh_executor=mock_ssh_executor,
        db_service=mock_db_service,
        server_service=mock_server_service,
        marketplace_service=mock_marketplace_service
    )


@pytest.fixture
def docker_inspect_running():
    """Docker inspect output for running container."""
    return json.dumps([{
        "State": {"Status": "running"},
        "NetworkSettings": {
            "Networks": {
                "bridge": {},
                "custom-net": {}
            }
        },
        "Mounts": [
            {
                "Type": "volume",
                "Name": "data-vol",
                "Destination": "/data",
                "Mode": "rw"
            },
            {
                "Type": "bind",
                "Source": "/host/path",
                "Destination": "/container/path",
                "Mode": "ro"
            }
        ]
    }])


class TestRefreshInstallationStatus:
    """Tests for refresh_installation_status method."""

    @pytest.mark.asyncio
    async def test_returns_none_when_installation_not_found(
        self, status_manager, mock_db_service
    ):
        """Should return None when installation not found."""
        mock_db_service.get_installation_by_id.return_value = None

        result = await status_manager.refresh_installation_status("inst-123")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_status_without_docker_when_no_container(
        self, status_manager, mock_db_service, sample_installation
    ):
        """Should return status from DB when no container name."""
        sample_installation.container_name = None
        sample_installation.status = "pending"
        mock_db_service.get_installation_by_id.return_value = sample_installation

        result = await status_manager.refresh_installation_status("inst-123")

        assert result == {"status": "pending"}

    @pytest.mark.asyncio
    async def test_handles_enum_status_without_container(
        self, status_manager, mock_db_service, sample_installation
    ):
        """Should handle enum status when no container."""
        sample_installation.container_name = None
        sample_installation.status = MagicMock()
        sample_installation.status.value = "deploying"
        mock_db_service.get_installation_by_id.return_value = sample_installation

        result = await status_manager.refresh_installation_status("inst-123")

        assert result == {"status": "deploying"}

    @pytest.mark.asyncio
    async def test_returns_stopped_on_docker_inspect_failure(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """Should return stopped when docker inspect fails."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        mock_ssh_executor.execute.return_value = (1, "", "container not found")

        result = await status_manager.refresh_installation_status("inst-123")

        assert result == {"status": "stopped"}

    @pytest.mark.asyncio
    async def test_returns_stopped_on_empty_stdout(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """Should return stopped when stdout is empty."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        mock_ssh_executor.execute.return_value = (0, "", "")

        result = await status_manager.refresh_installation_status("inst-123")

        assert result == {"status": "stopped"}

    @pytest.mark.asyncio
    async def test_returns_stopped_on_empty_json_array(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """Should return stopped when JSON is empty array."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        mock_ssh_executor.execute.return_value = (0, "[]", "")

        result = await status_manager.refresh_installation_status("inst-123")

        assert result == {"status": "stopped"}

    @pytest.mark.asyncio
    async def test_parses_running_status(
        self, status_manager, mock_db_service, mock_ssh_executor,
        sample_installation, docker_inspect_running
    ):
        """Should correctly parse running status."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        mock_ssh_executor.execute.return_value = (0, docker_inspect_running, "")

        result = await status_manager.refresh_installation_status("inst-123")

        assert result["status"] == "running"

    @pytest.mark.asyncio
    async def test_parses_exited_status_as_stopped(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """Should parse exited status as stopped."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        inspect_data = json.dumps([{"State": {"Status": "exited"}, "NetworkSettings": {"Networks": {}}, "Mounts": []}])
        mock_ssh_executor.execute.return_value = (0, inspect_data, "")

        result = await status_manager.refresh_installation_status("inst-123")

        assert result["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_parses_restarting_status_as_error(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """Should parse restarting status as error."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        inspect_data = json.dumps([{"State": {"Status": "restarting"}, "NetworkSettings": {"Networks": {}}, "Mounts": []}])
        mock_ssh_executor.execute.return_value = (0, inspect_data, "")

        result = await status_manager.refresh_installation_status("inst-123")

        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_parses_created_status_as_stopped(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """Should parse created status as stopped."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        inspect_data = json.dumps([{"State": {"Status": "created"}, "NetworkSettings": {"Networks": {}}, "Mounts": []}])
        mock_ssh_executor.execute.return_value = (0, inspect_data, "")

        result = await status_manager.refresh_installation_status("inst-123")

        assert result["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_parses_paused_status_as_stopped(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """Should parse paused status as stopped."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        inspect_data = json.dumps([{"State": {"Status": "paused"}, "NetworkSettings": {"Networks": {}}, "Mounts": []}])
        mock_ssh_executor.execute.return_value = (0, inspect_data, "")

        result = await status_manager.refresh_installation_status("inst-123")

        assert result["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_parses_unknown_status(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """Should preserve unknown status value."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        inspect_data = json.dumps([{"State": {"Status": "custom_status"}, "NetworkSettings": {"Networks": {}}, "Mounts": []}])
        mock_ssh_executor.execute.return_value = (0, inspect_data, "")

        result = await status_manager.refresh_installation_status("inst-123")

        assert result["status"] == "custom_status"

    @pytest.mark.asyncio
    async def test_handles_empty_status(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """Should default to stopped when status is empty."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        inspect_data = json.dumps([{"State": {"Status": ""}, "NetworkSettings": {"Networks": {}}, "Mounts": []}])
        mock_ssh_executor.execute.return_value = (0, inspect_data, "")

        result = await status_manager.refresh_installation_status("inst-123")

        assert result["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_extracts_networks(
        self, status_manager, mock_db_service, mock_ssh_executor,
        sample_installation, docker_inspect_running
    ):
        """Should extract network names."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        mock_ssh_executor.execute.return_value = (0, docker_inspect_running, "")

        result = await status_manager.refresh_installation_status("inst-123")

        assert "bridge" in result["networks"]
        assert "custom-net" in result["networks"]

    @pytest.mark.asyncio
    async def test_extracts_named_volumes(
        self, status_manager, mock_db_service, mock_ssh_executor,
        sample_installation, docker_inspect_running
    ):
        """Should extract named volumes."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        mock_ssh_executor.execute.return_value = (0, docker_inspect_running, "")

        result = await status_manager.refresh_installation_status("inst-123")

        assert len(result["named_volumes"]) == 1
        assert result["named_volumes"][0]["name"] == "data-vol"
        assert result["named_volumes"][0]["destination"] == "/data"
        assert result["named_volumes"][0]["mode"] == "rw"

    @pytest.mark.asyncio
    async def test_extracts_bind_mounts(
        self, status_manager, mock_db_service, mock_ssh_executor,
        sample_installation, docker_inspect_running
    ):
        """Should extract bind mounts."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        mock_ssh_executor.execute.return_value = (0, docker_inspect_running, "")

        result = await status_manager.refresh_installation_status("inst-123")

        assert len(result["bind_mounts"]) == 1
        assert result["bind_mounts"][0]["source"] == "/host/path"
        assert result["bind_mounts"][0]["destination"] == "/container/path"
        assert result["bind_mounts"][0]["mode"] == "ro"

    @pytest.mark.asyncio
    async def test_updates_database(
        self, status_manager, mock_db_service, mock_ssh_executor,
        sample_installation, docker_inspect_running
    ):
        """Should update database with new status."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        mock_ssh_executor.execute.return_value = (0, docker_inspect_running, "")

        await status_manager.refresh_installation_status("inst-123")

        mock_db_service.update_installation.assert_called_once()
        call_args = mock_db_service.update_installation.call_args
        assert call_args[0][0] == "inst-123"
        assert call_args[1]["status"] == "running"

    @pytest.mark.asyncio
    async def test_handles_exception(
        self, status_manager, mock_db_service
    ):
        """Should return None on exception."""
        mock_db_service.get_installation_by_id.side_effect = Exception("DB error")

        with patch("services.deployment.status.logger") as mock_logger:
            result = await status_manager.refresh_installation_status("inst-123")

        assert result is None
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_json_parse_error(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """Should handle JSON parse error gracefully."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        mock_ssh_executor.execute.return_value = (0, "invalid json", "")

        with patch("services.deployment.status.logger") as mock_logger:
            result = await status_manager.refresh_installation_status("inst-123")

        assert result is None
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_missing_state_key(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """Should handle missing State key gracefully."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        inspect_data = json.dumps([{"NetworkSettings": {"Networks": {}}, "Mounts": []}])
        mock_ssh_executor.execute.return_value = (0, inspect_data, "")

        result = await status_manager.refresh_installation_status("inst-123")

        assert result["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_handles_missing_network_settings(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """Should handle missing NetworkSettings gracefully."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        inspect_data = json.dumps([{"State": {"Status": "running"}, "Mounts": []}])
        mock_ssh_executor.execute.return_value = (0, inspect_data, "")

        result = await status_manager.refresh_installation_status("inst-123")

        assert result["networks"] == []

    @pytest.mark.asyncio
    async def test_handles_missing_mounts(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """Should handle missing Mounts gracefully."""
        mock_db_service.get_installation_by_id.return_value = sample_installation
        inspect_data = json.dumps([{"State": {"Status": "running"}, "NetworkSettings": {"Networks": {"bridge": {}}}}])
        mock_ssh_executor.execute.return_value = (0, inspect_data, "")

        result = await status_manager.refresh_installation_status("inst-123")

        assert result["named_volumes"] == []
        assert result["bind_mounts"] == []

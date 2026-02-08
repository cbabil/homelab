"""
Unit tests for services/deployment/status.py - Details functionality

Tests for get_all_installations_with_details method.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


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
    service.get_all_installations = AsyncMock(return_value=[])
    service.update_installation = AsyncMock()
    return service


@pytest.fixture
def mock_server_service():
    """Create mock server service."""
    service = MagicMock()
    server_mock = MagicMock()
    server_mock.id = "server-1"
    server_mock.name = "Test Server"
    server_mock.host = "192.168.1.100"
    service.get_server = AsyncMock(return_value=server_mock)
    return service


@pytest.fixture
def mock_marketplace_service():
    """Create mock marketplace service."""
    service = MagicMock()
    app_mock = MagicMock()
    app_mock.id = "app-1"
    app_mock.name = "Test App"
    app_mock.version = "1.0.0"
    app_mock.description = "A test app"
    app_mock.icon = "test-icon"
    app_mock.category = "Utilities"
    app_mock.repo_id = "repo-1"
    service.get_app = AsyncMock(return_value=app_mock)
    repo_mock = MagicMock()
    repo_mock.id = "repo-1"
    repo_mock.name = "Test Repo"
    service.get_repo = AsyncMock(return_value=repo_mock)
    return service


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
    inst.config = {"ports": {"8080": 8080}, "env": {"DEBUG": "true"}, "volumes": {}}
    inst.networks = ["bridge"]
    inst.named_volumes = []
    inst.bind_mounts = []
    return inst


@pytest.fixture
def status_manager(
    mock_ssh_executor, mock_db_service, mock_server_service, mock_marketplace_service
):
    """Create StatusManager instance with mocked dependencies."""
    from services.deployment.status import StatusManager

    return StatusManager(
        ssh_executor=mock_ssh_executor,
        db_service=mock_db_service,
        server_service=mock_server_service,
        marketplace_service=mock_marketplace_service,
    )


class TestGetAllInstallationsWithDetails:
    """Tests for get_all_installations_with_details method."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_installations(
        self, status_manager, mock_db_service
    ):
        """Should return empty list when no installations exist."""
        mock_db_service.get_all_installations.return_value = []

        result = await status_manager.get_all_installations_with_details()

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_installations_is_none(
        self, status_manager, mock_db_service
    ):
        """Should return empty list when installations is None."""
        mock_db_service.get_all_installations.return_value = None

        result = await status_manager.get_all_installations_with_details()

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_detailed_installation_info(
        self,
        status_manager,
        mock_db_service,
        mock_server_service,
        mock_marketplace_service,
        sample_installation,
    ):
        """Should return detailed installation info with server and app data."""
        mock_db_service.get_all_installations.return_value = [sample_installation]

        result = await status_manager.get_all_installations_with_details()

        assert len(result) == 1
        assert result[0]["id"] == "inst-123"
        assert result[0]["app_name"] == "Test App"
        assert result[0]["server_name"] == "Test Server"
        assert result[0]["app_source"] == "Test Repo"

    @pytest.mark.asyncio
    async def test_includes_app_metadata(
        self,
        status_manager,
        mock_db_service,
        mock_marketplace_service,
        sample_installation,
    ):
        """Should include app metadata in result."""
        mock_db_service.get_all_installations.return_value = [sample_installation]

        result = await status_manager.get_all_installations_with_details()

        assert result[0]["app_icon"] == "test-icon"
        assert result[0]["app_version"] == "1.0.0"
        assert result[0]["app_description"] == "A test app"
        assert result[0]["app_category"] == "Utilities"

    @pytest.mark.asyncio
    async def test_includes_server_metadata(
        self, status_manager, mock_db_service, mock_server_service, sample_installation
    ):
        """Should include server metadata in result."""
        mock_db_service.get_all_installations.return_value = [sample_installation]

        result = await status_manager.get_all_installations_with_details()

        assert result[0]["server_host"] == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_includes_container_info(
        self, status_manager, mock_db_service, sample_installation
    ):
        """Should include container info in result."""
        mock_db_service.get_all_installations.return_value = [sample_installation]

        result = await status_manager.get_all_installations_with_details()

        assert result[0]["container_id"] == "abc123def456"
        assert result[0]["container_name"] == "test-container"
        assert result[0]["status"] == "running"

    @pytest.mark.asyncio
    async def test_includes_config_ports(
        self, status_manager, mock_db_service, sample_installation
    ):
        """Should include ports from config."""
        mock_db_service.get_all_installations.return_value = [sample_installation]

        result = await status_manager.get_all_installations_with_details()

        assert result[0]["ports"] == {"8080": 8080}

    @pytest.mark.asyncio
    async def test_includes_config_env(
        self, status_manager, mock_db_service, sample_installation
    ):
        """Should include env from config."""
        mock_db_service.get_all_installations.return_value = [sample_installation]

        result = await status_manager.get_all_installations_with_details()

        assert result[0]["env"] == {"DEBUG": "true"}

    @pytest.mark.asyncio
    async def test_handles_missing_app(
        self,
        status_manager,
        mock_db_service,
        mock_marketplace_service,
        sample_installation,
    ):
        """Should handle missing app gracefully."""
        mock_db_service.get_all_installations.return_value = [sample_installation]
        mock_marketplace_service.get_app.return_value = None

        result = await status_manager.get_all_installations_with_details()

        assert result[0]["app_name"] == "app-1"
        assert result[0]["app_icon"] is None
        assert result[0]["app_version"] == "Unknown"
        assert result[0]["app_source"] == "Unknown"

    @pytest.mark.asyncio
    async def test_handles_missing_server(
        self, status_manager, mock_db_service, mock_server_service, sample_installation
    ):
        """Should handle missing server gracefully."""
        mock_db_service.get_all_installations.return_value = [sample_installation]
        mock_server_service.get_server.return_value = None

        result = await status_manager.get_all_installations_with_details()

        assert result[0]["server_name"] == "Unknown"
        assert result[0]["server_host"] == ""

    @pytest.mark.asyncio
    async def test_handles_missing_repo(
        self,
        status_manager,
        mock_db_service,
        mock_marketplace_service,
        sample_installation,
    ):
        """Should handle missing repo gracefully."""
        mock_db_service.get_all_installations.return_value = [sample_installation]
        mock_marketplace_service.get_repo.return_value = None

        result = await status_manager.get_all_installations_with_details()

        assert result[0]["app_source"] == "Unknown"

    @pytest.mark.asyncio
    async def test_handles_app_without_repo_id(
        self,
        status_manager,
        mock_db_service,
        mock_marketplace_service,
        sample_installation,
    ):
        """Should handle app without repo_id gracefully."""
        mock_db_service.get_all_installations.return_value = [sample_installation]
        app = MagicMock()
        app.id = "app-1"
        app.name = "Test App"
        app.version = "1.0.0"
        app.description = "Test"
        app.icon = None
        app.category = "Utilities"
        app.repo_id = None
        mock_marketplace_service.get_app.return_value = app

        result = await status_manager.get_all_installations_with_details()

        assert result[0]["app_source"] == "Unknown"

    @pytest.mark.asyncio
    async def test_handles_enum_status(
        self, status_manager, mock_db_service, sample_installation
    ):
        """Should handle enum status value."""
        sample_installation.status = MagicMock()
        sample_installation.status.value = "running"
        mock_db_service.get_all_installations.return_value = [sample_installation]

        result = await status_manager.get_all_installations_with_details()

        assert result[0]["status"] == "running"

    @pytest.mark.asyncio
    async def test_handles_string_status(
        self, status_manager, mock_db_service, sample_installation
    ):
        """Should handle string status value."""
        sample_installation.status = "stopped"
        mock_db_service.get_all_installations.return_value = [sample_installation]

        result = await status_manager.get_all_installations_with_details()

        assert result[0]["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_handles_null_config(
        self, status_manager, mock_db_service, sample_installation
    ):
        """Should handle null config gracefully."""
        sample_installation.config = None
        mock_db_service.get_all_installations.return_value = [sample_installation]

        result = await status_manager.get_all_installations_with_details()

        assert result[0]["ports"] == {}
        assert result[0]["env"] == {}
        assert result[0]["volumes"] == {}

    @pytest.mark.asyncio
    async def test_handles_multiple_installations(
        self,
        status_manager,
        mock_db_service,
        mock_server_service,
        mock_marketplace_service,
    ):
        """Should handle multiple installations efficiently."""
        inst1 = MagicMock()
        inst1.id = "inst-1"
        inst1.app_id = "app-1"
        inst1.server_id = "server-1"
        inst1.container_name = "container-1"
        inst1.container_id = "id-1"
        inst1.status = "running"
        inst1.installed_at = "2024-01-01T00:00:00Z"
        inst1.started_at = None
        inst1.error_message = None
        inst1.config = {}
        inst1.networks = []
        inst1.named_volumes = []
        inst1.bind_mounts = []

        inst2 = MagicMock()
        inst2.id = "inst-2"
        inst2.app_id = "app-2"
        inst2.server_id = "server-2"
        inst2.container_name = "container-2"
        inst2.container_id = "id-2"
        inst2.status = "stopped"
        inst2.installed_at = "2024-01-02T00:00:00Z"
        inst2.started_at = None
        inst2.error_message = None
        inst2.config = {}
        inst2.networks = []
        inst2.named_volumes = []
        inst2.bind_mounts = []

        mock_db_service.get_all_installations.return_value = [inst1, inst2]

        # Mock different servers and apps
        mock_server_service.get_server = AsyncMock(
            side_effect=[
                MagicMock(id="server-1", name="Server 1", host="192.168.1.1"),
                MagicMock(id="server-2", name="Server 2", host="192.168.1.2"),
            ]
        )

        app1 = MagicMock(
            id="app-1",
            name="App 1",
            version="1.0",
            description="Desc 1",
            icon="icon1",
            category="Cat1",
            repo_id="repo-1",
        )
        app2 = MagicMock(
            id="app-2",
            name="App 2",
            version="2.0",
            description="Desc 2",
            icon="icon2",
            category="Cat2",
            repo_id="repo-1",
        )
        mock_marketplace_service.get_app = AsyncMock(side_effect=[app1, app2])

        result = await status_manager.get_all_installations_with_details()

        assert len(result) == 2
        assert result[0]["id"] == "inst-1"
        assert result[1]["id"] == "inst-2"

    @pytest.mark.asyncio
    async def test_handles_exception(self, status_manager, mock_db_service):
        """Should return empty list on exception."""
        mock_db_service.get_all_installations.side_effect = Exception("DB error")

        with patch("services.deployment.status.logger") as mock_logger:
            result = await status_manager.get_all_installations_with_details()

        assert result == []
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_includes_networks(
        self, status_manager, mock_db_service, sample_installation
    ):
        """Should include networks in result."""
        sample_installation.networks = ["bridge", "custom-network"]
        mock_db_service.get_all_installations.return_value = [sample_installation]

        result = await status_manager.get_all_installations_with_details()

        assert result[0]["networks"] == ["bridge", "custom-network"]

    @pytest.mark.asyncio
    async def test_includes_volumes(
        self, status_manager, mock_db_service, sample_installation
    ):
        """Should include named_volumes and bind_mounts in result."""
        sample_installation.named_volumes = [{"name": "vol1", "dest": "/data"}]
        sample_installation.bind_mounts = [{"source": "/host", "dest": "/container"}]
        mock_db_service.get_all_installations.return_value = [sample_installation]

        result = await status_manager.get_all_installations_with_details()

        assert result[0]["named_volumes"] == [{"name": "vol1", "dest": "/data"}]
        assert result[0]["bind_mounts"] == [{"source": "/host", "dest": "/container"}]

    @pytest.mark.asyncio
    async def test_includes_timestamps(
        self, status_manager, mock_db_service, sample_installation
    ):
        """Should include installed_at and started_at."""
        mock_db_service.get_all_installations.return_value = [sample_installation]

        result = await status_manager.get_all_installations_with_details()

        assert result[0]["installed_at"] == "2024-01-01T00:00:00Z"
        assert result[0]["started_at"] == "2024-01-01T00:01:00Z"

    @pytest.mark.asyncio
    async def test_includes_error_message(
        self, status_manager, mock_db_service, sample_installation
    ):
        """Should include error_message in result."""
        sample_installation.error_message = "Failed to start"
        mock_db_service.get_all_installations.return_value = [sample_installation]

        result = await status_manager.get_all_installations_with_details()

        assert result[0]["error_message"] == "Failed to start"

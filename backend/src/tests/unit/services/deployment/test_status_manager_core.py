"""
Unit tests for services/deployment/status.py - Core functionality

Tests for StatusManager initialization, get_app_status, get_installed_apps,
and get_installation_status_by_id methods.
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
    service.get_installation = AsyncMock(return_value=None)
    service.get_installations = AsyncMock(return_value=[])
    service.get_installation_by_id = AsyncMock(return_value=None)
    service.get_all_installations = AsyncMock(return_value=[])
    service.update_installation = AsyncMock()
    return service


@pytest.fixture
def mock_server_service():
    """Create mock server service."""
    service = MagicMock()
    service.get_server = AsyncMock(
        return_value=MagicMock(id="server-1", name="Test Server", host="192.168.1.100")
    )
    return service


@pytest.fixture
def mock_marketplace_service():
    """Create mock marketplace service."""
    service = MagicMock()
    service.get_app = AsyncMock(
        return_value=MagicMock(
            id="app-1",
            name="Test App",
            version="1.0.0",
            description="A test app",
            icon="test-icon",
            category="Utilities",
            repo_id="repo-1",
        )
    )
    service.get_repo = AsyncMock(return_value=MagicMock(id="repo-1", name="Test Repo"))
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
    inst.config = {"ports": {"8080": 8080}}
    inst.networks = ["bridge"]
    inst.named_volumes = []
    inst.bind_mounts = []
    inst.step_durations = {}
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


class TestStatusManagerInit:
    """Tests for StatusManager initialization."""

    def test_init_sets_ssh_executor(
        self,
        mock_ssh_executor,
        mock_db_service,
        mock_server_service,
        mock_marketplace_service,
    ):
        """StatusManager should store ssh executor."""
        from services.deployment.status import StatusManager

        manager = StatusManager(
            mock_ssh_executor,
            mock_db_service,
            mock_server_service,
            mock_marketplace_service,
        )
        assert manager.ssh == mock_ssh_executor

    def test_init_sets_db_service(
        self,
        mock_ssh_executor,
        mock_db_service,
        mock_server_service,
        mock_marketplace_service,
    ):
        """StatusManager should store db service."""
        from services.deployment.status import StatusManager

        manager = StatusManager(
            mock_ssh_executor,
            mock_db_service,
            mock_server_service,
            mock_marketplace_service,
        )
        assert manager.db_service == mock_db_service

    def test_init_sets_server_service(
        self,
        mock_ssh_executor,
        mock_db_service,
        mock_server_service,
        mock_marketplace_service,
    ):
        """StatusManager should store server service."""
        from services.deployment.status import StatusManager

        manager = StatusManager(
            mock_ssh_executor,
            mock_db_service,
            mock_server_service,
            mock_marketplace_service,
        )
        assert manager.server_service == mock_server_service

    def test_init_sets_marketplace_service(
        self,
        mock_ssh_executor,
        mock_db_service,
        mock_server_service,
        mock_marketplace_service,
    ):
        """StatusManager should store marketplace service."""
        from services.deployment.status import StatusManager

        manager = StatusManager(
            mock_ssh_executor,
            mock_db_service,
            mock_server_service,
            mock_marketplace_service,
        )
        assert manager.marketplace_service == mock_marketplace_service


class TestGetAppStatus:
    """Tests for get_app_status method."""

    @pytest.mark.asyncio
    async def test_get_app_status_returns_none_when_not_found(
        self, status_manager, mock_db_service
    ):
        """get_app_status should return None when installation not found."""
        mock_db_service.get_installation.return_value = None
        result = await status_manager.get_app_status("server-1", "app-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_app_status_returns_status_dict(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """get_app_status should return status dict when found."""
        mock_db_service.get_installation.return_value = sample_installation
        mock_ssh_executor.execute.return_value = (0, "running", "")

        result = await status_manager.get_app_status("server-1", "app-1")

        assert result is not None
        assert result["installation_id"] == "inst-123"
        assert result["app_id"] == "app-1"
        assert result["container_name"] == "test-container"
        assert result["status"] == "running"

    @pytest.mark.asyncio
    async def test_get_app_status_returns_unknown_on_ssh_failure(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """get_app_status should return unknown status on SSH failure."""
        mock_db_service.get_installation.return_value = sample_installation
        mock_ssh_executor.execute.return_value = (1, "", "error")

        result = await status_manager.get_app_status("server-1", "app-1")

        assert result is not None
        assert result["status"] == "unknown"

    @pytest.mark.asyncio
    async def test_get_app_status_queries_correct_container(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """get_app_status should query the correct container."""
        mock_db_service.get_installation.return_value = sample_installation
        mock_ssh_executor.execute.return_value = (0, "running", "")

        await status_manager.get_app_status("server-1", "app-1")

        mock_ssh_executor.execute.assert_called_once()
        call_args = mock_ssh_executor.execute.call_args
        assert "test-container" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_app_status_handles_exception(
        self, status_manager, mock_db_service
    ):
        """get_app_status should return None on exception."""
        mock_db_service.get_installation.side_effect = Exception("DB error")

        with patch("services.deployment.status.logger") as mock_logger:
            result = await status_manager.get_app_status("server-1", "app-1")

        assert result is None
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_app_status_strips_stdout(
        self, status_manager, mock_db_service, mock_ssh_executor, sample_installation
    ):
        """get_app_status should strip whitespace from stdout."""
        mock_db_service.get_installation.return_value = sample_installation
        mock_ssh_executor.execute.return_value = (0, "  running  \n", "")

        result = await status_manager.get_app_status("server-1", "app-1")

        assert result["status"] == "running"


class TestGetInstalledApps:
    """Tests for get_installed_apps method."""

    @pytest.mark.asyncio
    async def test_get_installed_apps_returns_empty_list(
        self, status_manager, mock_db_service
    ):
        """get_installed_apps should return empty list when no installations."""
        mock_db_service.get_installations.return_value = []

        result = await status_manager.get_installed_apps("server-1")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_installed_apps_returns_list_of_dicts(
        self, status_manager, mock_db_service, sample_installation
    ):
        """get_installed_apps should return list of installation dicts."""
        mock_db_service.get_installations.return_value = [sample_installation]

        result = await status_manager.get_installed_apps("server-1")

        assert len(result) == 1
        assert result[0]["installation_id"] == "inst-123"
        assert result[0]["app_id"] == "app-1"
        assert result[0]["container_name"] == "test-container"
        assert result[0]["status"] == "running"

    @pytest.mark.asyncio
    async def test_get_installed_apps_handles_multiple_installations(
        self, status_manager, mock_db_service
    ):
        """get_installed_apps should handle multiple installations."""
        inst1 = MagicMock()
        inst1.id = "inst-1"
        inst1.app_id = "app-1"
        inst1.container_name = "container-1"
        inst1.status = "running"
        inst1.installed_at = "2024-01-01T00:00:00Z"

        inst2 = MagicMock()
        inst2.id = "inst-2"
        inst2.app_id = "app-2"
        inst2.container_name = "container-2"
        inst2.status = "stopped"
        inst2.installed_at = "2024-01-02T00:00:00Z"

        mock_db_service.get_installations.return_value = [inst1, inst2]

        result = await status_manager.get_installed_apps("server-1")

        assert len(result) == 2
        assert result[0]["app_id"] == "app-1"
        assert result[1]["app_id"] == "app-2"

    @pytest.mark.asyncio
    async def test_get_installed_apps_handles_exception(
        self, status_manager, mock_db_service
    ):
        """get_installed_apps should return empty list on exception."""
        mock_db_service.get_installations.side_effect = Exception("DB error")

        with patch("services.deployment.status.logger") as mock_logger:
            result = await status_manager.get_installed_apps("server-1")

        assert result == []
        mock_logger.error.assert_called_once()


class TestGetInstallationStatusById:
    """Tests for get_installation_status_by_id method."""

    @pytest.mark.asyncio
    async def test_get_installation_status_by_id_returns_none_when_not_found(
        self, status_manager, mock_db_service
    ):
        """get_installation_status_by_id should return None when not found."""
        mock_db_service.get_installation_by_id.return_value = None

        result = await status_manager.get_installation_status_by_id("inst-123")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_installation_status_by_id_returns_status_dict(
        self, status_manager, mock_db_service, sample_installation
    ):
        """get_installation_status_by_id should return status dict."""
        mock_db_service.get_installation_by_id.return_value = sample_installation

        result = await status_manager.get_installation_status_by_id("inst-123")

        assert result is not None
        assert result["id"] == "inst-123"
        assert result["app_id"] == "app-1"
        assert result["server_id"] == "server-1"
        assert result["container_id"] == "abc123def456"
        assert result["container_name"] == "test-container"

    @pytest.mark.asyncio
    async def test_get_installation_status_by_id_handles_enum_status(
        self, status_manager, mock_db_service, sample_installation
    ):
        """get_installation_status_by_id should handle enum status."""
        sample_installation.status = MagicMock()
        sample_installation.status.value = "running"
        mock_db_service.get_installation_by_id.return_value = sample_installation

        result = await status_manager.get_installation_status_by_id("inst-123")

        assert result["status"] == "running"

    @pytest.mark.asyncio
    async def test_get_installation_status_by_id_handles_string_status(
        self, status_manager, mock_db_service, sample_installation
    ):
        """get_installation_status_by_id should handle string status."""
        sample_installation.status = "stopped"
        mock_db_service.get_installation_by_id.return_value = sample_installation

        result = await status_manager.get_installation_status_by_id("inst-123")

        assert result["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_get_installation_status_by_id_includes_progress(
        self, status_manager, mock_db_service, sample_installation
    ):
        """get_installation_status_by_id should include progress."""
        sample_installation.progress = 75
        mock_db_service.get_installation_by_id.return_value = sample_installation

        result = await status_manager.get_installation_status_by_id("inst-123")

        assert result["progress"] == 75

    @pytest.mark.asyncio
    async def test_get_installation_status_by_id_defaults_progress_to_zero(
        self, status_manager, mock_db_service, sample_installation
    ):
        """get_installation_status_by_id should default progress to 0."""
        # Remove progress attribute
        delattr(sample_installation, "progress") if hasattr(
            sample_installation, "progress"
        ) else None
        mock_db_service.get_installation_by_id.return_value = sample_installation

        result = await status_manager.get_installation_status_by_id("inst-123")

        assert result["progress"] == 0

    @pytest.mark.asyncio
    async def test_get_installation_status_by_id_handles_exception(
        self, status_manager, mock_db_service
    ):
        """get_installation_status_by_id should return None on exception."""
        mock_db_service.get_installation_by_id.side_effect = Exception("DB error")

        with patch("services.deployment.status.logger") as mock_logger:
            result = await status_manager.get_installation_status_by_id("inst-123")

        assert result is None
        mock_logger.error.assert_called_once()

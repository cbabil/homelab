"""Tests for deployment service."""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from services.deployment_service import DeploymentService
from models.app_catalog import InstallationStatus
from models.marketplace import (
    MarketplaceApp, DockerConfig, AppPort, AppVolume, AppEnvVar, AppRequirements
)


def _make_mock_app(app_id="testapp", image="test:latest", ports=None, volumes=None):
    """Create a mock MarketplaceApp."""
    return MarketplaceApp(
        id=app_id,
        name="Test App",
        description="Test",
        version="1.0.0",
        category="utility",
        tags=["test"],
        author="Test",
        license="MIT",
        repo_id="official",
        docker=DockerConfig(
            image=image,
            ports=ports or [AppPort(container=80, host=8080)],
            volumes=volumes or [],
            environment=[],
            restart_policy="unless-stopped",
            privileged=False,
            capabilities=[]
        ),
        requirements=AppRequirements(architectures=["amd64"]),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


class TestDeploymentService:
    """Tests for DeploymentService."""

    @pytest.fixture
    def mock_ssh_service(self):
        """Create mock SSH service."""
        ssh = MagicMock()
        ssh.execute_command = AsyncMock(return_value=(0, "success", ""))
        return ssh

    @pytest.fixture
    def mock_server_service(self):
        """Create mock server service."""
        svc = MagicMock()
        svc.get_server = AsyncMock(return_value=MagicMock(id="server-123", host="192.168.1.100"))
        svc.get_credentials = AsyncMock(return_value={"username": "admin", "password": "pass"})
        return svc

    @pytest.fixture
    def mock_marketplace_service(self):
        """Create mock marketplace service."""
        svc = MagicMock()
        svc.get_app = AsyncMock(return_value=_make_mock_app())
        return svc

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = MagicMock()
        db.create_installation = AsyncMock()
        db.update_installation = AsyncMock()
        db.get_installation = AsyncMock()
        db.get_installations = AsyncMock(return_value=[])
        db.delete_installation = AsyncMock()
        return db

    @pytest.fixture
    def deployment_service(self, mock_ssh_service, mock_server_service, mock_marketplace_service, mock_db_service):
        """Create deployment service with mocks."""
        return DeploymentService(
            ssh_service=mock_ssh_service,
            server_service=mock_server_service,
            marketplace_service=mock_marketplace_service,
            db_service=mock_db_service
        )

    def test_build_docker_run_command(self, deployment_service):
        """Should build correct docker run command."""
        docker_config = DockerConfig(
            image="myapp:latest",
            ports=[AppPort(container=80, host=8080)],
            volumes=[AppVolume(host_path="/data", container_path="/app/data")],
            environment=[],
            restart_policy="unless-stopped",
            privileged=False,
            capabilities=[]
        )
        config = {"env": {"MY_VAR": "value"}}

        cmd = deployment_service._build_docker_run_command(docker_config, "myapp-container", config)

        assert "docker run" in cmd
        assert "-p 8080:80" in cmd
        assert "-v /data:/app/data" in cmd
        assert "myapp:latest" in cmd
        assert "--name myapp-container" in cmd

    def test_build_docker_run_with_env(self, deployment_service):
        """Should include environment variables."""
        docker_config = DockerConfig(
            image="myapp:latest",
            ports=[],
            volumes=[],
            environment=[],
            restart_policy="unless-stopped",
            privileged=False,
            capabilities=[]
        )
        config = {"env": {"DB_HOST": "localhost", "DB_PORT": "5432"}}

        cmd = deployment_service._build_docker_run_command(docker_config, "myapp", config)

        assert "-e DB_HOST=localhost" in cmd
        assert "-e DB_PORT=5432" in cmd

    @pytest.mark.asyncio
    async def test_install_app_creates_record(self, deployment_service, mock_db_service):
        """Should create installation record."""
        mock_db_service.create_installation.return_value = MagicMock(id="inst-123")

        result = await deployment_service.install_app(
            server_id="server-123",
            app_id="testapp",
            config={}
        )

        assert result is not None
        mock_db_service.create_installation.assert_called_once()

    @pytest.mark.asyncio
    async def test_uninstall_app(self, deployment_service, mock_ssh_service, mock_db_service):
        """Should stop and remove container."""
        mock_db_service.get_installation.return_value = MagicMock(
            container_name="testapp-container",
            status=InstallationStatus.RUNNING
        )

        result = await deployment_service.uninstall_app(
            server_id="server-123",
            app_id="testapp",
            remove_data=False
        )

        assert result is True
        assert mock_ssh_service.execute_command.call_count >= 2  # stop + rm

    @pytest.mark.asyncio
    async def test_get_app_status(self, deployment_service, mock_ssh_service, mock_db_service):
        """Should get container status."""
        mock_db_service.get_installation.return_value = MagicMock(
            container_name="testapp-container"
        )
        mock_ssh_service.execute_command.return_value = (0, "running", "")

        status = await deployment_service.get_app_status("server-123", "testapp")

        assert status is not None

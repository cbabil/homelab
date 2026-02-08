"""
Deployment Service Unit Tests

Tests for the deployment service module.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from services.deployment import DeploymentService
from services.deployment.docker_commands import build_run_command, parse_pull_progress
from services.deployment.scripts import (
    cleanup_container_script,
    create_container_script,
    uninstall_script,
)


class TestDockerCommands:
    """Tests for docker command builders."""

    def test_build_run_command_basic(self):
        """Test building a basic docker run command."""
        docker_config = MagicMock()
        docker_config.image = "nginx:latest"
        docker_config.restart_policy = "unless-stopped"
        docker_config.ports = []
        docker_config.volumes = []
        docker_config.network_mode = None
        docker_config.privileged = False
        docker_config.capabilities = []

        cmd = build_run_command(docker_config, "test-container", {})

        assert "docker run -d" in cmd
        assert "--name test-container" in cmd
        assert "--restart unless-stopped" in cmd
        assert "nginx:latest" in cmd

    def test_build_run_command_with_ports(self):
        """Test docker run command with port mappings."""
        docker_config = MagicMock()
        docker_config.image = "nginx:latest"
        docker_config.restart_policy = "always"
        docker_config.ports = [
            MagicMock(container=80, host=8080, protocol="tcp"),
            MagicMock(container=443, host=8443, protocol="tcp"),
        ]
        docker_config.volumes = []
        docker_config.network_mode = None
        docker_config.privileged = False
        docker_config.capabilities = []

        cmd = build_run_command(docker_config, "web", {})

        assert "-p 8080:80/tcp" in cmd
        assert "-p 8443:443/tcp" in cmd

    def test_build_run_command_with_config_overrides(self):
        """Test docker run command with user config overrides."""
        docker_config = MagicMock()
        docker_config.image = "nginx:latest"
        docker_config.restart_policy = "always"
        docker_config.ports = [MagicMock(container=80, host=8080, protocol="tcp")]
        docker_config.volumes = []
        docker_config.network_mode = None
        docker_config.privileged = False
        docker_config.capabilities = []

        config = {"ports": {"80": 9000}}  # Override port 80 -> 9000
        cmd = build_run_command(docker_config, "web", config)

        assert "-p 9000:80/tcp" in cmd

    def test_parse_pull_progress_downloading(self):
        """Test parsing docker pull downloading progress."""
        layer_progress = {}

        _progress = parse_pull_progress(
            "abc123: Downloading [====>    ] 10MB/100MB", layer_progress
        )

        assert "abc123" in layer_progress
        assert layer_progress["abc123"] == 10

    def test_parse_pull_progress_complete(self):
        """Test parsing docker pull complete status."""
        layer_progress = {"abc123": 50}

        _progress = parse_pull_progress("abc123: Pull complete", layer_progress)

        assert layer_progress["abc123"] == 100


class TestScripts:
    """Tests for batched shell scripts."""

    def test_cleanup_container_script(self):
        """Test cleanup container script generation."""
        script = cleanup_container_script("my-container")

        assert "docker stop my-container" in script
        assert "docker rm -v my-container" in script
        assert "CLEANUP_DONE" in script

    def test_cleanup_container_script_with_image(self):
        """Test cleanup script includes image removal."""
        script = cleanup_container_script("my-container", "nginx:latest")

        assert "docker rmi nginx:latest" in script

    def test_create_container_script(self):
        """Test create container script generation."""
        run_cmd = "docker run -d --name test nginx:latest"
        script = create_container_script(run_cmd)

        assert "docker image prune -f" in script
        assert run_cmd in script
        assert "SUCCESS:" in script
        assert "FAILED:" in script

    def test_uninstall_script(self):
        """Test uninstall script generation."""
        script = uninstall_script("my-app")

        assert "docker stop my-app" in script
        assert "docker rm my-app" in script
        assert "CLEANUP_COMPLETE" in script
        # Should include volume cleanup by default
        assert "docker volume rm" in script

    def test_uninstall_script_without_data(self):
        """Test uninstall script without data removal."""
        script = uninstall_script("my-app", remove_data=False)

        assert "docker stop my-app" in script
        # Should NOT include volume removal
        assert "for VOL in" not in script


class TestDeploymentService:
    """Tests for the deployment service."""

    @pytest.fixture
    def deployment_service(
        self,
        mock_ssh_service,
        mock_server_service,
        mock_marketplace_service,
        mock_db_service,
        mock_agent_manager,
        mock_agent_service,
    ):
        """Create deployment service with mocked dependencies."""
        return DeploymentService(
            ssh_service=mock_ssh_service,
            server_service=mock_server_service,
            marketplace_service=mock_marketplace_service,
            db_service=mock_db_service,
            activity_service=None,
            agent_manager=mock_agent_manager,
            agent_service=mock_agent_service,
        )

    @pytest.mark.asyncio
    async def test_start_app_success(self, deployment_service, mock_db_service):
        """Test starting an app successfully."""
        mock_db_service.get_installation = AsyncMock(
            return_value=MagicMock(id="inst-1", container_name="test-container")
        )

        result = await deployment_service.start_app("server-1", "app-1")

        assert result is True
        mock_db_service.update_installation.assert_called()

    @pytest.mark.asyncio
    async def test_start_app_not_found(self, deployment_service, mock_db_service):
        """Test starting an app that doesn't exist."""
        mock_db_service.get_installation = AsyncMock(return_value=None)

        result = await deployment_service.start_app("server-1", "app-1")

        assert result is False

    @pytest.mark.asyncio
    async def test_stop_app_success(self, deployment_service, mock_db_service):
        """Test stopping an app successfully."""
        mock_db_service.get_installation = AsyncMock(
            return_value=MagicMock(id="inst-1", container_name="test-container")
        )

        result = await deployment_service.stop_app("server-1", "app-1")

        assert result is True
        mock_db_service.update_installation.assert_called()

"""
Unit tests for services/deployment/service.py - Initialization

Tests for DeploymentService initialization and helper methods.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_services():
    """Create mock services for DeploymentService."""
    return {
        "ssh": MagicMock(),
        "server": MagicMock(),
        "marketplace": MagicMock(),
        "db": MagicMock(),
        "activity": MagicMock(),
        "agent_manager": MagicMock(),
        "agent_service": MagicMock(),
    }


class TestDeploymentServiceInit:
    """Tests for DeploymentService initialization."""

    def test_initializes_with_required_services(self, mock_services):
        """Should initialize with required services."""
        from services.deployment.service import DeploymentService

        with patch("services.deployment.service.logger"):
            service = DeploymentService(
                ssh_service=mock_services["ssh"],
                server_service=mock_services["server"],
                marketplace_service=mock_services["marketplace"],
                db_service=mock_services["db"],
            )

        assert service.ssh_service is mock_services["ssh"]
        assert service.server_service is mock_services["server"]
        assert service.marketplace_service is mock_services["marketplace"]
        assert service.db_service is mock_services["db"]

    def test_initializes_with_optional_services(self, mock_services):
        """Should initialize with optional services."""
        from services.deployment.service import DeploymentService

        with patch("services.deployment.service.logger"):
            service = DeploymentService(
                ssh_service=mock_services["ssh"],
                server_service=mock_services["server"],
                marketplace_service=mock_services["marketplace"],
                db_service=mock_services["db"],
                activity_service=mock_services["activity"],
                agent_manager=mock_services["agent_manager"],
                agent_service=mock_services["agent_service"],
            )

        assert service.activity_service is mock_services["activity"]
        assert service.agent_manager is mock_services["agent_manager"]
        assert service.agent_service is mock_services["agent_service"]

    def test_creates_default_ssh_executor(self, mock_services):
        """Should create SSHExecutor when no executor provided."""
        from services.deployment.service import DeploymentService

        with patch("services.deployment.service.logger"):
            service = DeploymentService(
                ssh_service=mock_services["ssh"],
                server_service=mock_services["server"],
                marketplace_service=mock_services["marketplace"],
                db_service=mock_services["db"],
            )

        assert service.ssh is not None

    def test_uses_provided_executor(self, mock_services):
        """Should use provided executor instead of default."""
        from services.deployment.service import DeploymentService

        custom_executor = MagicMock()

        with patch("services.deployment.service.logger"):
            service = DeploymentService(
                ssh_service=mock_services["ssh"],
                server_service=mock_services["server"],
                marketplace_service=mock_services["marketplace"],
                db_service=mock_services["db"],
                executor=custom_executor,
            )

        assert service.ssh is custom_executor

    def test_creates_validator(self, mock_services):
        """Should create DeploymentValidator."""
        from services.deployment.service import DeploymentService

        with patch("services.deployment.service.logger"):
            service = DeploymentService(
                ssh_service=mock_services["ssh"],
                server_service=mock_services["server"],
                marketplace_service=mock_services["marketplace"],
                db_service=mock_services["db"],
            )

        assert service.validator is not None

    def test_creates_status_manager(self, mock_services):
        """Should create StatusManager."""
        from services.deployment.service import DeploymentService

        with patch("services.deployment.service.logger"):
            service = DeploymentService(
                ssh_service=mock_services["ssh"],
                server_service=mock_services["server"],
                marketplace_service=mock_services["marketplace"],
                db_service=mock_services["db"],
            )

        assert service.status_manager is not None


class TestGetAgentForServer:
    """Tests for _get_agent_for_server helper method."""

    @pytest.fixture
    def deployment_service(self, mock_services):
        """Create DeploymentService instance."""
        from services.deployment.service import DeploymentService

        with patch("services.deployment.service.logger"):
            return DeploymentService(
                ssh_service=mock_services["ssh"],
                server_service=mock_services["server"],
                marketplace_service=mock_services["marketplace"],
                db_service=mock_services["db"],
                agent_manager=mock_services["agent_manager"],
                agent_service=mock_services["agent_service"],
            )

    @pytest.mark.asyncio
    async def test_returns_none_when_no_agent_service(self, mock_services):
        """Should return None when agent_service is None."""
        from services.deployment.service import DeploymentService

        with patch("services.deployment.service.logger"):
            service = DeploymentService(
                ssh_service=mock_services["ssh"],
                server_service=mock_services["server"],
                marketplace_service=mock_services["marketplace"],
                db_service=mock_services["db"],
            )

        result = await service._get_agent_for_server("server-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_agent_manager(self, mock_services):
        """Should return None when agent_manager is None."""
        from services.deployment.service import DeploymentService

        with patch("services.deployment.service.logger"):
            service = DeploymentService(
                ssh_service=mock_services["ssh"],
                server_service=mock_services["server"],
                marketplace_service=mock_services["marketplace"],
                db_service=mock_services["db"],
                agent_service=mock_services["agent_service"],
            )

        result = await service._get_agent_for_server("server-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_agent_not_found(
        self, deployment_service, mock_services
    ):
        """Should return None when agent not found for server."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=None
        )

        result = await deployment_service._get_agent_for_server("server-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_agent_not_connected(
        self, deployment_service, mock_services
    ):
        """Should return None when agent exists but not connected."""
        agent = MagicMock()
        agent.id = "agent-123"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = False

        result = await deployment_service._get_agent_for_server("server-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_agent_when_connected(
        self, deployment_service, mock_services
    ):
        """Should return agent when found and connected."""
        agent = MagicMock()
        agent.id = "agent-123"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True

        result = await deployment_service._get_agent_for_server("server-1")
        assert result is agent


class TestBuildContainerParams:
    """Tests for _build_container_params helper method."""

    @pytest.fixture
    def deployment_service(self, mock_services):
        """Create DeploymentService instance."""
        from services.deployment.service import DeploymentService

        with patch("services.deployment.service.logger"):
            return DeploymentService(
                ssh_service=mock_services["ssh"],
                server_service=mock_services["server"],
                marketplace_service=mock_services["marketplace"],
                db_service=mock_services["db"],
            )

    @pytest.fixture
    def mock_docker_config(self):
        """Create mock Docker config."""
        config = MagicMock()
        config.image = "nginx:latest"
        config.restart_policy = "unless-stopped"
        config.network_mode = "bridge"
        config.privileged = False
        config.capabilities = []

        # Port mapping
        port = MagicMock()
        port.container = 80
        port.host = 8080
        port.protocol = "tcp"
        config.ports = [port]

        # Volume mapping
        volume = MagicMock()
        volume.host_path = "/data/nginx"
        volume.container_path = "/usr/share/nginx/html"
        volume.readonly = False
        config.volumes = [volume]

        return config

    def test_builds_basic_params(self, deployment_service, mock_docker_config):
        """Should build basic container parameters."""
        result = deployment_service._build_container_params(
            mock_docker_config, "test-container", {}
        )

        assert result["image"] == "nginx:latest"
        assert result["name"] == "test-container"
        assert result["network_mode"] == "bridge"
        assert result["privileged"] is False

    def test_builds_port_mappings(self, deployment_service, mock_docker_config):
        """Should build port mappings."""
        result = deployment_service._build_container_params(
            mock_docker_config, "test-container", {}
        )

        assert "8080" in result["ports"]
        assert result["ports"]["8080"] == "80/tcp"

    def test_allows_port_override(self, deployment_service, mock_docker_config):
        """Should allow port override from user config."""
        user_config = {"ports": {"80": 9090}}

        result = deployment_service._build_container_params(
            mock_docker_config, "test-container", user_config
        )

        assert "9090" in result["ports"]

    def test_builds_volume_mappings(self, deployment_service, mock_docker_config):
        """Should build volume mappings."""
        result = deployment_service._build_container_params(
            mock_docker_config, "test-container", {}
        )

        assert len(result["volumes"]) == 1
        assert result["volumes"][0]["host"] == "/data/nginx"
        assert result["volumes"][0]["container"] == "/usr/share/nginx/html"
        assert result["volumes"][0]["mode"] == "rw"

    def test_readonly_volume(self, deployment_service, mock_docker_config):
        """Should set readonly mode for readonly volumes."""
        mock_docker_config.volumes[0].readonly = True

        result = deployment_service._build_container_params(
            mock_docker_config, "test-container", {}
        )

        assert result["volumes"][0]["mode"] == "ro"

    def test_uses_restart_policy_override(self, deployment_service, mock_docker_config):
        """Should use restart policy override when provided."""
        result = deployment_service._build_container_params(
            mock_docker_config, "test-container", {}, restart_policy="no"
        )

        assert result["restart_policy"] == "no"

    def test_uses_default_restart_policy(self, deployment_service, mock_docker_config):
        """Should use config restart policy when no override."""
        result = deployment_service._build_container_params(
            mock_docker_config, "test-container", {}
        )

        assert result["restart_policy"] == "unless-stopped"

    def test_includes_env_from_user_config(
        self, deployment_service, mock_docker_config
    ):
        """Should include environment variables from user config."""
        user_config = {"env": {"DEBUG": "true", "PORT": "8080"}}

        result = deployment_service._build_container_params(
            mock_docker_config, "test-container", user_config
        )

        assert result["env"]["DEBUG"] == "true"
        assert result["env"]["PORT"] == "8080"


class TestParseAgentInspectResult:
    """Tests for _parse_agent_inspect_result helper method."""

    @pytest.fixture
    def deployment_service(self, mock_services):
        """Create DeploymentService instance."""
        from services.deployment.service import DeploymentService

        with patch("services.deployment.service.logger"):
            return DeploymentService(
                ssh_service=mock_services["ssh"],
                server_service=mock_services["server"],
                marketplace_service=mock_services["marketplace"],
                db_service=mock_services["db"],
            )

    def test_returns_empty_structure_for_empty_data(self, deployment_service):
        """Should return empty structure for empty data."""
        result = deployment_service._parse_agent_inspect_result({})

        assert result["networks"] == []
        assert result["named_volumes"] == []
        assert result["bind_mounts"] == []

    def test_parses_networks_from_network_settings(self, deployment_service):
        """Should parse networks from NetworkSettings."""
        data = {
            "NetworkSettings": {
                "Networks": {
                    "bridge": {},
                    "custom-net": {},
                }
            }
        }

        result = deployment_service._parse_agent_inspect_result(data)

        assert "bridge" in result["networks"]
        assert "custom-net" in result["networks"]

    def test_parses_networks_from_lowercase(self, deployment_service):
        """Should parse networks from lowercase key."""
        data = {"networks": {"mynet": {}}}

        result = deployment_service._parse_agent_inspect_result(data)

        assert "mynet" in result["networks"]

    def test_parses_named_volumes(self, deployment_service):
        """Should parse named volumes from Mounts."""
        data = {
            "Mounts": [
                {
                    "Type": "volume",
                    "Name": "app-data",
                    "Destination": "/data",
                    "Mode": "rw",
                }
            ]
        }

        result = deployment_service._parse_agent_inspect_result(data)

        assert len(result["named_volumes"]) == 1
        assert result["named_volumes"][0]["name"] == "app-data"
        assert result["named_volumes"][0]["destination"] == "/data"

    def test_parses_bind_mounts(self, deployment_service):
        """Should parse bind mounts from Mounts."""
        data = {
            "Mounts": [
                {
                    "Type": "bind",
                    "Source": "/host/path",
                    "Destination": "/container/path",
                    "Mode": "ro",
                }
            ]
        }

        result = deployment_service._parse_agent_inspect_result(data)

        assert len(result["bind_mounts"]) == 1
        assert result["bind_mounts"][0]["source"] == "/host/path"
        assert result["bind_mounts"][0]["destination"] == "/container/path"
        assert result["bind_mounts"][0]["mode"] == "ro"

    def test_parses_lowercase_mount_keys(self, deployment_service):
        """Should parse mounts with lowercase keys."""
        data = {
            "mounts": [
                {
                    "type": "volume",
                    "name": "vol-1",
                    "destination": "/vol",
                    "mode": "rw",
                }
            ]
        }

        result = deployment_service._parse_agent_inspect_result(data)

        assert len(result["named_volumes"]) == 1

    def test_handles_list_input(self, deployment_service):
        """Should handle list input (takes first element)."""
        data = [{"NetworkSettings": {"Networks": {"bridge": {}}}}]

        result = deployment_service._parse_agent_inspect_result(data)

        assert "bridge" in result["networks"]

    def test_handles_exception(self, deployment_service):
        """Should return empty structure on exception."""
        data = None  # Will cause exception

        result = deployment_service._parse_agent_inspect_result(data)

        assert result["networks"] == []
        assert result["named_volumes"] == []
        assert result["bind_mounts"] == []

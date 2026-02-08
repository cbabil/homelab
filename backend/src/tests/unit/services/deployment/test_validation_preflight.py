"""
Unit tests for DeploymentValidator.run_preflight_checks method.

Tests pre-flight validation before deployment.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.deployment.validation import DeploymentValidator


@pytest.fixture
def mock_ssh_executor():
    """Create mock SSH executor."""
    executor = MagicMock()
    executor.execute = AsyncMock(return_value=(0, "success", ""))
    return executor


@pytest.fixture
def mock_marketplace_service():
    """Create mock marketplace service."""
    service = MagicMock()
    service.get_app = AsyncMock(return_value=None)
    return service


@pytest.fixture
def mock_server_service():
    """Create mock server service."""
    service = MagicMock()
    service.get_server = AsyncMock(return_value=None)
    return service


@pytest.fixture
def validator(mock_ssh_executor, mock_marketplace_service, mock_server_service):
    """Create DeploymentValidator with mocked dependencies."""
    with patch("services.deployment.validation.logger"):
        return DeploymentValidator(
            ssh_executor=mock_ssh_executor,
            marketplace_service=mock_marketplace_service,
            server_service=mock_server_service,
        )


@pytest.fixture
def mock_app_with_requirements():
    """Create mock app with requirements."""
    app = MagicMock()
    app.docker = MagicMock()
    app.docker.environment = []

    port1 = MagicMock()
    port1.container = 80
    port1.host = 8080

    app.docker.ports = [port1]

    requirements = MagicMock()
    requirements.min_storage = 2048
    requirements.architectures = ["amd64", "arm64"]
    app.requirements = requirements
    return app


@pytest.fixture
def mock_app_no_requirements():
    """Create mock app without requirements."""
    app = MagicMock()
    app.docker = MagicMock()
    app.docker.environment = []
    app.docker.ports = []
    app.requirements = None
    return app


@pytest.fixture
def mock_server():
    """Create mock server object."""
    server = MagicMock()
    server.id = "server-1"
    server.name = "Test Server"
    server.host = "192.168.1.100"
    return server


class TestRunPreflightChecksBasic:
    """Tests for basic preflight check scenarios."""

    @pytest.mark.asyncio
    async def test_preflight_app_not_found(
        self, validator, mock_marketplace_service, mock_server_service, mock_server
    ):
        """run_preflight_checks should fail when app not found."""
        mock_marketplace_service.get_app.return_value = None
        mock_server_service.get_server.return_value = mock_server

        result = await validator.run_preflight_checks("server-1", "nonexistent")

        assert result["passed"] is False
        assert result["can_proceed"] is False
        assert any("not found" in c["message"] for c in result["checks"])

    @pytest.mark.asyncio
    async def test_preflight_server_not_found(
        self,
        validator,
        mock_marketplace_service,
        mock_server_service,
        mock_app_no_requirements,
    ):
        """run_preflight_checks should fail when server not found."""
        mock_marketplace_service.get_app.return_value = mock_app_no_requirements
        mock_server_service.get_server.return_value = None

        result = await validator.run_preflight_checks("nonexistent", "app-1")

        assert result["passed"] is False
        assert result["can_proceed"] is False

    @pytest.mark.asyncio
    async def test_preflight_exception_handling(
        self, validator, mock_marketplace_service
    ):
        """run_preflight_checks should handle exceptions gracefully."""
        mock_marketplace_service.get_app.side_effect = Exception("Service error")

        with patch("services.deployment.validation.logger"):
            result = await validator.run_preflight_checks("server-1", "app-1")

        assert result["passed"] is False
        assert result["can_proceed"] is False
        assert any("error" in c["name"] for c in result["checks"])

    @pytest.mark.asyncio
    async def test_preflight_with_empty_config(
        self,
        validator,
        mock_ssh_executor,
        mock_marketplace_service,
        mock_server_service,
        mock_app_no_requirements,
        mock_server,
    ):
        """run_preflight_checks should work with no config provided."""
        mock_marketplace_service.get_app.return_value = mock_app_no_requirements
        mock_server_service.get_server.return_value = mock_server
        mock_ssh_executor.execute.return_value = (0, "running", "")

        result = await validator.run_preflight_checks("server-1", "app-1")

        assert "checks" in result
        assert isinstance(result["checks"], list)

    @pytest.mark.asyncio
    async def test_preflight_all_checks_pass(
        self,
        validator,
        mock_ssh_executor,
        mock_marketplace_service,
        mock_server_service,
        mock_app_with_requirements,
        mock_server,
    ):
        """run_preflight_checks should pass when all checks succeed."""
        mock_marketplace_service.get_app.return_value = mock_app_with_requirements
        mock_server_service.get_server.return_value = mock_server

        # Docker running
        mock_ssh_executor.execute.side_effect = [
            (0, "running", ""),  # Docker check
            (0, "5000", ""),  # Disk space (5GB)
            (0, "available", ""),  # Port check
            (0, "x86_64", ""),  # Architecture
        ]

        result = await validator.run_preflight_checks("server-1", "app-1")

        assert result["passed"] is True
        assert result["can_proceed"] is True
        assert len(result["checks"]) == 4


class TestPreflightDockerCheck:
    """Tests for Docker running check."""

    @pytest.mark.asyncio
    async def test_docker_check_running(
        self,
        validator,
        mock_ssh_executor,
        mock_marketplace_service,
        mock_server_service,
        mock_app_no_requirements,
        mock_server,
    ):
        """_check_docker_running should pass when Docker is running."""
        mock_marketplace_service.get_app.return_value = mock_app_no_requirements
        mock_server_service.get_server.return_value = mock_server
        mock_ssh_executor.execute.side_effect = [
            (0, "running", ""),
            (0, "5000", ""),
            (0, "x86_64", ""),
        ]

        result = await validator.run_preflight_checks("server-1", "app-1")

        docker_check = next(
            c for c in result["checks"] if c["name"] == "docker_running"
        )
        assert docker_check["passed"] is True
        assert "running" in docker_check["message"].lower()

    @pytest.mark.asyncio
    async def test_docker_check_not_running(
        self,
        validator,
        mock_ssh_executor,
        mock_marketplace_service,
        mock_server_service,
        mock_app_no_requirements,
        mock_server,
    ):
        """_check_docker_running should fail when Docker is not running."""
        mock_marketplace_service.get_app.return_value = mock_app_no_requirements
        mock_server_service.get_server.return_value = mock_server
        mock_ssh_executor.execute.side_effect = [
            (1, "not running", ""),
            (0, "5000", ""),
            (0, "x86_64", ""),
        ]

        result = await validator.run_preflight_checks("server-1", "app-1")

        docker_check = next(
            c for c in result["checks"] if c["name"] == "docker_running"
        )
        assert docker_check["passed"] is False
        assert result["passed"] is False

    @pytest.mark.asyncio
    async def test_docker_check_exit_success_but_not_running(
        self,
        validator,
        mock_ssh_executor,
        mock_marketplace_service,
        mock_server_service,
        mock_app_no_requirements,
        mock_server,
    ):
        """_check_docker_running should fail when output doesn't contain running."""
        mock_marketplace_service.get_app.return_value = mock_app_no_requirements
        mock_server_service.get_server.return_value = mock_server
        mock_ssh_executor.execute.side_effect = [
            (0, "stopped", ""),
            (0, "5000", ""),
            (0, "x86_64", ""),
        ]

        result = await validator.run_preflight_checks("server-1", "app-1")

        docker_check = next(
            c for c in result["checks"] if c["name"] == "docker_running"
        )
        assert docker_check["passed"] is False


class TestPreflightDiskSpaceCheck:
    """Tests for disk space check."""

    @pytest.mark.asyncio
    async def test_disk_space_sufficient_with_min_storage(
        self,
        validator,
        mock_ssh_executor,
        mock_marketplace_service,
        mock_server_service,
        mock_app_with_requirements,
        mock_server,
    ):
        """_check_disk_space should pass when disk space exceeds min_storage."""
        mock_marketplace_service.get_app.return_value = mock_app_with_requirements
        mock_server_service.get_server.return_value = mock_server
        mock_ssh_executor.execute.side_effect = [
            (0, "running", ""),
            (0, "5000", ""),  # 5GB > 2GB required
            (0, "available", ""),
            (0, "x86_64", ""),
        ]

        result = await validator.run_preflight_checks("server-1", "app-1")

        disk_check = next(c for c in result["checks"] if c["name"] == "disk_space")
        assert disk_check["passed"] is True
        assert disk_check["available_mb"] == 5000

    @pytest.mark.asyncio
    async def test_disk_space_insufficient(
        self,
        validator,
        mock_ssh_executor,
        mock_marketplace_service,
        mock_server_service,
        mock_app_with_requirements,
        mock_server,
    ):
        """_check_disk_space should fail when disk space is insufficient."""
        mock_marketplace_service.get_app.return_value = mock_app_with_requirements
        mock_server_service.get_server.return_value = mock_server
        mock_ssh_executor.execute.side_effect = [
            (0, "running", ""),
            (0, "1000", ""),  # 1GB < 2GB required
            (0, "available", ""),
            (0, "x86_64", ""),
        ]

        result = await validator.run_preflight_checks("server-1", "app-1")

        disk_check = next(c for c in result["checks"] if c["name"] == "disk_space")
        assert disk_check["passed"] is False
        assert "Need" in disk_check["message"]

    @pytest.mark.asyncio
    async def test_disk_space_default_minimum(
        self,
        validator,
        mock_ssh_executor,
        mock_marketplace_service,
        mock_server_service,
        mock_app_no_requirements,
        mock_server,
    ):
        """_check_disk_space should use 1024MB default when no requirement."""
        mock_marketplace_service.get_app.return_value = mock_app_no_requirements
        mock_server_service.get_server.return_value = mock_server
        mock_ssh_executor.execute.side_effect = [
            (0, "running", ""),
            (0, "500", ""),  # 500MB < 1024MB default
            (0, "x86_64", ""),
        ]

        result = await validator.run_preflight_checks("server-1", "app-1")

        disk_check = next(c for c in result["checks"] if c["name"] == "disk_space")
        assert disk_check["passed"] is False
        assert disk_check["required_mb"] == 1024

    @pytest.mark.asyncio
    async def test_disk_space_check_command_fails(
        self,
        validator,
        mock_ssh_executor,
        mock_marketplace_service,
        mock_server_service,
        mock_app_no_requirements,
        mock_server,
    ):
        """_check_disk_space should fail when command fails."""
        mock_marketplace_service.get_app.return_value = mock_app_no_requirements
        mock_server_service.get_server.return_value = mock_server
        mock_ssh_executor.execute.side_effect = [
            (0, "running", ""),
            (1, "", "Error"),  # Command failed
            (0, "x86_64", ""),
        ]

        result = await validator.run_preflight_checks("server-1", "app-1")

        disk_check = next(c for c in result["checks"] if c["name"] == "disk_space")
        assert disk_check["passed"] is False
        assert "Could not check" in disk_check["message"]

    @pytest.mark.asyncio
    async def test_disk_space_parse_error(
        self,
        validator,
        mock_ssh_executor,
        mock_marketplace_service,
        mock_server_service,
        mock_app_no_requirements,
        mock_server,
    ):
        """_check_disk_space should fail when output cannot be parsed."""
        mock_marketplace_service.get_app.return_value = mock_app_no_requirements
        mock_server_service.get_server.return_value = mock_server
        mock_ssh_executor.execute.side_effect = [
            (0, "running", ""),
            (0, "not_a_number", ""),
            (0, "x86_64", ""),
        ]

        result = await validator.run_preflight_checks("server-1", "app-1")

        disk_check = next(c for c in result["checks"] if c["name"] == "disk_space")
        assert disk_check["passed"] is False
        assert "Could not parse" in disk_check["message"]


class TestPreflightPortCheck:
    """Tests for port availability check."""

    @pytest.mark.asyncio
    async def test_port_unavailable(
        self,
        validator,
        mock_ssh_executor,
        mock_marketplace_service,
        mock_server_service,
        mock_app_with_requirements,
        mock_server,
    ):
        """_check_ports_available should fail when port is in use."""
        mock_marketplace_service.get_app.return_value = mock_app_with_requirements
        mock_server_service.get_server.return_value = mock_server
        mock_ssh_executor.execute.side_effect = [
            (0, "running", ""),
            (0, "5000", ""),
            (0, "tcp   LISTEN 0  0.0.0.0:8080", ""),  # Port in use
            (0, "x86_64", ""),
        ]

        result = await validator.run_preflight_checks("server-1", "app-1")

        port_check = next(
            c for c in result["checks"] if c["name"] == "port_availability"
        )
        assert port_check["passed"] is False
        assert result["passed"] is False
        assert 8080 in port_check["unavailable_ports"]

    @pytest.mark.asyncio
    async def test_port_none_in_list(
        self,
        validator,
        mock_ssh_executor,
        mock_marketplace_service,
        mock_server_service,
        mock_server,
    ):
        """_check_ports_available should skip None ports."""
        app = MagicMock()
        app.docker = MagicMock()
        app.docker.environment = []

        port1 = MagicMock()
        port1.container = 80
        port1.host = None  # None port should be skipped

        port2 = MagicMock()
        port2.container = 443
        port2.host = 8443

        app.docker.ports = [port1, port2]
        app.requirements = None

        mock_marketplace_service.get_app.return_value = app
        mock_server_service.get_server.return_value = mock_server
        mock_ssh_executor.execute.side_effect = [
            (0, "running", ""),
            (0, "5000", ""),
            (0, "available", ""),  # Only one port check (8443)
            (0, "x86_64", ""),
        ]

        result = await validator.run_preflight_checks("server-1", "app-1")

        port_check = next(
            c for c in result["checks"] if c["name"] == "port_availability"
        )
        assert port_check["passed"] is True


class TestPreflightArchitectureCheck:
    """Tests for architecture check."""

    @pytest.mark.asyncio
    async def test_architecture_check_fails(
        self,
        validator,
        mock_ssh_executor,
        mock_marketplace_service,
        mock_server_service,
        mock_app_with_requirements,
        mock_server,
    ):
        """_check_architecture should fail when arch is not supported."""
        mock_marketplace_service.get_app.return_value = mock_app_with_requirements
        mock_server_service.get_server.return_value = mock_server
        mock_ssh_executor.execute.side_effect = [
            (0, "running", ""),
            (0, "5000", ""),
            (0, "available", ""),
            (0, "ppc64le", ""),  # Unsupported architecture
        ]

        result = await validator.run_preflight_checks("server-1", "app-1")

        arch_check = next(c for c in result["checks"] if c["name"] == "architecture")
        assert arch_check["passed"] is False
        assert result["passed"] is False

    @pytest.mark.asyncio
    async def test_architecture_check_command_fails(
        self,
        validator,
        mock_ssh_executor,
        mock_marketplace_service,
        mock_server_service,
        mock_app_with_requirements,
        mock_server,
    ):
        """_check_architecture should fail when uname command fails."""
        mock_marketplace_service.get_app.return_value = mock_app_with_requirements
        mock_server_service.get_server.return_value = mock_server
        mock_ssh_executor.execute.side_effect = [
            (0, "running", ""),
            (0, "5000", ""),
            (0, "available", ""),
            (1, "", "Error"),  # uname command fails
        ]

        result = await validator.run_preflight_checks("server-1", "app-1")

        arch_check = next(c for c in result["checks"] if c["name"] == "architecture")
        assert arch_check["passed"] is False
        assert "Could not determine" in arch_check["message"]

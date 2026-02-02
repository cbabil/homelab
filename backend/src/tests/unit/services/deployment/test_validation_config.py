"""
Unit tests for DeploymentValidator.validate_config method.

Tests configuration validation against app definitions.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

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
def mock_app_basic():
    """Create mock app with basic configuration."""
    app = MagicMock()
    app.docker = MagicMock()
    app.docker.environment = []
    app.docker.ports = []
    app.requirements = None
    return app


@pytest.fixture
def mock_app_with_env_vars():
    """Create mock app with required environment variables."""
    app = MagicMock()
    app.docker = MagicMock()
    
    required_env = MagicMock()
    required_env.name = "DATABASE_URL"
    required_env.required = True
    required_env.default = None
    
    optional_env = MagicMock()
    optional_env.name = "LOG_LEVEL"
    optional_env.required = False
    optional_env.default = "info"
    
    required_with_default = MagicMock()
    required_with_default.name = "PORT"
    required_with_default.required = True
    required_with_default.default = "8080"
    
    app.docker.environment = [required_env, optional_env, required_with_default]
    app.docker.ports = []
    app.requirements = None
    return app


@pytest.fixture
def mock_app_with_ports():
    """Create mock app with port mappings."""
    app = MagicMock()
    app.docker = MagicMock()
    app.docker.environment = []
    
    port1 = MagicMock()
    port1.container = 80
    port1.host = 8080
    
    port2 = MagicMock()
    port2.container = 443
    port2.host = 8443
    
    app.docker.ports = [port1, port2]
    app.requirements = None
    return app


class TestValidateConfigInit:
    """Tests for DeploymentValidator initialization."""

    def test_init_stores_dependencies(
        self, mock_ssh_executor, mock_marketplace_service, mock_server_service
    ):
        """Validator should store all dependencies."""
        with patch("services.deployment.validation.logger"):
            validator = DeploymentValidator(
                ssh_executor=mock_ssh_executor,
                marketplace_service=mock_marketplace_service,
                server_service=mock_server_service,
            )
        
        assert validator.ssh is mock_ssh_executor
        assert validator.marketplace_service is mock_marketplace_service
        assert validator.server_service is mock_server_service


class TestValidateConfigBasic:
    """Tests for basic config validation scenarios."""

    @pytest.mark.asyncio
    async def test_validate_config_app_not_found(
        self, validator, mock_marketplace_service
    ):
        """validate_config should return error when app not found."""
        mock_marketplace_service.get_app.return_value = None

        result = await validator.validate_config("nonexistent-app", {})

        assert result["valid"] is False
        assert "not found" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_validate_config_basic_success(
        self, validator, mock_marketplace_service, mock_app_basic
    ):
        """validate_config should pass with valid basic configuration."""
        mock_marketplace_service.get_app.return_value = mock_app_basic

        result = await validator.validate_config("test-app", {})

        assert result["valid"] is True
        assert result["errors"] == []
        assert result["warnings"] == []

    @pytest.mark.asyncio
    async def test_validate_config_exception_handling(
        self, validator, mock_marketplace_service
    ):
        """validate_config should handle exceptions gracefully."""
        mock_marketplace_service.get_app.side_effect = Exception("Service error")

        with patch("services.deployment.validation.logger"):
            result = await validator.validate_config("test-app", {})

        assert result["valid"] is False
        assert "Service error" in result["errors"][0]


class TestValidateConfigEnvVars:
    """Tests for environment variable validation."""

    @pytest.mark.asyncio
    async def test_validate_config_missing_required_env(
        self, validator, mock_marketplace_service, mock_app_with_env_vars
    ):
        """validate_config should fail when required env var is missing."""
        mock_marketplace_service.get_app.return_value = mock_app_with_env_vars

        result = await validator.validate_config("test-app", {"env": {}})

        assert result["valid"] is False
        assert any("DATABASE_URL" in error for error in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_config_required_env_provided(
        self, validator, mock_marketplace_service, mock_app_with_env_vars
    ):
        """validate_config should pass when required env var is provided."""
        mock_marketplace_service.get_app.return_value = mock_app_with_env_vars

        config = {"env": {"DATABASE_URL": "postgres://localhost/db"}}
        result = await validator.validate_config("test-app", config)

        assert result["valid"] is True
        assert not any("DATABASE_URL" in error for error in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_config_required_with_default(
        self, validator, mock_marketplace_service, mock_app_with_env_vars
    ):
        """validate_config should pass when required env var has default."""
        mock_marketplace_service.get_app.return_value = mock_app_with_env_vars

        config = {"env": {"DATABASE_URL": "postgres://localhost/db"}}
        result = await validator.validate_config("test-app", config)

        assert result["valid"] is True
        assert not any("PORT" in error for error in result["errors"])


class TestValidateConfigPorts:
    """Tests for port validation."""

    @pytest.mark.asyncio
    async def test_validate_config_valid_ports(
        self, validator, mock_marketplace_service, mock_app_with_ports
    ):
        """validate_config should pass with valid port configuration."""
        mock_marketplace_service.get_app.return_value = mock_app_with_ports

        config = {"ports": {"80": 9000, "443": 9443}}
        result = await validator.validate_config("test-app", config)

        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_config_port_not_in_definition(
        self, validator, mock_marketplace_service, mock_app_with_ports
    ):
        """validate_config should warn when port not in app definition."""
        mock_marketplace_service.get_app.return_value = mock_app_with_ports

        config = {"ports": {"8080": 9000}}
        result = await validator.validate_config("test-app", config)

        assert result["valid"] is True
        assert any("8080" in warning for warning in result["warnings"])

    @pytest.mark.asyncio
    async def test_validate_config_invalid_port_number_negative(
        self, validator, mock_marketplace_service, mock_app_with_ports
    ):
        """validate_config should fail with negative port number."""
        mock_marketplace_service.get_app.return_value = mock_app_with_ports

        config = {"ports": {"80": -1}}
        result = await validator.validate_config("test-app", config)

        assert result["valid"] is False
        assert any("-1" in error for error in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_config_invalid_port_number_too_high(
        self, validator, mock_marketplace_service, mock_app_with_ports
    ):
        """validate_config should fail with port number > 65535."""
        mock_marketplace_service.get_app.return_value = mock_app_with_ports

        config = {"ports": {"80": 70000}}
        result = await validator.validate_config("test-app", config)

        assert result["valid"] is False
        assert any("70000" in error for error in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_config_invalid_port_value_string(
        self, validator, mock_marketplace_service, mock_app_with_ports
    ):
        """validate_config should fail with non-numeric port value."""
        mock_marketplace_service.get_app.return_value = mock_app_with_ports

        config = {"ports": {"80": "not_a_port"}}
        result = await validator.validate_config("test-app", config)

        assert result["valid"] is False
        assert any("not_a_port" in error for error in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_config_boundary_port_1(
        self, validator, mock_marketplace_service, mock_app_with_ports
    ):
        """validate_config should pass with port 1."""
        mock_marketplace_service.get_app.return_value = mock_app_with_ports

        config = {"ports": {"80": 1}}
        result = await validator.validate_config("test-app", config)

        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_config_boundary_port_65535(
        self, validator, mock_marketplace_service, mock_app_with_ports
    ):
        """validate_config should pass with port 65535."""
        mock_marketplace_service.get_app.return_value = mock_app_with_ports

        config = {"ports": {"80": 65535}}
        result = await validator.validate_config("test-app", config)

        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_config_boundary_port_0(
        self, validator, mock_marketplace_service, mock_app_with_ports
    ):
        """validate_config should fail with port 0."""
        mock_marketplace_service.get_app.return_value = mock_app_with_ports

        config = {"ports": {"80": 0}}
        result = await validator.validate_config("test-app", config)

        assert result["valid"] is False


class TestValidateConfigVolumes:
    """Tests for volume path validation."""

    @pytest.mark.asyncio
    async def test_validate_config_valid_volumes(
        self, validator, mock_marketplace_service, mock_app_basic
    ):
        """validate_config should pass with valid absolute volume paths."""
        mock_marketplace_service.get_app.return_value = mock_app_basic

        config = {"volumes": {"/container/data": "/host/data"}}
        result = await validator.validate_config("test-app", config)

        assert result["valid"] is True
        assert result["warnings"] == []

    @pytest.mark.asyncio
    async def test_validate_config_empty_volume_path(
        self, validator, mock_marketplace_service, mock_app_basic
    ):
        """validate_config should fail with empty volume host path."""
        mock_marketplace_service.get_app.return_value = mock_app_basic

        config = {"volumes": {"/container/data": ""}}
        result = await validator.validate_config("test-app", config)

        assert result["valid"] is False
        assert any("Empty host path" in error for error in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_config_relative_volume_path(
        self, validator, mock_marketplace_service, mock_app_basic
    ):
        """validate_config should warn with relative volume path."""
        mock_marketplace_service.get_app.return_value = mock_app_basic

        config = {"volumes": {"/container/data": "relative/path"}}
        result = await validator.validate_config("test-app", config)

        assert result["valid"] is True
        assert any("not absolute" in warning for warning in result["warnings"])

    @pytest.mark.asyncio
    async def test_validate_config_multiple_volumes(
        self, validator, mock_marketplace_service, mock_app_basic
    ):
        """validate_config should validate multiple volumes."""
        mock_marketplace_service.get_app.return_value = mock_app_basic

        config = {
            "volumes": {
                "/container/data": "/host/data",
                "/container/logs": "/host/logs",
            }
        }
        result = await validator.validate_config("test-app", config)

        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_config_no_volumes_config(
        self, validator, mock_marketplace_service, mock_app_basic
    ):
        """validate_config should pass when no volumes in config."""
        mock_marketplace_service.get_app.return_value = mock_app_basic

        config = {}
        result = await validator.validate_config("test-app", config)

        assert result["valid"] is True

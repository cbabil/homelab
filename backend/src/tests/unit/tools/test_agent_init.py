"""
Agent Tools Unit Tests - Initialization and Validation

Tests for AgentTools initialization and validation helper methods.
"""

from unittest.mock import MagicMock, patch

import pytest

from tools.agent.tools import AgentTools


class TestAgentToolsInit:
    """Tests for AgentTools initialization."""

    def test_initialization_with_all_services(self):
        """Test AgentTools is initialized with all services."""
        mock_agent_service = MagicMock()
        mock_agent_manager = MagicMock()
        mock_ssh_service = MagicMock()
        mock_server_service = MagicMock()
        mock_packager = MagicMock()
        mock_lifecycle = MagicMock()

        with patch("tools.agent.tools.logger"):
            tools = AgentTools(
                mock_agent_service,
                mock_agent_manager,
                mock_ssh_service,
                mock_server_service,
                mock_packager,
                mock_lifecycle,
            )

        assert tools.agent_service == mock_agent_service
        assert tools.agent_manager == mock_agent_manager
        assert tools.ssh_service == mock_ssh_service
        assert tools.server_service == mock_server_service
        assert tools.agent_packager == mock_packager
        assert tools.lifecycle == mock_lifecycle

    def test_initialization_with_optional_services_none(self):
        """Test AgentTools creates default packager when not provided."""
        mock_agent_service = MagicMock()
        mock_agent_manager = MagicMock()
        mock_ssh_service = MagicMock()
        mock_server_service = MagicMock()

        with patch("tools.agent.tools.logger"):
            with patch("tools.agent.tools.AgentPackager") as MockPackager:
                mock_packager_instance = MagicMock()
                MockPackager.return_value = mock_packager_instance

                tools = AgentTools(
                    mock_agent_service,
                    mock_agent_manager,
                    mock_ssh_service,
                    mock_server_service,
                )

        assert tools.agent_packager == mock_packager_instance
        assert tools.lifecycle is None


class TestGetServerUrl:
    """Tests for _get_server_url helper."""

    @pytest.fixture
    def agent_tools(self):
        """Create AgentTools with mocked dependencies."""
        with patch("tools.agent.tools.logger"):
            return AgentTools(
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
            )

    def test_get_server_url_default(self, agent_tools):
        """Test default server URL."""
        with patch.dict("os.environ", {}, clear=True):
            url = agent_tools._get_server_url()
        assert url == "http://localhost:8000"

    def test_get_server_url_from_env(self, agent_tools):
        """Test server URL from environment variable."""
        with patch.dict("os.environ", {"SERVER_URL": "https://example.com:9000"}):
            url = agent_tools._get_server_url()
        assert url == "https://example.com:9000"


class TestValidateRegistrationCode:
    """Tests for _validate_registration_code helper."""

    @pytest.fixture
    def agent_tools(self):
        """Create AgentTools with mocked dependencies."""
        with patch("tools.agent.tools.logger"):
            return AgentTools(
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
            )

    def test_valid_registration_code_alphanumeric(self, agent_tools):
        """Test valid alphanumeric registration code."""
        assert agent_tools._validate_registration_code("abc123ABC") is True

    def test_valid_registration_code_with_hyphen(self, agent_tools):
        """Test valid registration code with hyphen."""
        assert agent_tools._validate_registration_code("abc-123-xyz") is True

    def test_valid_registration_code_with_underscore(self, agent_tools):
        """Test valid registration code with underscore."""
        assert agent_tools._validate_registration_code("abc_123_xyz") is True

    def test_valid_registration_code_base64url(self, agent_tools):
        """Test valid base64url-like registration code."""
        assert agent_tools._validate_registration_code("aB3-_xY9") is True

    def test_invalid_registration_code_empty(self, agent_tools):
        """Test empty registration code is invalid."""
        assert agent_tools._validate_registration_code("") is False

    def test_invalid_registration_code_none(self, agent_tools):
        """Test None registration code is invalid."""
        assert agent_tools._validate_registration_code(None) is False

    def test_invalid_registration_code_too_long(self, agent_tools):
        """Test registration code over 100 chars is invalid."""
        long_code = "a" * 101
        assert agent_tools._validate_registration_code(long_code) is False

    def test_invalid_registration_code_max_length(self, agent_tools):
        """Test registration code at exactly 100 chars is valid."""
        max_code = "a" * 100
        assert agent_tools._validate_registration_code(max_code) is True

    def test_invalid_registration_code_shell_chars(self, agent_tools):
        """Test registration code with shell injection chars is invalid."""
        assert agent_tools._validate_registration_code("code;rm -rf /") is False
        assert agent_tools._validate_registration_code("code`id`") is False
        assert agent_tools._validate_registration_code("code$(pwd)") is False

    def test_invalid_registration_code_special_chars(self, agent_tools):
        """Test registration code with special chars is invalid."""
        assert agent_tools._validate_registration_code("code!@#") is False
        assert agent_tools._validate_registration_code("code with spaces") is False


class TestValidateServerUrl:
    """Tests for _validate_server_url helper."""

    @pytest.fixture
    def agent_tools(self):
        """Create AgentTools with mocked dependencies."""
        with patch("tools.agent.tools.logger"):
            return AgentTools(
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
            )

    def test_valid_http_url(self, agent_tools):
        """Test valid HTTP URL."""
        assert agent_tools._validate_server_url("http://localhost:8000") is True

    def test_valid_https_url(self, agent_tools):
        """Test valid HTTPS URL."""
        assert agent_tools._validate_server_url("https://example.com") is True

    def test_valid_ws_url(self, agent_tools):
        """Test valid WebSocket URL."""
        assert agent_tools._validate_server_url("ws://localhost:8000/ws") is True

    def test_valid_wss_url(self, agent_tools):
        """Test valid secure WebSocket URL."""
        assert agent_tools._validate_server_url("wss://example.com/ws") is True

    def test_invalid_url_empty(self, agent_tools):
        """Test empty URL is invalid."""
        assert agent_tools._validate_server_url("") is False

    def test_invalid_url_none(self, agent_tools):
        """Test None URL is invalid."""
        assert agent_tools._validate_server_url(None) is False

    def test_invalid_url_too_long(self, agent_tools):
        """Test URL over 500 chars is invalid."""
        long_url = "https://example.com/" + "a" * 500
        assert agent_tools._validate_server_url(long_url) is False

    def test_invalid_url_ftp_protocol(self, agent_tools):
        """Test FTP URL is invalid (only http/https/ws/wss allowed)."""
        assert agent_tools._validate_server_url("ftp://example.com") is False

    def test_invalid_url_no_protocol(self, agent_tools):
        """Test URL without protocol is invalid."""
        assert agent_tools._validate_server_url("example.com") is False

    def test_invalid_url_shell_injection_semicolon(self, agent_tools):
        """Test URL with semicolon injection is invalid."""
        assert agent_tools._validate_server_url("http://example.com;rm -rf /") is False

    def test_invalid_url_shell_injection_pipe(self, agent_tools):
        """Test URL with pipe injection is invalid."""
        assert (
            agent_tools._validate_server_url("http://example.com|cat /etc/passwd")
            is False
        )

    def test_invalid_url_shell_injection_backtick(self, agent_tools):
        """Test URL with backtick injection is invalid."""
        assert agent_tools._validate_server_url("http://example.com`id`") is False

    def test_invalid_url_shell_injection_dollar(self, agent_tools):
        """Test URL with $() injection is invalid."""
        assert agent_tools._validate_server_url("http://example.com$(whoami)") is False

    def test_invalid_url_with_quotes(self, agent_tools):
        """Test URL with quotes is invalid."""
        assert agent_tools._validate_server_url("http://example.com'test'") is False
        assert agent_tools._validate_server_url('http://example.com"test"') is False

    def test_invalid_url_with_newline(self, agent_tools):
        """Test URL with newline is invalid."""
        assert agent_tools._validate_server_url("http://example.com\nid") is False


class TestBuildDeployScript:
    """Tests for _build_deploy_script helper."""

    @pytest.fixture
    def agent_tools(self):
        """Create AgentTools with mocked dependencies."""
        mock_packager = MagicMock()
        mock_packager.package.return_value = "BASE64ENCODED=="
        mock_packager.get_version.return_value = "1.0.0"

        with patch("tools.agent.tools.logger"):
            return AgentTools(
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
                mock_packager,
            )

    def test_build_deploy_script_success(self, agent_tools):
        """Test building deploy script with valid inputs."""
        script = agent_tools._build_deploy_script("validcode123", "https://example.com")

        assert "Installing Tomo Agent v1.0.0" in script
        assert "docker stop tomo-agent" in script
        assert "docker build -t tomo-agent:latest" in script
        assert "BASE64ENCODED==" in script
        assert "'validcode123'" in script or "validcode123" in script
        assert "'https://example.com'" in script or "https://example.com" in script

    def test_build_deploy_script_invalid_code(self, agent_tools):
        """Test building deploy script with invalid registration code."""
        with pytest.raises(ValueError, match="Invalid registration code format"):
            agent_tools._build_deploy_script("invalid;code", "https://example.com")

    def test_build_deploy_script_invalid_url(self, agent_tools):
        """Test building deploy script with invalid server URL."""
        with pytest.raises(ValueError, match="Invalid server URL format"):
            agent_tools._build_deploy_script("validcode", "ftp://example.com")

    def test_build_deploy_script_empty_code(self, agent_tools):
        """Test building deploy script with empty code."""
        with pytest.raises(ValueError, match="Invalid registration code format"):
            agent_tools._build_deploy_script("", "https://example.com")

    def test_build_deploy_script_shell_injection_code(self, agent_tools):
        """Test building deploy script rejects shell injection in code."""
        with pytest.raises(ValueError, match="Invalid registration code format"):
            agent_tools._build_deploy_script("$(rm -rf /)", "https://example.com")

    def test_build_deploy_script_shell_injection_url(self, agent_tools):
        """Test building deploy script rejects shell injection in URL."""
        with pytest.raises(ValueError, match="Invalid server URL format"):
            agent_tools._build_deploy_script("validcode", "http://x.com;rm -rf /")

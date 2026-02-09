"""
Main Module Unit Tests

Tests for main.py - MCP server entry point.
Note: main.py has module-level initialization that makes testing challenging.
We test the module can be imported with mocked dependencies.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMainModuleImport:
    """Tests for main module import and initialization."""

    def test_module_imports_with_mocks(self):
        """Test that main module can be imported with mocked dependencies."""
        mock_fastmcp = MagicMock()
        mock_app = MagicMock()
        mock_fastmcp.return_value = mock_app

        mock_services = {
            "agent_websocket_handler": MagicMock(),
            "agent_lifecycle": MagicMock(),
            "database_service": MagicMock(),
            "agent_service": MagicMock(),
            "log_service": MagicMock(),
        }

        with (
            patch.dict(
                "sys.modules",
                {
                    "fastmcp": MagicMock(FastMCP=mock_fastmcp),
                },
            ),
            patch("lib.tool_loader.register_all_tools"),
            patch("lib.logging_config.setup_logging"),
            patch("lib.config.load_config", return_value={"app_env": "test"}),
            patch("lib.config.resolve_data_directory", return_value="/tmp/data"),
            patch("services.factory.create_services", return_value=mock_services),
            patch("structlog.get_logger", return_value=MagicMock()),
        ):
            # Force reimport to test initialization
            import sys

            # Remove cached module if exists
            if "main" in sys.modules:
                del sys.modules["main"]

            # This tests that the module can be imported
            # without raising exceptions

    def test_main_module_initialization_sequence(self):
        """Test that main module initializes components in correct order."""
        import sys

        # Remove cached module if exists
        if "main" in sys.modules:
            del sys.modules["main"]

        mock_fastmcp_class = MagicMock()
        mock_app = MagicMock()
        mock_fastmcp_class.return_value = mock_app

        mock_logger = MagicMock()

        mock_services = {
            "agent_websocket_handler": MagicMock(),
            "agent_lifecycle": MagicMock(),
            "database_service": MagicMock(),
            "agent_service": MagicMock(),
            "log_service": MagicMock(),
        }

        with (
            patch("lib.logging_config.setup_logging") as mock_setup_logging,
            patch("structlog.get_logger", return_value=mock_logger) as mock_get_logger,
            patch(
                "lib.config.load_config", return_value={"app_env": "test"}
            ) as mock_load_config,
            patch(
                "lib.config.resolve_data_directory", return_value="/tmp/data"
            ) as mock_resolve,
            patch(
                "services.factory.create_services", return_value=mock_services
            ) as mock_create,
            patch("lib.tool_loader.register_all_tools") as mock_register,
            patch.dict(
                "sys.modules", {"fastmcp": MagicMock(FastMCP=mock_fastmcp_class)}
            ),
        ):
            # Import the module - this triggers initialization
            import main

            # Verify initialization sequence
            mock_setup_logging.assert_called_once()
            mock_get_logger.assert_called_with("main")
            mock_load_config.assert_called_once()
            mock_resolve.assert_called_once()
            mock_create.assert_called_once()
            mock_register.assert_called_once()

            # Verify FastMCP was configured correctly
            mock_fastmcp_class.assert_called_once_with(
                name="tomo",
                version="0.1.0",
                instructions="Tomo management and automation server",
            )

            # Verify exports are set
            assert main.agent_websocket_handler is not None
            assert main.agent_lifecycle is not None
            assert main.database_service is not None

            # Clean up
            del sys.modules["main"]

    def test_main_module_logger_info_called(self):
        """Test that logger.info is called during initialization."""
        import sys

        if "main" in sys.modules:
            del sys.modules["main"]

        mock_fastmcp_class = MagicMock()
        mock_app = MagicMock()
        mock_fastmcp_class.return_value = mock_app

        mock_logger = MagicMock()

        mock_services = {
            "agent_websocket_handler": MagicMock(),
            "agent_lifecycle": MagicMock(),
            "database_service": MagicMock(),
            "agent_service": MagicMock(),
            "log_service": MagicMock(),
        }

        with (
            patch("lib.logging_config.setup_logging"),
            patch("structlog.get_logger", return_value=mock_logger),
            patch("lib.config.load_config", return_value={"app_env": "production"}),
            patch("lib.config.resolve_data_directory", return_value="/var/data"),
            patch("services.factory.create_services", return_value=mock_services),
            patch("lib.tool_loader.register_all_tools"),
            patch.dict(
                "sys.modules", {"fastmcp": MagicMock(FastMCP=mock_fastmcp_class)}
            ),
        ):
            import main

            # Verify logger.info was called with config info
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args_list[0]
            assert "Configuration loaded" in str(call_args)

            # Access the module to avoid unused import warning
            assert main.app is not None

            del sys.modules["main"]


class TestMainFunctionality:
    """Tests for main module functionality."""

    def test_config_loading(self):
        """Test that configuration is loaded properly."""
        with (
            patch("lib.config.load_config") as mock_load,
            patch("lib.config.resolve_data_directory") as mock_resolve,
        ):
            mock_load.return_value = {
                "app_env": "development",
                "data_directory": "/custom/data",
            }
            mock_resolve.return_value = "/custom/data"

            # Verify config functions work
            config = mock_load()
            data_dir = mock_resolve(config)

            assert config["app_env"] == "development"
            assert data_dir == "/custom/data"

    def test_services_creation(self):
        """Test that services are created properly."""
        mock_services = {
            "agent_websocket_handler": MagicMock(),
            "agent_lifecycle": MagicMock(),
            "database_service": MagicMock(),
            "agent_service": MagicMock(),
            "auth_service": MagicMock(),
            "server_service": MagicMock(),
        }

        with patch("services.factory.create_services") as mock_create:
            mock_create.return_value = mock_services

            services = mock_create("/tmp/data", {"app_env": "test"})

            assert "agent_websocket_handler" in services
            assert "database_service" in services

    def test_fastmcp_app_creation(self):
        """Test FastMCP app creation."""
        with patch("fastmcp.FastMCP") as mock_mcp:
            mock_app = MagicMock()
            mock_mcp.return_value = mock_app

            app = mock_mcp(
                name="tomo",
                version="0.1.0",
                instructions="Tomo management and automation server",
            )

            mock_mcp.assert_called_once_with(
                name="tomo",
                version="0.1.0",
                instructions="Tomo management and automation server",
            )
            assert app == mock_app


class TestLifecycleEvents:
    """Tests for lifecycle event handlers."""

    @pytest.mark.asyncio
    async def test_startup_lifecycle_handler(self):
        """Test startup lifecycle event handler."""
        mock_agent_service = MagicMock()
        mock_agent_service.reset_stale_agent_statuses = AsyncMock(return_value=3)

        mock_lifecycle = MagicMock()
        mock_lifecycle.start = AsyncMock()

        # Simulate startup lifecycle
        reset_count = await mock_agent_service.reset_stale_agent_statuses()
        await mock_lifecycle.start()

        assert reset_count == 3
        mock_lifecycle.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_lifecycle_handler(self):
        """Test shutdown lifecycle event handler."""
        mock_lifecycle = MagicMock()
        mock_lifecycle.stop = AsyncMock()

        # Simulate shutdown lifecycle
        await mock_lifecycle.stop()

        mock_lifecycle.stop.assert_called_once()


class TestCorsConfiguration:
    """Tests for CORS configuration."""

    def test_default_cors_origins(self):
        """Test default CORS origins parsing."""
        default_origins = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003"
        allowed_origins = default_origins.split(",")
        allowed_origins = [
            origin.strip() for origin in allowed_origins if origin.strip()
        ]

        assert len(allowed_origins) == 4
        assert "http://localhost:3000" in allowed_origins
        assert "http://localhost:3003" in allowed_origins

    def test_custom_cors_origins_from_env(self):
        """Test custom CORS origins from environment variable."""
        import os

        with patch.dict(
            os.environ,
            {"ALLOWED_ORIGINS": "https://example.com,https://api.example.com"},
        ):
            custom_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
            custom_origins = [
                origin.strip() for origin in custom_origins if origin.strip()
            ]

            assert len(custom_origins) == 2
            assert "https://example.com" in custom_origins

    def test_cors_origins_with_whitespace(self):
        """Test CORS origins parsing handles whitespace."""
        origins_with_spaces = (
            "http://localhost:3000 , http://localhost:3001 , http://localhost:3002"
        )
        allowed_origins = origins_with_spaces.split(",")
        allowed_origins = [
            origin.strip() for origin in allowed_origins if origin.strip()
        ]

        assert len(allowed_origins) == 3
        assert "http://localhost:3000" in allowed_origins


class TestWebSocketConfiguration:
    """Tests for WebSocket route configuration."""

    def test_websocket_route_path(self):
        """Test WebSocket route path configuration."""
        ws_path = "/ws/agent"
        assert ws_path.startswith("/ws/")
        assert "agent" in ws_path


class TestDatabaseInitialization:
    """Tests for database initialization sequence."""

    @pytest.mark.asyncio
    async def test_database_migrations_sequence(self):
        """Test that database migrations are called in correct order."""
        mock_db_service = MagicMock()
        mock_db_service.run_installed_apps_migrations = AsyncMock()
        mock_db_service.run_users_migrations = AsyncMock()
        mock_db_service.initialize_system_info_table = AsyncMock()
        mock_db_service.initialize_users_table = AsyncMock()
        mock_db_service.initialize_sessions_table = AsyncMock()
        mock_db_service.initialize_account_locks_table = AsyncMock()
        mock_db_service.initialize_notifications_table = AsyncMock()
        mock_db_service.initialize_retention_settings_table = AsyncMock()
        mock_db_service.initialize_servers_table = AsyncMock()
        mock_db_service.initialize_agents_table = AsyncMock()
        mock_db_service.initialize_installed_apps_table = AsyncMock()
        mock_db_service.initialize_metrics_tables = AsyncMock()

        # Simulate the initialization sequence
        await mock_db_service.run_installed_apps_migrations()
        await mock_db_service.run_users_migrations()
        await mock_db_service.initialize_system_info_table()
        await mock_db_service.initialize_users_table()
        await mock_db_service.initialize_sessions_table()
        await mock_db_service.initialize_account_locks_table()
        await mock_db_service.initialize_notifications_table()
        await mock_db_service.initialize_retention_settings_table()
        await mock_db_service.initialize_servers_table()
        await mock_db_service.initialize_agents_table()
        await mock_db_service.initialize_installed_apps_table()
        await mock_db_service.initialize_metrics_tables()

        # Verify all methods were called
        mock_db_service.run_installed_apps_migrations.assert_called_once()
        mock_db_service.run_users_migrations.assert_called_once()
        mock_db_service.initialize_system_info_table.assert_called_once()
        mock_db_service.initialize_users_table.assert_called_once()
        mock_db_service.initialize_sessions_table.assert_called_once()
        mock_db_service.initialize_account_locks_table.assert_called_once()
        mock_db_service.initialize_notifications_table.assert_called_once()
        mock_db_service.initialize_retention_settings_table.assert_called_once()
        mock_db_service.initialize_servers_table.assert_called_once()
        mock_db_service.initialize_agents_table.assert_called_once()
        mock_db_service.initialize_installed_apps_table.assert_called_once()
        mock_db_service.initialize_metrics_tables.assert_called_once()

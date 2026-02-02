"""
Unit tests for services/factory.py

Tests for service factory that creates and wires all application services.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestCreateServices:
    """Tests for create_services function."""

    def test_create_services_returns_dict(self):
        """Should return dictionary of services."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            config = {"test": "config"}

            with patch.multiple(
                "services.factory",
                db_manager=MagicMock(),
                DatabaseService=MagicMock(),
                AppService=MagicMock(),
                AuthService=MagicMock(),
                SessionService=MagicMock(),
                SSHService=MagicMock(),
                MonitoringService=MagicMock(),
                ServerService=MagicMock(),
                SettingsService=MagicMock(),
                MarketplaceService=MagicMock(),
                BackupService=MagicMock(),
                ActivityService=MagicMock(),
                NotificationService=MagicMock(),
                RetentionService=MagicMock(),
                MetricsService=MagicMock(),
                DatabaseConnection=MagicMock(),
                AgentDatabaseService=MagicMock(),
                AgentService=MagicMock(),
                AgentLifecycleManager=MagicMock(),
                AgentManager=MagicMock(),
                AgentWebSocketHandler=MagicMock(),
                CommandRouter=MagicMock(),
                RoutedExecutor=MagicMock(),
                AgentExecutor=MagicMock(),
                DeploymentService=MagicMock(),
                DashboardService=MagicMock(),
                logger=MagicMock(),
            ):
                from services.factory import create_services

                result = create_services(data_dir, config)

                assert isinstance(result, dict)

    def test_create_services_sets_data_directory(self):
        """Should set data directory on db_manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            config = {}
            mock_db_manager = MagicMock()

            with patch.multiple(
                "services.factory",
                db_manager=mock_db_manager,
                DatabaseService=MagicMock(),
                AppService=MagicMock(),
                AuthService=MagicMock(),
                SessionService=MagicMock(),
                SSHService=MagicMock(),
                MonitoringService=MagicMock(),
                ServerService=MagicMock(),
                SettingsService=MagicMock(),
                MarketplaceService=MagicMock(),
                BackupService=MagicMock(),
                ActivityService=MagicMock(),
                NotificationService=MagicMock(),
                RetentionService=MagicMock(),
                MetricsService=MagicMock(),
                DatabaseConnection=MagicMock(),
                AgentDatabaseService=MagicMock(),
                AgentService=MagicMock(),
                AgentLifecycleManager=MagicMock(),
                AgentManager=MagicMock(),
                AgentWebSocketHandler=MagicMock(),
                CommandRouter=MagicMock(),
                RoutedExecutor=MagicMock(),
                AgentExecutor=MagicMock(),
                DeploymentService=MagicMock(),
                DashboardService=MagicMock(),
                logger=MagicMock(),
            ):
                from services.factory import create_services

                create_services(data_dir, config)

                mock_db_manager.set_data_directory.assert_called_once_with(data_dir)

    def test_create_services_includes_config(self):
        """Should include config in returned dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            config = {"key": "value", "another": 123}

            with patch.multiple(
                "services.factory",
                db_manager=MagicMock(),
                DatabaseService=MagicMock(),
                AppService=MagicMock(),
                AuthService=MagicMock(),
                SessionService=MagicMock(),
                SSHService=MagicMock(),
                MonitoringService=MagicMock(),
                ServerService=MagicMock(),
                SettingsService=MagicMock(),
                MarketplaceService=MagicMock(),
                BackupService=MagicMock(),
                ActivityService=MagicMock(),
                NotificationService=MagicMock(),
                RetentionService=MagicMock(),
                MetricsService=MagicMock(),
                DatabaseConnection=MagicMock(),
                AgentDatabaseService=MagicMock(),
                AgentService=MagicMock(),
                AgentLifecycleManager=MagicMock(),
                AgentManager=MagicMock(),
                AgentWebSocketHandler=MagicMock(),
                CommandRouter=MagicMock(),
                RoutedExecutor=MagicMock(),
                AgentExecutor=MagicMock(),
                DeploymentService=MagicMock(),
                DashboardService=MagicMock(),
                logger=MagicMock(),
            ):
                from services.factory import create_services

                result = create_services(data_dir, config)

                assert result["config"] == config

    def test_create_services_includes_all_expected_services(self):
        """Should include all expected service keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            config = {}

            with patch.multiple(
                "services.factory",
                db_manager=MagicMock(),
                DatabaseService=MagicMock(),
                AppService=MagicMock(),
                AuthService=MagicMock(),
                SessionService=MagicMock(),
                SSHService=MagicMock(),
                MonitoringService=MagicMock(),
                ServerService=MagicMock(),
                SettingsService=MagicMock(),
                MarketplaceService=MagicMock(),
                BackupService=MagicMock(),
                ActivityService=MagicMock(),
                NotificationService=MagicMock(),
                RetentionService=MagicMock(),
                MetricsService=MagicMock(),
                DatabaseConnection=MagicMock(),
                AgentDatabaseService=MagicMock(),
                AgentService=MagicMock(),
                AgentLifecycleManager=MagicMock(),
                AgentManager=MagicMock(),
                AgentWebSocketHandler=MagicMock(),
                CommandRouter=MagicMock(),
                RoutedExecutor=MagicMock(),
                AgentExecutor=MagicMock(),
                DeploymentService=MagicMock(),
                DashboardService=MagicMock(),
                logger=MagicMock(),
            ):
                from services.factory import create_services

                result = create_services(data_dir, config)

                expected_keys = [
                    "config",
                    "database_service",
                    "app_service",
                    "auth_service",
                    "session_service",
                    "ssh_service",
                    "monitoring_service",
                    "server_service",
                    "settings_service",
                    "marketplace_service",
                    "backup_service",
                    "activity_service",
                    "notification_service",
                    "retention_service",
                    "deployment_service",
                    "metrics_service",
                    "dashboard_service",
                    "agent_service",
                    "agent_manager",
                    "agent_lifecycle",
                    "agent_websocket_handler",
                    "command_router",
                    "routed_executor",
                ]

                for key in expected_keys:
                    assert key in result, f"Missing key: {key}"

    def test_create_services_logs_creation(self):
        """Should log when all services are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            config = {}
            mock_logger = MagicMock()

            with patch.multiple(
                "services.factory",
                db_manager=MagicMock(),
                DatabaseService=MagicMock(),
                AppService=MagicMock(),
                AuthService=MagicMock(),
                SessionService=MagicMock(),
                SSHService=MagicMock(),
                MonitoringService=MagicMock(),
                ServerService=MagicMock(),
                SettingsService=MagicMock(),
                MarketplaceService=MagicMock(),
                BackupService=MagicMock(),
                ActivityService=MagicMock(),
                NotificationService=MagicMock(),
                RetentionService=MagicMock(),
                MetricsService=MagicMock(),
                DatabaseConnection=MagicMock(),
                AgentDatabaseService=MagicMock(),
                AgentService=MagicMock(),
                AgentLifecycleManager=MagicMock(),
                AgentManager=MagicMock(),
                AgentWebSocketHandler=MagicMock(),
                CommandRouter=MagicMock(),
                RoutedExecutor=MagicMock(),
                AgentExecutor=MagicMock(),
                DeploymentService=MagicMock(),
                DashboardService=MagicMock(),
                logger=mock_logger,
            ):
                from services.factory import create_services

                create_services(data_dir, config)

                mock_logger.info.assert_called_once_with(
                    "All services created", service_count=22
                )

    def test_create_services_creates_database_service_with_data_dir(self):
        """Should create DatabaseService with data_directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            config = {}
            mock_db_service = MagicMock()

            with patch.multiple(
                "services.factory",
                db_manager=MagicMock(),
                DatabaseService=mock_db_service,
                AppService=MagicMock(),
                AuthService=MagicMock(),
                SessionService=MagicMock(),
                SSHService=MagicMock(),
                MonitoringService=MagicMock(),
                ServerService=MagicMock(),
                SettingsService=MagicMock(),
                MarketplaceService=MagicMock(),
                BackupService=MagicMock(),
                ActivityService=MagicMock(),
                NotificationService=MagicMock(),
                RetentionService=MagicMock(),
                MetricsService=MagicMock(),
                DatabaseConnection=MagicMock(),
                AgentDatabaseService=MagicMock(),
                AgentService=MagicMock(),
                AgentLifecycleManager=MagicMock(),
                AgentManager=MagicMock(),
                AgentWebSocketHandler=MagicMock(),
                CommandRouter=MagicMock(),
                RoutedExecutor=MagicMock(),
                AgentExecutor=MagicMock(),
                DeploymentService=MagicMock(),
                DashboardService=MagicMock(),
                logger=MagicMock(),
            ):
                from services.factory import create_services

                create_services(data_dir, config)

                mock_db_service.assert_called_once_with(data_directory=data_dir)

    def test_create_services_wires_auth_service_with_db_service(self):
        """Should wire AuthService with database service."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            config = {}
            mock_db_service_instance = MagicMock()
            mock_db_service = MagicMock(return_value=mock_db_service_instance)
            mock_auth_service = MagicMock()

            with patch.multiple(
                "services.factory",
                db_manager=MagicMock(),
                DatabaseService=mock_db_service,
                AppService=MagicMock(),
                AuthService=mock_auth_service,
                SessionService=MagicMock(),
                SSHService=MagicMock(),
                MonitoringService=MagicMock(),
                ServerService=MagicMock(),
                SettingsService=MagicMock(),
                MarketplaceService=MagicMock(),
                BackupService=MagicMock(),
                ActivityService=MagicMock(),
                NotificationService=MagicMock(),
                RetentionService=MagicMock(),
                MetricsService=MagicMock(),
                DatabaseConnection=MagicMock(),
                AgentDatabaseService=MagicMock(),
                AgentService=MagicMock(),
                AgentLifecycleManager=MagicMock(),
                AgentManager=MagicMock(),
                AgentWebSocketHandler=MagicMock(),
                CommandRouter=MagicMock(),
                RoutedExecutor=MagicMock(),
                AgentExecutor=MagicMock(),
                DeploymentService=MagicMock(),
                DashboardService=MagicMock(),
                logger=MagicMock(),
            ):
                from services.factory import create_services

                create_services(data_dir, config)

                mock_auth_service.assert_called_once_with(
                    db_service=mock_db_service_instance
                )

    def test_create_services_command_router_prefers_agent(self):
        """Should create CommandRouter with prefer_agent=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            config = {}
            mock_command_router = MagicMock()

            with patch.multiple(
                "services.factory",
                db_manager=MagicMock(),
                DatabaseService=MagicMock(),
                AppService=MagicMock(),
                AuthService=MagicMock(),
                SessionService=MagicMock(),
                SSHService=MagicMock(),
                MonitoringService=MagicMock(),
                ServerService=MagicMock(),
                SettingsService=MagicMock(),
                MarketplaceService=MagicMock(),
                BackupService=MagicMock(),
                ActivityService=MagicMock(),
                NotificationService=MagicMock(),
                RetentionService=MagicMock(),
                MetricsService=MagicMock(),
                DatabaseConnection=MagicMock(),
                AgentDatabaseService=MagicMock(),
                AgentService=MagicMock(),
                AgentLifecycleManager=MagicMock(),
                AgentManager=MagicMock(),
                AgentWebSocketHandler=MagicMock(),
                CommandRouter=mock_command_router,
                RoutedExecutor=MagicMock(),
                AgentExecutor=MagicMock(),
                DeploymentService=MagicMock(),
                DashboardService=MagicMock(),
                logger=MagicMock(),
            ):
                from services.factory import create_services

                create_services(data_dir, config)

                call_kwargs = mock_command_router.call_args[1]
                assert call_kwargs["prefer_agent"] is True

    def test_create_services_all_services_are_not_none(self):
        """Should return non-None values for all services."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            config = {}

            with patch.multiple(
                "services.factory",
                db_manager=MagicMock(),
                DatabaseService=MagicMock(return_value=MagicMock()),
                AppService=MagicMock(return_value=MagicMock()),
                AuthService=MagicMock(return_value=MagicMock()),
                SessionService=MagicMock(return_value=MagicMock()),
                SSHService=MagicMock(return_value=MagicMock()),
                MonitoringService=MagicMock(return_value=MagicMock()),
                ServerService=MagicMock(return_value=MagicMock()),
                SettingsService=MagicMock(return_value=MagicMock()),
                MarketplaceService=MagicMock(return_value=MagicMock()),
                BackupService=MagicMock(return_value=MagicMock()),
                ActivityService=MagicMock(return_value=MagicMock()),
                NotificationService=MagicMock(return_value=MagicMock()),
                RetentionService=MagicMock(return_value=MagicMock()),
                MetricsService=MagicMock(return_value=MagicMock()),
                DatabaseConnection=MagicMock(return_value=MagicMock()),
                AgentDatabaseService=MagicMock(return_value=MagicMock()),
                AgentService=MagicMock(return_value=MagicMock()),
                AgentLifecycleManager=MagicMock(return_value=MagicMock()),
                AgentManager=MagicMock(return_value=MagicMock()),
                AgentWebSocketHandler=MagicMock(return_value=MagicMock()),
                CommandRouter=MagicMock(return_value=MagicMock()),
                RoutedExecutor=MagicMock(return_value=MagicMock()),
                AgentExecutor=MagicMock(return_value=MagicMock()),
                DeploymentService=MagicMock(return_value=MagicMock()),
                DashboardService=MagicMock(return_value=MagicMock()),
                logger=MagicMock(),
            ):
                from services.factory import create_services

                result = create_services(data_dir, config)

                for key, value in result.items():
                    assert value is not None, f"Service {key} is None"

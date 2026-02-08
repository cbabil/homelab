"""
Unit tests for services/factory.py

Tests service factory for creating and wiring application services.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services.factory import create_services


class TestCreateServices:
    """Tests for create_services function."""

    @pytest.fixture
    def mock_services(self):
        """Create patches for all service imports."""
        patches = {
            "db_manager": patch("services.factory.db_manager"),
            "DatabaseService": patch("services.factory.DatabaseService"),
            "AppService": patch("services.factory.AppService"),
            "AuthService": patch("services.factory.AuthService"),
            "SessionService": patch("services.factory.SessionService"),
            "SSHService": patch("services.factory.SSHService"),
            "MonitoringService": patch("services.factory.MonitoringService"),
            "ServerService": patch("services.factory.ServerService"),
            "SettingsService": patch("services.factory.SettingsService"),
            "MarketplaceService": patch("services.factory.MarketplaceService"),
            "BackupService": patch("services.factory.BackupService"),
            "ActivityService": patch("services.factory.ActivityService"),
            "NotificationService": patch("services.factory.NotificationService"),
            "RetentionService": patch("services.factory.RetentionService"),
            "MetricsService": patch("services.factory.MetricsService"),
            "DatabaseConnection": patch("services.factory.DatabaseConnection"),
            "AgentDatabaseService": patch("services.factory.AgentDatabaseService"),
            "AgentService": patch("services.factory.AgentService"),
            "AgentLifecycleManager": patch("services.factory.AgentLifecycleManager"),
            "AgentManager": patch("services.factory.AgentManager"),
            "AgentWebSocketHandler": patch("services.factory.AgentWebSocketHandler"),
            "CommandRouter": patch("services.factory.CommandRouter"),
            "AgentExecutor": patch("services.factory.AgentExecutor"),
            "DeploymentService": patch("services.factory.DeploymentService"),
            "DashboardService": patch("services.factory.DashboardService"),
            "logger": patch("services.factory.logger"),
        }
        return patches

    def test_create_services_returns_dict(self, mock_services, tmp_path):
        """create_services should return a dictionary."""
        with patch.multiple(
            "services.factory",
            **{name: mock.start() for name, mock in mock_services.items()},
        ):
            result = create_services(tmp_path, {"key": "value"})
            assert isinstance(result, dict)

        for mock in mock_services.values():
            mock.stop()

    def test_create_services_contains_all_services(self, mock_services, tmp_path):
        """create_services should return dict with all service keys."""
        expected_keys = {
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
        }

        with patch.multiple(
            "services.factory",
            **{name: mock.start() for name, mock in mock_services.items()},
        ):
            result = create_services(tmp_path, {})
            assert set(result.keys()) == expected_keys

        for mock in mock_services.values():
            mock.stop()

    def test_create_services_includes_config(self, mock_services, tmp_path):
        """create_services should include passed config in result."""
        config = {"debug": True, "port": 8080}

        with patch.multiple(
            "services.factory",
            **{name: mock.start() for name, mock in mock_services.items()},
        ):
            result = create_services(tmp_path, config)
            assert result["config"] == config

        for mock in mock_services.values():
            mock.stop()

    def test_create_services_sets_db_directory(self, mock_services, tmp_path):
        """create_services should set db_manager data directory."""
        mocks = {name: mock.start() for name, mock in mock_services.items()}

        with patch.multiple("services.factory", **mocks):
            create_services(tmp_path, {})
            mocks["db_manager"].set_data_directory.assert_called_once_with(tmp_path)

        for mock in mock_services.values():
            mock.stop()

    def test_create_services_creates_database_service(self, mock_services, tmp_path):
        """create_services should create DatabaseService with data directory."""
        mocks = {name: mock.start() for name, mock in mock_services.items()}

        with patch.multiple("services.factory", **mocks):
            create_services(tmp_path, {})
            mocks["DatabaseService"].assert_called_once_with(data_directory=tmp_path)

        for mock in mock_services.values():
            mock.stop()

    def test_create_services_logs_completion(self, mock_services, tmp_path):
        """create_services should log service count."""
        mocks = {name: mock.start() for name, mock in mock_services.items()}

        with patch.multiple("services.factory", **mocks):
            create_services(tmp_path, {})
            mocks["logger"].info.assert_called_once()
            call_kwargs = mocks["logger"].info.call_args.kwargs
            assert "service_count" in call_kwargs

        for mock in mock_services.values():
            mock.stop()

    def test_create_services_wires_auth_service(self, mock_services, tmp_path):
        """create_services should wire AuthService with db_service."""
        mocks = {name: mock.start() for name, mock in mock_services.items()}
        mock_db_service = MagicMock()
        mocks["DatabaseService"].return_value = mock_db_service

        with patch.multiple("services.factory", **mocks):
            create_services(tmp_path, {})
            mocks["AuthService"].assert_called_once_with(db_service=mock_db_service)

        for mock in mock_services.values():
            mock.stop()

    def test_create_services_wires_metrics_service(self, mock_services, tmp_path):
        """create_services should wire MetricsService with dependencies."""
        mocks = {name: mock.start() for name, mock in mock_services.items()}
        mock_ssh = MagicMock()
        mock_db = MagicMock()
        mock_server = MagicMock()
        mocks["SSHService"].return_value = mock_ssh
        mocks["DatabaseService"].return_value = mock_db
        mocks["ServerService"].return_value = mock_server

        with patch.multiple("services.factory", **mocks):
            create_services(tmp_path, {})
            mocks["MetricsService"].assert_called_once_with(
                ssh_service=mock_ssh,
                db_service=mock_db,
                server_service=mock_server,
            )

        for mock in mock_services.values():
            mock.stop()

    def test_create_services_wires_command_router(self, mock_services, tmp_path):
        """create_services should wire CommandRouter with prefer_agent=True."""
        mocks = {name: mock.start() for name, mock in mock_services.items()}

        with patch.multiple("services.factory", **mocks):
            create_services(tmp_path, {})
            call_kwargs = mocks["CommandRouter"].call_args.kwargs
            assert call_kwargs["prefer_agent"] is True

        for mock in mock_services.values():
            mock.stop()

    def test_create_services_wires_retention_service(self, mock_services, tmp_path):
        """create_services should wire RetentionService with db and auth."""
        mocks = {name: mock.start() for name, mock in mock_services.items()}
        mock_db = MagicMock()
        mock_auth = MagicMock()
        mocks["DatabaseService"].return_value = mock_db
        mocks["AuthService"].return_value = mock_auth

        with patch.multiple("services.factory", **mocks):
            create_services(tmp_path, {})
            mocks["RetentionService"].assert_called_once_with(
                db_service=mock_db,
                auth_service=mock_auth,
            )

        for mock in mock_services.values():
            mock.stop()

    def test_create_services_accepts_path_object(self, mock_services, tmp_path):
        """create_services should accept Path object for data_directory."""
        mocks = {name: mock.start() for name, mock in mock_services.items()}

        with patch.multiple("services.factory", **mocks):
            # Should not raise
            result = create_services(Path(tmp_path), {})
            assert result is not None

        for mock in mock_services.values():
            mock.stop()

"""Service factory for creating and wiring all application services."""

from pathlib import Path
from typing import Any

import structlog

from database.connection import db_manager
from services.app_service import AppService
from services.auth_service import AuthService
from services.activity_service import ActivityService
from services.agent_service import AgentService
from services.agent_manager import AgentManager
from services.agent_lifecycle import AgentLifecycleManager
from services.agent_websocket import AgentWebSocketHandler
from services.command_router import CommandRouter
from services.backup_service import BackupService
from services.dashboard_service import DashboardService
from services.database_service import DatabaseService
from services.database import DatabaseConnection, AgentDatabaseService
from services.deployment import DeploymentService
from services.deployment.ssh_executor import AgentExecutor
from services.marketplace_service import MarketplaceService
from services.metrics_service import MetricsService
from services.monitoring_service import MonitoringService
from services.server_service import ServerService
from services.session_service import SessionService
from services.settings_service import SettingsService
from services.notification_service import NotificationService
from services.retention_service import RetentionService
from services.ssh_service import SSHService

logger = structlog.get_logger("service_factory")


def create_services(data_directory: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Create and wire all application services.

    Args:
        data_directory: Path to the data directory.
        config: Application configuration dictionary.

    Returns:
        Dictionary of service name to service instance.
    """
    # Ensure shared database components use the resolved configuration
    db_manager.set_data_directory(data_directory)
    database_service = DatabaseService(data_directory=data_directory)

    # Core services
    app_service = AppService()
    auth_service = AuthService(db_service=database_service)
    session_service = SessionService(db_service=database_service)
    ssh_service = SSHService()
    monitoring_service = MonitoringService()
    server_service = ServerService(db_service=database_service)
    settings_service = SettingsService(db_service=database_service)
    marketplace_service = MarketplaceService()
    backup_service = BackupService(db_service=database_service)
    activity_service = ActivityService(db_service=database_service)
    notification_service = NotificationService(db_service=database_service)
    retention_service = RetentionService(
        db_service=database_service, auth_service=auth_service
    )

    metrics_service = MetricsService(
        ssh_service=ssh_service,
        db_service=database_service,
        server_service=server_service,
    )

    # Agent services for WebSocket-based agent communication
    db_connection = DatabaseConnection(data_directory=data_directory)
    agent_db_service = AgentDatabaseService(db_connection)
    agent_service = AgentService(
        db_service=database_service,
        settings_service=settings_service,
        agent_db=agent_db_service,
    )

    # Lifecycle manager for health monitoring and updates
    agent_lifecycle = AgentLifecycleManager(agent_db=agent_db_service)

    # Agent manager with lifecycle integration
    agent_manager = AgentManager(
        agent_db=agent_db_service,
        lifecycle_manager=agent_lifecycle,
    )
    agent_websocket_handler = AgentWebSocketHandler(agent_service, agent_manager)

    # Command router for agent-first execution with SSH fallback
    command_router = CommandRouter(
        agent_service=agent_service,
        agent_manager=agent_manager,
        server_service=server_service,
        ssh_service=ssh_service,
        prefer_agent=True,
    )

    # Agent executor for deployment (agent-only, no SSH fallback)
    agent_executor = AgentExecutor(command_router)

    # Deployment service using agent with Docker RPC methods
    deployment_service = DeploymentService(
        ssh_service=ssh_service,
        server_service=server_service,
        marketplace_service=marketplace_service,
        db_service=database_service,
        activity_service=activity_service,
        executor=agent_executor,
        agent_manager=agent_manager,
        agent_service=agent_service,
    )

    dashboard_service = DashboardService(
        server_service=server_service,
        deployment_service=deployment_service,
        metrics_service=metrics_service,
        activity_service=activity_service,
    )

    logger.info("All services created", service_count=22)

    return {
        "config": config,
        "database_service": database_service,
        "app_service": app_service,
        "auth_service": auth_service,
        "session_service": session_service,
        "ssh_service": ssh_service,
        "monitoring_service": monitoring_service,
        "server_service": server_service,
        "settings_service": settings_service,
        "marketplace_service": marketplace_service,
        "backup_service": backup_service,
        "activity_service": activity_service,
        "notification_service": notification_service,
        "retention_service": retention_service,
        "deployment_service": deployment_service,
        "metrics_service": metrics_service,
        "dashboard_service": dashboard_service,
        "agent_service": agent_service,
        "agent_manager": agent_manager,
        "agent_lifecycle": agent_lifecycle,
        "agent_websocket_handler": agent_websocket_handler,
        "command_router": command_router,
    }

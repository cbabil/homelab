"""Service factory for creating and wiring all application services."""

from pathlib import Path
from typing import Any

import structlog

from services.activity_service import ActivityService
from services.agent_lifecycle import AgentLifecycleManager
from services.agent_manager import AgentManager
from services.agent_service import AgentService
from services.agent_websocket import AgentWebSocketHandler
from services.app_service import AppService
from services.auth_service import AuthService
from services.backup_service import BackupService
from services.command_router import CommandRouter
from services.csrf_service import CSRFService
from services.dashboard_service import DashboardService
from services.database import AgentDatabaseService, DatabaseConnection
from services.database_service import DatabaseService
from services.deployment import DeploymentService
from services.deployment.ssh_executor import AgentExecutor
from services.marketplace_service import MarketplaceService
from services.metrics_service import MetricsService
from services.monitoring_service import MonitoringService
from services.notification_service import NotificationService
from services.rate_limit_service import RateLimitService
from services.retention_service import RetentionService
from services.server_service import ServerService
from services.service_log import LogService
from services.session_service import SessionService
from services.settings_service import SettingsService
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
    database_service = DatabaseService(data_directory=data_directory)

    # Shared database connection for all raw-aiosqlite services
    db_connection = DatabaseConnection(data_directory=data_directory)

    # Log service (used by auth, monitoring, retention, audit, app)
    log_service = LogService(connection=db_connection)

    # Core services
    app_service = AppService(connection=db_connection, log_service=log_service)
    auth_service = AuthService(db_service=database_service, log_service=log_service)
    session_service = SessionService(db_service=database_service)
    rate_limit_service = RateLimitService(db_service=database_service)
    csrf_service = CSRFService(db_service=database_service)
    ssh_service = SSHService()
    monitoring_service = MonitoringService(log_service=log_service)
    server_service = ServerService(db_service=database_service)
    settings_service = SettingsService(db_service=database_service)
    marketplace_service = MarketplaceService(connection=db_connection)
    backup_service = BackupService(db_service=database_service)
    activity_service = ActivityService(db_service=database_service)
    notification_service = NotificationService(db_service=database_service)
    retention_service = RetentionService(
        db_service=database_service,
        auth_service=auth_service,
        log_service=log_service,
    )

    metrics_service = MetricsService(
        ssh_service=ssh_service,
        db_service=database_service,
        server_service=server_service,
    )

    # Agent services for WebSocket-based agent communication
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

    logger.info("All services created", service_count=24)

    return {
        "config": config,
        "database_service": database_service,
        "log_service": log_service,
        "app_service": app_service,
        "auth_service": auth_service,
        "session_service": session_service,
        "rate_limit_service": rate_limit_service,
        "csrf_service": csrf_service,
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

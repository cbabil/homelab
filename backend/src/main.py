"""Homelab Assistant MCP Server Entry Point."""

import structlog
from fastmcp import FastMCP

from database.connection import db_manager
from services.app_service import AppService
from services.auth_service import AuthService
from services.activity_service import ActivityService
from services.backup_service import BackupService
from services.catalog_service import CatalogService
from services.dashboard_service import DashboardService
from services.database_service import DatabaseService
from services.deployment_service import DeploymentService
from services.metrics_service import MetricsService
from services.monitoring_service import MonitoringService
from services.preparation_service import PreparationService
from services.retention_service import RetentionService
from services.server_service import ServerService
from services.settings_service import SettingsService
from services.ssh_service import SSHService
from lib.tool_loader import register_all_tools
from lib.logging_config import setup_logging
from lib.config import load_config, resolve_data_directory

# Setup structured logging
setup_logging()
logger = structlog.get_logger("main")

# Initialize configuration
config = load_config()
data_directory = resolve_data_directory(config)

# Ensure shared database components use the resolved configuration
db_manager.set_data_directory(data_directory)
database_service = DatabaseService(data_directory=data_directory)

logger.info(
    "Configuration loaded",
    data_directory=str(data_directory),
    app_env=config.get("app_env"),
)

app_service = AppService()
auth_service = AuthService(db_service=database_service)
ssh_service = SSHService()
monitoring_service = MonitoringService()
server_service = ServerService()
retention_service = RetentionService(db_service=database_service, auth_service=auth_service)
settings_service = SettingsService(db_service=database_service)

# Additional services
catalog_dirs = [str(data_directory / "catalog")]
catalog_service = CatalogService(catalog_dirs=catalog_dirs)
catalog_service.load_catalog()

deployment_service = DeploymentService(
    ssh_service=ssh_service,
    server_service=server_service,
    catalog_service=catalog_service,
    db_service=database_service
)

backup_service = BackupService(db_service=database_service)
activity_service = ActivityService(db_service=database_service)

metrics_service = MetricsService(
    ssh_service=ssh_service,
    db_service=database_service,
    server_service=server_service
)

dashboard_service = DashboardService(
    server_service=server_service,
    deployment_service=deployment_service,
    metrics_service=metrics_service,
    activity_service=activity_service
)

preparation_service = PreparationService(
    ssh_service=ssh_service,
    server_service=server_service,
    db_service=database_service
)

# Create FastMCP app
app = FastMCP(
    name="homelab-assistant",
    version="0.1.0",
    instructions="Homelab management and automation server"
)

# Add CORS middleware (if possible with FastMCP)
# Note: This might need to be handled at the underlying FastAPI/Uvicorn level

# Register modular tools dynamically
tool_dependencies = {
    "config": config,
    "app_service": app_service,
    "auth_service": auth_service,
    "ssh_service": ssh_service,
    "server_service": server_service,
    "monitoring_service": monitoring_service,
    "retention_service": retention_service,
    "settings_service": settings_service,
    "database_service": database_service,
    "catalog_service": catalog_service,
    "deployment_service": deployment_service,
    "backup_service": backup_service,
    "activity_service": activity_service,
    "metrics_service": metrics_service,
    "dashboard_service": dashboard_service,
    "preparation_service": preparation_service,
}

register_all_tools(app, config, tool_dependencies)


if __name__ == "__main__":
    import asyncio
    from starlette.middleware.cors import CORSMiddleware
    from starlette.middleware import Middleware
    
    # Configure CORS middleware
    cors_middleware = Middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["mcp-session-id"]
    )

    logger.info("FastMCP HTTP server initialized", version="0.1.0")
    asyncio.run(app.run_http_async(host="0.0.0.0", port=8000, middleware=[cors_middleware]))

"""Tomo MCP Server Entry Point."""

import structlog
from fastmcp import FastMCP

from lib.config import DEFAULT_ENV_VALUES, load_config, resolve_data_directory
from lib.logging_config import setup_logging
from lib.tool_loader import register_all_tools
from services.factory import create_services

# Setup structured logging
setup_logging()
logger = structlog.get_logger("main")

# Initialize configuration
config = load_config()
data_directory = resolve_data_directory(config)

logger.info(
    "Configuration loaded",
    data_directory=str(data_directory),
    app_env=config.get("app_env"),
)

# Create all services
services = create_services(data_directory, config)

# Create FastMCP app
app = FastMCP(
    name="tomo",
    version=config.get("version", DEFAULT_ENV_VALUES["VERSION"]),
    instructions="Tomo management and automation server",
)

# Register modular tools dynamically
register_all_tools(app, config, services)

# Export for WebSocket handler access
agent_websocket_handler = services["agent_websocket_handler"]
agent_lifecycle = services["agent_lifecycle"]
database_service = services["database_service"]


if __name__ == "__main__":
    import asyncio
    import os

    import uvicorn
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    from starlette.routing import WebSocketRoute

    # Run database migrations and initializations
    async def _run_migrations():
        await database_service.run_installed_apps_migrations()
        await database_service.run_users_migrations()
        await database_service.initialize_system_info_table()
        await database_service.initialize_users_table()
        await database_service.initialize_sessions_table()
        await database_service.initialize_account_locks_table()
        await database_service.initialize_notifications_table()
        await database_service.initialize_retention_settings_table()
        await database_service.initialize_servers_table()
        await database_service.initialize_agents_table()
        await database_service.initialize_installed_apps_table()
        await database_service.initialize_metrics_tables()

    asyncio.run(_run_migrations())

    # Configure CORS origins from environment variable
    default_origins = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003"
    allowed_origins = os.getenv("ALLOWED_ORIGINS", default_origins).split(",")
    allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

    # Reject wildcard with credentials (browsers block this anyway)
    if "*" in allowed_origins and len(allowed_origins) > 1:
        logger.warning(
            "Wildcard '*' mixed with specific origins; removing wildcard",
            origins=allowed_origins,
        )
        allowed_origins = [o for o in allowed_origins if o != "*"]
    if "*" in allowed_origins:
        env = os.getenv("APP_ENV", "production").lower()
        if env == "production":
            logger.error(
                "Wildcard CORS origin rejected in production mode"
            )
            allowed_origins = [o for o in allowed_origins if o != "*"] or [
                "http://localhost:3000"
            ]
        else:
            logger.warning(
                "Wildcard CORS origin used — restrict via ALLOWED_ORIGINS in production"
            )

    # Configure CORS middleware
    cors_middleware = Middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials="*" not in allowed_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "mcp-session-id"],
        expose_headers=["mcp-session-id"],
        max_age=3600,
    )

    # Get Starlette app with MCP routes
    starlette_app = app.http_app(
        path="/mcp",
        stateless_http=True,
        json_response=True,
        middleware=[cors_middleware],
    )

    # Add WebSocket route for agent connections
    starlette_app.routes.append(
        WebSocketRoute("/ws/agent", agent_websocket_handler.handle_connection)
    )

    # Add lifecycle event handlers
    agent_service = services["agent_service"]
    agent_manager = services["agent_manager"]

    @starlette_app.on_event("startup")
    async def startup_lifecycle():
        """Start agent lifecycle manager and rotation scheduler on app startup."""
        logger.info("Starting agent lifecycle manager")
        # Reset any stale CONNECTED statuses from previous run
        reset_count = await agent_service.reset_stale_agent_statuses()
        if reset_count > 0:
            logger.info(f"Reset {reset_count} stale agent status(es) to DISCONNECTED")
        await agent_lifecycle.start()

        # Start automatic token rotation scheduler
        logger.info("Starting token rotation scheduler")
        agent_service.set_rotation_callback(agent_manager.send_rotation_request)
        await agent_service.start_rotation_scheduler(check_interval=3600)  # 1 hour

    @starlette_app.on_event("shutdown")
    async def shutdown_lifecycle():
        """Stop agent lifecycle manager and rotation scheduler on app shutdown."""
        logger.info("Stopping token rotation scheduler")
        await agent_service.stop_rotation_scheduler()
        logger.info("Stopping agent lifecycle manager")
        await agent_lifecycle.stop()

    logger.info(
        "FastMCP HTTP server initialized",
        version=config.get("version", DEFAULT_ENV_VALUES["VERSION"]),
        allowed_origins=allowed_origins,
        mcp_path="/mcp",
        ws_path="/ws/agent",
    )

    uvicorn.run(starlette_app, host="0.0.0.0", port=8000)

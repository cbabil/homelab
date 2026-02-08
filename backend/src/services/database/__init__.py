"""Database services package.

Provides modular database services for the tomo application.
Each service handles a specific domain while sharing a common connection manager.
"""

from .agent_service import AgentDatabaseService
from .app_service import AppDatabaseService
from .base import (
    ALLOWED_INSTALLATION_COLUMNS,
    ALLOWED_SERVER_COLUMNS,
    ALLOWED_SYSTEM_INFO_COLUMNS,
    DatabaseConnection,
)
from .export_service import ExportDatabaseService
from .metrics_service import MetricsDatabaseService
from .registration_code_service import RegistrationCodeDatabaseService
from .schema_init import SchemaInitializer
from .server_service import ServerDatabaseService
from .session_service import SessionDatabaseService
from .system_service import SystemDatabaseService
from .user_service import UserDatabaseService

__all__ = [
    # Connection
    "DatabaseConnection",
    # Services
    "UserDatabaseService",
    "ServerDatabaseService",
    "SessionDatabaseService",
    "AppDatabaseService",
    "MetricsDatabaseService",
    "SystemDatabaseService",
    "ExportDatabaseService",
    "AgentDatabaseService",
    "RegistrationCodeDatabaseService",
    "SchemaInitializer",
    # Column whitelists
    "ALLOWED_SERVER_COLUMNS",
    "ALLOWED_INSTALLATION_COLUMNS",
    "ALLOWED_SYSTEM_INFO_COLUMNS",
]

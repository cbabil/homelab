"""Database services package.

Provides modular database services for the tomo application.
Each service handles a specific domain while sharing a common connection manager.
"""

from .base import (
    DatabaseConnection,
    ALLOWED_SERVER_COLUMNS,
    ALLOWED_INSTALLATION_COLUMNS,
    ALLOWED_SYSTEM_INFO_COLUMNS,
)
from .user_service import UserDatabaseService
from .server_service import ServerDatabaseService
from .session_service import SessionDatabaseService
from .app_service import AppDatabaseService
from .metrics_service import MetricsDatabaseService
from .system_service import SystemDatabaseService
from .export_service import ExportDatabaseService
from .agent_service import AgentDatabaseService
from .registration_code_service import RegistrationCodeDatabaseService
from .schema_init import SchemaInitializer

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

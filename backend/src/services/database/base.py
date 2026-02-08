"""Database Connection Manager.

Provides the base async database connection manager and column whitelists
for SQL injection prevention.
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite
import structlog

logger = structlog.get_logger("database")

# Whitelisted columns for dynamic updates (SQL injection prevention)
ALLOWED_SERVER_COLUMNS = frozenset(
    {
        "name",
        "host",
        "port",
        "username",
        "auth_type",
        "status",
        "last_connected",
        "system_info",
        "docker_installed",
        "system_info_updated_at",
    }
)
ALLOWED_INSTALLATION_COLUMNS = frozenset(
    {
        "status",
        "container_id",
        "container_name",
        "config",
        "started_at",
        "error_message",
        "progress",
        "step_durations",
        "step_started_at",
        "networks",
        "named_volumes",
        "bind_mounts",
    }
)
ALLOWED_AGENT_COLUMNS = frozenset(
    {
        "server_id",
        "token_hash",
        "version",
        "status",
        "last_seen",
        "registered_at",
        "config",
        "pending_token_hash",
        "token_issued_at",
        "token_expires_at",
    }
)
ALLOWED_SYSTEM_INFO_COLUMNS = frozenset(
    {
        "app_name",
        "is_setup",
        "setup_completed_at",
        "setup_by_user_id",
        "license_type",
        "license_key",
        "license_expires_at",
    }
)


class DatabaseConnection:
    """Async database connection manager."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        data_directory: str | Path | None = None,
    ):
        """Initialize database connection with path to tomo.db.

        Args:
            db_path: Direct path to database file.
            data_directory: Directory containing tomo.db.

        Raises:
            ValueError: If both db_path and data_directory are provided.
        """
        backend_root = Path(__file__).resolve().parents[3]

        if db_path is not None and data_directory is not None:
            raise ValueError("Provide either db_path or data_directory, not both")

        if db_path is not None:
            resolved_path = Path(db_path)
            if not resolved_path.is_absolute():
                resolved_path = (backend_root / resolved_path).resolve()
        else:
            directory = Path(
                data_directory
                if data_directory is not None
                else os.getenv("DATA_DIRECTORY", "data")
            )
            if not directory.is_absolute():
                directory = (backend_root / directory).resolve()
            resolved_path = directory / "tomo.db"

        self.db_path = str(resolved_path)
        logger.info("Database connection initialized", db_path=self.db_path)

    @property
    def path(self) -> str:
        """Get the database file path."""
        return self.db_path

    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[aiosqlite.Connection]:
        """Get async database connection with automatic cleanup.

        Yields:
            aiosqlite connection with row factory enabled.

        Raises:
            Exception: Re-raises any exception after rolling back.
        """
        async with aiosqlite.connect(self.db_path) as connection:
            connection.row_factory = aiosqlite.Row
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

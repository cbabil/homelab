"""
Database Connection Management

Provides async SQLAlchemy connection management for SQLite database.
Handles engine creation, session management, and connection lifecycle.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

logger = structlog.get_logger("database")

Base = declarative_base()


class DatabaseManager:
    """Async database connection manager for SQLite."""

    def __init__(self, data_directory: str = "data"):
        self._default_directory = data_directory
        self._override_directory: str | None = None
        self.engine = None
        self.session_factory = None
        self._configure_paths()

    def _configure_paths(self):
        backend_root = Path(__file__).resolve().parents[2]
        raw_directory = self._override_directory or os.getenv(
            "DATA_DIRECTORY", self._default_directory
        )
        configured_path = Path(raw_directory)

        if not configured_path.is_absolute():
            configured_path = (backend_root / configured_path).resolve()

        self.data_directory = str(configured_path)
        self.database_path = str(configured_path / "tomo.db")
        self.database_url = f"sqlite+aiosqlite:///{self.database_path}"

    def set_data_directory(self, data_directory: str | Path) -> None:
        """Override the data directory and reset cached connections."""

        resolved = Path(data_directory).resolve()
        self._override_directory = str(resolved)
        # Reset engine/session so they are recreated with the new path
        self.engine = None
        self.session_factory = None
        self._configure_paths()

    async def initialize(self):
        """Initialize database engine and session factory."""
        self._configure_paths()
        os.makedirs(self.data_directory, exist_ok=True)

        self.engine = create_async_engine(self.database_url, echo=False, future=True)

        self.session_factory = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

        logger.info("Database initialized", path=self.database_path)

    @asynccontextmanager
    async def get_session(self):
        """Get async database session with automatic cleanup."""
        if not self.session_factory:
            await self.initialize()

        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


db_manager = DatabaseManager()

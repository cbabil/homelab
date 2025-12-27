"""Marketplace Service

Provides data access and business logic for marketplace repository management."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

import structlog
from sqlalchemy import delete, select, update

from database.connection import db_manager
from init_db.schema_marketplace import initialize_marketplace_database
from models.marketplace import (
    MarketplaceRepo,
    MarketplaceRepoTable,
    MarketplaceAppTable,
    RepoType,
    RepoStatus,
)

logger = structlog.get_logger("marketplace_service")


class MarketplaceService:
    """Service for managing marketplace repositories."""

    def __init__(self) -> None:
        self._initialized = False
        logger.info("Marketplace service initialized")

    async def _ensure_initialized(self) -> None:
        """Ensure the marketplace database is initialized."""
        if not self._initialized:
            await initialize_marketplace_database()
            self._initialized = True

    async def add_repo(
        self,
        name: str,
        url: str,
        repo_type: RepoType,
        branch: str = "main"
    ) -> MarketplaceRepo:
        """Create a new marketplace repository.

        Args:
            name: Human-readable repository name
            url: Git repository URL
            repo_type: Repository type (official/community/personal)
            branch: Git branch to sync from (default: "main")

        Returns:
            Created MarketplaceRepo instance
        """
        await self._ensure_initialized()

        repo_id = uuid.uuid4().hex[:8]
        now = datetime.utcnow()

        async with db_manager.get_session() as session:
            repo_table = MarketplaceRepoTable(
                id=repo_id,
                name=name,
                url=url,
                branch=branch,
                repo_type=repo_type.value,
                enabled=True,
                status=RepoStatus.ACTIVE.value,
                last_synced=None,
                app_count=0,
                error_message=None,
                created_at=now,
                updated_at=now,
            )
            session.add(repo_table)
            await session.flush()

            repo = self._repo_from_table(repo_table)

        logger.info("Repository added", repo_id=repo_id, name=name, repo_type=repo_type.value)
        return repo

    async def get_repos(self, enabled_only: bool = False) -> List[MarketplaceRepo]:
        """Get all marketplace repositories.

        Args:
            enabled_only: If True, only return enabled repositories

        Returns:
            List of MarketplaceRepo instances
        """
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            query = select(MarketplaceRepoTable)
            if enabled_only:
                query = query.where(MarketplaceRepoTable.enabled == True)  # noqa: E712

            result = await session.execute(query)
            rows = result.scalars().all()

        repos = [self._repo_from_table(row) for row in rows]
        logger.debug("Fetched repositories", count=len(repos), enabled_only=enabled_only)
        return repos

    async def get_repo(self, repo_id: str) -> Optional[MarketplaceRepo]:
        """Get a single repository by ID.

        Args:
            repo_id: Repository identifier

        Returns:
            MarketplaceRepo instance if found, None otherwise
        """
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            result = await session.execute(
                select(MarketplaceRepoTable).where(MarketplaceRepoTable.id == repo_id)
            )
            row = result.scalar_one_or_none()

        if not row:
            logger.warning("Repository not found", repo_id=repo_id)
            return None

        repo = self._repo_from_table(row)
        logger.debug("Retrieved repository", repo_id=repo_id)
        return repo

    async def remove_repo(self, repo_id: str) -> bool:
        """Delete a repository and all its associated apps.

        Args:
            repo_id: Repository identifier

        Returns:
            True if deleted, False if not found
        """
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            # First, delete all apps associated with this repo
            await session.execute(
                delete(MarketplaceAppTable).where(MarketplaceAppTable.repo_id == repo_id)
            )

            # Then delete the repository
            result = await session.execute(
                delete(MarketplaceRepoTable).where(MarketplaceRepoTable.id == repo_id)
            )
            deleted = result.rowcount > 0

        if deleted:
            logger.info("Repository removed", repo_id=repo_id)
        else:
            logger.warning("Repository not found for removal", repo_id=repo_id)

        return deleted

    async def toggle_repo(self, repo_id: str, enabled: bool) -> bool:
        """Enable or disable a repository.

        Args:
            repo_id: Repository identifier
            enabled: True to enable, False to disable

        Returns:
            True if updated, False if not found
        """
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            result = await session.execute(
                update(MarketplaceRepoTable)
                .where(MarketplaceRepoTable.id == repo_id)
                .values(enabled=enabled, updated_at=datetime.utcnow())
            )
            updated = result.rowcount > 0

        if updated:
            action = "enabled" if enabled else "disabled"
            logger.info(f"Repository {action}", repo_id=repo_id)
        else:
            logger.warning("Repository not found for toggle", repo_id=repo_id)

        return updated

    @staticmethod
    def _repo_from_table(row: MarketplaceRepoTable) -> MarketplaceRepo:
        """Convert a table row to a MarketplaceRepo model.

        Args:
            row: SQLAlchemy MarketplaceRepoTable instance

        Returns:
            MarketplaceRepo Pydantic model
        """
        return MarketplaceRepo(
            id=row.id,
            name=row.name,
            url=row.url,
            branch=row.branch,
            repo_type=RepoType(row.repo_type),
            enabled=row.enabled,
            status=RepoStatus(row.status),
            last_synced=row.last_synced,
            app_count=row.app_count,
            error_message=row.error_message,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

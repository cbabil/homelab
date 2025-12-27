"""Marketplace Service

Provides data access and business logic for marketplace repository management."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import structlog
from sqlalchemy import delete, select, update

from database.connection import db_manager
from init_db.schema_marketplace import initialize_marketplace_database
from lib.git_sync import GitSync
from models.marketplace import (
    MarketplaceApp,
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

    async def sync_repo(
        self,
        repo_id: str,
        local_path: Optional[Path] = None
    ) -> List[MarketplaceApp]:
        """Sync apps from a repository.

        Args:
            repo_id: Repository identifier
            local_path: Optional local path for testing (skips Git clone/pull)

        Returns:
            List of synced MarketplaceApp instances

        Raises:
            ValueError: If repository not found
            RuntimeError: If Git operations fail
        """
        await self._ensure_initialized()

        repo = await self.get_repo(repo_id)
        if not repo:
            raise ValueError(f"Repository {repo_id} not found")

        # Update status to SYNCING
        async with db_manager.get_session() as session:
            await session.execute(
                update(MarketplaceRepoTable)
                .where(MarketplaceRepoTable.id == repo_id)
                .values(status=RepoStatus.SYNCING.value)
            )

        git_sync = GitSync()
        apps: List[MarketplaceApp] = []

        try:
            # Use local path for testing or clone from URL
            if local_path:
                repo_path = Path(local_path)
            else:
                repo_path = git_sync.clone_or_pull(repo.url, repo.branch)

            # Find and parse app files
            app_files = git_sync.find_app_files(repo_path)

            for app_file in app_files:
                app = git_sync.load_app_from_file(app_file, repo_id)
                if app:
                    apps.append(app)
                    await self._upsert_app(app)

            # Update repo with success
            async with db_manager.get_session() as session:
                await session.execute(
                    update(MarketplaceRepoTable)
                    .where(MarketplaceRepoTable.id == repo_id)
                    .values(
                        status=RepoStatus.ACTIVE.value,
                        last_synced=datetime.utcnow(),
                        app_count=len(apps),
                        error_message=None
                    )
                )

            logger.info("Repository synced", repo_id=repo_id, app_count=len(apps))

        except Exception as e:
            # Update repo with error
            async with db_manager.get_session() as session:
                await session.execute(
                    update(MarketplaceRepoTable)
                    .where(MarketplaceRepoTable.id == repo_id)
                    .values(
                        status=RepoStatus.ERROR.value,
                        error_message=str(e)
                    )
                )
            logger.error("Repository sync failed", repo_id=repo_id, error=str(e))
            raise

        finally:
            if not local_path:
                git_sync.cleanup()

        return apps

    async def _upsert_app(self, app: MarketplaceApp) -> None:
        """Insert or update an app in the database.

        Args:
            app: MarketplaceApp instance to upsert
        """
        docker_json = app.docker.model_dump_json()
        req_json = app.requirements.model_dump_json()
        tags_json = json.dumps(app.tags)

        async with db_manager.get_session() as session:
            # Check if exists
            result = await session.execute(
                select(MarketplaceAppTable).where(MarketplaceAppTable.id == app.id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update
                await session.execute(
                    update(MarketplaceAppTable)
                    .where(MarketplaceAppTable.id == app.id)
                    .values(
                        name=app.name,
                        description=app.description,
                        long_description=app.long_description,
                        version=app.version,
                        category=app.category,
                        tags=tags_json,
                        icon=app.icon,
                        author=app.author,
                        license=app.license,
                        repository=app.repository,
                        documentation=app.documentation,
                        docker_config=docker_json,
                        requirements=req_json,
                        updated_at=datetime.utcnow()
                    )
                )
            else:
                # Insert
                table_row = MarketplaceAppTable(
                    id=app.id,
                    name=app.name,
                    description=app.description,
                    long_description=app.long_description,
                    version=app.version,
                    category=app.category,
                    tags=tags_json,
                    icon=app.icon,
                    author=app.author,
                    license=app.license,
                    repository=app.repository,
                    documentation=app.documentation,
                    repo_id=app.repo_id,
                    docker_config=docker_json,
                    requirements=req_json
                )
                session.add(table_row)

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

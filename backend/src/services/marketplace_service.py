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
    AppRating,
    MarketplaceRepoTable,
    MarketplaceAppTable,
    AppRatingTable,
    RepoType,
    RepoStatus,
    DockerConfig,
    AppRequirements,
)

logger = structlog.get_logger("marketplace_service")

# CasaOS App Store configuration (primary source)
CASAOS_APPSTORE_URL = "https://github.com/IceWhaleTech/CasaOS-AppStore"
CASAOS_APPSTORE_NAME = "CasaOS App Store"
CASAOS_APPSTORE_BRANCH = "main"

# Legacy official marketplace (kept for backwards compatibility)
OFFICIAL_MARKETPLACE_URL = "https://github.com/cbabil/tomo-marketplace"
OFFICIAL_MARKETPLACE_NAME = "Tomo Marketplace"
OFFICIAL_MARKETPLACE_BRANCH = "master"


class MarketplaceService:
    """Service for managing marketplace repositories."""

    def __init__(self) -> None:
        self._initialized = False
        logger.info("Marketplace service initialized")

    async def _ensure_initialized(self) -> None:
        """Ensure the marketplace database is initialized with official marketplace."""
        if not self._initialized:
            await initialize_marketplace_database()
            await self._ensure_official_marketplace()
            self._initialized = True

    async def _ensure_official_marketplace(self) -> None:
        """Add the CasaOS app store and official marketplace if not already present."""
        from sqlalchemy.exc import IntegrityError

        async with db_manager.get_session() as session:
            # Check if CasaOS app store exists
            result = await session.execute(
                select(MarketplaceRepoTable).where(MarketplaceRepoTable.id == "casaos")
            )
            casaos_exists = result.scalar_one_or_none()

            if not casaos_exists:
                # Add CasaOS app store as primary source
                now = datetime.utcnow()
                casaos_repo = MarketplaceRepoTable(
                    id="casaos",
                    name=CASAOS_APPSTORE_NAME,
                    url=CASAOS_APPSTORE_URL,
                    branch=CASAOS_APPSTORE_BRANCH,
                    repo_type=RepoType.OFFICIAL.value,
                    enabled=True,
                    status=RepoStatus.ACTIVE.value,
                    last_synced=None,
                    app_count=0,
                    error_message=None,
                    created_at=now,
                    updated_at=now,
                )
                session.add(casaos_repo)
                try:
                    await session.commit()
                    logger.info(
                        "CasaOS app store added",
                        repo_id="casaos",
                        url=CASAOS_APPSTORE_URL,
                    )
                except IntegrityError:
                    await session.rollback()
                    logger.debug("CasaOS app store already exists")

            # Check if legacy official marketplace exists
            result = await session.execute(
                select(MarketplaceRepoTable).where(
                    MarketplaceRepoTable.id == "official"
                )
            )
            official_exists = result.scalar_one_or_none()

            if not official_exists:
                # Add legacy official marketplace (disabled by default)
                now = datetime.utcnow()
                repo_table = MarketplaceRepoTable(
                    id="official",
                    name=OFFICIAL_MARKETPLACE_NAME,
                    url=OFFICIAL_MARKETPLACE_URL,
                    branch=OFFICIAL_MARKETPLACE_BRANCH,
                    repo_type=RepoType.COMMUNITY.value,
                    enabled=True,
                    status=RepoStatus.ACTIVE.value,
                    last_synced=None,
                    app_count=0,
                    error_message=None,
                    created_at=now,
                    updated_at=now,
                )
                session.add(repo_table)
                try:
                    await session.commit()
                    logger.info(
                        "Official marketplace added (disabled)",
                        repo_id="official",
                        url=OFFICIAL_MARKETPLACE_URL,
                    )
                except IntegrityError:
                    await session.rollback()
                    logger.debug("Official marketplace already exists")

    async def add_repo(
        self, name: str, url: str, repo_type: RepoType, branch: str = "main"
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

        logger.info(
            "Repository added", repo_id=repo_id, name=name, repo_type=repo_type.value
        )
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
        logger.debug(
            "Fetched repositories", count=len(repos), enabled_only=enabled_only
        )
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
                delete(MarketplaceAppTable).where(
                    MarketplaceAppTable.repo_id == repo_id
                )
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
        self, repo_id: str, local_path: Optional[Path] = None
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

            # Detect repository format and parse accordingly
            is_casaos_format = self._is_casaos_repo(repo_path)

            if is_casaos_format:
                # CasaOS format: Apps/<AppName>/docker-compose.yml
                app_files = git_sync.find_casaos_app_files(repo_path)
                for app_file in app_files:
                    app = git_sync.load_casaos_app(app_file, repo_id)
                    if app:
                        apps.append(app)
                        await self._upsert_app(app)
                logger.info(
                    "Synced CasaOS format repo", repo_id=repo_id, app_count=len(apps)
                )
            else:
                # Legacy format: apps/<app>/app.yaml
                app_files = git_sync.find_app_files(repo_path)
                for app_file in app_files:
                    app = git_sync.load_app_from_file(app_file, repo_id)
                    if app:
                        apps.append(app)
                        await self._upsert_app(app)
                logger.info(
                    "Synced legacy format repo", repo_id=repo_id, app_count=len(apps)
                )

            # Update repo with success
            async with db_manager.get_session() as session:
                await session.execute(
                    update(MarketplaceRepoTable)
                    .where(MarketplaceRepoTable.id == repo_id)
                    .values(
                        status=RepoStatus.ACTIVE.value,
                        last_synced=datetime.utcnow(),
                        app_count=len(apps),
                        error_message=None,
                    )
                )

            logger.info("Repository synced", repo_id=repo_id, app_count=len(apps))

        except Exception as e:
            # Update repo with error
            async with db_manager.get_session() as session:
                await session.execute(
                    update(MarketplaceRepoTable)
                    .where(MarketplaceRepoTable.id == repo_id)
                    .values(status=RepoStatus.ERROR.value, error_message=str(e))
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
                        maintainers=json.dumps(app.maintainers),
                        repository=app.repository,
                        documentation=app.documentation,
                        docker_config=docker_json,
                        requirements=req_json,
                        updated_at=datetime.utcnow(),
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
                    maintainers=json.dumps(app.maintainers),
                    repository=app.repository,
                    documentation=app.documentation,
                    repo_id=app.repo_id,
                    docker_config=docker_json,
                    requirements=req_json,
                )
                session.add(table_row)

    # ─────────────────────────────────────────────────────────────
    # App Search & Discovery
    # ─────────────────────────────────────────────────────────────

    async def search_apps(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        repo_id: Optional[str] = None,
        featured: Optional[bool] = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> List[MarketplaceApp]:
        """Search marketplace apps with filters.

        Args:
            search: Search term to match against name or description
            category: Filter by category
            tags: Filter by tags (all tags must match)
            repo_id: Filter by repository ID
            featured: Filter by featured status
            sort_by: Sort field (name, rating, popularity, updated)
            sort_order: Sort order (asc, desc)
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of matching MarketplaceApp instances
        """
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            query = (
                select(MarketplaceAppTable, MarketplaceRepoTable)
                .join(
                    MarketplaceRepoTable,
                    MarketplaceAppTable.repo_id == MarketplaceRepoTable.id,
                )
                .where(MarketplaceRepoTable.enabled == True)
            )  # noqa: E712

            # Apply filters
            if category:
                query = query.where(MarketplaceAppTable.category == category)
            if repo_id:
                query = query.where(MarketplaceAppTable.repo_id == repo_id)
            if featured is not None:
                query = query.where(MarketplaceAppTable.featured == featured)

            result = await session.execute(query)
            rows = result.all()

        # Convert to models
        apps = [self._app_from_table(app_row) for app_row, _ in rows]

        # In-memory filtering for search and tags
        if search:
            search_lower = search.lower()
            apps = [
                a
                for a in apps
                if search_lower in a.name.lower()
                or search_lower in a.description.lower()
            ]

        if tags:
            required_tags = set(t.lower() for t in tags)
            apps = [
                a
                for a in apps
                if required_tags.issubset(set(t.lower() for t in a.tags))
            ]

        # Sort
        reverse = sort_order.lower() == "desc"
        if sort_by == "name":
            apps.sort(key=lambda a: a.name.lower(), reverse=reverse)
        elif sort_by == "rating":
            apps.sort(key=lambda a: a.avg_rating or 0, reverse=reverse)
        elif sort_by == "popularity":
            apps.sort(key=lambda a: a.install_count, reverse=reverse)
        elif sort_by == "updated":
            apps.sort(key=lambda a: a.updated_at, reverse=reverse)

        # Pagination
        return apps[offset : offset + limit]

    async def get_app(self, app_id: str) -> Optional[MarketplaceApp]:
        """Get app by ID.

        Args:
            app_id: Application identifier

        Returns:
            MarketplaceApp instance if found, None otherwise
        """
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            result = await session.execute(
                select(MarketplaceAppTable).where(MarketplaceAppTable.id == app_id)
            )
            row = result.scalar_one_or_none()

        return self._app_from_table(row) if row else None

    async def get_featured_apps(self, limit: int = 10) -> List[MarketplaceApp]:
        """Get featured apps.

        Args:
            limit: Maximum number of apps to return

        Returns:
            List of featured MarketplaceApp instances
        """
        return await self.search_apps(featured=True, limit=limit)

    async def get_trending_apps(self, limit: int = 10) -> List[MarketplaceApp]:
        """Get trending apps by recent popularity.

        Args:
            limit: Maximum number of apps to return

        Returns:
            List of trending MarketplaceApp instances sorted by popularity
        """
        return await self.search_apps(
            sort_by="popularity", sort_order="desc", limit=limit
        )

    async def get_categories(self) -> List[dict]:
        """Get all categories with app counts.

        Returns:
            List of dictionaries with category id, name, and count
        """
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            result = await session.execute(select(MarketplaceAppTable.category))
            rows = result.all()

        # Count apps per category
        category_counts: dict = {}
        for row in rows:
            cat = row[0]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return [
            {"id": cat, "name": cat.title(), "count": count}
            for cat, count in sorted(category_counts.items())
        ]

    # ─────────────────────────────────────────────────────────────
    # Ratings
    # ─────────────────────────────────────────────────────────────

    async def rate_app(self, app_id: str, user_id: str, rating: int) -> AppRating:
        """Rate an app (1-5 stars). Updates existing rating if present.

        Args:
            app_id: Application identifier
            user_id: User identifier
            rating: Rating value (1-5)

        Returns:
            AppRating instance

        Raises:
            ValueError: If rating is not between 1 and 5
        """
        await self._ensure_initialized()

        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        rating_id = f"rating-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()

        async with db_manager.get_session() as session:
            # Check for existing rating
            result = await session.execute(
                select(AppRatingTable).where(
                    AppRatingTable.app_id == app_id, AppRatingTable.user_id == user_id
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                await session.execute(
                    update(AppRatingTable)
                    .where(AppRatingTable.id == existing.id)
                    .values(rating=rating, updated_at=now)
                )
                rating_id = existing.id
            else:
                # Insert new
                new_rating = AppRatingTable(
                    id=rating_id, app_id=app_id, user_id=user_id, rating=rating
                )
                session.add(new_rating)

            # Flush to ensure the new rating is committed
            await session.flush()

            # Update app's average rating - query again after flush
            avg_result = await session.execute(
                select(AppRatingTable.rating).where(AppRatingTable.app_id == app_id)
            )
            all_ratings = [r[0] for r in avg_result.all()]
            avg_rating = sum(all_ratings) / len(all_ratings) if all_ratings else None

            await session.execute(
                update(MarketplaceAppTable)
                .where(MarketplaceAppTable.id == app_id)
                .values(avg_rating=avg_rating, rating_count=len(all_ratings))
            )

        logger.info("App rated", app_id=app_id, user_id=user_id, rating=rating)

        return AppRating(
            id=rating_id,
            app_id=app_id,
            user_id=user_id,
            rating=rating,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
        )

    async def get_user_rating(self, app_id: str, user_id: str) -> Optional[int]:
        """Get user's rating for an app.

        Args:
            app_id: Application identifier
            user_id: User identifier

        Returns:
            Rating value (1-5) if found, None otherwise
        """
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            result = await session.execute(
                select(AppRatingTable.rating).where(
                    AppRatingTable.app_id == app_id, AppRatingTable.user_id == user_id
                )
            )
            row = result.scalar_one_or_none()

        return row if row else None

    # ─────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _is_casaos_repo(repo_path: Path) -> bool:
        """Detect if repository uses CasaOS format.

        CasaOS format has an 'Apps' directory with docker-compose.yml files.
        """
        apps_dir = repo_path / "Apps"
        if apps_dir.exists():
            # Check if any subdirectory contains docker-compose.yml
            for subdir in apps_dir.iterdir():
                if subdir.is_dir() and (subdir / "docker-compose.yml").exists():
                    return True
        return False

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

    @staticmethod
    def _app_from_table(row: MarketplaceAppTable) -> MarketplaceApp:
        """Convert table row to MarketplaceApp model.

        Args:
            row: SQLAlchemy MarketplaceAppTable instance

        Returns:
            MarketplaceApp Pydantic model
        """
        docker_config = DockerConfig.model_validate_json(row.docker_config)
        requirements = (
            AppRequirements.model_validate_json(row.requirements)
            if row.requirements
            else AppRequirements(architectures=["amd64", "arm64"])
        )
        tags = json.loads(row.tags) if row.tags else []

        return MarketplaceApp(
            id=row.id,
            name=row.name,
            description=row.description,
            long_description=row.long_description,
            version=row.version,
            category=row.category,
            tags=tags,
            icon=row.icon,
            author=row.author,
            license=row.license,
            maintainers=json.loads(row.maintainers) if row.maintainers else [],
            repository=row.repository,
            documentation=row.documentation,
            repo_id=row.repo_id,
            docker=docker_config,
            requirements=requirements,
            install_count=row.install_count or 0,
            avg_rating=row.avg_rating or 0.0,
            rating_count=row.rating_count or 0,
            featured=row.featured or False,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

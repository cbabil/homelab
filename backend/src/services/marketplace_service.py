"""Marketplace Service.

Provides data access and business logic for marketplace repository management."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

import structlog

from lib.git_sync import GitSync
from models.marketplace import (
    AppRating,
    AppRequirements,
    DockerConfig,
    MarketplaceApp,
    MarketplaceRepo,
    RepoStatus,
    RepoType,
)
from services.database.base import DatabaseConnection

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

    def __init__(self, connection: DatabaseConnection) -> None:
        self._conn = connection
        self._initialized = False
        logger.info("Marketplace service initialized")

    async def _ensure_initialized(self) -> None:
        """Ensure the marketplace database is initialized with official repos."""
        if not self._initialized:
            await self._ensure_official_marketplace()
            self._initialized = True

    async def _ensure_official_marketplace(self) -> None:
        """Add CasaOS app store and official marketplace if not already present."""
        now = datetime.utcnow().isoformat()

        async with self._conn.get_connection() as conn:
            # CasaOS app store
            cursor = await conn.execute(
                "SELECT id FROM marketplace_repos WHERE id = ?", ("casaos",)
            )
            if not await cursor.fetchone():
                await conn.execute(
                    """INSERT OR IGNORE INTO marketplace_repos
                       (id, name, url, branch, repo_type, enabled, status,
                        app_count, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, 1, ?, 0, ?, ?)""",
                    (
                        "casaos",
                        CASAOS_APPSTORE_NAME,
                        CASAOS_APPSTORE_URL,
                        CASAOS_APPSTORE_BRANCH,
                        RepoType.OFFICIAL.value,
                        RepoStatus.ACTIVE.value,
                        now,
                        now,
                    ),
                )
                await conn.commit()
                logger.info(
                    "CasaOS app store added",
                    repo_id="casaos",
                    url=CASAOS_APPSTORE_URL,
                )

            # Legacy official marketplace
            cursor = await conn.execute(
                "SELECT id FROM marketplace_repos WHERE id = ?", ("official",)
            )
            if not await cursor.fetchone():
                await conn.execute(
                    """INSERT OR IGNORE INTO marketplace_repos
                       (id, name, url, branch, repo_type, enabled, status,
                        app_count, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, 1, ?, 0, ?, ?)""",
                    (
                        "official",
                        OFFICIAL_MARKETPLACE_NAME,
                        OFFICIAL_MARKETPLACE_URL,
                        OFFICIAL_MARKETPLACE_BRANCH,
                        RepoType.COMMUNITY.value,
                        RepoStatus.ACTIVE.value,
                        now,
                        now,
                    ),
                )
                await conn.commit()
                logger.info(
                    "Official marketplace added",
                    repo_id="official",
                    url=OFFICIAL_MARKETPLACE_URL,
                )

    async def add_repo(
        self, name: str, url: str, repo_type: RepoType, branch: str = "main"
    ) -> MarketplaceRepo:
        """Create a new marketplace repository."""
        await self._ensure_initialized()

        repo_id = uuid.uuid4().hex[:8]
        now = datetime.utcnow().isoformat()

        async with self._conn.get_connection() as conn:
            await conn.execute(
                """INSERT INTO marketplace_repos
                   (id, name, url, branch, repo_type, enabled, status,
                    app_count, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?, 0, ?, ?)""",
                (
                    repo_id,
                    name,
                    url,
                    branch,
                    repo_type.value,
                    RepoStatus.ACTIVE.value,
                    now,
                    now,
                ),
            )
            await conn.commit()

            cursor = await conn.execute(
                "SELECT * FROM marketplace_repos WHERE id = ?", (repo_id,)
            )
            row = await cursor.fetchone()

        repo = self._repo_from_row(row)
        logger.info(
            "Repository added",
            repo_id=repo_id,
            name=name,
            repo_type=repo_type.value,
        )
        return repo

    async def get_repos(self, enabled_only: bool = False) -> list[MarketplaceRepo]:
        """Get all marketplace repositories."""
        await self._ensure_initialized()

        sql = "SELECT * FROM marketplace_repos"
        params: list = []
        if enabled_only:
            sql += " WHERE enabled = 1"

        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(sql, params)
            rows = await cursor.fetchall()

        repos = [self._repo_from_row(row) for row in rows]
        logger.debug(
            "Fetched repositories", count=len(repos), enabled_only=enabled_only
        )
        return repos

    async def get_repo(self, repo_id: str) -> MarketplaceRepo | None:
        """Get a single repository by ID."""
        await self._ensure_initialized()

        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM marketplace_repos WHERE id = ?", (repo_id,)
            )
            row = await cursor.fetchone()

        if not row:
            logger.warning("Repository not found", repo_id=repo_id)
            return None

        repo = self._repo_from_row(row)
        logger.debug("Retrieved repository", repo_id=repo_id)
        return repo

    async def remove_repo(self, repo_id: str) -> bool:
        """Delete a repository and all its associated apps."""
        await self._ensure_initialized()

        async with self._conn.get_connection() as conn:
            # Delete ratings for apps in this repo
            await conn.execute(
                """DELETE FROM app_ratings WHERE app_id IN
                   (SELECT id FROM marketplace_apps WHERE repo_id = ?)""",
                (repo_id,),
            )
            # Delete apps
            await conn.execute(
                "DELETE FROM marketplace_apps WHERE repo_id = ?", (repo_id,)
            )
            # Delete repo
            cursor = await conn.execute(
                "DELETE FROM marketplace_repos WHERE id = ?", (repo_id,)
            )
            deleted = cursor.rowcount > 0
            await conn.commit()

        if deleted:
            logger.info("Repository removed", repo_id=repo_id)
        else:
            logger.warning("Repository not found for removal", repo_id=repo_id)

        return deleted

    async def toggle_repo(self, repo_id: str, enabled: bool) -> bool:
        """Enable or disable a repository."""
        await self._ensure_initialized()

        now = datetime.utcnow().isoformat()
        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                "UPDATE marketplace_repos SET enabled = ?, updated_at = ? WHERE id = ?",
                (1 if enabled else 0, now, repo_id),
            )
            updated = cursor.rowcount > 0
            await conn.commit()

        if updated:
            action = "enabled" if enabled else "disabled"
            logger.info(f"Repository {action}", repo_id=repo_id)
        else:
            logger.warning("Repository not found for toggle", repo_id=repo_id)

        return updated

    async def sync_repo(
        self, repo_id: str, local_path: Path | None = None
    ) -> list[MarketplaceApp]:
        """Sync apps from a repository."""
        await self._ensure_initialized()

        repo = await self.get_repo(repo_id)
        if not repo:
            raise ValueError(f"Repository {repo_id} not found")

        # Update status to SYNCING
        async with self._conn.get_connection() as conn:
            await conn.execute(
                "UPDATE marketplace_repos SET status = ? WHERE id = ?",
                (RepoStatus.SYNCING.value, repo_id),
            )
            await conn.commit()

        git_sync = GitSync()
        apps: list[MarketplaceApp] = []

        try:
            if local_path:
                repo_path = Path(local_path)
            else:
                repo_path = git_sync.clone_or_pull(repo.url, repo.branch)

            is_casaos_format = self._is_casaos_repo(repo_path)

            if is_casaos_format:
                app_files = git_sync.find_casaos_app_files(repo_path)
                for app_file in app_files:
                    app = git_sync.load_casaos_app(app_file, repo_id)
                    if app:
                        apps.append(app)
                        await self._upsert_app(app)
                logger.info(
                    "Synced CasaOS format repo",
                    repo_id=repo_id,
                    app_count=len(apps),
                )
            else:
                app_files = git_sync.find_app_files(repo_path)
                for app_file in app_files:
                    app = git_sync.load_app_from_file(app_file, repo_id)
                    if app:
                        apps.append(app)
                        await self._upsert_app(app)
                logger.info(
                    "Synced legacy format repo",
                    repo_id=repo_id,
                    app_count=len(apps),
                )

            now = datetime.utcnow().isoformat()
            async with self._conn.get_connection() as conn:
                await conn.execute(
                    """UPDATE marketplace_repos
                       SET status = ?, last_synced = ?, app_count = ?, error_message = NULL
                       WHERE id = ?""",
                    (RepoStatus.ACTIVE.value, now, len(apps), repo_id),
                )
                await conn.commit()

            logger.info("Repository synced", repo_id=repo_id, app_count=len(apps))

        except Exception as e:
            async with self._conn.get_connection() as conn:
                await conn.execute(
                    "UPDATE marketplace_repos SET status = ?, error_message = ? WHERE id = ?",
                    (RepoStatus.ERROR.value, str(e), repo_id),
                )
                await conn.commit()
            logger.error("Repository sync failed", repo_id=repo_id, error=str(e))
            raise

        finally:
            if not local_path:
                git_sync.cleanup()

        return apps

    async def _upsert_app(self, app: MarketplaceApp) -> None:
        """Insert or update an app in the database."""
        docker_json = app.docker.model_dump_json()
        req_json = app.requirements.model_dump_json()
        tags_json = json.dumps(app.tags)
        maintainers_json = json.dumps(app.maintainers)
        now = datetime.utcnow().isoformat()

        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT id FROM marketplace_apps WHERE id = ?", (app.id,)
            )
            existing = await cursor.fetchone()

            if existing:
                await conn.execute(
                    """UPDATE marketplace_apps SET
                       name = ?, description = ?, long_description = ?,
                       version = ?, category = ?, tags = ?, icon = ?,
                       author = ?, license = ?, maintainers = ?,
                       repository = ?, documentation = ?,
                       docker_config = ?, requirements = ?, updated_at = ?
                       WHERE id = ?""",
                    (
                        app.name,
                        app.description,
                        app.long_description,
                        app.version,
                        app.category,
                        tags_json,
                        app.icon,
                        app.author,
                        app.license,
                        maintainers_json,
                        app.repository,
                        app.documentation,
                        docker_json,
                        req_json,
                        now,
                        app.id,
                    ),
                )
            else:
                await conn.execute(
                    """INSERT INTO marketplace_apps
                       (id, name, description, long_description, version,
                        category, tags, icon, author, license, maintainers,
                        repository, documentation, repo_id,
                        docker_config, requirements, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        app.id,
                        app.name,
                        app.description,
                        app.long_description,
                        app.version,
                        app.category,
                        tags_json,
                        app.icon,
                        app.author,
                        app.license,
                        maintainers_json,
                        app.repository,
                        app.documentation,
                        app.repo_id,
                        docker_json,
                        req_json,
                        now,
                        now,
                    ),
                )
            await conn.commit()

    # ─────────────────────────────────────────────────────────────
    # App Search & Discovery
    # ─────────────────────────────────────────────────────────────

    async def search_apps(
        self,
        search: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        repo_id: str | None = None,
        featured: bool | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[MarketplaceApp]:
        """Search marketplace apps with filters."""
        await self._ensure_initialized()

        sql = """SELECT a.* FROM marketplace_apps a
                 JOIN marketplace_repos r ON a.repo_id = r.id
                 WHERE r.enabled = 1"""
        params: list = []

        if category:
            sql += " AND a.category = ?"
            params.append(category)
        if repo_id:
            sql += " AND a.repo_id = ?"
            params.append(repo_id)
        if featured is not None:
            sql += " AND a.featured = ?"
            params.append(1 if featured else 0)

        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(sql, params)
            rows = await cursor.fetchall()

        apps = [self._app_from_row(row) for row in rows]

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

        return apps[offset : offset + limit]

    async def get_app(self, app_id: str) -> MarketplaceApp | None:
        """Get app by ID."""
        await self._ensure_initialized()

        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM marketplace_apps WHERE id = ?", (app_id,)
            )
            row = await cursor.fetchone()

        return self._app_from_row(row) if row else None

    async def get_featured_apps(self, limit: int = 10) -> list[MarketplaceApp]:
        """Get featured apps."""
        return await self.search_apps(featured=True, limit=limit)

    async def get_trending_apps(self, limit: int = 10) -> list[MarketplaceApp]:
        """Get trending apps by recent popularity."""
        return await self.search_apps(
            sort_by="popularity", sort_order="desc", limit=limit
        )

    async def get_categories(self) -> list[dict]:
        """Get all categories with app counts."""
        await self._ensure_initialized()

        async with self._conn.get_connection() as conn:
            cursor = await conn.execute("SELECT category FROM marketplace_apps")
            rows = await cursor.fetchall()

        category_counts: dict = {}
        for row in rows:
            cat = row["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return [
            {"id": cat, "name": cat.title(), "count": count}
            for cat, count in sorted(category_counts.items())
        ]

    # ─────────────────────────────────────────────────────────────
    # Ratings
    # ─────────────────────────────────────────────────────────────

    async def rate_app(self, app_id: str, user_id: str, rating: int) -> AppRating:
        """Rate an app (1-5 stars). Updates existing rating if present."""
        await self._ensure_initialized()

        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        rating_id = f"rating-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()

        async with self._conn.get_connection() as conn:
            # Check for existing rating
            cursor = await conn.execute(
                "SELECT id FROM app_ratings WHERE app_id = ? AND user_id = ?",
                (app_id, user_id),
            )
            existing = await cursor.fetchone()

            if existing:
                rating_id = existing["id"]
                await conn.execute(
                    "UPDATE app_ratings SET rating = ?, updated_at = ? WHERE id = ?",
                    (rating, now, rating_id),
                )
            else:
                await conn.execute(
                    """INSERT INTO app_ratings
                       (id, app_id, user_id, rating, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (rating_id, app_id, user_id, rating, now, now),
                )

            await conn.commit()

            # Update app's average rating
            cursor = await conn.execute(
                "SELECT rating FROM app_ratings WHERE app_id = ?", (app_id,)
            )
            all_ratings = [r["rating"] for r in await cursor.fetchall()]
            avg_rating = sum(all_ratings) / len(all_ratings) if all_ratings else None

            await conn.execute(
                "UPDATE marketplace_apps SET avg_rating = ?, rating_count = ? WHERE id = ?",
                (avg_rating, len(all_ratings), app_id),
            )
            await conn.commit()

        logger.info("App rated", app_id=app_id, user_id=user_id, rating=rating)

        return AppRating(
            id=rating_id,
            app_id=app_id,
            user_id=user_id,
            rating=rating,
            created_at=now,
            updated_at=now,
        )

    async def get_user_rating(self, app_id: str, user_id: str) -> int | None:
        """Get user's rating for an app."""
        await self._ensure_initialized()

        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT rating FROM app_ratings WHERE app_id = ? AND user_id = ?",
                (app_id, user_id),
            )
            row = await cursor.fetchone()

        return row["rating"] if row else None

    # ─────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _is_casaos_repo(repo_path: Path) -> bool:
        """Detect if repository uses CasaOS format."""
        apps_dir = repo_path / "Apps"
        if apps_dir.exists():
            for subdir in apps_dir.iterdir():
                if subdir.is_dir() and (subdir / "docker-compose.yml").exists():
                    return True
        return False

    @staticmethod
    def _repo_from_row(row) -> MarketplaceRepo:
        """Convert an aiosqlite.Row to a MarketplaceRepo model."""
        return MarketplaceRepo(
            id=row["id"],
            name=row["name"],
            url=row["url"],
            branch=row["branch"],
            repo_type=RepoType(row["repo_type"]),
            enabled=bool(row["enabled"]),
            status=RepoStatus(row["status"]),
            last_synced=row["last_synced"],
            app_count=row["app_count"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _app_from_row(row) -> MarketplaceApp:
        """Convert an aiosqlite.Row to a MarketplaceApp model."""
        docker_config = DockerConfig.model_validate_json(row["docker_config"])
        requirements = (
            AppRequirements.model_validate_json(row["requirements"])
            if row["requirements"]
            else AppRequirements(architectures=["amd64", "arm64"])
        )
        tags = json.loads(row["tags"]) if row["tags"] else []

        return MarketplaceApp(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            long_description=row["long_description"],
            version=row["version"],
            category=row["category"],
            tags=tags,
            icon=row["icon"],
            author=row["author"],
            license=row["license"],
            maintainers=json.loads(row["maintainers"]) if row["maintainers"] else [],
            repository=row["repository"],
            documentation=row["documentation"],
            repo_id=row["repo_id"],
            docker=docker_config,
            requirements=requirements,
            install_count=row["install_count"] or 0,
            avg_rating=row["avg_rating"] or 0.0,
            rating_count=row["rating_count"] or 0,
            featured=bool(row["featured"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

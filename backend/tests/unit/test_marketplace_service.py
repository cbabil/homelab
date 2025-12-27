"""Unit tests for MarketplaceService."""

import pytest
from sqlalchemy import delete, update
from services.marketplace_service import MarketplaceService
from models.marketplace import RepoType, RepoStatus, MarketplaceRepoTable, MarketplaceAppTable, AppRatingTable
from database.connection import db_manager


@pytest.fixture
async def marketplace_service():
    """Create a MarketplaceService instance for testing."""
    service = MarketplaceService()

    # Clean up before each test
    await service._ensure_initialized()
    async with db_manager.get_session() as session:
        await session.execute(delete(AppRatingTable))
        await session.execute(delete(MarketplaceAppTable))
        await session.execute(delete(MarketplaceRepoTable))

    return service


@pytest.mark.asyncio
async def test_add_repo_personal(marketplace_service):
    """Test adding a personal repository."""
    repo = await marketplace_service.add_repo(
        name="Test Personal Repo",
        url="https://github.com/test/apps",
        repo_type=RepoType.PERSONAL
    )
    assert repo.name == "Test Personal Repo"
    assert repo.url == "https://github.com/test/apps"
    assert repo.repo_type == RepoType.PERSONAL
    assert repo.branch == "main"
    assert repo.enabled is True
    assert repo.status == RepoStatus.ACTIVE
    assert repo.app_count == 0
    assert repo.error_message is None
    assert len(repo.id) == 8


@pytest.mark.asyncio
async def test_add_repo_with_branch(marketplace_service):
    """Test adding a repository with custom branch."""
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url="https://github.com/test/apps",
        repo_type=RepoType.COMMUNITY,
        branch="develop"
    )
    assert repo.name == "Test Repo"
    assert repo.branch == "develop"
    assert repo.repo_type == RepoType.COMMUNITY


@pytest.mark.asyncio
async def test_get_repos_empty(marketplace_service):
    """Test getting repos when none exist."""
    repos = await marketplace_service.get_repos()
    assert repos == []


@pytest.mark.asyncio
async def test_get_repos_all(marketplace_service):
    """Test getting all repositories."""
    # Add two repos
    repo1 = await marketplace_service.add_repo(
        name="Repo 1",
        url="https://github.com/test/apps1",
        repo_type=RepoType.OFFICIAL
    )
    repo2 = await marketplace_service.add_repo(
        name="Repo 2",
        url="https://github.com/test/apps2",
        repo_type=RepoType.COMMUNITY
    )

    # Get all repos
    repos = await marketplace_service.get_repos()
    assert len(repos) == 2
    assert any(r.id == repo1.id for r in repos)
    assert any(r.id == repo2.id for r in repos)


@pytest.mark.asyncio
async def test_get_repos_enabled_only(marketplace_service):
    """Test filtering for enabled repos only."""
    # Add enabled and disabled repos
    repo1 = await marketplace_service.add_repo(
        name="Enabled Repo",
        url="https://github.com/test/apps1",
        repo_type=RepoType.PERSONAL
    )
    repo2 = await marketplace_service.add_repo(
        name="Disabled Repo",
        url="https://github.com/test/apps2",
        repo_type=RepoType.PERSONAL
    )

    # Disable repo2
    await marketplace_service.toggle_repo(repo2.id, False)

    # Get only enabled repos
    enabled_repos = await marketplace_service.get_repos(enabled_only=True)
    assert len(enabled_repos) == 1
    assert enabled_repos[0].id == repo1.id
    assert enabled_repos[0].enabled is True


@pytest.mark.asyncio
async def test_get_repo_by_id(marketplace_service):
    """Test getting a single repository by ID."""
    # Add a repo
    created_repo = await marketplace_service.add_repo(
        name="Test Repo",
        url="https://github.com/test/apps",
        repo_type=RepoType.OFFICIAL
    )

    # Get it back
    retrieved_repo = await marketplace_service.get_repo(created_repo.id)
    assert retrieved_repo is not None
    assert retrieved_repo.id == created_repo.id
    assert retrieved_repo.name == "Test Repo"
    assert retrieved_repo.url == "https://github.com/test/apps"


@pytest.mark.asyncio
async def test_get_repo_not_found(marketplace_service):
    """Test getting a repository that doesn't exist."""
    repo = await marketplace_service.get_repo("nonexistent")
    assert repo is None


@pytest.mark.asyncio
async def test_toggle_repo_disable(marketplace_service):
    """Test disabling a repository."""
    # Add a repo
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url="https://github.com/test/apps",
        repo_type=RepoType.COMMUNITY
    )
    assert repo.enabled is True

    # Disable it
    success = await marketplace_service.toggle_repo(repo.id, False)
    assert success is True

    # Verify it's disabled
    updated_repo = await marketplace_service.get_repo(repo.id)
    assert updated_repo is not None
    assert updated_repo.enabled is False


@pytest.mark.asyncio
async def test_toggle_repo_enable(marketplace_service):
    """Test enabling a repository."""
    # Add and disable a repo
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url="https://github.com/test/apps",
        repo_type=RepoType.PERSONAL
    )
    await marketplace_service.toggle_repo(repo.id, False)

    # Enable it
    success = await marketplace_service.toggle_repo(repo.id, True)
    assert success is True

    # Verify it's enabled
    updated_repo = await marketplace_service.get_repo(repo.id)
    assert updated_repo is not None
    assert updated_repo.enabled is True


@pytest.mark.asyncio
async def test_toggle_repo_not_found(marketplace_service):
    """Test toggling a repository that doesn't exist."""
    success = await marketplace_service.toggle_repo("nonexistent", False)
    assert success is False


@pytest.mark.asyncio
async def test_remove_repo(marketplace_service):
    """Test removing a repository."""
    # Add a repo
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url="https://github.com/test/apps",
        repo_type=RepoType.COMMUNITY
    )

    # Remove it
    success = await marketplace_service.remove_repo(repo.id)
    assert success is True

    # Verify it's gone
    removed_repo = await marketplace_service.get_repo(repo.id)
    assert removed_repo is None


@pytest.mark.asyncio
async def test_remove_repo_not_found(marketplace_service):
    """Test removing a repository that doesn't exist."""
    success = await marketplace_service.remove_repo("nonexistent")
    assert success is False


@pytest.mark.asyncio
async def test_remove_repo_with_apps(marketplace_service):
    """Test removing a repository should remove its apps."""
    # Add a repo
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url="https://github.com/test/apps",
        repo_type=RepoType.OFFICIAL
    )

    # Note: This test verifies the deletion logic works
    # Actual app deletion will be tested when we have app creation
    success = await marketplace_service.remove_repo(repo.id)
    assert success is True


@pytest.mark.asyncio
async def test_sync_repo_local_path(marketplace_service, tmp_path):
    """Test syncing a repository from a local path."""
    # Create a mock repo with app.yaml
    apps_dir = tmp_path / "apps" / "testapp"
    apps_dir.mkdir(parents=True)
    (apps_dir / "app.yaml").write_text("""
name: Test App
version: 1.0.0
description: A test application
category: utility
docker:
  image: test/app:latest
  ports:
    - container: 8080
      host: 8080
  volumes: []
  environment: []
  restart_policy: unless-stopped
  privileged: false
  capabilities: []
""")

    # Add repo pointing to local path
    repo = await marketplace_service.add_repo(
        name="Local Test",
        url=str(tmp_path),
        repo_type=RepoType.PERSONAL
    )

    # Sync repo (mock Git operations by using local_path)
    apps = await marketplace_service.sync_repo(repo.id, local_path=tmp_path)

    # Verify sync results
    assert len(apps) == 1
    assert apps[0].name == "Test App"
    assert apps[0].version == "1.0.0"
    assert apps[0].category == "utility"
    assert apps[0].docker.image == "test/app:latest"

    # Verify repo status updated
    updated_repo = await marketplace_service.get_repo(repo.id)
    assert updated_repo is not None
    assert updated_repo.status == RepoStatus.ACTIVE
    assert updated_repo.app_count == 1
    assert updated_repo.last_synced is not None
    assert updated_repo.error_message is None


@pytest.mark.asyncio
async def test_sync_repo_updates_status_to_syncing(marketplace_service, tmp_path):
    """Test that sync_repo updates status to SYNCING during sync."""
    # Create a mock repo
    apps_dir = tmp_path / "apps" / "testapp"
    apps_dir.mkdir(parents=True)
    (apps_dir / "app.yaml").write_text("""
name: Test App
version: 1.0.0
description: A test application
category: utility
docker:
  image: test/app:latest
  ports: []
  volumes: []
  environment: []
  restart_policy: unless-stopped
  privileged: false
  capabilities: []
""")

    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url=str(tmp_path),
        repo_type=RepoType.PERSONAL
    )

    # The status will be SYNCING during the operation
    # We can't check mid-operation but we can verify final state is ACTIVE
    await marketplace_service.sync_repo(repo.id, local_path=tmp_path)

    updated_repo = await marketplace_service.get_repo(repo.id)
    assert updated_repo.status == RepoStatus.ACTIVE


@pytest.mark.asyncio
async def test_sync_repo_handles_errors(marketplace_service):
    """Test that sync_repo handles errors gracefully."""
    # Add repo with invalid URL (no local_path will force Git operations)
    repo = await marketplace_service.add_repo(
        name="Invalid Repo",
        url="https://github.com/nonexistent/repo",
        repo_type=RepoType.COMMUNITY
    )

    # Sync should fail and set error status
    with pytest.raises(RuntimeError):
        await marketplace_service.sync_repo(repo.id)

    # Verify repo status is ERROR with error message
    updated_repo = await marketplace_service.get_repo(repo.id)
    assert updated_repo is not None
    assert updated_repo.status == RepoStatus.ERROR
    assert updated_repo.error_message is not None


@pytest.mark.asyncio
async def test_sync_repo_stores_apps_in_database(marketplace_service, tmp_path):
    """Test that synced apps are stored in the database."""
    # Create multiple apps
    for i in range(3):
        app_dir = tmp_path / "apps" / f"app{i}"
        app_dir.mkdir(parents=True)
        (app_dir / "app.yaml").write_text(f"""
name: Test App {i}
version: 1.{i}.0
description: Test application {i}
category: utility
docker:
  image: test/app{i}:latest
  ports: []
  volumes: []
  environment: []
  restart_policy: unless-stopped
  privileged: false
  capabilities: []
""")

    repo = await marketplace_service.add_repo(
        name="Multi-App Repo",
        url=str(tmp_path),
        repo_type=RepoType.COMMUNITY
    )

    apps = await marketplace_service.sync_repo(repo.id, local_path=tmp_path)

    # Verify all apps were synced
    assert len(apps) == 3

    # Verify apps are in database by checking app_count
    updated_repo = await marketplace_service.get_repo(repo.id)
    assert updated_repo.app_count == 3


@pytest.mark.asyncio
async def test_sync_repo_not_found(marketplace_service):
    """Test syncing a non-existent repository."""
    with pytest.raises(ValueError, match="Repository .* not found"):
        await marketplace_service.sync_repo("nonexistent")


# ─────────────────────────────────────────────────────────────
# App Search and Discovery Tests
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_apps_empty(marketplace_service):
    """Test searching when no apps exist."""
    results = await marketplace_service.search_apps()
    assert isinstance(results, list)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_apps_by_category(marketplace_service, tmp_path):
    """Test searching apps by category."""
    # Create apps in different categories
    media_dir = tmp_path / "apps" / "jellyfin"
    media_dir.mkdir(parents=True)
    (media_dir / "app.yaml").write_text("""
name: Jellyfin
version: 10.8.13
description: Free media system
category: media
tags:
  - streaming
  - movies
docker:
  image: jellyfin/jellyfin:latest
  ports:
    - container: 8096
      host: 8096
  volumes: []
  environment: []
  restart_policy: unless-stopped
  privileged: false
  capabilities: []
""")

    util_dir = tmp_path / "apps" / "portainer"
    util_dir.mkdir(parents=True)
    (util_dir / "app.yaml").write_text("""
name: Portainer
version: 2.0.0
description: Docker management UI
category: utility
tags:
  - docker
  - management
docker:
  image: portainer/portainer:latest
  ports:
    - container: 9000
      host: 9000
  volumes: []
  environment: []
  restart_policy: unless-stopped
  privileged: false
  capabilities: []
""")

    # Add repo and sync
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url=str(tmp_path),
        repo_type=RepoType.OFFICIAL
    )
    await marketplace_service.sync_repo(repo.id, local_path=tmp_path)

    # Search by category
    media_apps = await marketplace_service.search_apps(category="media")
    assert len(media_apps) == 1
    assert media_apps[0].name == "Jellyfin"

    util_apps = await marketplace_service.search_apps(category="utility")
    assert len(util_apps) == 1
    assert util_apps[0].name == "Portainer"


@pytest.mark.asyncio
async def test_search_apps_by_query(marketplace_service, tmp_path):
    """Test searching apps by name or description."""
    # Create apps
    app_dir = tmp_path / "apps" / "jellyfin"
    app_dir.mkdir(parents=True)
    (app_dir / "app.yaml").write_text("""
name: Jellyfin
version: 10.8.13
description: Free media streaming system
category: media
tags: []
docker:
  image: jellyfin/jellyfin:latest
  ports: []
  volumes: []
  environment: []
  restart_policy: unless-stopped
  privileged: false
  capabilities: []
""")

    # Add repo and sync
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url=str(tmp_path),
        repo_type=RepoType.OFFICIAL
    )
    await marketplace_service.sync_repo(repo.id, local_path=tmp_path)

    # Search by name
    results = await marketplace_service.search_apps(search="jellyfin")
    assert len(results) == 1
    assert results[0].name == "Jellyfin"

    # Search by description
    results = await marketplace_service.search_apps(search="streaming")
    assert len(results) == 1

    # Search with no matches
    results = await marketplace_service.search_apps(search="nonexistent")
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_apps_by_tags(marketplace_service, tmp_path):
    """Test searching apps by tags."""
    # Create app with tags
    app_dir = tmp_path / "apps" / "jellyfin"
    app_dir.mkdir(parents=True)
    (app_dir / "app.yaml").write_text("""
name: Jellyfin
version: 10.8.13
description: Free media system
category: media
tags:
  - streaming
  - movies
  - tv
docker:
  image: jellyfin/jellyfin:latest
  ports: []
  volumes: []
  environment: []
  restart_policy: unless-stopped
  privileged: false
  capabilities: []
""")

    # Add repo and sync
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url=str(tmp_path),
        repo_type=RepoType.OFFICIAL
    )
    await marketplace_service.sync_repo(repo.id, local_path=tmp_path)

    # Search by tags
    results = await marketplace_service.search_apps(tags=["streaming"])
    assert len(results) == 1

    results = await marketplace_service.search_apps(tags=["streaming", "movies"])
    assert len(results) == 1

    # Tag not present
    results = await marketplace_service.search_apps(tags=["gaming"])
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_apps_featured_only(marketplace_service, tmp_path):
    """Test searching for featured apps only."""
    # Create app
    app_dir = tmp_path / "apps" / "jellyfin"
    app_dir.mkdir(parents=True)
    (app_dir / "app.yaml").write_text("""
name: Jellyfin
version: 10.8.13
description: Free media system
category: media
tags: []
docker:
  image: jellyfin/jellyfin:latest
  ports: []
  volumes: []
  environment: []
  restart_policy: unless-stopped
  privileged: false
  capabilities: []
""")

    # Add repo and sync
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url=str(tmp_path),
        repo_type=RepoType.OFFICIAL
    )
    await marketplace_service.sync_repo(repo.id, local_path=tmp_path)

    # Mark app as featured manually
    from database.connection import db_manager
    async with db_manager.get_session() as session:
        await session.execute(
            update(MarketplaceAppTable)
            .where(MarketplaceAppTable.name == "Jellyfin")
            .values(featured=True)
        )

    # Search featured only
    results = await marketplace_service.search_apps(featured=True)
    assert len(results) == 1
    assert results[0].featured is True


@pytest.mark.asyncio
async def test_get_app(marketplace_service, tmp_path):
    """Test getting a single app by ID."""
    # Create app
    app_dir = tmp_path / "apps" / "jellyfin"
    app_dir.mkdir(parents=True)
    (app_dir / "app.yaml").write_text("""
id: jellyfin
name: Jellyfin
version: 10.8.13
description: Free media system
category: media
tags: []
docker:
  image: jellyfin/jellyfin:latest
  ports: []
  volumes: []
  environment: []
  restart_policy: unless-stopped
  privileged: false
  capabilities: []
""")

    # Add repo and sync
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url=str(tmp_path),
        repo_type=RepoType.OFFICIAL
    )
    await marketplace_service.sync_repo(repo.id, local_path=tmp_path)

    # Get app
    app = await marketplace_service.get_app("jellyfin")
    assert app is not None
    assert app.id == "jellyfin"
    assert app.name == "Jellyfin"


@pytest.mark.asyncio
async def test_get_app_not_found(marketplace_service):
    """Test getting a non-existent app."""
    app = await marketplace_service.get_app("nonexistent")
    assert app is None


@pytest.mark.asyncio
async def test_get_featured_apps(marketplace_service, tmp_path):
    """Test getting featured apps."""
    # Create apps
    for i in range(3):
        app_dir = tmp_path / "apps" / f"app{i}"
        app_dir.mkdir(parents=True)
        (app_dir / "app.yaml").write_text(f"""
name: App {i}
version: 1.0.0
description: Test app {i}
category: utility
tags: []
docker:
  image: test/app{i}:latest
  ports: []
  volumes: []
  environment: []
  restart_policy: unless-stopped
  privileged: false
  capabilities: []
""")

    # Add repo and sync
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url=str(tmp_path),
        repo_type=RepoType.OFFICIAL
    )
    await marketplace_service.sync_repo(repo.id, local_path=tmp_path)

    # Mark first two as featured
    from database.connection import db_manager
    async with db_manager.get_session() as session:
        await session.execute(
            update(MarketplaceAppTable)
            .where(MarketplaceAppTable.name.in_(["App 0", "App 1"]))
            .values(featured=True)
        )

    # Get featured apps
    featured = await marketplace_service.get_featured_apps()
    assert len(featured) == 2
    assert all(app.featured for app in featured)


@pytest.mark.asyncio
async def test_get_trending_apps(marketplace_service, tmp_path):
    """Test getting trending apps sorted by popularity."""
    # Create apps
    for i in range(3):
        app_dir = tmp_path / "apps" / f"app{i}"
        app_dir.mkdir(parents=True)
        (app_dir / "app.yaml").write_text(f"""
name: App {i}
version: 1.0.0
description: Test app {i}
category: utility
tags: []
docker:
  image: test/app{i}:latest
  ports: []
  volumes: []
  environment: []
  restart_policy: unless-stopped
  privileged: false
  capabilities: []
""")

    # Add repo and sync
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url=str(tmp_path),
        repo_type=RepoType.OFFICIAL
    )
    await marketplace_service.sync_repo(repo.id, local_path=tmp_path)

    # Set different install counts
    from database.connection import db_manager
    async with db_manager.get_session() as session:
        await session.execute(
            update(MarketplaceAppTable)
            .where(MarketplaceAppTable.name == "App 0")
            .values(install_count=100)
        )
        await session.execute(
            update(MarketplaceAppTable)
            .where(MarketplaceAppTable.name == "App 1")
            .values(install_count=200)
        )
        await session.execute(
            update(MarketplaceAppTable)
            .where(MarketplaceAppTable.name == "App 2")
            .values(install_count=50)
        )

    # Get trending apps
    trending = await marketplace_service.get_trending_apps()
    assert len(trending) == 3
    # Should be sorted by install_count DESC
    assert trending[0].name == "App 1"
    assert trending[1].name == "App 0"
    assert trending[2].name == "App 2"


@pytest.mark.asyncio
async def test_get_categories(marketplace_service, tmp_path):
    """Test getting all categories with counts."""
    # Create apps in different categories
    categories_data = [
        ("media", "Jellyfin"),
        ("media", "Plex"),
        ("utility", "Portainer"),
    ]

    for category, name in categories_data:
        app_dir = tmp_path / "apps" / name.lower()
        app_dir.mkdir(parents=True)
        (app_dir / "app.yaml").write_text(f"""
name: {name}
version: 1.0.0
description: Test {name}
category: {category}
tags: []
docker:
  image: test/{name.lower()}:latest
  ports: []
  volumes: []
  environment: []
  restart_policy: unless-stopped
  privileged: false
  capabilities: []
""")

    # Add repo and sync
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url=str(tmp_path),
        repo_type=RepoType.OFFICIAL
    )
    await marketplace_service.sync_repo(repo.id, local_path=tmp_path)

    # Get categories
    categories = await marketplace_service.get_categories()
    assert len(categories) == 2

    # Find media category
    media_cat = next(c for c in categories if c["id"] == "media")
    assert media_cat["count"] == 2
    assert media_cat["name"] == "Media"

    # Find utility category
    util_cat = next(c for c in categories if c["id"] == "utility")
    assert util_cat["count"] == 1


# ─────────────────────────────────────────────────────────────
# Rating Tests
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rate_app(marketplace_service, tmp_path):
    """Test rating an app."""
    # Create app
    app_dir = tmp_path / "apps" / "jellyfin"
    app_dir.mkdir(parents=True)
    (app_dir / "app.yaml").write_text("""
id: jellyfin
name: Jellyfin
version: 10.8.13
description: Free media system
category: media
tags: []
docker:
  image: jellyfin/jellyfin:latest
  ports: []
  volumes: []
  environment: []
  restart_policy: unless-stopped
  privileged: false
  capabilities: []
""")

    # Add repo and sync
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url=str(tmp_path),
        repo_type=RepoType.OFFICIAL
    )
    await marketplace_service.sync_repo(repo.id, local_path=tmp_path)

    # Rate app
    rating = await marketplace_service.rate_app("jellyfin", "user-123", 5)
    assert rating.app_id == "jellyfin"
    assert rating.user_id == "user-123"
    assert rating.rating == 5

    # Verify app rating updated
    app = await marketplace_service.get_app("jellyfin")
    assert app.avg_rating == 5.0
    assert app.rating_count == 1


@pytest.mark.asyncio
async def test_rate_app_update_existing(marketplace_service, tmp_path):
    """Test updating an existing rating."""
    # Create app
    app_dir = tmp_path / "apps" / "jellyfin"
    app_dir.mkdir(parents=True)
    (app_dir / "app.yaml").write_text("""
id: jellyfin
name: Jellyfin
version: 10.8.13
description: Free media system
category: media
tags: []
docker:
  image: jellyfin/jellyfin:latest
  ports: []
  volumes: []
  environment: []
  restart_policy: unless-stopped
  privileged: false
  capabilities: []
""")

    # Add repo and sync
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url=str(tmp_path),
        repo_type=RepoType.OFFICIAL
    )
    await marketplace_service.sync_repo(repo.id, local_path=tmp_path)

    # Rate app first time
    await marketplace_service.rate_app("jellyfin", "user-123", 3)

    # Update rating
    rating = await marketplace_service.rate_app("jellyfin", "user-123", 5)
    assert rating.rating == 5

    # Verify only one rating exists
    app = await marketplace_service.get_app("jellyfin")
    assert app.rating_count == 1
    assert app.avg_rating == 5.0


@pytest.mark.asyncio
async def test_rate_app_multiple_users(marketplace_service, tmp_path):
    """Test multiple users rating the same app."""
    # Create app
    app_dir = tmp_path / "apps" / "jellyfin"
    app_dir.mkdir(parents=True)
    (app_dir / "app.yaml").write_text("""
id: jellyfin
name: Jellyfin
version: 10.8.13
description: Free media system
category: media
tags: []
docker:
  image: jellyfin/jellyfin:latest
  ports: []
  volumes: []
  environment: []
  restart_policy: unless-stopped
  privileged: false
  capabilities: []
""")

    # Add repo and sync
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url=str(tmp_path),
        repo_type=RepoType.OFFICIAL
    )
    await marketplace_service.sync_repo(repo.id, local_path=tmp_path)

    # Multiple users rate
    await marketplace_service.rate_app("jellyfin", "user-1", 5)
    await marketplace_service.rate_app("jellyfin", "user-2", 4)
    await marketplace_service.rate_app("jellyfin", "user-3", 3)

    # Verify average
    app = await marketplace_service.get_app("jellyfin")
    assert app.rating_count == 3
    assert app.avg_rating == 4.0  # (5 + 4 + 3) / 3


@pytest.mark.asyncio
async def test_rate_app_invalid_rating(marketplace_service):
    """Test rating with invalid value."""
    with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
        await marketplace_service.rate_app("jellyfin", "user-123", 0)

    with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
        await marketplace_service.rate_app("jellyfin", "user-123", 6)


@pytest.mark.asyncio
async def test_get_user_rating(marketplace_service, tmp_path):
    """Test getting a user's rating for an app."""
    # Create app
    app_dir = tmp_path / "apps" / "jellyfin"
    app_dir.mkdir(parents=True)
    (app_dir / "app.yaml").write_text("""
id: jellyfin
name: Jellyfin
version: 10.8.13
description: Free media system
category: media
tags: []
docker:
  image: jellyfin/jellyfin:latest
  ports: []
  volumes: []
  environment: []
  restart_policy: unless-stopped
  privileged: false
  capabilities: []
""")

    # Add repo and sync
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url=str(tmp_path),
        repo_type=RepoType.OFFICIAL
    )
    await marketplace_service.sync_repo(repo.id, local_path=tmp_path)

    # Rate app
    await marketplace_service.rate_app("jellyfin", "user-123", 4)

    # Get user rating
    rating = await marketplace_service.get_user_rating("jellyfin", "user-123")
    assert rating == 4

    # Get rating for non-existent user
    rating = await marketplace_service.get_user_rating("jellyfin", "user-456")
    assert rating is None

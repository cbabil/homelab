"""Tests for marketplace database schema."""

from __future__ import annotations

import pytest
from datetime import datetime
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from database.connection import Base, db_manager
from models.marketplace import (
    MarketplaceRepoTable,
    MarketplaceAppTable,
    AppRatingTable,
)
from init_db.schema_marketplace import (
    initialize_marketplace_database,
    check_marketplace_schema_exists,
)


@pytest.fixture
async def test_db():
    """Create test database with marketplace schema."""
    await db_manager.initialize()
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_marketplace_repo_table_exists(test_db):
    """Verify marketplace_repos table is created with correct columns."""
    async with db_manager.engine.begin() as conn:
        inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
        tables = await conn.run_sync(lambda sync_conn: inspector.get_table_names())

    assert "marketplace_repos" in tables

    # Check columns
    async with db_manager.engine.begin() as conn:
        columns = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_columns("marketplace_repos")
        )

    column_names = {col["name"] for col in columns}
    expected_columns = {
        "id", "name", "url", "branch", "repo_type", "enabled",
        "status", "last_synced", "app_count", "error_message",
        "created_at", "updated_at"
    }
    assert expected_columns.issubset(column_names)


@pytest.mark.asyncio
async def test_marketplace_app_table_exists(test_db):
    """Verify marketplace_apps table is created with correct columns."""
    async with db_manager.engine.begin() as conn:
        inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
        tables = await conn.run_sync(lambda sync_conn: inspector.get_table_names())

    assert "marketplace_apps" in tables

    # Check columns
    async with db_manager.engine.begin() as conn:
        columns = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_columns("marketplace_apps")
        )

    column_names = {col["name"] for col in columns}
    expected_columns = {
        "id", "name", "description", "long_description", "version",
        "category", "tags", "icon", "author", "license", "repository",
        "documentation", "repo_id", "docker_config", "requirements",
        "install_count", "avg_rating", "rating_count", "featured",
        "created_at", "updated_at"
    }
    assert expected_columns.issubset(column_names)


@pytest.mark.asyncio
async def test_app_rating_table_exists(test_db):
    """Verify app_ratings table is created with correct columns."""
    async with db_manager.engine.begin() as conn:
        inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
        tables = await conn.run_sync(lambda sync_conn: inspector.get_table_names())

    assert "app_ratings" in tables

    # Check columns
    async with db_manager.engine.begin() as conn:
        columns = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_columns("app_ratings")
        )

    column_names = {col["name"] for col in columns}
    expected_columns = {"id", "app_id", "user_id", "rating", "created_at", "updated_at"}
    assert expected_columns.issubset(column_names)


@pytest.mark.asyncio
async def test_create_marketplace_repo(test_db):
    """Test creating a marketplace repository record."""
    async with db_manager.get_session() as session:
        repo = MarketplaceRepoTable(
            id="test-repo",
            name="Test Repository",
            url="https://github.com/test/repo",
            branch="main",
            repo_type="community",
            enabled=True,
            status="active",
            app_count=0
        )
        session.add(repo)
        await session.commit()

        # Verify it was created
        result = await session.execute(
            select(MarketplaceRepoTable).where(MarketplaceRepoTable.id == "test-repo")
        )
        saved_repo = result.scalar_one_or_none()

    assert saved_repo is not None
    assert saved_repo.name == "Test Repository"
    assert saved_repo.url == "https://github.com/test/repo"
    assert saved_repo.branch == "main"
    assert saved_repo.enabled is True
    assert saved_repo.created_at is not None
    assert saved_repo.updated_at is not None


@pytest.mark.asyncio
async def test_create_marketplace_app_with_repo(test_db):
    """Test creating a marketplace app with repository relationship."""
    async with db_manager.get_session() as session:
        # Create repo first
        repo = MarketplaceRepoTable(
            id="test-repo",
            name="Test Repository",
            url="https://github.com/test/repo",
        )
        session.add(repo)

        # Create app
        app = MarketplaceAppTable(
            id="test-app",
            name="Test App",
            description="A test application",
            version="1.0.0",
            category="media",
            tags='["docker", "media"]',
            author="Test Author",
            license="MIT",
            repo_id="test-repo",
            docker_config='{"image": "test/app:latest"}',
            install_count=0,
            rating_count=0,
            featured=False
        )
        session.add(app)
        await session.commit()

        # Verify relationship
        result = await session.execute(
            select(MarketplaceAppTable).where(MarketplaceAppTable.id == "test-app")
        )
        saved_app = result.scalar_one_or_none()

    assert saved_app is not None
    assert saved_app.name == "Test App"
    assert saved_app.repo_id == "test-repo"
    assert saved_app.category == "media"
    assert saved_app.created_at is not None


@pytest.mark.asyncio
async def test_create_app_rating(test_db):
    """Test creating an app rating."""
    async with db_manager.get_session() as session:
        # Create repo and app first
        repo = MarketplaceRepoTable(
            id="test-repo",
            name="Test Repository",
            url="https://github.com/test/repo",
        )
        session.add(repo)

        app = MarketplaceAppTable(
            id="test-app",
            name="Test App",
            description="A test application",
            version="1.0.0",
            category="media",
            author="Test Author",
            license="MIT",
            repo_id="test-repo",
            docker_config='{"image": "test/app:latest"}',
        )
        session.add(app)

        # Create rating
        rating = AppRatingTable(
            id="rating-1",
            app_id="test-app",
            user_id="user-1",
            rating=5
        )
        session.add(rating)
        await session.commit()

        # Verify
        result = await session.execute(
            select(AppRatingTable).where(AppRatingTable.id == "rating-1")
        )
        saved_rating = result.scalar_one_or_none()

    assert saved_rating is not None
    assert saved_rating.app_id == "test-app"
    assert saved_rating.user_id == "user-1"
    assert saved_rating.rating == 5
    assert saved_rating.created_at is not None


@pytest.mark.asyncio
async def test_app_rating_unique_constraint(test_db):
    """Test that app_id + user_id must be unique."""
    async with db_manager.get_session() as session:
        # Create repo and app
        repo = MarketplaceRepoTable(
            id="test-repo",
            name="Test Repository",
            url="https://github.com/test/repo",
        )
        session.add(repo)

        app = MarketplaceAppTable(
            id="test-app",
            name="Test App",
            description="A test application",
            version="1.0.0",
            category="media",
            author="Test Author",
            license="MIT",
            repo_id="test-repo",
            docker_config='{"image": "test/app:latest"}',
        )
        session.add(app)

        # Create first rating
        rating1 = AppRatingTable(
            id="rating-1",
            app_id="test-app",
            user_id="user-1",
            rating=5
        )
        session.add(rating1)
        await session.commit()

    # Try to create duplicate
    with pytest.raises(IntegrityError):
        async with db_manager.get_session() as session:
            rating2 = AppRatingTable(
                id="rating-2",
                app_id="test-app",
                user_id="user-1",
                rating=4
            )
            session.add(rating2)
            await session.commit()


@pytest.mark.asyncio
async def test_marketplace_repo_defaults(test_db):
    """Test default values for marketplace repo."""
    async with db_manager.get_session() as session:
        repo = MarketplaceRepoTable(
            id="test-repo",
            name="Test Repository",
            url="https://github.com/test/repo",
        )
        session.add(repo)
        await session.commit()

        result = await session.execute(
            select(MarketplaceRepoTable).where(MarketplaceRepoTable.id == "test-repo")
        )
        saved_repo = result.scalar_one_or_none()

    assert saved_repo.branch == "main"
    assert saved_repo.repo_type == "community"
    assert saved_repo.enabled is True
    assert saved_repo.status == "active"
    assert saved_repo.app_count == 0


@pytest.mark.asyncio
async def test_initialize_marketplace_database():
    """Test the initialize_marketplace_database function."""
    # Clean up first
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Check schema doesn't exist
    exists_before = await check_marketplace_schema_exists()
    assert exists_before is False

    # Initialize
    await initialize_marketplace_database()

    # Check schema exists now
    exists_after = await check_marketplace_schema_exists()
    assert exists_after is True

    # Clean up
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

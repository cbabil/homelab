"""Tests for CLI commands."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from cli import create_admin_user


class TestCreateAdminCLI:
    """Tests for admin creation CLI."""

    @pytest.mark.asyncio
    async def test_create_admin_success(self):
        """Should create admin user successfully."""
        with patch('cli.DatabaseService') as mock_db_class:
            mock_db = MagicMock()
            mock_db.get_user_by_username = AsyncMock(return_value=None)
            mock_db.create_user = AsyncMock(return_value=MagicMock(
                id="admin-123",
                username="admin"
            ))
            mock_db_class.return_value = mock_db

            result = await create_admin_user(
                username="admin",
                email="admin@example.com",
                password="SecureAdmin123!"
            )

            assert result is True
            mock_db.create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_admin_already_exists(self):
        """Should fail if admin already exists."""
        with patch('cli.DatabaseService') as mock_db_class:
            mock_db = MagicMock()
            mock_db.get_user_by_username = AsyncMock(return_value=MagicMock())
            mock_db_class.return_value = mock_db

            result = await create_admin_user(
                username="admin",
                email="admin@example.com",
                password="SecureAdmin123!"
            )

            assert result is False

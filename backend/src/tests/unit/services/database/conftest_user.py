"""
Shared fixtures and helpers for user_service tests.
"""

import json
import pytest
from unittest.mock import MagicMock
from contextlib import asynccontextmanager


@pytest.fixture
def mock_connection():
    """Create mock DatabaseConnection."""
    return MagicMock()


def create_mock_context(mock_conn):
    """Create async context manager for database connection."""

    @asynccontextmanager
    async def context():
        yield mock_conn

    return context()


def create_user_row(
    user_id="user-123",
    username="testuser",
    email="test@example.com",
    role="user",
    created_at="2024-01-01T00:00:00Z",
    last_login="2024-01-02T00:00:00Z",
    password_changed_at="2024-01-01T00:00:00Z",
    is_active=1,
    preferences_json=None,
    avatar=None,
):
    """Create a mock user row dict."""
    return {
        "id": user_id,
        "username": username,
        "email": email,
        "role": role,
        "created_at": created_at,
        "last_login": last_login,
        "password_changed_at": password_changed_at,
        "is_active": is_active,
        "preferences_json": preferences_json,
        "avatar": avatar,
    }

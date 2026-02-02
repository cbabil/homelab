# Phase 1: Foundation & Auth - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the foundation and authentication layer, ensuring all quality gates pass.

**Architecture:** FastMCP backend with SQLite persistence, React frontend with JWT-based auth. MCP tools provide the API layer.

**Tech Stack:** Python 3.11+, FastMCP, SQLite, React 18, TypeScript, Vite

---

## Current State Assessment

### Already Implemented
- FastMCP server with CORS middleware (`backend/src/main.py`)
- SQLite database with async connection (`backend/src/database/`)
- User model with roles (`backend/src/models/auth.py`)
- Auth service with JWT + bcrypt (`backend/src/services/auth_service.py`)
- Auth tools: login, logout, validate_token (`backend/src/tools/auth_tools.py`)
- Structured logging via structlog
- React app with routing (`frontend/src/App.tsx`)
- Login/Registration pages
- AuthProvider with JWT support
- ProtectedRoute wrapper

### Missing for Phase 1 Completion
1. ❌ `get_current_user()` MCP tool
2. ❌ `create_user()` MCP tool (admin only)
3. ❌ `list_users()` MCP tool (admin only)
4. ❌ CLI command for first-run admin creation
5. ❌ Health endpoint verification
6. ❌ Quality gates: run all tests, verify 90% coverage

---

## Task 1: Add get_current_user MCP Tool

**Files:**
- Modify: `backend/src/tools/auth_tools.py`
- Test: `backend/tests/unit/test_auth_tools.py` (create)

**Step 1: Write the failing test**

Create `backend/tests/unit/test_auth_tools.py`:

```python
"""Tests for auth tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from tools.auth_tools import AuthTools
from models.auth import User, UserRole


@pytest.fixture
def mock_auth_service():
    """Create mock auth service."""
    service = MagicMock()
    service.get_user_by_id = AsyncMock()
    service._validate_jwt_token = MagicMock()
    return service


@pytest.fixture
def auth_tools(mock_auth_service):
    """Create auth tools with mock service."""
    return AuthTools(mock_auth_service)


class TestGetCurrentUser:
    """Tests for get_current_user tool."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, auth_tools, mock_auth_service):
        """Should return user data for valid token."""
        # Arrange
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
            last_login="2025-01-01T00:00:00Z",
            is_active=True
        )
        mock_auth_service._validate_jwt_token.return_value = {
            "user_id": "user-123",
            "username": "testuser"
        }
        mock_auth_service.get_user_by_id.return_value = user

        # Act
        result = await auth_tools.get_current_user(token="valid-token")

        # Assert
        assert result["success"] is True
        assert result["data"]["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, auth_tools, mock_auth_service):
        """Should return error for invalid token."""
        mock_auth_service._validate_jwt_token.return_value = None

        result = await auth_tools.get_current_user(token="invalid-token")

        assert result["success"] is False
        assert result["error"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_get_current_user_inactive_user(self, auth_tools, mock_auth_service):
        """Should return error for inactive user."""
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
            last_login="2025-01-01T00:00:00Z",
            is_active=False
        )
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id.return_value = user

        result = await auth_tools.get_current_user(token="valid-token")

        assert result["success"] is False
        assert result["error"] == "USER_INACTIVE"
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && pytest tests/unit/test_auth_tools.py -v
```

Expected: FAIL - `AttributeError: 'AuthTools' object has no attribute 'get_current_user'`

**Step 3: Write minimal implementation**

Add to `backend/src/tools/auth_tools.py` in the `AuthTools` class:

```python
async def get_current_user(self, token: str) -> Dict[str, Any]:
    """Get current user from JWT token."""
    try:
        payload = self.auth_service._validate_jwt_token(token)

        if not payload:
            return {
                "success": False,
                "message": "Invalid or expired token",
                "error": "INVALID_TOKEN"
            }

        user_id = payload.get("user_id")
        user = await self.auth_service.get_user_by_id(user_id) if user_id else None

        if not user or not user.is_active:
            return {
                "success": False,
                "message": "User not found or inactive",
                "error": "USER_INACTIVE"
            }

        return {
            "success": True,
            "data": {"user": user.model_dump()},
            "message": "User retrieved successfully"
        }

    except Exception as e:
        logger.error("Get current user error", error=str(e))
        return {
            "success": False,
            "message": f"Failed to get user: {str(e)}",
            "error": "GET_USER_ERROR"
        }
```

Also register the tool in `register_auth_tools()`:

```python
app.tool(auth_tools.get_current_user)
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && pytest tests/unit/test_auth_tools.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
cd /Users/christophebabilotte/source/tomo
git add backend/src/tools/auth_tools.py backend/tests/unit/test_auth_tools.py
git commit -m "feat(auth): add get_current_user MCP tool"
```

---

## Task 2: Add create_user MCP Tool (Admin Only)

**Files:**
- Modify: `backend/src/tools/auth_tools.py`
- Modify: `backend/src/services/auth_service.py`
- Test: `backend/tests/unit/test_auth_tools.py`

**Step 1: Write the failing test**

Add to `backend/tests/unit/test_auth_tools.py`:

```python
class TestCreateUser:
    """Tests for create_user tool (admin only)."""

    @pytest.mark.asyncio
    async def test_create_user_as_admin(self, auth_tools, mock_auth_service):
        """Admin should be able to create new user."""
        # Arrange
        admin = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            last_login="2025-01-01T00:00:00Z",
            is_active=True
        )
        new_user = User(
            id="user-456",
            username="newuser",
            email="new@example.com",
            role=UserRole.USER,
            last_login="2025-01-01T00:00:00Z",
            is_active=True
        )
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "admin-123"}
        mock_auth_service.get_user_by_id.return_value = admin
        mock_auth_service.create_user = AsyncMock(return_value=new_user)

        # Act
        result = await auth_tools.create_user(
            token="admin-token",
            username="newuser",
            email="new@example.com",
            password="SecurePass123!",
            role="user"
        )

        # Assert
        assert result["success"] is True
        assert result["data"]["user"]["username"] == "newuser"

    @pytest.mark.asyncio
    async def test_create_user_as_non_admin_fails(self, auth_tools, mock_auth_service):
        """Non-admin should not be able to create users."""
        regular_user = User(
            id="user-123",
            username="regular",
            email="regular@example.com",
            role=UserRole.USER,
            last_login="2025-01-01T00:00:00Z",
            is_active=True
        )
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id.return_value = regular_user

        result = await auth_tools.create_user(
            token="user-token",
            username="newuser",
            email="new@example.com",
            password="SecurePass123!",
            role="user"
        )

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && pytest tests/unit/test_auth_tools.py::TestCreateUser -v
```

Expected: FAIL - `AttributeError: 'AuthTools' object has no attribute 'create_user'`

**Step 3: Write minimal implementation**

First, add `create_user` to `backend/src/services/auth_service.py`:

```python
async def create_user(
    self,
    username: str,
    email: str,
    password: str,
    role: UserRole = UserRole.USER
) -> Optional[User]:
    """Create a new user in the database."""
    try:
        from lib.auth_helpers import hash_password
        password_hash = hash_password(password)

        user = await self.db_service.create_user(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role
        )

        logger.info("User created", username=username, role=role.value)
        return user

    except Exception as e:
        logger.error("Failed to create user", username=username, error=str(e))
        return None
```

Then add to `backend/src/tools/auth_tools.py` in `AuthTools` class:

```python
async def create_user(
    self,
    token: str,
    username: str,
    email: str,
    password: str,
    role: str = "user"
) -> Dict[str, Any]:
    """Create a new user (admin only)."""
    try:
        # Validate admin token
        payload = self.auth_service._validate_jwt_token(token)
        if not payload:
            return {"success": False, "message": "Invalid token", "error": "INVALID_TOKEN"}

        # Check if requesting user is admin
        admin_user = await self.auth_service.get_user_by_id(payload.get("user_id"))
        if not admin_user or admin_user.role != UserRole.ADMIN:
            return {
                "success": False,
                "message": "Admin privileges required",
                "error": "PERMISSION_DENIED"
            }

        # Create the new user
        from models.auth import UserRole
        user_role = UserRole.ADMIN if role == "admin" else UserRole.USER

        new_user = await self.auth_service.create_user(
            username=username,
            email=email,
            password=password,
            role=user_role
        )

        if not new_user:
            return {
                "success": False,
                "message": "Failed to create user",
                "error": "CREATE_USER_ERROR"
            }

        return {
            "success": True,
            "data": {"user": new_user.model_dump()},
            "message": "User created successfully"
        }

    except Exception as e:
        logger.error("Create user error", error=str(e))
        return {
            "success": False,
            "message": f"Failed to create user: {str(e)}",
            "error": "CREATE_USER_ERROR"
        }
```

Register the tool:

```python
app.tool(auth_tools.create_user)
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && pytest tests/unit/test_auth_tools.py::TestCreateUser -v
```

Expected: PASS

**Step 5: Commit**

```bash
cd /Users/christophebabilotte/source/tomo
git add backend/src/tools/auth_tools.py backend/src/services/auth_service.py backend/tests/unit/test_auth_tools.py
git commit -m "feat(auth): add create_user MCP tool with admin-only access"
```

---

## Task 3: Add list_users MCP Tool (Admin Only)

**Files:**
- Modify: `backend/src/tools/auth_tools.py`
- Test: `backend/tests/unit/test_auth_tools.py`

**Step 1: Write the failing test**

Add to `backend/tests/unit/test_auth_tools.py`:

```python
class TestListUsers:
    """Tests for list_users tool (admin only)."""

    @pytest.mark.asyncio
    async def test_list_users_as_admin(self, auth_tools, mock_auth_service):
        """Admin should be able to list all users."""
        admin = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            last_login="2025-01-01T00:00:00Z",
            is_active=True
        )
        users = [
            admin,
            User(
                id="user-456",
                username="user1",
                email="user1@example.com",
                role=UserRole.USER,
                last_login="2025-01-01T00:00:00Z",
                is_active=True
            )
        ]
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "admin-123"}
        mock_auth_service.get_user_by_id.return_value = admin
        mock_auth_service.get_all_users = AsyncMock(return_value=users)

        result = await auth_tools.list_users(token="admin-token")

        assert result["success"] is True
        assert len(result["data"]["users"]) == 2

    @pytest.mark.asyncio
    async def test_list_users_as_non_admin_fails(self, auth_tools, mock_auth_service):
        """Non-admin should not be able to list users."""
        regular_user = User(
            id="user-123",
            username="regular",
            email="regular@example.com",
            role=UserRole.USER,
            last_login="2025-01-01T00:00:00Z",
            is_active=True
        )
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id.return_value = regular_user

        result = await auth_tools.list_users(token="user-token")

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && pytest tests/unit/test_auth_tools.py::TestListUsers -v
```

Expected: FAIL

**Step 3: Write minimal implementation**

Add to `backend/src/tools/auth_tools.py` in `AuthTools` class:

```python
async def list_users(self, token: str) -> Dict[str, Any]:
    """List all users (admin only)."""
    try:
        # Validate admin token
        payload = self.auth_service._validate_jwt_token(token)
        if not payload:
            return {"success": False, "message": "Invalid token", "error": "INVALID_TOKEN"}

        # Check if requesting user is admin
        admin_user = await self.auth_service.get_user_by_id(payload.get("user_id"))
        if not admin_user or admin_user.role != UserRole.ADMIN:
            return {
                "success": False,
                "message": "Admin privileges required",
                "error": "PERMISSION_DENIED"
            }

        # Get all users
        users = await self.auth_service.get_all_users()

        return {
            "success": True,
            "data": {"users": [u.model_dump() for u in users]},
            "message": f"Retrieved {len(users)} users"
        }

    except Exception as e:
        logger.error("List users error", error=str(e))
        return {
            "success": False,
            "message": f"Failed to list users: {str(e)}",
            "error": "LIST_USERS_ERROR"
        }
```

Register the tool:

```python
app.tool(auth_tools.list_users)
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && pytest tests/unit/test_auth_tools.py::TestListUsers -v
```

Expected: PASS

**Step 5: Commit**

```bash
cd /Users/christophebabilotte/source/tomo
git add backend/src/tools/auth_tools.py backend/tests/unit/test_auth_tools.py
git commit -m "feat(auth): add list_users MCP tool with admin-only access"
```

---

## Task 4: Add CLI for First-Run Admin Creation

**Files:**
- Create: `backend/src/cli.py`
- Create: `backend/tests/unit/test_cli.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_cli.py`:

```python
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
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && pytest tests/unit/test_cli.py -v
```

Expected: FAIL - `ModuleNotFoundError: No module named 'cli'`

**Step 3: Write minimal implementation**

Create `backend/src/cli.py`:

```python
#!/usr/bin/env python3
"""
Tomo CLI

Provides command-line utilities for administration tasks.
"""

import argparse
import asyncio
import sys
import getpass
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from services.database_service import DatabaseService
from models.auth import UserRole
from lib.auth_helpers import hash_password
from lib.config import load_config, resolve_data_directory


async def create_admin_user(
    username: str,
    email: str,
    password: str,
    data_directory: str = None
) -> bool:
    """Create the initial admin user."""
    try:
        config = load_config()
        data_dir = data_directory or resolve_data_directory(config)

        db_service = DatabaseService(data_directory=data_dir)

        # Check if user already exists
        existing = await db_service.get_user_by_username(username)
        if existing:
            print(f"Error: User '{username}' already exists")
            return False

        # Create admin user
        password_hash = hash_password(password)
        user = await db_service.create_user(
            username=username,
            email=email,
            password_hash=password_hash,
            role=UserRole.ADMIN
        )

        if user:
            print(f"Admin user '{username}' created successfully")
            return True
        else:
            print("Error: Failed to create admin user")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Tomo CLI",
        prog="tomo"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # create-admin command
    admin_parser = subparsers.add_parser(
        "create-admin",
        help="Create the initial admin user"
    )
    admin_parser.add_argument(
        "--username", "-u",
        required=True,
        help="Admin username"
    )
    admin_parser.add_argument(
        "--email", "-e",
        required=True,
        help="Admin email address"
    )
    admin_parser.add_argument(
        "--password", "-p",
        help="Admin password (will prompt if not provided)"
    )
    admin_parser.add_argument(
        "--data-dir", "-d",
        help="Data directory path"
    )

    args = parser.parse_args()

    if args.command == "create-admin":
        password = args.password
        if not password:
            password = getpass.getpass("Enter admin password: ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Error: Passwords do not match")
                sys.exit(1)

        success = asyncio.run(create_admin_user(
            username=args.username,
            email=args.email,
            password=password,
            data_directory=args.data_dir
        ))
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && pytest tests/unit/test_cli.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
cd /Users/christophebabilotte/source/tomo
git add backend/src/cli.py backend/tests/unit/test_cli.py
git commit -m "feat(cli): add create-admin CLI command for first-run setup"
```

---

## Task 5: Add Health Endpoint Tool

**Files:**
- Review: `backend/src/tools/health_tools.py`
- Test: `backend/tests/unit/test_health_tools.py`

**Step 1: Verify health tool exists and test it**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && pytest tests/unit/test_health_tools.py -v
```

If tests pass, skip to commit. If not, fix any issues.

**Step 2: Commit (if changes needed)**

```bash
cd /Users/christophebabilotte/source/tomo
git add backend/src/tools/health_tools.py backend/tests/unit/test_health_tools.py
git commit -m "fix(health): ensure health endpoint works correctly"
```

---

## Task 6: Run Full Test Suite and Verify Quality Gates

**Step 1: Run backend tests with coverage**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && pytest --cov=src --cov-report=term-missing -v
```

Target: 90% coverage. Fix any failing tests.

**Step 2: Run frontend tests**

```bash
cd /Users/christophebabilotte/source/tomo/frontend && source /Users/christophebabilotte/source/tomo/venv/bin/activate && yarn test
```

Fix any failing tests.

**Step 3: Run frontend lint and type-check**

```bash
cd /Users/christophebabilotte/source/tomo/frontend && source /Users/christophebabilotte/source/tomo/venv/bin/activate && yarn lint && yarn type-check
```

Fix any errors.

**Step 4: Run E2E tests**

```bash
cd /Users/christophebabilotte/source/tomo/frontend && source /Users/christophebabilotte/source/tomo/venv/bin/activate && yarn test:e2e
```

Fix any failing E2E tests.

**Step 5: Final commit for Phase 1**

```bash
cd /Users/christophebabilotte/source/tomo
git add .
git commit -m "chore: Phase 1 complete - foundation and auth verified"
```

---

## Quality Gates Checklist

- [ ] Backend unit tests passing (90%+ coverage)
- [ ] Frontend component tests passing
- [ ] E2E test: login flow working
- [ ] Security: no plaintext passwords, JWT expiry works
- [ ] Linting/type-check passes
- [ ] All MCP tools implemented:
  - [ ] login
  - [ ] logout
  - [ ] validate_token
  - [ ] get_current_user
  - [ ] create_user (admin only)
  - [ ] list_users (admin only)
- [ ] CLI: create-admin command works

---

**Document Version:** 1.0
**Created:** 2025-12-25

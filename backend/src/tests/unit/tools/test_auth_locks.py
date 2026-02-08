"""
Auth Tools Unit Tests - Account Lock Operations

Tests for get_locked_accounts and update_account_lock methods.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tools.auth.tools import AuthTools


class TestGetLockedAccounts:
    """Tests for get_locked_accounts method."""

    @pytest.fixture
    def mock_auth_service(self):
        """Create mock auth service."""
        return MagicMock()

    @pytest.fixture
    def auth_tools(self, mock_auth_service):
        """Create AuthTools instance."""
        with patch("tools.auth.tools.logger"):
            return AuthTools(mock_auth_service)

    @pytest.fixture
    def admin_user(self):
        """Create admin user mock."""
        user = MagicMock()
        user.is_active = True
        user.username = "admin"
        user.role = MagicMock()
        user.role.value = "admin"
        return user

    @pytest.fixture
    def regular_user(self):
        """Create regular user mock."""
        user = MagicMock()
        user.is_active = True
        user.username = "user"
        user.role = MagicMock()
        user.role.value = "user"
        return user

    @pytest.mark.asyncio
    async def test_missing_token(self, auth_tools):
        """Test get_locked_accounts without token."""
        result = await auth_tools.get_locked_accounts({})
        assert result["success"] is False
        assert result["error"] == "MISSING_TOKEN"

    @pytest.mark.asyncio
    async def test_invalid_token(self, auth_tools, mock_auth_service):
        """Test get_locked_accounts with invalid token."""
        mock_auth_service._validate_jwt_token.return_value = None

        result = await auth_tools.get_locked_accounts({"token": "invalid"})
        assert result["success"] is False
        assert result["error"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_user_inactive(self, auth_tools, mock_auth_service):
        """Test get_locked_accounts when user inactive."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = False
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)

        result = await auth_tools.get_locked_accounts({"token": "valid"})
        assert result["success"] is False
        assert result["error"] == "USER_INACTIVE"

    @pytest.mark.asyncio
    async def test_non_admin_user(self, auth_tools, mock_auth_service, regular_user):
        """Test get_locked_accounts by non-admin."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id = AsyncMock(return_value=regular_user)

        result = await auth_tools.get_locked_accounts({"token": "valid"})
        assert result["success"] is False
        assert result["error"] == "ADMIN_REQUIRED"

    @pytest.mark.asyncio
    async def test_get_by_lock_id_found(
        self, auth_tools, mock_auth_service, admin_user
    ):
        """Test get_locked_accounts by lock_id - found."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_auth_service.db_service.get_lock_by_id = AsyncMock(
            return_value={"id": "lock-123", "identifier": "testuser"}
        )

        result = await auth_tools.get_locked_accounts(
            {
                "token": "valid",
                "lock_id": "lock-123",
            }
        )

        assert result["success"] is True
        assert result["data"]["count"] == 1

    @pytest.mark.asyncio
    async def test_get_by_lock_id_not_found(
        self, auth_tools, mock_auth_service, admin_user
    ):
        """Test get_locked_accounts by lock_id - not found."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_auth_service.db_service.get_lock_by_id = AsyncMock(return_value=None)

        result = await auth_tools.get_locked_accounts(
            {
                "token": "valid",
                "lock_id": "lock-123",
            }
        )

        assert result["success"] is False
        assert result["error"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_by_identifier_missing_type(
        self, auth_tools, mock_auth_service, admin_user
    ):
        """Test get_locked_accounts by identifier without type."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id = AsyncMock(return_value=admin_user)

        result = await auth_tools.get_locked_accounts(
            {
                "token": "valid",
                "identifier": "testuser",
            }
        )

        assert result["success"] is False
        assert result["error"] == "MISSING_IDENTIFIER_TYPE"

    @pytest.mark.asyncio
    async def test_get_by_identifier_invalid_type(
        self, auth_tools, mock_auth_service, admin_user
    ):
        """Test get_locked_accounts by identifier with invalid type."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id = AsyncMock(return_value=admin_user)

        result = await auth_tools.get_locked_accounts(
            {
                "token": "valid",
                "identifier": "testuser",
                "identifier_type": "email",
            }
        )

        assert result["success"] is False
        assert result["error"] == "INVALID_IDENTIFIER_TYPE"

    @pytest.mark.asyncio
    async def test_get_by_identifier_found(
        self, auth_tools, mock_auth_service, admin_user
    ):
        """Test get_locked_accounts by identifier - found."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_auth_service.db_service.is_account_locked = AsyncMock(
            return_value=(True, {"id": "lock-123", "identifier": "testuser"})
        )

        result = await auth_tools.get_locked_accounts(
            {
                "token": "valid",
                "identifier": "testuser",
                "identifier_type": "username",
            }
        )

        assert result["success"] is True
        assert result["data"]["is_locked"] is True
        assert result["data"]["count"] == 1

    @pytest.mark.asyncio
    async def test_get_by_identifier_not_found(
        self, auth_tools, mock_auth_service, admin_user
    ):
        """Test get_locked_accounts by identifier - not found."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_auth_service.db_service.is_account_locked = AsyncMock(
            return_value=(False, None)
        )

        result = await auth_tools.get_locked_accounts(
            {
                "token": "valid",
                "identifier": "testuser",
                "identifier_type": "username",
            }
        )

        assert result["success"] is True
        assert result["data"]["is_locked"] is False
        assert result["data"]["count"] == 0

    @pytest.mark.asyncio
    async def test_get_all_locked_accounts(
        self, auth_tools, mock_auth_service, admin_user
    ):
        """Test get_locked_accounts all."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_auth_service.db_service.get_locked_accounts = AsyncMock(
            return_value=[
                {"id": "lock-1", "identifier": "user1"},
                {"id": "lock-2", "identifier": "user2"},
            ]
        )

        result = await auth_tools.get_locked_accounts(
            {
                "token": "valid",
                "include_expired": True,
                "include_unlocked": False,
            }
        )

        assert result["success"] is True
        assert result["data"]["count"] == 2

    @pytest.mark.asyncio
    async def test_exception(self, auth_tools, mock_auth_service):
        """Test get_locked_accounts handles exceptions."""
        mock_auth_service._validate_jwt_token.side_effect = Exception("Error")

        result = await auth_tools.get_locked_accounts({"token": "valid"})
        assert result["success"] is False
        assert result["error"] == "GET_ERROR"


class TestUpdateAccountLock:
    """Tests for update_account_lock method."""

    @pytest.fixture
    def mock_auth_service(self):
        """Create mock auth service."""
        return MagicMock()

    @pytest.fixture
    def auth_tools(self, mock_auth_service):
        """Create AuthTools instance."""
        with patch("tools.auth.tools.logger"):
            return AuthTools(mock_auth_service)

    @pytest.fixture
    def admin_user(self):
        """Create admin user mock."""
        user = MagicMock()
        user.is_active = True
        user.username = "admin"
        user.role = MagicMock()
        user.role.value = "admin"
        return user

    @pytest.fixture
    def regular_user(self):
        """Create regular user mock."""
        user = MagicMock()
        user.is_active = True
        user.username = "user"
        user.role = MagicMock()
        user.role.value = "user"
        return user

    @pytest.mark.asyncio
    async def test_missing_token(self, auth_tools):
        """Test update_account_lock without token."""
        result = await auth_tools.update_account_lock({})
        assert result["success"] is False
        assert result["error"] == "MISSING_TOKEN"

    @pytest.mark.asyncio
    async def test_missing_lock_id(self, auth_tools):
        """Test update_account_lock without lock_id."""
        result = await auth_tools.update_account_lock({"token": "valid"})
        assert result["success"] is False
        assert result["error"] == "MISSING_LOCK_ID"

    @pytest.mark.asyncio
    async def test_missing_locked_param(self, auth_tools):
        """Test update_account_lock without locked param."""
        result = await auth_tools.update_account_lock(
            {
                "token": "valid",
                "lock_id": "lock-123",
            }
        )
        assert result["success"] is False
        assert result["error"] == "MISSING_LOCKED_PARAM"

    @pytest.mark.asyncio
    async def test_invalid_token(self, auth_tools, mock_auth_service):
        """Test update_account_lock with invalid token."""
        mock_auth_service._validate_jwt_token.return_value = None

        result = await auth_tools.update_account_lock(
            {
                "token": "invalid",
                "lock_id": "lock-123",
                "locked": False,
            }
        )
        assert result["success"] is False
        assert result["error"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_user_inactive(self, auth_tools, mock_auth_service):
        """Test update_account_lock when user inactive."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = False
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)

        result = await auth_tools.update_account_lock(
            {
                "token": "valid",
                "lock_id": "lock-123",
                "locked": False,
            }
        )
        assert result["success"] is False
        assert result["error"] == "USER_INACTIVE"

    @pytest.mark.asyncio
    async def test_non_admin_user(self, auth_tools, mock_auth_service, regular_user):
        """Test update_account_lock by non-admin."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id = AsyncMock(return_value=regular_user)

        result = await auth_tools.update_account_lock(
            {
                "token": "valid",
                "lock_id": "lock-123",
                "locked": False,
            }
        )
        assert result["success"] is False
        assert result["error"] == "ADMIN_REQUIRED"

    @pytest.mark.asyncio
    async def test_lock_not_found(self, auth_tools, mock_auth_service, admin_user):
        """Test update_account_lock when lock not found."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_auth_service.db_service.get_lock_by_id = AsyncMock(return_value=None)

        result = await auth_tools.update_account_lock(
            {
                "token": "valid",
                "lock_id": "lock-123",
                "locked": False,
            }
        )
        assert result["success"] is False
        assert result["error"] == "LOCK_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_unlock_success(self, auth_tools, mock_auth_service, admin_user):
        """Test successful account unlock."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_auth_service.db_service.get_lock_by_id = AsyncMock(
            return_value={"identifier": "testuser", "identifier_type": "username"}
        )
        mock_auth_service.db_service.unlock_account = AsyncMock(return_value=True)
        mock_auth_service._log_security_event = AsyncMock()

        result = await auth_tools.update_account_lock(
            {
                "token": "valid",
                "lock_id": "lock-123",
                "locked": False,
                "notes": "Unlocked by admin",
            }
        )

        assert result["success"] is True
        assert "unlocked" in result["message"]

    @pytest.mark.asyncio
    async def test_lock_success(self, auth_tools, mock_auth_service, admin_user):
        """Test successful account lock."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_auth_service.db_service.get_lock_by_id = AsyncMock(
            return_value={"identifier": "testuser", "identifier_type": "username"}
        )
        mock_auth_service.db_service.lock_account = AsyncMock(return_value=True)
        mock_auth_service._log_security_event = AsyncMock()

        result = await auth_tools.update_account_lock(
            {
                "token": "valid",
                "lock_id": "lock-123",
                "locked": True,
            }
        )

        assert result["success"] is True
        assert "locked" in result["message"]

    @pytest.mark.asyncio
    async def test_unlock_failed(self, auth_tools, mock_auth_service, admin_user):
        """Test unlock failure."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id = AsyncMock(return_value=admin_user)
        mock_auth_service.db_service.get_lock_by_id = AsyncMock(
            return_value={"identifier": "testuser", "identifier_type": "username"}
        )
        mock_auth_service.db_service.unlock_account = AsyncMock(return_value=False)

        result = await auth_tools.update_account_lock(
            {
                "token": "valid",
                "lock_id": "lock-123",
                "locked": False,
            }
        )

        assert result["success"] is False
        assert "FAILED" in result["error"]

    @pytest.mark.asyncio
    async def test_exception(self, auth_tools, mock_auth_service):
        """Test update_account_lock handles exceptions."""
        mock_auth_service._validate_jwt_token.side_effect = Exception("Error")

        result = await auth_tools.update_account_lock(
            {
                "token": "valid",
                "lock_id": "lock-123",
                "locked": False,
            }
        )
        assert result["success"] is False
        assert result["error"] == "UPDATE_ERROR"

"""
Auth Tools Unit Tests - Additional Methods

Tests for change_password, update_avatar, get_locked_accounts, update_account_lock.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tools.auth.tools import AuthTools


class TestChangePassword:
    """Tests for change_password method."""

    @pytest.fixture
    def mock_auth_service(self):
        """Create mock auth service."""
        service = MagicMock()
        service._password_change_attempts = {}
        return service

    @pytest.fixture
    def auth_tools(self, mock_auth_service):
        """Create AuthTools instance."""
        with patch("tools.auth.tools.logger"):
            tools = AuthTools(mock_auth_service)
            tools._password_tools._password_change_attempts = {}
            return tools

    @pytest.mark.asyncio
    async def test_missing_token(self, auth_tools):
        """Test change_password without token."""
        result = await auth_tools.change_password({})
        assert result["success"] is False
        assert result["error"] == "MISSING_TOKEN"

    @pytest.mark.asyncio
    async def test_missing_current_password(self, auth_tools):
        """Test change_password without current password."""
        result = await auth_tools.change_password({"token": "valid-token"})
        assert result["success"] is False
        assert result["error"] == "MISSING_CURRENT_PASSWORD"

    @pytest.mark.asyncio
    async def test_missing_new_password(self, auth_tools):
        """Test change_password without new password."""
        result = await auth_tools.change_password(
            {
                "token": "valid-token",
                "current_password": "oldpass",
            }
        )
        assert result["success"] is False
        assert result["error"] == "MISSING_NEW_PASSWORD"

    @pytest.mark.asyncio
    async def test_invalid_token(self, auth_tools, mock_auth_service):
        """Test change_password with invalid token."""
        mock_auth_service._validate_jwt_token.return_value = None

        result = await auth_tools.change_password(
            {
                "token": "invalid-token",
                "current_password": "oldpass",
                "new_password": "NewPass123!@#",
            }
        )

        assert result["success"] is False
        assert result["error"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_user_not_found(self, auth_tools, mock_auth_service):
        """Test change_password when user not found."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id = AsyncMock(return_value=None)

        result = await auth_tools.change_password(
            {
                "token": "valid-token",
                "current_password": "oldpass",
                "new_password": "NewPass123!@#",
            }
        )

        assert result["success"] is False
        assert result["error"] == "USER_INACTIVE"

    @pytest.mark.asyncio
    async def test_user_inactive(self, auth_tools, mock_auth_service):
        """Test change_password when user inactive."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = False
        user.username = "testuser"
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)

        result = await auth_tools.change_password(
            {
                "token": "valid-token",
                "current_password": "oldpass",
                "new_password": "NewPass123!@#",
            }
        )

        assert result["success"] is False
        assert result["error"] == "USER_INACTIVE"

    @pytest.mark.asyncio
    async def test_rate_limited(self, auth_tools, mock_auth_service):
        """Test change_password when rate limited."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        user.username = "testuser"
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)
        mock_auth_service._log_security_event = AsyncMock()

        # Set up lockout
        auth_tools._password_tools._password_change_attempts["testuser:unknown"] = {
            "count": 5,
            "lockout_until": datetime.now(UTC) + timedelta(minutes=10),
        }

        result = await auth_tools.change_password(
            {
                "token": "valid-token",
                "current_password": "oldpass",
                "new_password": "NewPass123!@#",
            }
        )

        assert result["success"] is False
        assert result["error"] == "RATE_LIMITED"

    @pytest.mark.asyncio
    async def test_no_stored_hash(self, auth_tools, mock_auth_service):
        """Test change_password when no password hash found."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        user.username = "testuser"
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)
        mock_auth_service.db_service.get_user_password_hash = AsyncMock(
            return_value=None
        )

        result = await auth_tools.change_password(
            {
                "token": "valid-token",
                "current_password": "oldpass",
                "new_password": "NewPass123!@#",
            }
        )

        assert result["success"] is False
        assert result["error"] == "VERIFICATION_ERROR"

    @pytest.mark.asyncio
    async def test_wrong_current_password(self, auth_tools, mock_auth_service):
        """Test change_password with wrong current password."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        user.username = "testuser"
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)
        mock_auth_service.db_service.get_user_password_hash = AsyncMock(
            return_value="$hash$"
        )
        mock_auth_service._log_security_event = AsyncMock()

        with patch("lib.auth_helpers.verify_password", return_value=False):
            result = await auth_tools.change_password(
                {
                    "token": "valid-token",
                    "current_password": "wrongpass",
                    "new_password": "NewPass123!@#",
                }
            )

        assert result["success"] is False
        assert result["error"] == "INVALID_CURRENT_PASSWORD"

    @pytest.mark.asyncio
    async def test_weak_password_too_short(self, auth_tools, mock_auth_service):
        """Test change_password with too short password."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        user.username = "testuser"
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)
        mock_auth_service.db_service.get_user_password_hash = AsyncMock(
            return_value="$hash$"
        )

        with patch("lib.auth_helpers.verify_password", return_value=True):
            result = await auth_tools.change_password(
                {
                    "token": "valid-token",
                    "current_password": "oldpass",
                    "new_password": "Short1!",
                }
            )

        assert result["success"] is False
        assert result["error"] == "WEAK_PASSWORD"
        assert "8 characters" in result["message"]

    @pytest.mark.asyncio
    async def test_weak_password_missing_complexity(
        self, auth_tools, mock_auth_service
    ):
        """Test change_password missing complexity requirements."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        user.username = "testuser"
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)
        mock_auth_service.db_service.get_user_password_hash = AsyncMock(
            return_value="$hash$"
        )

        with patch("lib.auth_helpers.verify_password", return_value=True):
            result = await auth_tools.change_password(
                {
                    "token": "valid-token",
                    "current_password": "oldpass",
                    "new_password": "abcdefghijkl",  # All lowercase, no special chars
                }
            )

        assert result["success"] is False
        assert result["error"] == "WEAK_PASSWORD"

    @pytest.mark.asyncio
    async def test_same_password(self, auth_tools, mock_auth_service):
        """Test change_password with same password."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        user.username = "testuser"
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)
        mock_auth_service.db_service.get_user_password_hash = AsyncMock(
            return_value="$hash$"
        )

        with patch("lib.auth_helpers.verify_password", return_value=True):
            result = await auth_tools.change_password(
                {
                    "token": "valid-token",
                    "current_password": "SamePass123!@#",
                    "new_password": "SamePass123!@#",
                }
            )

        assert result["success"] is False
        assert result["error"] == "SAME_PASSWORD"

    @pytest.mark.asyncio
    async def test_update_failed(self, auth_tools, mock_auth_service):
        """Test change_password when DB update fails."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        user.username = "testuser"
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)
        mock_auth_service.db_service.get_user_password_hash = AsyncMock(
            return_value="$hash$"
        )
        mock_auth_service.db_service.update_user_password = AsyncMock(
            return_value=False
        )

        with patch("lib.auth_helpers.verify_password", return_value=True):
            with patch("lib.auth_helpers.hash_password", return_value="$newhash$"):
                result = await auth_tools.change_password(
                    {
                        "token": "valid-token",
                        "current_password": "OldPass123!@#",
                        "new_password": "NewPass123!@#",
                    }
                )

        assert result["success"] is False
        assert result["error"] == "UPDATE_FAILED"

    @pytest.mark.asyncio
    async def test_success(self, auth_tools, mock_auth_service):
        """Test successful password change."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        user.username = "testuser"
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)
        mock_auth_service.db_service.get_user_password_hash = AsyncMock(
            return_value="$hash$"
        )
        mock_auth_service.db_service.update_user_password = AsyncMock(return_value=True)
        mock_auth_service._log_security_event = AsyncMock()

        with patch("lib.auth_helpers.verify_password", return_value=True):
            with patch("lib.auth_helpers.hash_password", return_value="$newhash$"):
                result = await auth_tools.change_password(
                    {
                        "token": "valid-token",
                        "current_password": "OldPass123!@#",
                        "new_password": "NewPass123!@#",
                    }
                )

        assert result["success"] is True
        assert "successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_with_context_metadata(self, auth_tools, mock_auth_service):
        """Test change_password extracts context metadata."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        user.username = "testuser"
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)
        mock_auth_service.db_service.get_user_password_hash = AsyncMock(
            return_value="$hash$"
        )
        mock_auth_service.db_service.update_user_password = AsyncMock(return_value=True)
        mock_auth_service._log_security_event = AsyncMock()

        ctx = MagicMock()
        ctx.meta = {"clientIp": "10.0.0.1", "userAgent": "TestAgent/1.0"}

        with patch("lib.auth_helpers.verify_password", return_value=True):
            with patch("lib.auth_helpers.hash_password", return_value="$newhash$"):
                result = await auth_tools.change_password(
                    {
                        "token": "valid-token",
                        "current_password": "OldPass123!@#",
                        "new_password": "NewPass123!@#",
                    },
                    ctx=ctx,
                )

        assert result["success"] is True
        call_args = mock_auth_service._log_security_event.call_args
        assert call_args[1]["client_ip"] == "10.0.0.1"
        assert call_args[1]["user_agent"] == "TestAgent/1.0"

    @pytest.mark.asyncio
    async def test_lockout_triggered(self, auth_tools, mock_auth_service):
        """Test change_password triggers lockout after max attempts."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        user.username = "testuser"
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)
        mock_auth_service.db_service.get_user_password_hash = AsyncMock(
            return_value="$hash$"
        )
        mock_auth_service._log_security_event = AsyncMock()

        # Set up with 4 existing attempts (MAX_ATTEMPTS - 1)
        auth_tools._password_tools._password_change_attempts["testuser:unknown"] = {"count": 4}

        with patch("lib.auth_helpers.verify_password", return_value=False):
            result = await auth_tools.change_password(
                {
                    "token": "valid-token",
                    "current_password": "wrongpass",
                    "new_password": "NewPass123!@#",
                }
            )

        assert result["success"] is False
        assert result["error"] == "RATE_LIMITED"
        assert "locked" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_weak_password_missing_lowercase(self, auth_tools, mock_auth_service):
        """Test change_password with password missing lowercase."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        user.username = "testuser"
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)
        mock_auth_service.db_service.get_user_password_hash = AsyncMock(
            return_value="$hash$"
        )

        with patch("lib.auth_helpers.verify_password", return_value=True):
            result = await auth_tools.change_password(
                {
                    "token": "valid-token",
                    "current_password": "oldpass",
                    "new_password": "ABCDEFGH1234!@#",  # All uppercase
                }
            )

        assert result["success"] is False
        assert result["error"] == "WEAK_PASSWORD"
        assert "lowercase" in result["message"]

    @pytest.mark.asyncio
    async def test_clears_rate_limiting_on_success(self, auth_tools, mock_auth_service):
        """Test change_password clears rate limiting on success."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        user.username = "testuser"
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)
        mock_auth_service.db_service.get_user_password_hash = AsyncMock(
            return_value="$hash$"
        )
        mock_auth_service.db_service.update_user_password = AsyncMock(return_value=True)
        mock_auth_service._log_security_event = AsyncMock()

        # Set up existing rate limiting
        auth_tools._password_tools._password_change_attempts["testuser:unknown"] = {"count": 2}

        with patch("lib.auth_helpers.verify_password", return_value=True):
            with patch("lib.auth_helpers.hash_password", return_value="$newhash$"):
                result = await auth_tools.change_password(
                    {
                        "token": "valid-token",
                        "current_password": "OldPass123!@#",
                        "new_password": "NewPass123!@#",
                    }
                )

        assert result["success"] is True
        assert "testuser:unknown" not in auth_tools._password_tools._password_change_attempts

    @pytest.mark.asyncio
    async def test_exception_with_logging_failure(self, auth_tools, mock_auth_service):
        """Test change_password exception when security logging also fails."""
        mock_auth_service._validate_jwt_token.side_effect = Exception("DB error")
        mock_auth_service._log_security_event = AsyncMock(
            side_effect=Exception("Log error")
        )

        result = await auth_tools.change_password(
            {
                "token": "valid-token",
                "current_password": "oldpass",
                "new_password": "NewPass123!@#",
            }
        )

        assert result["success"] is False
        assert result["error"] == "CHANGE_ERROR"

    @pytest.mark.asyncio
    async def test_exception(self, auth_tools, mock_auth_service):
        """Test change_password handles exceptions."""
        mock_auth_service._validate_jwt_token.side_effect = Exception("DB error")
        mock_auth_service._log_security_event = AsyncMock()

        result = await auth_tools.change_password(
            {
                "token": "valid-token",
                "current_password": "oldpass",
                "new_password": "NewPass123!@#",
            }
        )

        assert result["success"] is False
        assert result["error"] == "CHANGE_ERROR"


class TestUpdateAvatar:
    """Tests for update_avatar method."""

    @pytest.fixture
    def mock_auth_service(self):
        """Create mock auth service."""
        return MagicMock()

    @pytest.fixture
    def auth_tools(self, mock_auth_service):
        """Create AuthTools instance."""
        with patch("tools.auth.tools.logger"):
            return AuthTools(mock_auth_service)

    @pytest.mark.asyncio
    async def test_missing_token(self, auth_tools):
        """Test update_avatar without token."""
        result = await auth_tools.update_avatar({})
        assert result["success"] is False
        assert result["error"] == "MISSING_TOKEN"

    @pytest.mark.asyncio
    async def test_invalid_token(self, auth_tools, mock_auth_service):
        """Test update_avatar with invalid token."""
        mock_auth_service._validate_jwt_token.return_value = None

        result = await auth_tools.update_avatar({"token": "invalid"})
        assert result["success"] is False
        assert result["error"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_user_inactive(self, auth_tools, mock_auth_service):
        """Test update_avatar when user inactive."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = False
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)

        result = await auth_tools.update_avatar({"token": "valid"})
        assert result["success"] is False
        assert result["error"] == "USER_INACTIVE"

    @pytest.mark.asyncio
    async def test_invalid_format(self, auth_tools, mock_auth_service):
        """Test update_avatar with invalid format."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)

        result = await auth_tools.update_avatar(
            {
                "token": "valid",
                "avatar": "not-a-data-url",
            }
        )
        assert result["success"] is False
        assert result["error"] == "INVALID_FORMAT"

    @pytest.mark.asyncio
    async def test_invalid_image_type(self, auth_tools, mock_auth_service):
        """Test update_avatar with invalid image type."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)

        result = await auth_tools.update_avatar(
            {
                "token": "valid",
                "avatar": "data:image/bmp;base64,abc",
            }
        )
        assert result["success"] is False
        assert result["error"] == "INVALID_IMAGE_TYPE"

    @pytest.mark.asyncio
    async def test_avatar_too_large(self, auth_tools, mock_auth_service):
        """Test update_avatar with too large image."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)

        large_avatar = "data:image/png;base64," + "a" * (600 * 1024)
        result = await auth_tools.update_avatar(
            {
                "token": "valid",
                "avatar": large_avatar,
            }
        )
        assert result["success"] is False
        assert result["error"] == "AVATAR_TOO_LARGE"

    @pytest.mark.asyncio
    async def test_update_failed(self, auth_tools, mock_auth_service):
        """Test update_avatar when DB update fails."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)
        mock_auth_service.db_service.update_user_avatar = AsyncMock(return_value=False)

        result = await auth_tools.update_avatar(
            {
                "token": "valid",
                "avatar": "data:image/png;base64,abc123",
            }
        )
        assert result["success"] is False
        assert result["error"] == "UPDATE_FAILED"

    @pytest.mark.asyncio
    async def test_success_with_avatar(self, auth_tools, mock_auth_service):
        """Test successful avatar update."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)
        mock_auth_service.db_service.update_user_avatar = AsyncMock(return_value=True)

        result = await auth_tools.update_avatar(
            {
                "token": "valid",
                "avatar": "data:image/png;base64,abc123",
            }
        )
        assert result["success"] is True
        assert "updated" in result["message"]

    @pytest.mark.asyncio
    async def test_success_remove_avatar(self, auth_tools, mock_auth_service):
        """Test successful avatar removal."""
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        user = MagicMock()
        user.is_active = True
        mock_auth_service.get_user_by_id = AsyncMock(return_value=user)
        mock_auth_service.db_service.update_user_avatar = AsyncMock(return_value=True)

        result = await auth_tools.update_avatar(
            {
                "token": "valid",
                "avatar": "",
            }
        )
        assert result["success"] is True
        assert "removed" in result["message"]

    @pytest.mark.asyncio
    async def test_exception(self, auth_tools, mock_auth_service):
        """Test update_avatar handles exceptions."""
        mock_auth_service._validate_jwt_token.side_effect = Exception("Error")

        result = await auth_tools.update_avatar({"token": "valid"})
        assert result["success"] is False
        assert result["error"] == "UPDATE_ERROR"

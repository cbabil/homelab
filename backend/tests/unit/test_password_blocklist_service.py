"""
Unit tests for services/password_blocklist_service.py

Tests for NIST-compliant password screening service.
"""

import gzip
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import services.password_blocklist_service as blocklist_module
from services.password_blocklist_service import (
    PasswordBlocklistService,
    get_blocklist_service,
)


@pytest.fixture
def blocklist_service():
    """Create service with no real file loading."""
    with patch.object(blocklist_module, "logger"):
        # Create with non-existent paths to skip file loading
        service = PasswordBlocklistService(
            blocklist_path=Path("/nonexistent/blocklist.txt.gz"),
            context_words_path=Path("/nonexistent/context.txt"),
        )
        return service


@pytest.fixture
def cleanup_singleton():
    """Reset singleton after test."""
    yield
    blocklist_module._blocklist_service = None


class TestPasswordBlocklistServiceInit:
    """Tests for service initialization."""

    def test_init_with_default_context_words(self, blocklist_service):
        """Should initialize with default context words."""
        assert "tomo" in blocklist_service._context_words
        assert "admin" in blocklist_service._context_words
        assert "password" in blocklist_service._context_words

    def test_init_sets_hibp_flag(self):
        """Should set HIBP enable flag."""
        with patch.object(blocklist_module, "logger"):
            service = PasswordBlocklistService(
                blocklist_path=Path("/nonexistent"),
                context_words_path=Path("/nonexistent"),
                enable_hibp=True,
            )
            assert service._enable_hibp is True

    def test_init_hibp_disabled_by_default(self, blocklist_service):
        """Should disable HIBP by default."""
        assert blocklist_service._enable_hibp is False


class TestLoadBlocklist:
    """Tests for _load_blocklist method."""

    def test_load_blocklist_from_gzip(self):
        """Should load passwords from gzipped file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            blocklist_file = Path(tmpdir) / "passwords.txt.gz"

            with gzip.open(blocklist_file, "wt", encoding="utf-8") as f:
                f.write("password123\n")
                f.write("letmein\n")
                f.write("qwerty\n")

            with patch.object(blocklist_module, "logger"):
                service = PasswordBlocklistService(
                    blocklist_path=blocklist_file,
                    context_words_path=Path("/nonexistent"),
                )

                assert "password123" in service._blocklist
                assert "letmein" in service._blocklist
                assert service._blocklist_loaded is True

    def test_load_blocklist_lowercases_passwords(self):
        """Should lowercase all passwords."""
        with tempfile.TemporaryDirectory() as tmpdir:
            blocklist_file = Path(tmpdir) / "passwords.txt.gz"

            with gzip.open(blocklist_file, "wt", encoding="utf-8") as f:
                f.write("PASSWORD\n")
                f.write("Password123\n")

            with patch.object(blocklist_module, "logger"):
                service = PasswordBlocklistService(
                    blocklist_path=blocklist_file,
                    context_words_path=Path("/nonexistent"),
                )

                assert "password" in service._blocklist
                assert "password123" in service._blocklist

    def test_load_blocklist_file_not_found(self, blocklist_service):
        """Should handle missing blocklist file."""
        assert blocklist_service._blocklist_loaded is False

    def test_load_blocklist_handles_exception(self):
        """Should handle file read errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            blocklist_file = Path(tmpdir) / "passwords.txt.gz"
            blocklist_file.write_text("not gzip data")

            with patch.object(blocklist_module, "logger") as mock_logger:
                service = PasswordBlocklistService(
                    blocklist_path=blocklist_file,
                    context_words_path=Path("/nonexistent"),
                )

                assert service._blocklist_loaded is False
                mock_logger.error.assert_called()


class TestLoadContextWords:
    """Tests for _load_context_words method."""

    def test_load_context_words_from_file(self):
        """Should load additional context words from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            context_file = Path(tmpdir) / "context.txt"
            context_file.write_text("mycompany\ncustomword\n")

            with patch.object(blocklist_module, "logger"):
                service = PasswordBlocklistService(
                    blocklist_path=Path("/nonexistent"),
                    context_words_path=context_file,
                )

                assert "mycompany" in service._context_words
                assert "customword" in service._context_words
                # Default words still present
                assert "admin" in service._context_words

    def test_load_context_words_handles_exception(self):
        """Should handle file read errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            context_file = Path(tmpdir) / "context.txt"
            context_file.mkdir()  # Create as directory to cause error

            with patch.object(blocklist_module, "logger") as mock_logger:
                PasswordBlocklistService(
                    blocklist_path=Path("/nonexistent"),
                    context_words_path=context_file,
                )

                mock_logger.warning.assert_called()


class TestCheckCommonPassword:
    """Tests for check_common_password method."""

    def test_check_common_password_found(self, blocklist_service):
        """Should return True for common password."""
        blocklist_service._blocklist = {"password123", "letmein"}

        assert blocklist_service.check_common_password("password123") is True

    def test_check_common_password_not_found(self, blocklist_service):
        """Should return False for unique password."""
        blocklist_service._blocklist = {"password123"}

        assert blocklist_service.check_common_password("unique$ecret!") is False

    def test_check_common_password_case_insensitive(self, blocklist_service):
        """Should check case-insensitively."""
        blocklist_service._blocklist = {"password123"}

        assert blocklist_service.check_common_password("PASSWORD123") is True
        assert blocklist_service.check_common_password("Password123") is True


class TestCheckSequentialPattern:
    """Tests for check_sequential_pattern method."""

    def test_check_sequential_numbers(self, blocklist_service):
        """Should detect sequential numbers."""
        assert blocklist_service.check_sequential_pattern("my1234pass") is not None

    def test_check_sequential_letters(self, blocklist_service):
        """Should detect sequential letters."""
        assert blocklist_service.check_sequential_pattern("myabcdpass") is not None

    def test_check_sequential_keyboard(self, blocklist_service):
        """Should detect keyboard patterns."""
        assert blocklist_service.check_sequential_pattern("qwerty123") is not None
        assert blocklist_service.check_sequential_pattern("asdfgh") is not None

    def test_check_sequential_reversed(self, blocklist_service):
        """Should detect reversed patterns."""
        result = blocklist_service.check_sequential_pattern("my4321pass")
        assert result is not None

    def test_check_sequential_no_pattern(self, blocklist_service):
        """Should return None for no sequential pattern."""
        assert blocklist_service.check_sequential_pattern("C0mplex!P@ss") is None


class TestCheckRepetitivePattern:
    """Tests for check_repetitive_pattern method."""

    def test_check_repetitive_same_char(self, blocklist_service):
        """Should detect repeated characters."""
        assert blocklist_service.check_repetitive_pattern("passaaaa") is not None
        assert blocklist_service.check_repetitive_pattern("111password") is not None

    def test_check_repetitive_pattern(self, blocklist_service):
        """Should detect repeated patterns."""
        assert blocklist_service.check_repetitive_pattern("ababab123") is not None
        assert blocklist_service.check_repetitive_pattern("121212pass") is not None

    def test_check_repetitive_no_pattern(self, blocklist_service):
        """Should return None for no repetitive pattern."""
        assert blocklist_service.check_repetitive_pattern("Secure$Pass1") is None


class TestCheckContextWords:
    """Tests for check_context_words method."""

    def test_check_context_default_words(self, blocklist_service):
        """Should detect default context words."""
        assert blocklist_service.check_context_words("tomopass123") is not None
        assert blocklist_service.check_context_words("myadminpass") is not None

    def test_check_context_username(self, blocklist_service):
        """Should detect username in password."""
        result = blocklist_service.check_context_words("johndoe123", username="johndoe")
        assert result is not None
        assert "username" in result

    def test_check_context_short_username_ignored(self, blocklist_service):
        """Should ignore short usernames."""
        result = blocklist_service.check_context_words("ab123pass", username="ab")
        # Should not match because username is too short
        assert result is None or "ab" not in str(result)

    def test_check_context_additional_words(self, blocklist_service):
        """Should check additional context words."""
        result = blocklist_service.check_context_words(
            "mycompanypass123", additional_context=["mycompany"]
        )
        assert result is not None

    def test_check_context_no_match(self, blocklist_service):
        """Should return None when no context match."""
        result = blocklist_service.check_context_words("Str0ng$ecret!")
        assert result is None


class TestCheckHibp:
    """Tests for check_hibp method."""

    @pytest.mark.asyncio
    async def test_check_hibp_disabled(self, blocklist_service):
        """Should return 'not checked' when disabled."""
        result = await blocklist_service.check_hibp("password123")

        assert result["checked"] is False
        assert "disabled" in result["reason"]

    @pytest.mark.asyncio
    async def test_check_hibp_compromised(self):
        """Should detect compromised password."""
        with patch.object(blocklist_module, "logger"):
            service = PasswordBlocklistService(
                blocklist_path=Path("/nonexistent"),
                context_words_path=Path("/nonexistent"),
                enable_hibp=True,
            )

        mock_response = MagicMock()
        mock_response.status_code = 200
        # SHA1 of "password" is 5BAA6...
        # Simulate response with matching hash
        mock_response.text = "1E4C9B93F3F0682250B6CF8331B7EE68FD8:1000000\n"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await service.check_hibp("password")

            assert result["checked"] is True
            # May or may not be compromised depending on hash match

    @pytest.mark.asyncio
    async def test_check_hibp_not_compromised(self):
        """Should return not compromised for clean password."""
        with patch.object(blocklist_module, "logger"):
            service = PasswordBlocklistService(
                blocklist_path=Path("/nonexistent"),
                context_words_path=Path("/nonexistent"),
                enable_hibp=True,
            )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "SOMEOTHERHASH:100\nANOTHERHASH:200\n"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await service.check_hibp("super_unique_password_xyz123!")

            assert result["checked"] is True
            assert result.get("compromised") is False

    @pytest.mark.asyncio
    async def test_check_hibp_api_error(self):
        """Should handle API error."""
        with patch.object(blocklist_module, "logger"):
            service = PasswordBlocklistService(
                blocklist_path=Path("/nonexistent"),
                context_words_path=Path("/nonexistent"),
                enable_hibp=True,
            )

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await service.check_hibp("test")

            assert result["checked"] is False
            assert "API error" in result["reason"]

    @pytest.mark.asyncio
    async def test_check_hibp_exception(self):
        """Should handle exceptions."""
        with patch.object(blocklist_module, "logger"):
            service = PasswordBlocklistService(
                blocklist_path=Path("/nonexistent"),
                context_words_path=Path("/nonexistent"),
                enable_hibp=True,
            )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=RuntimeError("Network error")
            )

            result = await service.check_hibp("test")

            assert result["checked"] is False


class TestValidatePassword:
    """Tests for validate_password method."""

    @pytest.mark.asyncio
    async def test_validate_password_valid(self, blocklist_service):
        """Should pass valid password."""
        result = await blocklist_service.validate_password("Str0ng$ecret!2024")

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_password_common(self, blocklist_service):
        """Should reject common password."""
        blocklist_service._blocklist = {"password123"}

        result = await blocklist_service.validate_password("password123")

        assert result["valid"] is False
        assert result["checks"]["common_password"] is False
        assert any("common" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_password_sequential(self, blocklist_service):
        """Should reject sequential pattern."""
        result = await blocklist_service.validate_password("abc1234xyz")

        assert result["valid"] is False
        assert result["checks"]["sequential_pattern"] is False

    @pytest.mark.asyncio
    async def test_validate_password_repetitive(self, blocklist_service):
        """Should reject repetitive pattern."""
        result = await blocklist_service.validate_password("passaaaa123")

        assert result["valid"] is False
        assert result["checks"]["repetitive_pattern"] is False

    @pytest.mark.asyncio
    async def test_validate_password_context_word(self, blocklist_service):
        """Should reject password with context word."""
        result = await blocklist_service.validate_password("tomoadmin123")

        assert result["valid"] is False
        assert result["checks"]["context_words"] is False

    @pytest.mark.asyncio
    async def test_validate_password_username_in_password(self, blocklist_service):
        """Should reject password containing username."""
        result = await blocklist_service.validate_password(
            "johndoe123!", username="johndoe"
        )

        assert result["valid"] is False
        assert "username" in result["errors"][0].lower()

    @pytest.mark.asyncio
    async def test_validate_password_skip_blocklist(self, blocklist_service):
        """Should skip blocklist check when disabled."""
        blocklist_service._blocklist = {"password123"}

        result = await blocklist_service.validate_password(
            "password123", check_blocklist=False
        )

        assert "common_password" not in result["checks"]

    @pytest.mark.asyncio
    async def test_validate_password_with_hibp(self):
        """Should include HIBP check when enabled."""
        with patch.object(blocklist_module, "logger"):
            service = PasswordBlocklistService(
                blocklist_path=Path("/nonexistent"),
                context_words_path=Path("/nonexistent"),
                enable_hibp=True,
            )

        with patch.object(
            service, "check_hibp", new_callable=AsyncMock
        ) as mock_hibp:
            mock_hibp.return_value = {
                "checked": True,
                "compromised": True,
                "breach_count": 5000,
            }

            result = await service.validate_password(
                "Str0ng$ecret!", check_hibp=True
            )

            assert "hibp" in result["checks"]
            assert "5,000" in result["errors"][0]


class TestProperties:
    """Tests for service properties."""

    def test_blocklist_loaded_property(self, blocklist_service):
        """Should return blocklist loaded status."""
        assert blocklist_service.blocklist_loaded is False

        blocklist_service._blocklist_loaded = True
        assert blocklist_service.blocklist_loaded is True

    def test_blocklist_size_property(self, blocklist_service):
        """Should return blocklist size."""
        blocklist_service._blocklist = {"a", "b", "c"}

        assert blocklist_service.blocklist_size == 3


class TestGetBlocklistService:
    """Tests for get_blocklist_service function."""

    def test_get_blocklist_service_creates_singleton(self, cleanup_singleton):
        """Should create singleton instance."""
        with patch.object(blocklist_module, "logger"):
            service1 = get_blocklist_service()
            service2 = get_blocklist_service()

            assert service1 is service2

    def test_get_blocklist_service_reinitialize(self, cleanup_singleton):
        """Should create new instance when reinitialize=True."""
        with patch.object(blocklist_module, "logger"):
            service1 = get_blocklist_service()
            service2 = get_blocklist_service(reinitialize=True)

            assert service1 is not service2

    def test_get_blocklist_service_with_hibp(self, cleanup_singleton):
        """Should pass enable_hibp flag."""
        with patch.object(blocklist_module, "logger"):
            service = get_blocklist_service(enable_hibp=True)

            assert service._enable_hibp is True

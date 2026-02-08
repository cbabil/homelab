"""
Unit tests for services/password_blocklist_service.py

Tests NIST SP 800-63B-4 compliant password screening service.
"""

import gzip
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import services.password_blocklist_service as blocklist_module
from services.password_blocklist_service import (
    DEFAULT_CONTEXT_WORDS,
    SEQUENTIAL_PATTERNS,
    PasswordBlocklistService,
    get_blocklist_service,
)


@pytest.fixture
def mock_blocklist_path(tmp_path):
    """Create a temporary gzipped blocklist file."""
    blocklist_file = tmp_path / "passwords.txt.gz"
    with gzip.open(blocklist_file, "wt", encoding="utf-8") as f:
        f.write("password123\n")
        f.write("qwerty\n")
        f.write("letmein\n")
    return blocklist_file


@pytest.fixture
def mock_context_path(tmp_path):
    """Create a temporary context words file."""
    context_file = tmp_path / "context.txt"
    context_file.write_text("testword\ncustomcontext\n")
    return context_file


@pytest.fixture
def blocklist_service(mock_blocklist_path, mock_context_path):
    """Create PasswordBlocklistService with test files."""
    with patch("services.password_blocklist_service.logger"):
        return PasswordBlocklistService(
            blocklist_path=mock_blocklist_path,
            context_words_path=mock_context_path,
            enable_hibp=False,
        )


class TestPasswordBlocklistServiceInit:
    """Tests for PasswordBlocklistService initialization."""

    def test_init_creates_empty_blocklist(self):
        """Init should start with empty blocklist when file not found."""
        with patch("services.password_blocklist_service.logger"):
            service = PasswordBlocklistService(
                blocklist_path=Path("/nonexistent/path.txt.gz")
            )
            assert service._blocklist == set()

    def test_init_loads_blocklist(self, mock_blocklist_path):
        """Init should load blocklist from file."""
        with patch("services.password_blocklist_service.logger"):
            service = PasswordBlocklistService(blocklist_path=mock_blocklist_path)
            assert "password123" in service._blocklist
            assert "qwerty" in service._blocklist

    def test_init_loads_context_words(self, mock_context_path):
        """Init should load context words from file."""
        with patch("services.password_blocklist_service.logger"):
            service = PasswordBlocklistService(context_words_path=mock_context_path)
            assert "testword" in service._context_words
            assert "customcontext" in service._context_words

    def test_init_includes_default_context_words(self, mock_context_path):
        """Init should include default context words."""
        with patch("services.password_blocklist_service.logger"):
            service = PasswordBlocklistService(context_words_path=mock_context_path)
            for word in DEFAULT_CONTEXT_WORDS:
                assert word in service._context_words

    def test_init_hibp_disabled_by_default(self):
        """Init should have HIBP disabled by default."""
        with patch("services.password_blocklist_service.logger"):
            service = PasswordBlocklistService(blocklist_path=Path("/nonexistent"))
            assert service._enable_hibp is False

    def test_init_hibp_enabled(self):
        """Init should enable HIBP when specified."""
        with patch("services.password_blocklist_service.logger"):
            service = PasswordBlocklistService(
                blocklist_path=Path("/nonexistent"), enable_hibp=True
            )
            assert service._enable_hibp is True


class TestLoadBlocklist:
    """Tests for _load_blocklist method."""

    def test_load_blocklist_success(self, mock_blocklist_path):
        """_load_blocklist should load passwords from gzipped file."""
        with patch("services.password_blocklist_service.logger"):
            service = PasswordBlocklistService(blocklist_path=mock_blocklist_path)
            assert service._blocklist_loaded is True
            assert len(service._blocklist) == 3

    def test_load_blocklist_lowercases_passwords(self, tmp_path):
        """_load_blocklist should lowercase all passwords."""
        blocklist_file = tmp_path / "passwords.txt.gz"
        with gzip.open(blocklist_file, "wt", encoding="utf-8") as f:
            f.write("PASSWORD\nQWERTY\n")

        with patch("services.password_blocklist_service.logger"):
            service = PasswordBlocklistService(blocklist_path=blocklist_file)
            assert "password" in service._blocklist
            assert "qwerty" in service._blocklist

    def test_load_blocklist_file_not_found(self):
        """_load_blocklist should handle missing file."""
        with patch("services.password_blocklist_service.logger") as mock_logger:
            service = PasswordBlocklistService(
                blocklist_path=Path("/nonexistent/file.txt.gz")
            )
            assert service._blocklist_loaded is False
            mock_logger.warning.assert_called()

    def test_load_blocklist_error(self, tmp_path):
        """_load_blocklist should handle read errors."""
        bad_file = tmp_path / "bad.txt.gz"
        bad_file.write_bytes(b"not valid gzip")

        with patch("services.password_blocklist_service.logger") as mock_logger:
            PasswordBlocklistService(blocklist_path=bad_file)
            mock_logger.error.assert_called()


class TestLoadContextWords:
    """Tests for _load_context_words method."""

    def test_load_context_words_success(self, mock_context_path):
        """_load_context_words should load words from file."""
        with patch("services.password_blocklist_service.logger"):
            service = PasswordBlocklistService(context_words_path=mock_context_path)
            assert "testword" in service._context_words

    def test_load_context_words_file_not_found(self):
        """_load_context_words should handle missing file gracefully."""
        with patch("services.password_blocklist_service.logger"):
            service = PasswordBlocklistService(
                blocklist_path=Path("/nonexistent"),
                context_words_path=Path("/nonexistent/context.txt"),
            )
            # Should still have default context words
            assert len(service._context_words) > 0

    def test_load_context_words_error(self, tmp_path):
        """_load_context_words should handle read errors gracefully."""
        # Create an invalid context words file
        bad_context_file = tmp_path / "context.txt"
        bad_context_file.write_bytes(b"\xff\xfe")  # Invalid UTF-8

        with patch("services.password_blocklist_service.logger") as mock_logger:
            service = PasswordBlocklistService(
                blocklist_path=Path("/nonexistent"), context_words_path=bad_context_file
            )
            # Should log warning
            mock_logger.warning.assert_called()
            # Should still have default context words
            assert len(service._context_words) > 0


class TestCheckCommonPassword:
    """Tests for check_common_password method."""

    def test_check_common_password_found(self, blocklist_service):
        """check_common_password should return True for common passwords."""
        assert blocklist_service.check_common_password("password123") is True
        assert blocklist_service.check_common_password("qwerty") is True

    def test_check_common_password_case_insensitive(self, blocklist_service):
        """check_common_password should be case insensitive."""
        assert blocklist_service.check_common_password("PASSWORD123") is True
        assert blocklist_service.check_common_password("QWERTY") is True

    def test_check_common_password_not_found(self, blocklist_service):
        """check_common_password should return False for unique passwords."""
        assert blocklist_service.check_common_password("xK9#mL2$pQ7") is False


class TestCheckSequentialPattern:
    """Tests for check_sequential_pattern method."""

    def test_check_sequential_numeric(self, blocklist_service):
        """check_sequential_pattern should detect numeric sequences."""
        assert blocklist_service.check_sequential_pattern("pass1234word") == "1234"
        assert blocklist_service.check_sequential_pattern("6789test") == "6789"

    def test_check_sequential_alpha(self, blocklist_service):
        """check_sequential_pattern should detect alphabetic sequences."""
        assert blocklist_service.check_sequential_pattern("testabcd123") == "abcd"

    def test_check_sequential_keyboard(self, blocklist_service):
        """check_sequential_pattern should detect keyboard sequences."""
        assert blocklist_service.check_sequential_pattern("myqwertypass") == "qwer"
        assert blocklist_service.check_sequential_pattern("asdfghjk") == "asdf"

    def test_check_sequential_reverse(self, blocklist_service):
        """check_sequential_pattern should detect reverse sequences."""
        assert blocklist_service.check_sequential_pattern("pass4321word") == "4321"
        assert blocklist_service.check_sequential_pattern("testdcba") == "dcba"

    def test_check_sequential_none(self, blocklist_service):
        """check_sequential_pattern should return None for no patterns."""
        assert blocklist_service.check_sequential_pattern("xK9#mL2$") is None


class TestCheckRepetitivePattern:
    """Tests for check_repetitive_pattern method."""

    def test_check_repetitive_single_char(self, blocklist_service):
        """check_repetitive_pattern should detect repeated single chars."""
        assert blocklist_service.check_repetitive_pattern("passaaaa") == "aaaa"
        assert blocklist_service.check_repetitive_pattern("111pass") == "111"

    def test_check_repetitive_multi_char(self, blocklist_service):
        """check_repetitive_pattern should detect repeated patterns."""
        assert blocklist_service.check_repetitive_pattern("abababab") is not None
        assert blocklist_service.check_repetitive_pattern("121212") is not None

    def test_check_repetitive_none(self, blocklist_service):
        """check_repetitive_pattern should return None for no patterns."""
        assert blocklist_service.check_repetitive_pattern("xK9#mL2$") is None


class TestCheckContextWords:
    """Tests for check_context_words method."""

    def test_check_context_default_words(self, blocklist_service):
        """check_context_words should detect default context words."""
        assert blocklist_service.check_context_words("myadminpass") == "admin"
        assert blocklist_service.check_context_words("servertest") == "server"

    def test_check_context_custom_words(self, blocklist_service):
        """check_context_words should detect custom loaded words."""
        assert blocklist_service.check_context_words("mytestwordpass") == "testword"

    def test_check_context_username(self, blocklist_service):
        """check_context_words should detect username in password."""
        result = blocklist_service.check_context_words("johndoe123", username="johndoe")
        assert result == "username:johndoe"

    def test_check_context_username_short(self, blocklist_service):
        """check_context_words should ignore short usernames."""
        result = blocklist_service.check_context_words("abpass", username="ab")
        assert result is None or not result.startswith("username:")

    def test_check_context_additional(self, blocklist_service):
        """check_context_words should detect additional context words."""
        result = blocklist_service.check_context_words(
            "mycompanypass", additional_context=["company", "project"]
        )
        assert result == "company"

    def test_check_context_none(self, blocklist_service):
        """check_context_words should return None when no context found."""
        result = blocklist_service.check_context_words("xK9#mL2$pQ7")
        assert result is None


class TestCheckHibp:
    """Tests for check_hibp method."""

    @pytest.mark.asyncio
    async def test_check_hibp_disabled(self, blocklist_service):
        """check_hibp should return not checked when disabled."""
        result = await blocklist_service.check_hibp("password")
        assert result["checked"] is False
        assert "disabled" in result["reason"]

    @pytest.mark.asyncio
    async def test_check_hibp_compromised(self, mock_blocklist_path):
        """check_hibp should detect compromised passwords."""
        with patch("services.password_blocklist_service.logger"):
            service = PasswordBlocklistService(
                blocklist_path=mock_blocklist_path, enable_hibp=True
            )

        # Mock the HIBP API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        # SHA1 of "password" = 5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8
        # Prefix: 5BAA6, Suffix: 1E4C9B93F3F0682250B6CF8331B7EE68FD8
        mock_response.text = "1E4C9B93F3F0682250B6CF8331B7EE68FD8:12345\nOTHERHASH:100"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await service.check_hibp("password")

            assert result["checked"] is True
            assert result["compromised"] is True
            assert result["breach_count"] == 12345

    @pytest.mark.asyncio
    async def test_check_hibp_not_compromised(self, mock_blocklist_path):
        """check_hibp should return not compromised for safe passwords."""
        with patch("services.password_blocklist_service.logger"):
            service = PasswordBlocklistService(
                blocklist_path=mock_blocklist_path, enable_hibp=True
            )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA:100"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await service.check_hibp("uniquepassword123!")

            assert result["checked"] is True
            assert result["compromised"] is False

    @pytest.mark.asyncio
    async def test_check_hibp_api_error(self, mock_blocklist_path):
        """check_hibp should handle API errors."""
        with patch("services.password_blocklist_service.logger"):
            service = PasswordBlocklistService(
                blocklist_path=mock_blocklist_path, enable_hibp=True
            )

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await service.check_hibp("password")

            assert result["checked"] is False
            assert "API error" in result["reason"]

    @pytest.mark.asyncio
    async def test_check_hibp_exception(self, mock_blocklist_path):
        """check_hibp should handle exceptions."""
        with patch("services.password_blocklist_service.logger"):
            service = PasswordBlocklistService(
                blocklist_path=mock_blocklist_path, enable_hibp=True
            )

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Network error"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await service.check_hibp("password")

            assert result["checked"] is False


class TestValidatePassword:
    """Tests for validate_password method."""

    @pytest.mark.asyncio
    async def test_validate_password_valid(self, blocklist_service):
        """validate_password should pass for strong passwords."""
        result = await blocklist_service.validate_password("xK9#mL2$pQ7@nR5")
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_password_common(self, blocklist_service):
        """validate_password should fail for common passwords."""
        result = await blocklist_service.validate_password("password123")
        assert result["valid"] is False
        assert "common" in result["errors"][0].lower()

    @pytest.mark.asyncio
    async def test_validate_password_sequential(self, blocklist_service):
        """validate_password should fail for sequential patterns."""
        result = await blocklist_service.validate_password("test1234pass")
        assert result["valid"] is False
        assert any("sequential" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_password_repetitive(self, blocklist_service):
        """validate_password should fail for repetitive patterns."""
        result = await blocklist_service.validate_password("aaaa5678")
        assert result["valid"] is False
        assert any("repetitive" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_password_context(self, blocklist_service):
        """validate_password should fail for context words."""
        result = await blocklist_service.validate_password("myadminpass")
        assert result["valid"] is False
        assert any("guessed" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_password_username(self, blocklist_service):
        """validate_password should fail when containing username."""
        result = await blocklist_service.validate_password(
            "johndoe123!", username="johndoe"
        )
        assert result["valid"] is False
        assert any("username" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_password_skip_blocklist(self, blocklist_service):
        """validate_password should skip blocklist when disabled."""
        result = await blocklist_service.validate_password(
            "password123", check_blocklist=False
        )
        # Should still check other patterns, but not blocklist
        assert "common_password" not in result["checks"]

    @pytest.mark.asyncio
    async def test_validate_password_checks_structure(self, blocklist_service):
        """validate_password should return proper structure."""
        result = await blocklist_service.validate_password("test")
        assert "valid" in result
        assert "errors" in result
        assert "warnings" in result
        assert "checks" in result

    @pytest.mark.asyncio
    async def test_validate_password_hibp_enabled_compromised(
        self, mock_blocklist_path
    ):
        """validate_password should fail for HIBP compromised passwords."""
        with patch("services.password_blocklist_service.logger"):
            service = PasswordBlocklistService(
                blocklist_path=mock_blocklist_path, enable_hibp=True
            )

        # Mock the check_hibp method to return compromised
        with patch.object(
            service,
            "check_hibp",
            new_callable=AsyncMock,
            return_value={"checked": True, "compromised": True, "breach_count": 50000},
        ):
            result = await service.validate_password(
                "uniqueStrongP@ss!", check_hibp=True
            )

            # HIBP check should be present
            assert "hibp" in result["checks"]
            assert result["checks"]["hibp"]["compromised"] is True
            # Should have error about breaches
            assert result["valid"] is False
            assert any("50,000" in e for e in result["errors"])


class TestProperties:
    """Tests for service properties."""

    def test_blocklist_loaded_true(self, blocklist_service):
        """blocklist_loaded should return True when loaded."""
        assert blocklist_service.blocklist_loaded is True

    def test_blocklist_loaded_false(self):
        """blocklist_loaded should return False when not loaded."""
        with patch("services.password_blocklist_service.logger"):
            service = PasswordBlocklistService(blocklist_path=Path("/nonexistent"))
            assert service.blocklist_loaded is False

    def test_blocklist_size(self, blocklist_service):
        """blocklist_size should return number of passwords."""
        assert blocklist_service.blocklist_size == 3


class TestGetBlocklistService:
    """Tests for get_blocklist_service function."""

    def test_get_blocklist_service_creates_singleton(self):
        """get_blocklist_service should create singleton."""
        # Reset global
        blocklist_module._blocklist_service = None

        with patch("services.password_blocklist_service.logger"):
            service1 = get_blocklist_service(reinitialize=True)
            service2 = get_blocklist_service()
            assert service1 is service2

    def test_get_blocklist_service_reinitialize(self):
        """get_blocklist_service should reinitialize when requested."""
        blocklist_module._blocklist_service = None

        with patch("services.password_blocklist_service.logger"):
            service1 = get_blocklist_service(reinitialize=True)
            service2 = get_blocklist_service(reinitialize=True)
            assert service1 is not service2


class TestConstants:
    """Tests for module constants."""

    def test_sequential_patterns_contains_numeric(self):
        """SEQUENTIAL_PATTERNS should contain numeric sequences."""
        assert "1234" in SEQUENTIAL_PATTERNS
        assert "0123" in SEQUENTIAL_PATTERNS

    def test_sequential_patterns_contains_alpha(self):
        """SEQUENTIAL_PATTERNS should contain alphabetic sequences."""
        assert "abcd" in SEQUENTIAL_PATTERNS

    def test_sequential_patterns_contains_keyboard(self):
        """SEQUENTIAL_PATTERNS should contain keyboard sequences."""
        assert "qwer" in SEQUENTIAL_PATTERNS
        assert "asdf" in SEQUENTIAL_PATTERNS

    def test_default_context_words_contains_common(self):
        """DEFAULT_CONTEXT_WORDS should contain common words."""
        assert "admin" in DEFAULT_CONTEXT_WORDS
        assert "password" in DEFAULT_CONTEXT_WORDS
        assert "tomo" in DEFAULT_CONTEXT_WORDS

"""
Unit tests for Password Blocklist Service

Tests for modern password validation including blocklist checking,
pattern detection, and compliance mode validation.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.services.password_blocklist_service import (
    PasswordBlocklistService,
    get_blocklist_service,
    SEQUENTIAL_PATTERNS,
    DEFAULT_CONTEXT_WORDS
)


class TestPasswordBlocklistService:
    """Tests for PasswordBlocklistService class."""

    @pytest.fixture
    def service(self):
        """Create a blocklist service with test data."""
        return PasswordBlocklistService(enable_hibp=False)

    def test_check_sequential_pattern_detects_numeric(self, service):
        """Test detection of numeric sequential patterns."""
        assert service.check_sequential_pattern("password1234") == "1234"
        assert service.check_sequential_pattern("test5678end") == "5678"

    def test_check_sequential_pattern_detects_alphabetic(self, service):
        """Test detection of alphabetic sequential patterns."""
        assert service.check_sequential_pattern("testabcdend") == "abcd"
        assert service.check_sequential_pattern("myqwertypass") == "qwer"

    def test_check_sequential_pattern_detects_reverse(self, service):
        """Test detection of reverse sequential patterns."""
        assert service.check_sequential_pattern("test4321end") == "4321"
        assert service.check_sequential_pattern("mydcbapass") == "dcba"

    def test_check_sequential_pattern_returns_none_for_safe(self, service):
        """Test no detection for passwords without sequential patterns."""
        assert service.check_sequential_pattern("MySecurePassword123!") is None
        assert service.check_sequential_pattern("xK9#mP2@nL5$") is None

    def test_check_repetitive_pattern_detects_repeated_chars(self, service):
        """Test detection of repeated characters."""
        assert service.check_repetitive_pattern("passaaaa123") is not None
        assert service.check_repetitive_pattern("111password") is not None

    def test_check_repetitive_pattern_detects_repeated_sequences(self, service):
        """Test detection of repeated sequences."""
        assert service.check_repetitive_pattern("passabab123") is not None
        assert service.check_repetitive_pattern("1212password") is not None

    def test_check_repetitive_pattern_returns_none_for_safe(self, service):
        """Test no detection for passwords without repetitive patterns."""
        assert service.check_repetitive_pattern("MySecurePass123!") is None
        assert service.check_repetitive_pattern("xK9mP2nL5q") is None

    def test_check_context_words_detects_admin(self, service):
        """Test detection of admin-related words."""
        # Use passwords that only contain one context word to avoid set order issues
        assert service.check_context_words("myadminsecure") == "admin"
        assert service.check_context_words("rootaccess123") == "root"

    def test_check_context_words_detects_tomo_terms(self, service):
        """Test detection of tomo-specific words."""
        # Set iteration order is not guaranteed, so check that some word is detected
        result = service.check_context_words("tomosecure")
        assert result in ("tomo", "home", "lab")
        assert service.check_context_words("mydockerpass") == "docker"

    def test_check_context_words_detects_username(self, service):
        """Test detection of username in password."""
        result = service.check_context_words("johndoe123secure", username="johndoe")
        assert result == "username:johndoe"

    def test_check_context_words_returns_none_for_safe(self, service):
        """Test no detection for passwords without context words."""
        result = service.check_context_words(
            "MyUniqueSecurePhrase42!",
            username="alice"
        )
        assert result is None


class TestValidatePassword:
    """Tests for comprehensive password validation."""

    @pytest.fixture
    def service(self):
        """Create a blocklist service with test data."""
        return PasswordBlocklistService(enable_hibp=False)

    @pytest.mark.asyncio
    async def test_validate_rejects_sequential_patterns(self, service):
        """Test rejection of passwords with sequential patterns."""
        result = await service.validate_password("secure1234password")
        assert not result["valid"]
        assert any("sequential" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_rejects_repetitive_patterns(self, service):
        """Test rejection of passwords with repetitive patterns."""
        result = await service.validate_password("secureaaaa123pass")
        assert not result["valid"]
        assert any("repetitive" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_rejects_context_words(self, service):
        """Test rejection of passwords with context words."""
        # Use password with only one context word to avoid set order issues
        result = await service.validate_password(
            "myadminsecure123",
            username="testuser"
        )
        assert not result["valid"]
        assert any("admin" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_rejects_username_in_password(self, service):
        """Test rejection of passwords containing username."""
        result = await service.validate_password(
            "johndoe123secure!",
            username="johndoe"
        )
        assert not result["valid"]
        assert any("username" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_accepts_strong_password(self, service):
        """Test acceptance of a strong, unique password."""
        result = await service.validate_password(
            "xK9#mP2@nL5$qR7*",
            username="testuser"
        )
        assert result["valid"]
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_checks_dict_contains_all_keys(self, service):
        """Test that validation result contains expected keys."""
        result = await service.validate_password("testpassword123")
        assert "valid" in result
        assert "errors" in result
        assert "warnings" in result
        assert "checks" in result


class TestLengthPolicyPasswordValidation:
    """Tests for modern (SP 800-63B-4) password validation."""

    @pytest.mark.asyncio
    async def test_modern_validation_accepts_long_simple_password(self):
        """Modern mode should accept long passwords without complexity."""
        from src.lib.security import validate_password_length_policy

        # Long passphrase without special chars - valid in length policy mode
        # Uses unique words to avoid repetitive pattern detection
        result = await validate_password_length_policy(
            password="purple elephant dancing gracefully",
            length_policy_mode=True,
            min_length=15
        )
        assert result["valid"]
        assert result["mode"] == "length_policy"

    @pytest.mark.asyncio
    async def test_modern_validation_rejects_short_password(self):
        """Modern mode should reject passwords shorter than minimum."""
        from src.lib.security import validate_password_length_policy

        result = await validate_password_length_policy(
            password="short",
            length_policy_mode=True,
            min_length=15
        )
        assert not result["valid"]
        assert any("15" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_legacy_validation_requires_complexity(self):
        """Legacy mode should require complexity rules."""
        from src.lib.security import validate_password_length_policy

        # Long but simple - invalid in legacy mode
        result = await validate_password_length_policy(
            password="this is a long passphrase",
            length_policy_mode=False,
            min_length=8,
            require_uppercase=True,
            require_numbers=True
        )
        assert not result["valid"]
        assert result["mode"] == "legacy"

    @pytest.mark.asyncio
    async def test_legacy_validation_accepts_complex_password(self):
        """Legacy mode should accept complex passwords."""
        from src.lib.security import validate_password_length_policy

        result = await validate_password_length_policy(
            password="MySecure123!Pass",
            length_policy_mode=False,
            min_length=8,
            require_uppercase=True,
            require_lowercase=True,
            require_numbers=True,
            require_special=True
        )
        assert result["valid"]
        assert result["mode"] == "legacy"


class TestGetBlocklistService:
    """Tests for the singleton factory function."""

    def test_returns_same_instance(self):
        """Test that get_blocklist_service returns singleton."""
        service1 = get_blocklist_service()
        service2 = get_blocklist_service()
        assert service1 is service2

    def test_reinitialize_creates_new_instance(self):
        """Test that reinitialize flag creates new instance."""
        service1 = get_blocklist_service()
        service2 = get_blocklist_service(reinitialize=True)
        assert service1 is not service2

"""
Unit tests for services/database/registration_code_service.py utility functions.

Tests constant_time_compare and hash_code helper functions.
"""

import pytest

from services.database.registration_code_service import (
    constant_time_compare,
    hash_code,
)


# =============================================================================
# Tests for constant_time_compare function
# =============================================================================


class TestConstantTimeCompare:
    """Tests for constant_time_compare function."""

    def test_equal_strings_returns_true(self):
        """constant_time_compare should return True for equal strings."""
        assert constant_time_compare("abc", "abc") is True

    def test_different_strings_returns_false(self):
        """constant_time_compare should return False for different strings."""
        assert constant_time_compare("abc", "def") is False

    def test_empty_strings_returns_true(self):
        """constant_time_compare should return True for empty strings."""
        assert constant_time_compare("", "") is True

    def test_different_lengths_returns_false(self):
        """constant_time_compare should return False for different length strings."""
        assert constant_time_compare("abc", "abcd") is False

    def test_case_sensitive(self):
        """constant_time_compare should be case sensitive."""
        assert constant_time_compare("ABC", "abc") is False

    def test_whitespace_sensitive(self):
        """constant_time_compare should be whitespace sensitive."""
        assert constant_time_compare("abc ", "abc") is False

    def test_special_characters(self):
        """constant_time_compare should handle special characters."""
        assert constant_time_compare("a-b_c!@#", "a-b_c!@#") is True
        assert constant_time_compare("a-b_c!@#", "a-b_c!@$") is False

    def test_unicode_strings(self):
        """constant_time_compare should handle unicode strings."""
        assert constant_time_compare("hello\u00e9", "hello\u00e9") is True
        assert constant_time_compare("hello\u00e9", "hello\u00e8") is False


# =============================================================================
# Tests for hash_code function
# =============================================================================


class TestHashCode:
    """Tests for hash_code function."""

    def test_returns_sha256_hex(self):
        """hash_code should return SHA-256 hex digest."""
        result = hash_code("TEST")
        # SHA-256 produces 64 character hex string
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_removes_dashes(self):
        """hash_code should normalize by removing dashes."""
        with_dashes = hash_code("ABCD-EFGH")
        without_dashes = hash_code("ABCDEFGH")
        assert with_dashes == without_dashes

    def test_case_insensitive(self):
        """hash_code should normalize to uppercase."""
        upper = hash_code("ABCD")
        lower = hash_code("abcd")
        mixed = hash_code("AbCd")
        assert upper == lower == mixed

    def test_different_codes_produce_different_hashes(self):
        """hash_code should produce different hashes for different codes."""
        hash1 = hash_code("AAAA-BBBB")
        hash2 = hash_code("CCCC-DDDD")
        assert hash1 != hash2

    def test_consistent_hashing(self):
        """hash_code should produce consistent results."""
        code = "ABCD-1234-EFGH-5678"
        hash1 = hash_code(code)
        hash2 = hash_code(code)
        assert hash1 == hash2

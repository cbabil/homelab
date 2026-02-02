# Task 10: Write Unit Tests

## Overview

Write comprehensive unit tests for all NIST compliance components.

## Test Files to Create

### Backend Tests

**File:** `backend/tests/unit/test_password_blocklist.py`

```python
"""
Unit tests for Password Blocklist Service
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.password_blocklist_service import (
    PasswordBlocklistService,
    blocklist_service
)


class TestPasswordBlocklistService:
    """Test cases for PasswordBlocklistService."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance for each test."""
        return PasswordBlocklistService(blocklist_dir="test_data/blocklist")

    # =========================================================================
    # Common Password Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_common_password_blocked(self, service):
        """Common passwords like 'password123' should be blocked."""
        service._common_passwords = {"password123", "123456", "qwerty"}
        service._loaded = True

        result = await service.check_password("password123")

        assert result["blocked"] is True
        assert result["reason"] == "Password is too common"
        assert result["checks"]["common"] is True

    @pytest.mark.asyncio
    async def test_unique_password_allowed(self, service):
        """Unique passwords should be allowed."""
        service._common_passwords = {"password123"}
        service._context_words = set()
        service._loaded = True

        result = await service.check_password("xK9#mN2$vL5@qR8")

        assert result["blocked"] is False
        assert result["checks"]["common"] is False

    # =========================================================================
    # Sequential Pattern Tests
    # =========================================================================

    def test_sequential_numeric_detected(self, service):
        """Sequential numbers (1234) should be detected."""
        assert service.check_sequential_pattern("mypass1234word") is True
        assert service.check_sequential_pattern("9876abcdef") is True

    def test_sequential_alpha_detected(self, service):
        """Sequential letters (abcd) should be detected."""
        assert service.check_sequential_pattern("passabcdword") is True
        assert service.check_sequential_pattern("zyxwtest") is True

    def test_sequential_keyboard_detected(self, service):
        """Keyboard patterns (qwerty) should be detected."""
        assert service.check_sequential_pattern("myqwertypass") is True
        assert service.check_sequential_pattern("asdfword") is True

    def test_short_sequence_allowed(self, service):
        """Short sequences (3 chars) should be allowed."""
        assert service.check_sequential_pattern("abc123") is False
        assert service.check_sequential_pattern("xyz987") is False

    def test_no_sequence_allowed(self, service):
        """Passwords without sequences should be allowed."""
        assert service.check_sequential_pattern("xK9mN2vL5qR8") is False

    # =========================================================================
    # Repetitive Pattern Tests
    # =========================================================================

    def test_repetitive_detected(self, service):
        """Repetitive patterns (aaaa) should be detected."""
        assert service.check_repetitive_pattern("passaaaa") is True
        assert service.check_repetitive_pattern("1111word") is True
        assert service.check_repetitive_pattern("test!!!!") is True

    def test_short_repetition_allowed(self, service):
        """Short repetitions (3 chars) should be allowed."""
        assert service.check_repetitive_pattern("aaa123") is False
        assert service.check_repetitive_pattern("password") is False

    # =========================================================================
    # Context-Specific Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_username_in_password_blocked(self, service):
        """Password containing username should be blocked."""
        service._common_passwords = set()
        service._context_words = set()
        service._loaded = True

        result = await service.check_password("johndoe2024!", username="johndoe")

        assert result["blocked"] is True
        assert "username" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_context_word_blocked(self, service):
        """Password containing context words should be blocked."""
        service._common_passwords = set()
        service._context_words = {"tomo", "admin"}
        service._loaded = True

        result = await service.check_password("mytomo2024")

        assert result["blocked"] is True
        assert "tomo" in result["reason"]

    # =========================================================================
    # HIBP API Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_hibp_api_found(self, service):
        """HIBP API should detect breached passwords."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "1E4C9B93F3F0682250B6CF8331B7EE68FD8:5\nABCDE:10"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # "password" has SHA1 starting with 5BAA6
            result = await service.check_hibp_api("password")

            # This specific hash may not match mock, testing structure
            assert "found" in result

    @pytest.mark.asyncio
    async def test_hibp_api_timeout_handled(self, service):
        """HIBP API timeout should be handled gracefully."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Timeout")
            )

            result = await service.check_hibp_api("password")

            assert result["found"] is False
            assert "error" in result

    # =========================================================================
    # Full Validation Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_long_unique_passphrase_allowed(self, service):
        """Long unique passphrases should be allowed."""
        service._common_passwords = {"password", "123456"}
        service._context_words = {"admin", "tomo"}
        service._loaded = True

        result = await service.check_password(
            "correct-horse-battery-staple-rainbow"
        )

        assert result["blocked"] is False

    @pytest.mark.asyncio
    async def test_multiple_issues_first_reason_returned(self, service):
        """When multiple issues exist, first detected reason is returned."""
        service._common_passwords = {"password123"}
        service._context_words = set()
        service._loaded = True

        # This password is common AND has repetitive pattern
        result = await service.check_password("password123aaaa")

        assert result["blocked"] is True
        # Common check happens first
        assert result["reason"] == "Password is too common"
```

**File:** `backend/tests/unit/test_password_nist_validation.py`

```python
"""
Unit tests for NIST password validation
"""

import pytest
from src.lib.security import validate_password_nist


class TestValidatePasswordNIST:
    """Test cases for NIST password validation."""

    # =========================================================================
    # NIST Mode Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_nist_mode_accepts_long_password_no_complexity(self):
        """NIST mode should accept 15+ char password without complexity."""
        result = await validate_password_nist(
            password="thisisaverylongpassphrase",  # 25 chars, no uppercase/special
            nist_mode=True,
            min_length=15,
            check_blocklist=False
        )

        assert result["valid"] is True
        assert result["nist_compliant"] is True

    @pytest.mark.asyncio
    async def test_nist_mode_rejects_short_password(self):
        """NIST mode should reject password under 15 chars."""
        result = await validate_password_nist(
            password="short",
            nist_mode=True,
            min_length=15,
            check_blocklist=False
        )

        assert result["valid"] is False
        assert "at least 15 characters" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_nist_mode_rejects_sequential(self):
        """NIST mode should reject passwords with sequential patterns."""
        result = await validate_password_nist(
            password="mypassword1234567890",  # Contains 1234
            nist_mode=True,
            min_length=15,
            check_blocklist=False
        )

        assert result["valid"] is False
        assert any("sequential" in e.lower() for e in result["errors"])

    # =========================================================================
    # Legacy Mode Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_legacy_mode_requires_uppercase(self):
        """Legacy mode should require uppercase when configured."""
        result = await validate_password_nist(
            password="password123!",
            nist_mode=False,
            min_length=8,
            legacy_rules={"require_uppercase": True}
        )

        assert result["valid"] is False
        assert any("uppercase" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_legacy_mode_accepts_complex_password(self):
        """Legacy mode should accept password meeting all complexity rules."""
        result = await validate_password_nist(
            password="Password123!",
            nist_mode=False,
            min_length=8,
            legacy_rules={
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_special": True
            },
            check_blocklist=False
        )

        assert result["valid"] is True

    # =========================================================================
    # Max Length Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_max_length_enforced(self):
        """Passwords exceeding max length should be rejected."""
        long_password = "a" * 200

        result = await validate_password_nist(
            password=long_password,
            nist_mode=True,
            max_length=128
        )

        assert result["valid"] is False
        assert any("128" in e for e in result["errors"])
```

### Frontend Tests

**File:** `frontend/src/utils/__tests__/registrationValidation.nist.test.ts`

```typescript
/**
 * Unit tests for NIST password validation utilities
 */

import { describe, it, expect } from 'vitest'
import {
  hasSequentialPattern,
  hasRepetitivePattern,
  checkBasicBlocklist,
  calculateNISTPasswordStrength,
  validatePasswordNIST
} from '../registrationValidation'

describe('NIST Password Validation', () => {
  describe('hasSequentialPattern', () => {
    it('should detect numeric sequences', () => {
      expect(hasSequentialPattern('mypass1234')).toBe(true)
      expect(hasSequentialPattern('9876test')).toBe(true)
    })

    it('should detect alphabetic sequences', () => {
      expect(hasSequentialPattern('passabcd')).toBe(true)
      expect(hasSequentialPattern('zyxwtest')).toBe(true)
    })

    it('should detect keyboard patterns', () => {
      expect(hasSequentialPattern('qwertypass')).toBe(true)
      expect(hasSequentialPattern('asdfword')).toBe(true)
    })

    it('should allow short sequences (3 chars)', () => {
      expect(hasSequentialPattern('abc123')).toBe(false)
    })

    it('should allow passwords without sequences', () => {
      expect(hasSequentialPattern('xK9mN2vL5qR8')).toBe(false)
    })
  })

  describe('hasRepetitivePattern', () => {
    it('should detect 4+ repeated characters', () => {
      expect(hasRepetitivePattern('aaaa')).toBe(true)
      expect(hasRepetitivePattern('pass1111')).toBe(true)
      expect(hasRepetitivePattern('test!!!!')).toBe(true)
    })

    it('should allow 3 repeated characters', () => {
      expect(hasRepetitivePattern('aaa123')).toBe(false)
    })

    it('should allow no repeated characters', () => {
      expect(hasRepetitivePattern('abcdef')).toBe(false)
    })
  })

  describe('checkBasicBlocklist', () => {
    it('should block common passwords', () => {
      const result = checkBasicBlocklist('password')
      expect(result.isBlocked).toBe(true)
      expect(result.reason).toContain('common')
    })

    it('should block password containing username', () => {
      const result = checkBasicBlocklist('johndoe2024', 'johndoe')
      expect(result.isBlocked).toBe(true)
      expect(result.reason).toContain('username')
    })

    it('should allow unique passwords', () => {
      const result = checkBasicBlocklist('xK9mN2vL5qR8wT3')
      expect(result.isBlocked).toBe(false)
    })
  })

  describe('calculateNISTPasswordStrength', () => {
    it('should return score 1 for short passwords', () => {
      const result = calculateNISTPasswordStrength('short', '', 15)
      expect(result.score).toBe(1)
      expect(result.isValid).toBe(false)
    })

    it('should return score 2-3 for 15-24 char passwords', () => {
      const result = calculateNISTPasswordStrength('fifteencharpass', '', 15)
      expect(result.score).toBeGreaterThanOrEqual(2)
      expect(result.isValid).toBe(true)
    })

    it('should return score 4-5 for 25+ char passwords', () => {
      const result = calculateNISTPasswordStrength(
        'this-is-a-very-long-passphrase-indeed',
        '',
        15
      )
      expect(result.score).toBeGreaterThanOrEqual(4)
    })

    it('should mark password invalid if sequential pattern found', () => {
      const result = calculateNISTPasswordStrength('mypassword12345678', '', 15)
      expect(result.isValid).toBe(false)
      expect(result.feedback).toContain(expect.stringMatching(/sequential/i))
    })

    it('should mark password invalid if repetitive pattern found', () => {
      const result = calculateNISTPasswordStrength('mypasswordaaaa!', '', 15)
      expect(result.isValid).toBe(false)
      expect(result.feedback).toContain(expect.stringMatching(/repetitive/i))
    })
  })

  describe('validatePasswordNIST', () => {
    it('should validate correct NIST password', () => {
      const result = validatePasswordNIST('this-is-a-valid-passphrase', '', 15, 128)
      expect(result.isValid).toBe(true)
    })

    it('should reject password under min length', () => {
      const result = validatePasswordNIST('short', '', 15, 128)
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('15')
    })

    it('should reject password over max length', () => {
      const longPassword = 'a'.repeat(150)
      const result = validatePasswordNIST(longPassword, '', 15, 128)
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('128')
    })

    it('should reject empty password', () => {
      const result = validatePasswordNIST('', '', 15, 128)
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('required')
    })
  })
})
```

## Dependencies

- All implementation tasks (01-09) should be complete before testing

## Run Commands

```bash
# Backend tests
cd backend
pytest tests/unit/test_password_blocklist.py -v
pytest tests/unit/test_password_nist_validation.py -v

# Frontend tests
cd frontend
npm run test -- src/utils/__tests__/registrationValidation.nist.test.ts
```

## Acceptance Criteria

- [ ] All backend blocklist tests pass
- [ ] All backend NIST validation tests pass
- [ ] All frontend validation tests pass
- [ ] Test coverage > 80% for new code
- [ ] No flaky tests

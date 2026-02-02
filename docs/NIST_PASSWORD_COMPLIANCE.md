# NIST SP 800-63B-4 Password Compliance

This document describes the implementation plan for making Tomo security settings compliant with NIST Special Publication 800-63B-4 (Digital Identity Guidelines - Authentication and Lifecycle Management).

## Table of Contents

1. [Overview](#overview)
2. [NIST SP 800-63B-4 Requirements](#nist-sp-800-63b-4-requirements)
3. [Current vs NIST Comparison](#current-vs-nist-comparison)
4. [Implementation Design](#implementation-design)
5. [Migration Strategy](#migration-strategy)
6. [Testing Plan](#testing-plan)
7. [References](#references)

---

## Overview

NIST SP 800-63B-4 (Revision 4, published in 2024) represents a significant shift in password policy recommendations. The guidelines move away from arbitrary complexity requirements and mandatory password rotation toward evidence-based practices focused on password length and blocklist screening.

### Key Changes from Traditional Policies

| Traditional (Legacy) | NIST SP 800-63B-4 |
|---------------------|-------------------|
| Force uppercase, numbers, special chars | SHALL NOT impose composition rules |
| Mandatory 90-day password rotation | No mandatory changes unless compromised |
| 8 character minimum | 15 character minimum (password-only auth) |
| ASCII-only passwords | SHALL allow Unicode, spaces, emojis |
| No blocklist checking | SHALL screen against breached passwords |

---

## NIST SP 800-63B-4 Requirements

### Mandatory Requirements (SHALL)

1. **Minimum Password Length**: At least 15 characters when the password is the sole authenticator (8 characters when combined with MFA)

2. **Maximum Password Length**: SHALL permit passwords of at least 64 characters

3. **No Composition Rules**: SHALL NOT impose composition rules requiring mixtures of character types (uppercase, lowercase, digits, special characters)

4. **No Mandatory Rotation**: SHALL NOT require periodic password changes unless there is evidence of compromise

5. **Blocklist Screening**: SHALL compare passwords against a blocklist containing:
   - Passwords from previous breach corpuses (e.g., Have I Been Pwned)
   - Dictionary words
   - Context-specific words (username, service name)
   - Repetitive/sequential characters (aaaa, 1234, abcd)

6. **Unicode Support**: SHALL accept all printable ASCII characters, the space character, and Unicode characters

### Recommended Practices (SHOULD)

1. Offer password strength meters based on length and entropy
2. Allow paste functionality in password fields
3. Provide clear feedback when passwords are rejected
4. Avoid password hints

---

## Current vs NIST Comparison

### Current Implementation

| Setting | Current Default | Location |
|---------|----------------|----------|
| Minimum length | 8 characters | `seed_default_settings.sql` |
| Require uppercase | true | `seed_default_settings.sql` |
| Require numbers | true | `seed_default_settings.sql` |
| Require special chars | true | `seed_default_settings.sql` |
| Password expiration | 90 days | `seed_default_settings.sql` |
| Blocklist checking | Not implemented | - |
| Unicode support | Limited | `security.py` |

### NIST-Compliant Target

| Setting | NIST Value | Notes |
|---------|-----------|-------|
| Minimum length | 15 characters | Password-only authentication |
| Require uppercase | false (disabled) | SHALL NOT impose |
| Require numbers | false (disabled) | SHALL NOT impose |
| Require special chars | false (disabled) | SHALL NOT impose |
| Password expiration | 0 (disabled) | No mandatory rotation |
| Blocklist checking | Enabled | Required by NIST |
| Unicode support | Full | Including spaces and emojis |

---

## Implementation Design

### Architecture Overview

```
+------------------+     +------------------+     +-------------------+
|   Frontend UI    |     |   Backend API    |     |  Blocklist Data   |
|                  |     |                  |     |                   |
| SecuritySettings |---->| validate_nist()  |---->| common_passwords  |
| PasswordStrength |     | BlocklistService |     | context_words     |
| Registration     |     |                  |     | (optional: HIBP)  |
+------------------+     +------------------+     +-------------------+
```

### New Settings

The following settings will be added to enable NIST compliance:

```sql
-- NIST Compliance Mode (master toggle)
security.nist_compliance_mode = false  -- Default OFF for backward compatibility

-- Password length bounds
security.password_max_length = 128     -- NIST requires at least 64

-- Blocklist settings
security.enable_blocklist_check = true -- Screen against common passwords
security.enable_hibp_api_check = false -- Optional: Check Have I Been Pwned API

-- Unicode support
security.allow_unicode_passwords = true
```

### Dual-Mode Operation

The implementation supports two modes:

#### NIST Compliance Mode (ON)

When `security.nist_compliance_mode = true`:

- **Minimum length**: 15-64 characters (configurable)
- **Complexity rules**: Disabled (hidden in UI)
- **Password expiration**: Disabled (hidden in UI)
- **Blocklist screening**: Enabled
- **Password strength**: Calculated based on length and entropy

#### Legacy Mode (OFF)

When `security.nist_compliance_mode = false`:

- **Minimum length**: 6-32 characters (configurable)
- **Complexity rules**: Configurable toggles (uppercase, numbers, special)
- **Password expiration**: Configurable (0-365 days)
- **Blocklist screening**: Optional
- **Password strength**: Calculated based on complexity checklist

### Password Blocklist Service

A new service will handle password screening:

```python
class PasswordBlocklistService:
    """
    NIST SP 800-63B-4 compliant password screening.

    Checks:
    1. Common passwords (top 10,000 from breaches)
    2. Context-specific words (username, service name)
    3. Sequential patterns (1234, abcd, qwerty)
    4. Repetitive patterns (aaaa, 1111)
    5. Optional: HIBP API (k-Anonymity, privacy-preserving)
    """

    async def check_password(
        self,
        password: str,
        username: str = "",
        check_hibp: bool = False
    ) -> BlocklistResult:
        ...
```

### UI Changes

#### Security Settings Page

```
Password Policy
+-------------------------------------------+
| [Toggle] NIST SP 800-63B Compliance       |
|          Modern password policy based on  |
|          length and blocklist screening   |
+-------------------------------------------+

When ENABLED (NIST mode):
  +---------------------------------------+
  | [Info Banner]                         |
  | NIST mode enforces 15+ character      |
  | passwords, screens against breached   |
  | passwords, and removes complexity     |
  | rules and mandatory expiration.       |
  +---------------------------------------+

  Minimum Length:    [15] (slider: 15-64)
  Blocklist Check:   [x] Enabled
  HIBP API Check:    [ ] Disabled

  (Complexity toggles hidden)
  (Expiration hidden)

When DISABLED (Legacy mode):
  +---------------------------------------+
  | [Warning Banner]                      |
  | Legacy complexity rules are being     |
  | phased out. Consider NIST compliance. |
  +---------------------------------------+

  Minimum Length:    [8]  (slider: 6-32)
  Require Uppercase: [x]
  Require Numbers:   [x]
  Require Special:   [x]
  Expiration:        [90 days]
```

#### Password Strength Indicator

```
NIST Mode:
+----------------------------------------+
| Password Strength: Strong              |
| [=========----------] 65%              |
|                                        |
| [x] At least 15 characters             |
| [x] Not a commonly used password       |
| [x] No sequential patterns (1234)      |
| [x] No repetitive characters (aaaa)    |
|                                        |
| Tip: Use a passphrase like             |
| "correct-horse-battery-staple"         |
+----------------------------------------+

Legacy Mode:
+----------------------------------------+
| Password Strength: Good                |
| [=======-----------] 80%               |
|                                        |
| [x] 12+ characters                     |
| [x] Uppercase letter                   |
| [x] Lowercase letter                   |
| [x] Number                             |
| [ ] Special character                  |
+----------------------------------------+
```

---

## Migration Strategy

### Phase 1: Introduction (v1.1.0)

- Add NIST compliance settings (default: OFF)
- Add blocklist service
- Add NIST mode toggle to Security Settings
- Existing deployments unaffected

### Phase 2: Deprecation Warning (v1.2.0)

- Show deprecation banner for legacy mode
- Add documentation links
- Encourage migration to NIST mode

### Phase 3: Default Change (v2.0.0)

- Change default to NIST mode ON
- Legacy mode still available
- Migration guide provided

### Phase 4: Legacy Removal (v3.0.0)

- Consider removing legacy mode entirely
- Based on adoption metrics

### Backward Compatibility

1. **Existing passwords**: Continue to work regardless of mode
2. **New passwords only**: NIST rules apply only to new passwords and password changes
3. **Settings preserved**: Switching modes doesn't lose previous settings
4. **API compatibility**: Existing API endpoints unchanged

---

## Testing Plan

### Unit Tests

```python
# Backend: test_password_blocklist.py
def test_common_password_blocked():
    """Password123 should be blocked"""

def test_sequential_pattern_detected():
    """mypassword1234 should fail"""

def test_repetitive_pattern_detected():
    """aaaa in password should fail"""

def test_username_in_password_blocked():
    """johndoe2024 should fail for user 'johndoe'"""

def test_long_unique_passphrase_allowed():
    """correct-horse-battery-staple should pass"""
```

```typescript
// Frontend: registrationValidation.test.ts
it('should reject password under 15 chars in NIST mode')
it('should accept 15+ char password without complexity in NIST mode')
it('should detect sequential patterns')
it('should detect repetitive patterns')
```

### Integration Tests

```typescript
// E2E: nist-password-compliance.spec.ts
test('toggle NIST mode shows/hides complexity options')
test('NIST mode enforces 15 char minimum')
test('legacy mode enforces complexity rules')
test('blocklist rejects common passwords')
```

### Manual Testing Checklist

- [ ] Enable NIST mode in Security Settings
- [ ] Verify complexity toggles are hidden
- [ ] Verify expiration dropdown is hidden
- [ ] Set minimum length to 15
- [ ] Create new user with 15+ char password (no complexity)
- [ ] Verify password "password123456" is rejected (too common)
- [ ] Verify password "1234567890123456" is rejected (sequential)
- [ ] Disable NIST mode
- [ ] Verify complexity toggles reappear
- [ ] Verify legacy validation works

---

## References

1. **NIST SP 800-63B-4**: [Digital Identity Guidelines - Authentication and Lifecycle Management](https://pages.nist.gov/800-63-4/sp800-63b.html)

2. **NIST SP 800-63B-4 Supplement**: [Syncable Authenticators (Passkeys)](https://pages.nist.gov/800-63-4/sp800-63Bsup1.html)

3. **Have I Been Pwned API**: [k-Anonymity Password Search](https://haveibeenpwned.com/API/v3#SearchingPwnedPasswordsByRange)

4. **SecLists Common Passwords**: [GitHub - danielmiessler/SecLists](https://github.com/danielmiessler/SecLists/tree/master/Passwords/Common-Credentials)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-22 | Initial implementation plan |

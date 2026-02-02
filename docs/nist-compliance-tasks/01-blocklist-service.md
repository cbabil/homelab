# Task 01: Create Password Blocklist Service

## Overview

Create a new backend service to screen passwords against known breached/common passwords per NIST SP 800-63B-4 requirements.

## File to Create

`backend/src/services/password_blocklist_service.py`

## Requirements

### Functional Requirements

1. **Common Password Check**: Load and check against top 10,000 common passwords
2. **Context-Specific Check**: Reject passwords containing username or service-related words
3. **Sequential Pattern Detection**: Detect patterns like `1234`, `abcd`, `qwerty`
4. **Repetitive Pattern Detection**: Detect patterns like `aaaa`, `1111`
5. **Optional HIBP API**: Check Have I Been Pwned API using k-Anonymity (privacy-preserving)

### Non-Functional Requirements

1. **Performance**: Blocklist lookup must be O(1) using hash set
2. **Memory**: Keep memory footprint reasonable (~5MB for blocklist)
3. **Graceful Degradation**: HIBP API failures should not block authentication
4. **Logging**: Log blocklist check results for audit purposes

## Implementation

```python
"""
Password Blocklist Service

Implements NIST SP 800-63B-4 password screening:
- Common/breached passwords
- Context-specific words
- Sequential/repetitive patterns
- Optional HIBP API integration
"""

import gzip
import hashlib
import re
from pathlib import Path
from typing import Dict, Set, Optional, Any
import httpx
import structlog

logger = structlog.get_logger("password_blocklist")


class BlocklistResult:
    """Result of password blocklist check."""
    blocked: bool
    reason: Optional[str]
    checks: Dict[str, Any]


class PasswordBlocklistService:
    """NIST-compliant password screening service."""

    def __init__(self, blocklist_dir: str = "data/blocklist"):
        self.blocklist_dir = Path(blocklist_dir)
        self._common_passwords: Set[str] = set()
        self._context_words: Set[str] = set()
        self._loaded = False

    async def load_blocklists(self) -> None:
        """Load blocklist files into memory."""
        # Load common passwords (normalized to lowercase)
        common_file = self.blocklist_dir / "common_passwords.txt.gz"
        if common_file.exists():
            with gzip.open(common_file, 'rt', encoding='utf-8') as f:
                self._common_passwords = {line.strip().lower() for line in f if line.strip()}

        # Load context words
        context_file = self.blocklist_dir / "context_words.txt"
        if context_file.exists():
            with open(context_file, 'r', encoding='utf-8') as f:
                self._context_words = {line.strip().lower() for line in f if line.strip()}

        self._loaded = True
        logger.info("Blocklists loaded",
                   common_count=len(self._common_passwords),
                   context_count=len(self._context_words))

    def check_common_password(self, password: str) -> bool:
        """Check if password is in common passwords list."""
        return password.lower() in self._common_passwords

    def check_context_specific(self, password: str, username: str = "") -> Optional[str]:
        """Check for context-specific words in password."""
        pwd_lower = password.lower()

        # Check username variants
        if username and len(username) >= 3:
            if username.lower() in pwd_lower:
                return "Password contains your username"

        # Check service-specific words
        for word in self._context_words:
            if word in pwd_lower:
                return f"Password contains common word: {word}"

        return None

    def check_sequential_pattern(self, password: str) -> bool:
        """Check for sequential characters (1234, abcd)."""
        sequences = [
            "0123456789",
            "9876543210",
            "abcdefghijklmnopqrstuvwxyz",
            "zyxwvutsrqponmlkjihgfedcba",
            "qwertyuiop",
            "asdfghjkl",
            "zxcvbnm"
        ]
        pwd_lower = password.lower()
        for seq in sequences:
            for i in range(len(seq) - 3):
                if seq[i:i+4] in pwd_lower:
                    return True
        return False

    def check_repetitive_pattern(self, password: str) -> bool:
        """Check for repetitive characters (aaaa, 1111)."""
        return bool(re.search(r'(.)\1{3,}', password))

    async def check_hibp_api(self, password: str) -> Dict[str, Any]:
        """
        Check password against Have I Been Pwned API (k-Anonymity).

        Only the first 5 characters of the SHA-1 hash are sent,
        preserving privacy while checking against breach data.
        """
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.pwnedpasswords.com/range/{prefix}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    for line in response.text.splitlines():
                        hash_suffix, count = line.split(':')
                        if hash_suffix == suffix:
                            return {
                                "found": True,
                                "count": int(count),
                                "message": f"Password found in {count} data breaches"
                            }
        except Exception as e:
            logger.warning("HIBP API check failed", error=str(e))
            return {"found": False, "error": str(e)}

        return {"found": False}

    async def check_password(
        self,
        password: str,
        username: str = "",
        check_hibp: bool = False
    ) -> Dict[str, Any]:
        """
        Comprehensive password blocklist check.

        Args:
            password: The password to check
            username: Optional username for context check
            check_hibp: Whether to check HIBP API

        Returns:
            {
                "blocked": bool,
                "reason": str or None,
                "checks": {
                    "common": bool,
                    "context": str or None,
                    "sequential": bool,
                    "repetitive": bool,
                    "hibp": dict or None
                }
            }
        """
        if not self._loaded:
            await self.load_blocklists()

        checks = {
            "common": self.check_common_password(password),
            "context": self.check_context_specific(password, username),
            "sequential": self.check_sequential_pattern(password),
            "repetitive": self.check_repetitive_pattern(password),
            "hibp": None
        }

        if check_hibp:
            checks["hibp"] = await self.check_hibp_api(password)

        # Determine if blocked and why
        if checks["common"]:
            return {"blocked": True, "reason": "Password is too common", "checks": checks}
        if checks["context"]:
            return {"blocked": True, "reason": checks["context"], "checks": checks}
        if checks["sequential"]:
            return {"blocked": True, "reason": "Password contains sequential characters", "checks": checks}
        if checks["repetitive"]:
            return {"blocked": True, "reason": "Password contains repetitive characters", "checks": checks}
        if checks["hibp"] and checks["hibp"].get("found"):
            return {"blocked": True, "reason": checks["hibp"]["message"], "checks": checks}

        return {"blocked": False, "reason": None, "checks": checks}


# Singleton instance
blocklist_service = PasswordBlocklistService()
```

## Dependencies

Add to `backend/requirements.txt`:
```
httpx>=0.24.0  # For async HIBP API calls (may already be present)
```

## Testing

See [10-unit-tests.md](./10-unit-tests.md) for test cases.

## Acceptance Criteria

- [ ] Service loads blocklist files on first use
- [ ] Common passwords are blocked (e.g., "password123")
- [ ] Passwords containing username are blocked
- [ ] Sequential patterns are detected (4+ chars)
- [ ] Repetitive patterns are detected (4+ same char)
- [ ] HIBP API check is optional and gracefully handles failures
- [ ] Service is available as singleton `blocklist_service`

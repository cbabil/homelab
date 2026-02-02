"""
Password Blocklist Service

NIST SP 800-63B-4 compliant password screening service.
Checks passwords against common password lists, patterns, and context-specific words.
Optionally integrates with Have I Been Pwned API using k-Anonymity.
"""

import gzip
import hashlib
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import structlog
import httpx

logger = structlog.get_logger("password_blocklist")

# Pattern definitions
SEQUENTIAL_PATTERNS = [
    r'0123', r'1234', r'2345', r'3456', r'4567', r'5678', r'6789',
    r'abcd', r'bcde', r'cdef', r'defg', r'efgh', r'fghi', r'ghij',
    r'hijk', r'ijkl', r'jklm', r'klmn', r'lmno', r'mnop', r'nopq',
    r'opqr', r'pqrs', r'qrst', r'rstu', r'stuv', r'tuvw', r'uvwx',
    r'vwxy', r'wxyz',
    r'qwer', r'wert', r'erty', r'rtyu', r'tyui', r'yuio', r'uiop',
    r'asdf', r'sdfg', r'dfgh', r'fghj', r'ghjk', r'hjkl',
    r'zxcv', r'xcvb', r'cvbn', r'vbnm',
]

# Context-specific words to block
DEFAULT_CONTEXT_WORDS = [
    'tomo', 'admin', 'administrator', 'password', 'passwd',
    'root', 'user', 'login', 'welcome', 'letmein', 'master',
    'docker', 'server', 'linux', 'ubuntu', 'debian', 'centos',
]


class PasswordBlocklistService:
    """Service for checking passwords against blocklists and patterns."""

    def __init__(
        self,
        blocklist_path: Optional[Path] = None,
        context_words_path: Optional[Path] = None,
        enable_hibp: bool = False
    ):
        self._blocklist: Set[str] = set()
        self._context_words: Set[str] = set(DEFAULT_CONTEXT_WORDS)
        self._enable_hibp = enable_hibp
        self._blocklist_loaded = False

        # Set default paths
        data_dir = Path(__file__).parent.parent / "data" / "blocklist"
        self._blocklist_path = blocklist_path or data_dir / "common_passwords.txt.gz"
        self._context_words_path = context_words_path or data_dir / "context_words.txt"

        # Load blocklists
        self._load_blocklist()
        self._load_context_words()

    def _load_blocklist(self) -> None:
        """Load the common passwords blocklist from gzipped file."""
        try:
            if self._blocklist_path.exists():
                with gzip.open(self._blocklist_path, 'rt', encoding='utf-8') as f:
                    self._blocklist = {line.strip().lower() for line in f if line.strip()}
                self._blocklist_loaded = True
                logger.info(
                    "password_blocklist_loaded",
                    count=len(self._blocklist),
                    path=str(self._blocklist_path)
                )
            else:
                logger.warning(
                    "password_blocklist_not_found",
                    path=str(self._blocklist_path)
                )
        except Exception as e:
            logger.error("password_blocklist_load_error", error=str(e))

    def _load_context_words(self) -> None:
        """Load context-specific words from file."""
        try:
            if self._context_words_path.exists():
                with open(self._context_words_path, 'r', encoding='utf-8') as f:
                    additional_words = {
                        line.strip().lower() for line in f if line.strip()
                    }
                    self._context_words.update(additional_words)
                logger.info(
                    "context_words_loaded",
                    count=len(self._context_words),
                    path=str(self._context_words_path)
                )
        except Exception as e:
            logger.warning("context_words_load_error", error=str(e))

    def check_common_password(self, password: str) -> bool:
        """Check if password is in the common passwords blocklist."""
        return password.lower() in self._blocklist

    def check_sequential_pattern(self, password: str) -> Optional[str]:
        """Check for sequential character patterns."""
        password_lower = password.lower()
        for pattern in SEQUENTIAL_PATTERNS:
            if pattern in password_lower:
                return pattern
            # Check reverse patterns
            if pattern[::-1] in password_lower:
                return pattern[::-1]
        return None

    def check_repetitive_pattern(self, password: str) -> Optional[str]:
        """Check for repetitive character patterns (e.g., aaaa, 1111)."""
        # Check for 3+ consecutive identical characters
        match = re.search(r'(.)\1{2,}', password)
        if match:
            return match.group(0)

        # Check for repeated patterns like 'abab', '1212'
        for length in range(2, 5):
            pattern = rf'(.{{{length}}})\1+'
            match = re.search(pattern, password)
            if match:
                return match.group(0)

        return None

    def check_context_words(
        self,
        password: str,
        username: str = "",
        additional_context: Optional[List[str]] = None
    ) -> Optional[str]:
        """Check if password contains context-specific words."""
        password_lower = password.lower()

        # Check against default context words
        for word in self._context_words:
            if len(word) >= 3 and word in password_lower:
                return word

        # Check against username
        if username and len(username) >= 3:
            if username.lower() in password_lower:
                return f"username:{username}"

        # Check additional context words
        if additional_context:
            for word in additional_context:
                if len(word) >= 3 and word.lower() in password_lower:
                    return word

        return None

    async def check_hibp(self, password: str) -> Dict[str, Any]:
        """
        Check password against Have I Been Pwned API using k-Anonymity.
        Only sends first 5 chars of SHA-1 hash to API.
        """
        if not self._enable_hibp:
            return {"checked": False, "reason": "HIBP check disabled"}

        try:
            # Create SHA-1 hash
            sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
            prefix = sha1_hash[:5]
            suffix = sha1_hash[5:]

            # Query HIBP API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.pwnedpasswords.com/range/{prefix}",
                    headers={"Add-Padding": "true"},
                    timeout=5.0
                )

                if response.status_code == 200:
                    # Parse response to find matching hash
                    for line in response.text.splitlines():
                        hash_suffix, count = line.split(':')
                        if hash_suffix == suffix:
                            return {
                                "checked": True,
                                "compromised": True,
                                "breach_count": int(count)
                            }
                    return {"checked": True, "compromised": False}
                else:
                    return {
                        "checked": False,
                        "reason": f"API error: {response.status_code}"
                    }
        except Exception as e:
            logger.warning("hibp_check_error", error=str(e))
            return {"checked": False, "reason": str(e)}

    async def validate_password(
        self,
        password: str,
        username: str = "",
        check_blocklist: bool = True,
        check_hibp: bool = False,
        additional_context: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive password validation for NIST compliance.

        Returns:
            Dict with validation results including:
            - valid: bool
            - errors: List of error messages
            - warnings: List of warning messages
            - checks: Dict of individual check results
        """
        errors: List[str] = []
        warnings: List[str] = []
        checks: Dict[str, Any] = {}

        # Check blocklist
        if check_blocklist:
            if self.check_common_password(password):
                errors.append("Password is too common and easily guessed")
                checks["common_password"] = False
            else:
                checks["common_password"] = True

        # Check sequential patterns
        seq_pattern = self.check_sequential_pattern(password)
        if seq_pattern:
            errors.append(f"Password contains sequential pattern: {seq_pattern}")
            checks["sequential_pattern"] = False
        else:
            checks["sequential_pattern"] = True

        # Check repetitive patterns
        rep_pattern = self.check_repetitive_pattern(password)
        if rep_pattern:
            errors.append("Password contains repetitive pattern")
            checks["repetitive_pattern"] = False
        else:
            checks["repetitive_pattern"] = True

        # Check context words
        context_word = self.check_context_words(password, username, additional_context)
        if context_word:
            if context_word.startswith("username:"):
                errors.append("Password should not contain your username")
            else:
                errors.append(f"Password contains easily guessed word: {context_word}")
            checks["context_words"] = False
        else:
            checks["context_words"] = True

        # Check HIBP if enabled
        if check_hibp and self._enable_hibp:
            hibp_result = await self.check_hibp(password)
            checks["hibp"] = hibp_result
            if hibp_result.get("compromised"):
                count = hibp_result.get("breach_count", 0)
                errors.append(
                    f"Password found in {count:,} data breaches"
                )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "checks": checks
        }

    @property
    def blocklist_loaded(self) -> bool:
        """Check if blocklist was successfully loaded."""
        return self._blocklist_loaded

    @property
    def blocklist_size(self) -> int:
        """Get number of passwords in blocklist."""
        return len(self._blocklist)


# Singleton instance
_blocklist_service: Optional[PasswordBlocklistService] = None


def get_blocklist_service(
    enable_hibp: bool = False,
    reinitialize: bool = False
) -> PasswordBlocklistService:
    """Get or create the blocklist service singleton."""
    global _blocklist_service
    if _blocklist_service is None or reinitialize:
        _blocklist_service = PasswordBlocklistService(enable_hibp=enable_hibp)
    return _blocklist_service

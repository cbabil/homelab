# Phase 6: Production Hardening - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Security audit, backup/restore, RPM packaging, and documentation. Ready for public release.

**Architecture:** Security hardening across all layers, encrypted backup/restore CLI, RPM packaging with systemd integration, comprehensive documentation.

**Tech Stack:** Python (cryptography for backup, Pydantic strict mode), RPM spec files, systemd units, Markdown docs

---

## Task 1: Add Input Validation and Security Hardening

**Files:**
- Create: `backend/src/lib/security.py`
- Create: `backend/src/lib/rate_limiter.py`
- Test: `backend/tests/unit/test_security.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_security.py`:

```python
"""Tests for security utilities."""
import pytest
import time
from lib.security import (
    validate_server_input,
    validate_app_config,
    constant_time_compare,
    sanitize_log_message
)
from lib.rate_limiter import RateLimiter


class TestInputValidation:
    """Tests for input validation."""

    def test_validate_server_hostname_valid(self):
        """Should accept valid hostname."""
        result = validate_server_input(host="server.example.com", port=22)
        assert result["valid"] is True

    def test_validate_server_hostname_invalid(self):
        """Should reject invalid hostname with shell chars."""
        result = validate_server_input(host="server;rm -rf /", port=22)
        assert result["valid"] is False
        assert "invalid" in result["error"].lower()

    def test_validate_server_ip_valid(self):
        """Should accept valid IP address."""
        result = validate_server_input(host="192.168.1.100", port=22)
        assert result["valid"] is True

    def test_validate_server_port_range(self):
        """Should reject invalid port numbers."""
        result = validate_server_input(host="server.local", port=99999)
        assert result["valid"] is False

    def test_validate_app_config_safe(self):
        """Should accept safe app config."""
        config = {"env": {"DB_HOST": "localhost"}, "ports": {"80": 8080}}
        result = validate_app_config(config)
        assert result["valid"] is True

    def test_validate_app_config_dangerous_env(self):
        """Should reject dangerous environment values."""
        config = {"env": {"CMD": "$(rm -rf /)"}}
        result = validate_app_config(config)
        assert result["valid"] is False


class TestConstantTimeCompare:
    """Tests for constant-time comparison."""

    def test_constant_time_compare_equal(self):
        """Should return True for equal strings."""
        assert constant_time_compare("password123", "password123") is True

    def test_constant_time_compare_not_equal(self):
        """Should return False for different strings."""
        assert constant_time_compare("password123", "password456") is False

    def test_constant_time_compare_timing(self):
        """Should take similar time regardless of input."""
        # This is a basic timing check
        start = time.perf_counter()
        constant_time_compare("a" * 1000, "b" * 1000)
        time1 = time.perf_counter() - start

        start = time.perf_counter()
        constant_time_compare("a" * 1000, "a" * 999 + "b")
        time2 = time.perf_counter() - start

        # Times should be within 10x of each other (loose bound for test stability)
        assert time1 < time2 * 10 and time2 < time1 * 10


class TestRateLimiter:
    """Tests for rate limiting."""

    def test_rate_limiter_allows_initial(self):
        """Should allow initial requests."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        assert limiter.is_allowed("user1") is True

    def test_rate_limiter_blocks_excess(self):
        """Should block after exceeding limit."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is False

    def test_rate_limiter_per_key(self):
        """Should track limits per key."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is False
        assert limiter.is_allowed("user2") is True  # Different key


class TestLogSanitization:
    """Tests for log sanitization."""

    def test_sanitize_removes_password(self):
        """Should mask password in log messages."""
        msg = "Login attempt with password=secret123"
        sanitized = sanitize_log_message(msg)
        assert "secret123" not in sanitized
        assert "***" in sanitized

    def test_sanitize_removes_token(self):
        """Should mask tokens in log messages."""
        msg = "Auth token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz"
        sanitized = sanitize_log_message(msg)
        assert "eyJ" not in sanitized
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_security.py -v --no-cov
```

Expected: FAIL

**Step 3: Create security utilities**

Create `backend/src/lib/security.py`:

```python
"""
Security Utilities

Input validation, constant-time operations, and log sanitization.
"""

import re
import hmac
import ipaddress
from typing import Dict, Any
import structlog

logger = structlog.get_logger("security")

# Dangerous patterns for shell injection
DANGEROUS_PATTERNS = [
    r'[;&|`$()]',  # Shell metacharacters
    r'\.\.',  # Path traversal
    r'[\x00-\x1f]',  # Control characters
]

# Patterns to sanitize in logs
SENSITIVE_PATTERNS = [
    (r'password[=:]\s*\S+', 'password=***'),
    (r'token[=:]\s*\S+', 'token=***'),
    (r'key[=:]\s*\S+', 'key=***'),
    (r'secret[=:]\s*\S+', 'secret=***'),
    (r'eyJ[A-Za-z0-9_-]*\.?[A-Za-z0-9_-]*\.?[A-Za-z0-9_-]*', '***JWT***'),
]


def validate_server_input(host: str, port: int) -> Dict[str, Any]:
    """Validate server connection parameters."""
    errors = []

    # Validate host
    if not host:
        errors.append("Host is required")
    else:
        # Check for dangerous characters
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, host):
                errors.append(f"Invalid characters in hostname")
                break

        # Validate as IP or hostname
        if not errors:
            try:
                ipaddress.ip_address(host)
            except ValueError:
                # Not an IP, validate as hostname
                hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
                if not re.match(hostname_pattern, host):
                    errors.append("Invalid hostname format")

    # Validate port
    if not isinstance(port, int) or port < 1 or port > 65535:
        errors.append("Port must be between 1 and 65535")

    if errors:
        return {"valid": False, "error": "; ".join(errors)}
    return {"valid": True}


def validate_app_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate app deployment configuration."""
    errors = []

    # Validate environment variables
    env_vars = config.get("env", {})
    for key, value in env_vars.items():
        if not isinstance(key, str) or not isinstance(value, str):
            errors.append(f"Invalid env var type for {key}")
            continue

        # Check for command injection in values
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, str(value)):
                errors.append(f"Dangerous characters in env var {key}")
                break

    # Validate port mappings
    ports = config.get("ports", {})
    for container_port, host_port in ports.items():
        try:
            cp = int(container_port)
            hp = int(host_port)
            if cp < 1 or cp > 65535 or hp < 1 or hp > 65535:
                errors.append(f"Invalid port mapping: {container_port}:{host_port}")
        except (ValueError, TypeError):
            errors.append(f"Invalid port format: {container_port}:{host_port}")

    if errors:
        return {"valid": False, "error": "; ".join(errors)}
    return {"valid": True}


def constant_time_compare(a: str, b: str) -> bool:
    """
    Compare two strings in constant time to prevent timing attacks.
    Used for password/token comparison.
    """
    return hmac.compare_digest(a.encode('utf-8'), b.encode('utf-8'))


def sanitize_log_message(message: str) -> str:
    """Remove sensitive data from log messages."""
    result = message
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def validate_username(username: str) -> Dict[str, Any]:
    """Validate username format."""
    if not username:
        return {"valid": False, "error": "Username is required"}

    if len(username) < 3 or len(username) > 32:
        return {"valid": False, "error": "Username must be 3-32 characters"}

    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', username):
        return {"valid": False, "error": "Username must start with letter and contain only alphanumeric, underscore, hyphen"}

    return {"valid": True}


def validate_password_strength(password: str) -> Dict[str, Any]:
    """Check password meets minimum requirements."""
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters")

    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain uppercase letter")

    if not re.search(r'[a-z]', password):
        errors.append("Password must contain lowercase letter")

    if not re.search(r'[0-9]', password):
        errors.append("Password must contain digit")

    if errors:
        return {"valid": False, "errors": errors}
    return {"valid": True}
```

Create `backend/src/lib/rate_limiter.py`:

```python
"""
Rate Limiter

Simple in-memory rate limiting for auth endpoints.
"""

import time
from collections import defaultdict
from typing import Dict, List
import structlog

logger = structlog.get_logger("rate_limiter")


class RateLimiter:
    """In-memory rate limiter with sliding window."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed for given key.

        Args:
            key: Identifier (e.g., IP address, user ID)

        Returns:
            True if request is allowed, False if rate limited
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        self.requests[key] = [
            ts for ts in self.requests[key]
            if ts > window_start
        ]

        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            logger.warning("Rate limit exceeded", key=key)
            return False

        # Record request
        self.requests[key].append(now)
        return True

    def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        self.requests[key] = []

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key."""
        now = time.time()
        window_start = now - self.window_seconds

        current = len([
            ts for ts in self.requests[key]
            if ts > window_start
        ])

        return max(0, self.max_requests - current)
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_security.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/lib/security.py backend/src/lib/rate_limiter.py backend/tests/unit/test_security.py
git commit -m "feat(security): add input validation and rate limiting"
```

---

## Task 2: Create Backup Service

**Files:**
- Create: `backend/src/services/backup_service.py`
- Test: `backend/tests/unit/test_backup_service.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_backup_service.py`:

```python
"""Tests for backup service."""
import pytest
import json
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch
from services.backup_service import BackupService


class TestBackupService:
    """Tests for BackupService."""

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = MagicMock()
        db.export_users = AsyncMock(return_value=[
            {"id": "u1", "username": "admin", "role": "admin"}
        ])
        db.export_servers = AsyncMock(return_value=[
            {"id": "s1", "name": "server1", "host": "192.168.1.1"}
        ])
        db.export_settings = AsyncMock(return_value={"theme": "dark"})
        db.import_users = AsyncMock()
        db.import_servers = AsyncMock()
        db.import_settings = AsyncMock()
        return db

    @pytest.fixture
    def backup_service(self, mock_db_service):
        """Create backup service with mocks."""
        return BackupService(db_service=mock_db_service)

    def test_create_backup_data(self, backup_service, mock_db_service):
        """Should create backup data structure."""
        import asyncio
        data = asyncio.get_event_loop().run_until_complete(
            backup_service._collect_backup_data()
        )

        assert "version" in data
        assert "timestamp" in data
        assert "users" in data
        assert "servers" in data

    def test_encrypt_backup(self, backup_service):
        """Should encrypt backup data."""
        data = {"test": "data"}
        password = "testpassword123"

        encrypted = backup_service._encrypt_data(data, password)

        assert encrypted != json.dumps(data).encode()
        assert len(encrypted) > 0

    def test_decrypt_backup(self, backup_service):
        """Should decrypt backup data."""
        original_data = {"test": "data", "nested": {"key": "value"}}
        password = "testpassword123"

        encrypted = backup_service._encrypt_data(original_data, password)
        decrypted = backup_service._decrypt_data(encrypted, password)

        assert decrypted == original_data

    def test_decrypt_wrong_password(self, backup_service):
        """Should fail with wrong password."""
        data = {"test": "data"}
        encrypted = backup_service._encrypt_data(data, "correct")

        with pytest.raises(Exception):
            backup_service._decrypt_data(encrypted, "wrong")

    def test_validate_backup_structure(self, backup_service):
        """Should validate backup structure."""
        valid_backup = {
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00Z",
            "users": [],
            "servers": [],
            "settings": {}
        }

        result = backup_service._validate_backup(valid_backup)
        assert result["valid"] is True

    def test_validate_backup_missing_fields(self, backup_service):
        """Should reject backup with missing fields."""
        invalid_backup = {"version": "1.0"}

        result = backup_service._validate_backup(invalid_backup)
        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_export_backup(self, backup_service):
        """Should export backup to file."""
        with tempfile.NamedTemporaryFile(suffix='.enc', delete=False) as f:
            output_path = f.name

        try:
            result = await backup_service.export_backup(
                output_path=output_path,
                password="testpassword"
            )

            assert result["success"] is True
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @pytest.mark.asyncio
    async def test_import_backup(self, backup_service, mock_db_service):
        """Should import backup from file."""
        # First create a backup
        with tempfile.NamedTemporaryFile(suffix='.enc', delete=False) as f:
            output_path = f.name

        try:
            await backup_service.export_backup(output_path, "testpassword")

            result = await backup_service.import_backup(
                input_path=output_path,
                password="testpassword"
            )

            assert result["success"] is True
            mock_db_service.import_users.assert_called()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_backup_service.py -v --no-cov
```

Expected: FAIL

**Step 3: Create backup service**

Create `backend/src/services/backup_service.py`:

```python
"""
Backup Service

Export and import encrypted backups of all application data.
"""

import json
import os
import hashlib
from datetime import datetime, UTC
from typing import Dict, Any
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import structlog

logger = structlog.get_logger("backup_service")

BACKUP_VERSION = "1.0"
REQUIRED_FIELDS = ["version", "timestamp", "users", "servers", "settings"]


class BackupService:
    """Service for backup and restore operations."""

    def __init__(self, db_service):
        """Initialize backup service."""
        self.db_service = db_service
        logger.info("Backup service initialized")

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _encrypt_data(self, data: Dict[str, Any], password: str) -> bytes:
        """Encrypt backup data with password."""
        # Generate random salt
        salt = os.urandom(16)

        # Derive key from password
        key = self._derive_key(password, salt)
        fernet = Fernet(key)

        # Serialize and encrypt
        json_data = json.dumps(data, indent=2).encode('utf-8')
        encrypted = fernet.encrypt(json_data)

        # Prepend salt to encrypted data
        return salt + encrypted

    def _decrypt_data(self, encrypted: bytes, password: str) -> Dict[str, Any]:
        """Decrypt backup data with password."""
        # Extract salt and encrypted data
        salt = encrypted[:16]
        data = encrypted[16:]

        # Derive key from password
        key = self._derive_key(password, salt)
        fernet = Fernet(key)

        # Decrypt and deserialize
        try:
            decrypted = fernet.decrypt(data)
            return json.loads(decrypted.decode('utf-8'))
        except InvalidToken:
            raise ValueError("Invalid password or corrupted backup")

    def _validate_backup(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate backup data structure."""
        missing = [f for f in REQUIRED_FIELDS if f not in data]
        if missing:
            return {
                "valid": False,
                "error": f"Missing required fields: {', '.join(missing)}"
            }

        # Check version compatibility
        version = data.get("version", "0.0")
        if version > BACKUP_VERSION:
            return {
                "valid": False,
                "error": f"Backup version {version} is newer than supported {BACKUP_VERSION}"
            }

        return {"valid": True}

    async def _collect_backup_data(self) -> Dict[str, Any]:
        """Collect all data for backup."""
        users = await self.db_service.export_users()
        servers = await self.db_service.export_servers()
        settings = await self.db_service.export_settings()

        return {
            "version": BACKUP_VERSION,
            "timestamp": datetime.now(UTC).isoformat(),
            "users": users,
            "servers": servers,
            "settings": settings,
            "app_configs": [],  # Future: installed app configurations
        }

    async def export_backup(
        self,
        output_path: str,
        password: str
    ) -> Dict[str, Any]:
        """Export encrypted backup to file."""
        try:
            # Collect data
            data = await self._collect_backup_data()

            # Encrypt
            encrypted = self._encrypt_data(data, password)

            # Write to file
            with open(output_path, 'wb') as f:
                f.write(encrypted)

            # Calculate checksum
            checksum = hashlib.sha256(encrypted).hexdigest()[:16]

            logger.info("Backup exported", path=output_path, checksum=checksum)
            return {
                "success": True,
                "path": output_path,
                "size": len(encrypted),
                "checksum": checksum,
                "timestamp": data["timestamp"]
            }

        except Exception as e:
            logger.error("Export failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def import_backup(
        self,
        input_path: str,
        password: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """Import backup from encrypted file."""
        try:
            # Read file
            with open(input_path, 'rb') as f:
                encrypted = f.read()

            # Decrypt
            data = self._decrypt_data(encrypted, password)

            # Validate
            validation = self._validate_backup(data)
            if not validation["valid"]:
                return {"success": False, "error": validation["error"]}

            # Import data
            await self.db_service.import_users(data["users"], overwrite=overwrite)
            await self.db_service.import_servers(data["servers"], overwrite=overwrite)
            await self.db_service.import_settings(data["settings"], overwrite=overwrite)

            logger.info("Backup imported", path=input_path, timestamp=data["timestamp"])
            return {
                "success": True,
                "version": data["version"],
                "timestamp": data["timestamp"],
                "users_imported": len(data["users"]),
                "servers_imported": len(data["servers"])
            }

        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error("Import failed", error=str(e))
            return {"success": False, "error": str(e)}
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_backup_service.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/backup_service.py backend/tests/unit/test_backup_service.py
git commit -m "feat(backup): add encrypted backup/restore service"
```

---

## Task 3: Create Backup CLI Commands

**Files:**
- Modify: `backend/src/cli.py`
- Test: `backend/tests/unit/test_backup_cli.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_backup_cli.py`:

```python
"""Tests for backup CLI commands."""
import pytest
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch
from click.testing import CliRunner


class TestBackupCLI:
    """Tests for backup CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def mock_backup_service(self):
        """Create mock backup service."""
        svc = MagicMock()
        svc.export_backup = AsyncMock(return_value={
            "success": True,
            "path": "/tmp/backup.enc",
            "checksum": "abc123"
        })
        svc.import_backup = AsyncMock(return_value={
            "success": True,
            "users_imported": 1,
            "servers_imported": 2
        })
        return svc

    def test_export_command(self, runner, mock_backup_service):
        """Should export backup."""
        from cli import export_backup

        with patch('cli.get_backup_service', return_value=mock_backup_service):
            result = runner.invoke(export_backup, [
                '--output', '/tmp/test.enc',
                '--password', 'testpass'
            ])

        assert result.exit_code == 0 or "success" in result.output.lower()

    def test_import_command(self, runner, mock_backup_service):
        """Should import backup."""
        from cli import import_backup

        # Create a dummy file
        with tempfile.NamedTemporaryFile(suffix='.enc', delete=False) as f:
            f.write(b"dummy")
            temp_path = f.name

        try:
            with patch('cli.get_backup_service', return_value=mock_backup_service):
                result = runner.invoke(import_backup, [
                    '--input', temp_path,
                    '--password', 'testpass'
                ])

            assert result.exit_code == 0 or "success" in result.output.lower()
        finally:
            os.unlink(temp_path)
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_backup_cli.py -v --no-cov
```

Expected: FAIL

**Step 3: Add backup commands to CLI**

Add to `backend/src/cli.py`:

```python
# Add at top of file
import asyncio

# Add these commands after existing CLI commands

@click.command()
@click.option('--output', '-o', required=True, help='Output file path')
@click.option('--password', '-p', prompt=True, hide_input=True,
              confirmation_prompt=True, help='Encryption password')
def export_backup(output: str, password: str):
    """Export encrypted backup of all data."""
    from services.backup_service import BackupService
    from services.database_service import DatabaseService

    db_service = DatabaseService(data_directory=os.getenv('DATA_DIRECTORY', './data'))
    backup_service = BackupService(db_service=db_service)

    async def do_export():
        return await backup_service.export_backup(output, password)

    result = asyncio.run(do_export())

    if result["success"]:
        click.echo(f"Backup exported successfully to {result['path']}")
        click.echo(f"Checksum: {result['checksum']}")
    else:
        click.echo(f"Export failed: {result['error']}", err=True)
        raise SystemExit(1)


@click.command()
@click.option('--input', '-i', 'input_path', required=True, help='Input file path')
@click.option('--password', '-p', prompt=True, hide_input=True, help='Decryption password')
@click.option('--overwrite', is_flag=True, help='Overwrite existing data')
def import_backup(input_path: str, password: str, overwrite: bool):
    """Import backup from encrypted file."""
    from services.backup_service import BackupService
    from services.database_service import DatabaseService

    if not os.path.exists(input_path):
        click.echo(f"File not found: {input_path}", err=True)
        raise SystemExit(1)

    db_service = DatabaseService(data_directory=os.getenv('DATA_DIRECTORY', './data'))
    backup_service = BackupService(db_service=db_service)

    async def do_import():
        return await backup_service.import_backup(input_path, password, overwrite)

    result = asyncio.run(do_import())

    if result["success"]:
        click.echo(f"Backup imported successfully")
        click.echo(f"Users imported: {result['users_imported']}")
        click.echo(f"Servers imported: {result['servers_imported']}")
    else:
        click.echo(f"Import failed: {result['error']}", err=True)
        raise SystemExit(1)


# Add to CLI group
cli.add_command(export_backup, name='export')
cli.add_command(import_backup, name='import')
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_backup_cli.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/cli.py backend/tests/unit/test_backup_cli.py
git commit -m "feat(backup): add export/import CLI commands"
```

---

## Task 4: Create RPM Packaging Files

**Files:**
- Create: `packaging/homelab-assistant.spec`
- Create: `packaging/homelab-assistant.service`
- Create: `packaging/config.yaml.example`
- Create: `packaging/post-install.sh`

**Step 1: Create RPM spec file**

Create `packaging/homelab-assistant.spec`:

```spec
Name:           homelab-assistant
Version:        1.0.0
Release:        1%{?dist}
Summary:        Self-hosted homelab infrastructure management

License:        MIT
URL:            https://github.com/cbabil/homelab
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python3-devel
BuildRequires:  nodejs
Requires:       python3 >= 3.11
Requires:       python3-pip

%description
A self-hosted web application for managing homelab infrastructure.
Connect to remote servers via SSH, deploy Docker applications through
an extensible catalog, and monitor your infrastructure.

%prep
%setup -q

%build
# Build frontend
cd frontend
npm install
npm run build
cd ..

%install
# Create directories
mkdir -p %{buildroot}/opt/homelab-assistant
mkdir -p %{buildroot}/etc/homelab-assistant
mkdir -p %{buildroot}/var/lib/homelab-assistant
mkdir -p %{buildroot}/var/log/homelab-assistant
mkdir -p %{buildroot}%{_unitdir}

# Install backend
cp -r backend/src/* %{buildroot}/opt/homelab-assistant/
cp backend/requirements.txt %{buildroot}/opt/homelab-assistant/

# Install frontend build
cp -r frontend/dist %{buildroot}/opt/homelab-assistant/static

# Install config
cp packaging/config.yaml.example %{buildroot}/etc/homelab-assistant/config.yaml

# Install systemd service
cp packaging/homelab-assistant.service %{buildroot}%{_unitdir}/

%post
# Create user if not exists
getent group homelab >/dev/null || groupadd -r homelab
getent passwd homelab >/dev/null || useradd -r -g homelab -d /var/lib/homelab-assistant -s /sbin/nologin homelab

# Set permissions
chown -R homelab:homelab /var/lib/homelab-assistant
chown -R homelab:homelab /var/log/homelab-assistant
chmod 750 /var/lib/homelab-assistant
chmod 750 /var/log/homelab-assistant

# Install Python dependencies
cd /opt/homelab-assistant && pip3 install -r requirements.txt

# Enable service
systemctl daemon-reload
systemctl enable homelab-assistant

%preun
if [ $1 -eq 0 ]; then
    systemctl stop homelab-assistant
    systemctl disable homelab-assistant
fi

%files
%defattr(-,root,root,-)
/opt/homelab-assistant
%config(noreplace) /etc/homelab-assistant/config.yaml
%{_unitdir}/homelab-assistant.service
%dir %attr(750,homelab,homelab) /var/lib/homelab-assistant
%dir %attr(750,homelab,homelab) /var/log/homelab-assistant

%changelog
* Thu Dec 26 2025 Homelab Team <team@example.com> - 1.0.0-1
- Initial release
```

**Step 2: Create systemd service**

Create `packaging/homelab-assistant.service`:

```ini
[Unit]
Description=Homelab Assistant
Documentation=https://github.com/cbabil/homelab
After=network.target

[Service]
Type=simple
User=homelab
Group=homelab
WorkingDirectory=/opt/homelab-assistant

Environment=DATA_DIRECTORY=/var/lib/homelab-assistant
Environment=LOG_DIRECTORY=/var/log/homelab-assistant
Environment=CONFIG_FILE=/etc/homelab-assistant/config.yaml

ExecStart=/usr/bin/python3 /opt/homelab-assistant/main.py
ExecReload=/bin/kill -HUP $MAINPID

Restart=always
RestartSec=5

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=/var/lib/homelab-assistant /var/log/homelab-assistant

[Install]
WantedBy=multi-user.target
```

**Step 3: Create example config**

Create `packaging/config.yaml.example`:

```yaml
# Homelab Assistant Configuration

# Server settings
server:
  host: 127.0.0.1
  port: 8080

# Database
database:
  path: /var/lib/homelab-assistant/homelab.db

# Logging
logging:
  level: INFO
  format: json
  file: /var/log/homelab-assistant/app.log

# Security
security:
  session_timeout_minutes: 60
  max_login_attempts: 5
  lockout_duration_minutes: 15

# Metrics collection
metrics:
  enabled: true
  collection_interval_seconds: 300
  retention_days: 30

# App catalog
catalog:
  builtin_path: /opt/homelab-assistant/data/catalog
  custom_path: /var/lib/homelab-assistant/catalog
```

**Step 4: Create post-install script**

Create `packaging/post-install.sh`:

```bash
#!/bin/bash
# Post-installation script for homelab-assistant

set -e

# Create homelab user and group
if ! getent group homelab >/dev/null; then
    groupadd -r homelab
    echo "Created homelab group"
fi

if ! getent passwd homelab >/dev/null; then
    useradd -r -g homelab -d /var/lib/homelab-assistant -s /sbin/nologin -c "Homelab Assistant" homelab
    echo "Created homelab user"
fi

# Create directories
mkdir -p /var/lib/homelab-assistant/catalog
mkdir -p /var/log/homelab-assistant

# Set ownership
chown -R homelab:homelab /var/lib/homelab-assistant
chown -R homelab:homelab /var/log/homelab-assistant

# Set permissions
chmod 750 /var/lib/homelab-assistant
chmod 750 /var/log/homelab-assistant

# Initialize database if not exists
if [ ! -f /var/lib/homelab-assistant/homelab.db ]; then
    echo "Initializing database..."
    sudo -u homelab python3 /opt/homelab-assistant/cli.py init-db
fi

# Reload systemd
systemctl daemon-reload

echo "Post-installation complete"
echo ""
echo "To start the service:"
echo "  systemctl start homelab-assistant"
echo ""
echo "To create an admin user:"
echo "  homelab-assistant create-admin"
```

**Step 5: Commit**

```bash
git add packaging/
git commit -m "feat(packaging): add RPM spec and systemd service"
```

---

## Task 5: Add Backup Database Methods

**Files:**
- Modify: `backend/src/services/database_service.py`
- Test: `backend/tests/unit/test_backup_database.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_backup_database.py`:

```python
"""Tests for backup database operations."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager


class TestBackupDatabaseOperations:
    """Tests for backup export/import in database."""

    @pytest.fixture
    def mock_connection(self):
        """Create mock database connection."""
        conn = MagicMock()
        conn.execute = AsyncMock()
        conn.executemany = AsyncMock()
        conn.commit = AsyncMock()
        return conn

    @pytest.fixture
    def db_service(self, mock_connection):
        """Create database service with mocked connection."""
        from services.database_service import DatabaseService

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_connection

        with patch.object(DatabaseService, 'get_connection', mock_get_connection):
            service = DatabaseService(data_directory="/tmp/test")
            service._mock_conn = mock_connection
            return service

    @pytest.mark.asyncio
    async def test_export_users(self, db_service, mock_connection):
        """Should export all users."""
        mock_rows = [
            {"id": "u1", "username": "admin", "email": "admin@test.com",
             "role": "admin", "is_active": 1, "created_at": "2025-01-01"}
        ]
        mock_connection.execute.return_value = MagicMock(
            fetchall=AsyncMock(return_value=mock_rows)
        )

        result = await db_service.export_users()

        assert len(result) == 1
        assert result[0]["username"] == "admin"

    @pytest.mark.asyncio
    async def test_export_servers(self, db_service, mock_connection):
        """Should export all servers."""
        mock_rows = [
            {"id": "s1", "name": "server1", "host": "192.168.1.1",
             "port": 22, "username": "root", "auth_type": "password"}
        ]
        mock_connection.execute.return_value = MagicMock(
            fetchall=AsyncMock(return_value=mock_rows)
        )

        result = await db_service.export_servers()

        assert len(result) == 1
        assert result[0]["name"] == "server1"

    @pytest.mark.asyncio
    async def test_import_users(self, db_service, mock_connection):
        """Should import users."""
        users = [
            {"id": "u1", "username": "admin", "email": "admin@test.com"}
        ]

        await db_service.import_users(users, overwrite=True)

        mock_connection.execute.assert_called()

    @pytest.mark.asyncio
    async def test_import_servers(self, db_service, mock_connection):
        """Should import servers."""
        servers = [
            {"id": "s1", "name": "server1", "host": "192.168.1.1"}
        ]

        await db_service.import_servers(servers, overwrite=True)

        mock_connection.execute.assert_called()
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_backup_database.py -v --no-cov
```

Expected: FAIL

**Step 3: Add backup methods to database_service.py**

Add to `backend/src/services/database_service.py`:

```python
async def export_users(self) -> list:
    """Export all users for backup."""
    try:
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT id, username, email, role, is_active, created_at FROM users"
            )
            rows = await cursor.fetchall()

        return [dict(row) for row in rows]
    except Exception as e:
        logger.error("Failed to export users", error=str(e))
        return []

async def export_servers(self) -> list:
    """Export all servers for backup (including encrypted credentials)."""
    try:
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM servers"
            )
            rows = await cursor.fetchall()

        return [dict(row) for row in rows]
    except Exception as e:
        logger.error("Failed to export servers", error=str(e))
        return []

async def export_settings(self) -> dict:
    """Export settings for backup."""
    try:
        async with self.get_connection() as conn:
            cursor = await conn.execute("SELECT key, value FROM settings")
            rows = await cursor.fetchall()

        return {row["key"]: row["value"] for row in rows}
    except Exception as e:
        logger.error("Failed to export settings", error=str(e))
        return {}

async def import_users(self, users: list, overwrite: bool = False) -> None:
    """Import users from backup."""
    try:
        async with self.get_connection() as conn:
            for user in users:
                if overwrite:
                    await conn.execute(
                        "DELETE FROM users WHERE id = ?", (user["id"],)
                    )
                await conn.execute(
                    """INSERT OR IGNORE INTO users
                       (id, username, email, role, is_active, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (user["id"], user["username"], user.get("email"),
                     user.get("role", "user"), user.get("is_active", 1),
                     user.get("created_at"))
                )
            await conn.commit()
        logger.info("Imported users", count=len(users))
    except Exception as e:
        logger.error("Failed to import users", error=str(e))
        raise

async def import_servers(self, servers: list, overwrite: bool = False) -> None:
    """Import servers from backup."""
    try:
        async with self.get_connection() as conn:
            for server in servers:
                if overwrite:
                    await conn.execute(
                        "DELETE FROM servers WHERE id = ?", (server["id"],)
                    )
                await conn.execute(
                    """INSERT OR IGNORE INTO servers
                       (id, name, host, port, username, auth_type, credentials, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (server["id"], server["name"], server["host"],
                     server.get("port", 22), server.get("username"),
                     server.get("auth_type"), server.get("credentials"),
                     server.get("status", "unknown"))
                )
            await conn.commit()
        logger.info("Imported servers", count=len(servers))
    except Exception as e:
        logger.error("Failed to import servers", error=str(e))
        raise

async def import_settings(self, settings: dict, overwrite: bool = False) -> None:
    """Import settings from backup."""
    try:
        async with self.get_connection() as conn:
            for key, value in settings.items():
                if overwrite:
                    await conn.execute(
                        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                        (key, value)
                    )
                else:
                    await conn.execute(
                        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                        (key, value)
                    )
            await conn.commit()
        logger.info("Imported settings", count=len(settings))
    except Exception as e:
        logger.error("Failed to import settings", error=str(e))
        raise
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_backup_database.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/database_service.py backend/tests/unit/test_backup_database.py
git commit -m "feat(backup): add database export/import methods"
```

---

## Task 6: Create Backup MCP Tools

**Files:**
- Create: `backend/src/tools/backup_tools.py`
- Test: `backend/tests/unit/test_backup_tools.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_backup_tools.py`:

```python
"""Tests for backup MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from tools.backup_tools import BackupTools


@pytest.fixture
def mock_backup_service():
    """Create mock backup service."""
    svc = MagicMock()
    svc.export_backup = AsyncMock(return_value={
        "success": True,
        "path": "/tmp/backup.enc",
        "checksum": "abc123"
    })
    svc.import_backup = AsyncMock(return_value={
        "success": True,
        "users_imported": 1,
        "servers_imported": 2
    })
    return svc


@pytest.fixture
def backup_tools(mock_backup_service):
    """Create backup tools with mocks."""
    return BackupTools(backup_service=mock_backup_service)


class TestExportBackup:
    """Tests for export_backup tool."""

    @pytest.mark.asyncio
    async def test_export_success(self, backup_tools, mock_backup_service):
        """Should export backup successfully."""
        result = await backup_tools.export_backup(
            output_path="/tmp/backup.enc",
            password="testpass"
        )

        assert result["success"] is True
        assert "path" in result["data"]

    @pytest.mark.asyncio
    async def test_export_failure(self, backup_tools, mock_backup_service):
        """Should handle export failure."""
        mock_backup_service.export_backup.return_value = {
            "success": False,
            "error": "Disk full"
        }

        result = await backup_tools.export_backup(
            output_path="/tmp/backup.enc",
            password="testpass"
        )

        assert result["success"] is False


class TestImportBackup:
    """Tests for import_backup tool."""

    @pytest.mark.asyncio
    async def test_import_success(self, backup_tools, mock_backup_service):
        """Should import backup successfully."""
        result = await backup_tools.import_backup(
            input_path="/tmp/backup.enc",
            password="testpass"
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_import_wrong_password(self, backup_tools, mock_backup_service):
        """Should handle wrong password."""
        mock_backup_service.import_backup.return_value = {
            "success": False,
            "error": "Invalid password"
        }

        result = await backup_tools.import_backup(
            input_path="/tmp/backup.enc",
            password="wrongpass"
        )

        assert result["success"] is False
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_backup_tools.py -v --no-cov
```

Expected: FAIL

**Step 3: Create backup tools**

Create `backend/src/tools/backup_tools.py`:

```python
"""
Backup MCP Tools

Provides MCP tools for backup and restore operations.
"""

from typing import Dict, Any
import structlog
from fastmcp import FastMCP
from services.backup_service import BackupService

logger = structlog.get_logger("backup_tools")


class BackupTools:
    """Backup tools for the MCP server."""

    def __init__(self, backup_service: BackupService):
        """Initialize backup tools."""
        self.backup_service = backup_service
        logger.info("Backup tools initialized")

    async def export_backup(
        self,
        output_path: str,
        password: str
    ) -> Dict[str, Any]:
        """Export encrypted backup to file."""
        try:
            result = await self.backup_service.export_backup(output_path, password)

            if result["success"]:
                return {
                    "success": True,
                    "data": {
                        "path": result["path"],
                        "checksum": result["checksum"],
                        "size": result["size"],
                        "timestamp": result["timestamp"]
                    },
                    "message": "Backup exported successfully"
                }
            else:
                return {
                    "success": False,
                    "message": result["error"],
                    "error": "EXPORT_FAILED"
                }

        except Exception as e:
            logger.error("Export backup error", error=str(e))
            return {
                "success": False,
                "message": f"Export failed: {str(e)}",
                "error": "EXPORT_ERROR"
            }

    async def import_backup(
        self,
        input_path: str,
        password: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """Import backup from encrypted file."""
        try:
            result = await self.backup_service.import_backup(
                input_path, password, overwrite
            )

            if result["success"]:
                return {
                    "success": True,
                    "data": {
                        "version": result["version"],
                        "timestamp": result["timestamp"],
                        "users_imported": result["users_imported"],
                        "servers_imported": result["servers_imported"]
                    },
                    "message": "Backup imported successfully"
                }
            else:
                return {
                    "success": False,
                    "message": result["error"],
                    "error": "IMPORT_FAILED"
                }

        except Exception as e:
            logger.error("Import backup error", error=str(e))
            return {
                "success": False,
                "message": f"Import failed: {str(e)}",
                "error": "IMPORT_ERROR"
            }


def register_backup_tools(app: FastMCP, backup_service: BackupService):
    """Register backup tools with FastMCP app."""
    tools = BackupTools(backup_service)

    app.tool(tools.export_backup)
    app.tool(tools.import_backup)

    logger.info("Backup tools registered")
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_backup_tools.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/tools/backup_tools.py backend/tests/unit/test_backup_tools.py
git commit -m "feat(backup): add backup MCP tools"
```

---

## Task 7: Verify All Phase 6 Tests Pass

**Step 1: Run all Phase 6 tests**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_security.py tests/unit/test_backup*.py -v --no-cov
```

**Step 2: Run all project tests to ensure no regressions**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/ -v --no-cov
```

**Step 3: Commit if any fixes needed**

```bash
git add .
git commit -m "fix(phase6): fix test failures"
```

---

## Quality Gates Checklist

- [ ] Input validation prevents shell injection
- [ ] Rate limiting works on auth endpoints
- [ ] Constant-time comparison prevents timing attacks
- [ ] Log sanitization removes sensitive data
- [ ] Backup encryption is secure (PBKDF2 + Fernet)
- [ ] Backup/restore round-trip works
- [ ] RPM spec file is valid
- [ ] Systemd service starts correctly
- [ ] All unit tests pass

---

## Definition of Done

The application is production-ready with:
1. Security hardening (input validation, rate limiting)
2. Encrypted backup/restore functionality
3. RPM packaging for RHEL/Rocky/Fedora
4. Systemd service integration

---

**Document Version:** 1.0
**Created:** 2025-12-26

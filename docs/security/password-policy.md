# Password Policy

This document describes the password policy feature in Tomo Management, including configurable requirements and password expiration.

## Overview

The password policy feature provides:
- Configurable password complexity requirements
- Password expiration enforcement
- Password change tracking per user

## Configuration

Password policy settings are stored in the `system_settings` table and can be managed via:
- **Settings UI**: Settings > Security > Password Policy
- **MCP Tools**: `get_settings` and `update_settings`

### Available Settings

| Setting Key | Default | Description |
|-------------|---------|-------------|
| `security.password_min_length` | 8 | Minimum password length (6-32) |
| `security.password_require_uppercase` | true | Require at least one uppercase letter |
| `security.password_require_numbers` | true | Require at least one number |
| `security.password_require_special_chars` | true | Require at least one special character |
| `security.force_password_change_days` | 90 | Days before password expires (0 = never) |

### Expiration Options

- **Never** (0 days)
- **30 days**
- **60 days**
- **90 days** (default)
- **180 days**
- **1 year** (365 days)

## Database Schema

### Users Table

The `users` table includes a `password_changed_at` column to track when each user last changed their password:

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT DEFAULT '',
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_login TEXT,
    password_changed_at TEXT DEFAULT (datetime('now')),
    is_active INTEGER NOT NULL DEFAULT 1,
    preferences_json TEXT DEFAULT '{}',
    avatar TEXT DEFAULT NULL
);
```

### Migration

For existing databases, a migration automatically:
1. Adds the `password_changed_at` column if missing
2. Sets existing users' `password_changed_at` to their `created_at` value

## API

### Database Service Methods

#### `update_user_password(username: str, password_hash: str) -> bool`

Updates a user's password and sets the `password_changed_at` timestamp:

```python
from services.database_service import DatabaseService
from lib.auth_helpers import hash_password

db_service = DatabaseService()
new_hash = hash_password("NewSecurePassword123!")
success = await db_service.update_user_password("admin", new_hash)
```

### MCP Tools

#### Get Password Policy Settings

```json
{
  "tool": "get_settings",
  "params": {
    "user_id": "admin",
    "setting_keys": [
      "security.password_min_length",
      "security.password_require_uppercase",
      "security.password_require_numbers",
      "security.password_require_special_chars",
      "security.force_password_change_days"
    ]
  }
}
```

#### Update Password Policy Settings

```json
{
  "tool": "update_settings",
  "params": {
    "user_id": "admin",
    "settings": {
      "security.password_min_length": 12,
      "security.password_require_special_chars": true,
      "security.force_password_change_days": 60
    },
    "change_reason": "Updated password policy"
  }
}
```

## Frontend Components

### SecuritySettings Component

Located at: `frontend/src/pages/settings/SecuritySettings.tsx`

Provides a UI for managing:
- **Account Locking**: Max login attempts, lockout duration
- **Password Policy**: Min length, complexity requirements, expiration

### Toggle Component

Used for boolean settings (require uppercase, numbers, special chars):

```tsx
import { Toggle } from './components'

<Toggle
  checked={settings.passwordRequireUppercase}
  onChange={(checked) => updateSetting('passwordRequireUppercase', checked)}
/>
```

## Password Expiration Flow

1. User logs in
2. System checks `password_changed_at` against `force_password_change_days`
3. If expired:
   - User is prompted to change password
   - Cannot access protected resources until password is changed
4. After password change:
   - `password_changed_at` is updated to current timestamp
   - User can continue normally

## Security Considerations

- Password hashes use bcrypt with automatic salt
- Policy settings are admin-only (`is_admin_only = 1`)
- All changes are logged to the settings audit table
- Failed password changes do not reveal whether username exists

## Testing

Unit tests are located at:
- `backend/src/tests/unit/services/test_password_management.py`

Run tests:
```bash
cd backend
pytest src/tests/unit/services/test_password_management.py -v
```

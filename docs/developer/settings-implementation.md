# Settings Database Implementation Guide

## Backend Service Integration Patterns

### 1. Settings Service (`services/settings_service.py`)

Create a new service following the existing `database_service.py` patterns:

```python
"""
Settings Service for Comprehensive Settings Management

Provides async database operations for system and user settings management.
Handles settings hierarchy, validation, and migration with structured logging.
"""

import json
import sqlite3
import aiosqlite
import structlog
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from models.settings import UserSettings, SystemSettings, SettingsValidation
from contextlib import asynccontextmanager

logger = structlog.get_logger("settings_service")

class SettingsService:
    """Async service for settings management operations."""

    def __init__(self, db_path: str | Path | None = None):
        """Initialize settings service with database path."""
        self.db_path = db_path
        logger.info("Settings service initialized", db_path=self.db_path)

    @asynccontextmanager
    async def get_connection(self):
        """Get async database connection with automatic cleanup."""
        async with aiosqlite.connect(self.db_path) as connection:
            connection.row_factory = aiosqlite.Row
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    async def get_effective_user_settings(self, user_id: str) -> Optional[UserSettings]:
        """
        Get effective settings for user (user overrides + system defaults + app defaults).

        Priority order:
        1. User settings (user_settings table)
        2. System settings (system_settings table)
        3. Application defaults (DEFAULT_SETTINGS)
        """
        try:
            async with self.get_connection() as conn:
                # Get user-specific overrides
                user_cursor = await conn.execute("""
                    SELECT setting_key, setting_value, category
                    FROM user_settings
                    WHERE user_id = ?
                """, (user_id,))
                user_settings = {row['setting_key']: json.loads(row['setting_value'])
                                for row in await user_cursor.fetchall()}

                # Get system defaults for keys not overridden by user
                system_cursor = await conn.execute("""
                    SELECT setting_key, setting_value, category
                    FROM system_settings
                    WHERE scope = 'user_overridable'
                """)
                system_settings = {row['setting_key']: json.loads(row['setting_value'])
                                  for row in await system_cursor.fetchall()}

                # Build effective settings hierarchy
                effective_settings = self._build_settings_hierarchy(
                    user_settings, system_settings
                )

                logger.debug("Retrieved effective user settings",
                           user_id=user_id, settings_count=len(effective_settings))
                return effective_settings

        except Exception as e:
            logger.error("Failed to get effective user settings", user_id=user_id, error=str(e))
            return None

    async def update_user_setting(self, user_id: str, setting_key: str,
                                 setting_value: Any, category: str) -> bool:
        """Update a single user setting with validation and audit logging."""
        try:
            async with self.get_connection() as conn:
                await conn.execute("BEGIN IMMEDIATE")

                try:
                    # Validate setting is user-modifiable
                    if not await self._is_user_modifiable_setting(conn, setting_key):
                        logger.warning("Attempted to modify admin-only setting",
                                     user_id=user_id, setting_key=setting_key)
                        return False

                    # Validate setting value
                    if not await self._validate_setting_value(conn, setting_key, setting_value):
                        logger.warning("Invalid setting value",
                                     user_id=user_id, setting_key=setting_key)
                        return False

                    # Insert or update user setting
                    await conn.execute("""
                        INSERT INTO user_settings (user_id, setting_key, setting_value, category)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(user_id, setting_key) DO UPDATE SET
                            setting_value = excluded.setting_value,
                            updated_at = datetime('now'),
                            version = version + 1
                    """, (user_id, setting_key, json.dumps(setting_value), category))

                    await conn.commit()

                    logger.info("Updated user setting",
                              user_id=user_id, setting_key=setting_key)
                    return True

                except Exception as e:
                    await conn.rollback()
                    raise

        except Exception as e:
            logger.error("Failed to update user setting",
                        user_id=user_id, setting_key=setting_key, error=str(e))
            return False

    async def get_system_settings(self, admin_user_id: str) -> Optional[Dict[str, Any]]:
        """Get all system settings (admin only)."""
        try:
            # Verify admin permissions
            if not await self._verify_admin_permissions(admin_user_id):
                logger.warning("Non-admin attempted to access system settings",
                             user_id=admin_user_id)
                return None

            async with self.get_connection() as conn:
                cursor = await conn.execute("""
                    SELECT setting_key, setting_value, category, description, is_admin_only
                    FROM system_settings
                    ORDER BY category, setting_key
                """)

                settings = {}
                for row in await cursor.fetchall():
                    settings[row['setting_key']] = {
                        'value': json.loads(row['setting_value']),
                        'category': row['category'],
                        'description': row['description'],
                        'admin_only': bool(row['is_admin_only'])
                    }

                logger.debug("Retrieved system settings",
                           admin_user_id=admin_user_id, count=len(settings))
                return settings

        except Exception as e:
            logger.error("Failed to get system settings",
                        admin_user_id=admin_user_id, error=str(e))
            return None

    async def update_system_setting(self, admin_user_id: str, setting_key: str,
                                   setting_value: Any) -> bool:
        """Update system setting (admin only)."""
        try:
            # Verify admin permissions
            if not await self._verify_admin_permissions(admin_user_id):
                logger.warning("Non-admin attempted to modify system settings",
                             user_id=admin_user_id)
                return False

            async with self.get_connection() as conn:
                await conn.execute("BEGIN IMMEDIATE")

                try:
                    # Validate setting value against schema
                    if not await self._validate_system_setting_value(conn, setting_key, setting_value):
                        return False

                    # Update system setting
                    await conn.execute("""
                        UPDATE system_settings
                        SET setting_value = ?, updated_at = datetime('now'),
                            updated_by = ?, version = version + 1
                        WHERE setting_key = ?
                    """, (json.dumps(setting_value), admin_user_id, setting_key))

                    if conn.total_changes == 0:
                        logger.warning("System setting not found", setting_key=setting_key)
                        return False

                    await conn.commit()

                    logger.info("Updated system setting",
                              admin_user_id=admin_user_id, setting_key=setting_key)
                    return True

                except Exception as e:
                    await conn.rollback()
                    raise

        except Exception as e:
            logger.error("Failed to update system setting",
                        admin_user_id=admin_user_id, setting_key=setting_key, error=str(e))
            return False

    # Helper methods would continue here...
    # (abbreviated for space - full implementation would include all helper methods)
```

### 2. MCP Tools (`tools/settings_tools.py`)

Following the pattern from `retention_tools.py`:

```python
"""
Settings MCP Tools

Provides MCP tools for settings management with comprehensive security controls,
user/admin access verification, and validation.
"""

from typing import Dict, Any, Optional
import structlog
from fastmcp import FastMCP, Context
from services.settings_service import SettingsService

logger = structlog.get_logger("settings_tools")

class SettingsTools:
    """MCP tools for settings management."""

    def __init__(self, settings_service: SettingsService):
        """Initialize settings tools with service dependency."""
        self.settings_service = settings_service
        logger.info("Settings tools initialized")

    async def get_user_settings(self, user_id: str = None, ctx: Context = None) -> Dict[str, Any]:
        """Get effective settings for user."""
        try:
            logger.info("Getting user settings", user_id=user_id)

            if not user_id:
                return {
                    "success": False,
                    "message": "User ID is required",
                    "error": "MISSING_USER_ID"
                }

            settings = await self.settings_service.get_effective_user_settings(user_id)
            if settings is None:
                return {
                    "success": False,
                    "message": "Failed to retrieve user settings",
                    "error": "SETTINGS_RETRIEVAL_ERROR"
                }

            return {
                "success": True,
                "data": settings.model_dump(),
                "message": "User settings retrieved successfully"
            }

        except Exception as e:
            logger.error("Failed to get user settings", user_id=user_id, error=str(e))
            return {
                "success": False,
                "message": f"Failed to get user settings: {str(e)}",
                "error": "GET_SETTINGS_ERROR"
            }

    async def update_user_settings(self, user_id: str = None,
                                  settings_data: Dict[str, Any] = None,
                                  ctx: Context = None) -> Dict[str, Any]:
        """Update user settings with validation."""
        # Implementation following retention_tools pattern...

    async def get_system_settings(self, admin_user_id: str = None,
                                 ctx: Context = None) -> Dict[str, Any]:
        """Get system settings (admin only)."""
        # Implementation following retention_tools pattern...

    async def update_system_settings(self, admin_user_id: str = None,
                                    settings_data: Dict[str, Any] = None,
                                    ctx: Context = None) -> Dict[str, Any]:
        """Update system settings (admin only)."""
        # Implementation following retention_tools pattern...

def register_settings_tools(app: FastMCP, settings_service: SettingsService):
    """Register settings tools with FastMCP app."""
    settings_tools = SettingsTools(settings_service)

    # Register each tool method
    app.tool(settings_tools.get_user_settings)
    app.tool(settings_tools.update_user_settings)
    app.tool(settings_tools.get_system_settings)
    app.tool(settings_tools.update_system_settings)

    logger.info("Settings tools registered with MCP app")
```

### 3. Backend Models (`models/settings.py`)

Create Pydantic models for type safety:

```python
"""
Settings Models

Pydantic models for settings data structures, validation, and serialization.
Ensures type safety and validation across the settings system.
"""

from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

class SettingScope(str, Enum):
    SYSTEM = "system"
    USER_OVERRIDABLE = "user_overridable"

class SettingCategory(str, Enum):
    UI = "ui"
    SECURITY = "security"
    SYSTEM = "system"
    RETENTION = "retention"

class SystemSetting(BaseModel):
    id: Optional[int] = None
    setting_key: str
    setting_value: Any
    category: SettingCategory
    scope: SettingScope = SettingScope.SYSTEM
    data_type: str
    is_admin_only: bool = True
    description: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    version: int = 1

class UserSetting(BaseModel):
    id: Optional[int] = None
    user_id: str
    setting_key: str
    setting_value: Any
    category: SettingCategory
    is_override: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: int = 1

class EffectiveSettings(BaseModel):
    """Computed effective settings for a user."""
    user_id: str
    security: Dict[str, Any]
    ui: Dict[str, Any]
    system: Dict[str, Any]
    retention: Dict[str, Any]
    computed_at: datetime
    version: int
```

## Frontend Integration Patterns

### 1. Enhanced Settings Service

Update `frontend/src/services/settingsService.ts`:

```typescript
/**
 * Enhanced Settings Service with Database Backend
 *
 * Provides settings management with database persistence, local caching,
 * and backward compatibility with localStorage.
 */

import { UserSettings, DEFAULT_SETTINGS } from '@/types/settings'
import { mcpClient } from '@/services/mcpClient'

class DatabaseSettingsService {
    private settings: UserSettings | null = null
    private listeners: Set<(settings: UserSettings) => void> = new Set()
    private isInitialized = false
    private userId: string | null = null

    async initialize(userId: string): Promise<UserSettings> {
        this.userId = userId

        try {
            // Try to load from database first
            const dbSettings = await this.loadFromDatabase()

            if (dbSettings) {
                this.settings = dbSettings
                await this.syncToLocalStorage() // Backup to localStorage
                this.isInitialized = true
                return dbSettings
            }

            // Fallback to localStorage migration
            const migratedSettings = await this.migrateFromLocalStorage()
            this.settings = migratedSettings
            this.isInitialized = true
            return migratedSettings

        } catch (error) {
            console.error('Settings initialization failed:', error)
            // Ultimate fallback to defaults
            this.settings = { ...DEFAULT_SETTINGS }
            this.isInitialized = true
            return this.settings
        }
    }

    private async loadFromDatabase(): Promise<UserSettings | null> {
        if (!this.userId) return null

        try {
            const response = await mcpClient.callTool('get_user_settings', {
                user_id: this.userId
            })

            if (response.success && response.data) {
                return this.validateAndMigrateSettings(response.data)
            }

            return null
        } catch (error) {
            console.error('Failed to load settings from database:', error)
            return null
        }
    }

    async updateSettings(
        section: keyof Omit<UserSettings, 'lastUpdated' | 'version'>,
        updates: Partial<UserSettings[typeof section]>
    ): Promise<{ success: boolean; error?: string }> {
        if (!this.isInitialized || !this.userId) {
            return { success: false, error: 'Settings service not initialized' }
        }

        try {
            const newSettings = {
                ...this.settings!,
                [section]: { ...this.settings![section], ...updates },
                lastUpdated: new Date().toISOString(),
                version: this.settings!.version + 1
            }

            // Save to database
            const response = await mcpClient.callTool('update_user_settings', {
                user_id: this.userId,
                settings_data: this.convertToDbFormat(newSettings)
            })

            if (response.success) {
                this.settings = newSettings
                await this.syncToLocalStorage() // Keep localStorage in sync
                this.notifyListeners(newSettings)
                return { success: true }
            } else {
                return { success: false, error: response.message }
            }

        } catch (error) {
            console.error('Failed to update settings:', error)
            return { success: false, error: 'Failed to save settings' }
        }
    }

    private convertToDbFormat(settings: UserSettings): Record<string, any> {
        // Convert TypeScript settings to database key-value format
        return {
            'ui.theme': settings.ui.theme,
            'ui.language': settings.ui.language,
            'ui.notifications': settings.ui.notifications,
            'security.session.timeout': settings.security.session.timeout,
            'system.auto_refresh': settings.system.autoRefresh,
            // ... continue for all settings
        }
    }

    private async migrateFromLocalStorage(): Promise<UserSettings> {
        // Legacy migration logic
        const stored = localStorage.getItem('tomo-user-settings')
        if (stored && this.userId) {
            try {
                const parsed = JSON.parse(stored)
                // Save to database for future use
                await this.saveToDatabase(parsed)
                return parsed
            } catch (error) {
                console.error('Failed to migrate from localStorage:', error)
            }
        }
        return { ...DEFAULT_SETTINGS }
    }

    // Additional methods for caching, validation, etc.
}
```

### 2. Settings Hook Integration

Update settings hooks to use new service:

```typescript
// hooks/useSettings.ts
export function useSettings() {
    const { user } = useAuth()
    const [settings, setSettings] = useState<UserSettings | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (user?.id) {
            settingsService.initialize(user.id)
                .then(setSettings)
                .catch(setError)
                .finally(() => setLoading(false))
        }
    }, [user?.id])

    const updateSetting = useCallback(async (section, updates) => {
        const result = await settingsService.updateSettings(section, updates)
        if (!result.success) {
            setError(result.error)
        }
        return result
    }, [])

    return { settings, loading, error, updateSetting }
}
```

## Installation and Upgrade Procedures

### For New Installations

1. **Database Creation**: Run `init_database.py` (existing) to create base structure
2. **Settings Schema**: Run `init_settings_database.py` to add settings tables
3. **Verification**: Use built-in verification to ensure proper setup

```bash
# Complete new installation
cd backend
python init_database.py          # Create base database
python init_settings_database.py # Add settings system
python -c "from init_settings_database import SettingsDatabaseManager; print(SettingsDatabaseManager().verify_installation())"
```

### For Existing Installations

1. **Backup**: Automatic backup creation before migration
2. **Migration**: Run settings migration script
3. **Verification**: Validate successful migration

```bash
# Upgrade existing installation
cd backend
python init_settings_database.py # Automatically detects existing DB and migrates
```

### Integration with Existing Codebase

#### 1. Update Main Application (`main.py`)

```python
# Add settings service initialization
from services.settings_service import SettingsService
from tools.settings_tools import register_settings_tools

# Initialize settings service
settings_service = SettingsService()

# Register MCP tools
register_settings_tools(app, settings_service)
```

#### 2. Update Frontend App Initialization

```typescript
// src/App.tsx or main initialization
import { settingsService } from '@/services/settingsService'

// Initialize settings service after authentication
useEffect(() => {
    if (user) {
        settingsService.initialize(user.id)
    }
}, [user])
```

## Security Considerations

### 1. Access Control Matrix

| Setting Type | Admin Read | Admin Write | User Read | User Write |
|-------------|------------|-------------|-----------|------------|
| System Settings (admin-only) | ✅ | ✅ | ❌ | ❌ |
| System Settings (user-overridable) | ✅ | ✅ | ✅ | ❌ |
| User Settings | ✅ | ✅ | ✅* | ✅* |

*Users can only access their own settings

### 2. Validation Strategy

- **Schema Validation**: JSON schema validation for all setting values
- **Range Validation**: Numeric constraints (min/max values)
- **Permission Validation**: Verify user can modify specific settings
- **Cross-Setting Validation**: Ensure setting combinations are valid

### 3. Audit Requirements

- **All Changes**: Complete audit trail for all setting modifications
- **User Context**: Track user, IP, and timestamp for all changes
- **Rollback Capability**: Ability to restore previous values
- **Compliance**: Meet audit requirements for sensitive settings

This implementation guide provides a comprehensive foundation for integrating the settings database system with your existing tomo application architecture.

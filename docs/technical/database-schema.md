# Database Schema Design for Settings Management

## Architectural Analysis

### Current System
- **Database**: SQLite with `users` table containing `preferences_json` field
- **Frontend**: Settings managed via `settingsService.ts` with localStorage
- **Backend**: Async patterns, structured logging, MCP tool architecture
- **Types**: Comprehensive TypeScript settings structure with validation

### Design Decisions

#### 1. Schema Architecture: Hybrid Approach
**Decision**: Use both normalized columns and JSON storage
**Rationale**:
- Maintains flexibility for settings evolution
- Enables efficient querying on key fields
- Follows existing JSON pattern in `users.preferences_json`
- Supports both global and user-specific settings

#### 2. Settings Scope: Two-Tier System
**Decision**: Global system settings + user-specific overrides
**Rationale**:
- Admin can set system defaults
- Users can override specific preferences
- Maintains security boundaries (admin-only vs user-editable)

#### 3. Storage Strategy: JSON with Metadata
**Decision**: JSON settings with versioning and audit metadata
**Rationale**:
- Schema evolution support
- Audit trail for compliance
- Backward compatibility
- Performance optimization for common queries

## Database Schema Design

### New Tables

#### 1. `system_settings` Table
Global configuration settings managed by administrators.

```sql
CREATE TABLE system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT UNIQUE NOT NULL,           -- e.g., 'ui.theme_default', 'security.session_timeout'
    setting_value TEXT NOT NULL,               -- JSON value
    category TEXT NOT NULL,                    -- 'ui', 'security', 'system', 'retention'
    scope TEXT NOT NULL DEFAULT 'system',     -- 'system', 'user_overridable'
    data_type TEXT NOT NULL,                  -- 'string', 'number', 'boolean', 'object'
    is_admin_only BOOLEAN NOT NULL DEFAULT 1, -- Admin-only settings
    description TEXT,                         -- Human-readable description
    validation_rules TEXT,                    -- JSON schema for validation
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT,                          -- User ID who made the change
    version INTEGER NOT NULL DEFAULT 1
);

-- Indexes for efficient querying
CREATE INDEX idx_system_settings_key ON system_settings (setting_key);
CREATE INDEX idx_system_settings_category ON system_settings (category);
CREATE INDEX idx_system_settings_scope ON system_settings (scope);
CREATE INDEX idx_system_settings_admin_only ON system_settings (is_admin_only);
CREATE INDEX idx_system_settings_updated_at ON system_settings (updated_at);
```

#### 2. `user_settings` Table
User-specific setting overrides and preferences.

```sql
CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,                    -- References users.id
    setting_key TEXT NOT NULL,               -- Same keys as system_settings
    setting_value TEXT NOT NULL,             -- JSON value (user's override)
    category TEXT NOT NULL,                  -- 'ui', 'security', 'system', 'retention'
    is_override BOOLEAN NOT NULL DEFAULT 1,  -- Is this overriding a system setting?
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,

    UNIQUE(user_id, setting_key),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Indexes for efficient user setting queries
CREATE INDEX idx_user_settings_user_id ON user_settings (user_id);
CREATE INDEX idx_user_settings_key ON user_settings (setting_key);
CREATE INDEX idx_user_settings_category ON user_settings (category, user_id);
CREATE INDEX idx_user_settings_updated_at ON user_settings (updated_at);
```

#### 3. `settings_audit` Table
Comprehensive audit trail for all settings changes.

```sql
CREATE TABLE settings_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,                -- 'system_settings' or 'user_settings'
    record_id INTEGER NOT NULL,             -- ID from the settings table
    user_id TEXT,                           -- User who made the change (NULL for system)
    setting_key TEXT NOT NULL,             -- The setting that changed
    old_value TEXT,                        -- Previous JSON value
    new_value TEXT NOT NULL,               -- New JSON value
    change_type TEXT NOT NULL,             -- 'CREATE', 'UPDATE', 'DELETE'
    change_reason TEXT,                    -- Optional reason for the change
    client_ip TEXT,                        -- IP address of client
    user_agent TEXT,                       -- User agent string
    created_at TEXT NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);

-- Indexes for audit queries
CREATE INDEX idx_settings_audit_table_record ON settings_audit (table_name, record_id);
CREATE INDEX idx_settings_audit_user_id ON settings_audit (user_id);
CREATE INDEX idx_settings_audit_setting_key ON settings_audit (setting_key);
CREATE INDEX idx_settings_audit_created_at ON settings_audit (created_at);
CREATE INDEX idx_settings_audit_change_type ON settings_audit (change_type);
```

### Enhanced Existing Tables

#### Modified `users` Table
Leverage existing `preferences_json` field for backward compatibility.

```sql
-- No structural changes needed to users table
-- preferences_json will continue to store legacy preferences
-- New settings system will gradually migrate data
```

## Settings Hierarchy

### Priority Order (Highest to Lowest)
1. **User Override Settings** (`user_settings` table)
2. **System Default Settings** (`system_settings` table)
3. **Application Defaults** (TypeScript `DEFAULT_SETTINGS`)
4. **Legacy User Preferences** (`users.preferences_json` - backward compatibility)

### Setting Categories

#### 1. UI Settings (`ui` category)
- `ui.theme_default` - System default theme
- `ui.language_default` - Default language
- `ui.compact_mode_enabled` - Allow compact mode
- `ui.sidebar_collapsed_default` - Default sidebar state

#### 2. Security Settings (`security` category)
- `security.session_timeout_default` - Default session timeout
- `security.idle_detection_enabled` - Enable idle detection
- `security.password_change_required` - Force password changes
- `security.two_factor_enabled` - System 2FA requirement

#### 3. System Settings (`system` category)
- `system.auto_refresh_default` - Default auto-refresh setting
- `system.max_log_entries` - Maximum log entries to display
- `system.debug_mode_enabled` - Enable debug features

#### 4. Data Retention Settings (`retention` category)
- `retention.log_retention_days_default` - Default log retention
- `retention.cleanup_enabled` - Enable automatic cleanup
- `retention.cleanup_schedule` - Cleanup schedule configuration

## Integration Architecture

### Backend Integration

#### 1. Settings Service (`services/settings_service.py`)
```python
class SettingsService:
    async def get_effective_settings(user_id: str) -> UserSettings
    async def update_user_setting(user_id: str, key: str, value: Any) -> bool
    async def update_system_setting(admin_user_id: str, key: str, value: Any) -> bool
    async def migrate_legacy_preferences() -> MigrationResult
```

#### 2. MCP Tools (`tools/settings_tools.py`)
```python
async def get_user_settings(user_id: str) -> Dict[str, Any]
async def update_user_settings(user_id: str, settings: Dict[str, Any]) -> Dict[str, Any]
async def get_system_settings(admin_user_id: str) -> Dict[str, Any]  # Admin only
async def update_system_settings(admin_user_id: str, settings: Dict[str, Any]) -> Dict[str, Any]  # Admin only
```

### Frontend Integration

#### 1. Enhanced Settings Service
```typescript
class DatabaseSettingsService {
    async loadSettingsFromDatabase(): Promise<UserSettings>
    async saveSettingToDatabase(key: string, value: any): Promise<boolean>
    async syncWithLocalStorage(): Promise<void>  // Backward compatibility
}
```

#### 2. Migration Strategy
1. **Phase 1**: Load from database, fallback to localStorage
2. **Phase 2**: Gradual migration of localStorage settings to database
3. **Phase 3**: Database-only operation with localStorage cache

## Security Considerations

### 1. Access Control
- **System Settings**: Admin-only access (`is_admin_only` flag)
- **User Settings**: User can only modify their own settings
- **Audit Trail**: All changes logged with user and IP information

### 2. Validation
- **Schema Validation**: JSON schema validation for all settings
- **Range Validation**: Enforce MIN/MAX constraints on numeric values
- **Permission Validation**: Verify user permissions before allowing changes

### 3. Data Protection
- **Sensitive Settings**: Certain settings (like retention policies) require admin approval
- **Change Auditing**: Complete audit trail for compliance requirements
- **Rollback Capability**: Ability to restore previous setting values

## Performance Considerations

### 1. Indexing Strategy
- **Composite Indexes**: `(user_id, category)` for efficient user queries
- **Range Queries**: Timestamp indexes for audit queries
- **Unique Constraints**: Prevent duplicate settings

### 2. Caching Strategy
- **Frontend Cache**: Settings cached in memory with refresh mechanism
- **Backend Cache**: Redis cache for frequently accessed system settings
- **Database Optimization**: Efficient JSON queries with proper indexing

### 3. Query Optimization
- **Batch Operations**: Bulk setting updates in single transaction
- **Lazy Loading**: Load settings on-demand by category
- **Change Detection**: Only update when values actually change

## Migration Strategy

### 1. New Installations
- Create all tables with initial system settings
- Populate default admin and user settings
- No migration needed

### 2. Existing Installations
- Add new tables to existing database
- Migrate `users.preferences_json` data to new structure
- Maintain backward compatibility during transition

### 3. Version Management
- **Schema Version**: Track database schema version
- **Setting Version**: Individual setting versioning for conflict resolution
- **Migration Scripts**: Automated migration between versions
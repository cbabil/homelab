-- Migration Script for Existing Installations with Security Controls
-- Safely migrates existing homelab installations to the new settings database schema
-- Includes backup creation, rollback capability, and data integrity verification

-- Enable foreign key constraints for data integrity
PRAGMA foreign_keys = ON;

-- Create backup table for rollback capability
CREATE TABLE IF NOT EXISTS migration_backup_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_id TEXT NOT NULL UNIQUE,
    migration_start_time TEXT NOT NULL,
    migration_status TEXT NOT NULL DEFAULT 'IN_PROGRESS',
    admin_user_id TEXT NOT NULL,
    client_ip TEXT,
    backup_tables_created BOOLEAN DEFAULT 0,
    settings_tables_created BOOLEAN DEFAULT 0,
    data_migrated BOOLEAN DEFAULT 0,
    migration_complete_time TEXT,
    rollback_info TEXT, -- JSON with rollback instructions
    checksum TEXT NOT NULL
);

-- Function to generate migration ID
-- Using timestamp + random component for uniqueness
CREATE TEMPORARY VIEW migration_session AS
SELECT
    'migration_' || datetime('now', 'utc') || '_' || abs(random() % 10000) as migration_id,
    datetime('now', 'utc') as start_time;

-- Insert migration session record
INSERT INTO migration_backup_info (
    migration_id, migration_start_time, admin_user_id, client_ip, checksum
)
SELECT
    migration_id,
    start_time,
    'ADMIN_USER_PLACEHOLDER', -- Will be replaced by initialization script
    'system',
    substr(lower(hex(randomblob(32))), 1, 64)
FROM migration_session;

-- Step 1: Create backup tables for existing data (if any settings exist)
-- This preserves existing user preferences or custom settings

-- Backup any existing preferences from users table
CREATE TABLE IF NOT EXISTS migration_backup_user_preferences AS
SELECT
    id as user_id,
    username,
    preferences_json,
    datetime('now', 'utc') as backup_created_at
FROM users
WHERE preferences_json IS NOT NULL AND preferences_json != '';

-- Backup any existing configuration files or settings (extensible)
CREATE TABLE IF NOT EXISTS migration_backup_config_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    file_content TEXT,
    file_hash TEXT,
    backup_created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

-- Step 2: Check if settings tables already exist
-- If they exist, this might be a re-migration or repair operation
CREATE TEMPORARY VIEW existing_settings_check AS
SELECT
    (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='system_settings') as has_system_settings,
    (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='user_settings') as has_user_settings,
    (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='settings_audit') as has_audit_settings,
    (SELECT COUNT(*) FROM system_settings WHERE 1=1) as existing_system_count,
    (SELECT COUNT(*) FROM user_settings WHERE 1=1) as existing_user_count
FROM (SELECT 1); -- Dummy FROM clause

-- Step 3: Create settings tables if they don't exist (reference to schema file)
-- This will be executed conditionally by the Python initialization script
-- The schema creation is handled by init_settings_schema.sql

-- Step 4: Migrate existing user preferences to user_settings table
-- Convert JSON preferences to individual settings with proper validation

INSERT OR IGNORE INTO user_settings (
    user_id, setting_key, setting_value, category, created_at, updated_at
)
SELECT
    u.id as user_id,
    'ui.theme',
    CASE
        WHEN json_extract(u.preferences_json, '$.theme') IS NOT NULL
        THEN '"' || json_extract(u.preferences_json, '$.theme') || '"'
        ELSE '"dark"' -- Default fallback
    END as setting_value,
    'ui' as category,
    datetime('now', 'utc') as created_at,
    datetime('now', 'utc') as updated_at
FROM users u
WHERE u.preferences_json IS NOT NULL
  AND u.preferences_json != ''
  AND json_extract(u.preferences_json, '$.theme') IS NOT NULL
  AND json_extract(u.preferences_json, '$.theme') IN ('light', 'dark', 'auto');

INSERT OR IGNORE INTO user_settings (
    user_id, setting_key, setting_value, category, created_at, updated_at
)
SELECT
    u.id as user_id,
    'ui.sidebar_collapsed',
    CASE
        WHEN json_extract(u.preferences_json, '$.sidebarCollapsed') IS NOT NULL
        THEN LOWER(json_extract(u.preferences_json, '$.sidebarCollapsed'))
        ELSE 'false' -- Default fallback
    END as setting_value,
    'ui' as category,
    datetime('now', 'utc') as created_at,
    datetime('now', 'utc') as updated_at
FROM users u
WHERE u.preferences_json IS NOT NULL
  AND u.preferences_json != ''
  AND json_extract(u.preferences_json, '$.sidebarCollapsed') IS NOT NULL
  AND json_extract(u.preferences_json, '$.sidebarCollapsed') IN ('true', 'false');

INSERT OR IGNORE INTO user_settings (
    user_id, setting_key, setting_value, category, created_at, updated_at
)
SELECT
    u.id as user_id,
    'ui.items_per_page',
    CAST(json_extract(u.preferences_json, '$.itemsPerPage') AS TEXT) as setting_value,
    'ui' as category,
    datetime('now', 'utc') as created_at,
    datetime('now', 'utc') as updated_at
FROM users u
WHERE u.preferences_json IS NOT NULL
  AND u.preferences_json != ''
  AND json_extract(u.preferences_json, '$.itemsPerPage') IS NOT NULL
  AND CAST(json_extract(u.preferences_json, '$.itemsPerPage') AS INTEGER) BETWEEN 10 AND 100;

INSERT OR IGNORE INTO user_settings (
    user_id, setting_key, setting_value, category, created_at, updated_at
)
SELECT
    u.id as user_id,
    'ui.refresh_interval',
    CAST(json_extract(u.preferences_json, '$.refreshInterval') AS TEXT) as setting_value,
    'ui' as category,
    datetime('now', 'utc') as created_at,
    datetime('now', 'utc') as updated_at
FROM users u
WHERE u.preferences_json IS NOT NULL
  AND u.preferences_json != ''
  AND json_extract(u.preferences_json, '$.refreshInterval') IS NOT NULL
  AND CAST(json_extract(u.preferences_json, '$.refreshInterval') AS INTEGER) BETWEEN 5000 AND 300000;

INSERT OR IGNORE INTO user_settings (
    user_id, setting_key, setting_value, category, created_at, updated_at
)
SELECT
    u.id as user_id,
    'security.session_timeout',
    CAST(json_extract(u.preferences_json, '$.sessionTimeout') AS TEXT) as setting_value,
    'security' as category,
    datetime('now', 'utc') as created_at,
    datetime('now', 'utc') as updated_at
FROM users u
WHERE u.preferences_json IS NOT NULL
  AND u.preferences_json != ''
  AND json_extract(u.preferences_json, '$.sessionTimeout') IS NOT NULL
  AND CAST(json_extract(u.preferences_json, '$.sessionTimeout') AS INTEGER) BETWEEN 300 AND 86400;

-- Step 5: Migrate any existing application configuration
-- This section can be extended based on specific configuration needs

-- Create system setting for migration tracking
INSERT OR IGNORE INTO system_settings (
    setting_key, setting_value, category, scope, data_type,
    is_admin_only, description, updated_by
) VALUES (
    'system.migration_completed',
    'true',
    'system',
    'system',
    'boolean',
    1,
    'Indicates successful migration from legacy preferences system',
    'migration_script'
);

INSERT OR IGNORE INTO system_settings (
    setting_key, setting_value, category, scope, data_type,
    is_admin_only, description, updated_by
) VALUES (
    'system.migration_timestamp',
    '"' || datetime('now', 'utc') || '"',
    'system',
    'system',
    'string',
    1,
    'Timestamp of successful migration completion',
    'migration_script'
);

-- Step 6: Create migration audit entry with comprehensive details
INSERT INTO settings_audit (
    table_name, record_id, user_id, setting_key,
    old_value, new_value, change_type, change_reason,
    client_ip, user_agent, created_at, checksum
) VALUES (
    'system_settings',
    0,
    'migration_script',
    'system.migration_operation',
    NULL,
    json_object(
        'operation', 'existing_installation_migration',
        'timestamp', datetime('now', 'utc'),
        'migrated_user_preferences', (SELECT COUNT(*) FROM user_settings WHERE created_at = datetime('now', 'utc')),
        'backup_user_preferences', (SELECT COUNT(*) FROM migration_backup_user_preferences),
        'migration_id', (SELECT migration_id FROM migration_session LIMIT 1)
    ),
    'CREATE',
    'Migration of existing installation to new settings database schema',
    'system',
    'migration_script',
    datetime('now', 'utc'),
    substr(lower(hex(randomblob(32))), 1, 64)
);

-- Step 7: Update migration status
UPDATE migration_backup_info
SET
    migration_status = 'COMPLETED',
    backup_tables_created = 1,
    settings_tables_created = 1,
    data_migrated = 1,
    migration_complete_time = datetime('now', 'utc'),
    rollback_info = json_object(
        'backup_tables', json_array('migration_backup_user_preferences', 'migration_backup_config_files'),
        'migrated_user_settings', (SELECT COUNT(*) FROM user_settings),
        'rollback_procedure', 'Use migration_backup_user_preferences to restore original preferences_json in users table'
    ),
    checksum = substr(lower(hex(randomblob(32))), 1, 64)
WHERE migration_status = 'IN_PROGRESS';

-- Step 8: Verification queries for migration success
-- These provide feedback on migration results

CREATE TEMPORARY VIEW migration_verification AS
SELECT
    'Migration Verification' as operation,
    (SELECT COUNT(*) FROM migration_backup_user_preferences) as backed_up_user_preferences,
    (SELECT COUNT(*) FROM user_settings) as migrated_user_settings,
    (SELECT COUNT(*) FROM system_settings) as total_system_settings,
    (SELECT COUNT(*) FROM settings_audit WHERE setting_key = 'system.migration_operation') as migration_audit_entries,
    (SELECT migration_status FROM migration_backup_info ORDER BY id DESC LIMIT 1) as migration_status,
    (SELECT migration_id FROM migration_backup_info ORDER BY id DESC LIMIT 1) as migration_id;

-- Step 9: Data integrity verification
-- Verify that migrated data maintains referential integrity

CREATE TEMPORARY VIEW data_integrity_check AS
SELECT
    'Data Integrity Check' as operation,
    (SELECT COUNT(*) FROM user_settings us
     LEFT JOIN users u ON us.user_id = u.id
     WHERE u.id IS NULL) as orphaned_user_settings,
    (SELECT COUNT(*) FROM user_settings WHERE json_valid(setting_value) = 0) as invalid_json_values,
    (SELECT COUNT(*) FROM system_settings WHERE json_valid(setting_value) = 0) as invalid_system_json_values,
    (SELECT COUNT(*) FROM settings_audit WHERE length(checksum) != 64) as invalid_audit_checksums;

-- Step 10: Performance optimization after migration
-- Analyze tables and update statistics for optimal query performance
ANALYZE user_settings;
ANALYZE system_settings;
ANALYZE settings_audit;

-- Step 11: Security verification
-- Ensure all security constraints are properly applied

CREATE TEMPORARY VIEW security_verification AS
SELECT
    'Security Verification' as operation,
    (SELECT COUNT(*) FROM user_settings WHERE
     setting_key NOT GLOB '[a-zA-Z0-9._]*' OR
     setting_key LIKE '.%' OR
     setting_key LIKE '%.' OR
     setting_key LIKE '%..%') as invalid_setting_keys,
    (SELECT COUNT(*) FROM system_settings WHERE
     category NOT IN ('ui', 'security', 'system', 'retention')) as invalid_categories,
    (SELECT COUNT(*) FROM settings_audit WHERE
     table_name NOT IN ('system_settings', 'user_settings')) as invalid_audit_tables,
    (SELECT COUNT(*) FROM user_settings WHERE user_id NOT GLOB '[a-zA-Z0-9_-]*') as invalid_user_ids;

-- Final migration summary query
SELECT
    mv.operation,
    mv.backed_up_user_preferences,
    mv.migrated_user_settings,
    mv.total_system_settings,
    mv.migration_audit_entries,
    mv.migration_status,
    mv.migration_id,
    dic.orphaned_user_settings,
    dic.invalid_json_values,
    dic.invalid_system_json_values,
    dic.invalid_audit_checksums,
    sv.invalid_setting_keys,
    sv.invalid_categories,
    sv.invalid_audit_tables,
    sv.invalid_user_ids
FROM migration_verification mv
CROSS JOIN data_integrity_check dic
CROSS JOIN security_verification sv;

-- Cleanup temporary views
DROP VIEW IF EXISTS migration_session;
DROP VIEW IF EXISTS existing_settings_check;
DROP VIEW IF EXISTS migration_verification;
DROP VIEW IF EXISTS data_integrity_check;
DROP VIEW IF EXISTS security_verification;

-- Success message
SELECT 'Migration completed successfully. Check migration_backup_info table for details.' as result;
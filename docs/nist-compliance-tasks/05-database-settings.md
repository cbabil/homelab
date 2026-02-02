# Task 05: Add NIST Settings to Database

## Overview

Add new security settings to the database seed file to support NIST SP 800-63B-4 compliance configuration.

## File to Modify

`backend/sql/seed_default_settings.sql`

## Requirements

1. Add NIST compliance mode toggle
2. Add blocklist configuration settings
3. Add Unicode support setting
4. Update password length bounds for NIST mode
5. Maintain backward compatibility (default OFF)

## New Settings to Add

Insert after the existing security settings section:

```sql
-- NIST SP 800-63B-4 Compliance Settings
-- These settings enable modern password policy based on length and blocklist screening
INSERT OR IGNORE INTO system_settings (
    setting_key, setting_value, default_value, category, scope, data_type,
    is_admin_only, description, updated_by
) VALUES
    -- Master toggle for NIST compliance mode
    ('security.nist_compliance_mode', 'false', 'false', 'security', 'system', 'boolean', 1,
     'Enable NIST SP 800-63B-4 compliant password policy (length + blocklist, no complexity rules)', 'system'),

    -- Maximum password length (NIST requires at least 64)
    ('security.password_max_length', '128', '128', 'security', 'system', 'number', 1,
     'Maximum password length (NIST requires at least 64 characters)', 'system'),

    -- Blocklist screening settings
    ('security.enable_blocklist_check', 'true', 'true', 'security', 'system', 'boolean', 1,
     'Screen passwords against known breached and common passwords', 'system'),

    ('security.enable_hibp_api_check', 'false', 'false', 'security', 'system', 'boolean', 1,
     'Check passwords against Have I Been Pwned API (requires internet connectivity)', 'system'),

    -- Unicode support
    ('security.allow_unicode_passwords', 'true', 'true', 'security', 'system', 'boolean', 1,
     'Allow Unicode characters including spaces and emojis in passwords', 'system');
```

## Complete Settings Section

For reference, here's how the security settings section should look after the update:

```sql
-- Security Settings: Session management and authentication
INSERT OR IGNORE INTO system_settings (
    setting_key, setting_value, default_value, category, scope, data_type,
    is_admin_only, description, updated_by
) VALUES
    -- Session settings
    ('security.session_timeout_default', '3600', '3600', 'security', 'user_overridable', 'number', 0,
     'Default session timeout in seconds', 'system'),

    ('security.session_idle_timeout', '900', '900', 'security', 'system', 'number', 1,
     'Session idle timeout in seconds', 'system'),

    -- Account lockout settings
    ('security.max_login_attempts', '5', '5', 'security', 'system', 'number', 1,
     'Maximum login attempts before account lockout', 'system'),

    ('security.account_lockout_duration', '900', '900', 'security', 'system', 'number', 1,
     'Account lockout duration in seconds', 'system'),

    -- Password policy settings (Legacy mode)
    ('security.password_min_length', '8', '8', 'security', 'system', 'number', 1,
     'Minimum password length requirement', 'system'),

    ('security.password_require_special_chars', 'true', 'true', 'security', 'system', 'boolean', 1,
     'Require special characters in passwords (legacy mode only)', 'system'),

    ('security.password_require_numbers', 'true', 'true', 'security', 'system', 'boolean', 1,
     'Require numbers in passwords (legacy mode only)', 'system'),

    ('security.password_require_uppercase', 'true', 'true', 'security', 'system', 'boolean', 1,
     'Require uppercase letters in passwords (legacy mode only)', 'system'),

    ('security.force_password_change_days', '90', '90', 'security', 'system', 'number', 1,
     'Force password change after N days, 0 = disabled (legacy mode only)', 'system'),

    -- NIST SP 800-63B-4 Compliance Settings (NEW)
    ('security.nist_compliance_mode', 'false', 'false', 'security', 'system', 'boolean', 1,
     'Enable NIST SP 800-63B-4 compliant password policy', 'system'),

    ('security.password_max_length', '128', '128', 'security', 'system', 'number', 1,
     'Maximum password length (NIST requires at least 64)', 'system'),

    ('security.enable_blocklist_check', 'true', 'true', 'security', 'system', 'boolean', 1,
     'Screen passwords against known breached passwords', 'system'),

    ('security.enable_hibp_api_check', 'false', 'false', 'security', 'system', 'boolean', 1,
     'Check passwords against Have I Been Pwned API', 'system'),

    ('security.allow_unicode_passwords', 'true', 'true', 'security', 'system', 'boolean', 1,
     'Allow Unicode characters in passwords', 'system'),

    -- Audit settings
    ('security.audit_log_retention_days', '365', '365', 'security', 'system', 'number', 1,
     'Audit log retention period in days', 'system'),

    ('security.enable_audit_logging', 'true', 'true', 'security', 'system', 'boolean', 1,
     'Enable comprehensive audit logging', 'system');
```

## Migration Script

For existing deployments, create a migration script:

`backend/sql/migrations/001_add_nist_settings.sql`

```sql
-- Migration: Add NIST SP 800-63B-4 security settings
-- Version: 1.1.0

-- Add new NIST compliance settings (INSERT OR IGNORE prevents duplicates)
INSERT OR IGNORE INTO system_settings (
    setting_key, setting_value, default_value, category, scope, data_type,
    is_admin_only, description, updated_by
) VALUES
    ('security.nist_compliance_mode', 'false', 'false', 'security', 'system', 'boolean', 1,
     'Enable NIST SP 800-63B-4 compliant password policy', 'migration'),

    ('security.password_max_length', '128', '128', 'security', 'system', 'number', 1,
     'Maximum password length (NIST requires at least 64)', 'migration'),

    ('security.enable_blocklist_check', 'true', 'true', 'security', 'system', 'boolean', 1,
     'Screen passwords against known breached passwords', 'migration'),

    ('security.enable_hibp_api_check', 'false', 'false', 'security', 'system', 'boolean', 1,
     'Check passwords against Have I Been Pwned API', 'migration'),

    ('security.allow_unicode_passwords', 'true', 'true', 'security', 'system', 'boolean', 1,
     'Allow Unicode characters in passwords', 'migration');

-- Update schema version
UPDATE system_settings
SET setting_value = '"1.1.0"'
WHERE setting_key = 'app.settings_schema_version';

-- Audit the migration
INSERT INTO settings_audit (
    table_name, record_id, user_id, setting_key,
    old_value, new_value, change_type, change_reason,
    client_ip, user_agent, created_at, checksum
) VALUES (
    'system_settings',
    0,
    'system',
    'security.nist_compliance_mode',
    NULL,
    '{"action": "nist_settings_added", "version": "1.1.0"}',
    'CREATE',
    'Added NIST SP 800-63B-4 compliance settings',
    'migration',
    'migration_script',
    datetime('now', 'utc'),
    substr(lower(hex(randomblob(32))), 1, 64)
);
```

## Setting Descriptions for UI

| Setting Key | Display Name | Description |
|-------------|--------------|-------------|
| `security.nist_compliance_mode` | NIST SP 800-63B Compliance | Enable modern password policy based on length and blocklist screening instead of complexity rules |
| `security.password_max_length` | Maximum Password Length | Maximum allowed password length (NIST requires at least 64 characters) |
| `security.enable_blocklist_check` | Password Blocklist Screening | Screen passwords against known breached and common passwords |
| `security.enable_hibp_api_check` | Have I Been Pwned API | Check passwords against the HIBP database (requires internet) |
| `security.allow_unicode_passwords` | Allow Unicode Passwords | Allow spaces, emojis, and international characters in passwords |

## Acceptance Criteria

- [ ] All 5 new settings added to `seed_default_settings.sql`
- [ ] `nist_compliance_mode` defaults to `false` for backward compatibility
- [ ] Migration script created for existing deployments
- [ ] Settings audit entry created for migration
- [ ] Schema version updated to 1.1.0

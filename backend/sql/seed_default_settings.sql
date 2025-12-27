-- Default Settings Seed Script with Security Validation
-- Populates secure default settings for the homelab management application
-- All values are JSON-encoded and validated according to security constraints

-- UI Settings: Default theme and interface preferences
INSERT OR IGNORE INTO system_settings (
    setting_key, setting_value, category, scope, data_type,
    is_admin_only, description, updated_by
) VALUES
    ('ui.theme_default', '"dark"', 'ui', 'user_overridable', 'string', 0,
     'Default theme for new users (light, dark, auto)', 'system'),

    ('ui.sidebar_collapsed_default', 'false', 'ui', 'user_overridable', 'boolean', 0,
     'Default sidebar state for new users', 'system'),

    ('ui.items_per_page_default', '25', 'ui', 'user_overridable', 'number', 0,
     'Default number of items per page in lists', 'system'),

    ('ui.refresh_interval_default', '30000', 'ui', 'user_overridable', 'number', 0,
     'Default auto-refresh interval in milliseconds', 'system'),

    ('ui.date_format_default', '"YYYY-MM-DD HH:mm:ss"', 'ui', 'user_overridable', 'string', 0,
     'Default date/time format for display', 'system'),

    ('ui.timezone_default', '"UTC"', 'ui', 'user_overridable', 'string', 0,
     'Default timezone for new users', 'system'),

    ('ui.language_default', '"en"', 'ui', 'user_overridable', 'string', 0,
     'Default language for new users', 'system');

-- Security Settings: Session management and authentication
INSERT OR IGNORE INTO system_settings (
    setting_key, setting_value, category, scope, data_type,
    is_admin_only, description, updated_by
) VALUES
    ('security.session_timeout_default', '3600', 'security', 'user_overridable', 'number', 0,
     'Default session timeout in seconds', 'system'),

    ('security.max_login_attempts', '5', 'security', 'system', 'number', 1,
     'Maximum login attempts before account lockout', 'system'),

    ('security.account_lockout_duration', '900', 'security', 'system', 'number', 1,
     'Account lockout duration in seconds', 'system'),

    ('security.password_min_length', '8', 'security', 'system', 'number', 1,
     'Minimum password length requirement', 'system'),

    ('security.password_require_special_chars', 'true', 'security', 'system', 'boolean', 1,
     'Require special characters in passwords', 'system'),

    ('security.password_require_numbers', 'true', 'security', 'system', 'boolean', 1,
     'Require numbers in passwords', 'system'),

    ('security.password_require_uppercase', 'true', 'security', 'system', 'boolean', 1,
     'Require uppercase letters in passwords', 'system'),

    ('security.force_password_change_days', '90', 'security', 'system', 'number', 1,
     'Force password change after N days (0 = disabled)', 'system'),

    ('security.audit_log_retention_days', '365', 'security', 'system', 'number', 1,
     'Audit log retention period in days', 'system'),

    ('security.enable_audit_logging', 'true', 'security', 'system', 'boolean', 1,
     'Enable comprehensive audit logging', 'system');

-- System Settings: Core application configuration
INSERT OR IGNORE INTO system_settings (
    setting_key, setting_value, category, scope, data_type,
    is_admin_only, description, updated_by
) VALUES
    ('app.settings_schema_version', '"1.0.0"', 'system', 'system', 'string', 1,
     'Settings database schema version for migration tracking', 'system'),

    ('system.app_name', '"Homelab Management"', 'system', 'system', 'string', 1,
     'Application display name', 'system'),

    ('system.app_version', '"1.0.0"', 'system', 'system', 'string', 1,
     'Current application version', 'system'),

    ('system.maintenance_mode', 'false', 'system', 'system', 'boolean', 1,
     'Enable maintenance mode (blocks non-admin access)', 'system'),

    ('system.maintenance_message', '"System maintenance in progress. Please try again later."', 'system', 'system', 'string', 1,
     'Message displayed during maintenance mode', 'system'),

    ('system.max_concurrent_sessions_per_user', '3', 'system', 'system', 'number', 1,
     'Maximum concurrent sessions per user', 'system'),

    ('system.api_rate_limit_requests_per_minute', '100', 'system', 'system', 'number', 1,
     'API rate limit per user per minute', 'system'),

    ('system.enable_user_registration', 'false', 'system', 'system', 'boolean', 1,
     'Allow new user self-registration', 'system'),

    ('system.default_user_role', '"user"', 'system', 'system', 'string', 1,
     'Default role for new users', 'system'),

    ('system.backup_retention_days', '30', 'system', 'system', 'number', 1,
     'Database backup retention period in days', 'system'),

    ('system.log_level', '"INFO"', 'system', 'system', 'string', 1,
     'Application logging level (DEBUG, INFO, WARNING, ERROR)', 'system');

-- Data Retention Settings: Configurable data cleanup policies
INSERT OR IGNORE INTO system_settings (
    setting_key, setting_value, category, scope, data_type,
    is_admin_only, description, updated_by
) VALUES
    ('retention.log_entries_default_days', '90', 'retention', 'user_overridable', 'number', 0,
     'Default retention period for log entries in days', 'system'),

    ('retention.other_data_default_days', '365', 'retention', 'user_overridable', 'number', 0,
     'Default retention period for other data in days', 'system'),

    ('retention.min_log_retention_days', '7', 'retention', 'system', 'number', 1,
     'Minimum allowed log retention period in days', 'system'),

    ('retention.max_log_retention_days', '365', 'retention', 'system', 'number', 1,
     'Maximum allowed log retention period in days', 'system'),

    ('retention.min_other_data_retention_days', '30', 'retention', 'system', 'number', 1,
     'Minimum allowed other data retention period in days', 'system'),

    ('retention.max_other_data_retention_days', '3650', 'retention', 'system', 'number', 1,
     'Maximum allowed other data retention period in days (10 years)', 'system'),

    ('retention.auto_cleanup_enabled', 'true', 'retention', 'system', 'boolean', 1,
     'Enable automatic data cleanup based on retention policies', 'system'),

    ('retention.cleanup_schedule_cron', '"0 2 * * 0"', 'retention', 'system', 'string', 1,
     'Cron schedule for automatic cleanup (weekly at 2 AM Sunday)', 'system'),

    ('retention.cleanup_batch_size', '1000', 'retention', 'system', 'number', 1,
     'Batch size for cleanup operations to prevent performance issues', 'system');

-- Notification Settings: Alert and notification preferences
INSERT OR IGNORE INTO system_settings (
    setting_key, setting_value, category, scope, data_type,
    is_admin_only, description, updated_by
) VALUES
    ('notifications.email_enabled', 'false', 'system', 'system', 'boolean', 1,
     'Enable email notifications', 'system'),

    ('notifications.smtp_server', '""', 'system', 'system', 'string', 1,
     'SMTP server for email notifications', 'system'),

    ('notifications.smtp_port', '587', 'system', 'system', 'number', 1,
     'SMTP server port', 'system'),

    ('notifications.smtp_use_tls', 'true', 'system', 'system', 'boolean', 1,
     'Use TLS for SMTP connection', 'system'),

    ('notifications.from_email', '""', 'system', 'system', 'string', 1,
     'From email address for notifications', 'system'),

    ('notifications.admin_email', '""', 'system', 'system', 'string', 1,
     'Admin email for critical alerts', 'system'),

    ('notifications.enable_login_alerts', 'true', 'security', 'user_overridable', 'boolean', 0,
     'Send alerts for successful logins', 'system'),

    ('notifications.enable_security_alerts', 'true', 'security', 'user_overridable', 'boolean', 0,
     'Send alerts for security events', 'system');

-- Monitoring Settings: System monitoring and health check configuration
INSERT OR IGNORE INTO system_settings (
    setting_key, setting_value, category, scope, data_type,
    is_admin_only, description, updated_by
) VALUES
    ('monitoring.health_check_interval', '300', 'system', 'system', 'number', 1,
     'Health check interval in seconds', 'system'),

    ('monitoring.enable_performance_metrics', 'true', 'system', 'system', 'boolean', 1,
     'Enable performance metrics collection', 'system'),

    ('monitoring.metrics_retention_days', '30', 'system', 'system', 'number', 1,
     'Performance metrics retention period in days', 'system'),

    ('monitoring.enable_disk_space_monitoring', 'true', 'system', 'system', 'boolean', 1,
     'Monitor disk space usage', 'system'),

    ('monitoring.disk_space_warning_threshold', '85', 'system', 'system', 'number', 1,
     'Disk space warning threshold percentage', 'system'),

    ('monitoring.disk_space_critical_threshold', '95', 'system', 'system', 'number', 1,
     'Disk space critical threshold percentage', 'system'),

    ('monitoring.enable_memory_monitoring', 'true', 'system', 'system', 'boolean', 1,
     'Monitor memory usage', 'system'),

    ('monitoring.memory_warning_threshold', '80', 'system', 'system', 'number', 1,
     'Memory usage warning threshold percentage', 'system'),

    ('monitoring.memory_critical_threshold', '90', 'system', 'system', 'number', 1,
     'Memory usage critical threshold percentage', 'system');

-- API and Integration Settings: External API and webhook configuration
INSERT OR IGNORE INTO system_settings (
    setting_key, setting_value, category, scope, data_type,
    is_admin_only, description, updated_by
) VALUES
    ('api.enable_swagger_ui', 'true', 'system', 'system', 'boolean', 1,
     'Enable Swagger UI for API documentation', 'system'),

    ('api.enable_cors', 'true', 'system', 'system', 'boolean', 1,
     'Enable CORS for cross-origin requests', 'system'),

    ('api.cors_origins', '["http://localhost:5173", "http://localhost:3000"]', 'system', 'system', 'array', 1,
     'Allowed CORS origins', 'system'),

    ('api.enable_webhooks', 'false', 'system', 'system', 'boolean', 1,
     'Enable webhook notifications', 'system'),

    ('api.webhook_timeout_seconds', '30', 'system', 'system', 'number', 1,
     'Webhook request timeout in seconds', 'system'),

    ('api.webhook_retry_attempts', '3', 'system', 'system', 'number', 1,
     'Number of webhook retry attempts on failure', 'system'),

    ('api.enable_api_versioning', 'true', 'system', 'system', 'boolean', 1,
     'Enable API versioning support', 'system'),

    ('api.current_api_version', '"v1"', 'system', 'system', 'string', 1,
     'Current API version', 'system');

-- Advanced Security Settings: Additional security configurations
INSERT OR IGNORE INTO system_settings (
    setting_key, setting_value, category, scope, data_type,
    is_admin_only, description, updated_by
) VALUES
    ('security.enable_2fa', 'false', 'security', 'system', 'boolean', 1,
     'Enable two-factor authentication', 'system'),

    ('security.2fa_issuer_name', '"Homelab Management"', 'security', 'system', 'string', 1,
     'TOTP issuer name for 2FA apps', 'system'),

    ('security.enable_ip_whitelist', 'false', 'security', 'system', 'boolean', 1,
     'Enable IP address whitelisting', 'system'),

    ('security.ip_whitelist', '[]', 'security', 'system', 'array', 1,
     'Allowed IP addresses or CIDR ranges', 'system'),

    ('security.enable_geolocation_blocking', 'false', 'security', 'system', 'boolean', 1,
     'Enable geolocation-based access blocking', 'system'),

    ('security.blocked_countries', '[]', 'security', 'system', 'array', 1,
     'List of blocked country codes', 'system'),

    ('security.enable_csrf_protection', 'true', 'security', 'system', 'boolean', 1,
     'Enable CSRF protection for forms', 'system'),

    ('security.csrf_token_expiry_hours', '24', 'security', 'system', 'number', 1,
     'CSRF token expiry time in hours', 'system'),

    ('security.enable_content_security_policy', 'true', 'security', 'system', 'boolean', 1,
     'Enable Content Security Policy headers', 'system');

-- Feature Flags: Toggle application features on/off
INSERT OR IGNORE INTO system_settings (
    setting_key, setting_value, category, scope, data_type,
    is_admin_only, description, updated_by
) VALUES
    ('features.enable_user_preferences', 'true', 'system', 'system', 'boolean', 1,
     'Enable user preference customization', 'system'),

    ('features.enable_data_export', 'true', 'system', 'system', 'boolean', 1,
     'Enable data export functionality', 'system'),

    ('features.enable_data_import', 'false', 'system', 'system', 'boolean', 1,
     'Enable data import functionality', 'system'),

    ('features.enable_bulk_operations', 'true', 'system', 'system', 'boolean', 1,
     'Enable bulk operations on data', 'system'),

    ('features.enable_advanced_search', 'true', 'system', 'system', 'boolean', 1,
     'Enable advanced search and filtering', 'system'),

    ('features.enable_real_time_updates', 'true', 'system', 'system', 'boolean', 1,
     'Enable real-time updates via WebSocket', 'system'),

    ('features.enable_mobile_app_support', 'false', 'system', 'system', 'boolean', 1,
     'Enable mobile app API endpoints', 'system'),

    ('features.enable_third_party_integrations', 'false', 'system', 'system', 'boolean', 1,
     'Enable third-party service integrations', 'system');

-- Create initial system audit entry for seeding operation
INSERT INTO settings_audit (
    table_name, record_id, user_id, setting_key,
    old_value, new_value, change_type, change_reason,
    client_ip, user_agent, created_at, checksum
) VALUES (
    'system_settings',
    0,
    'system',
    'system.database_seeding',
    NULL,
    '{"action": "default_settings_seeded", "timestamp": "' || datetime('now', 'utc') || '", "settings_count": "' || (SELECT COUNT(*) FROM system_settings) || '"}',
    'CREATE',
    'Default settings seeded during database initialization',
    'system',
    'seed_script',
    datetime('now', 'utc'),
    substr(
        lower(hex(randomblob(32))),
        1, 64
    )
);

-- Verification: Count seeded settings by category
-- This helps verify the seeding was successful
SELECT
    'Seeding Summary' as operation,
    COUNT(*) as total_settings,
    COUNT(CASE WHEN category = 'ui' THEN 1 END) as ui_settings,
    COUNT(CASE WHEN category = 'security' THEN 1 END) as security_settings,
    COUNT(CASE WHEN category = 'system' THEN 1 END) as system_settings,
    COUNT(CASE WHEN category = 'retention' THEN 1 END) as retention_settings,
    COUNT(CASE WHEN is_admin_only = 1 THEN 1 END) as admin_only_settings,
    COUNT(CASE WHEN scope = 'user_overridable' THEN 1 END) as user_overridable_settings
FROM system_settings;
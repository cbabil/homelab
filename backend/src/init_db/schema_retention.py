"""
Retention Settings Schema

Stores system-wide retention settings for logs and data.
Default values are inserted on first run and can be modified by admins.
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS retention_settings (
    id TEXT PRIMARY KEY DEFAULT 'system',
    -- Log retention (in days)
    audit_log_retention INTEGER NOT NULL DEFAULT 365,
    access_log_retention INTEGER NOT NULL DEFAULT 30,
    application_log_retention INTEGER NOT NULL DEFAULT 30,
    server_log_retention INTEGER NOT NULL DEFAULT 90,
    -- Data retention (in days)
    metrics_retention INTEGER NOT NULL DEFAULT 90,
    notification_retention INTEGER NOT NULL DEFAULT 30,
    session_retention INTEGER NOT NULL DEFAULT 7,
    -- Metadata
    last_updated TEXT,
    updated_by_user_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Insert default values if not exists
INSERT OR IGNORE INTO retention_settings (id) VALUES ('system');
"""

# Constraints for validation (used by backend service)
RETENTION_CONSTRAINTS = {
    "audit_log_retention": {"min": 90, "max": 3650, "default": 365},
    "access_log_retention": {"min": 7, "max": 365, "default": 30},
    "application_log_retention": {"min": 7, "max": 365, "default": 30},
    "server_log_retention": {"min": 7, "max": 365, "default": 90},
    "metrics_retention": {"min": 7, "max": 365, "default": 90},
    "notification_retention": {"min": 7, "max": 365, "default": 30},
    "session_retention": {"min": 1, "max": 90, "default": 7},
}

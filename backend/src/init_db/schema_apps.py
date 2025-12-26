"""App installation database schema."""

APPS_SCHEMA = """
CREATE TABLE IF NOT EXISTS installed_apps (
    id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL,
    app_id TEXT NOT NULL,
    container_id TEXT,
    container_name TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    config TEXT,
    installed_at TEXT,
    started_at TEXT,
    error_message TEXT,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    UNIQUE(server_id, app_id)
);

CREATE INDEX IF NOT EXISTS idx_installed_apps_server ON installed_apps(server_id);
CREATE INDEX IF NOT EXISTS idx_installed_apps_status ON installed_apps(status);
"""


def get_apps_schema() -> str:
    """Return apps schema SQL."""
    return APPS_SCHEMA

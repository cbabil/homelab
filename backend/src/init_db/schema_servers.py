"""Server database schema initialization."""

SERVERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS servers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    host TEXT NOT NULL,
    port INTEGER NOT NULL DEFAULT 22,
    username TEXT NOT NULL,
    auth_type TEXT NOT NULL CHECK(auth_type IN ('password', 'key')),
    status TEXT NOT NULL DEFAULT 'disconnected',
    created_at TEXT NOT NULL,
    last_connected TEXT,
    UNIQUE(host, port, username)
);

CREATE TABLE IF NOT EXISTS server_credentials (
    server_id TEXT PRIMARY KEY,
    encrypted_data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_servers_status ON servers(status);
CREATE INDEX IF NOT EXISTS idx_servers_host ON servers(host);
"""


def get_servers_schema() -> str:
    """Return servers schema SQL."""
    return SERVERS_SCHEMA

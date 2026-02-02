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
    system_info TEXT,
    docker_installed INTEGER NOT NULL DEFAULT 0,
    system_info_updated_at TEXT,
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


# Migration for adding system_info columns to existing databases
SERVERS_MIGRATION_V2 = """
-- Add system_info columns if they don't exist
-- SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so we use a workaround

-- Check if column exists and add if not
PRAGMA foreign_keys=off;

-- Create a temp table with the new schema
CREATE TABLE IF NOT EXISTS servers_new (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    host TEXT NOT NULL,
    port INTEGER NOT NULL DEFAULT 22,
    username TEXT NOT NULL,
    auth_type TEXT NOT NULL CHECK(auth_type IN ('password', 'key')),
    status TEXT NOT NULL DEFAULT 'disconnected',
    created_at TEXT NOT NULL,
    last_connected TEXT,
    system_info TEXT,
    docker_installed INTEGER NOT NULL DEFAULT 0,
    system_info_updated_at TEXT,
    UNIQUE(host, port, username)
);

-- Copy data from old table if it exists and has data
INSERT OR IGNORE INTO servers_new (id, name, host, port, username, auth_type, status, created_at, last_connected)
SELECT id, name, host, port, username, auth_type, status, created_at, last_connected
FROM servers WHERE EXISTS (SELECT 1 FROM servers LIMIT 1);

-- Drop old table and rename new one (only if migration is needed)
DROP TABLE IF EXISTS servers;
ALTER TABLE servers_new RENAME TO servers;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_servers_status ON servers(status);
CREATE INDEX IF NOT EXISTS idx_servers_host ON servers(host);
CREATE INDEX IF NOT EXISTS idx_servers_docker ON servers(docker_installed);

PRAGMA foreign_keys=on;
"""


def get_servers_migration_v2() -> str:
    """Return migration SQL for adding system_info columns."""
    return SERVERS_MIGRATION_V2

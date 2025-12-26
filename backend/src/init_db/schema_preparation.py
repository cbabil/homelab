"""Preparation database schema."""

PREPARATION_SCHEMA = """
CREATE TABLE IF NOT EXISTS server_preparations (
    id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    current_step TEXT,
    detected_os TEXT,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS preparation_logs (
    id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL,
    preparation_id TEXT NOT NULL,
    step TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT NOT NULL,
    output TEXT,
    error TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    FOREIGN KEY (preparation_id) REFERENCES server_preparations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_preparations_server ON server_preparations(server_id);
CREATE INDEX IF NOT EXISTS idx_preparations_status ON server_preparations(status);
CREATE INDEX IF NOT EXISTS idx_prep_logs_server ON preparation_logs(server_id);
CREATE INDEX IF NOT EXISTS idx_prep_logs_preparation ON preparation_logs(preparation_id);
"""


def get_preparation_schema() -> str:
    """Return preparation schema SQL."""
    return PREPARATION_SCHEMA

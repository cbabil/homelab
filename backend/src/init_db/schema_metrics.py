"""Metrics and activity log database schema."""

METRICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS server_metrics (
    id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL,
    cpu_percent REAL NOT NULL,
    memory_percent REAL NOT NULL,
    memory_used_mb INTEGER NOT NULL,
    memory_total_mb INTEGER NOT NULL,
    disk_percent REAL NOT NULL,
    disk_used_gb INTEGER NOT NULL,
    disk_total_gb INTEGER NOT NULL,
    network_rx_bytes INTEGER DEFAULT 0,
    network_tx_bytes INTEGER DEFAULT 0,
    load_average_1m REAL,
    load_average_5m REAL,
    load_average_15m REAL,
    uptime_seconds INTEGER,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS container_metrics (
    id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL,
    container_id TEXT NOT NULL,
    container_name TEXT NOT NULL,
    cpu_percent REAL NOT NULL,
    memory_usage_mb INTEGER NOT NULL,
    memory_limit_mb INTEGER NOT NULL,
    network_rx_bytes INTEGER DEFAULT 0,
    network_tx_bytes INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id TEXT PRIMARY KEY,
    activity_type TEXT NOT NULL,
    user_id TEXT,
    server_id TEXT,
    app_id TEXT,
    message TEXT NOT NULL,
    details TEXT,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_server_metrics_server ON server_metrics(server_id);
CREATE INDEX IF NOT EXISTS idx_server_metrics_timestamp ON server_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_container_metrics_server ON container_metrics(server_id);
CREATE INDEX IF NOT EXISTS idx_container_metrics_timestamp ON container_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_logs_type ON activity_logs(activity_type);
CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user ON activity_logs(user_id);
"""


def get_metrics_schema() -> str:
    """Return metrics schema SQL."""
    return METRICS_SCHEMA

# Metrics & Monitoring

## Entity Relationship Diagram

```mermaid
erDiagram
    servers {
        TEXT id PK "Server reference"
    }

    server_metrics {
        TEXT id PK "Unique metric identifier"
        TEXT server_id FK "References servers.id"
        REAL cpu_percent "CPU usage percentage"
        REAL memory_percent "Memory usage percentage"
        INTEGER memory_used_mb "Used memory in MB"
        INTEGER memory_total_mb "Total memory in MB"
        REAL disk_percent "Disk usage percentage"
        INTEGER disk_used_gb "Used disk in GB"
        INTEGER disk_total_gb "Total disk in GB"
        INTEGER network_rx_bytes "Network bytes received"
        INTEGER network_tx_bytes "Network bytes transmitted"
        REAL load_average_1m "1-minute load average"
        REAL load_average_5m "5-minute load average"
        REAL load_average_15m "15-minute load average"
        INTEGER uptime_seconds "Server uptime in seconds"
        TEXT timestamp "Metric collection timestamp"
    }

    container_metrics {
        TEXT id PK "Unique metric identifier"
        TEXT server_id FK "References servers.id"
        TEXT container_id "Docker container ID"
        TEXT container_name "Container name"
        REAL cpu_percent "CPU usage percentage"
        INTEGER memory_usage_mb "Memory usage in MB"
        INTEGER memory_limit_mb "Memory limit in MB"
        INTEGER network_rx_bytes "Network bytes received"
        INTEGER network_tx_bytes "Network bytes transmitted"
        TEXT status "Container status"
        TEXT timestamp "Metric collection timestamp"
    }

    servers ||--o{ server_metrics : "monitored by"
    servers ||--o{ container_metrics : "containers on"
```

## Tables

### `server_metrics`
Server resource usage snapshots.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | Metric identifier |
| `server_id` | TEXT | NOT NULL, FK | Server reference |
| `cpu_percent` | REAL | NOT NULL | CPU usage % |
| `memory_percent` | REAL | NOT NULL | Memory usage % |
| `memory_used_mb` | INTEGER | NOT NULL | Used memory (MB) |
| `memory_total_mb` | INTEGER | NOT NULL | Total memory (MB) |
| `disk_percent` | REAL | NOT NULL | Disk usage % |
| `disk_used_gb` | INTEGER | NOT NULL | Used disk (GB) |
| `disk_total_gb` | INTEGER | NOT NULL | Total disk (GB) |
| `network_rx_bytes` | INTEGER | DEFAULT 0 | Bytes received |
| `network_tx_bytes` | INTEGER | DEFAULT 0 | Bytes transmitted |
| `load_average_1m` | REAL | | 1-min load avg |
| `load_average_5m` | REAL | | 5-min load avg |
| `load_average_15m` | REAL | | 15-min load avg |
| `uptime_seconds` | INTEGER | | Server uptime |
| `timestamp` | TEXT | NOT NULL | Collection time |

**Indexes:** `idx_server_metrics_server`, `idx_server_metrics_timestamp`
**Foreign Keys:** `server_id` → `servers(id)` ON DELETE CASCADE

---

### `container_metrics`
Docker container resource usage.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | Metric identifier |
| `server_id` | TEXT | NOT NULL, FK | Server reference |
| `container_id` | TEXT | NOT NULL | Container ID |
| `container_name` | TEXT | NOT NULL | Container name |
| `cpu_percent` | REAL | NOT NULL | CPU usage % |
| `memory_usage_mb` | INTEGER | NOT NULL | Memory usage (MB) |
| `memory_limit_mb` | INTEGER | NOT NULL | Memory limit (MB) |
| `network_rx_bytes` | INTEGER | DEFAULT 0 | Bytes received |
| `network_tx_bytes` | INTEGER | DEFAULT 0 | Bytes transmitted |
| `status` | TEXT | NOT NULL | Container status |
| `timestamp` | TEXT | NOT NULL | Collection time |

**Indexes:** `idx_container_metrics_server`, `idx_container_metrics_timestamp`
**Foreign Keys:** `server_id` → `servers(id)` ON DELETE CASCADE

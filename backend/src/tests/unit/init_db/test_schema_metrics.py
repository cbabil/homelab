"""
Metrics Schema Unit Tests

Tests for schema_metrics.py - SQL schema and getter function.
"""

from init_db.schema_metrics import METRICS_SCHEMA, get_metrics_schema


class TestMetricsSchema:
    """Tests for METRICS_SCHEMA constant."""

    def test_schema_is_string(self):
        """Test that schema is a non-empty string."""
        assert isinstance(METRICS_SCHEMA, str)
        assert len(METRICS_SCHEMA) > 0

    def test_schema_creates_server_metrics_table(self):
        """Test that schema creates server_metrics table."""
        assert "CREATE TABLE IF NOT EXISTS server_metrics" in METRICS_SCHEMA

    def test_schema_creates_container_metrics_table(self):
        """Test that schema creates container_metrics table."""
        assert "CREATE TABLE IF NOT EXISTS container_metrics" in METRICS_SCHEMA

    def test_schema_creates_activity_logs_table(self):
        """Test that schema creates activity_logs table."""
        assert "CREATE TABLE IF NOT EXISTS activity_logs" in METRICS_SCHEMA

    def test_server_metrics_has_required_columns(self):
        """Test that server_metrics has required columns."""
        required_columns = [
            "id TEXT PRIMARY KEY",
            "server_id TEXT NOT NULL",
            "cpu_percent REAL NOT NULL",
            "memory_percent REAL NOT NULL",
            "memory_used_mb INTEGER NOT NULL",
            "memory_total_mb INTEGER NOT NULL",
            "disk_percent REAL NOT NULL",
            "disk_used_gb INTEGER NOT NULL",
            "disk_total_gb INTEGER NOT NULL",
            "timestamp TEXT NOT NULL",
        ]
        for column in required_columns:
            assert column in METRICS_SCHEMA, f"Missing column: {column}"

    def test_container_metrics_has_required_columns(self):
        """Test that container_metrics has required columns."""
        required_columns = [
            "container_id TEXT NOT NULL",
            "container_name TEXT NOT NULL",
            "cpu_percent REAL NOT NULL",
            "memory_usage_mb INTEGER NOT NULL",
            "memory_limit_mb INTEGER NOT NULL",
            "status TEXT NOT NULL",
        ]
        for column in required_columns:
            assert column in METRICS_SCHEMA, f"Missing column: {column}"

    def test_activity_logs_has_required_columns(self):
        """Test that activity_logs has required columns."""
        required_columns = [
            "activity_type TEXT NOT NULL",
            "user_id TEXT",
            "server_id TEXT",
            "app_id TEXT",
            "message TEXT NOT NULL",
        ]
        for column in required_columns:
            assert column in METRICS_SCHEMA, f"Missing column: {column}"

    def test_schema_has_foreign_keys(self):
        """Test that schema has foreign key constraints."""
        assert "FOREIGN KEY (server_id) REFERENCES servers(id)" in METRICS_SCHEMA

    def test_schema_has_indexes(self):
        """Test that schema creates required indexes."""
        indexes = [
            "idx_server_metrics_server",
            "idx_server_metrics_timestamp",
            "idx_container_metrics_server",
            "idx_container_metrics_timestamp",
            "idx_activity_logs_type",
            "idx_activity_logs_timestamp",
            "idx_activity_logs_user",
        ]
        for index in indexes:
            assert index in METRICS_SCHEMA, f"Missing index: {index}"


class TestGetMetricsSchema:
    """Tests for get_metrics_schema function."""

    def test_returns_schema(self):
        """Test that function returns the schema."""
        result = get_metrics_schema()
        assert result == METRICS_SCHEMA

    def test_returns_string(self):
        """Test that function returns a string."""
        result = get_metrics_schema()
        assert isinstance(result, str)

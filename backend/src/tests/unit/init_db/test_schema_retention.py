"""
Retention Schema Unit Tests

Tests for schema_retention.py - SQL schema and retention constraints.
"""

from init_db.schema_retention import SCHEMA, RETENTION_CONSTRAINTS


class TestRetentionSchema:
    """Tests for SCHEMA constant."""

    def test_schema_is_string(self):
        """Test that schema is a non-empty string."""
        assert isinstance(SCHEMA, str)
        assert len(SCHEMA) > 0

    def test_schema_creates_table(self):
        """Test that schema contains CREATE TABLE statement."""
        assert "CREATE TABLE IF NOT EXISTS retention_settings" in SCHEMA

    def test_schema_has_required_columns(self):
        """Test that schema has all required columns."""
        required_columns = [
            "id TEXT PRIMARY KEY",
            "audit_log_retention INTEGER",
            "access_log_retention INTEGER",
            "application_log_retention INTEGER",
            "server_log_retention INTEGER",
            "metrics_retention INTEGER",
            "notification_retention INTEGER",
            "session_retention INTEGER",
            "last_updated TEXT",
            "updated_by_user_id TEXT",
            "created_at TEXT",
        ]
        for column in required_columns:
            assert column in SCHEMA, f"Missing column: {column}"

    def test_schema_has_default_insert(self):
        """Test that schema inserts default values."""
        assert "INSERT OR IGNORE INTO retention_settings" in SCHEMA
        assert "VALUES ('system')" in SCHEMA


class TestRetentionConstraints:
    """Tests for RETENTION_CONSTRAINTS constant."""

    def test_constraints_is_dict(self):
        """Test that constraints is a dictionary."""
        assert isinstance(RETENTION_CONSTRAINTS, dict)

    def test_constraints_has_all_fields(self):
        """Test that all retention fields have constraints."""
        expected_fields = [
            "audit_log_retention",
            "access_log_retention",
            "application_log_retention",
            "server_log_retention",
            "metrics_retention",
            "notification_retention",
            "session_retention",
        ]
        for field in expected_fields:
            assert field in RETENTION_CONSTRAINTS, f"Missing field: {field}"

    def test_constraints_have_required_keys(self):
        """Test that each constraint has min, max, and default."""
        for field, constraint in RETENTION_CONSTRAINTS.items():
            assert "min" in constraint, f"Missing min in {field}"
            assert "max" in constraint, f"Missing max in {field}"
            assert "default" in constraint, f"Missing default in {field}"

    def test_constraints_values_are_valid(self):
        """Test that constraint values are logical."""
        for field, constraint in RETENTION_CONSTRAINTS.items():
            assert constraint["min"] > 0, f"Invalid min in {field}"
            assert constraint["max"] > constraint["min"], f"max <= min in {field}"
            assert constraint["min"] <= constraint["default"] <= constraint["max"], \
                f"default outside range in {field}"

    def test_audit_log_has_longer_retention(self):
        """Test that audit logs have minimum 90 days retention."""
        assert RETENTION_CONSTRAINTS["audit_log_retention"]["min"] >= 90

    def test_session_retention_is_shorter(self):
        """Test that session retention is shorter than log retention."""
        session_max = RETENTION_CONSTRAINTS["session_retention"]["max"]
        audit_min = RETENTION_CONSTRAINTS["audit_log_retention"]["min"]
        assert session_max <= audit_min

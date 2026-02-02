"""
Servers Schema Unit Tests

Tests for schema_servers.py - SQL schema and getter functions.
"""

from init_db.schema_servers import (
    SERVERS_SCHEMA,
    SERVERS_MIGRATION_V2,
    get_servers_schema,
    get_servers_migration_v2,
)


class TestServersSchema:
    """Tests for SERVERS_SCHEMA constant."""

    def test_schema_is_string(self):
        """Test that schema is a non-empty string."""
        assert isinstance(SERVERS_SCHEMA, str)
        assert len(SERVERS_SCHEMA) > 0

    def test_schema_creates_servers_table(self):
        """Test that schema creates servers table."""
        assert "CREATE TABLE IF NOT EXISTS servers" in SERVERS_SCHEMA

    def test_schema_creates_credentials_table(self):
        """Test that schema creates server_credentials table."""
        assert "CREATE TABLE IF NOT EXISTS server_credentials" in SERVERS_SCHEMA

    def test_servers_has_required_columns(self):
        """Test that servers table has required columns."""
        required_columns = [
            "id TEXT PRIMARY KEY",
            "name TEXT NOT NULL",
            "host TEXT NOT NULL",
            "port INTEGER NOT NULL",
            "username TEXT NOT NULL",
            "auth_type TEXT NOT NULL",
            "status TEXT NOT NULL",
            "created_at TEXT NOT NULL",
            "last_connected TEXT",
            "system_info TEXT",
            "docker_installed INTEGER NOT NULL",
        ]
        for column in required_columns:
            assert column in SERVERS_SCHEMA, f"Missing column: {column}"

    def test_servers_has_auth_type_check(self):
        """Test that auth_type has CHECK constraint."""
        assert "CHECK(auth_type IN ('password', 'key'))" in SERVERS_SCHEMA

    def test_servers_has_unique_constraint(self):
        """Test that schema has unique constraint."""
        assert "UNIQUE(host, port, username)" in SERVERS_SCHEMA

    def test_credentials_has_required_columns(self):
        """Test that server_credentials has required columns."""
        required_columns = [
            "server_id TEXT PRIMARY KEY",
            "encrypted_data TEXT NOT NULL",
            "created_at TEXT NOT NULL",
            "updated_at TEXT NOT NULL",
        ]
        for column in required_columns:
            assert column in SERVERS_SCHEMA, f"Missing column: {column}"

    def test_credentials_has_foreign_key(self):
        """Test that credentials has foreign key."""
        assert "FOREIGN KEY (server_id) REFERENCES servers(id)" in SERVERS_SCHEMA

    def test_schema_has_indexes(self):
        """Test that schema creates indexes."""
        indexes = [
            "idx_servers_status",
            "idx_servers_host",
        ]
        for index in indexes:
            assert index in SERVERS_SCHEMA, f"Missing index: {index}"


class TestServersMigrationV2:
    """Tests for SERVERS_MIGRATION_V2 constant."""

    def test_migration_is_string(self):
        """Test that migration is a non-empty string."""
        assert isinstance(SERVERS_MIGRATION_V2, str)
        assert len(SERVERS_MIGRATION_V2) > 0

    def test_migration_creates_temp_table(self):
        """Test that migration creates temporary table."""
        assert "CREATE TABLE IF NOT EXISTS servers_new" in SERVERS_MIGRATION_V2

    def test_migration_copies_data(self):
        """Test that migration copies data from old table."""
        assert "INSERT OR IGNORE INTO servers_new" in SERVERS_MIGRATION_V2
        assert "SELECT" in SERVERS_MIGRATION_V2
        assert "FROM servers" in SERVERS_MIGRATION_V2

    def test_migration_drops_old_table(self):
        """Test that migration drops old table."""
        assert "DROP TABLE IF EXISTS servers" in SERVERS_MIGRATION_V2

    def test_migration_renames_new_table(self):
        """Test that migration renames new table."""
        assert "ALTER TABLE servers_new RENAME TO servers" in SERVERS_MIGRATION_V2

    def test_migration_manages_foreign_keys(self):
        """Test that migration manages foreign keys properly."""
        assert "PRAGMA foreign_keys=off" in SERVERS_MIGRATION_V2
        assert "PRAGMA foreign_keys=on" in SERVERS_MIGRATION_V2

    def test_migration_recreates_indexes(self):
        """Test that migration recreates indexes."""
        indexes = [
            "idx_servers_status",
            "idx_servers_host",
            "idx_servers_docker",
        ]
        for index in indexes:
            assert index in SERVERS_MIGRATION_V2, f"Missing index: {index}"


class TestGetServersSchema:
    """Tests for get_servers_schema function."""

    def test_returns_schema(self):
        """Test that function returns the schema."""
        result = get_servers_schema()
        assert result == SERVERS_SCHEMA

    def test_returns_string(self):
        """Test that function returns a string."""
        result = get_servers_schema()
        assert isinstance(result, str)


class TestGetServersMigrationV2:
    """Tests for get_servers_migration_v2 function."""

    def test_returns_migration(self):
        """Test that function returns the migration."""
        result = get_servers_migration_v2()
        assert result == SERVERS_MIGRATION_V2

    def test_returns_string(self):
        """Test that function returns a string."""
        result = get_servers_migration_v2()
        assert isinstance(result, str)

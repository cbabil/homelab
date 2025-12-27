#!/usr/bin/env python3
"""
Database Initialization Script for Homelab

Creates the unified SQLite database with proper schema for users and logs.
Populates with default admin and user accounts using bcrypt password hashing.
"""

import os
import sqlite3
import sys
import bcrypt
import json
import uuid
from datetime import datetime
from pathlib import Path

# Ensure we can locate the backend src for imports executed by scripts
BACKEND_DIR = Path(__file__).resolve().parent
SRC_DIR = BACKEND_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Database path
DATA_DIRECTORY = Path(os.getenv("DATA_DIRECTORY", "data"))
if not DATA_DIRECTORY.is_absolute():
    DATA_DIRECTORY = (BACKEND_DIR / DATA_DIRECTORY).resolve()
DB_PATH = str((DATA_DIRECTORY / "homelab.db").resolve())

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_database():
    """Create the SQLite database with users and logs tables."""

    # Remove existing database if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing database: {DB_PATH}")

    # Create database connection
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Creating database schema...")

    # Create users table
    cursor.execute("""
    CREATE TABLE users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TEXT NOT NULL,
        last_login TEXT,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        preferences_json TEXT
    )
    """)

    # Create logs table (migrated from existing logs.db)
    cursor.execute("""
    CREATE TABLE logs (
        id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        level TEXT NOT NULL,
        source TEXT NOT NULL,
        message TEXT NOT NULL,
        tags_json TEXT,
        metadata_json TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # Create indexes for users table
    cursor.execute("CREATE INDEX idx_users_username ON users (username)")
    cursor.execute("CREATE INDEX idx_users_email ON users (email)")
    cursor.execute("CREATE INDEX idx_users_role ON users (role)")
    cursor.execute("CREATE INDEX idx_users_active ON users (is_active)")
    cursor.execute("CREATE INDEX idx_users_created_at ON users (created_at)")

    # Create indexes for logs table (performance optimized)
    cursor.execute("CREATE INDEX idx_logs_timestamp ON logs (timestamp)")
    cursor.execute("CREATE INDEX idx_logs_level ON logs (level)")
    cursor.execute("CREATE INDEX idx_logs_source ON logs (source)")
    cursor.execute("CREATE INDEX idx_logs_level_source ON logs (level, source)")
    cursor.execute("CREATE INDEX idx_logs_created_at ON logs (created_at)")
    cursor.execute("CREATE INDEX idx_logs_timestamp_level ON logs (timestamp, level)")

    print("Database schema created successfully!")

    # Create default users
    now = datetime.utcnow().isoformat()

    # Admin user
    admin_id = str(uuid.uuid4())
    admin_preferences = {
        "theme": "dark",
        "language": "en",
        "notifications": True,
        "dashboard_layout": "grid",
        "auto_refresh": True
    }

    cursor.execute("""
    INSERT INTO users (id, username, email, password_hash, role, created_at, last_login, is_active, preferences_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        admin_id,
        "admin",
        "admin@homelab.dev",
        hash_password("HomeLabAdmin123!"),
        "admin",
        now,
        None,
        True,
        json.dumps(admin_preferences)
    ))

    # Regular user
    user_id = str(uuid.uuid4())
    user_preferences = {
        "theme": "light",
        "language": "en",
        "notifications": True,
        "dashboard_layout": "list",
        "auto_refresh": False
    }

    cursor.execute("""
    INSERT INTO users (id, username, email, password_hash, role, created_at, last_login, is_active, preferences_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        "user",
        "user@homelab.dev",
        hash_password("HomeLabUser123!"),
        "user",
        now,
        None,
        True,
        json.dumps(user_preferences)
    ))

    # Create initial log entry
    log_id = str(uuid.uuid4())
    log_metadata = {
        "event_type": "database_initialization",
        "admin_user_id": admin_id,
        "user_user_id": user_id,
        "timestamp": now
    }

    cursor.execute("""
    INSERT INTO logs (id, timestamp, level, source, message, tags_json, metadata_json, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        log_id,
        now,
        "INFO",
        "database_init",
        "Database initialized with default admin and user accounts",
        json.dumps(["initialization", "database", "users", "setup"]),
        json.dumps(log_metadata),
        now
    ))

    conn.commit()
    conn.close()

    print("Default users created successfully!")
    print(f"Admin credentials: admin / HomeLabAdmin123!")
    print(f"User credentials: user / HomeLabUser123!")
    print(f"Database created at: {DB_PATH}")

def migrate_logs():
    """Migrate existing logs from logs.db to homelab.db."""
    old_logs_path = str(DATA_DIRECTORY / "logs.db")

    if not os.path.exists(old_logs_path):
        print("No existing logs.db found to migrate")
        return

    print("Migrating existing logs...")

    # Connect to both databases
    old_conn = sqlite3.connect(old_logs_path)
    new_conn = sqlite3.connect(DB_PATH)

    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()

    # Get all logs from old database
    old_cursor.execute("SELECT id, timestamp, level, source, message, tags, extra_data, created_at FROM log_entries")
    logs = old_cursor.fetchall()

    # Insert into new database with updated schema
    for log in logs:
        log_id, timestamp, level, source, message, tags, extra_data, created_at = log

        # Convert old schema to new schema
        tags_json = tags if tags else json.dumps([])
        metadata_json = extra_data if extra_data else json.dumps({})

        new_cursor.execute("""
        INSERT INTO logs (id, timestamp, level, source, message, tags_json, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (log_id, timestamp, level, source, message, tags_json, metadata_json, created_at))

    new_conn.commit()
    old_conn.close()
    new_conn.close()

    print(f"Migrated {len(logs)} log entries from logs.db")

def verify_database():
    """Verify the database was created correctly."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check users table
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"Users table: {user_count} users")

    # Check logs table
    cursor.execute("SELECT COUNT(*) FROM logs")
    log_count = cursor.fetchone()[0]
    print(f"Logs table: {log_count} log entries")

    # Check indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
    indexes = cursor.fetchall()
    print(f"Indexes created: {len(indexes)}")

    # Display table schemas
    print("\nUsers table schema:")
    cursor.execute("PRAGMA table_info(users)")
    for column in cursor.fetchall():
        print(f"  {column[1]} {column[2]} {'NOT NULL' if column[3] else 'NULL'}")

    print("\nLogs table schema:")
    cursor.execute("PRAGMA table_info(logs)")
    for column in cursor.fetchall():
        print(f"  {column[1]} {column[2]} {'NOT NULL' if column[3] else 'NULL'}")

    conn.close()

if __name__ == "__main__":
    print("Initializing Homelab Database...")
    print("=" * 50)

    create_database()
    migrate_logs()
    verify_database()

    print("\n" + "=" * 50)
    print("Database initialization complete!")
    print(f"Database location: {DB_PATH}")

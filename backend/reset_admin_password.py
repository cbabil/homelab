#!/usr/bin/env python3
"""
Reset admin password to a new value.

Usage:
    python reset_admin_password.py --password "NewSecurePassword123!"
    ADMIN_PASSWORD="NewSecurePassword123!" python reset_admin_password.py
    python reset_admin_password.py  # Interactive prompt
"""

import argparse
import asyncio
import getpass
import os
import sys
import sqlite3

# Add the src directory to the Python path
sys.path.insert(0, 'src')

from lib.auth_helpers import hash_password


def get_password_from_args() -> str:
    """Get password from CLI args, environment, or interactive prompt."""
    parser = argparse.ArgumentParser(description='Reset admin password')
    parser.add_argument(
        '--password', '-p',
        help='New admin password (or use ADMIN_PASSWORD env var)'
    )
    args = parser.parse_args()

    # Priority: CLI arg > env var > interactive prompt
    password = args.password or os.getenv('ADMIN_PASSWORD')

    if not password:
        password = getpass.getpass("Enter new admin password: ")
        confirm = getpass.getpass("Confirm new admin password: ")
        if password != confirm:
            print("[ERROR] Passwords do not match")
            sys.exit(1)

    if not password:
        print("[ERROR] Password is required")
        sys.exit(1)

    if len(password) < 8:
        print("[ERROR] Password must be at least 8 characters")
        sys.exit(1)

    return password


async def reset_admin_password():
    """Reset admin password."""
    print("[INFO] Resetting admin password...")

    new_password = get_password_from_args()

    try:
        # Hash the new password
        hashed_password = hash_password(new_password)

        # Update database
        db_path = "data/tomo.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Update admin password
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE username = 'admin'",
            (hashed_password,)
        )

        if cursor.rowcount > 0:
            print("[SUCCESS] Admin password updated successfully")
        else:
            print("[ERROR] Admin user not found")

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"[ERROR] Error resetting password: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("[INFO] Starting admin password reset...")
    asyncio.run(reset_admin_password())
    print("[INFO] Password reset completed!")

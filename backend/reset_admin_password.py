#!/usr/bin/env python3
"""
Reset admin password to a known value
"""

import asyncio
import sys
import sqlite3

# Add the src directory to the Python path
sys.path.insert(0, 'src')

from lib.auth_helpers import hash_password


async def reset_admin_password():
    """Reset admin password to 'admin123'."""

    print("🔐 Resetting admin password...")

    try:
        # Hash the new password
        new_password = "admin123"
        hashed_password = hash_password(new_password)

        print(f"New password hash: {hashed_password}")

        # Update database
        db_path = "data/homelab.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Update admin password
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE username = 'admin'",
            (hashed_password,)
        )

        if cursor.rowcount > 0:
            print("✅ Admin password updated successfully")
        else:
            print("❌ Admin user not found")

        conn.commit()
        conn.close()

        print(f"Admin password reset to: {new_password}")

    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Resetting admin password...")
    asyncio.run(reset_admin_password())
    print("✅ Password reset completed!")

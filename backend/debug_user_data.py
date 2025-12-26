#!/usr/bin/env python3
"""
Debug script to check user data in the database.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.database_service import DatabaseService

async def check_user_data():
    """Check what user data is actually in the database."""
    print("=== Checking Database User Data ===")

    # Set environment
    os.environ['DATA_DIRECTORY'] = './data'

    # Initialize database service
    db_service = DatabaseService()

    try:
        # Get user
        user = await db_service.get_user_by_username("admin")
        if user:
            print(f"User found:")
            print(f"  ID: {user.id}")
            print(f"  Username: {user.username}")
            print(f"  Email: {user.email}")
            print(f"  Role: {user.role}")
            print(f"  Is Active: {user.is_active}")
            print(f"  Last Login: {user.last_login}")

            # Get password hash
            password_hash = await db_service.get_user_password_hash("admin")
            print(f"  Password Hash: {password_hash[:50] if password_hash else None}...")

        else:
            print("❌ No admin user found in database")

        # List all users
        print("\n=== All Users in Database ===")
        users = await db_service.get_all_users()
        for user in users:
            print(f"Username: {user.username}, Active: {user.is_active}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_user_data())
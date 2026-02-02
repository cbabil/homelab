#!/usr/bin/env python3
"""
Test script to verify the new database-driven authentication system
"""

import asyncio
import sys
from pathlib import Path

# Ensure src directory is on the import path
SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from services.auth_service import AuthService
from services.database_service import DatabaseService
from models.auth import LoginCredentials

async def test_database_authentication():
    """Test the new database-driven authentication service."""
    print("🔍 Testing database-driven authentication system...")

    # Test database service
    db_service = DatabaseService()

    # Test user lookup
    print("\n1. Testing database user lookup...")
    admin_user = await db_service.get_user_by_username("admin")
    if admin_user:
        print(f"✅ Admin user found: {admin_user.username}, role: {admin_user.role}")
    else:
        print("❌ Admin user not found in database!")
        return

    user_user = await db_service.get_user_by_username("user")
    if user_user:
        print(f"✅ User account found: {user_user.username}, role: {user_user.role}")
    else:
        print("❌ User account not found in database!")
        return

    # Test authentication service with database
    print("\n2. Testing authentication service...")
    auth_service = AuthService()

    # Test admin authentication
    admin_creds = LoginCredentials(
        username="admin",
        password="TomoAdmin123!",
        remember_me=False
    )

    print(f"Testing admin login: {admin_creds.username}")
    result = await auth_service.authenticate_user(
        admin_creds,
        client_ip="127.0.0.1",
        user_agent="test-database-client"
    )

    if result:
        print(f"✅ Admin authentication successful!")
        print(f"   User: {result.user.username}")
        print(f"   Role: {result.user.role}")
        print(f"   Token type: {result.token_type}")
        print(f"   Session ID: {result.session_id}")
        print(f"   Token length: {len(result.token)}")
    else:
        print("❌ Admin authentication failed!")
        return

    # Test user authentication
    user_creds = LoginCredentials(
        username="user",
        password="TomoUser123!",
        remember_me=False
    )

    print(f"\nTesting user login: {user_creds.username}")
    result2 = await auth_service.authenticate_user(
        user_creds,
        client_ip="127.0.0.1",
        user_agent="test-database-client"
    )

    if result2:
        print(f"✅ User authentication successful!")
        print(f"   User: {result2.user.username}")
        print(f"   Role: {result2.user.role}")
        print(f"   Session ID: {result2.session_id}")
    else:
        print("❌ User authentication failed!")
        return

    # Test invalid credentials
    print("\n3. Testing invalid credentials...")
    invalid_creds = LoginCredentials(
        username="admin",
        password="wrongpassword",
        remember_me=False
    )

    result3 = await auth_service.authenticate_user(
        invalid_creds,
        client_ip="127.0.0.1",
        user_agent="test-database-client"
    )

    if result3:
        print("❌ Invalid credentials should have failed!")
    else:
        print("✅ Invalid credentials correctly rejected")

    print("\n🎉 Database authentication system is working correctly!")

if __name__ == "__main__":
    asyncio.run(test_database_authentication())

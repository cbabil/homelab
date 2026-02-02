#!/usr/bin/env python3
"""
Test script to directly test authentication service
"""

import asyncio
import sys
from pathlib import Path

# Ensure src directory is on the import path
SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from services.auth_service import AuthService
from models.auth import LoginCredentials

async def test_authentication():
    """Test authentication service directly."""
    print("Testing authentication service...")

    # Initialize auth service
    auth_service = AuthService()

    # Test with admin credentials
    admin_creds = LoginCredentials(
        username="admin",
        password="TomoAdmin123!",
        remember_me=False
    )

    print(f"Testing with admin credentials: {admin_creds.username}")
    print(f"Password length: {len(admin_creds.password)}")

    # Test authentication
    result = await auth_service.authenticate_user(
        admin_creds,
        client_ip="127.0.0.1",
        user_agent="test-client"
    )

    if result:
        print(f"✅ Authentication successful!")
        print(f"User: {result.user.username}")
        print(f"Role: {result.user.role}")
        print(f"Token type: {result.token_type}")
        print(f"Session ID: {result.session_id}")
    else:
        print("❌ Authentication failed!")

        # Debug: Check if user exists
        print(f"Users in database: {list(auth_service.users.keys())}")

        # Debug: Check password hash
        if "admin" in auth_service._user_passwords:
            print("✅ Admin password hash exists")
            # Test password verification directly
            from lib.auth_helpers import verify_password
            stored_hash = auth_service._user_passwords["admin"]
            verification = verify_password("TomoAdmin123!", stored_hash)
            print(f"Direct password verification: {verification}")
        else:
            print("❌ Admin password hash missing")

    # Test with user credentials
    user_creds = LoginCredentials(
        username="user",
        password="TomoUser123!",
        remember_me=False
    )

    print(f"\nTesting with user credentials: {user_creds.username}")
    result2 = await auth_service.authenticate_user(
        user_creds,
        client_ip="127.0.0.1",
        user_agent="test-client"
    )

    if result2:
        print(f"✅ User authentication successful!")
        print(f"User: {result2.user.username}")
        print(f"Role: {result2.user.role}")
    else:
        print("❌ User authentication failed!")

if __name__ == "__main__":
    asyncio.run(test_authentication())

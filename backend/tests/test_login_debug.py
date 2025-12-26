#!/usr/bin/env python3
"""
Debug authentication flow without running full server.
Tests the actual login flow to see what's being returned.
"""

import asyncio
import sys
from pathlib import Path

# Ensure src directory is on the import path
SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from services.auth_service import AuthService
from tools.auth.login_tool import LoginTool
from models.auth import LoginCredentials

async def test_login_flow():
    """Test the complete login flow with verbose logging."""
    print("=== Testing Authentication Flow ===")

    # Initialize services
    print("Initializing AuthService...")
    auth_service = AuthService()

    print("Initializing LoginTool...")
    login_tool = LoginTool(auth_service)

    # Test credentials (using default admin from init_database.py)
    credentials = {
        "username": "admin",
        "password": "HomeLabAdmin123!"
    }

    print(f"Testing login with credentials: {list(credentials.keys())}")

    try:
        # Call login directly
        result = await login_tool.login(credentials)

        print("\n=== Login Result ===")
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message')}")
        if result.get('data'):
            print(f"Has user data: {bool(result['data'].get('user'))}")
            if result['data'].get('user'):
                user_data = result['data']['user']
                print(f"User ID: {user_data.get('id')}")
                print(f"Username: {user_data.get('username')}")
                print(f"Email: {user_data.get('email')}")
                print(f"Role: {user_data.get('role')}")
        else:
            print("No data field in response")

        print(f"Error: {result.get('error')}")

        # Test what frontend expects
        frontend_check = result.get('success') and result.get('data', {}).get('user')
        print(f"\nFrontend check (success && data.user): {frontend_check}")

        return result

    except Exception as e:
        print(f"Exception during login: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Set data directory
    os.environ['DATA_DIRECTORY'] = './data'

    result = asyncio.run(test_login_flow())

    if result:
        print("\n=== Final Assessment ===")
        if result.get('success') and result.get('data', {}).get('user'):
            print("✅ Login flow should work with frontend")
        else:
            print("❌ Login flow will fail with frontend")
            print("Expected: success=True and data.user object")
            print(f"Got: success={result.get('success')}, has_user={bool(result.get('data', {}).get('user'))}")
    else:
        print("\n❌ Login flow failed completely")

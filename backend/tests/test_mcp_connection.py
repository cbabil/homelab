#!/usr/bin/env python3
"""
Test MCP connection and login tool directly
"""

import asyncio
import sys
from pathlib import Path

# Ensure src directory is on the import path
SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from services.auth_service import AuthService
from tools.auth.tools import AuthTools
from models.auth import LoginCredentials


async def test_mcp_login():
    """Test the MCP login functionality directly."""

    # Initialize services
    auth_service = AuthService()
    auth_tools = AuthTools(auth_service)

    print("🔐 Testing MCP login functionality...")

    try:
        # Create mock context
        class MockContext:
            def __init__(self):
                self.meta = {
                    'clientIp': '127.0.0.1',
                    'userAgent': 'Test/1.0'
                }

        mock_ctx = MockContext()

        # Test login with correct credentials
        credentials = {
            "credentials": {
                "username": "admin",
                "password": "admin123"
            }
        }

        print("1. Testing login with admin credentials...")
        result = await auth_tools.login(credentials, mock_ctx)
        print(f"Login result: {result}")

        if result.get('success'):
            print("✅ Login successful!")
            if result.get('data'):
                print(f"User data: {result['data']}")
        else:
            print("❌ Login failed!")

    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Testing MCP login functionality...")
    asyncio.run(test_mcp_login())
    print("✅ MCP login test completed!")

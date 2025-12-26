#!/usr/bin/env python3
"""
Test MCP logout tool directly
"""

import asyncio
import sys
import json
from pathlib import Path

# Ensure src directory is on the import path
SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from services.auth_service import AuthService
from tools.auth_tools import AuthTools
from services.service_log import log_service


async def test_mcp_logout_tool():
    """Test the MCP logout tool functionality."""

    # Initialize services
    auth_service = AuthService()
    auth_tools = AuthTools(auth_service)

    print("🔐 Testing MCP logout tool...")

    try:
        # Test the logout tool directly as it would be called by MCP
        print("\n1. Testing logout tool with username...")

        # This simulates how the MCP framework would call the tool
        result = await auth_tools.logout(
            session_id="web-session-123",
            username="admin"
        )

        print(f"Logout tool result: {json.dumps(result, indent=2)}")

        # Check if log was created
        print("\n2. Checking if logout was logged...")
        all_logs = await log_service.get_logs()
        logout_logs = [log for log in all_logs if "logout" in log.tags and "admin" in log.message]

        print(f"Found {len(logout_logs)} logout logs for admin")
        if logout_logs:
            latest = logout_logs[-1]
            print(f"Latest logout log: {latest.message}")
            print(f"Metadata: {latest.metadata}")

        # Test with missing username
        print("\n3. Testing logout without username (should not log)...")
        result2 = await auth_tools.logout(session_id="web-session-456")
        print(f"Result without username: {json.dumps(result2, indent=2)}")

        # Final log count
        final_logs = await log_service.get_logs()
        final_logout_logs = [log for log in final_logs if "logout" in log.tags]
        print(f"\nTotal logout logs in database: {len(final_logout_logs)}")

    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Testing MCP logout tool directly...")
    asyncio.run(test_mcp_logout_tool())
    print("✅ MCP logout tool test completed!")

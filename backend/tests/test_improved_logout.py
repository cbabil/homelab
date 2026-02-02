#!/usr/bin/env python3
"""
Test improved logout functionality with username parameter
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
from services.service_log import log_service


async def test_improved_logout():
    """Test logout with username parameter."""

    # Initialize services
    auth_service = AuthService()
    auth_tools = AuthTools(auth_service)

    print("🔐 Testing improved logout logging...")

    try:
        # Mock context object
        class MockContext:
            def __init__(self):
                self.meta = {
                    'clientIp': '127.0.0.1',
                    'userAgent': 'Frontend/1.0'
                }

        mock_ctx = MockContext()

        # Test 1: Logout with username (preferred method)
        print("\n1. Testing logout with username parameter...")
        logout_result = await auth_tools.logout(
            session_id="test-session-1",
            username="admin",
            ctx=mock_ctx
        )
        print(f"Logout result: {logout_result}")

        # Test 2: Logout without username (should not log)
        print("\n2. Testing logout without username...")
        logout_result2 = await auth_tools.logout(
            session_id="test-session-2",
            username=None,
            ctx=mock_ctx
        )
        print(f"Logout result: {logout_result2}")

        # Test 3: Logout with session that has user_id
        print("\n3. Testing logout with session containing user_id...")

        # Create a mock session with user_id
        auth_service.sessions["test-session-3"] = {
            "user_id": "2dffa20f-eb98-4b47-a2ae-a4f599c250e0",  # admin user
            "created_at": "2025-09-14T09:41:00Z",
        }

        logout_result3 = await auth_tools.logout(
            session_id="test-session-3",
            ctx=mock_ctx
        )
        print(f"Logout result: {logout_result3}")

        # Verify logout logs
        print("\n4. Verifying logout logs...")
        all_logs = await log_service.get_logs()
        logout_logs = [log for log in all_logs if "logout" in log.tags]

        print(f"Total logout logs: {len(logout_logs)}")

        # Show recent logout logs
        recent_logouts = logout_logs[-3:] if len(logout_logs) >= 3 else logout_logs
        for i, log in enumerate(recent_logouts, 1):
            print(f"  {i}. {log.message} (User: {log.metadata.get('username', 'N/A')})")

    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Running improved logout test...")
    asyncio.run(test_improved_logout())
    print("✅ Improved logout test completed!")

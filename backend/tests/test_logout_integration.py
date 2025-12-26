#!/usr/bin/env python3
"""
Integration test for logout functionality with logging
"""

import asyncio
import sys
from pathlib import Path

# Ensure src directory is on the import path
SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from services.auth_service import AuthService
from tools.auth_tools import AuthTools
from models.auth import LoginCredentials
from services.service_log import log_service


async def test_logout_integration():
    """Test the complete logout flow with logging."""

    # Initialize services
    auth_service = AuthService()
    auth_tools = AuthTools(auth_service)

    print("🔐 Testing logout integration with logging...")

    try:
        # Create a mock session manually for testing logout
        print("1. Creating mock session for logout test...")
        session_id = "test-session-12345"
        user_id = "2dffa20f-eb98-4b47-a2ae-a4f599c250e0"  # admin user ID from database

        # Manually add session to auth service for testing
        auth_service.sessions[session_id] = {
            "user_id": user_id,
            "created_at": "2025-09-14T09:41:00Z",
            "expires_at": "2025-09-14T10:41:00Z"
        }

        print(f"✅ Mock session created, session_id: {session_id}")

        # Mock context object for logout
        class MockContext:
            def __init__(self):
                self.meta = {
                    'clientIp': '127.0.0.1',
                    'userAgent': 'Test-Integration/1.0'
                }

        mock_ctx = MockContext()

        # Test successful logout
        print("\n2. Testing logout with session context...")
        logout_result = await auth_tools.logout(session_id, mock_ctx)

        print(f"Logout result: {logout_result}")

        if logout_result.get('success'):
            print("✅ Logout successful")
        else:
            print("❌ Logout failed")

        # Verify logout logging
        print("\n3. Verifying logout logs were created...")
        all_logs = await log_service.get_logs()
        logout_logs = [log for log in all_logs if "logout" in log.tags]

        print(f"Found {len(logout_logs)} logout log entries")

        # Show recent logout logs
        if logout_logs:
            recent_logout = logout_logs[-1]  # Most recent
            print(f"Most recent logout log:")
            print(f"  ID: {recent_logout.id}")
            print(f"  Message: {recent_logout.message}")
            print(f"  Tags: {recent_logout.tags}")
            print(f"  Success: {recent_logout.metadata.get('success')}")
            print(f"  Username: {recent_logout.metadata.get('username')}")
            print(f"  Client IP: {recent_logout.metadata.get('client_ip')}")

        # Test logout with invalid session
        print("\n4. Testing logout with invalid session...")
        invalid_logout_result = await auth_tools.logout("invalid-session-id", mock_ctx)
        print(f"Invalid logout result: {invalid_logout_result}")

        # Verify both success and failure logout logs
        print("\n5. Final logout log summary...")
        all_logs_final = await log_service.get_logs()
        logout_logs_final = [log for log in all_logs_final if "logout" in log.tags]

        success_logouts = [log for log in logout_logs_final if log.metadata.get('success') is True]
        failed_logouts = [log for log in logout_logs_final if log.metadata.get('success') is False]

        print(f"  ✅ Successful logout logs: {len(success_logouts)}")
        print(f"  ❌ Failed logout logs: {len(failed_logouts)}")

    except Exception as e:
        print(f"❌ Integration test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Running logout integration test...")
    asyncio.run(test_logout_integration())
    print("✅ Logout integration test completed!")

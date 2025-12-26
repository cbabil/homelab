#!/usr/bin/env python3
"""
Test script to create logout log entries and verify they appear in the logs page
"""

import asyncio
import sys
from datetime import datetime
import uuid
from pathlib import Path

# Ensure src directory is on the import path
SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from models.log import LogEntry
from services.service_log import log_service


async def create_test_logout_logs():
    """Create test logout log entries to verify security logging works."""

    # Create a successful logout log
    success_log = LogEntry(
        id=f"sec-{uuid.uuid4().hex[:8]}",
        timestamp=datetime.utcnow(),
        level="INFO",
        source="auth_service",
        message="LOGOUT successful for user: admin",
        tags=["security", "authentication", "logout", "success"],
        metadata={
            "username": "admin",
            "event_type": "LOGOUT",
            "success": True,
            "client_ip": "127.0.0.1",
            "user_agent": "Mozilla/5.0 (Chrome)",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    # Create a failed logout log
    failed_log = LogEntry(
        id=f"sec-{uuid.uuid4().hex[:8]}",
        timestamp=datetime.utcnow(),
        level="WARNING",
        source="auth_service",
        message="LOGOUT failed for user: testuser",
        tags=["security", "authentication", "logout", "failure"],
        metadata={
            "username": "testuser",
            "event_type": "LOGOUT",
            "success": False,
            "client_ip": "192.168.1.100",
            "user_agent": "curl/7.68.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    # Create additional logout logs for different scenarios
    timeout_log = LogEntry(
        id=f"sec-{uuid.uuid4().hex[:8]}",
        timestamp=datetime.utcnow(),
        level="INFO",
        source="auth_service",
        message="LOGOUT successful for user: user1 (session timeout)",
        tags=["security", "authentication", "logout", "success", "timeout"],
        metadata={
            "username": "user1",
            "event_type": "LOGOUT",
            "success": True,
            "client_ip": "10.0.0.5",
            "user_agent": "Mozilla/5.0 (Safari)",
            "logout_reason": "session_timeout",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    try:
        # Create the log entries
        await log_service.create_log_entry(success_log)
        print(f"✅ Created successful logout log: {success_log.id}")

        await log_service.create_log_entry(failed_log)
        print(f"✅ Created failed logout log: {failed_log.id}")

        await log_service.create_log_entry(timeout_log)
        print(f"✅ Created timeout logout log: {timeout_log.id}")

        # Retrieve all logs to verify
        all_logs = await log_service.get_logs()
        print(f"\n📊 Total logs in database: {len(all_logs)}")

        # Filter security logs
        security_logs = [log for log in all_logs if "security" in log.tags]
        print(f"🔐 Security logs: {len(security_logs)}")

        # Filter logout-specific logs
        logout_logs = [log for log in security_logs if "logout" in log.tags]
        print(f"🚪 Logout logs: {len(logout_logs)}")

        print("\n🔍 Recent logout logs:")
        for log in logout_logs[-3:]:  # Show last 3
            print(f"  - {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{log.level}] {log.message}")

        # Show breakdown by success/failure
        success_logouts = [log for log in logout_logs if log.metadata.get('success') is True]
        failed_logouts = [log for log in logout_logs if log.metadata.get('success') is False]

        print(f"\n📈 Logout statistics:")
        print(f"  ✅ Successful logouts: {len(success_logouts)}")
        print(f"  ❌ Failed logouts: {len(failed_logouts)}")

    except Exception as e:
        print(f"❌ Error creating test logs: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚪 Creating test logout log entries...")
    asyncio.run(create_test_logout_logs())
    print("✅ Test logout logs created successfully!")

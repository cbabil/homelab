#!/usr/bin/env python3
"""
Test script to create login log entries and verify they appear in the logs page
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


async def create_test_login_logs():
    """Create test login log entries to verify security logging works."""

    # Create a successful login log
    success_log = LogEntry(
        id=f"sec-{uuid.uuid4().hex[:8]}",
        timestamp=datetime.utcnow(),
        level="INFO",
        source="auth_service",
        message="LOGIN successful for user: admin",
        tags=["security", "authentication", "login", "success"],
        metadata={
            "username": "admin",
            "event_type": "LOGIN",
            "success": True,
            "client_ip": "127.0.0.1",
            "user_agent": "Mozilla/5.0 (Chrome)",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    # Create a failed login log
    failed_log = LogEntry(
        id=f"sec-{uuid.uuid4().hex[:8]}",
        timestamp=datetime.utcnow(),
        level="WARNING",
        source="auth_service",
        message="LOGIN failed for user: baduser",
        tags=["security", "authentication", "login", "failure"],
        metadata={
            "username": "baduser",
            "event_type": "LOGIN",
            "success": False,
            "client_ip": "192.168.1.100",
            "user_agent": "curl/7.68.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    # Create additional security logs for testing
    session_log = LogEntry(
        id=f"sec-{uuid.uuid4().hex[:8]}",
        timestamp=datetime.utcnow(),
        level="INFO",
        source="auth_service",
        message="Session created for user: admin",
        tags=["security", "session", "creation"],
        metadata={
            "username": "admin",
            "event_type": "SESSION_CREATE",
            "success": True,
            "session_id": "abc123-def456",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    try:
        # Create the log entries
        await log_service.create_log_entry(success_log)
        print(f"✅ Created successful login log: {success_log.id}")

        await log_service.create_log_entry(failed_log)
        print(f"✅ Created failed login log: {failed_log.id}")

        await log_service.create_log_entry(session_log)
        print(f"✅ Created session log: {session_log.id}")

        # Retrieve all logs to verify
        all_logs = await log_service.get_logs()
        print(f"\n📊 Total logs in database: {len(all_logs)}")

        # Filter security logs
        security_logs = [log for log in all_logs if "security" in log.tags]
        print(f"🔐 Security logs: {len(security_logs)}")

        print("\n🔍 Recent security logs:")
        for log in security_logs[-3:]:  # Show last 3
            print(f"  - {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{log.level}] {log.message}")

    except Exception as e:
        print(f"❌ Error creating test logs: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Creating test login log entries...")
    asyncio.run(create_test_login_logs())
    print("✅ Test login logs created successfully!")

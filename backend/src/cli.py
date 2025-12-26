#!/usr/bin/env python3
"""
Homelab Assistant CLI

Provides command-line utilities for administration tasks.
"""

import argparse
import asyncio
import sys
import getpass
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from services.database_service import DatabaseService
from models.auth import UserRole
from lib.auth_helpers import hash_password
from lib.config import load_config, resolve_data_directory


async def create_admin_user(
    username: str,
    email: str,
    password: str,
    data_directory: str = None
) -> bool:
    """Create the initial admin user."""
    try:
        config = load_config()
        data_dir = data_directory or resolve_data_directory(config)

        db_service = DatabaseService(data_directory=data_dir)

        # Check if user already exists
        existing = await db_service.get_user_by_username(username)
        if existing:
            print(f"Error: User '{username}' already exists")
            return False

        # Create admin user
        password_hash = hash_password(password)
        user = await db_service.create_user(
            username=username,
            email=email,
            password_hash=password_hash,
            role=UserRole.ADMIN
        )

        if user:
            print(f"Admin user '{username}' created successfully")
            return True
        else:
            print("Error: Failed to create admin user")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Homelab Assistant CLI",
        prog="homelab-assistant"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # create-admin command
    admin_parser = subparsers.add_parser(
        "create-admin",
        help="Create the initial admin user"
    )
    admin_parser.add_argument(
        "--username", "-u",
        required=True,
        help="Admin username"
    )
    admin_parser.add_argument(
        "--email", "-e",
        required=True,
        help="Admin email address"
    )
    admin_parser.add_argument(
        "--password", "-p",
        help="Admin password (will prompt if not provided)"
    )
    admin_parser.add_argument(
        "--data-dir", "-d",
        help="Data directory path"
    )

    args = parser.parse_args()

    if args.command == "create-admin":
        password = args.password
        if not password:
            password = getpass.getpass("Enter admin password: ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Error: Passwords do not match")
                sys.exit(1)

        success = asyncio.run(create_admin_user(
            username=args.username,
            email=args.email,
            password=password,
            data_directory=args.data_dir
        ))
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

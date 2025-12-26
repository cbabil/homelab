#!/usr/bin/env python3
"""
Homelab Assistant CLI

Provides command-line utilities for administration tasks.
"""

import argparse
import asyncio
import sys
import getpass
import os
from pathlib import Path
import click

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


def get_backup_service():
    """Get backup service instance with database service."""
    from services.backup_service import BackupService

    config = load_config()
    data_dir = resolve_data_directory(config)
    db_service = DatabaseService(data_directory=data_dir)
    return BackupService(db_service=db_service)


@click.command()
@click.option('--output', '-o', required=True, help='Output file path')
@click.option('--password', '-p', prompt=True, hide_input=True,
              confirmation_prompt=True, help='Encryption password')
def export_backup(output: str, password: str):
    """Export encrypted backup of all data."""
    backup_service = get_backup_service()

    async def do_export():
        return await backup_service.export_backup(output, password)

    result = asyncio.run(do_export())

    if result["success"]:
        click.echo(f"Backup exported successfully to {result['path']}")
        click.echo(f"Checksum: {result['checksum']}")
    else:
        click.echo(f"Export failed: {result['error']}", err=True)
        raise SystemExit(1)


@click.command()
@click.option('--input', '-i', 'input_path', required=True, help='Input file path')
@click.option('--password', '-p', prompt=True, hide_input=True, help='Decryption password')
@click.option('--overwrite', is_flag=True, help='Overwrite existing data')
def import_backup(input_path: str, password: str, overwrite: bool):
    """Import backup from encrypted file."""
    if not os.path.exists(input_path):
        click.echo(f"File not found: {input_path}", err=True)
        raise SystemExit(1)

    backup_service = get_backup_service()

    async def do_import():
        return await backup_service.import_backup(input_path, password, overwrite)

    result = asyncio.run(do_import())

    if result["success"]:
        click.echo(f"Backup imported successfully")
        click.echo(f"Users imported: {result['users_imported']}")
        click.echo(f"Servers imported: {result['servers_imported']}")
    else:
        click.echo(f"Import failed: {result['error']}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

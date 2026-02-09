"""
Settings Audit Service

Handles audit trail retrieval and settings reset operations
(user and system) for the settings management system.
"""

from contextlib import asynccontextmanager
from datetime import UTC, datetime

import aiosqlite
import structlog

from models.auth import UserRole
from models.settings import (
    ChangeType,
    SettingCategory,
    SettingsAuditEntry,
    SettingsResponse,
)
from services.database_service import DatabaseService

logger = structlog.get_logger("settings_audit")


class SettingsAuditService:
    """Service for settings audit trail and reset operations."""

    def __init__(self, db_service: DatabaseService) -> None:
        """Initialize audit service with database dependency.

        Args:
            db_service: Shared database service instance.
        """
        self.db_service = db_service

    @asynccontextmanager
    async def get_connection(self):
        """Get secure database connection with automatic cleanup."""
        async with self.db_service.get_connection() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    async def verify_admin_access(self, user_id: str) -> bool:
        """Verify user has admin privileges for protected operations."""
        try:
            user = await self.db_service.get_user_by_id(user_id)
            if not user:
                logger.warning(
                    "Admin verification failed - user not found",
                    user_id=user_id,
                )
                return False

            if user.role != UserRole.ADMIN:
                logger.warning(
                    "Admin verification failed - insufficient privileges",
                    user_id=user_id,
                    role=user.role,
                )
                return False

            logger.debug("Admin access verified", user_id=user_id)
            return True

        except Exception as e:
            logger.error(
                "Admin verification error", user_id=user_id, error=str(e)
            )
            return False

    async def _create_audit_entry(
        self,
        connection: aiosqlite.Connection,
        table_name: str,
        record_id: int,
        user_id: str | None,
        setting_key: str,
        old_value: str | None,
        new_value: str,
        change_type: ChangeType,
        change_reason: str | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> int:
        """Create audit entry with integrity protection."""
        try:
            audit_entry = SettingsAuditEntry(
                table_name=table_name,
                record_id=record_id,
                user_id=user_id,
                setting_key=setting_key,
                old_value=old_value,
                new_value=new_value,
                change_type=change_type,
                change_reason=change_reason,
                client_ip=client_ip,
                user_agent=user_agent,
                created_at=datetime.now(UTC).isoformat(),
            )

            checksum = audit_entry.generate_checksum()

            cursor = await connection.execute(
                """
                INSERT INTO settings_audit (
                    table_name, record_id, user_id, setting_key,
                    old_value, new_value, change_type, change_reason,
                    client_ip, user_agent, created_at, checksum
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_entry.table_name,
                    audit_entry.record_id,
                    audit_entry.user_id,
                    audit_entry.setting_key,
                    audit_entry.old_value,
                    audit_entry.new_value,
                    audit_entry.change_type.value,
                    audit_entry.change_reason,
                    audit_entry.client_ip,
                    audit_entry.user_agent,
                    audit_entry.created_at,
                    checksum,
                ),
            )

            audit_id = cursor.lastrowid
            logger.debug(
                "Audit entry created with integrity protection",
                audit_id=audit_id,
                setting_key=setting_key,
                change_type=change_type,
                checksum=checksum[:16],
            )

            return audit_id

        except Exception as e:
            logger.error(
                "Failed to create audit entry",
                error=str(e),
                setting_key=setting_key,
                change_type=change_type,
            )
            raise

    async def get_settings_audit(
        self,
        user_id: str,
        setting_key: str | None = None,
        filter_user_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> SettingsResponse:
        """Get settings audit trail with admin verification.

        Args:
            user_id: Authenticated user ID (for admin verification)
            setting_key: Filter by specific setting key
            filter_user_id: Filter by user who made the changes
            limit: Maximum entries to return
            offset: Number of entries to skip (for pagination)
        """
        try:
            is_admin = await self.verify_admin_access(user_id)
            if not is_admin:
                return SettingsResponse(
                    success=False,
                    message="Admin privileges required to access audit logs",
                    error="ADMIN_REQUIRED",
                )

            async with self.get_connection() as conn:
                query_parts = [
                    "SELECT id, table_name, record_id, user_id, setting_key,",
                    "old_value, new_value, change_type, change_reason,",
                    "client_ip, user_agent, created_at, checksum",
                    "FROM settings_audit",
                    "WHERE 1=1",
                ]
                params: list = []

                if setting_key:
                    query_parts.append("AND setting_key = ?")
                    params.append(setting_key)

                if filter_user_id:
                    query_parts.append("AND user_id = ?")
                    params.append(filter_user_id)

                query_parts.extend(
                    ["ORDER BY created_at DESC", "LIMIT ? OFFSET ?"]
                )
                params.extend([limit, offset])

                query = " ".join(query_parts)

                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()

                audit_entries = []
                for row in rows:
                    audit_entries.append(
                        {
                            "id": row["id"],
                            "table_name": row["table_name"],
                            "record_id": row["record_id"],
                            "user_id": row["user_id"],
                            "setting_key": row["setting_key"],
                            "old_value": row["old_value"],
                            "new_value": row["new_value"],
                            "change_type": row["change_type"],
                            "change_reason": row["change_reason"],
                            "client_ip": row["client_ip"],
                            "user_agent": row["user_agent"],
                            "created_at": row["created_at"],
                            "checksum": row["checksum"],
                        }
                    )

            response = SettingsResponse(
                success=True,
                message=f"Retrieved {len(audit_entries)} audit entries",
                data={"audit_entries": audit_entries},
            )

            logger.info(
                "Settings audit retrieved successfully",
                user_id=user_id,
                count=len(audit_entries),
            )

            return response

        except Exception as e:
            logger.error(
                "Failed to get settings audit",
                user_id=user_id,
                error=str(e),
            )
            return SettingsResponse(
                success=False,
                message=f"Failed to get settings audit: {str(e)}",
                error="AUDIT_ERROR",
            )

    async def reset_user_settings(
        self,
        user_id: str,
        category: SettingCategory | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> SettingsResponse:
        """Reset user settings by deleting overrides, falling back to system defaults."""
        try:
            logger.info(
                "Resetting user settings",
                user_id=user_id,
                category=category,
            )

            async with self.get_connection() as conn:
                await conn.execute("BEGIN IMMEDIATE")

                try:
                    if category:
                        cursor = await conn.execute(
                            """
                            SELECT id, setting_key, setting_value
                            FROM user_settings
                            WHERE user_id = ? AND category = ?
                            """,
                            (user_id, category.value),
                        )
                    else:
                        cursor = await conn.execute(
                            """
                            SELECT id, setting_key, setting_value
                            FROM user_settings
                            WHERE user_id = ?
                            """,
                            (user_id,),
                        )

                    rows = await cursor.fetchall()
                    deleted_count = 0

                    for row in rows:
                        await self._create_audit_entry(
                            conn,
                            "user_settings",
                            row["id"],
                            user_id,
                            row["setting_key"],
                            row["setting_value"],
                            '""',
                            ChangeType.DELETE,
                            "User settings reset to defaults",
                            client_ip,
                            user_agent,
                        )
                        deleted_count += 1

                    if category:
                        await conn.execute(
                            "DELETE FROM user_settings WHERE user_id = ? AND category = ?",
                            (user_id, category.value),
                        )
                    else:
                        await conn.execute(
                            "DELETE FROM user_settings WHERE user_id = ?",
                            (user_id,),
                        )

                    await conn.commit()

                    response = SettingsResponse(
                        success=True,
                        message=f"Reset {deleted_count} user settings to defaults",
                        data={
                            "deleted_count": deleted_count,
                            "user_id": user_id,
                        },
                    )
                    response.checksum = response.generate_checksum()

                    logger.info(
                        "User settings reset successfully",
                        user_id=user_id,
                        deleted_count=deleted_count,
                    )

                    return response

                except Exception as e:
                    await conn.rollback()
                    logger.error(
                        "User settings reset failed, rolled back",
                        user_id=user_id,
                        error=str(e),
                    )
                    raise

        except Exception as e:
            logger.error(
                "Failed to reset user settings",
                user_id=user_id,
                error=str(e),
            )
            return SettingsResponse(
                success=False,
                message=f"Failed to reset user settings: {str(e)}",
                error="RESET_USER_SETTINGS_ERROR",
            )

    async def reset_system_settings(
        self,
        user_id: str,
        category: SettingCategory | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> SettingsResponse:
        """Reset system settings to factory defaults (admin only).

        Copies default_value to setting_value for all matching settings.
        """
        try:
            is_admin = await self.verify_admin_access(user_id)
            if not is_admin:
                return SettingsResponse(
                    success=False,
                    message="Admin privileges required to reset system settings",
                    error="ADMIN_REQUIRED",
                )

            logger.info(
                "Resetting system settings to defaults",
                user_id=user_id,
                category=category,
            )

            async with self.get_connection() as conn:
                await conn.execute("BEGIN IMMEDIATE")

                try:
                    if category:
                        cursor = await conn.execute(
                            """
                            SELECT id, setting_key, setting_value, default_value
                            FROM system_settings
                            WHERE category = ? AND setting_value != default_value
                            """,
                            (category.value,),
                        )
                    else:
                        cursor = await conn.execute(
                            """
                            SELECT id, setting_key, setting_value, default_value
                            FROM system_settings
                            WHERE setting_value != default_value
                            """
                        )

                    rows = await cursor.fetchall()
                    reset_count = 0
                    now = datetime.now(UTC).isoformat()

                    for row in rows:
                        await self._create_audit_entry(
                            conn,
                            "system_settings",
                            row["id"],
                            user_id,
                            row["setting_key"],
                            row["setting_value"],
                            row["default_value"],
                            ChangeType.UPDATE,
                            "System setting reset to factory default",
                            client_ip,
                            user_agent,
                        )

                        await conn.execute(
                            """
                            UPDATE system_settings
                            SET setting_value = default_value,
                                updated_at = ?,
                                updated_by = ?,
                                version = version + 1
                            WHERE id = ?
                            """,
                            (now, user_id, row["id"]),
                        )
                        reset_count += 1

                    await conn.commit()

                    response = SettingsResponse(
                        success=True,
                        message=f"Reset {reset_count} system settings to factory defaults",
                        data={"reset_count": reset_count},
                    )
                    response.checksum = response.generate_checksum()

                    logger.info(
                        "System settings reset successfully",
                        user_id=user_id,
                        reset_count=reset_count,
                    )

                    return response

                except Exception as e:
                    await conn.rollback()
                    logger.error(
                        "System settings reset failed, rolled back",
                        user_id=user_id,
                        error=str(e),
                    )
                    raise

        except Exception as e:
            logger.error(
                "Failed to reset system settings",
                user_id=user_id,
                error=str(e),
            )
            return SettingsResponse(
                success=False,
                message=f"Failed to reset system settings: {str(e)}",
                error="RESET_SYSTEM_SETTINGS_ERROR",
            )

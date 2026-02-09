"""
Settings Service with Enhanced Security

Comprehensive settings management service with parameterized queries,
audit trail protection, and security controls addressing all identified vulnerabilities.
"""

import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import aiosqlite
import structlog

from models.auth import UserRole
from models.settings import (
    ChangeType,
    SettingCategory,
    SettingDataType,
    SettingsAuditEntry,
    SettingScope,
    SettingsRequest,
    SettingsResponse,
    SettingsUpdateRequest,
    SettingsValidationResult,
    SettingValue,
    SystemSetting,
    UserSetting,
)
from services.database_service import DatabaseService
from services.settings_audit import SettingsAuditService
from services.settings_schema import SettingsSchemaService

logger = structlog.get_logger("settings_service")


class SettingsService:
    """Secure settings management service with comprehensive security controls."""

    def __init__(self, db_service: DatabaseService | None = None):
        """Initialize settings service with database dependency."""
        self.db_service = db_service or DatabaseService()
        self._audit_service = SettingsAuditService(self.db_service)
        self._schema_service = SettingsSchemaService(self.db_service)
        logger.info("Settings service initialized with security controls")

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
                    "Admin verification failed - user not found", user_id=user_id
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
            logger.error("Admin verification error", user_id=user_id, error=str(e))
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
        """Create audit entry with integrity protection - SECURE parameterized queries."""
        try:
            # Create audit entry model for validation
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

            # Generate integrity checksum
            checksum = audit_entry.generate_checksum()

            # SECURE: Use parameterized query to prevent SQL injection
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

    async def _validate_setting_value(
        self, setting_key: str, value: Any, system_setting: SystemSetting | None = None
    ) -> SettingValue:
        """Validate setting value with runtime validation and sanitization."""
        try:
            # Get system setting for validation rules if not provided
            if not system_setting:
                system_setting = await self.get_system_setting(setting_key)
                if not system_setting:
                    raise ValueError(f"System setting not found: {setting_key}")

            # Create JSON-encoded value
            json_value = json.dumps(value)

            # Create SettingValue with type validation
            setting_value = SettingValue(
                raw_value=json_value, data_type=system_setting.data_type
            )

            # Additional validation against JSON schema if provided
            if system_setting.validation_rules:
                try:
                    import jsonschema

                    schema = json.loads(system_setting.validation_rules)
                    jsonschema.validate(value, schema)
                except ImportError:
                    logger.warning("jsonschema not available for advanced validation")
                except Exception as validation_error:
                    raise ValueError(f"Value validation failed: {validation_error}")

            return setting_value

        except Exception as e:
            logger.error(
                "Setting value validation failed", setting_key=setting_key, error=str(e)
            )
            raise

    async def get_system_setting(self, setting_key: str) -> SystemSetting | None:
        """Get system setting by key with secure parameterized query."""
        try:
            async with self.get_connection() as conn:
                # SECURE: Use parameterized query to prevent SQL injection
                cursor = await conn.execute(
                    """
                    SELECT id, setting_key, setting_value, default_value, category, scope, data_type,
                           is_admin_only, description, validation_rules, created_at,
                           updated_at, updated_by, version
                    FROM system_settings
                    WHERE setting_key = ?
                    """,
                    (setting_key,),
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                data_type = SettingDataType(row["data_type"])

                # Create SettingValue with validation
                setting_value = SettingValue(
                    raw_value=row["setting_value"], data_type=data_type
                )

                # Create default SettingValue
                default_value = SettingValue(
                    raw_value=row["default_value"], data_type=data_type
                )

                return SystemSetting(
                    id=row["id"],
                    setting_key=row["setting_key"],
                    setting_value=setting_value,
                    default_value=default_value,
                    category=SettingCategory(row["category"]),
                    scope=SettingScope(row["scope"]),
                    data_type=data_type,
                    is_admin_only=bool(row["is_admin_only"]),
                    description=row["description"],
                    validation_rules=row["validation_rules"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    updated_by=row["updated_by"],
                    version=row["version"],
                )

        except Exception as e:
            logger.error(
                "Failed to get system setting", setting_key=setting_key, error=str(e)
            )
            return None

    async def get_user_setting(
        self, user_id: str, setting_key: str
    ) -> UserSetting | None:
        """Get user setting by key with secure parameterized query."""
        try:
            async with self.get_connection() as conn:
                # SECURE: Use parameterized query to prevent SQL injection
                cursor = await conn.execute(
                    """
                    SELECT id, user_id, setting_key, setting_value, category,
                           is_override, created_at, updated_at, version
                    FROM user_settings
                    WHERE user_id = ? AND setting_key = ?
                    """,
                    (user_id, setting_key),
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                # Get system setting for data type
                system_setting = await self.get_system_setting(setting_key)
                if not system_setting:
                    logger.warning(
                        "User setting exists but no system setting found",
                        user_id=user_id,
                        setting_key=setting_key,
                    )
                    return None

                # Create SettingValue with validation
                setting_value = SettingValue(
                    raw_value=row["setting_value"], data_type=system_setting.data_type
                )

                return UserSetting(
                    id=row["id"],
                    user_id=row["user_id"],
                    setting_key=row["setting_key"],
                    setting_value=setting_value,
                    category=SettingCategory(row["category"]),
                    is_override=bool(row["is_override"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    version=row["version"],
                )

        except Exception as e:
            logger.error(
                "Failed to get user setting",
                user_id=user_id,
                setting_key=setting_key,
                error=str(e),
            )
            return None

    async def get_settings(self, request: SettingsRequest) -> SettingsResponse:
        """Get settings with security validation and permission checks."""
        try:
            logger.info(
                "Getting settings",
                user_id=request.user_id,
                category=request.category,
                keys=request.setting_keys,
            )

            settings = {}

            async with self.get_connection() as conn:
                # Build secure parameterized query for system settings
                if request.include_system_defaults:
                    query_parts = [
                        "SELECT setting_key, setting_value, category, scope, data_type, is_admin_only",
                        "FROM system_settings",
                        "WHERE 1=1",
                    ]
                    params = []

                    if request.category:
                        query_parts.append("AND category = ?")
                        params.append(request.category.value)

                    if request.setting_keys:
                        placeholders = ",".join("?" * len(request.setting_keys))
                        query_parts.append(f"AND setting_key IN ({placeholders})")
                        params.extend(request.setting_keys)

                    query = " ".join(query_parts)

                    # SECURE: Use parameterized query
                    cursor = await conn.execute(query, params)
                    rows = await cursor.fetchall()

                    for row in rows:
                        # Check admin-only permissions
                        if row["is_admin_only"]:
                            is_admin = await self.verify_admin_access(request.user_id)
                            if not is_admin:
                                continue

                        try:
                            setting_value = SettingValue(
                                raw_value=row["setting_value"],
                                data_type=SettingDataType(row["data_type"]),
                            )
                            settings[row["setting_key"]] = {
                                "value": setting_value.get_parsed_value(),
                                "category": row["category"],
                                "scope": row["scope"],
                                "data_type": row["data_type"],
                                "is_admin_only": bool(row["is_admin_only"]),
                                "source": "system",
                            }
                        except Exception as e:
                            logger.warning(
                                "Invalid system setting value",
                                setting_key=row["setting_key"],
                                error=str(e),
                            )

                # Get user overrides
                if request.include_user_overrides:
                    query_parts = [
                        "SELECT us.setting_key, us.setting_value, us.category, ss.data_type",
                        "FROM user_settings us",
                        "JOIN system_settings ss ON us.setting_key = ss.setting_key",
                        "WHERE us.user_id = ?",
                    ]
                    params = [request.user_id]

                    if request.category:
                        query_parts.append("AND us.category = ?")
                        params.append(request.category.value)

                    if request.setting_keys:
                        placeholders = ",".join("?" * len(request.setting_keys))
                        query_parts.append(f"AND us.setting_key IN ({placeholders})")
                        params.extend(request.setting_keys)

                    query = " ".join(query_parts)

                    # SECURE: Use parameterized query
                    cursor = await conn.execute(query, params)
                    rows = await cursor.fetchall()

                    for row in rows:
                        try:
                            setting_value = SettingValue(
                                raw_value=row["setting_value"],
                                data_type=SettingDataType(row["data_type"]),
                            )
                            settings[row["setting_key"]] = {
                                "value": setting_value.get_parsed_value(),
                                "category": row["category"],
                                "data_type": row["data_type"],
                                "source": "user_override",
                            }
                        except Exception as e:
                            logger.warning(
                                "Invalid user setting value",
                                setting_key=row["setting_key"],
                                error=str(e),
                            )

            response = SettingsResponse(
                success=True,
                message=f"Retrieved {len(settings)} settings",
                data={"settings": settings},
            )
            response.checksum = response.generate_checksum()

            logger.info(
                "Settings retrieved successfully",
                user_id=request.user_id,
                count=len(settings),
            )

            return response

        except Exception as e:
            logger.error(
                "Failed to get settings", user_id=request.user_id, error=str(e)
            )
            return SettingsResponse(
                success=False,
                message=f"Failed to get settings: {str(e)}",
                error="GET_SETTINGS_ERROR",
            )

    async def update_settings(self, request: SettingsUpdateRequest) -> SettingsResponse:
        """Update settings with comprehensive security validation and audit trail."""
        try:
            logger.info(
                "Updating settings",
                user_id=request.user_id,
                setting_count=len(request.settings),
            )

            # Validate all settings first
            validation_result = await self.validate_settings(
                request.settings, request.user_id
            )
            if not validation_result.is_valid:
                return SettingsResponse(
                    success=False,
                    message="Settings validation failed",
                    data={
                        "validation_errors": validation_result.errors,
                        "security_violations": validation_result.security_violations,
                    },
                    error="VALIDATION_ERROR",
                )

            # Check admin privileges for admin-only settings
            admin_required_settings = validation_result.admin_required
            if admin_required_settings:
                is_admin = await self.verify_admin_access(request.user_id)
                if not is_admin:
                    return SettingsResponse(
                        success=False,
                        message="Admin privileges required for some settings",
                        data={"admin_required_settings": admin_required_settings},
                        error="ADMIN_REQUIRED",
                    )

            updated_settings = {}
            audit_ids = []

            async with self.get_connection() as conn:
                await conn.execute("BEGIN IMMEDIATE")

                try:
                    for (
                        setting_key,
                        value,
                    ) in validation_result.validated_settings.items():
                        audit_id = await self._update_single_setting(
                            conn,
                            request.user_id,
                            setting_key,
                            value,
                            request.change_reason,
                            request.client_ip,
                            request.user_agent,
                        )
                        if audit_id:
                            audit_ids.append(audit_id)
                            updated_settings[setting_key] = value

                    await conn.commit()

                    response = SettingsResponse(
                        success=True,
                        message=f"Updated {len(updated_settings)} settings",
                        data={
                            "updated_settings": updated_settings,
                            "audit_ids": audit_ids,
                        },
                    )
                    response.checksum = response.generate_checksum()

                    logger.info(
                        "Settings updated successfully",
                        user_id=request.user_id,
                        count=len(updated_settings),
                    )

                    return response

                except Exception as e:
                    await conn.rollback()
                    logger.error(
                        "Settings update failed, rolled back transaction",
                        user_id=request.user_id,
                        error=str(e),
                    )
                    raise

        except Exception as e:
            logger.error(
                "Failed to update settings", user_id=request.user_id, error=str(e)
            )
            return SettingsResponse(
                success=False,
                message=f"Failed to update settings: {str(e)}",
                error="UPDATE_SETTINGS_ERROR",
            )

    async def _update_single_setting(
        self,
        conn: aiosqlite.Connection,
        user_id: str,
        setting_key: str,
        value: Any,
        change_reason: str | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> int | None:
        """Update a single setting with audit trail - SECURE parameterized queries."""
        try:
            # Get system setting for validation
            system_setting = await self.get_system_setting(setting_key)
            if not system_setting:
                raise ValueError(f"System setting not found: {setting_key}")

            # Validate the value
            setting_value = await self._validate_setting_value(
                setting_key, value, system_setting
            )

            # Check if user setting exists
            existing_user_setting = await self.get_user_setting(user_id, setting_key)

            if existing_user_setting:
                # Update existing user setting
                old_value = existing_user_setting.setting_value.raw_value

                # SECURE: Use parameterized query
                await conn.execute(
                    """
                    UPDATE user_settings
                    SET setting_value = ?, updated_at = ?, version = version + 1
                    WHERE user_id = ? AND setting_key = ?
                    """,
                    (
                        setting_value.raw_value,
                        datetime.now(UTC).isoformat(),
                        user_id,
                        setting_key,
                    ),
                )

                # Create audit entry
                audit_id = await self._create_audit_entry(
                    conn,
                    "user_settings",
                    existing_user_setting.id,
                    user_id,
                    setting_key,
                    old_value,
                    setting_value.raw_value,
                    ChangeType.UPDATE,
                    change_reason,
                    client_ip,
                    user_agent,
                )

            else:
                # Create new user setting override
                # SECURE: Use parameterized query
                cursor = await conn.execute(
                    """
                    INSERT INTO user_settings (
                        user_id, setting_key, setting_value, category, is_override,
                        created_at, updated_at, version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        setting_key,
                        setting_value.raw_value,
                        system_setting.category.value,
                        True,
                        datetime.now(UTC).isoformat(),
                        datetime.now(UTC).isoformat(),
                        1,
                    ),
                )

                record_id = cursor.lastrowid

                # Create audit entry
                audit_id = await self._create_audit_entry(
                    conn,
                    "user_settings",
                    record_id,
                    user_id,
                    setting_key,
                    None,
                    setting_value.raw_value,
                    ChangeType.CREATE,
                    change_reason,
                    client_ip,
                    user_agent,
                )

            return audit_id

        except Exception as e:
            logger.error(
                "Failed to update single setting",
                user_id=user_id,
                setting_key=setting_key,
                error=str(e),
            )
            raise

    async def validate_settings(
        self, settings: dict[str, Any], user_id: str
    ) -> SettingsValidationResult:
        """Validate settings with comprehensive security checks."""
        try:
            result = SettingsValidationResult(is_valid=True)

            for setting_key, value in settings.items():
                try:
                    # Get system setting for validation
                    system_setting = await self.get_system_setting(setting_key)
                    if not system_setting:
                        result.errors.append(f"Unknown setting: {setting_key}")
                        continue

                    # Check if setting is admin-only
                    if system_setting.is_admin_only:
                        result.admin_required.append(setting_key)

                    # Validate the value and use the validated result
                    validated_value = await self._validate_setting_value(
                        setting_key, value, system_setting
                    )
                    result.validated_settings[setting_key] = validated_value

                except ValueError as e:
                    result.errors.append(
                        f"Validation error for {setting_key}: {str(e)}"
                    )
                except Exception as e:
                    result.security_violations.append(
                        f"Security violation for {setting_key}: {str(e)}"
                    )

            result.is_valid = (
                len(result.errors) == 0 and len(result.security_violations) == 0
            )

            return result

        except Exception as e:
            logger.error("Settings validation failed", error=str(e))
            return SettingsValidationResult(
                is_valid=False, errors=[f"Validation system error: {str(e)}"]
            )

    async def get_settings_audit(
        self,
        user_id: str,
        setting_key: str | None = None,
        filter_user_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> SettingsResponse:
        """Get settings audit trail with admin verification.

        Delegates to SettingsAuditService.
        """
        return await self._audit_service.get_settings_audit(
            user_id=user_id,
            setting_key=setting_key,
            filter_user_id=filter_user_id,
            limit=limit,
            offset=offset,
        )

    async def reset_user_settings(
        self,
        user_id: str,
        category: SettingCategory | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> SettingsResponse:
        """Reset user settings by deleting overrides. Delegates to SettingsAuditService."""
        return await self._audit_service.reset_user_settings(
            user_id=user_id,
            category=category,
            client_ip=client_ip,
            user_agent=user_agent,
        )

    async def reset_system_settings(
        self,
        user_id: str,
        category: SettingCategory | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> SettingsResponse:
        """Reset system settings to factory defaults. Delegates to SettingsAuditService."""
        return await self._audit_service.reset_system_settings(
            user_id=user_id,
            category=category,
            client_ip=client_ip,
            user_agent=user_agent,
        )

    async def get_default_settings(
        self, category: SettingCategory | None = None
    ) -> SettingsResponse:
        """Get factory default settings values. Delegates to SettingsSchemaService."""
        return await self._schema_service.get_default_settings(category=category)

    async def get_settings_schema(self) -> SettingsResponse:
        """Get settings schema for frontend validation. Delegates to SettingsSchemaService."""
        return await self._schema_service.get_settings_schema()

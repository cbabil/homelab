"""
Settings Schema Service

Handles settings schema retrieval and factory default lookups
for the settings management system.
"""

import json
from contextlib import asynccontextmanager

import structlog

from models.settings import (
    SettingCategory,
    SettingDataType,
    SettingsResponse,
    SettingValue,
)
from services.database_service import DatabaseService

logger = structlog.get_logger("settings_schema")


class SettingsSchemaService:
    """Service for settings schema and default value operations."""

    def __init__(self, db_service: DatabaseService) -> None:
        """Initialize schema service with database dependency.

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

    async def get_default_settings(
        self, category: SettingCategory | None = None
    ) -> SettingsResponse:
        """Get factory default settings values.

        Args:
            category: Optional category filter.

        Returns:
            SettingsResponse with default values for each setting.
        """
        try:
            async with self.get_connection() as conn:
                if category:
                    cursor = await conn.execute(
                        """
                        SELECT setting_key, default_value, category, data_type, description
                        FROM system_settings
                        WHERE category = ?
                        ORDER BY setting_key
                        """,
                        (category.value,),
                    )
                else:
                    cursor = await conn.execute(
                        """
                        SELECT setting_key, default_value, category, data_type, description
                        FROM system_settings
                        ORDER BY category, setting_key
                        """
                    )

                rows = await cursor.fetchall()
                defaults = {}

                for row in rows:
                    try:
                        setting_value = SettingValue(
                            raw_value=row["default_value"],
                            data_type=SettingDataType(row["data_type"]),
                        )
                        defaults[row["setting_key"]] = {
                            "value": setting_value.get_parsed_value(),
                            "category": row["category"],
                            "data_type": row["data_type"],
                            "description": row["description"],
                        }
                    except Exception as e:
                        logger.warning(
                            "Invalid default value",
                            setting_key=row["setting_key"],
                            error=str(e),
                        )

            return SettingsResponse(
                success=True,
                message=f"Retrieved {len(defaults)} default settings",
                data={"defaults": defaults},
            )

        except Exception as e:
            logger.error("Failed to get default settings", error=str(e))
            return SettingsResponse(
                success=False,
                message=f"Failed to get default settings: {str(e)}",
                error="GET_DEFAULTS_ERROR",
            )

    async def get_settings_schema(self) -> SettingsResponse:
        """Get settings schema for frontend validation.

        Returns:
            SettingsResponse with schema metadata for each setting.
        """
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    """
                    SELECT setting_key, category, scope, data_type, is_admin_only,
                           description, validation_rules
                    FROM system_settings
                    ORDER BY category, setting_key
                    """
                )
                rows = await cursor.fetchall()

                schema = {}
                for row in rows:
                    schema[row["setting_key"]] = {
                        "category": row["category"],
                        "scope": row["scope"],
                        "data_type": row["data_type"],
                        "is_admin_only": bool(row["is_admin_only"]),
                        "description": row["description"],
                        "validation_rules": json.loads(row["validation_rules"])
                        if row["validation_rules"]
                        else None,
                    }

            return SettingsResponse(
                success=True,
                message=f"Retrieved schema for {len(schema)} settings",
                data={"schema": schema},
            )

        except Exception as e:
            logger.error("Failed to get settings schema", error=str(e))
            return SettingsResponse(
                success=False,
                message=f"Failed to get settings schema: {str(e)}",
                error="SCHEMA_ERROR",
            )

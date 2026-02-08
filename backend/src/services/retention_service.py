"""
Data Retention Service

Provides secure data cleanup operations with comprehensive audit logging,
transaction safety, and mandatory security controls for data deletion.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog

from models.auth import UserRole
from models.log import LogEntry
from models.retention import (
    CleanupPreview,
    CleanupRequest,
    CleanupResult,
    RetentionAuditEntry,
    RetentionOperation,
    RetentionSettings,
    RetentionType,
    SecurityValidationResult,
)
from services.auth_service import AuthService
from services.database_service import DatabaseService
from services.service_log import log_service

logger = structlog.get_logger("retention_service")


class RetentionService:
    """Service for managing data retention policies and cleanup operations."""

    def __init__(
        self,
        db_service: DatabaseService | None = None,
        auth_service: AuthService | None = None,
    ):
        """Initialize retention service with required dependencies."""
        self.db_service = db_service or DatabaseService()
        self.auth_service = auth_service or AuthService()
        self.max_batch_size = 10000
        self.min_batch_size = 100
        logger.info("Retention service initialized")

    async def _validate_security(
        self, request: CleanupRequest
    ) -> SecurityValidationResult:
        """Validate security requirements for retention operations."""
        try:
            # Validate session token and get user
            token_validation = self.auth_service._validate_jwt_token(
                request.session_token
            )
            if not token_validation:
                return SecurityValidationResult(
                    is_valid=False, error_message="Invalid or expired session token"
                )

            # Get user by username from token
            username = token_validation.get("username")
            if not username:
                return SecurityValidationResult(
                    is_valid=False, error_message="Invalid token payload"
                )

            user = await self.auth_service.get_user_by_username(username)
            if not user or not user.is_active:
                return SecurityValidationResult(
                    is_valid=False, error_message="User not found or inactive"
                )

            # Verify admin role
            is_admin = user.role == UserRole.ADMIN
            if not is_admin:
                return SecurityValidationResult(
                    is_valid=False,
                    is_admin=False,
                    session_valid=True,
                    user_id=user.id,
                    error_message="Admin privileges required for retention operations",
                )

            # Additional validation for non-dry-run operations
            requires_additional_verification = False
            if not request.dry_run and request.force_cleanup:
                requires_additional_verification = True

            return SecurityValidationResult(
                is_valid=True,
                is_admin=True,
                session_valid=True,
                user_id=user.id,
                requires_additional_verification=requires_additional_verification,
            )

        except Exception as e:
            logger.error("Security validation failed", error=str(e))
            return SecurityValidationResult(
                is_valid=False, error_message=f"Security validation error: {str(e)}"
            )

    async def _log_retention_operation(
        self,
        operation: RetentionOperation,
        retention_type: RetentionType | None,
        admin_user_id: str,
        success: bool,
        records_affected: int = 0,
        error_message: str | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Log retention operation for comprehensive audit trail."""
        try:
            audit_entry = RetentionAuditEntry(
                id=f"ret-{uuid.uuid4().hex[:8]}",
                operation=operation,
                retention_type=retention_type,
                admin_user_id=admin_user_id,
                client_ip=client_ip or "unknown",
                user_agent=user_agent or "unknown",
                success=success,
                records_affected=records_affected,
                error_message=error_message,
                metadata=metadata or {},
            )

            # Create log entry for service_log
            log_entry = LogEntry(
                id=audit_entry.id,
                timestamp=audit_entry.timestamp,
                level="INFO" if success else "ERROR",
                source="retention_service",
                message=f"Retention {operation.value} {'succeeded' if success else 'failed'}: {retention_type.value if retention_type else 'settings'} - {records_affected} records affected",
                tags=[
                    "retention",
                    "audit",
                    operation.value,
                    "success" if success else "failure",
                ],
                metadata=audit_entry.model_dump(),
            )

            await log_service.create_log_entry(log_entry)
            logger.info(
                "Retention operation logged",
                operation=operation.value,
                retention_type=retention_type.value if retention_type else None,
                success=success,
                records_affected=records_affected,
            )

        except Exception as e:
            logger.error("Failed to log retention operation", error=str(e))

    async def get_retention_settings(self, user_id: str) -> RetentionSettings | None:
        """Get current system-wide retention settings from database.

        Returns simplified settings with log_retention and data_retention integers.
        Uses access_log_retention as the representative log value and
        metrics_retention as the representative data value.
        """
        try:
            async with self.db_service.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM retention_settings WHERE id = 'system'"
                )
                row = await cursor.fetchone()

            if not row:
                return RetentionSettings()

            # Use access_log_retention as representative for all logs
            # Use metrics_retention as representative for all data
            return RetentionSettings(
                log_retention=row["access_log_retention"],
                data_retention=row["metrics_retention"],
                last_updated=row["last_updated"],
                updated_by_user_id=row["updated_by_user_id"],
            )

        except Exception as e:
            logger.error("Failed to get retention settings", error=str(e))
            return RetentionSettings()

    async def update_retention_settings(
        self, user_id: str, settings: RetentionSettings
    ) -> bool:
        """Update system-wide retention settings in database.

        Applies log_retention to all log columns (audit, access, application, server).
        Applies data_retention to all data columns (metrics, notification, session).
        """
        try:
            # Get user and verify admin role
            user = await self.db_service.get_user_by_id(user_id)
            if not user or user.role != UserRole.ADMIN:
                logger.error("Unauthorized retention settings update", user_id=user_id)
                return False

            now = datetime.now(UTC).isoformat()

            # Update database - apply single values to all columns in each category
            async with self.db_service.get_connection() as conn:
                await conn.execute(
                    """UPDATE retention_settings SET
                        audit_log_retention = ?,
                        access_log_retention = ?,
                        application_log_retention = ?,
                        server_log_retention = ?,
                        metrics_retention = ?,
                        notification_retention = ?,
                        session_retention = ?,
                        last_updated = ?,
                        updated_by_user_id = ?
                    WHERE id = 'system'""",
                    (
                        settings.log_retention,  # All log types get same value
                        settings.log_retention,
                        settings.log_retention,
                        settings.log_retention,
                        settings.data_retention,  # All data types get same value
                        settings.data_retention,
                        settings.data_retention,
                        now,
                        user_id,
                    ),
                )
                await conn.commit()

            await self._log_retention_operation(
                RetentionOperation.SETTINGS_UPDATE,
                None,
                user_id,
                True,
                metadata={"settings": settings.model_dump()},
            )

            logger.info(
                "Retention settings updated",
                user_id=user_id,
                log_retention=settings.log_retention,
                data_retention=settings.data_retention,
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to update retention settings", user_id=user_id, error=str(e)
            )
            await self._log_retention_operation(
                RetentionOperation.SETTINGS_UPDATE,
                None,
                user_id,
                False,
                error_message=str(e),
            )
            return False

    async def preview_cleanup(self, request: CleanupRequest) -> CleanupPreview | None:
        """Preview cleanup operations without performing deletion (dry-run)."""
        try:
            # Validate security first
            validation = await self._validate_security(request)
            if not validation.is_valid:
                logger.error(
                    "Security validation failed for cleanup preview",
                    error=validation.error_message,
                )
                return None

            # Get retention settings
            settings = await self.get_retention_settings(validation.user_id)
            if not settings:
                logger.error(
                    "No retention settings found for user", user_id=validation.user_id
                )
                return None

            # Calculate cutoff date based on retention type
            cutoff_date = self._calculate_cutoff_date(request.retention_type, settings)
            if not cutoff_date:
                return None

            # Preview records to be deleted
            preview = await self._preview_records_for_deletion(
                request.retention_type, cutoff_date
            )

            await self._log_retention_operation(
                RetentionOperation.DRY_RUN,
                request.retention_type,
                validation.user_id,
                True,
                records_affected=preview.affected_records if preview else 0,
                metadata={"cutoff_date": cutoff_date},
            )

            return preview

        except Exception as e:
            logger.error(
                "Cleanup preview failed",
                retention_type=request.retention_type,
                error=str(e),
            )
            await self._log_retention_operation(
                RetentionOperation.DRY_RUN,
                request.retention_type,
                request.admin_user_id,
                False,
                error_message=str(e),
            )
            return None

    async def perform_cleanup(self, request: CleanupRequest) -> CleanupResult | None:
        """Perform secure cleanup operations with transaction safety."""
        operation_id = f"cleanup-{uuid.uuid4().hex[:8]}"
        start_time = datetime.now(UTC)

        try:
            # Security validation
            validation = await self._validate_security(request)
            if not validation.is_valid:
                return CleanupResult(
                    operation_id=operation_id,
                    retention_type=request.retention_type,
                    operation=RetentionOperation.CLEANUP,
                    success=False,
                    start_time=start_time.isoformat(),
                    end_time=datetime.now(UTC).isoformat(),
                    admin_user_id=request.admin_user_id,
                    error_message=validation.error_message,
                )

            # Mandatory dry-run check
            if not request.dry_run and not request.force_cleanup:
                return CleanupResult(
                    operation_id=operation_id,
                    retention_type=request.retention_type,
                    operation=RetentionOperation.CLEANUP,
                    success=False,
                    start_time=start_time.isoformat(),
                    end_time=datetime.now(UTC).isoformat(),
                    admin_user_id=validation.user_id,
                    error_message="Dry-run must be performed before actual cleanup",
                )

            # Get retention settings
            settings = await self.get_retention_settings(validation.user_id)
            if not settings:
                return self._create_error_result(
                    operation_id,
                    request,
                    start_time,
                    validation.user_id,
                    "No retention settings found",
                )

            # Calculate cutoff date
            cutoff_date = self._calculate_cutoff_date(request.retention_type, settings)
            if not cutoff_date:
                return self._create_error_result(
                    operation_id,
                    request,
                    start_time,
                    validation.user_id,
                    "Invalid retention type",
                )

            # Perform deletion with transaction safety
            if request.dry_run:
                preview = await self._preview_records_for_deletion(
                    request.retention_type, cutoff_date
                )
                result = CleanupResult(
                    operation_id=operation_id,
                    retention_type=request.retention_type,
                    operation=RetentionOperation.DRY_RUN,
                    success=True,
                    records_affected=preview.affected_records if preview else 0,
                    start_time=start_time.isoformat(),
                    end_time=datetime.now(UTC).isoformat(),
                    admin_user_id=validation.user_id,
                    preview_data=preview,
                )
            else:
                deleted_count, space_freed = await self._perform_secure_deletion(
                    request.retention_type, cutoff_date, request.batch_size or 1000
                )
                result = CleanupResult(
                    operation_id=operation_id,
                    retention_type=request.retention_type,
                    operation=RetentionOperation.CLEANUP,
                    success=True,
                    records_affected=deleted_count,
                    space_freed_mb=space_freed,
                    duration_seconds=(datetime.now(UTC) - start_time).total_seconds(),
                    start_time=start_time.isoformat(),
                    end_time=datetime.now(UTC).isoformat(),
                    admin_user_id=validation.user_id,
                )

            await self._log_retention_operation(
                result.operation,
                request.retention_type,
                validation.user_id,
                True,
                records_affected=result.records_affected,
                metadata={"operation_id": operation_id, "cutoff_date": cutoff_date},
            )

            return result

        except Exception as e:
            logger.error(
                "Cleanup operation failed", operation_id=operation_id, error=str(e)
            )
            await self._log_retention_operation(
                RetentionOperation.CLEANUP,
                request.retention_type,
                request.admin_user_id,
                False,
                error_message=str(e),
            )
            return self._create_error_result(
                operation_id, request, start_time, request.admin_user_id, str(e)
            )

    def _calculate_cutoff_date(
        self, retention_type: RetentionType, settings: RetentionSettings
    ) -> str | None:
        """Calculate cutoff date based on retention type and settings.

        Uses log_retention for all log types and data_retention for all data types.
        """
        try:
            now = datetime.now(UTC)

            # Log retention types - all use log_retention value
            if retention_type in (
                RetentionType.AUDIT_LOGS,
                RetentionType.ACCESS_LOGS,
                RetentionType.APPLICATION_LOGS,
                RetentionType.SERVER_LOGS,
            ):
                cutoff = now - timedelta(days=settings.log_retention)
            # Data retention types - all use data_retention value
            elif retention_type in (
                RetentionType.METRICS,
                RetentionType.NOTIFICATIONS,
                RetentionType.SESSIONS,
            ):
                cutoff = now - timedelta(days=settings.data_retention)
            else:
                return None

            return cutoff.isoformat()
        except Exception as e:
            logger.error(
                "Failed to calculate cutoff date",
                retention_type=retention_type,
                error=str(e),
            )
            return None

    async def _preview_records_for_deletion(
        self, retention_type: RetentionType, cutoff_date: str
    ) -> CleanupPreview | None:
        """Preview records that would be deleted without performing deletion."""
        try:
            # All log types share the same preview logic
            if retention_type in (
                RetentionType.AUDIT_LOGS,
                RetentionType.ACCESS_LOGS,
                RetentionType.APPLICATION_LOGS,
                RetentionType.SERVER_LOGS,
            ):
                return await self._preview_log_deletion(retention_type, cutoff_date)
            # Add other retention types as needed
            return None
        except Exception as e:
            logger.error(
                "Failed to preview records", retention_type=retention_type, error=str(e)
            )
            return None

    async def _preview_log_deletion(
        self, retention_type: RetentionType, cutoff_date: str
    ) -> CleanupPreview | None:
        """Preview log entries that would be deleted."""
        try:
            async with self.db_service.get_connection() as conn:
                # Count records to be deleted
                cursor = await conn.execute(
                    "SELECT COUNT(*) as count FROM log_entries WHERE timestamp < ?",
                    (cutoff_date,),
                )
                result = await cursor.fetchone()
                affected_records = result["count"] if result else 0

                if affected_records == 0:
                    return CleanupPreview(
                        retention_type=retention_type,
                        affected_records=0,
                        cutoff_date=cutoff_date,
                    )

                # Get date range of affected records
                cursor = await conn.execute(
                    """
                    SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest
                    FROM log_entries WHERE timestamp < ?
                    """,
                    (cutoff_date,),
                )
                date_result = await cursor.fetchone()

                # Estimate space (rough calculation based on average log size)
                estimated_space_mb = affected_records * 0.001  # ~1KB per log entry

                return CleanupPreview(
                    retention_type=retention_type,
                    affected_records=affected_records,
                    oldest_record_date=date_result["oldest"] if date_result else None,
                    newest_record_date=date_result["newest"] if date_result else None,
                    estimated_space_freed_mb=round(estimated_space_mb, 2),
                    cutoff_date=cutoff_date,
                )

        except Exception as e:
            logger.error("Failed to preview log deletion", error=str(e))
            return None

    async def _perform_secure_deletion(
        self, retention_type: RetentionType, cutoff_date: str, batch_size: int
    ) -> tuple[int, float]:
        """Perform secure deletion with transaction safety and batch processing."""
        total_deleted = 0
        estimated_space_freed = 0.0

        try:
            # All log types share the same deletion logic
            if retention_type in (
                RetentionType.AUDIT_LOGS,
                RetentionType.ACCESS_LOGS,
                RetentionType.APPLICATION_LOGS,
                RetentionType.SERVER_LOGS,
            ):
                total_deleted, estimated_space_freed = await self._delete_logs_batch(
                    cutoff_date, batch_size
                )

            logger.info(
                "Secure deletion completed",
                retention_type=retention_type,
                total_deleted=total_deleted,
                space_freed_mb=estimated_space_freed,
            )
            return total_deleted, estimated_space_freed

        except Exception as e:
            logger.error(
                "Secure deletion failed", retention_type=retention_type, error=str(e)
            )
            raise

    async def _delete_logs_batch(
        self, cutoff_date: str, batch_size: int
    ) -> tuple[int, float]:
        """Delete log entries in batches with transaction safety."""
        total_deleted = 0

        try:
            async with self.db_service.get_connection() as conn:
                # Begin transaction
                await conn.execute("BEGIN IMMEDIATE")

                try:
                    # Delete in batches to avoid locking issues
                    while True:
                        cursor = await conn.execute(
                            "DELETE FROM log_entries WHERE timestamp < ? LIMIT ?",
                            (cutoff_date, batch_size),
                        )

                        deleted_count = cursor.rowcount
                        total_deleted += deleted_count

                        logger.debug(
                            "Deleted batch of log entries",
                            batch_size=deleted_count,
                            total=total_deleted,
                        )

                        # Break if no more records to delete
                        if deleted_count < batch_size:
                            break

                    # Commit transaction
                    await conn.commit()

                    # Estimate space freed (rough calculation)
                    estimated_space_mb = total_deleted * 0.001  # ~1KB per log entry

                    logger.info(
                        "Log deletion completed successfully",
                        total_deleted=total_deleted,
                        space_freed_mb=estimated_space_mb,
                    )

                    return total_deleted, round(estimated_space_mb, 2)

                except Exception as e:
                    # Rollback on error
                    await conn.rollback()
                    logger.error(
                        "Log deletion failed, transaction rolled back", error=str(e)
                    )
                    raise

        except Exception as e:
            logger.error("Failed to delete logs in batches", error=str(e))
            raise

    def _create_error_result(
        self,
        operation_id: str,
        request: CleanupRequest,
        start_time: datetime,
        admin_user_id: str,
        error_message: str,
    ) -> CleanupResult:
        """Create error result for failed cleanup operations."""
        return CleanupResult(
            operation_id=operation_id,
            retention_type=request.retention_type,
            operation=RetentionOperation.DRY_RUN
            if request.dry_run
            else RetentionOperation.CLEANUP,
            success=False,
            start_time=start_time.isoformat(),
            end_time=datetime.now(UTC).isoformat(),
            admin_user_id=admin_user_id,
            error_message=error_message,
        )

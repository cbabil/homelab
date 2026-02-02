"""Metrics Database Service.

Database operations for server metrics, container metrics, and activity logs.
"""

import json
from typing import Any, List, Optional

import structlog

from models.metrics import ServerMetrics, ContainerMetrics, ActivityLog, ActivityType
from .base import DatabaseConnection

logger = structlog.get_logger("database.metrics")


class MetricsDatabaseService:
    """Database operations for metrics and activity log management."""

    def __init__(self, connection: DatabaseConnection):
        """Initialize with database connection.

        Args:
            connection: DatabaseConnection instance.
        """
        self._conn = connection

    # ========== Server Metrics ==========

    async def save_server_metrics(self, metrics: ServerMetrics) -> bool:
        """Save server metrics to database."""
        try:
            async with self._conn.get_connection() as conn:
                await conn.execute(
                    """INSERT INTO server_metrics
                       (id, server_id, cpu_percent, memory_percent, memory_used_mb,
                        memory_total_mb, disk_percent, disk_used_gb, disk_total_gb,
                        network_rx_bytes, network_tx_bytes, load_average_1m,
                        load_average_5m, load_average_15m, uptime_seconds, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        metrics.id,
                        metrics.server_id,
                        metrics.cpu_percent,
                        metrics.memory_percent,
                        metrics.memory_used_mb,
                        metrics.memory_total_mb,
                        metrics.disk_percent,
                        metrics.disk_used_gb,
                        metrics.disk_total_gb,
                        metrics.network_rx_bytes,
                        metrics.network_tx_bytes,
                        metrics.load_average_1m,
                        metrics.load_average_5m,
                        metrics.load_average_15m,
                        metrics.uptime_seconds,
                        metrics.timestamp,
                    ),
                )
                await conn.commit()
            return True
        except Exception as e:
            logger.error("Failed to save server metrics", error=str(e))
            return False

    async def get_server_metrics(
        self, server_id: str, since: Optional[str] = None, limit: int = 100
    ) -> List[ServerMetrics]:
        """Get server metrics from database."""
        try:
            query = "SELECT * FROM server_metrics WHERE server_id = ?"
            params: List[Any] = [server_id]

            if since:
                query += " AND timestamp >= ?"
                params.append(since)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()

            return [
                ServerMetrics(
                    id=row["id"],
                    server_id=row["server_id"],
                    cpu_percent=row["cpu_percent"],
                    memory_percent=row["memory_percent"],
                    memory_used_mb=row["memory_used_mb"],
                    memory_total_mb=row["memory_total_mb"],
                    disk_percent=row["disk_percent"],
                    disk_used_gb=row["disk_used_gb"],
                    disk_total_gb=row["disk_total_gb"],
                    network_rx_bytes=row["network_rx_bytes"],
                    network_tx_bytes=row["network_tx_bytes"],
                    load_average_1m=row["load_average_1m"],
                    load_average_5m=row["load_average_5m"],
                    load_average_15m=row["load_average_15m"],
                    uptime_seconds=row["uptime_seconds"],
                    timestamp=row["timestamp"],
                )
                for row in rows
            ]
        except Exception as e:
            logger.error("Failed to get server metrics", error=str(e))
            return []

    # ========== Container Metrics ==========

    async def save_container_metrics(self, metrics: ContainerMetrics) -> bool:
        """Save container metrics to database."""
        try:
            async with self._conn.get_connection() as conn:
                await conn.execute(
                    """INSERT INTO container_metrics
                       (id, server_id, container_id, container_name, cpu_percent,
                        memory_usage_mb, memory_limit_mb, network_rx_bytes,
                        network_tx_bytes, status, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        metrics.id,
                        metrics.server_id,
                        metrics.container_id,
                        metrics.container_name,
                        metrics.cpu_percent,
                        metrics.memory_usage_mb,
                        metrics.memory_limit_mb,
                        metrics.network_rx_bytes,
                        metrics.network_tx_bytes,
                        metrics.status,
                        metrics.timestamp,
                    ),
                )
                await conn.commit()
            return True
        except Exception as e:
            logger.error("Failed to save container metrics", error=str(e))
            return False

    async def get_container_metrics(
        self,
        server_id: str,
        container_name: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> List[ContainerMetrics]:
        """Get container metrics from database."""
        try:
            query = "SELECT * FROM container_metrics WHERE server_id = ?"
            params: List[Any] = [server_id]

            if container_name:
                query += " AND container_name = ?"
                params.append(container_name)

            if since:
                query += " AND timestamp >= ?"
                params.append(since)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()

            return [
                ContainerMetrics(
                    id=row["id"],
                    server_id=row["server_id"],
                    container_id=row["container_id"],
                    container_name=row["container_name"],
                    cpu_percent=row["cpu_percent"],
                    memory_usage_mb=row["memory_usage_mb"],
                    memory_limit_mb=row["memory_limit_mb"],
                    network_rx_bytes=row["network_rx_bytes"],
                    network_tx_bytes=row["network_tx_bytes"],
                    status=row["status"],
                    timestamp=row["timestamp"],
                )
                for row in rows
            ]
        except Exception as e:
            logger.error("Failed to get container metrics", error=str(e))
            return []

    # ========== Activity Logs ==========

    async def save_activity_log(self, log: ActivityLog) -> bool:
        """Save activity log to database."""
        try:
            details_json = json.dumps(log.details) if log.details else "{}"
            async with self._conn.get_connection() as conn:
                await conn.execute(
                    """INSERT INTO activity_logs
                       (id, activity_type, user_id, server_id, app_id, message, details, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        log.id,
                        log.activity_type.value,
                        log.user_id,
                        log.server_id,
                        log.app_id,
                        log.message,
                        details_json,
                        log.timestamp,
                    ),
                )
                await conn.commit()
            return True
        except Exception as e:
            logger.error("Failed to save activity log", error=str(e))
            return False

    async def get_activity_logs(
        self,
        activity_types: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        server_id: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ActivityLog]:
        """Get activity logs from database."""
        try:
            query = "SELECT * FROM activity_logs WHERE 1=1"
            params: List[Any] = []

            if activity_types:
                placeholders = ",".join("?" * len(activity_types))
                query += f" AND activity_type IN ({placeholders})"
                params.extend(activity_types)

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            if server_id:
                query += " AND server_id = ?"
                params.append(server_id)

            if since:
                query += " AND timestamp >= ?"
                params.append(since)

            if until:
                query += " AND timestamp <= ?"
                params.append(until)

            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()

            return [
                ActivityLog(
                    id=row["id"],
                    activity_type=ActivityType(row["activity_type"]),
                    user_id=row["user_id"],
                    server_id=row["server_id"],
                    app_id=row["app_id"],
                    message=row["message"],
                    details=json.loads(row["details"]) if row["details"] else {},
                    timestamp=row["timestamp"],
                )
                for row in rows
            ]
        except Exception as e:
            logger.error("Failed to get activity logs", error=str(e))
            return []

    async def count_activity_logs(
        self, activity_types: Optional[List[str]] = None, since: Optional[str] = None
    ) -> int:
        """Count activity logs matching filters."""
        try:
            query = "SELECT COUNT(*) as count FROM activity_logs WHERE 1=1"
            params: List[Any] = []

            if activity_types:
                placeholders = ",".join("?" * len(activity_types))
                query += f" AND activity_type IN ({placeholders})"
                params.extend(activity_types)

            if since:
                query += " AND timestamp >= ?"
                params.append(since)

            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(query, params)
                row = await cursor.fetchone()

            return row["count"] if row else 0
        except Exception as e:
            logger.error("Failed to count activity logs", error=str(e))
            return 0

    # ========== Log Retention ==========

    async def get_log_entries_count_before_date(self, cutoff_date: str) -> int:
        """Get count of log entries before specified date for retention operations."""
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT COUNT(*) as count FROM log_entries WHERE timestamp < ?",
                    (cutoff_date,),
                )
                result = await cursor.fetchone()
                return result["count"] if result else 0

        except Exception as e:
            logger.error(
                "Failed to count log entries", cutoff_date=cutoff_date, error=str(e)
            )
            return 0

    async def delete_log_entries_before_date(
        self, cutoff_date: str, batch_size: int = 1000
    ) -> int:
        """Delete log entries before specified date in batches."""
        total_deleted = 0

        try:
            async with self._conn.get_connection() as conn:
                await conn.execute("BEGIN IMMEDIATE")

                try:
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

                        if deleted_count < batch_size:
                            break

                    await conn.commit()
                    logger.info("Successfully deleted log entries", total=total_deleted)
                    return total_deleted

                except Exception as e:
                    await conn.rollback()
                    logger.error("Log deletion failed, rolled back", error=str(e))
                    raise

        except Exception as e:
            logger.error("Failed to delete log entries", error=str(e))
            raise

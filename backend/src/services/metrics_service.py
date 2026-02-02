"""
Metrics Collection Service

Collects server and container metrics via SSH.
"""

import re
import uuid
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, Optional, List
import structlog
from models.metrics import ServerMetrics, ContainerMetrics

logger = structlog.get_logger("metrics_service")


# Period to timedelta mapping
PERIOD_MAP = {
    "1h": timedelta(hours=1),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


class MetricsService:
    """Service for collecting and managing metrics."""

    def __init__(self, ssh_service, db_service, server_service):
        """Initialize metrics service."""
        self.ssh_service = ssh_service
        self.db_service = db_service
        self.server_service = server_service
        logger.info("Metrics service initialized")

    def _parse_cpu_percent(self, output: str) -> float:
        """Parse CPU usage from top/mpstat output."""
        try:
            # Match patterns like "25.5 us, 10.2 sy" or "25.5%us"
            match = re.search(r'(\d+\.?\d*)\s*(?:%\s*)?us.*?(\d+\.?\d*)\s*(?:%\s*)?sy', output)
            if match:
                user = float(match.group(1))
                system = float(match.group(2))
                return user + system

            # Alternative: match single CPU percentage
            match = re.search(r'(\d+\.?\d*)%?\s*(?:cpu|CPU)', output)
            if match:
                return float(match.group(1))

            return 0.0
        except Exception as e:
            logger.error("Failed to parse CPU", error=str(e))
            return 0.0

    def _parse_memory(self, output: str) -> tuple:
        """Parse memory from free command output."""
        try:
            lines = output.strip().split('\n')
            for line in lines:
                if line.startswith('Mem:'):
                    parts = line.split()
                    total = int(parts[1])
                    used = int(parts[2])
                    percent = (used / total) * 100 if total > 0 else 0
                    return used, total, percent
            return 0, 0, 0.0
        except Exception as e:
            logger.error("Failed to parse memory", error=str(e))
            return 0, 0, 0.0

    def _parse_disk(self, output: str) -> tuple:
        """Parse disk usage from df command output."""
        try:
            lines = output.strip().split('\n')
            for line in lines:
                if '/' in line and not line.startswith('Filesystem'):
                    parts = line.split()
                    # Parse size (e.g., "200G")
                    total_str = parts[1]
                    used_str = parts[2]
                    percent_str = parts[4].replace('%', '')

                    total = int(re.sub(r'[^\d]', '', total_str))
                    used = int(re.sub(r'[^\d]', '', used_str))
                    percent = float(percent_str)

                    return used, total, percent
            return 0, 0, 0.0
        except Exception as e:
            logger.error("Failed to parse disk", error=str(e))
            return 0, 0, 0.0

    def _parse_docker_stats(self, output: str) -> List[Dict[str, Any]]:
        """Parse docker stats output."""
        containers = []
        try:
            for line in output.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) >= 7:
                    # Parse memory like "256MiB / 512MiB"
                    mem_parts = parts[3].split('/')
                    mem_used = int(re.sub(r'[^\d]', '', mem_parts[0]))
                    mem_limit = int(re.sub(r'[^\d]', '', mem_parts[1])) if len(mem_parts) > 1 else 0

                    containers.append({
                        "container_id": parts[0].strip(),
                        "name": parts[1].strip(),
                        "cpu_percent": float(parts[2].replace('%', '').strip()),
                        "memory_usage_mb": mem_used,
                        "memory_limit_mb": mem_limit,
                        "network_rx": int(parts[4]) if parts[4].isdigit() else 0,
                        "network_tx": int(parts[5]) if parts[5].isdigit() else 0,
                        "status": parts[6].strip()
                    })
        except Exception as e:
            logger.error("Failed to parse docker stats", error=str(e))
        return containers

    async def collect_server_metrics(self, server_id: str) -> Optional[ServerMetrics]:
        """Collect current metrics from a server."""
        try:
            # Collect CPU
            exit_code, cpu_out, _ = await self.ssh_service.execute_command(
                server_id,
                "top -bn1 | head -5"
            )
            cpu_percent = self._parse_cpu_percent(cpu_out) if exit_code == 0 else 0.0

            # Collect Memory
            exit_code, mem_out, _ = await self.ssh_service.execute_command(
                server_id,
                "free -k | grep -E '^Mem:'"
            )
            mem_used, mem_total, mem_percent = self._parse_memory(mem_out) if exit_code == 0 else (0, 0, 0.0)

            # Collect Disk
            exit_code, disk_out, _ = await self.ssh_service.execute_command(
                server_id,
                "df -h / | tail -1"
            )
            disk_used, disk_total, disk_percent = self._parse_disk(disk_out) if exit_code == 0 else (0, 0, 0.0)

            metrics = ServerMetrics(
                id=f"sm-{uuid.uuid4().hex[:8]}",
                server_id=server_id,
                cpu_percent=cpu_percent,
                memory_percent=mem_percent,
                memory_used_mb=mem_used // 1024,  # Convert KB to MB
                memory_total_mb=mem_total // 1024,
                disk_percent=disk_percent,
                disk_used_gb=disk_used,
                disk_total_gb=disk_total,
                timestamp=datetime.now(UTC).isoformat()
            )

            await self.db_service.save_server_metrics(metrics)
            logger.debug("Collected server metrics", server_id=server_id)
            return metrics

        except Exception as e:
            logger.error("Failed to collect metrics", server_id=server_id, error=str(e))
            return None

    async def collect_container_metrics(self, server_id: str) -> List[ContainerMetrics]:
        """Collect metrics for all containers on a server."""
        try:
            # Get docker stats in parseable format
            cmd = 'docker stats --no-stream --format "{{.ID}}|{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}|{{.Status}}"'
            exit_code, output, _ = await self.ssh_service.execute_command(server_id, cmd)

            if exit_code != 0:
                return []

            containers = self._parse_docker_stats(output)
            results = []

            for c in containers:
                metrics = ContainerMetrics(
                    id=f"cm-{uuid.uuid4().hex[:8]}",
                    server_id=server_id,
                    container_id=c["container_id"],
                    container_name=c["name"],
                    cpu_percent=c["cpu_percent"],
                    memory_usage_mb=c["memory_usage_mb"],
                    memory_limit_mb=c["memory_limit_mb"],
                    network_rx_bytes=c["network_rx"],
                    network_tx_bytes=c["network_tx"],
                    status=c["status"],
                    timestamp=datetime.now(UTC).isoformat()
                )
                await self.db_service.save_container_metrics(metrics)
                results.append(metrics)

            return results

        except Exception as e:
            logger.error("Failed to collect container metrics", error=str(e))
            return []

    async def get_server_metrics(
        self,
        server_id: str,
        period: str = "24h"
    ) -> List[ServerMetrics]:
        """Get historical metrics for a server."""
        try:
            delta = PERIOD_MAP.get(period, timedelta(hours=24))
            since = datetime.now(UTC) - delta

            return await self.db_service.get_server_metrics(
                server_id=server_id,
                since=since.isoformat()
            )
        except Exception as e:
            logger.error("Failed to get server metrics", error=str(e))
            return []

    async def get_container_metrics(
        self,
        server_id: str,
        container_name: str = None,
        period: str = "24h"
    ) -> List[ContainerMetrics]:
        """Get historical container metrics."""
        try:
            delta = PERIOD_MAP.get(period, timedelta(hours=24))
            since = datetime.now(UTC) - delta

            return await self.db_service.get_container_metrics(
                server_id=server_id,
                container_name=container_name,
                since=since.isoformat()
            )
        except Exception as e:
            logger.error("Failed to get container metrics", error=str(e))
            return []

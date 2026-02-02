"""Collectors package for metrics and health reporting."""

try:
    from .health import HealthReporter
    from .metrics import MetricsCollector
except ImportError:
    from collectors.health import HealthReporter
    from collectors.metrics import MetricsCollector

__all__ = ["HealthReporter", "MetricsCollector"]

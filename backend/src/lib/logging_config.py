"""
Logging Configuration Module

Sets up structured logging with JSON output for the MCP server.
Includes security-conscious filtering of sensitive data.
"""

import os
import logging
import structlog


def setup_logging():
    """Configure structured logging for the application."""
    log_level = os.getenv("MCP_LOG_LEVEL", "INFO").upper()
    
    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(message)s",
        handlers=[logging.StreamHandler()]
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            _filter_sensitive_data,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _filter_sensitive_data(logger, method_name, event_dict):
    """Filter sensitive data from log entries."""
    sensitive_keys = ["password", "private_key", "credentials", "token"]
    
    for key in sensitive_keys:
        if key in event_dict:
            event_dict[key] = "[REDACTED]"
    
    return event_dict
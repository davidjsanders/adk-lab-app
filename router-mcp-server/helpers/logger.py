"""Structured Cloud Run JSON logging formatter helper."""

from datetime import datetime, timezone
import json
import logging
import os
import sys
from typing import Any, Dict


class CloudRunJsonFormatter(logging.Formatter):
    """Formats Python log records as single-line JSON objects for Google Cloud Logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Formats log record into a single-line JSON string.

        Args:
            record: Incoming Python LogRecord object.

        Returns:
            Formatted single-line JSON log string.

        Raises:
            None.
        """
        log_data: Dict[str, Any] = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


def setup_json_logging(logger_name: str = "router-mcp-server") -> logging.Logger:
    """Configures structured JSON stdout logging for Google Cloud Run compatibility.

    Args:
        logger_name: Logger instance name string (default: 'router-mcp-server').

    Returns:
        Configured Logger instance with CloudRunJsonFormatter.

    Raises:
        None.
    """
    logger = logging.getLogger(logger_name)

    # Read dynamic LOG_LEVEL from environment (default: INFO)
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper().strip()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CloudRunJsonFormatter())

    # Configure application logger
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False

    # Also format WSGI access logs (werkzeug) as structured JSON
    w_logger = logging.getLogger("werkzeug")
    w_logger.setLevel(log_level)
    w_logger.handlers.clear()
    w_logger.addHandler(handler)
    w_logger.propagate = False

    return logger

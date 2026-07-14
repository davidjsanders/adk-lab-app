# helpers/logger.py
import logging
import sys
import structlog

def configure_logger():
    """Configures structlog to output structured JSON for production environments."""
    processors = [
        # Merges context variables (e.g., trace_id, session_id) automatically
        structlog.contextvars.merge_contextvars,
        # Adds log level (info, error, etc.) as a field
        structlog.processors.add_log_level,
        # Adds human-readable timestamp to the JSON payload
        structlog.processors.TimeStamper(fmt="iso"),
        # Formats stack trace nicely if an exception is logged
        structlog.processors.format_exc_info,
        # CRITICAL: Render the output payload as raw JSON
        structlog.processors.JSONRenderer()
    ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        logger_factory=structlog.WriteLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )

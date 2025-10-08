"""
Enhanced logging configuration with structured output.

This module provides a centralized logging setup with structured JSON output,
contextual information, and proper log levels for different components.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request context if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id

        # Add extra fields from the record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add source location for errors and above
        if record.levelno >= logging.ERROR:
            log_data["source"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        return json.dumps(log_data)


class ContextLogger(logging.LoggerAdapter):
    """Logger adapter that includes contextual information."""

    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger, {})

    def process(
        self, msg: str, kwargs: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """Add contextual information to log records."""
        extra = kwargs.get("extra", {})

        # Add request context
        request_id = request_id_var.get()
        if request_id:
            extra["request_id"] = request_id

        user_id = user_id_var.get()
        if user_id:
            extra["user_id"] = user_id

        kwargs["extra"] = extra
        return msg, kwargs


def configure_logging(
    level: str = "INFO",
    structured: bool = True,
) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: Whether to use structured JSON output
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create formatter
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add new handler with our formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> ContextLogger:
    """
    Get a logger with contextual information.

    Args:
        name: Logger name (usually __name__ of the module)

    Returns:
        A ContextLogger instance
    """
    base_logger = logging.getLogger(name)
    return ContextLogger(base_logger)


class LogTimer:
    """Context manager for timing operations with automatic logging."""

    def __init__(
        self,
        logger: logging.Logger | ContextLogger,
        operation: str,
        level: int = logging.INFO,
    ) -> None:
        """
        Initialize the timer.

        Args:
            logger: Logger instance to use
            operation: Name of the operation being timed
            level: Log level to use for the timing message
        """
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self) -> LogTimer:
        """Start the timer."""
        self.start_time = time.perf_counter()
        self.logger.log(self.level, f"Starting: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop the timer and log the duration."""
        self.end_time = time.perf_counter()
        duration_ms = (self.end_time - self.start_time) * 1000

        if exc_type is None:
            self.logger.log(
                self.level,
                f"Completed: {self.operation}",
                extra={"duration_ms": duration_ms},
            )
        else:
            self.logger.error(
                f"Failed: {self.operation}",
                extra={"duration_ms": duration_ms, "error": str(exc_val)},
                exc_info=True,
            )

    @property
    def duration_ms(self) -> Optional[float]:
        """Get the duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None


def log_exception(
    logger: logging.Logger | ContextLogger,
    exception: Exception,
    operation: str,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an exception with contextual information.

    Args:
        logger: Logger instance
        exception: The exception to log
        operation: Name of the operation that failed
        extra_fields: Additional fields to include in the log
    """
    fields = extra_fields or {}
    fields.update(
        {
            "operation": operation,
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
        }
    )
    logger.error(f"Operation failed: {operation}", extra=fields, exc_info=True)

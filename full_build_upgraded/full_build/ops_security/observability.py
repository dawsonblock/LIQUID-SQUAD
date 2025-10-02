"""
Observability hooks: logging, metrics and tracing.

This module provides simple wrappers around Python's logging and the
`prometheus_client` library for metrics collection.  Use these
functions to instrument your code and emit metrics.
"""
from __future__ import annotations
import logging
from prometheus_client import Counter, Histogram

logger = logging.getLogger("agent")
logger.setLevel(logging.INFO)

REQUESTS_TOTAL = Counter("requests_total", "Total number of requests", ["path"])
REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "Request latency in seconds",
    ["path"]
)
# Additional histogram for error tracking
REQUEST_ERRORS = Counter("request_errors_total", "Total number of failed requests", ["path", "error"])

def record_request(path: str, duration: float) -> None:
    """Increment counters and observe latency for a given path."""
    REQUESTS_TOTAL.labels(path=path).inc()
    REQUEST_LATENCY.labels(path=path).observe(duration)
    logger.info("Request on path %s took %.3fs", path, duration)

def record_error(path: str, error: str) -> None:
    """Increment error counters and log an error event.

    Use this helper to report failures.  The `error` label should be a
    short identifier (e.g. "timeout", "quota", "validation") rather than
    a full traceback.
    """
    REQUEST_ERRORS.labels(path=path, error=error).inc()
    logger.error("Error on path %s: %s", path, error)
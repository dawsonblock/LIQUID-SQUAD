"""
Observability hooks: logging, metrics and tracing.

This module provides simple wrappers around Python's logging and the
`prometheus_client` library for metrics collection.  Use these
functions to instrument your code and emit metrics.
"""
from __future__ import annotations
import logging
from prometheus_client import Counter, Histogram, Gauge, Summary

logger = logging.getLogger("agent")
logger.setLevel(logging.INFO)

# Request metrics
REQUESTS_TOTAL = Counter("requests_total", "Total number of requests", ["path"])
REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "Request latency in seconds",
    ["path"]
)
REQUEST_ERRORS = Counter("request_errors_total", "Total number of failed requests", ["path", "error"])

# Self-loop metrics
SELFLOOP_ITERATIONS = Histogram(
    "selfloop_iterations_total",
    "Number of iterations per self-loop execution",
    buckets=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
)
SELFLOOP_CONFIDENCE = Histogram(
    "selfloop_confidence",
    "Final confidence score from self-loop",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)
SELFLOOP_DURATION = Histogram(
    "selfloop_duration_ms",
    "Self-loop execution duration in milliseconds",
    buckets=[100, 250, 500, 1000, 2500, 5000, 10000, 20000, 30000]
)

# Model tier metrics
MODEL_TIER_USAGE = Counter(
    "model_tier_usage_total",
    "Usage count by model tier",
    ["tier"]
)
MODEL_TIER_LATENCY = Histogram(
    "model_tier_latency_seconds",
    "Model inference latency by tier",
    ["tier"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Cache metrics
CACHE_HITS = Counter("cache_hits_total", "Total number of cache hits")
CACHE_MISSES = Counter("cache_misses_total", "Total number of cache misses")
CACHE_SIZE = Gauge("cache_size", "Current number of items in cache")

# Retrieval metrics
RETRIEVAL_QUERIES = Counter(
    "retrieval_queries_total",
    "Total number of retrieval queries",
    ["mode"]
)
RETRIEVAL_LATENCY = Histogram(
    "retrieval_latency_seconds",
    "Retrieval query latency",
    ["mode"]
)
RETRIEVAL_DOCUMENTS = Histogram(
    "retrieval_documents_count",
    "Number of documents retrieved per query",
    buckets=[0, 1, 3, 5, 10, 20, 50]
)

# Verifier metrics
VERIFIER_RUNS = Counter(
    "verifier_runs_total",
    "Total number of verifier runs",
    ["verifier_type"]
)
VERIFIER_ISSUES = Counter(
    "verifier_issues_total",
    "Total number of issues found by verifiers",
    ["verifier_type"]
)

# Conversation metrics
ACTIVE_CONVERSATIONS = Gauge(
    "active_conversations",
    "Number of active conversations"
)
CONVERSATION_TURNS = Histogram(
    "conversation_turns",
    "Number of turns per conversation",
    buckets=[1, 2, 3, 5, 10, 20, 50]
)

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

def record_selfloop_execution(
    iterations: int,
    confidence: float,
    duration_ms: int,
    model_tier: str
) -> None:
    """Record metrics for a self-loop execution."""
    SELFLOOP_ITERATIONS.observe(iterations)
    SELFLOOP_CONFIDENCE.observe(confidence)
    SELFLOOP_DURATION.observe(duration_ms)
    MODEL_TIER_USAGE.labels(tier=model_tier).inc()
    logger.info(
        "Self-loop completed: %d iterations, %.2f%% confidence, %dms, tier=%s",
        iterations, confidence * 100, duration_ms, model_tier
    )

def record_model_inference(tier: str, duration: float) -> None:
    """Record metrics for a model inference call."""
    MODEL_TIER_USAGE.labels(tier=tier).inc()
    MODEL_TIER_LATENCY.labels(tier=tier).observe(duration)

def record_cache_hit() -> None:
    """Record a cache hit."""
    CACHE_HITS.inc()

def record_cache_miss() -> None:
    """Record a cache miss."""
    CACHE_MISSES.inc()

def update_cache_size(size: int) -> None:
    """Update the current cache size."""
    CACHE_SIZE.set(size)

def record_retrieval(mode: str, duration: float, doc_count: int) -> None:
    """Record metrics for a retrieval query."""
    RETRIEVAL_QUERIES.labels(mode=mode).inc()
    RETRIEVAL_LATENCY.labels(mode=mode).observe(duration)
    RETRIEVAL_DOCUMENTS.observe(doc_count)

def record_verifier_run(verifier_type: str, issues_found: int) -> None:
    """Record metrics for a verifier run."""
    VERIFIER_RUNS.labels(verifier_type=verifier_type).inc()
    if issues_found > 0:
        VERIFIER_ISSUES.labels(verifier_type=verifier_type).inc(issues_found)

def update_active_conversations(count: int) -> None:
    """Update the count of active conversations."""
    ACTIVE_CONVERSATIONS.set(count)

def record_conversation_end(turns: int) -> None:
    """Record metrics when a conversation ends."""
    CONVERSATION_TURNS.observe(turns)
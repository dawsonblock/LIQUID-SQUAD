"""
Response caching layer for improving performance and reducing API costs.

This module provides a simple but effective caching mechanism that stores
responses based on question hashes. The cache uses a LRU strategy with
configurable TTL and max size.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
from typing import Optional

from full_build.self_loop import SelfLoopResult


@dataclass
class CacheEntry:
    """Container for a cached response with metadata."""

    result: SelfLoopResult
    timestamp: float
    hit_count: int = 0


class ResponseCache:
    """Thread-safe LRU cache for self-loop results."""

    def __init__(self, max_size: int = 100, ttl_seconds: float = 3600.0) -> None:
        """
        Initialize the response cache.

        Args:
            max_size: Maximum number of entries to store
            ttl_seconds: Time-to-live for cache entries in seconds (default 1 hour)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def _generate_key(
        self,
        question: str,
        retrieval_mode: str = "disabled",
        max_rounds: int = 3,
        conf_threshold: float = 0.65,
    ) -> str:
        """Generate a cache key from question and parameters."""
        key_data = {
            "question": question.strip().lower(),
            "retrieval_mode": retrieval_mode,
            "max_rounds": max_rounds,
            "conf_threshold": conf_threshold,
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get(
        self,
        question: str,
        retrieval_mode: str = "disabled",
        max_rounds: int = 3,
        conf_threshold: float = 0.65,
    ) -> Optional[SelfLoopResult]:
        """
        Retrieve a cached result if available and not expired.

        Returns:
            The cached SelfLoopResult or None if not found/expired
        """
        key = self._generate_key(question, retrieval_mode, max_rounds, conf_threshold)

        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None

            # Check if entry is expired
            age = time.time() - entry.timestamp
            if age > self.ttl_seconds:
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end (mark as recently used)
            self._cache.move_to_end(key)
            entry.hit_count += 1
            self._hits += 1
            return entry.result

    def put(
        self,
        question: str,
        result: SelfLoopResult,
        retrieval_mode: str = "disabled",
        max_rounds: int = 3,
        conf_threshold: float = 0.65,
    ) -> None:
        """Store a result in the cache."""
        key = self._generate_key(question, retrieval_mode, max_rounds, conf_threshold)

        with self._lock:
            # If key exists, update it
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = CacheEntry(
                    result=result,
                    timestamp=time.time(),
                    hit_count=self._cache[key].hit_count,
                )
                return

            # Add new entry
            self._cache[key] = CacheEntry(
                result=result,
                timestamp=time.time(),
                hit_count=0,
            )

            # Evict oldest entry if cache is full
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict:
        """Return cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "total_requests": total_requests,
            }

    def prune_expired(self) -> int:
        """Remove all expired entries and return the count of removed items."""
        now = time.time()
        removed = 0

        with self._lock:
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if now - entry.timestamp > self.ttl_seconds
            ]
            for key in expired_keys:
                del self._cache[key]
                removed += 1

        return removed


# Global cache instance (can be configured via environment variables)
_global_cache: Optional[ResponseCache] = None


def get_cache() -> ResponseCache:
    """Get or create the global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = ResponseCache()
    return _global_cache


def configure_cache(max_size: int = 100, ttl_seconds: float = 3600.0) -> None:
    """Configure the global cache instance."""
    global _global_cache
    _global_cache = ResponseCache(max_size=max_size, ttl_seconds=ttl_seconds)

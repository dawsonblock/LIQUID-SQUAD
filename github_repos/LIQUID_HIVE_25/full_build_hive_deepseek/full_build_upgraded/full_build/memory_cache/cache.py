"""
Simple memory and key‑value cache.

This module provides a minimal in‑memory store to persist plans and
final answers across sessions.  The cache is a dict wrapped with TTL
logic; the long‑term memory is a list of capsules with timestamps.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import time
import threading

class KVCache:
    """A thread‑safe key–value cache with TTL support."""
    def __init__(self):
        self.store: Dict[str, Tuple[Any, float]] = {}
        self.lock = threading.Lock()

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set a value with an optional time‑to‑live in seconds."""
        exp = time.time() + ttl if ttl is not None else float("inf")
        with self.lock:
            self.store[key] = (value, exp)

    def get(self, key: str) -> Optional[Any]:
        """Get a value if it hasn't expired."""
        with self.lock:
            item = self.store.get(key)
            if not item:
                return None
            value, exp = item
            if exp < time.time():
                del self.store[key]
                return None
            return value

    def cleanup(self) -> None:
        """Remove expired items."""
        now = time.time()
        with self.lock:
            keys = [k for k, (_, exp) in self.store.items() if exp < now]
            for k in keys:
                del self.store[k]

class LongTermMemory:
    """A simple list of memory capsules with pruning."""
    def __init__(self):
        self.memories: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

    def write(self, text: str, meta: Dict[str, Any]) -> None:
        """Append a memory capsule."""
        with self.lock:
            cap_id = f"m{len(self.memories)}"
            self.memories.append({"id": cap_id,
                                  "text": text,
                                  "ts": time.time(),
                                  **meta})

    def recent(self, window: float = 300.0) -> List[Dict[str, Any]]:
        """Return memories from the last `window` seconds."""
        now = time.time()
        with self.lock:
            return [m for m in self.memories if now - m["ts"] <= window]

    def prune(self, max_age_days: float = 7.0, min_keep: int = 100) -> None:
        """Remove old memories beyond the minimum keep threshold."""
        cutoff = time.time() - max_age_days * 86400
        with self.lock:
            old = [m for m in self.memories if m["ts"] < cutoff]
            if len(self.memories) - len(old) < min_keep:
                return
            self.memories = [m for m in self.memories if m["ts"] >= cutoff]
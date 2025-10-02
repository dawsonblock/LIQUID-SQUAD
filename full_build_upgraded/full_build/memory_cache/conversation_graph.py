"""
Conversation graph representation.

This module implements a simple undirected graph to track the relationships
between memory capsules.  Each node is a memory id and edges connect
memories that were referenced within a short time window.  The graph is
used by the self‑wiring engine to compute correlations and prune or add
edges dynamically.
"""
from __future__ import annotations
from typing import Dict, Tuple
import threading
import random

import networkx as nx

class ConversationGraph:
    """Thread‑safe wrapper around a NetworkX graph."""
    def __init__(self):
        self.graph = nx.Graph()
        self.lock = threading.RLock()
        self.graph.add_node("seed", vector=None, entropy=0.0)

    def add_memory(self, mem_id: str) -> None:
        """Add a memory node and connect it to a random existing node."""
        with self.lock:
            self.graph.add_node(mem_id)
            if self.graph.nodes:
                rand = random.choice(list(self.graph.nodes))
                self.graph.add_edge(mem_id, rand)

    def remove_memory(self, mem_id: str) -> None:
        """Remove a memory node if present."""
        with self.lock:
            if mem_id in self.graph:
                self.graph.remove_node(mem_id)

    def update_edges(self, correlations: Dict[Tuple[str, str], float],
                     add_thresh: float, prune_thresh: float) -> None:
        """Update edges based on correlation values.

        Adds edges for correlations ≥ add_thresh and removes edges for
        correlations < prune_thresh.
        """
        with self.lock:
            for (a, b) in list(self.graph.edges()):
                r = correlations.get((a, b)) or correlations.get((b, a))
                if r is not None and r < prune_thresh:
                    self.graph.remove_edge(a, b)
            for (a, b), r in correlations.items():
                if r >= add_thresh and not self.graph.has_edge(a, b):
                    self.graph.add_edge(a, b, weight=float(r))
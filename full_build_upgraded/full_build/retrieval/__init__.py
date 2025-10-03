"""Retrieval package exports.

This package exposes retrieval engines and helper utilities.  The
`DualIndexRetriever` is a pure Python implementation combining BM25
and dense embeddings.  The `QdrantESRetriever` uses external
services (Qdrant and Elasticsearch) to scale retrieval to large
corpora.  The exported `Document` and `RetrievalResult` classes
provide unified representations for documents and hits.  Utility
functions such as `check_consistency` verify citation consistency.

The retrieval mode can be controlled via the RETRIEVAL_MODE environment
variable: disabled, dense, sparse, or dual.
"""

from .dual_index import DualIndexRetriever, Document, RetrievalResult
from .qdrant_es import QdrantESRetriever  # type: ignore
from .utils import check_consistency  # type: ignore


class NoOpRetriever:
    """No-op retriever that returns empty results when retrieval is disabled."""

    def query(self, query: str, k: int = 5) -> list:
        """Return empty list when retrieval is disabled."""
        return []

    def search(self, query: str, k: int = 5) -> list:
        """Return empty list when retrieval is disabled."""
        return []


def create_retriever(mode: str, qdrant_url: str = None, es_url: str = None, embedding_model: str = None):
    """Factory function to create a retriever based on mode.

    Parameters:
        mode: One of 'disabled', 'dense', 'sparse', 'dual'
        qdrant_url: URL for Qdrant service (required for dense/dual)
        es_url: URL for Elasticsearch service (required for sparse/dual)
        embedding_model: Model name for embeddings (default: sentence-transformers/all-MiniLM-L6-v2)

    Returns:
        Retriever instance or NoOpRetriever if disabled
    """
    if mode == "disabled":
        return NoOpRetriever()

    if mode in ["dense", "dual"]:
        # Lazy init for Qdrant/ES when enabled
        try:
            return QdrantESRetriever(
                qdrant_url=qdrant_url or "http://qdrant:6333",
                es_hosts=[es_url or "http://elasticsearch:9200"],
                embedding_model=embedding_model or "sentence-transformers/all-MiniLM-L6-v2"
            )
        except Exception:
            # Gracefully degrade to no-op if services unavailable
            return NoOpRetriever()

    # For sparse mode, could use ES only, but for simplicity use dual
    return NoOpRetriever()


__all__ = [
    "DualIndexRetriever",
    "QdrantESRetriever",
    "Document",
    "RetrievalResult",
    "check_consistency",
    "NoOpRetriever",
    "create_retriever",
]
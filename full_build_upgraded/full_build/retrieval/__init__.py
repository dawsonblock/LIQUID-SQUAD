"""Retrieval package exports.

This package exposes retrieval engines and helper utilities.  The
`DualIndexRetriever` is a pure Python implementation combining BM25
and dense embeddings.  The `QdrantESRetriever` uses external
services (Qdrant and Elasticsearch) to scale retrieval to large
corpora.  The exported `Document` and `RetrievalResult` classes
provide unified representations for documents and hits.  Utility
functions such as `check_consistency` verify citation consistency.
"""

from .dual_index import DualIndexRetriever, Document, RetrievalResult
from .qdrant_es import QdrantESRetriever  # type: ignore
from .utils import check_consistency  # type: ignore

__all__ = [
    "DualIndexRetriever",
    "QdrantESRetriever",
    "Document",
    "RetrievalResult",
    "check_consistency",
]
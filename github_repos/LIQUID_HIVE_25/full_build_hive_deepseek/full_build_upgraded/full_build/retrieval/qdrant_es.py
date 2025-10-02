"""Hybrid retrieval engine backed by Qdrant and Elasticsearch.

This module implements a retrieval engine that combines a dense
vector store (Qdrant) with a sparse BM25 store (Elasticsearch).
Documents are stored in both systems; at query time, results from
both stores are merged and optionally re‑ranked using a cross
encoder.  This setup scales to large corpora and allows flexible
configuration of weighting between dense and sparse components.

Usage:

```python
from full_build.retrieval.qdrant_es import Document, QdrantESRetriever

docs = [Document(id="doc1", text="The sky is blue", metadata={"source": "wiki"}), ...]
retriever = QdrantESRetriever(
    qdrant_url="http://localhost:6333",
    es_hosts=["http://localhost:9200"],
)
retriever.index(docs)
results = retriever.query("What colour is the sky?", k=5)
for res in results:
    print(res.id, res.score)
```

This implementation requires the `qdrant-client`, `elasticsearch`,
`sentence-transformers` and `transformers` libraries.  If they are
missing, fallback behaviour will be used (random embeddings and
sparse scoring only).  See the README for more details on
deployment.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Iterable, Optional
import logging

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct, VectorParams
except ImportError:  # pragma: no cover
    QdrantClient = None  # type: ignore
    PointStruct = None  # type: ignore
    VectorParams = None  # type: ignore

try:
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import bulk
except ImportError:  # pragma: no cover
    Elasticsearch = None  # type: ignore
    bulk = None  # type: ignore

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover
    SentenceTransformer = None  # type: ignore

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
except ImportError:  # pragma: no cover
    AutoTokenizer = None  # type: ignore
    AutoModelForSequenceClassification = None  # type: ignore
    torch = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Representation of a text document."""
    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """Result returned by a retrieval query."""
    id: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class QdrantESRetriever:
    """Hybrid retriever using Qdrant for dense and Elasticsearch for sparse."""

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        es_hosts: Optional[list[str]] = None,
        collection_name: str = "docs",
        es_index: str = "docs",
        embedding_model_name: str = "intfloat/e5-small",
        reranker_model_name: str = "BAAI/bge-reranker-base",
        embedding_dim: int = 384,
    ) -> None:
        self.collection_name = collection_name
        self.es_index = es_index
        # initialise Qdrant client if available
        if QdrantClient is not None:
            self.qdrant = QdrantClient(url=qdrant_url)
            # Create collection if not exists
            try:
                self.qdrant.get_collection(collection_name)
            except Exception:
                self.qdrant.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=embedding_dim, distance="cosine"),
                )
        else:
            self.qdrant = None
        # initialise Elasticsearch client if available
        if es_hosts is not None and Elasticsearch is not None:
            self.es = Elasticsearch(es_hosts)
            # Create index with BM25 similarity if not exists
            if not self.es.indices.exists(index=es_index):
                self.es.indices.create(index=es_index, body={
                    "mappings": {
                        "properties": {
                            "text": {"type": "text", "analyzer": "standard"},
                            "metadata": {"type": "object"},
                        }
                    }
                })
        else:
            self.es = None
        # load embedding model
        if SentenceTransformer is not None:
            try:
                self.embedding_model = SentenceTransformer(embedding_model_name)
            except Exception as exc:
                logger.warning("Failed to load embedding model %s: %s", embedding_model_name, exc)
                self.embedding_model = None
        else:
            self.embedding_model = None
        # load reranker model
        if AutoTokenizer is not None and AutoModelForSequenceClassification is not None:
            try:
                self.reranker_tokenizer = AutoTokenizer.from_pretrained(reranker_model_name)
                self.reranker_model = AutoModelForSequenceClassification.from_pretrained(reranker_model_name)
                # Use CPU by default; adjust as needed
                self.reranker_model.eval()
            except Exception as exc:
                logger.warning("Failed to load reranker model %s: %s", reranker_model_name, exc)
                self.reranker_tokenizer = None
                self.reranker_model = None
        else:
            self.reranker_tokenizer = None
            self.reranker_model = None

    def _embed(self, texts: List[str]) -> List[List[float]]:
        if self.embedding_model is not None:
            return self.embedding_model.encode(texts, normalize_embeddings=True).tolist()
        # fallback to random embeddings for demonstration
        import numpy as np
        np.random.seed(42)
        return np.random.randn(len(texts), 384).astype(float).tolist()

    def _rerank(self, query: str, candidates: List[RetrievalResult]) -> List[RetrievalResult]:
        """Apply cross‑encoder reranking to a list of candidates.

        The reranker model scores each candidate pair (query, doc) and
        reorders them by descending score.  If no reranker is available,
        candidates are returned unchanged.
        """
        if self.reranker_model is None or self.reranker_tokenizer is None or torch is None:
            return candidates
        # Build inputs for the cross encoder: [CLS] query [SEP] doc
        pairs = [(query, c.metadata.get("text", "")) for c in candidates]
        inputs = self.reranker_tokenizer(
            [q for q, d in pairs], [d for q, d in pairs],
            padding=True, truncation=True, return_tensors="pt"
        )
        with torch.no_grad():
            scores = self.reranker_model(**inputs).logits.squeeze().tolist()
        # assign new scores and sort
        for c, s in zip(candidates, scores):
            c.score = float(s)
        return sorted(candidates, key=lambda x: x.score, reverse=True)

    def index(self, docs: Iterable[Document]) -> None:
        """Index documents in both Qdrant and Elasticsearch."""
        docs = list(docs)
        if self.qdrant is not None:
            vectors = self._embed([d.text for d in docs])
            points = [
                PointStruct(id=d.id, vector=vec, payload={"metadata": d.metadata, "text": d.text})
                for d, vec in zip(docs, vectors)
            ]
            self.qdrant.upsert(collection_name=self.collection_name, points=points)
        if self.es is not None and bulk is not None:
            actions = []
            for d in docs:
                actions.append({
                    "_op_type": "index",
                    "_index": self.es_index,
                    "_id": d.id,
                    "text": d.text,
                    "metadata": d.metadata,
                })
            if actions:
                bulk(self.es, actions)

    def query(self, query: str, k: int = 5, alpha: float = 0.5) -> List[RetrievalResult]:
        """Query both stores and return top‑k combined results.

        Parameters:
            query: Query string.
            k: Number of results to return.
            alpha: Weight between dense and sparse scores (0..1).

        Returns:
            List of top‑k RetrievalResult objects sorted by combined score.
        """
        results: Dict[str, RetrievalResult] = {}
        # Dense search via Qdrant
        if self.qdrant is not None:
            query_vec = self._embed([query])[0]
            dense_hits = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_vec,
                limit=max(k * 5, 10),
                with_payload=True,
            )
            for hit in dense_hits:
                meta = hit.payload or {}
                score = 1.0 - hit.score  # Qdrant returns distance; invert for similarity
                results[hit.id] = RetrievalResult(id=hit.id, score=alpha * score, metadata=meta)
        # Sparse search via Elasticsearch
        if self.es is not None:
            try:
                resp = self.es.search(index=self.es_index, body={
                    "query": {"match": {"text": query}},
                    "size": max(k * 5, 10),
                })
                for hit in resp["hits"]["hits"]:
                    doc_id = hit["_id"]
                    score = hit["_score"] or 0.0
                    meta = hit["_source"]
                    # combine with any existing dense score
                    combined = results.get(doc_id)
                    if combined:
                        combined.score += (1.0 - alpha) * score
                    else:
                        results[doc_id] = RetrievalResult(
                            id=doc_id,
                            score=(1.0 - alpha) * score,
                            metadata=meta,
                        )
            except Exception as exc:
                logger.warning("Elasticsearch query failed: %s", exc)
        # Convert to list and sort
        ranked = sorted(results.values(), key=lambda x: x.score, reverse=True)
        ranked = ranked[: max(k * 2, len(ranked))]
        # Rerank with cross encoder if available
        reranked = self._rerank(query, ranked)[:k]
        return reranked
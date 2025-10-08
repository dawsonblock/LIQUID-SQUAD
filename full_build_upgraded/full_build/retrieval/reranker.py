"""
Cross-encoder reranker for improving retrieval quality.

This module implements a reranking layer that scores retrieved documents
against the query using a cross-encoder model for better relevance ranking.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, List, Optional

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False


@dataclass
class ScoredDocument:
    """A document with relevance score."""

    doc: Any
    score: float
    original_rank: int


class Reranker:
    """Base class for rerankers."""

    async def rerank(
        self, query: str, documents: List[Any], top_k: Optional[int] = None
    ) -> List[Any]:
        """
        Rerank documents based on relevance to query.

        Args:
            query: The search query
            documents: List of documents to rerank
            top_k: Number of top documents to return (None = all)

        Returns:
            Reranked list of documents
        """
        raise NotImplementedError


class CrossEncoderReranker(Reranker):
    """Reranker using a cross-encoder model for scoring."""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        max_length: int = 512,
        device: Optional[str] = None,
    ) -> None:
        """
        Initialize the cross-encoder reranker.

        Args:
            model_name: HuggingFace model name for the cross-encoder
            max_length: Maximum sequence length
            device: Device to use (cpu/cuda/mps), auto-detected if None
        """
        if not CROSS_ENCODER_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for CrossEncoderReranker. "
                "Install with: pip install sentence-transformers"
            )

        self.model_name = model_name
        self.max_length = max_length
        self._model: Optional[CrossEncoder] = None
        self._device = device

    def _ensure_model_loaded(self) -> CrossEncoder:
        """Lazy load the model."""
        if self._model is None:
            self._model = CrossEncoder(
                self.model_name,
                max_length=self.max_length,
                device=self._device,
            )
        return self._model

    def _extract_text(self, doc: Any) -> str:
        """Extract text from a document object."""
        if isinstance(doc, str):
            return doc
        elif hasattr(doc, "text"):
            return doc.text
        elif hasattr(doc, "content"):
            return doc.content
        elif hasattr(doc, "page_content"):
            return doc.page_content
        elif isinstance(doc, dict):
            # Try common keys
            for key in ["text", "content", "page_content", "body"]:
                if key in doc:
                    return str(doc[key])
        return str(doc)

    async def rerank(
        self,
        query: str,
        documents: List[Any],
        top_k: Optional[int] = None,
        batch_size: int = 32,
    ) -> List[Any]:
        """
        Rerank documents using cross-encoder scoring.

        Args:
            query: The search query
            documents: List of documents to rerank
            top_k: Number of top documents to return (None = all)
            batch_size: Batch size for model inference

        Returns:
            Reranked list of documents
        """
        if not documents:
            return []

        # Ensure model is loaded
        model = self._ensure_model_loaded()

        # Prepare query-document pairs
        doc_texts = [self._extract_text(doc) for doc in documents]
        query_doc_pairs = [(query, text) for text in doc_texts]

        # Run inference in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            None,
            lambda: model.predict(query_doc_pairs, batch_size=batch_size),
        )

        # Create scored documents
        scored_docs = [
            ScoredDocument(doc=doc, score=float(score), original_rank=i)
            for i, (doc, score) in enumerate(zip(documents, scores))
        ]

        # Sort by score (descending)
        scored_docs.sort(key=lambda x: x.score, reverse=True)

        # Return top-k documents
        if top_k is not None:
            scored_docs = scored_docs[:top_k]

        return [sd.doc for sd in scored_docs]

    async def score(
        self, query: str, document: Any
    ) -> float:
        """
        Score a single document against a query.

        Args:
            query: The search query
            document: The document to score

        Returns:
            Relevance score (higher is better)
        """
        results = await self.rerank(query, [document], top_k=1)
        if results:
            # Extract score from the scored document
            model = self._ensure_model_loaded()
            doc_text = self._extract_text(document)
            score = model.predict([(query, doc_text)])[0]
            return float(score)
        return 0.0


class BM25Reranker(Reranker):
    """Simple reranker using BM25 scoring (no ML model required)."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        """
        Initialize BM25 reranker.

        Args:
            k1: BM25 k1 parameter (term frequency saturation)
            b: BM25 b parameter (length normalization)
        """
        self.k1 = k1
        self.b = b

    def _extract_text(self, doc: Any) -> str:
        """Extract text from a document object."""
        if isinstance(doc, str):
            return doc
        elif hasattr(doc, "text"):
            return doc.text
        elif hasattr(doc, "content"):
            return doc.content
        return str(doc)

    def _tokenize(self, text: str) -> List[str]:
        """Simple whitespace tokenization."""
        return text.lower().split()

    def _compute_bm25(
        self,
        query_terms: List[str],
        doc_terms: List[str],
        avgdl: float,
    ) -> float:
        """Compute BM25 score for a document."""
        score = 0.0
        doc_len = len(doc_terms)

        # Term frequency in document
        term_freqs = {}
        for term in doc_terms:
            term_freqs[term] = term_freqs.get(term, 0) + 1

        for term in query_terms:
            if term in term_freqs:
                tf = term_freqs[term]
                # Simplified BM25 (without IDF component)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / avgdl))
                score += numerator / denominator

        return score

    async def rerank(
        self, query: str, documents: List[Any], top_k: Optional[int] = None
    ) -> List[Any]:
        """
        Rerank documents using BM25 scoring.

        Args:
            query: The search query
            documents: List of documents to rerank
            top_k: Number of top documents to return

        Returns:
            Reranked list of documents
        """
        if not documents:
            return []

        # Extract texts and tokenize
        query_terms = self._tokenize(query)
        doc_texts = [self._extract_text(doc) for doc in documents]
        doc_terms_list = [self._tokenize(text) for text in doc_texts]

        # Calculate average document length
        avgdl = sum(len(terms) for terms in doc_terms_list) / len(doc_terms_list)

        # Score documents
        scored_docs = [
            ScoredDocument(
                doc=doc,
                score=self._compute_bm25(query_terms, doc_terms, avgdl),
                original_rank=i,
            )
            for i, (doc, doc_terms) in enumerate(zip(documents, doc_terms_list))
        ]

        # Sort by score (descending)
        scored_docs.sort(key=lambda x: x.score, reverse=True)

        # Return top-k documents
        if top_k is not None:
            scored_docs = scored_docs[:top_k]

        return [sd.doc for sd in scored_docs]


class NoOpReranker(Reranker):
    """Pass-through reranker that returns documents as-is."""

    async def rerank(
        self, query: str, documents: List[Any], top_k: Optional[int] = None
    ) -> List[Any]:
        """Return documents without reranking."""
        if top_k is not None:
            return documents[:top_k]
        return documents


def create_reranker(
    reranker_type: str = "cross-encoder",
    model_name: Optional[str] = None,
    **kwargs,
) -> Reranker:
    """
    Factory function to create a reranker.

    Args:
        reranker_type: Type of reranker ("cross-encoder", "bm25", "none")
        model_name: Model name for cross-encoder (optional)
        **kwargs: Additional arguments for the reranker

    Returns:
        A Reranker instance
    """
    if reranker_type == "cross-encoder":
        if not CROSS_ENCODER_AVAILABLE:
            # Fallback to BM25 if cross-encoder not available
            return BM25Reranker(**kwargs)

        reranker_model = model_name or "cross-encoder/ms-marco-MiniLM-L-6-v2"
        return CrossEncoderReranker(model_name=reranker_model, **kwargs)

    elif reranker_type == "bm25":
        return BM25Reranker(**kwargs)

    elif reranker_type == "none":
        return NoOpReranker()

    else:
        raise ValueError(
            f"Unknown reranker type: {reranker_type}. "
            "Use 'cross-encoder', 'bm25', or 'none'"
        )

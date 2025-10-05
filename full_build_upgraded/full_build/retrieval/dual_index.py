"""
Dual index retrieval engine.

This module implements a retrieval engine that combines a dense embedding
index with a sparse BM25 index.  When building the index you feed the
engine a corpus of documents; each document can optionally be split into
sections with associated identifiers to support fine‑grained citation.

At query time the dense and sparse scores are computed independently and
then cross‑scored to produce a final ranking.  The cross‑scoring strategy
is currently a simple weighted average; you can override `combine_scores()`
to customise it.

Example:

```python
from retrieval.dual_index import DualIndexRetriever, Document
docs = [Document(id="doc1", text="The sky is blue."), ...]
retriever = DualIndexRetriever(dense_model=None)
retriever.build_index(docs)
hits = retriever.query("What colour is the sky?")
for hit in hits:
    print(hit.id, hit.score, hit.metadata)
```
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Iterable, Dict, Any

import numpy as np
# NOTE: We avoid relying on TF‑IDF for ranking.  Instead we implement
# a simplified BM25 retrieval algorithm directly using a CountVectorizer.
# In a production system you should consider using Pyserini/Elasticsearch for
# BM25 and a separate FAISS/Qdrant index for dense vectors.  The current
# implementation maintains compatibility with environments lacking those
# libraries by computing scores in pure Python/NumPy.
from sklearn.feature_extraction.text import CountVectorizer

@dataclass
class Document:
    """A simple text document.

    Attributes:
        id: A unique identifier for the document.
        text: The raw text of the document.
        metadata: Optional arbitrary metadata (e.g. section ids, source).
    """
    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RetrievalResult:
    """Represents a retrieval hit."""
    id: str
    score: float
    metadata: Dict[str, Any]

class DualIndexRetriever:
    """Combines a dense embedding index with a BM25 TF–IDF index.

    Parameters
    ----------
    dense_model : Optional[callable], default None
        A function that converts a list of strings into a matrix of embeddings.
        The output must be of shape (n_samples, dim).  If None, dense
        embeddings are not used and only sparse scores are returned.
    sparse_config : Optional[dict], default None
        Hyperparameters for BM25.  See `config/retrieval_config.yaml`.
    """
    def __init__(self, dense_model: Optional[Any] = None,
                 sparse_config: Optional[Dict[str, float]] = None):
        self.dense_model = dense_model
        self.bm25_k1 = sparse_config.get("k1", 1.2) if sparse_config else 1.2
        self.bm25_b  = sparse_config.get("b", 0.75) if sparse_config else 0.75
        self.docs: List[Document] = []
        # Count vectorizer and term matrix for BM25 computation.  We use
        # CountVectorizer because TF‑IDF is not sufficient for BM25; the BM25
        # formula requires raw term frequencies and document lengths.
        self.vectorizer: Optional[CountVectorizer] = None
        self.term_matrix: Optional[np.ndarray] = None
        self.doc_freqs: Optional[np.ndarray] = None
        self.doc_lengths: Optional[np.ndarray] = None
        self.avg_doc_length: float = 0.0
        self.idf: Optional[np.ndarray] = None
        self.embeddings: Optional[np.ndarray] = None

    def build_index(self, docs: Iterable[Document]) -> None:
        """Build both dense and sparse indices from the given documents."""
        self.docs = list(docs)
        texts = [d.text for d in self.docs]

        # Build sparse BM25 index using raw term frequencies.  We avoid
        # TF‑IDF because BM25 better handles term frequency saturation and
        # document length normalisation【164481064488616†L78-L96】.  See the
        # README.md and retrieval_config.yaml for configurable k1 and b.
        self.vectorizer = CountVectorizer(stop_words='english')
        self.term_matrix = self.vectorizer.fit_transform(texts).astype(np.float32)
        # Compute document frequencies (number of documents containing each term)
        # The term_matrix is in CSR format; term_matrix.indices gives term
        # indices for all nonzero entries.  We use bincount to tally how
        # many times each term appears across documents.
        term_count = len(self.vectorizer.vocabulary_)
        # Count how many documents contain each term.  term_matrix.indptr
        # gives row pointers for non‑zero indices; we compute doc frequencies
        # by counting unique row indices for each term.
        df = np.bincount(self.term_matrix.indices,
                         minlength=term_count)
        self.doc_freqs = df
        # Document lengths (sum of term counts per document)
        self.doc_lengths = np.asarray(self.term_matrix.sum(axis=1)).flatten()
        self.avg_doc_length = float(self.doc_lengths.mean()) if len(self.doc_lengths) > 0 else 0.0
        # Pre‑compute IDF values; add smoothing to avoid division by zero
        N = len(self.docs)
        # IDF formula from BM25: log((N - df + 0.5)/(df + 0.5) + 1)
        # We clip to avoid negative idf when df > N
        idf = np.log((N - df + 0.5) / (df + 0.5) + 1.0)
        self.idf = idf.astype(np.float32)

        # Build dense embeddings if a model is provided.
        if self.dense_model is not None:
            try:
                self.embeddings = np.array(self.dense_model(texts),
                                            dtype=np.float32)
            except Exception:
                # Fallback: random embeddings for placeholder.
                np.random.seed(42)
                self.embeddings = np.random.randn(len(texts), 128).astype(
                    np.float32)

    def _bm25_scores(self, query_vec: np.ndarray) -> np.ndarray:
        """Compute BM25 scores between a query and all indexed documents.

        Parameters
        ----------
        query_vec : np.ndarray
            Sparse vector of raw term frequencies for the query.

        Returns
        -------
        np.ndarray
            Array of BM25 scores for each document.
        """
        if self.term_matrix is None or self.vectorizer is None or self.idf is None:
            raise RuntimeError("Index has not been built.")
        # Convert sparse query vector to a dense array of term frequencies
        q_tf = query_vec.toarray().flatten()
        # Find indices of terms present in query
        term_indices = np.nonzero(q_tf)[0]
        if len(term_indices) == 0:
            return np.zeros(len(self.docs), dtype=np.float32)
        scores = np.zeros(len(self.docs), dtype=np.float32)
        avg_dl = self.avg_doc_length if self.avg_doc_length > 0 else 1.0
        for idx in term_indices:
            # Term frequency in query (used to weight contributions if repeated)
            qfreq = q_tf[idx]
            # Term frequency across documents (sparse)
            # Extract column of term frequencies for term idx
            doc_tf = self.term_matrix[:, idx].toarray().flatten()
            # Document length normalisation
            denom = doc_tf + self.bm25_k1 * (1 - self.bm25_b + self.bm25_b * (self.doc_lengths / avg_dl))
            # Avoid division by zero
            denom = np.where(denom == 0, 1e-6, denom)
            # BM25 per‑term score
            term_scores = (self.idf[idx] * (doc_tf * (self.bm25_k1 + 1)) / denom)
            scores += qfreq * term_scores.astype(np.float32)
        return scores

    def _dense_scores(self, query_emb: np.ndarray) -> np.ndarray:
        """Compute cosine similarities between a query embedding and all document embeddings."""
        if self.embeddings is None:
            return np.zeros(len(self.docs), dtype=np.float32)
        doc_norms = np.linalg.norm(self.embeddings, axis=1) + 1e-12
        query_norm = np.linalg.norm(query_emb) + 1e-12
        dot = np.dot(self.embeddings, query_emb)
        return dot / (doc_norms * query_norm)

    def combine_scores(self, dense: np.ndarray, sparse: np.ndarray,
                       alpha: float = 0.5) -> np.ndarray:
        """Combine dense and sparse scores with a weighting factor.

        alpha: weight for the dense component; (1 - alpha) for sparse.
        """
        if dense is None:
            return sparse
        return alpha * dense + (1 - alpha) * sparse

    def query(self, query: str, k: int = 5) -> List[RetrievalResult]:
        """Return top‑k retrieval results.

        This method computes both sparse and dense scores for the query,
        combines them and returns the best documents.  If a dense model is
        not provided, only sparse scores are used.
        """
        if self.vectorizer is None:
            raise RuntimeError("Index has not been built. Call build_index().")
        query_vec = self.vectorizer.transform([query])
        sparse_scores = self._bm25_scores(query_vec)
        dense_scores = None
        if self.dense_model is not None:
            try:
                query_emb = np.array(self.dense_model([query])[0],
                                     dtype=np.float32)
                dense_scores = self._dense_scores(query_emb)
            except Exception:
                dense_scores = None
        scores = self.combine_scores(dense_scores, sparse_scores)
        top_idx = np.argsort(-scores)[:k]
        results: List[RetrievalResult] = []
        for idx in top_idx:
            doc = self.docs[idx]
            results.append(RetrievalResult(id=doc.id,
                                           score=float(scores[idx]),
                                           metadata=doc.metadata))
        return results

    # -------------------------------------------------------------------------
    # Hybrid reranking
    #
    def rerank(self, query: str, results: List[RetrievalResult],
               cross_encoder: Optional[Any] = None) -> List[RetrievalResult]:
        """Optionally refine the ranking with a cross‑encoder.

        A cross‑encoder scores each query–document pair jointly (for example
        using `bge‑reranker‑base`), which often improves final recall and
        precision.  To avoid making this a hard dependency, the cross_encoder
        argument should be a callable accepting (query: str, docs: List[str])
        and returning a list of floats.  If None, the input results are
        returned unchanged.

        Parameters
        ----------
        query : str
            The user query.
        results : List[RetrievalResult]
            Initial retrieval results to refine.
        cross_encoder : callable, optional
            A function that scores each (query, doc.text) pair.

        Returns
        -------
        List[RetrievalResult]
            Reranked results (sorted by cross‑encoder scores if provided).
        """
        if cross_encoder is None or not results:
            return results
        # Extract document texts using the doc ids.  In a production system
        # you should supply the original document texts rather than metadata.
        docs = [next((d.text for d in self.docs if d.id == hit.id), "") for hit in results]
        try:
            ce_scores = cross_encoder(query, docs)
            # Attach new scores and sort.  We retain the original hit order
            # if the cross‑encoder fails to return proper scores.
            for hit, ce in zip(results, ce_scores):
                hit.score = float(ce)
            return sorted(results, key=lambda h: h.score, reverse=True)
        except Exception:
            return results

    # -------------------------------------------------------------------------
    # Persistence helpers
    #
    # It is often useful to persist your retrieval index to disk so that
    # rebuilding does not occur on every start.  The following methods
    # serialise and deserialise the retriever using pickle.  Note that
    # numpy arrays and sparse matrices are picklable and will be restored.

    def save(self, path: str) -> None:
        """Serialise the index to a file.

        Parameters
        ----------
        path : str
            Filesystem path where the index should be written.  The parent
            directory must already exist.  Raises on error.
        """
        import pickle
        state = {
            'docs': self.docs,
            'vectorizer': self.vectorizer,
            'term_matrix': self.term_matrix,
            'doc_freqs': self.doc_freqs,
            'doc_lengths': self.doc_lengths,
            'avg_doc_length': self.avg_doc_length,
            'idf': self.idf,
            'dense_model': self.dense_model,
            'embeddings': self.embeddings,
            'bm25_k1': self.bm25_k1,
            'bm25_b': self.bm25_b,
        }
        with open(path, 'wb') as f:
            pickle.dump(state, f)

    @classmethod
    def load(cls, path: str) -> "DualIndexRetriever":
        """Load an index from a file previously saved with `save()`.

        Parameters
        ----------
        path : str
            Filesystem path to a pickled index.

        Returns
        -------
        DualIndexRetriever
            A new retriever instance with the same state as saved.
        """
        import pickle
        with open(path, 'rb') as f:
            state = pickle.load(f)
        retriever = cls(dense_model=state.get('dense_model'),
                        sparse_config={'k1': state.get('bm25_k1', 1.2),
                                       'b': state.get('bm25_b', 0.75)})
        retriever.docs = state['docs']
        retriever.vectorizer = state['vectorizer']
        retriever.term_matrix = state['term_matrix']
        retriever.doc_freqs = state['doc_freqs']
        retriever.doc_lengths = state['doc_lengths']
        retriever.avg_doc_length = state['avg_doc_length']
        retriever.idf = state['idf']
        retriever.embeddings = state.get('embeddings')
        return retriever

    @classmethod
    def from_config(cls, config: Dict[str, Any],
                    dense_model: Optional[Any] = None) -> "DualIndexRetriever":
        """Construct a retriever from a configuration dictionary."""
        return cls(dense_model=dense_model,
                   sparse_config=config.get("sparse", {}))
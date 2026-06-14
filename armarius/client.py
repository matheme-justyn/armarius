"""Programmatic client for Armarius indexing and querying.

A thin, importable wrapper over the storage + agent stack, intended for
scripts and evaluations that need an in-process API (rather than the Click
CLI). Heavy dependencies are imported lazily so importing this module stays
cheap until a client is actually constructed.
"""

from pathlib import Path
from typing import Optional, Union


class ArmariusClient:
    """In-process client exposing ``index()`` and ``query()``.

    Backed by :class:`armarius.storage.DocumentIndexer` and
    :class:`armarius.storage.SemanticSearch`. Construction loads the embedding
    model and opens the local vector store, so create one client and reuse it.
    """

    def __init__(self, top_k: int = 5) -> None:
        from armarius.storage import (
            DocumentIndexer,
            Embedder,
            SemanticSearch,
            VectorStore,
        )

        self._top_k = top_k
        embedder = Embedder()
        vector_store = VectorStore(embedding_dim=embedder.dimension)
        self._indexer = DocumentIndexer(embedder=embedder, vector_store=vector_store)
        self._search = SemanticSearch(embedder=embedder, vector_store=vector_store)

    def index(self, pdf_path: Union[str, Path], chunk_size: int = 512) -> int:
        """Index a single PDF; returns the number of chunks stored."""
        return self._indexer.index_pdf(Path(pdf_path), chunk_size=chunk_size)

    def query(self, text: str, top_k: Optional[int] = None) -> str:
        """Semantic search; returns the concatenated text of the top matches.

        The return value is a plain string so callers can stringify or slice it
        directly (e.g. for PII/leakage checks in security evaluations).
        """
        from armarius.storage import SearchQuery

        results = self._search.search(
            SearchQuery(text=text, top_k=top_k or self._top_k)
        )
        return "\n\n".join(r.chunk.text for r in results)

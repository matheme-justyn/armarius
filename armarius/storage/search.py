"""Semantic search service."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from armarius.parser import TextChunk
from armarius.storage import Embedder, VectorStore, SearchFilters, SearchResult


@dataclass
class SearchQuery:
    text: str
    top_k: int = 10
    pdf_path: Optional[str] = None
    page_range: Optional[tuple[int, int]] = None


class SemanticSearch:
    def __init__(
        self,
        embedder: Optional[Embedder] = None,
        vector_store: Optional[VectorStore] = None,
    ):
        self.embedder = embedder or Embedder()
        self.vector_store = vector_store or VectorStore(
            embedding_dim=self.embedder.dimension
        )

    def search(self, query: SearchQuery) -> List[SearchResult]:
        query_embedding = self.embedder.embed_text(query.text)

        filters = SearchFilters(
            pdf_path=query.pdf_path,
            page_range=query.page_range,
        )

        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=query.top_k,
            filters=filters if (query.pdf_path or query.page_range) else None,
        )

        return results

    def search_by_pdf(self, query_text: str, pdf_path: Path, top_k: int = 10) -> List[SearchResult]:
        return self.search(
            SearchQuery(
                text=query_text,
                top_k=top_k,
                pdf_path=str(pdf_path),
            )
        )

    def search_by_page_range(
        self,
        query_text: str,
        page_start: int,
        page_end: int,
        top_k: int = 10,
    ) -> List[SearchResult]:
        return self.search(
            SearchQuery(
                text=query_text,
                top_k=top_k,
                page_range=(page_start, page_end),
            )
        )

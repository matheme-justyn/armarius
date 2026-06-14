"""Vector store interface for Qdrant integration."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
)

from armarius.parser import TextChunk


@dataclass
class SearchFilters:
    pdf_path: Optional[str] = None
    page_range: Optional[tuple[int, int]] = None
    chunk_ids: Optional[List[str]] = None


@dataclass
class SearchResult:
    chunk: TextChunk
    score: float
    chunk_id: str


class VectorStore:
    def __init__(
        self,
        collection_name: str = "armarius_chunks",
        data_dir: Optional[Path] = None,
        embedding_dim: int = 384,
    ):
        self.collection_name = collection_name
        self.data_dir = data_dir or Path.home() / ".armarius" / "qdrant"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = QdrantClient(path=str(self.data_dir))
        self._ensure_collection(embedding_dim)

    def _ensure_collection(self, embedding_dim: int):
        collections = self.client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
            )

    def add_chunk(self, chunk: TextChunk, embedding: List[float]) -> str:
        chunk_id = chunk.chunk_id or str(uuid4())
        
        point = PointStruct(
            id=chunk_id,
            vector=embedding,
            payload={
                "text": chunk.text,
                "pdf_path": chunk.pdf_path,
                "page": chunk.bbox.page,
                "bbox": chunk.bbox.to_dict(),
            },
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )
        
        return chunk_id

    def add_chunks_batch(
        self, chunks: List[TextChunk], embeddings: List[List[float]]
    ) -> List[str]:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have same length")
        
        chunk_ids = []
        points = []
        
        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = chunk.chunk_id or str(uuid4())
            chunk_ids.append(chunk_id)
            
            points.append(
                PointStruct(
                    id=chunk_id,
                    vector=embedding,
                    payload={
                        "text": chunk.text,
                        "pdf_path": chunk.pdf_path,
                        "page": chunk.bbox.page,
                        "bbox": chunk.bbox.to_dict(),
                    },
                )
            )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        
        return chunk_ids

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[SearchFilters] = None,
    ) -> List[SearchResult]:
        search_filter = self._build_filter(filters) if filters else None
        
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=top_k,
            query_filter=search_filter,
        ).points
        
        return [
            SearchResult(
                chunk=self._payload_to_chunk(r.payload),
                score=r.score,
                chunk_id=str(r.id),
            )
            for r in results
        ]

    def _build_filter(self, filters: SearchFilters) -> Optional[Filter]:
        conditions = []
        
        if filters.pdf_path:
            conditions.append(
                FieldCondition(
                    key="pdf_path",
                    match=MatchValue(value=filters.pdf_path),
                )
            )
        
        if filters.page_range:
            start, end = filters.page_range
            conditions.append(
                FieldCondition(
                    key="page",
                    range=Range(gte=start, lte=end),
                )
            )
        
        if filters.chunk_ids:
            return None
        
        if not conditions:
            return None
        
        return Filter(must=conditions)

    def _payload_to_chunk(self, payload: Dict) -> TextChunk:
        from armarius.parser.pdf_parser import BoundingBox
        
        bbox_data = payload["bbox"]
        bbox = BoundingBox(
            x0=bbox_data["x0"],
            y0=bbox_data["y0"],
            x1=bbox_data["x1"],
            y1=bbox_data["y1"],
            page=bbox_data["page"],
        )
        
        return TextChunk(
            text=payload["text"],
            bbox=bbox,
            pdf_path=payload["pdf_path"],
        )

    def delete_by_pdf(self, pdf_path: str):
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="pdf_path",
                        match=MatchValue(value=pdf_path),
                    )
                ]
            ),
        )

    def count(self) -> int:
        return self.client.count(collection_name=self.collection_name).count

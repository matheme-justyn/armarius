"""Document indexing pipeline."""

from pathlib import Path
from typing import List, Optional

from armarius.parser import PDFParser, ChunkingStrategy
from armarius.storage import Embedder, VectorStore, EmbeddingConfig


class DocumentIndexer:
    def __init__(
        self,
        embedder: Optional[Embedder] = None,
        vector_store: Optional[VectorStore] = None,
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.BLOCK,
    ):
        self.embedder = embedder or Embedder()
        self.vector_store = vector_store or VectorStore(
            embedding_dim=self.embedder.dimension
        )
        self.chunking_strategy = chunking_strategy
        self.parser = PDFParser()

    def index_pdf(self, pdf_path: Path, chunk_size: int = 512, overlap: int = 50) -> int:
        chunks = self.parser.extract_all(
            pdf_path=pdf_path,
            strategy=self.chunking_strategy,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        if not chunks:
            return 0

        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedder.embed_batch(texts)

        chunk_ids = self.vector_store.add_chunks_batch(chunks, embeddings)

        for chunk, chunk_id in zip(chunks, chunk_ids):
            chunk.chunk_id = chunk_id

        return len(chunks)

    def index_directory(
        self,
        directory: Path,
        chunk_size: int = 512,
        overlap: int = 50,
        pattern: str = "*.pdf",
    ) -> dict[str, int]:
        results = {}

        for pdf_file in directory.rglob(pattern):
            if pdf_file.is_file():
                try:
                    count = self.index_pdf(pdf_file, chunk_size, overlap)
                    results[str(pdf_file)] = count
                except Exception as e:
                    results[str(pdf_file)] = -1

        return results

    def reindex_pdf(self, pdf_path: Path, chunk_size: int = 512, overlap: int = 50) -> int:
        self.vector_store.delete_by_pdf(str(pdf_path))
        return self.index_pdf(pdf_path, chunk_size, overlap)

    def total_chunks(self) -> int:
        return self.vector_store.count()

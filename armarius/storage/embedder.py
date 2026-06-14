"""Embedding service using sentence-transformers."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from sentence_transformers import SentenceTransformer


@dataclass
class EmbeddingConfig:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    device: Optional[str] = None
    cache_dir: Optional[Path] = None


class Embedder:
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            cache_folder = str(self.config.cache_dir) if self.config.cache_dir else None
            self._model = SentenceTransformer(
                self.config.model_name,
                device=self.config.device,
                cache_folder=cache_folder,
            )
        return self._model

    @property
    def dimension(self) -> int:
        return self.model.get_embedding_dimension()

    def embed_text(self, text: str) -> List[float]:
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True,
        )
        return [emb.tolist() for emb in embeddings]

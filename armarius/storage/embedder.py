"""Embedding service using sentence-transformers."""

from dataclasses import dataclass
import hashlib
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
        self._fallback_dimension = 384

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            cache_folder = str(self.config.cache_dir) if self.config.cache_dir else None
            try:
                self._model = SentenceTransformer(
                    self.config.model_name,
                    device=self.config.device,
                    cache_folder=cache_folder,
                )
            except Exception:
                self._model = None
        return self._model

    @property
    def dimension(self) -> int:
        if self.model is None:
            return self._fallback_dimension
        return self.model.get_embedding_dimension()

    def _fallback_embed(self, text: str) -> List[float]:
        """Deterministic offline embedding fallback for tests and no-network runs."""
        if not text:
            text = " "
        values: List[float] = []
        counter = 0
        while len(values) < self._fallback_dimension:
            digest = hashlib.sha256(f"{text}\0{counter}".encode("utf-8")).digest()
            for index in range(0, len(digest), 4):
                chunk = digest[index:index + 4]
                number = int.from_bytes(chunk, "big", signed=False)
                values.append((number / 4294967295.0) * 2.0 - 1.0)
                if len(values) == self._fallback_dimension:
                    break
            counter += 1
        return values

    def embed_text(self, text: str) -> List[float]:
        if self.model is None:
            return self._fallback_embed(text)
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        if self.model is None:
            return [self._fallback_embed(text) for text in texts]
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True,
        )
        return [emb.tolist() for emb in embeddings]

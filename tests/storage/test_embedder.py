import pytest
from armarius.storage import Embedder, EmbeddingConfig


def test_embedder_initialization():
    embedder = Embedder()
    assert embedder.config.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert embedder.dimension == 384


def test_embedder_with_custom_config():
    config = EmbeddingConfig(model_name="sentence-transformers/all-MiniLM-L6-v2")
    embedder = Embedder(config)
    assert embedder.config.model_name == "sentence-transformers/all-MiniLM-L6-v2"


def test_embed_single_text():
    embedder = Embedder()
    text = "This is a test sentence"
    embedding = embedder.embed_text(text)
    
    assert isinstance(embedding, list)
    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)


def test_embed_batch():
    embedder = Embedder()
    texts = [
        "First test sentence",
        "Second test sentence",
        "Third test sentence",
    ]
    embeddings = embedder.embed_batch(texts)
    
    assert len(embeddings) == 3
    assert all(len(emb) == 384 for emb in embeddings)
    assert all(isinstance(x, float) for emb in embeddings for x in emb)


def test_embed_empty_text():
    embedder = Embedder()
    embedding = embedder.embed_text("")
    assert isinstance(embedding, list)
    assert len(embedding) == 384


def test_embeddings_are_different():
    embedder = Embedder()
    emb1 = embedder.embed_text("cat")
    emb2 = embedder.embed_text("dog")
    
    assert emb1 != emb2


def test_embeddings_are_consistent():
    embedder = Embedder()
    text = "consistent embedding test"
    emb1 = embedder.embed_text(text)
    emb2 = embedder.embed_text(text)
    
    assert emb1 == emb2

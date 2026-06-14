import pytest
from pathlib import Path
from armarius.parser.pdf_parser import TextChunk, BoundingBox
from armarius.storage import VectorStore, SearchFilters


@pytest.fixture
def temp_vector_store(tmp_path):
    return VectorStore(
        collection_name="test_collection",
        data_dir=tmp_path / "qdrant",
        embedding_dim=384,
    )


@pytest.fixture
def sample_chunks():
    return [
        TextChunk(
            text="The transformer architecture uses self-attention.",
            bbox=BoundingBox(x0=100, y0=200, x1=300, y1=220, page=1),
            pdf_path="/test/paper1.pdf",
        ),
        TextChunk(
            text="Neural networks learn from data.",
            bbox=BoundingBox(x0=100, y0=250, x1=300, y1=270, page=1),
            pdf_path="/test/paper1.pdf",
        ),
        TextChunk(
            text="Machine learning is a subset of AI.",
            bbox=BoundingBox(x0=100, y0=200, x1=300, y1=220, page=2),
            pdf_path="/test/paper2.pdf",
        ),
    ]


@pytest.fixture
def sample_embeddings():
    return [
        [0.1] * 384,
        [0.2] * 384,
        [0.3] * 384,
    ]


def test_vector_store_initialization(temp_vector_store):
    assert temp_vector_store.collection_name == "test_collection"
    assert temp_vector_store.count() == 0


def test_add_single_chunk(temp_vector_store, sample_chunks, sample_embeddings):
    chunk_id = temp_vector_store.add_chunk(sample_chunks[0], sample_embeddings[0])
    
    assert chunk_id is not None
    assert temp_vector_store.count() == 1


def test_add_chunks_batch(temp_vector_store, sample_chunks, sample_embeddings):
    chunk_ids = temp_vector_store.add_chunks_batch(sample_chunks, sample_embeddings)
    
    assert len(chunk_ids) == 3
    assert temp_vector_store.count() == 3
    assert all(isinstance(cid, str) for cid in chunk_ids)


def test_search_basic(temp_vector_store, sample_chunks, sample_embeddings):
    temp_vector_store.add_chunks_batch(sample_chunks, sample_embeddings)
    
    query_embedding = [0.15] * 384
    results = temp_vector_store.search(query_embedding, top_k=2)
    
    assert len(results) <= 2
    assert all(hasattr(r, "chunk") for r in results)
    assert all(hasattr(r, "score") for r in results)
    assert all(hasattr(r, "chunk_id") for r in results)


def test_search_with_pdf_filter(temp_vector_store, sample_chunks, sample_embeddings):
    temp_vector_store.add_chunks_batch(sample_chunks, sample_embeddings)
    
    query_embedding = [0.15] * 384
    filters = SearchFilters(pdf_path="/test/paper1.pdf")
    results = temp_vector_store.search(query_embedding, top_k=10, filters=filters)
    
    assert len(results) == 2
    assert all(r.chunk.pdf_path == "/test/paper1.pdf" for r in results)


def test_search_with_page_range_filter(temp_vector_store, sample_chunks, sample_embeddings):
    temp_vector_store.add_chunks_batch(sample_chunks, sample_embeddings)
    
    query_embedding = [0.15] * 384
    filters = SearchFilters(page_range=(1, 1))
    results = temp_vector_store.search(query_embedding, top_k=10, filters=filters)
    
    assert all(r.chunk.bbox.page == 1 for r in results)


def test_delete_by_pdf(temp_vector_store, sample_chunks, sample_embeddings):
    temp_vector_store.add_chunks_batch(sample_chunks, sample_embeddings)
    assert temp_vector_store.count() == 3
    
    temp_vector_store.delete_by_pdf("/test/paper1.pdf")
    assert temp_vector_store.count() == 1


def test_batch_add_mismatch_length(temp_vector_store, sample_chunks, sample_embeddings):
    with pytest.raises(ValueError):
        temp_vector_store.add_chunks_batch(sample_chunks, sample_embeddings[:2])


def test_empty_search(temp_vector_store):
    query_embedding = [0.1] * 384
    results = temp_vector_store.search(query_embedding, top_k=10)
    
    assert len(results) == 0

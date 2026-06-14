import pytest
from pathlib import Path
from armarius.storage import SemanticSearch, Embedder, VectorStore, SearchQuery
from armarius.parser.pdf_parser import TextChunk, BoundingBox


@pytest.fixture
def temp_search_service(tmp_path):
    embedder = Embedder()
    vector_store = VectorStore(
        collection_name="test_search",
        data_dir=tmp_path / "qdrant",
        embedding_dim=embedder.dimension,
    )
    return SemanticSearch(embedder=embedder, vector_store=vector_store)


@pytest.fixture
def indexed_data(temp_search_service):
    chunks = [
        TextChunk(
            text="Transformers use self-attention mechanism for processing sequences.",
            bbox=BoundingBox(x0=100, y0=200, x1=400, y1=220, page=1),
            pdf_path="/test/ai_paper.pdf",
        ),
        TextChunk(
            text="Convolutional neural networks are good for image processing.",
            bbox=BoundingBox(x0=100, y0=250, x1=400, y1=270, page=2),
            pdf_path="/test/ai_paper.pdf",
        ),
        TextChunk(
            text="Recurrent networks process sequential data.",
            bbox=BoundingBox(x0=100, y0=300, x1=400, y1=320, page=3),
            pdf_path="/test/ml_paper.pdf",
        ),
    ]
    
    texts = [chunk.text for chunk in chunks]
    embeddings = temp_search_service.embedder.embed_batch(texts)
    temp_search_service.vector_store.add_chunks_batch(chunks, embeddings)
    
    return temp_search_service


def test_search_basic(indexed_data):
    query = SearchQuery(text="attention mechanism", top_k=2)
    results = indexed_data.search(query)
    
    assert len(results) <= 2
    assert all(hasattr(r, "chunk") for r in results)
    assert all(hasattr(r, "score") for r in results)


def test_search_by_pdf(indexed_data):
    results = indexed_data.search_by_pdf(
        query_text="neural networks",
        pdf_path=Path("/test/ai_paper.pdf"),
        top_k=10,
    )
    
    assert all(r.chunk.pdf_path == "/test/ai_paper.pdf" for r in results)


def test_search_by_page_range(indexed_data):
    results = indexed_data.search_by_page_range(
        query_text="processing",
        page_start=1,
        page_end=2,
        top_k=10,
    )
    
    assert all(1 <= r.chunk.bbox.page <= 2 for r in results)


def test_search_with_filters(indexed_data):
    query = SearchQuery(
        text="network",
        top_k=5,
        pdf_path="/test/ai_paper.pdf",
        page_range=(1, 2),
    )
    results = indexed_data.search(query)
    
    assert all(r.chunk.pdf_path == "/test/ai_paper.pdf" for r in results)
    assert all(1 <= r.chunk.bbox.page <= 2 for r in results)


def test_search_no_results(temp_search_service):
    query = SearchQuery(text="quantum computing", top_k=10)
    results = temp_search_service.search(query)
    
    assert len(results) == 0


def test_search_semantic_similarity(indexed_data):
    results = indexed_data.search(SearchQuery(text="attention networks", top_k=3))
    
    assert len(results) > 0
    assert all(hasattr(r, "chunk") for r in results)
    assert all(hasattr(r, "score") for r in results)

import pytest
from pathlib import Path
from armarius.storage import DocumentIndexer, Embedder, VectorStore
from armarius.parser import ChunkingStrategy


@pytest.fixture
def temp_indexer(tmp_path):
    embedder = Embedder()
    vector_store = VectorStore(
        collection_name="test_indexer",
        data_dir=tmp_path / "qdrant",
        embedding_dim=embedder.dimension,
    )
    return DocumentIndexer(
        embedder=embedder,
        vector_store=vector_store,
        chunking_strategy=ChunkingStrategy.BLOCK,
    )


@pytest.mark.skip(reason="Requires actual PDF file")
def test_index_pdf(temp_indexer, tmp_path):
    pdf_path = tmp_path / "test.pdf"
    
    count = temp_indexer.index_pdf(pdf_path)
    
    assert count > 0
    assert temp_indexer.total_chunks() == count


@pytest.mark.skip(reason="Requires actual PDF files")
def test_index_directory(temp_indexer, tmp_path):
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    
    results = temp_indexer.index_directory(pdf_dir)
    
    assert isinstance(results, dict)
    assert len(results) > 0


@pytest.mark.skip(reason="Requires actual PDF file")
def test_reindex_pdf(temp_indexer, tmp_path):
    pdf_path = tmp_path / "test.pdf"
    
    initial_count = temp_indexer.index_pdf(pdf_path)
    reindex_count = temp_indexer.reindex_pdf(pdf_path)
    
    assert reindex_count == initial_count
    assert temp_indexer.total_chunks() == reindex_count


def test_indexer_initialization(temp_indexer):
    assert temp_indexer.embedder is not None
    assert temp_indexer.vector_store is not None
    assert temp_indexer.chunking_strategy == ChunkingStrategy.BLOCK


def test_total_chunks_empty(temp_indexer):
    assert temp_indexer.total_chunks() == 0

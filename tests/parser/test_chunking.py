import pytest
from armarius.parser.pdf_parser import TextChunk, BoundingBox
from armarius.parser.chunking import (
    BlockLevelChunking,
    SentenceLevelChunking,
    FixedSizeChunking,
)


@pytest.fixture
def sample_chunks():
    bbox = BoundingBox(x0=10.0, y0=20.0, x1=100.0, y1=50.0, page=0)
    return [
        TextChunk(
            text="First sentence. Second sentence. Third sentence.",
            bbox=bbox,
            pdf_path="/test.pdf",
        ),
        TextChunk(
            text="Another block with more text. This has multiple sentences too.",
            bbox=BoundingBox(x0=10.0, y0=60.0, x1=100.0, y1=90.0, page=0),
            pdf_path="/test.pdf",
        ),
    ]


def test_block_level_chunking(sample_chunks):
    strategy = BlockLevelChunking()
    result = strategy.chunk(sample_chunks)
    
    assert len(result) == len(sample_chunks)
    assert result[0].text == sample_chunks[0].text


def test_sentence_level_chunking(sample_chunks):
    strategy = SentenceLevelChunking(max_chars=30)
    result = strategy.chunk(sample_chunks)
    
    assert len(result) >= len(sample_chunks)
    
    for chunk in result:
        assert len(chunk.text) <= 30 + 50
        assert isinstance(chunk.bbox, BoundingBox)


def test_fixed_size_chunking(sample_chunks):
    strategy = FixedSizeChunking(chunk_size=20, overlap=5)
    result = strategy.chunk(sample_chunks)
    
    assert len(result) > len(sample_chunks)
    
    for chunk in result:
        assert len(chunk.text) <= 20 + 5
        assert isinstance(chunk.bbox, BoundingBox)


def test_fixed_size_chunking_overlap():
    bbox = BoundingBox(x0=0, y0=0, x1=100, y1=100, page=0)
    chunk = TextChunk(
        text="A" * 100,
        bbox=bbox,
        pdf_path="/test.pdf",
    )
    
    strategy = FixedSizeChunking(chunk_size=30, overlap=10)
    result = strategy.chunk([chunk])
    
    assert len(result) > 1
    
    for i in range(len(result) - 1):
        current_end = result[i].text[-10:]
        next_start = result[i+1].text[:10]
        assert current_end == next_start

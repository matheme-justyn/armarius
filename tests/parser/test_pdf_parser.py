import pytest
from pathlib import Path
from armarius.parser.pdf_parser import PDFParser, BoundingBox, TextChunk


def test_bounding_box_to_dict():
    bbox = BoundingBox(x0=10.0, y0=20.0, x1=100.0, y1=50.0, page=0)
    result = bbox.to_dict()
    
    assert result["x0"] == 10.0
    assert result["y0"] == 20.0
    assert result["x1"] == 100.0
    assert result["y1"] == 50.0
    assert result["page"] == 0


def test_text_chunk_to_dict():
    bbox = BoundingBox(x0=10.0, y0=20.0, x1=100.0, y1=50.0, page=0)
    chunk = TextChunk(
        text="Sample text",
        bbox=bbox,
        pdf_path="/path/to/file.pdf",
        chunk_id="chunk_001"
    )
    
    result = chunk.to_dict()
    assert result["text"] == "Sample text"
    assert result["pdf_path"] == "/path/to/file.pdf"
    assert result["chunk_id"] == "chunk_001"
    assert result["bbox"]["page"] == 0


@pytest.mark.skipif(
    not Path("tests/fixtures/sample.pdf").exists(),
    reason="Sample PDF not available"
)
def test_pdf_parser_metadata():
    with PDFParser("tests/fixtures/sample.pdf") as parser:
        metadata = parser.get_metadata()
        
        assert "title" in metadata
        assert "page_count" in metadata
        assert isinstance(metadata["page_count"], int)


@pytest.mark.skipif(
    not Path("tests/fixtures/sample.pdf").exists(),
    reason="Sample PDF not available"
)
def test_pdf_parser_extraction():
    with PDFParser("tests/fixtures/sample.pdf") as parser:
        page_count = parser.get_page_count()
        assert page_count > 0
        
        chunks = parser.extract_text_with_bbox(0)
        assert len(chunks) > 0
        
        first_chunk = chunks[0]
        assert isinstance(first_chunk.text, str)
        assert len(first_chunk.text) > 0
        assert isinstance(first_chunk.bbox, BoundingBox)
        assert first_chunk.bbox.page == 0


@pytest.mark.skipif(
    not Path("tests/fixtures/sample.pdf").exists(),
    reason="Sample PDF not available"
)
def test_pdf_parser_extract_all():
    with PDFParser("tests/fixtures/sample.pdf") as parser:
        all_chunks = parser.extract_all_pages()
        assert len(all_chunks) > 0
        
        for chunk in all_chunks:
            assert isinstance(chunk, TextChunk)
            assert chunk.text
            assert chunk.bbox


def test_pdf_parser_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        PDFParser("/nonexistent/file.pdf")

"""Tests for PDF processing data models."""

from pathlib import Path

from armarius.pdf_processing.models import PDFProcessingResult


def test_processing_result_supports_metadata_confidence() -> None:
    """Processing result should carry metadata confidence payloads."""
    result = PDFProcessingResult(
        source_path=Path("example.pdf"),
        markdown_text="# Demo",
        extracted_text="demo",
        page_count=1,
        metadata={"doi": None},
        metadata_confidence={"doi": {"value": None, "source": "none", "confidence": 0.0}},
    )
    assert "doi" in result.metadata_confidence

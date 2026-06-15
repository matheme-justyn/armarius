"""Data models for the PDF processing module."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class PDFValidationResult:
    """Result of validating whether a file is a real PDF."""

    path: Path
    is_valid: bool
    detected_mime_type: str
    reason: Optional[str] = None
    page_count: Optional[int] = None


@dataclass(slots=True)
class PDFProcessingResult:
    """Result of processing a PDF into normalized artifacts."""

    source_path: Path
    markdown_text: str
    extracted_text: str
    page_count: int
    tables: list[dict[str, object]] = field(default_factory=list)
    images: list[dict[str, object]] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)
    metadata_confidence: dict[str, dict[str, object]] = field(default_factory=dict)

"""Tests for intake state classification."""

from pathlib import Path

from armarius.database import ArmariusDatabase
from armarius.intake_service import IntakeService
from armarius.pdf_processing import PDFProcessor

MINIMAL_PDF = b"%PDF-1.1\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def test_invalid_header_is_rejected(tmp_path: Path) -> None:
    """Non-PDF bytes should be rejected."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    source_file = tmp_path / "not-a-pdf.pdf"
    source_file.write_bytes(b"not really pdf")

    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)
    record = service.intake_file(source_file)

    assert record.ingest_state == "rejected"

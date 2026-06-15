"""Tests for intake review actions."""

from pathlib import Path

from armarius.database import ArmariusDatabase
from armarius.intake_service import IntakeService
from armarius.pdf_processing import PDFProcessor

MINIMAL_PDF = b"%PDF-1.1\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def test_update_ingest_state_moves_blob(tmp_path: Path) -> None:
    """Review action should move blob to the requested state directory."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    source_pdf = tmp_path / "review.pdf"
    source_pdf.write_bytes(MINIMAL_PDF)

    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)
    record = service.intake_file(source_pdf)

    result = service.update_ingest_state(record.document_blob_id, "quarantine")
    assert Path(result["new_path"]).exists()
    assert "quarantine" in result["new_path"]

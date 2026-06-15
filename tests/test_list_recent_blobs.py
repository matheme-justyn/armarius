"""Tests for intake recent blob listing."""

from pathlib import Path

from armarius.database import ArmariusDatabase
from armarius.intake_service import IntakeService
from armarius.pdf_processing import PDFProcessor

MINIMAL_PDF = b"%PDF-1.1\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def test_list_recent_blobs_can_filter_states(tmp_path: Path) -> None:
    """Recent blob listing should support ingest-state filters."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    source_pdf = tmp_path / "filter.pdf"
    source_pdf.write_bytes(MINIMAL_PDF)

    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)
    record = service.intake_file(source_pdf)
    service.update_ingest_state(record.document_blob_id, "quarantine")

    rows = service.list_recent_blobs(states=["quarantine"])
    assert rows
    assert rows[0]["ingest_state"] == "quarantine"

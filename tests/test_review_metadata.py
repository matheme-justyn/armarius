"""Tests for review metadata persistence."""

from pathlib import Path

from armarius.database import ArmariusDatabase
from armarius.intake_service import IntakeService
from armarius.pdf_processing import PDFProcessor

MINIMAL_PDF = b"%PDF-1.1\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def test_review_note_and_reason_are_persisted(tmp_path: Path) -> None:
    """Review updates should persist notes and reasons."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    source_pdf = tmp_path / "review-meta.pdf"
    source_pdf.write_bytes(MINIMAL_PDF)

    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)
    record = service.intake_file(source_pdf)
    service.update_ingest_state(record.document_blob_id, "quarantine", review_note="manual check", reason="weak_metadata")

    row = db.conn.execute("SELECT ingest_reason, review_note FROM document_blobs WHERE id = ?", (record.document_blob_id,)).fetchone()
    assert row["ingest_reason"] == "weak_metadata"
    assert row["review_note"] == "manual check"

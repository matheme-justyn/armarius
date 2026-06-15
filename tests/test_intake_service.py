"""Tests for intake and normalization services."""

import sqlite3
from pathlib import Path

from armarius.database import ArmariusDatabase
from armarius.intake_service import IntakeService
from armarius.pdf_processing import PDFProcessor


MINIMAL_PDF = b"%PDF-1.1\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def test_intake_and_normalize_creates_artifacts(tmp_path: Path) -> None:
    """Accepted PDFs should normalize into markdown-backed artifacts."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    source_pdf = tmp_path / "paper.pdf"
    source_pdf.write_bytes(MINIMAL_PDF)

    db_path = tmp_path / "armarius.db"
    db = ArmariusDatabase(db_path=db_path)
    service = IntakeService(db, PDFProcessor(), library_root)

    record = service.intake_file(source_pdf)
    if record.ingest_state != "accepted":
        service.update_ingest_state(record.document_blob_id, "accepted", review_note="test override", reason="test fixture")

    artifacts = service.normalize_blob(record.document_blob_id)
    assert artifacts.markdown_path.exists()
    assert artifacts.raw_text_path.exists()
    assert artifacts.manifest_path.exists()

    row = db.conn.execute("SELECT text_sha256 FROM document_blobs WHERE id = ?", (record.document_blob_id,)).fetchone()
    assert row is not None
    assert row["text_sha256"] is not None

    artifact_count = db.conn.execute("SELECT COUNT(*) AS count FROM artifacts WHERE document_blob_id = ?", (record.document_blob_id,)).fetchone()["count"]
    assert artifact_count >= 3

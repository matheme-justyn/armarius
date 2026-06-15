"""Tests for provenance trace behavior."""

from pathlib import Path

from armarius.database import ArmariusDatabase
from armarius.intake_service import IntakeService
from armarius.pdf_processing import PDFProcessor

MINIMAL_PDF = b"%PDF-1.1\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def test_trace_blob_reports_artifacts(tmp_path: Path) -> None:
    """Trace should expose root metadata and generated artifacts."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    source_pdf = tmp_path / "trace.pdf"
    source_pdf.write_bytes(MINIMAL_PDF)

    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)
    record = service.intake_file(source_pdf)
    if record.ingest_state != "accepted":
        service.update_ingest_state(record.document_blob_id, "accepted", review_note="test override", reason="test fixture")
    service.normalize_blob(record.document_blob_id)

    payload = service.trace_blob(record.document_blob_id)
    assert payload["blob_id"] == record.document_blob_id
    assert payload["root"] is not None
    assert len(payload["artifacts"]) >= 3

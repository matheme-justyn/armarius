from pathlib import Path

from armarius.database import ArmariusDatabase
from armarius.intake_service import IntakeService
from armarius.pdf_processing import PDFProcessor

MINIMAL_PDF = b"%PDF-1.1\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def test_blob_detail_includes_transition_history(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()
    source_pdf = tmp_path / "review.pdf"
    source_pdf.write_bytes(MINIMAL_PDF)

    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)
    record = service.intake_file(source_pdf)
    service.update_ingest_state(record.document_blob_id, "quarantine")

    detail = service.get_blob_detail(record.document_blob_id)

    assert "transition_history" in detail
    assert detail["transition_history"][0]["state"] == "quarantine"


def test_list_recent_activity_returns_state_transitions(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()
    source_pdf = tmp_path / "review.pdf"
    source_pdf.write_bytes(MINIMAL_PDF)

    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)
    record = service.intake_file(source_pdf)
    service.update_ingest_state(record.document_blob_id, "needs_ocr")

    activity = service.list_recent_activity(limit=10)

    assert activity
    assert activity[0]["state"] == "needs_ocr"

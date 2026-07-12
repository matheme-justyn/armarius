from pathlib import Path

from armarius.database import ArmariusDatabase
from armarius.intake_service import IntakeService
from armarius.pdf_processing import PDFProcessor

MINIMAL_PDF = b"%PDF-1.1\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def test_list_recent_blobs_includes_governance_metadata(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()
    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)

    source_pdf = tmp_path / "paper.pdf"
    source_pdf.write_bytes(MINIMAL_PDF)
    record = service.intake_file(source_pdf)
    if record.ingest_state != "accepted":
        service.update_ingest_state(record.document_blob_id, "accepted")

    rows = service.list_recent_blobs(limit=10)

    assert rows
    assert rows[0]["governance_class"] == "library_shared"
    assert rows[0]["lifecycle_stage"] in {"intake", "library_active", "review"}
    assert rows[0]["review_status"] in {"pending", "accepted", "needs_revision"}

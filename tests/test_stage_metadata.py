from pathlib import Path

from armarius.database import ArmariusDatabase
from armarius.intake_service import IntakeService
from armarius.pdf_processing import PDFProcessor

MINIMAL_PDF = b"%PDF-1.1\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def test_document_root_tracks_governance_and_stage_metadata(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()
    source_pdf = tmp_path / "paper.pdf"
    source_pdf.write_bytes(MINIMAL_PDF)

    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)
    record = service.intake_file(source_pdf)

    row = db.conn.execute(
        "SELECT governance_class, lifecycle_stage, review_status FROM document_roots WHERE id = ?",
        (record.document_root_id,),
    ).fetchone()

    assert row is not None
    assert row["governance_class"] == "library_shared"
    assert row["lifecycle_stage"] in {"intake", "review"}
    assert row["review_status"] in {"accepted", "pending"}


def test_blob_detail_surfaces_stage_metadata(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()
    source_pdf = tmp_path / "paper.pdf"
    source_pdf.write_bytes(MINIMAL_PDF)

    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)
    record = service.intake_file(source_pdf)
    service.update_ingest_state(record.document_blob_id, "quarantine")

    detail = service.get_blob_detail(record.document_blob_id)

    assert detail["governance_class"] == "library_shared"
    assert detail["lifecycle_stage"] == "review"
    assert detail["review_status"] == "needs_revision"

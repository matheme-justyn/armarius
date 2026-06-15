"""Tests for rename proposal and apply workflow."""

from pathlib import Path

from armarius.database import ArmariusDatabase
from armarius.intake_service import IntakeService
from armarius.pdf_processing import PDFProcessor

MINIMAL_PDF = b"%PDF-1.1\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def test_rename_propose_and_apply(tmp_path: Path) -> None:
    """Accepted blobs should support deterministic rename proposals."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    source_pdf = tmp_path / "rename me.pdf"
    source_pdf.write_bytes(MINIMAL_PDF)

    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)
    record = service.intake_file(source_pdf)

    proposal = service.propose_filename(record.document_blob_id)
    assert proposal["proposed_filename"].endswith(".pdf")

    result = service.apply_filename(record.document_blob_id)
    assert Path(result["new_path"]).exists()
    assert Path(result["old_path"]) != Path(result["new_path"])

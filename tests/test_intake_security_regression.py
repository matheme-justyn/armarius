from pathlib import Path

from armarius.database import ArmariusDatabase
from armarius.intake_service import IntakeService
from armarius.pdf_processing import PDFProcessor

MINIMAL_PDF = b"%PDF-1.1\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def test_intake_sanitizes_unsafe_source_filename(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()
    source_pdf = tmp_path / '..unsafe:name?.pdf'
    source_pdf.write_bytes(MINIMAL_PDF)

    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)
    record = service.intake_file(source_pdf)

    assert '..' not in record.managed_path.name
    assert ':' not in record.managed_path.name
    assert '?' not in record.managed_path.name
    assert record.managed_path.parent.is_relative_to(library_root)


def test_apply_filename_keeps_blob_inside_library_root(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()
    source_pdf = tmp_path / "paper.pdf"
    source_pdf.write_bytes(MINIMAL_PDF)

    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)
    record = service.intake_file(source_pdf)
    if record.ingest_state != "accepted":
        service.update_ingest_state(record.document_blob_id, "accepted")

    result = service.apply_filename(record.document_blob_id)
    new_path = Path(result["new_path"])

    assert new_path.is_relative_to(library_root)
    assert new_path.exists()

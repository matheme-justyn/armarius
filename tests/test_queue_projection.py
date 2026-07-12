from pathlib import Path

from armarius.database import ArmariusDatabase
from armarius.intake_service import IntakeService
from armarius.pdf_processing import PDFProcessor

MINIMAL_PDF = b"%PDF-1.1\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def test_queue_summary_counts_ingest_and_processing_states(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()
    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)

    source_a = tmp_path / "accepted.pdf"
    source_a.write_bytes(MINIMAL_PDF)
    accepted = service.intake_file(source_a)
    if accepted.ingest_state != "accepted":
        service.update_ingest_state(accepted.document_blob_id, "accepted")
    service.normalize_blob(accepted.document_blob_id)

    source_b = tmp_path / "ocr.pdf"
    source_b.write_bytes(MINIMAL_PDF)
    needs_ocr = service.intake_file(source_b)
    service.update_ingest_state(needs_ocr.document_blob_id, "needs_ocr")

    source_c = tmp_path / "rejected.pdf"
    source_c.write_bytes(MINIMAL_PDF)
    rejected = service.intake_file(source_c)
    service.update_ingest_state(rejected.document_blob_id, "rejected")

    summary = service.get_queue_summary()

    assert summary["total_blobs"] == 3
    assert summary["ingest"]["accepted"] == 1
    assert summary["ingest"]["needs_ocr"] == 1
    assert summary["ingest"]["rejected"] == 1
    assert summary["processing"]["normalized"] == 1
    assert summary["processing"]["ready_for_analysis"] == 1


def test_blob_detail_includes_processing_stage(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()
    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)

    source_pdf = tmp_path / "paper.pdf"
    source_pdf.write_bytes(MINIMAL_PDF)
    record = service.intake_file(source_pdf)
    if record.ingest_state != "accepted":
        service.update_ingest_state(record.document_blob_id, "accepted")

    detail_before = service.get_blob_detail(record.document_blob_id)
    assert detail_before["processing_stage"] == "accepted_pending_normalize"

    service.normalize_blob(record.document_blob_id)
    detail_after = service.get_blob_detail(record.document_blob_id)
    assert detail_after["processing_stage"] == "ready_for_analysis"


def test_list_recent_blobs_supports_processing_stage_filter(tmp_path: Path) -> None:
    library_root = tmp_path / 'library'
    library_root.mkdir()
    db = ArmariusDatabase(db_path=tmp_path / 'armarius.db')
    service = IntakeService(db, PDFProcessor(), library_root)

    source_a = tmp_path / 'accepted.pdf'
    source_a.write_bytes(MINIMAL_PDF)
    accepted = service.intake_file(source_a)
    if accepted.ingest_state != 'accepted':
        service.update_ingest_state(accepted.document_blob_id, 'accepted')
    service.normalize_blob(accepted.document_blob_id)

    source_b = tmp_path / 'ocr.pdf'
    source_b.write_bytes(MINIMAL_PDF)
    needs_ocr = service.intake_file(source_b)
    service.update_ingest_state(needs_ocr.document_blob_id, 'needs_ocr')

    ready = service.list_recent_blobs(limit=20, processing_stages=['ready_for_analysis'])
    ocr = service.list_recent_blobs(limit=20, processing_stages=['needs_ocr'])

    assert len(ready) == 1
    assert ready[0]['processing_stage'] == 'ready_for_analysis'
    assert len(ocr) == 1
    assert ocr[0]['processing_stage'] == 'needs_ocr'


def test_queue_summary_includes_credibility_distribution(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()
    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)

    source_pdf = tmp_path / "paper.pdf"
    source_pdf.write_bytes(MINIMAL_PDF)
    record = service.intake_file(source_pdf)
    if record.ingest_state != "accepted":
        service.update_ingest_state(record.document_blob_id, "accepted")

    summary = service.get_queue_summary()

    assert "credibility" in summary
    assert set(summary["credibility"].keys()) == {"high", "medium", "low", "unknown"}
    assert sum(summary["credibility"].values()) == 1


def test_queue_summary_includes_credibility_distribution(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()
    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    service = IntakeService(db, PDFProcessor(), library_root)

    source_pdf = tmp_path / "paper.pdf"
    source_pdf.write_bytes(MINIMAL_PDF)
    record = service.intake_file(source_pdf)
    if record.ingest_state != "accepted":
        service.update_ingest_state(record.document_blob_id, "accepted")

    summary = service.get_queue_summary()

    assert "credibility" in summary
    assert set(summary["credibility"].keys()) == {"high", "medium", "low", "unknown"}
    assert sum(summary["credibility"].values()) == 1

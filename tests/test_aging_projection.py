from datetime import datetime, timedelta
from pathlib import Path

from armarius.database import ArmariusDatabase
from armarius.intake_service import IntakeService
from armarius.pdf_processing import PDFProcessor

MINIMAL_PDF = b"%PDF-1.1\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def test_queue_summary_includes_stale_counts(tmp_path: Path) -> None:
    library_root = tmp_path / 'library'
    library_root.mkdir()
    db = ArmariusDatabase(db_path=tmp_path / 'armarius.db')
    service = IntakeService(db, PDFProcessor(), library_root)

    source_pdf = tmp_path / 'paper.pdf'
    source_pdf.write_bytes(MINIMAL_PDF)
    record = service.intake_file(source_pdf)
    old_time = (datetime.now() - timedelta(days=5)).isoformat()
    db.conn.execute('UPDATE document_blobs SET created_at = ?, ingest_state = ? WHERE id = ?', (old_time, 'needs_ocr', record.document_blob_id))
    db.conn.commit()

    summary = service.get_queue_summary(stale_after_days=3)

    assert summary['stale']['total'] == 1
    assert summary['stale']['needs_ocr'] == 1

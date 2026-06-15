"""Tests for intake CLI and database-backed intake records."""

from pathlib import Path

from click.testing import CliRunner

from armarius.cli import main
from armarius.config import ArmariusConfig


def test_intake_run_accepts_valid_pdf(tmp_path: Path, monkeypatch) -> None:
    """A valid PDF should be copied into managed intake storage."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")

    config_path = tmp_path / "config.yaml"
    monkeypatch.setattr(ArmariusConfig, "DEFAULT_CONFIG_PATH", config_path)
    monkeypatch.setattr(ArmariusConfig, "DEFAULT_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(ArmariusConfig, "DEFAULT_LOG_DIR", tmp_path / "logs")

    config = ArmariusConfig()
    config.set("library.root_path", str(library_root))
    config.save()

    runner = CliRunner()
    result = runner.invoke(main, ["intake", "run", str(pdf_path)])

    assert result.exit_code == 0
    accepted_path = library_root / "_intake" / "accepted" / "sample.pdf"
    quarantine_path = library_root / "_intake" / "quarantine" / "sample.pdf"
    needs_ocr_path = library_root / "needs_ocr" / "sample.pdf"
    assert accepted_path.exists() or quarantine_path.exists() or needs_ocr_path.exists()

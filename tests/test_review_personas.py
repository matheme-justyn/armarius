from pathlib import Path

from armarius.database import ArmariusDatabase
from armarius.review_draft import ReviewDraftService


def test_generate_review_draft_with_personas(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()

    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    db.save_paradigm("p1", "Paradigm One", "topic", "name: Paradigm One")
    assert db.save_analysis("a1", "paper-1", "p1", "Lens A", "Analysis content A", 3)

    service = ReviewDraftService(db, library_root)
    result = service.generate("p1", personas=["teacher", "engineer"])

    text = Path(result["output_path"]).read_text(encoding="utf-8")
    assert "## Summary" in text
    assert "persona views for teacher, engineer" in text
    assert "## Teacher" in text
    assert "## Engineer" in text
    assert "teachable framing" in text
    assert "implementation relevance" in text
    assert "Focus:" in text
    assert "Analysis content A" in text
    assert result["personas"] == ["teacher", "engineer"]

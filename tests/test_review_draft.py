from pathlib import Path

from armarius.database import ArmariusDatabase
from armarius.review_draft import ReviewDraftService


def test_generate_review_draft_from_saved_analyses(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()

    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    db.save_paradigm("p1", "Paradigm One", "topic", "name: Paradigm One")
    assert db.save_analysis("a1", "paper-1", "p1", "Lens A", "Analysis content A", 3)
    assert db.save_analysis("a2", "paper-2", "p1", "Lens B", "Analysis content B", 3)

    service = ReviewDraftService(db, library_root)
    result = service.generate("p1")

    output_path = Path(result["output_path"])
    assert output_path.exists()
    text = output_path.read_text(encoding="utf-8")
    assert "# Literature Review Draft" in text
    assert "## Summary" in text
    assert "Analysis content A" in text
    assert "Analysis content B" in text
    assert len(result["analysis_ids"]) == 2


def test_generate_review_draft_orders_sections_for_reading_flow(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()

    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    db.save_paradigm("p1", "Paradigm One", "topic", "name: Paradigm One")
    assert db.save_analysis("a1", "paper-1", "p1", "Findings", "Findings body", 3)
    assert db.save_analysis("a2", "paper-2", "p1", "Background", "Background body", 3)
    assert db.save_analysis("a3", "paper-3", "p1", "Conclusion", "Conclusion body", 3)

    service = ReviewDraftService(db, library_root)
    result = service.generate("p1")

    text = Path(result["output_path"]).read_text(encoding="utf-8")
    background_index = text.index("### Background")
    findings_index = text.index("### Findings")
    conclusion_index = text.index("### Conclusion")

    assert background_index < findings_index < conclusion_index


def test_generate_review_draft_can_use_concerto_specific_outline(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()

    db = ArmariusDatabase(db_path=tmp_path / "armarius.db")
    db.save_paradigm("p1", "Paradigm One", "topic", "name: Paradigm One")
    assert db.save_analysis("a1", "paper-1", "p1", "Conclusion", "Conclusion body", 3)
    assert db.save_analysis("a2", "paper-2", "p1", "Findings", "Findings body", 3)
    assert db.save_analysis("a3", "paper-3", "p1", "Implications", "Implications body", 3)

    service = ReviewDraftService(db, library_root)
    result = service.generate("p1", concerto="executive_brief")

    text = Path(result["output_path"]).read_text(encoding="utf-8")
    findings_index = text.index("### Findings")
    implications_index = text.index("### Implications")
    conclusion_index = text.index("### Conclusion")

    assert findings_index < implications_index < conclusion_index

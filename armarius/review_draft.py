"""Minimal literature-review draft generation from saved analyses."""

from __future__ import annotations

import uuid
from pathlib import Path

from armarius.database import ArmariusDatabase


class ReviewDraftService:
    """Generate simple review drafts from existing analyses."""

    CONCERTO_OUTLINES = {
        "literature_review": ["background", "method", "findings", "discussion", "limitations", "conclusion"],
        "executive_brief": ["summary", "findings", "implications", "limitations", "conclusion"],
        "teaching_note": ["background", "findings", "discussion", "implications", "conclusion"],
    }

    PERSONA_PRESETS = {
        "teacher": {
            "intro": "Emphasize teachable framing, conceptual clarity, and what a learner should notice first.",
            "emphasis": "Highlight definitions, core arguments, and how to explain the material simply.",
        },
        "engineer": {
            "intro": "Emphasize implementation relevance, operational trade-offs, and what can be applied in practice.",
            "emphasis": "Highlight methods, constraints, decision criteria, and execution implications.",
        },
        "researcher": {
            "intro": "Emphasize contribution, evidence quality, and where the literature still leaves gaps.",
            "emphasis": "Highlight methods, findings, limitations, and future work opportunities.",
        },
    }

    SECTION_ORDER = {
        "summary": 0,
        "background": 1,
        "context": 2,
        "problem": 3,
        "method": 4,
        "methods": 4,
        "findings": 5,
        "results": 5,
        "discussion": 6,
        "implications": 7,
        "limitations": 8,
        "future_work": 9,
        "conclusion": 10,
    }

    def __init__(self, db: ArmariusDatabase, library_root: Path) -> None:
        self.db = db
        self.library_root = library_root

    @staticmethod
    def _persona_heading(persona: str) -> str:
        return persona.replace("_", " ").strip().title() or "Perspective"

    @classmethod
    def _section_rank(cls, lens_name: str) -> tuple[int, str]:
        key = lens_name.strip().lower().replace("-", "_").replace(" ", "_")
        return cls.SECTION_ORDER.get(key, 99), lens_name.lower()

    @classmethod
    def _outline_rank(cls, concerto: str, lens_name: str) -> tuple[int, int, str]:
        key = lens_name.strip().lower().replace("-", "_").replace(" ", "_")
        outline = cls.CONCERTO_OUTLINES.get(concerto, cls.CONCERTO_OUTLINES["literature_review"])
        outline_rank = outline.index(key) if key in outline else 99
        section_rank, normalized_name = cls._section_rank(lens_name)
        return outline_rank, section_rank, normalized_name

    @classmethod
    def _persona_preset(cls, persona: str) -> dict[str, str]:
        return cls.PERSONA_PRESETS.get(
            persona,
            {
                "intro": f"Emphasize what matters most for the `{persona}` perspective.",
                "emphasis": "Highlight the most actionable distinctions and implications for this reader.",
            },
        )

    @staticmethod
    def _build_summary_intro(paradigm_id: str, concerto: str, analyses: list[dict], personas: list[str]) -> list[str]:
        lenses = [item["lens_name"] for item in analyses]
        ordered_lenses = ", ".join(lenses)
        persona_text = (
            f" It also includes persona views for {', '.join(personas)}."
            if personas else
            ""
        )
        return [
            "## Summary",
            "",
            (
                f"This draft assembles {len(analyses)} saved analyses for paradigm `{paradigm_id}` into the `{concerto}` synthesis flow. "
                f"Sections are ordered for reading flow: {ordered_lenses}.{persona_text}"
            ).strip(),
            "",
        ]

    def generate(
        self,
        paradigm_id: str,
        concerto: str = "literature_review",
        personas: list[str] | None = None,
    ) -> dict[str, object]:
        analyses = self.db.get_analyses_by_paradigm(paradigm_id)
        if not analyses:
            raise ValueError(f"No analyses found for paradigm: {paradigm_id}")
        analyses = sorted(analyses, key=lambda item: self._outline_rank(concerto, item["lens_name"]))

        personas = personas or []
        output_dir = self.library_root / "synthesis"
        output_dir.mkdir(parents=True, exist_ok=True)
        suffix = concerto if not personas else f"{concerto}_personas"
        output_path = output_dir / f"{paradigm_id}_{suffix}.md"

        lines = [
            "# Literature Review Draft",
            "",
            f"Paradigm: `{paradigm_id}`",
            f"Concerto: `{concerto}`",
            "",
        ]
        lines.extend(self._build_summary_intro(paradigm_id, concerto, analyses, personas))
        if personas:
            lines.extend([
                "## Perspectives",
                "",
                *[f"- {self._persona_heading(persona)}" for persona in personas],
                "",
            ])

        analysis_ids: list[str] = []
        if personas:
            for persona in personas:
                preset = self._persona_preset(persona)
                lines.extend([
                    f"## {self._persona_heading(persona)}",
                    "",
                    f"This section reframes the same analysis set for the `{persona}` perspective. {preset['intro']}",
                    "",
                    f"Focus: {preset['emphasis']}",
                    "",
                ])
                for item in analyses:
                    analysis_ids.append(item["id"])
                    lines.extend([
                        f"### {item['lens_name']}",
                        "",
                        item["content"],
                        "",
                    ])
        else:
            lines.extend(["## Included Analyses", ""])
            for item in analyses:
                analysis_ids.append(item["id"])
                lines.extend([
                    f"### {item['lens_name']}",
                    "",
                    item["content"],
                    "",
                ])

        output_text = "\n".join(lines).strip() + "\n"
        output_path.write_text(output_text, encoding="utf-8")

        synthesis_id = str(uuid.uuid4())
        word_count = len(output_text.split())
        self.db.save_synthesis(
            synthesis_id=synthesis_id,
            paradigm_id=paradigm_id,
            concerto=concerto if not personas else f"{concerto}+personas",
            analysis_ids=analysis_ids,
            output_path=str(output_path),
            word_count=word_count,
        )
        return {
            "synthesis_id": synthesis_id,
            "output_path": str(output_path),
            "analysis_ids": analysis_ids,
            "word_count": word_count,
            "personas": personas,
        }

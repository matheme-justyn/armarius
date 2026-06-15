"""Artifact bundle definitions for PDF processing outputs."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class NormalizedArtifacts:
    """Filesystem locations for normalized PDF artifacts."""

    markdown_path: Path
    raw_text_path: Path
    manifest_path: Path
    table_paths: list[Path] = field(default_factory=list)
    image_paths: list[Path] = field(default_factory=list)

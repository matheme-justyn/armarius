"""Paradigm and Concerto configuration management.

This module handles loading, validation, and management of paradigm and concerto
configuration files.
"""

from pathlib import Path
from typing import Optional
import yaml
import hashlib


class ParadigmLoader:
    """Load and manage paradigm configurations."""

    def __init__(self, paradigms_dir: Optional[Path] = None):
        """Initialize paradigm loader.

        Args:
            paradigms_dir: Directory containing .paradigm files.
                          Defaults to ~/.cardex/paradigms/
        """
        if paradigms_dir is None:
            paradigms_dir = Path.home() / ".armarius" / "paradigms"

        self.paradigms_dir = paradigms_dir
        self.paradigms_dir.mkdir(parents=True, exist_ok=True)

    def list_paradigms(self) -> list[dict]:
        """List all available paradigms.

        Returns:
            List of paradigm metadata dicts with keys:
            - id: Paradigm identifier (hash of name)
            - name: Paradigm name
            - type: Type (researcher/topic/school)
            - file_path: Path to .paradigm file
            - lenses: List of lens names
            - core_questions: List of questions
        """
        paradigms = []

        for paradigm_file in self.paradigms_dir.glob("*.paradigm"):
            try:
                with open(paradigm_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)

                if not config:
                    continue

                paradigm_id = self._generate_id(config.get("name", paradigm_file.stem))

                paradigms.append(
                    {
                        "id": paradigm_id,
                        "name": config.get("name", paradigm_file.stem),
                        "type": config.get("type", "topic"),
                        "file_path": str(paradigm_file),
                        "lenses": [lens.get("name") for lens in config.get("lenses", [])],
                        "core_questions": config.get("core_questions", []),
                        "theoretical_frameworks": config.get("theoretical_frameworks", []),
                    }
                )
            except Exception as e:
                print(f"Error loading paradigm {paradigm_file}: {e}")

        return sorted(paradigms, key=lambda x: x["name"])

    def load_paradigm(self, name_or_path: str) -> Optional[dict]:
        """Load a specific paradigm by name or file path.

        Args:
            name_or_path: Paradigm name or full file path

        Returns:
            Paradigm configuration dict or None
        """
        # Try as file path first
        paradigm_path = Path(name_or_path)
        if not paradigm_path.exists():
            # Try as name in paradigms directory
            paradigm_path = self.paradigms_dir / f"{name_or_path}.paradigm"

        if not paradigm_path.exists():
            return None

        try:
            with open(paradigm_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # Add computed fields
            config["id"] = self._generate_id(config.get("name", paradigm_path.stem))
            config["file_path"] = str(paradigm_path)

            return config
        except Exception as e:
            print(f"Error loading paradigm from {paradigm_path}: {e}")
            return None

    def validate_paradigm(self, config: dict) -> tuple[bool, list[str]]:
        """Validate paradigm configuration.

        Args:
            config: Paradigm configuration dict

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Required fields
        if "name" not in config:
            errors.append("Missing required field: name")

        if "type" not in config:
            errors.append("Missing required field: type")
        elif config["type"] not in ["researcher", "topic", "school"]:
            errors.append(f"Invalid type: {config['type']}. Must be researcher/topic/school")

        if "lenses" not in config or not config["lenses"]:
            errors.append("At least one lens is required")
        else:
            # Validate lenses
            for i, lens in enumerate(config["lenses"]):
                if "name" not in lens:
                    errors.append(f"Lens #{i + 1} missing 'name' field")

        return (len(errors) == 0, errors)

    def _generate_id(self, name: str) -> str:
        """Generate paradigm ID from name.

        Args:
            name: Paradigm name

        Returns:
            Hash-based identifier
        """
        return hashlib.md5(name.encode()).hexdigest()[:16]


class ConcertoLoader:
    """Load and manage concerto configurations."""

    def __init__(self, concerti_dir: Optional[Path] = None):
        """Initialize concerto loader.

        Args:
            concerti_dir: Directory containing .concerto files.
                         Defaults to ~/.cardex/concerti/
        """
        if concerti_dir is None:
            concerti_dir = Path.home() / ".armarius" / "concerti"

        self.concerti_dir = concerti_dir
        self.concerti_dir.mkdir(parents=True, exist_ok=True)

    def list_concerti(self) -> list[dict]:
        """List all available concerti.

        Returns:
            List of concerto metadata dicts with keys:
            - id: Concerto identifier (filename stem)
            - name: Concerto name
            - type: Type (academic_journal/policy_brief/etc)
            - file_path: Path to .concerto file
            - audience: Primary audience
            - tone: Writing tone
            - length: Target length info
        """
        concerti = []

        for concerto_file in self.concerti_dir.glob("*.concerto"):
            try:
                with open(concerto_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)

                if not config:
                    continue

                concerti.append(
                    {
                        "id": concerto_file.stem,
                        "name": config.get("name", concerto_file.stem),
                        "type": config.get("type", "unknown"),
                        "file_path": str(concerto_file),
                        "audience": config.get("audience", {}).get("primary", "General"),
                        "tone": config.get("orchestra", {}).get("tone", "neutral"),
                        "length": config.get("orchestra", {}).get("length", {}),
                    }
                )
            except Exception as e:
                print(f"Error loading concerto {concerto_file}: {e}")

        return sorted(concerti, key=lambda x: x["name"])

    def load_concerto(self, name_or_path: str) -> Optional[dict]:
        """Load a specific concerto by name or file path.

        Args:
            name_or_path: Concerto name or full file path

        Returns:
            Concerto configuration dict or None
        """
        # Try as file path first
        concerto_path = Path(name_or_path)
        if not concerto_path.exists():
            # Try as name in concerti directory
            concerto_path = self.concerti_dir / f"{name_or_path}.concerto"

        if not concerto_path.exists():
            return None

        try:
            with open(concerto_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # Add computed fields
            config["id"] = concerto_path.stem
            config["file_path"] = str(concerto_path)

            return config
        except Exception as e:
            print(f"Error loading concerto from {concerto_path}: {e}")
            return None

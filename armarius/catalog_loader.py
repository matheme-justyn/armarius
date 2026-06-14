"""Catalog configuration management.

Load and manage catalog configuration files for organizing academic libraries.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
import hashlib


class CatalogLoader:
    """Load and manage catalog configurations."""

    def __init__(
        self, catalogs_dir: Optional[Path] = None, project_templates: Optional[Path] = None
    ):
        """Initialize catalog loader.

        Args:
            catalogs_dir: User's catalog directory (~/.armarius/catalogs/)
            project_templates: Project template directory (project_root/catalogs/)
        """
        if catalogs_dir is None:
            catalogs_dir = Path.home() / ".armarius" / "catalogs"

        self.catalogs_dir = catalogs_dir
        self.catalogs_dir.mkdir(parents=True, exist_ok=True)

        self.project_templates = project_templates
        if project_templates and not project_templates.exists():
            self.project_templates = None

    def list_catalogs(self) -> List[Dict[str, Any]]:
        """List all available catalog configurations.

        Returns:
            List of catalog metadata dicts with keys:
            - id: Catalog identifier (hash of name)
            - name: Catalog name
            - method: Catalog method (flat/by_year/by_venue/custom)
            - file_path: Path to .catalog.yaml file
            - source: 'user' or 'template'
        """
        catalogs = []

        for catalog_file in self.catalogs_dir.glob("*.catalog.yaml"):
            catalog = self._load_catalog_metadata(catalog_file, source="user")
            if catalog:
                catalogs.append(catalog)

        if self.project_templates:
            for catalog_file in self.project_templates.glob("*.catalog.yaml"):
                catalog = self._load_catalog_metadata(catalog_file, source="template")
                if catalog:
                    catalogs.append(catalog)

        return sorted(catalogs, key=lambda x: (x["source"], x["name"]))

    def _load_catalog_metadata(self, catalog_file: Path, source: str) -> Optional[Dict[str, Any]]:
        """Load catalog metadata from file."""
        try:
            with open(catalog_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config:
                return None

            catalog_id = self._generate_id(config.get("name", catalog_file.stem))

            return {
                "id": catalog_id,
                "name": config.get("name", catalog_file.stem),
                "method": config.get("method", "flat"),
                "file_path": str(catalog_file),
                "source": source,
                "description": config.get("description", ""),
            }
        except Exception as e:
            print(f"Error loading catalog {catalog_file}: {e}")
            return None

    def load_catalog(self, name_or_path: str) -> Optional[Dict[str, Any]]:
        """Load a specific catalog configuration.

        Args:
            name_or_path: Catalog name or full file path

        Returns:
            Catalog configuration dict or None
        """
        catalog_path = Path(name_or_path)

        if not catalog_path.exists():
            catalog_path = self.catalogs_dir / f"{name_or_path}.catalog.yaml"

        if not catalog_path.exists() and self.project_templates:
            catalog_path = self.project_templates / f"{name_or_path}.catalog.yaml"

        if not catalog_path.exists():
            return None

        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            config["id"] = self._generate_id(config.get("name", catalog_path.stem))
            config["file_path"] = str(catalog_path)

            return config
        except Exception as e:
            print(f"Error loading catalog from {catalog_path}: {e}")
            return None

    def validate_catalog(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate catalog configuration.

        Args:
            config: Catalog configuration dict

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        required_fields = ["name", "method", "naming"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")

        valid_methods = ["flat", "by_year", "by_venue", "custom"]
        if config.get("method") not in valid_methods:
            errors.append(f"Invalid method: {config.get('method')}. Must be one of {valid_methods}")

        if config.get("method") == "custom":
            if not config.get("categories"):
                errors.append("Method 'custom' requires 'categories' field")

        if "naming" in config:
            naming = config["naming"]
            if "primary" not in naming:
                errors.append("Naming configuration missing 'primary' field")
            if naming.get("primary") not in ["doi", "title", "original"]:
                errors.append("Invalid naming.primary value")

        return len(errors) == 0, errors

    def get_default_catalog(self) -> Dict[str, Any]:
        """Get default flat catalog configuration."""
        return {
            "name": "Default Flat",
            "description": "Default flat structure catalog",
            "version": "1.0",
            "method": "flat",
            "naming": {
                "primary": "doi",
                "fallback": "title",
                "sanitize": {
                    "replace_slash": "-",
                    "replace_space": "_",
                    "lowercase": False,
                    "max_length": 255,
                    "remove_special_chars": ["?", "!", ":", ";", "*", '"', "<", ">", "|"],
                },
                "duplicate_strategy": "number",
            },
            "special_dirs": {
                "inbox": "_input",
                "duplicates": "_duplicates",
                "no_metadata": "_no_metadata",
                "needs_ocr": "_needs_ocr",
            },
            "doi_lookup": {
                "enabled": True,
                "apis": ["crossref", "semantic_scholar"],
                "timeout": 10,
                "max_retries": 3,
                "retry_delay": 2,
            },
            "advanced": {
                "auto_categorize": False,
                "verify_after_move": True,
                "preserve_original_name": True,
                "backup_before_recatalog": True,
                "log_level": "INFO",
            },
        }

    def _generate_id(self, name: str) -> str:
        """Generate unique ID from name."""
        return hashlib.md5(name.encode()).hexdigest()[:8]

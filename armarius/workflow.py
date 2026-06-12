"""
Library workflow management for Cardex.

This module handles library folder initialization, version tracking, and upgrades.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum
import toml


class LibraryStatus(Enum):
    """Library folder status."""

    UNINITIALIZED = "uninitialized"  # No _cardex-config.toml file
    INITIALIZED = "initialized"  # Version matches
    OUTDATED = "outdated"  # Version mismatch


class LibraryWorkflow:
    """Manages library folder initialization and version tracking."""

    def __init__(self, library_path: Path, workflow_name: str = "default"):
        """
        Initialize LibraryWorkflow.

        Args:
            library_path: Path to the library folder
            workflow_name: Name of the workflow to use (default, simple, advanced)
        """
        self.library_path = library_path
        self.workflow_name = workflow_name
        self.config_file = library_path / "_cardex-config.toml"
        self.workflow_config = self._load_workflow_config()

    def _load_workflow_config(self) -> Dict[str, Any]:
        """
        Load workflow configuration.
        
        Priority:
        1. Library-specific: {library}/.library-workflow.toml
        2. Project workflows: workflows/{workflow_name}.toml
        3. Fallback: Default minimal config
        """
        # Try library-specific override
        local_config = self.library_path / ".library-workflow.toml"
        if local_config.exists():
            with open(local_config, "r", encoding="utf-8") as f:
                return toml.load(f)

        # Try project workflows directory
        project_root = Path(__file__).parent.parent
        workflow_file = project_root / "workflows" / f"{self.workflow_name}.toml"
        if workflow_file.exists():
            with open(workflow_file, "r", encoding="utf-8") as f:
                return toml.load(f)
        # Default minimal config
        return {
            "workflow": {
                "version": "1.0.0",
                "steps": {
                    "step": [
                        {
                            "id": "create_input",
                            "action": "mkdir",
                            "target": "_input",
                            "required": True,
                        },
                        {
                            "id": "create_config",
                            "action": "write_config",
                            "target": "_cardex-config.toml",
                            "required": True,
                        },
                    ]
                },
            },
            "folders": {"input": "_input", "config_file": "_cardex-config.toml"},
        }

    def get_status(self) -> LibraryStatus:
        """
        Check the current status of the library folder.

        Returns:
            LibraryStatus enum value
        """
        if not self.config_file.exists():
            return LibraryStatus.UNINITIALIZED

        # Read current version from config file
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = toml.load(f)
            current_version = config.get("library", {}).get("version")
        except Exception:
            return LibraryStatus.UNINITIALIZED

        if not current_version:
            return LibraryStatus.UNINITIALIZED

        # Compare with expected version
        expected_version = self.workflow_config.get("workflow", {}).get("version", "1.0.0")

        if current_version == expected_version:
            return LibraryStatus.INITIALIZED
        else:
            return LibraryStatus.OUTDATED

    def get_library_version(self) -> Optional[str]:
        """
        Get the current version of the library folder.

        Returns:
            Version string or None if not initialized
        """
        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = toml.load(f)
            return config.get("library", {}).get("version")
        except Exception:
            return None

    def get_expected_version(self) -> str:
        """
        Get the expected version from workflow config.

        Returns:
            Expected version string
        """
        return self.workflow_config.get("workflow", {}).get("version", "1.0.0")

    def initialize(self) -> Dict[str, Any]:
        """
        Initialize the library folder.

        Creates required directories and config file.

        Returns:
            Dictionary with status and created items
        """
        created = []
        errors = []

        steps = self.workflow_config.get("workflow", {}).get("steps", {}).get("step", [])

        for step in steps:
            step_id = step.get("id")
            action = step.get("action")
            target = step.get("target")
            required = step.get("required", False)

            try:
                if action == "mkdir":
                    # Create directory
                    target_path = self.library_path / target
                    target_path.mkdir(exist_ok=True)
                    created.append(f"Created directory: {target}")

                elif action == "write_config":
                    # Write config file
                    version = self.get_expected_version()
                    now = datetime.now().isoformat()
                    config_content = {
                        "library": {
                            "workflow": self.workflow_name,
                            "version": version,
                            "initialized_at": now,
                            "last_updated": now,
                        },
                        "folders": self.workflow_config.get("folders", {"input": "_input"}),
                    }
                    with open(self.config_file, "w", encoding="utf-8") as f:
                        toml.dump(config_content, f)
                    created.append(f"Created config file: {target} (v{version})")

            except Exception as e:
                error_msg = f"Failed to execute step '{step_id}': {str(e)}"
                errors.append(error_msg)
                if required:
                    return {"success": False, "created": created, "errors": errors}

        return {"success": len(errors) == 0, "created": created, "errors": errors}

    def upgrade(self) -> Dict[str, Any]:
        """
        Upgrade the library folder to the latest version.

        Returns:
            Dictionary with status and upgrade steps performed
        """
        current_version = self.get_library_version()
        expected_version = self.get_expected_version()

        if current_version == expected_version:
            return {
                "success": True,
                "message": "Already at latest version",
                "from_version": current_version,
                "to_version": expected_version,
                "steps": [],
            }

        # Get migration steps
        upgrade_config = self.workflow_config.get("upgrade", {})
        migration_steps = upgrade_config.get(current_version or "0.1.0", [])

        performed_steps = []
        errors = []

        # Execute migration steps
        for step in migration_steps:
            try:
                if step == "create_processed":
                    processed_path = self.library_path / "_processed"
                    processed_path.mkdir(exist_ok=True)
                    performed_steps.append(f"Created _processed directory")
            except Exception as e:
                errors.append(f"Migration step failed: {step} - {str(e)}")

        # Update config file
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = toml.load(f)
            else:
                config = {"library": {}, "folders": {}}

            config["library"]["version"] = expected_version
            config["library"]["last_updated"] = datetime.now().isoformat()

            with open(self.config_file, "w", encoding="utf-8") as f:
                toml.dump(config, f)
            performed_steps.append(f"Updated config to {expected_version}")
        except Exception as e:
            errors.append(f"Failed to update config: {str(e)}")
            return {
                "success": False,
                "message": "Failed to update version",
                "from_version": current_version,
                "to_version": expected_version,
                "steps": performed_steps,
                "errors": errors,
            }

        return {
            "success": len(errors) == 0,
            "message": f"Upgraded from {current_version} to {expected_version}",
            "from_version": current_version,
            "to_version": expected_version,
            "steps": performed_steps,
            "errors": errors,
        }

    def get_input_folder(self) -> Path:
        """
        Get the input folder path where new PDFs should be placed.

        Returns:
            Path to the _input folder
        """
        input_folder = self.workflow_config.get("folders", {}).get("input", "_input")
        return self.library_path / input_folder

"""File naming strategies for academic papers.

Provides DOI-based, title-based, and custom naming strategies with special character handling.
"""

import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class NamingResult:
    """Result of file naming operation."""

    filename: str
    strategy_used: str  # doi, title, fallback, original
    is_safe: bool  # Whether filename is filesystem-safe
    warnings: list[str]  # Any warnings or issues


class FileNamingStrategy:
    """Generate safe filenames for academic papers."""

    # Characters that are problematic in filenames
    UNSAFE_CHARS = r'[<>:"/\\|?*\x00-\x1f]'

    # Maximum filename length (conservative, works on all platforms)
    MAX_FILENAME_LENGTH = 200

    def __init__(self):
        """Initialize naming strategy."""
        pass

    def generate_filename(
        self,
        doi: Optional[str] = None,
        title: Optional[str] = None,
        original_filename: Optional[str] = None,
    ) -> NamingResult:
        """Generate filename using priority strategy:

        1. DOI-based (most reliable, unique)
        2. Title-based (if no DOI)
        3. Original filename (fallback)

        Args:
            doi: DOI string
            title: Paper title
            original_filename: Original PDF filename

        Returns:
            NamingResult with generated filename and metadata
        """
        warnings = []

        # Strategy 1: DOI-based naming
        if doi:
            filename = self._doi_to_filename(doi)
            if filename:
                return NamingResult(
                    filename=filename, strategy_used="doi", is_safe=True, warnings=warnings
                )
            else:
                warnings.append("Invalid DOI format, falling back to title")

        # Strategy 2: Title-based naming
        if title:
            filename = self._title_to_filename(title)
            if filename and len(filename) > 5:  # Sanity check
                return NamingResult(
                    filename=filename, strategy_used="title", is_safe=True, warnings=warnings
                )
            else:
                warnings.append("Title too short or invalid, falling back to original")

        # Strategy 3: Keep original filename (sanitized)
        if original_filename:
            filename = self._sanitize_filename(Path(original_filename).stem) + ".pdf"
            return NamingResult(
                filename=filename,
                strategy_used="fallback",
                is_safe=True,
                warnings=warnings + ["Using sanitized original filename"],
            )

        # Last resort: generate generic name
        import hashlib
        import time

        hash_input = f"{doi or ''}{title or ''}{time.time()}".encode()
        hash_str = hashlib.md5(hash_input).hexdigest()[:8]
        filename = f"paper_{hash_str}.pdf"

        return NamingResult(
            filename=filename,
            strategy_used="generated",
            is_safe=True,
            warnings=warnings + ["Could not determine meaningful name, generated random"],
        )

    def _doi_to_filename(self, doi: str) -> Optional[str]:
        """Convert DOI to safe filename.

        DOI format: 10.xxxx/yyyy
        Filename format: 10.xxxx-yyyy.pdf

        Examples:
            10.1234/abc-123 -> 10.1234-abc-123.pdf
            10.1000/xyz.456 -> 10.1000-xyz.456.pdf

        Args:
            doi: DOI string

        Returns:
            Safe filename or None if invalid DOI
        """
        if not doi or not doi.startswith("10."):
            return None

        # Replace forward slash with hyphen
        filename = doi.replace("/", "-")

        # Remove other unsafe characters
        filename = re.sub(self.UNSAFE_CHARS, "", filename)

        # Replace spaces and multiple hyphens
        filename = re.sub(r"\s+", "_", filename)
        filename = re.sub(r"-+", "-", filename)

        # Add extension
        filename = f"{filename}.pdf"

        # Length check
        if len(filename) > self.MAX_FILENAME_LENGTH:
            # Truncate but keep DOI prefix
            prefix = filename[:30]  # Keep "10.xxxx-" part
            suffix = filename[-20:]  # Keep extension
            filename = f"{prefix}...{suffix}"

        return filename

    def _title_to_filename(self, title: str) -> Optional[str]:
        """Convert title to safe filename.

        Rules:
        - Lowercase
        - Spaces -> underscores
        - Remove special characters
        - Limit length
        - Keep alphanumeric and basic punctuation

        Examples:
            "Deep Learning: A Survey" -> "deep_learning_a_survey.pdf"
            "What is AI?" -> "what_is_ai.pdf"

        Args:
            title: Paper title

        Returns:
            Safe filename or None if title is invalid
        """
        if not title or len(title) < 3:
            return None

        # Lowercase
        filename = title.lower()

        # Remove content in parentheses/brackets (often metadata)
        filename = re.sub(r"\([^)]*\)", "", filename)
        filename = re.sub(r"\[[^\]]*\]", "", filename)

        # Remove special characters, keep alphanumeric, spaces, hyphens
        filename = re.sub(r"[^a-z0-9\s\-]", "", filename)

        # Replace multiple spaces/hyphens with single underscore
        filename = re.sub(r"[\s\-]+", "_", filename)

        # Remove leading/trailing underscores
        filename = filename.strip("_")

        # Truncate if too long
        if len(filename) > self.MAX_FILENAME_LENGTH - 4:  # Reserve space for .pdf
            filename = filename[: self.MAX_FILENAME_LENGTH - 4]
            # Cut at last underscore to avoid partial words
            last_underscore = filename.rfind("_")
            if last_underscore > 50:  # Keep reasonable minimum
                filename = filename[:last_underscore]

        # Add extension
        filename = f"{filename}.pdf"

        return filename

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize any filename to be filesystem-safe.

        Args:
            filename: Original filename (without extension)

        Returns:
            Sanitized filename (without extension)
        """
        # Remove unsafe characters
        safe = re.sub(self.UNSAFE_CHARS, "", filename)

        # Replace spaces with underscores
        safe = re.sub(r"\s+", "_", safe)

        # Remove multiple underscores
        safe = re.sub(r"_+", "_", safe)

        # Remove leading/trailing underscores
        safe = safe.strip("_")

        # Ensure not empty
        if not safe:
            safe = "file"

        # Truncate if needed
        if len(safe) > self.MAX_FILENAME_LENGTH - 4:
            safe = safe[: self.MAX_FILENAME_LENGTH - 4]

        return safe

    def is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe for all platforms.

        Args:
            filename: Filename to check

        Returns:
            True if safe
        """
        # Check for unsafe characters
        if re.search(self.UNSAFE_CHARS, filename):
            return False

        # Check length
        if len(filename) > self.MAX_FILENAME_LENGTH:
            return False

        # Check reserved names (Windows)
        reserved = {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "LPT1", "LPT2"}
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in reserved:
            return False

        return True

    def suggest_unique_filename(self, base_filename: str, existing_files: set[str]) -> str:
        """Generate unique filename if collision detected.

        Args:
            base_filename: Desired filename
            existing_files: Set of existing filenames

        Returns:
            Unique filename with suffix if needed
        """
        if base_filename not in existing_files:
            return base_filename

        # Add numeric suffix
        name = Path(base_filename).stem
        ext = Path(base_filename).suffix

        counter = 1
        while True:
            candidate = f"{name}_{counter}{ext}"
            if candidate not in existing_files:
                return candidate
            counter += 1

            # Safety: prevent infinite loop
            if counter > 9999:
                import hashlib

                hash_str = hashlib.md5(base_filename.encode()).hexdigest()[:6]
                return f"{name}_{hash_str}{ext}"

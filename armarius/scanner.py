"""PDF file scanner for Cardex.

Discovers PDF files in configured directories and extracts basic metadata.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF


@dataclass
class PDFInfo:
    """Information about a discovered PDF file."""

    path: Path
    filename: str
    size_bytes: int
    modified_time: datetime
    is_readable: bool
    page_count: Optional[int] = None
    error: Optional[str] = None

    @property
    def size_mb(self) -> float:
        """File size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    @property
    def relative_path(self) -> str:
        """Get path relative to library root.

        This is set externally by the scanner.
        """
        return str(self.path)


class PDFScanner:
    """Scans directories for PDF files."""

    def __init__(self, root_path: Path, recursive: bool = True):
        """Initialize PDF scanner.

        Args:
            root_path: Root directory to scan
            recursive: If True, scan subdirectories recursively
        """
        self.root_path = Path(root_path).expanduser().resolve()
        self.recursive = recursive

    def scan(self) -> List[PDFInfo]:
        """Scan for PDF files in the configured directory.

        Returns:
            List of PDFInfo objects

        Raises:
            FileNotFoundError: If root_path does not exist
        """
        if not self.root_path.exists():
            raise FileNotFoundError(f"Directory not found: {self.root_path}")

        if not self.root_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.root_path}")

        # Find all PDF files
        pattern = "**/*.pdf" if self.recursive else "*.pdf"
        pdf_files = sorted(self.root_path.glob(pattern))

        # Extract info from each PDF
        results = []
        for pdf_path in pdf_files:
            info = self._extract_info(pdf_path)
            results.append(info)

        return results

    def _extract_info(self, pdf_path: Path) -> PDFInfo:
        """Extract basic information from a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            PDFInfo object with extracted information
        """
        stat = pdf_path.stat()
        modified_time = datetime.fromtimestamp(stat.st_mtime)

        # Try to open PDF and check readability
        is_readable = False
        page_count = None
        error = None

        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            is_readable = True
            doc.close()
        except Exception as e:
            error = str(e)

        # Calculate relative path
        try:
            relative_path = pdf_path.relative_to(self.root_path)
        except ValueError:
            relative_path = pdf_path

        return PDFInfo(
            path=relative_path,
            filename=pdf_path.name,
            size_bytes=stat.st_size,
            modified_time=modified_time,
            is_readable=is_readable,
            page_count=page_count,
            error=error,
        )

    def get_stats(self, pdf_list: List[PDFInfo]) -> dict:
        """Get summary statistics for scanned PDFs.

        Args:
            pdf_list: List of PDFInfo objects

        Returns:
            Dictionary with statistics
        """
        total_count = len(pdf_list)
        readable_count = sum(1 for pdf in pdf_list if pdf.is_readable)
        unreadable_count = total_count - readable_count
        total_size_mb = sum(pdf.size_bytes for pdf in pdf_list) / (1024 * 1024)
        total_pages = sum(pdf.page_count for pdf in pdf_list if pdf.page_count)

        return {
            "total_count": total_count,
            "readable_count": readable_count,
            "unreadable_count": unreadable_count,
            "total_size_mb": round(total_size_mb, 2),
            "total_pages": total_pages,
        }

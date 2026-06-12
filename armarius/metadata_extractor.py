"""Metadata extraction from PDF files.

Extracts DOI, title, authors, and other bibliographic information from PDFs.
"""

import re
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

import fitz  # PyMuPDF


@dataclass
class PaperMetadata:
    """Extracted metadata from a PDF file."""

    doi: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[list[str]] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    abstract: Optional[str] = None
    doi_source: str = "none"  # pdf_metadata, pdf_text, crossref, semantic_scholar, manual, none


class DOIExtractor:
    """Extract DOI from PDF files."""

    # DOI regex pattern (covers 10.xxxx/yyyy format)
    DOI_PATTERN = re.compile(r"10\.\d{4,}/[^\s\"<>]+", re.IGNORECASE)

    def __init__(self):
        """Initialize DOI extractor."""
        pass

    def extract_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """Extract DOI from PDF file.

        Tries multiple extraction methods:
        1. PDF metadata (most reliable if present)
        2. First page text extraction
        3. Full text search (slower, fallback)

        Args:
            pdf_path: Path to PDF file

        Returns:
            DOI string or None if not found
        """
        try:
            doc = fitz.open(pdf_path)

            # Method 1: Check PDF metadata
            doi = self._extract_from_metadata(doc)
            if doi:
                doc.close()
                return doi

            # Method 2: Check first page (most common location)
            doi = self._extract_from_first_page(doc)
            if doi:
                doc.close()
                return doi

            # Method 3: Full text search (fallback)
            doi = self._extract_from_full_text(doc)
            doc.close()
            return doi

        except Exception as e:
            print(f"Error extracting DOI from {pdf_path}: {e}")
            return None

    def _extract_from_metadata(self, doc: fitz.Document) -> Optional[str]:
        """Extract DOI from PDF metadata.

        Args:
            doc: PyMuPDF document object

        Returns:
            DOI string or None
        """
        metadata = doc.metadata
        if not metadata:
            return None

        # Check common metadata fields
        for key in ["doi", "subject", "keywords"]:
            value = metadata.get(key, "")
            if value:
                doi = self._parse_doi(value)
                if doi:
                    return doi

        return None

    def _extract_from_first_page(self, doc: fitz.Document) -> Optional[str]:
        """Extract DOI from first page text.

        Args:
            doc: PyMuPDF document object

        Returns:
            DOI string or None
        """
        if len(doc) == 0:
            return None

        try:
            first_page = doc[0]
            text = first_page.get_text()
            return self._parse_doi(text)
        except Exception:
            return None

    def _extract_from_full_text(self, doc: fitz.Document, max_pages: int = 3) -> Optional[str]:
        """Extract DOI from full document text (limited pages).

        Args:
            doc: PyMuPDF document object
            max_pages: Maximum pages to search (default: 3)

        Returns:
            DOI string or None
        """
        for page_num in range(min(len(doc), max_pages)):
            try:
                page = doc[page_num]
                text = page.get_text()
                doi = self._parse_doi(text)
                if doi:
                    return doi
            except Exception:
                continue

        return None

    def _parse_doi(self, text: str) -> Optional[str]:
        """Parse DOI from text using regex.

        Args:
            text: Text to search for DOI

        Returns:
            Clean DOI string or None
        """
        if not text:
            return None

        # Search for DOI pattern
        match = self.DOI_PATTERN.search(text)
        if match:
            doi = match.group(0)
            # Clean up DOI (remove trailing punctuation)
            doi = doi.rstrip(".,;:")
            return doi

        return None

    def validate_doi(self, doi: str) -> bool:
        """Validate DOI format.

        Args:
            doi: DOI string to validate

        Returns:
            True if valid DOI format
        """
        if not doi:
            return False

        return bool(self.DOI_PATTERN.match(doi))


class MetadataExtractor:
    """Extract comprehensive metadata from PDF files."""

    def __init__(self):
        """Initialize metadata extractor."""
        self.doi_extractor = DOIExtractor()

    def extract(self, pdf_path: Path) -> PaperMetadata:
        """Extract all available metadata from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            PaperMetadata object with extracted information
        """
        metadata = PaperMetadata()

        try:
            doc = fitz.open(pdf_path)

            # Extract DOI
            doi = self.doi_extractor.extract_from_pdf(pdf_path)
            if doi:
                metadata.doi = doi
                metadata.doi_source = "pdf_metadata"

            # Extract title from metadata or first page
            metadata.title = self._extract_title(doc)

            # Extract authors (basic implementation)
            metadata.authors = self._extract_authors(doc)

            # Extract year from metadata or text
            metadata.year = self._extract_year(doc)

            doc.close()

        except Exception as e:
            print(f"Error extracting metadata from {pdf_path}: {e}")

        return metadata

    def _extract_title(self, doc: fitz.Document) -> Optional[str]:
        """Extract title from PDF.

        Args:
            doc: PyMuPDF document object

        Returns:
            Title string or None
        """
        # Try PDF metadata first
        metadata = doc.metadata
        if metadata and metadata.get("title"):
            title = metadata["title"]
            # Filter out useless titles
            if len(title) > 10 and not title.lower().startswith("untitled"):
                return title.strip()

        # Fallback: Extract from first page (heuristic: largest text in first 1/3)
        # This is a placeholder - production would use more sophisticated methods
        try:
            first_page = doc[0]
            text = first_page.get_text()
            # Simple heuristic: first non-empty line
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            if lines:
                return lines[0][:200]  # Limit length
        except Exception:
            pass

        return None

    def _extract_authors(self, doc: fitz.Document) -> Optional[list[str]]:
        """Extract authors from PDF.

        Args:
            doc: PyMuPDF document object

        Returns:
            List of author names or None
        """
        metadata = doc.metadata
        if metadata and metadata.get("author"):
            author_str = metadata["author"]
            # Split by common delimiters
            authors = re.split(r"[,;]|\sand\s", author_str)
            return [a.strip() for a in authors if a.strip()]

        return None

    def _extract_year(self, doc: fitz.Document) -> Optional[int]:
        """Extract publication year from PDF.

        Args:
            doc: PyMuPDF document object

        Returns:
            Year as integer or None
        """
        # Try metadata creation date
        metadata = doc.metadata
        if metadata and metadata.get("creationDate"):
            date_str = metadata["creationDate"]
            # Parse year from date string (format: D:YYYYMMDDHHmmSS+TZ)
            year_match = re.search(r"D:(\d{4})", date_str)
            if year_match:
                year = int(year_match.group(1))
                # Sanity check
                if 1900 <= year <= 2100:
                    return year

        # Fallback: Search first page for year pattern
        try:
            first_page = doc[0]
            text = first_page.get_text()
            # Look for 4-digit year (common pattern: "2024", "2023", etc.)
            year_matches = re.findall(r"\b(19\d{2}|20\d{2})\b", text)
            if year_matches:
                # Return most recent plausible year
                years = [int(y) for y in year_matches if 1900 <= int(y) <= 2100]
                if years:
                    return max(years)
        except Exception:
            pass

        return None

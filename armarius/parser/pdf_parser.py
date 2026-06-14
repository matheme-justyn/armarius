"""PDF parser using PyMuPDF with bounding box extraction."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF


class ChunkingStrategy(Enum):
    BLOCK = "block"
    SENTENCE = "sentence"
    FIXED = "fixed"


@dataclass
class BoundingBox:
    """Bounding box coordinates in PDF coordinate system."""

    x0: float
    y0: float
    x1: float
    y1: float
    page: int

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "x0": self.x0,
            "y0": self.y0,
            "x1": self.x1,
            "y1": self.y1,
            "page": self.page,
        }

    def to_rect(self) -> fitz.Rect:
        """Convert to PyMuPDF Rect object."""
        return fitz.Rect(self.x0, self.y0, self.x1, self.y1)


@dataclass
class TextChunk:
    """Text chunk with bounding box and metadata."""

    text: str
    bbox: BoundingBox
    pdf_path: str
    chunk_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "text": self.text,
            "bbox": self.bbox.to_dict(),
            "pdf_path": self.pdf_path,
            "chunk_id": self.chunk_id,
        }


class PDFParser:
    """Parse PDF documents with bounding box extraction."""

    def __init__(self, pdf_path: Optional[str | Path] = None):
        """
        Initialize PDF parser.

        Args:
            pdf_path: Path to PDF file (optional for stateless usage)
        """
        self.pdf_path = Path(pdf_path) if pdf_path else None
        self.doc = None
        
        if self.pdf_path:
            if not self.pdf_path.exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")
            self.doc = fitz.open(self.pdf_path)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close document."""
        self.close()

    def close(self):
        """Close the PDF document."""
        if self.doc:
            self.doc.close()

    def extract_text_with_bbox(
        self, page_num: int
    ) -> List[TextChunk]:
        """
        Extract text blocks with bounding boxes from a page.

        Args:
            page_num: Page number (0-indexed)

        Returns:
            List of TextChunk objects with bbox info
        """
        if page_num >= len(self.doc):
            raise ValueError(
                f"Page {page_num} out of range (0-{len(self.doc)-1})"
            )

        page = self.doc[page_num]
        text_dict = page.get_text("dict")

        chunks = []
        for block in text_dict.get("blocks", []):
            # Only process text blocks (type 0), skip images
            if block.get("type") != 0:
                continue

            # Extract text from lines
            block_text = ""
            bbox_coords = block["bbox"]  # (x0, y0, x1, y1)

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    block_text += span.get("text", "")
                block_text += "\n"

            block_text = block_text.strip()
            if not block_text:
                continue

            bbox = BoundingBox(
                x0=bbox_coords[0],
                y0=bbox_coords[1],
                x1=bbox_coords[2],
                y1=bbox_coords[3],
                page=page_num,
            )

            chunk = TextChunk(
                text=block_text,
                bbox=bbox,
                pdf_path=str(self.pdf_path),
            )
            chunks.append(chunk)

        return chunks

    def extract_all_pages(self) -> List[TextChunk]:
        """
        Extract text chunks from all pages.

        Returns:
            List of all TextChunk objects from the document
        """
        all_chunks = []
        for page_num in range(len(self.doc)):
            chunks = self.extract_text_with_bbox(page_num)
            all_chunks.extend(chunks)
        return all_chunks

    def extract_all(
        self,
        pdf_path: Path,
        strategy: ChunkingStrategy = ChunkingStrategy.BLOCK,
        chunk_size: int = 512,
        overlap: int = 50,
    ) -> List[TextChunk]:
        """
        Extract and chunk text from PDF.

        Args:
            pdf_path: Path to PDF file
            strategy: Chunking strategy to use
            chunk_size: Size for fixed chunking
            overlap: Overlap for fixed chunking

        Returns:
            List of text chunks
        """
        if self.doc:
            self.close()
        
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        self.doc = fitz.open(self.pdf_path)
        
        base_chunks = self.extract_all_pages()
        
        if strategy == ChunkingStrategy.BLOCK:
            from armarius.parser.chunking import BlockLevelChunking
            chunker = BlockLevelChunking()
        elif strategy == ChunkingStrategy.SENTENCE:
            from armarius.parser.chunking import SentenceLevelChunking
            chunker = SentenceLevelChunking()
        elif strategy == ChunkingStrategy.FIXED:
            from armarius.parser.chunking import FixedSizeChunking
            chunker = FixedSizeChunking(chunk_size=chunk_size, overlap=overlap)
        else:
            chunker = None
        
        if chunker:
            return chunker.chunk(base_chunks)
        return base_chunks

    def get_page_count(self) -> int:
        """Get total number of pages."""
        return len(self.doc)

    def get_metadata(self) -> dict:
        """
        Extract PDF metadata.

        Returns:
            Dictionary with title, author, creation date, etc.
        """
        metadata = self.doc.metadata
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "mod_date": metadata.get("modDate", ""),
            "page_count": len(self.doc),
        }

    def generate_screenshot(
        self,
        bbox: BoundingBox,
        output_path: str | Path,
        dpi: int = 300,
    ) -> Path:
        """
        Generate screenshot of a bounding box region.

        Args:
            bbox: Bounding box to capture
            output_path: Path to save screenshot
            dpi: Resolution in dots per inch

        Returns:
            Path to saved screenshot
        """
        if bbox.page >= len(self.doc):
            raise ValueError(
                f"Page {bbox.page} out of range (0-{len(self.doc)-1})"
            )

        page = self.doc[bbox.page]
        rect = bbox.to_rect()

        # Calculate zoom factor from DPI (default PDF DPI is 72)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)

        # Get pixmap of the clipped region
        pix = page.get_pixmap(matrix=mat, clip=rect)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        pix.save(str(output_path))
        return output_path

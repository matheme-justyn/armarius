"""Dedicated PDF processing module boundary for Armarius."""

import csv
import io
import mimetypes
from pathlib import Path

import fitz

from armarius.metadata_extractor import MetadataExtractor
from armarius.pdf_processing.models import PDFProcessingResult, PDFValidationResult


class PDFProcessor:
    """Validate and normalize PDFs through a stable module interface."""

    ENGINE_NAME = "pymupdf"
    ENGINE_VERSION = getattr(fitz, "VersionBind", "unknown")
    RULE_VERSION = "1"

    def __init__(self) -> None:
        """Initialize the PDF processor."""
        self._metadata_extractor = MetadataExtractor()

    def validate_pdf(self, path: Path) -> PDFValidationResult:
        """Validate that a path points to a readable PDF file."""
        detected_mime_type, _ = mimetypes.guess_type(path.name)
        detected_mime_type = detected_mime_type or "application/octet-stream"

        try:
            with path.open("rb") as file_obj:
                header = file_obj.read(5)
            if header != b"%PDF-":
                return PDFValidationResult(
                    path=path,
                    is_valid=False,
                    detected_mime_type=detected_mime_type,
                    reason="invalid_pdf_header",
                )

            document = fitz.open(path)
            page_count = document.page_count
            document.close()
            return PDFValidationResult(
                path=path,
                is_valid=True,
                detected_mime_type="application/pdf",
                page_count=page_count,
            )
        except Exception as exc:
            return PDFValidationResult(
                path=path,
                is_valid=False,
                detected_mime_type=detected_mime_type,
                reason=str(exc),
            )

    def extract_metadata(self, path: Path) -> dict[str, object]:
        """Extract bibliographic metadata for a PDF path."""
        metadata = self._metadata_extractor.extract(path)
        return {
            "title": metadata.title,
            "authors": metadata.authors,
            "year": metadata.year,
            "venue": metadata.venue,
            "doi": metadata.doi,
            "doi_source": metadata.doi_source,
        }

    def extract_metadata_confidence(self, path: Path) -> dict[str, dict[str, object]]:
        """Return metadata values with simple source/confidence hints."""
        metadata = self._metadata_extractor.extract(path)
        return {
            "title": {"value": metadata.title, "source": "pdf_text", "confidence": 0.6 if metadata.title else 0.0},
            "authors": {"value": metadata.authors or [], "source": "pdf_text", "confidence": 0.4 if metadata.authors else 0.0},
            "year": {"value": metadata.year, "source": "pdf_text", "confidence": 0.5 if metadata.year else 0.0},
            "venue": {"value": metadata.venue, "source": "pdf_text", "confidence": 0.0},
            "doi": {"value": metadata.doi, "source": metadata.doi_source, "confidence": 0.9 if metadata.doi else 0.0},
        }

    def process_pdf(self, path: Path) -> PDFProcessingResult:
        """Extract normalized text and metadata from a PDF."""
        document = fitz.open(path)
        page_texts: list[str] = []
        tables: list[dict[str, object]] = []
        images: list[dict[str, object]] = []
        for page_index, page in enumerate(document, start=1):
            page_text = page.get_text("text").strip()
            page_texts.append(f"## Page {page_index}\n\n{page_text}" if page_text else f"## Page {page_index}")
            tables.extend(self._extract_tables(page, page_index))
            images.extend(self._extract_images(page, page_index, document))

        page_count = document.page_count
        extracted_text = "\n\n".join(text.replace("\x00", "") for text in page_texts).strip()
        metadata = self._metadata_extractor.extract(path)
        metadata_confidence = self.extract_metadata_confidence(path)
        document.close()

        safe_title = (metadata.title or path.stem).replace('"', '\"')
        markdown_lines = [
            "---",
            f'title: "{safe_title}"',
            f'doi: "{metadata.doi or ""}"',
            f'year: "{metadata.year or ""}"',
            "source: pdf_processing",
            f'engine: "{self.ENGINE_NAME}"',
            f'engine_version: "{self.ENGINE_VERSION}"',
            f'rule_version: "{self.RULE_VERSION}"',
            "---",
            "",
            extracted_text,
            "",
        ]

        return PDFProcessingResult(
            source_path=path,
            markdown_text="\n".join(markdown_lines),
            extracted_text=extracted_text,
            page_count=page_count,
            tables=tables,
            images=images,
            metadata={
                "title": metadata.title,
                "authors": metadata.authors,
                "year": metadata.year,
                "venue": metadata.venue,
                "doi": metadata.doi,
                "doi_source": metadata.doi_source,
            },
            metadata_confidence=metadata_confidence,
        )

    def _extract_tables(self, page: fitz.Page, page_index: int) -> list[dict[str, object]]:
        """Extract simple table-like structures when supported by the engine."""
        if not hasattr(page, "find_tables"):
            return []
        try:
            finder = page.find_tables()
        except Exception:
            return []
        extracted: list[dict[str, object]] = []
        for table_index, table in enumerate(getattr(finder, "tables", []), start=1):
            rows = table.extract()
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            for row in rows:
                writer.writerow(row)
            extracted.append({
                "page": page_index,
                "table_index": table_index,
                "rows": rows,
                "csv": csv_buffer.getvalue(),
                "bbox": list(table.bbox) if getattr(table, "bbox", None) else None,
            })
        return extracted

    def _extract_images(self, page: fitz.Page, page_index: int, document: fitz.Document) -> list[dict[str, object]]:
        """Extract image candidates while filtering tiny noisy icons."""
        extracted: list[dict[str, object]] = []
        if not hasattr(page, "get_images"):
            return extracted
        try:
            page_images = page.get_images(full=True)
        except Exception:
            return extracted
        for image_index, image_info in enumerate(page_images, start=1):
            xref = image_info[0]
            try:
                image_data = document.extract_image(xref)
            except Exception:
                continue
            width = image_data.get("width", 0)
            height = image_data.get("height", 0)
            if width < 48 or height < 48 or (width * height) < 4096:
                continue
            extracted.append({
                "page": page_index,
                "image_index": image_index,
                "xref": xref,
                "ext": image_data.get("ext", "bin"),
                "width": width,
                "height": height,
                "bytes": image_data.get("image", b""),
            })
        return extracted

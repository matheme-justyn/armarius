"""Cataloging system for organizing papers in different directory structures.

Supports switchable catalog methods: by year, by venue, by custom category, flat, etc.
"""

import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import json

from armarius.database import CardexDatabase
from armarius.metadata_extractor import MetadataExtractor, PaperMetadata
from armarius.doi_resolver import DOIResolver, ResolvedMetadata
from armarius.naming_strategy import FileNamingStrategy, NamingResult


@dataclass
class CatalogResult:
    """Result of cataloging operation."""

    success: bool
    paper_id: str
    original_path: Path
    new_path: Optional[Path]
    filename: str
    catalog_method: str
    errors: List[str]
    warnings: List[str]


class CatalogMethod:
    """Base class for catalog methods."""

    def get_target_directory(self, library_root: Path, metadata: PaperMetadata) -> Path:
        """Get target directory for a paper based on metadata.

        Args:
            library_root: Library root directory
            metadata: Paper metadata

        Returns:
            Target directory path
        """
        raise NotImplementedError


class FlatCatalog(CatalogMethod):
    """Flat structure - all papers in root directory."""

    def get_target_directory(self, library_root: Path, metadata: PaperMetadata) -> Path:
        return library_root


class ByYearCatalog(CatalogMethod):
    """Organize by publication year: library/2024/, library/2023/"""

    def get_target_directory(self, library_root: Path, metadata: PaperMetadata) -> Path:
        if metadata.year:
            return library_root / str(metadata.year)
        else:
            return library_root / "unknown_year"


class ByVenueCatalog(CatalogMethod):
    """Organize by venue: library/Nature/, library/ICML/"""

    def get_target_directory(self, library_root: Path, metadata: PaperMetadata) -> Path:
        if metadata.venue:
            # Sanitize venue name for directory
            safe_venue = metadata.venue.replace("/", "-").replace(":", "")
            safe_venue = safe_venue[:100]  # Limit length
            return library_root / safe_venue
        else:
            return library_root / "unknown_venue"


class ByCustomCategoryCatalog(CatalogMethod):
    """Organize by user-defined categories.

    Requires manual category assignment stored in database.
    """

    def get_target_directory(self, library_root: Path, metadata: PaperMetadata) -> Path:
        # This would need category info from database
        # For now, return a placeholder
        return library_root / "uncategorized"


CATALOG_METHODS: Dict[str, CatalogMethod] = {
    "flat": FlatCatalog(),
    "by_year": ByYearCatalog(),
    "by_venue": ByVenueCatalog(),
    "by_custom_category_A": ByCustomCategoryCatalog(),
}


class CatalogingService:
    """Main service for paper ingestion and cataloging."""

    def __init__(self, library_root: Path, db: CardexDatabase):
        """Initialize cataloging service.

        Args:
            library_root: Library root directory
            db: Database instance
        """
        self.library_root = Path(library_root)
        self.db = db
        self.metadata_extractor = MetadataExtractor()
        self.doi_resolver = DOIResolver()
        self.naming_strategy = FileNamingStrategy()

    def ingest_paper(
        self,
        pdf_path: Path,
        catalog_method: str = "by_year",
        enable_network_lookup: bool = True,
    ) -> CatalogResult:
        """Ingest a PDF paper into the library.

        Workflow:
        1. Extract metadata from PDF (DOI, title, etc.)
        2. If DOI missing, query Crossref/Semantic Scholar
        3. Generate safe filename (DOI-based or title-based)
        4. Determine target directory based on catalog method
        5. Move file to target location
        6. Record in database

        Args:
            pdf_path: Path to PDF file
            catalog_method: Catalog method to use
            enable_network_lookup: Whether to query external APIs

        Returns:
            CatalogResult with operation details
        """
        errors = []
        warnings = []

        try:
            # Step 1: Extract metadata from PDF
            metadata = self.metadata_extractor.extract(pdf_path)

            # Step 2: Enrich metadata via network if enabled
            if enable_network_lookup and (not metadata.doi or not metadata.title):
                resolved = self.doi_resolver.resolve(doi=metadata.doi, title=metadata.title)
                if resolved:
                    # Merge resolved metadata
                    if resolved.doi and not metadata.doi:
                        metadata.doi = resolved.doi
                        metadata.doi_source = resolved.source
                    if resolved.title and not metadata.title:
                        metadata.title = resolved.title
                    if resolved.authors and not metadata.authors:
                        metadata.authors = resolved.authors
                    if resolved.year and not metadata.year:
                        metadata.year = resolved.year
                    if resolved.venue and not metadata.venue:
                        metadata.venue = resolved.venue

            # Step 3: Generate filename
            naming_result = self.naming_strategy.generate_filename(
                doi=metadata.doi,
                title=metadata.title,
                original_filename=pdf_path.name,
            )
            warnings.extend(naming_result.warnings)

            # Step 4: Determine target directory
            catalog_impl = CATALOG_METHODS.get(catalog_method, FlatCatalog())
            target_dir = catalog_impl.get_target_directory(self.library_root, metadata)
            target_dir.mkdir(parents=True, exist_ok=True)

            # Step 5: Check for filename collision
            target_path = target_dir / naming_result.filename
            if target_path.exists() and target_path != pdf_path:
                # Handle collision
                existing_files = {f.name for f in target_dir.glob("*.pdf")}
                unique_filename = self.naming_strategy.suggest_unique_filename(
                    naming_result.filename, existing_files
                )
                target_path = target_dir / unique_filename
                warnings.append(f"Filename collision, renamed to {unique_filename}")

            # Step 6: Move file (or copy if same directory)
            if target_path != pdf_path:
                shutil.move(str(pdf_path), str(target_path))

            # Step 7: Record in database
            paper_id = self._generate_paper_id(metadata.doi, target_path)
            self._save_to_database(
                paper_id=paper_id,
                metadata=metadata,
                original_filename=pdf_path.name,
                current_filename=target_path.name,
                file_path=str(target_path.relative_to(self.library_root)),
                catalog_method=catalog_method,
            )

            return CatalogResult(
                success=True,
                paper_id=paper_id,
                original_path=pdf_path,
                new_path=target_path,
                filename=target_path.name,
                catalog_method=catalog_method,
                errors=errors,
                warnings=warnings,
            )

        except Exception as e:
            errors.append(str(e))
            return CatalogResult(
                success=False,
                paper_id="",
                original_path=pdf_path,
                new_path=None,
                filename=pdf_path.name,
                catalog_method=catalog_method,
                errors=errors,
                warnings=warnings,
            )

    def _generate_paper_id(self, doi: Optional[str], path: Path) -> str:
        """Generate unique paper ID.

        Args:
            doi: DOI if available
            path: File path

        Returns:
            Paper ID (DOI or hash)
        """
        if doi:
            # Use DOI as ID (URL-safe)
            return doi.replace("/", "_")
        else:
            # Generate hash from file
            import hashlib

            with open(path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash[:16]

    def _save_to_database(
        self,
        paper_id: str,
        metadata: PaperMetadata,
        original_filename: str,
        current_filename: str,
        file_path: str,
        catalog_method: str,
    ):
        """Save paper metadata to database.

        Args:
            paper_id: Unique paper ID
            metadata: Extracted metadata
            original_filename: Original filename
            current_filename: Current filename
            file_path: Relative file path
            catalog_method: Catalog method used
        """
        cursor = self.db.conn.cursor()
        now = datetime.now().isoformat()

        # Prepare authors JSON
        authors_json = json.dumps(metadata.authors) if metadata.authors else None

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO papers (
                    id, title, authors, year, venue, doi, file_path,
                    original_filename, current_filename, catalog_method,
                    doi_source, ingest_status, ingested_at, last_verified_at,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    paper_id,
                    metadata.title,
                    authors_json,
                    metadata.year,
                    metadata.venue,
                    metadata.doi,
                    file_path,
                    original_filename,
                    current_filename,
                    catalog_method,
                    metadata.doi_source,
                    "completed",
                    now,
                    now,
                    "unread",
                ),
            )
            self.db.conn.commit()
        except Exception as e:
            print(f"Error saving to database: {e}")
            raise

    def recatalog_library(self, new_method: str) -> Dict[str, Any]:
        """Switch catalog method and reorganize all papers.

        Workflow:
        1. Read current catalog method from database
        2. For each paper, calculate new location
        3. Move files if needed
        4. Update database with new paths
        5. Handle missing files (search + mark)

        Args:
            new_method: New catalog method name

        Returns:
            Summary dict with counts and errors
        """
        if new_method not in CATALOG_METHODS:
            raise ValueError(f"Unknown catalog method: {new_method}")

        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM papers")
        papers = cursor.fetchall()

        results = {
            "total": len(papers),
            "moved": 0,
            "not_found": 0,
            "errors": 0,
            "missing_papers": [],
        }

        catalog_impl = CATALOG_METHODS[new_method]

        for paper in papers:
            paper_dict = dict(paper)
            paper_id = paper_dict["id"]
            current_path = self.library_root / paper_dict["file_path"]

            try:
                # Check if file exists
                if not current_path.exists():
                    # Try to find it
                    found_path = self._search_for_file(paper_dict)
                    if found_path:
                        current_path = found_path
                        warnings = [f"Found file at {found_path}"]
                    else:
                        # Mark as missing
                        cursor.execute(
                            "UPDATE papers SET ingest_status = ?, error_message = ? WHERE id = ?",
                            ("missing", "File not found during recatalog", paper_id),
                        )
                        results["not_found"] += 1
                        results["missing_papers"].append(paper_id)
                        continue

                # Reconstruct metadata
                metadata = PaperMetadata(
                    doi=paper_dict.get("doi"),
                    title=paper_dict.get("title"),
                    year=paper_dict.get("year"),
                    venue=paper_dict.get("venue"),
                )

                # Calculate new location
                target_dir = catalog_impl.get_target_directory(self.library_root, metadata)
                target_dir.mkdir(parents=True, exist_ok=True)

                target_path = target_dir / paper_dict["current_filename"]

                # Move if different location
                if target_path != current_path:
                    shutil.move(str(current_path), str(target_path))

                    # Update database
                    new_file_path = str(target_path.relative_to(self.library_root))
                    cursor.execute(
                        """
                        UPDATE papers 
                        SET file_path = ?, catalog_method = ?, last_verified_at = ?
                        WHERE id = ?
                        """,
                        (new_file_path, new_method, datetime.now().isoformat(), paper_id),
                    )
                    results["moved"] += 1

            except Exception as e:
                print(f"Error processing paper {paper_id}: {e}")
                results["errors"] += 1
                cursor.execute(
                    "UPDATE papers SET error_message = ? WHERE id = ?",
                    (str(e), paper_id),
                )

        self.db.conn.commit()
        return {
            "success": True,
            "moved_count": results["moved"],
            "skipped_count": results["total"] - results["moved"] - results["not_found"] - results["errors"],
            "missing_files": results["missing_papers"],
            "errors": [] if results["errors"] == 0 else [f"{results['errors']} errors occurred"],
        }

    def _search_for_file(self, paper_dict: Dict[str, Any]) -> Optional[Path]:
        """Search for missing file in library.

        Args:
            paper_dict: Paper record from database

        Returns:
            Found path or None
        """
        # Search by current filename
        current_filename = paper_dict.get("current_filename")
        if current_filename:
            matches = list(self.library_root.rglob(current_filename))
            if matches:
                return matches[0]

        # Search by original filename
        original_filename = paper_dict.get("original_filename")
        if original_filename:
            matches = list(self.library_root.rglob(original_filename))
            if matches:
                return matches[0]

        # Search by DOI in filename (partial match)
        doi = paper_dict.get("doi")
        if doi:
            doi_part = doi.replace("/", "-")[:20]
            for pdf_file in self.library_root.rglob("*.pdf"):
                if doi_part in pdf_file.name:
                    return pdf_file

        return None

"""Database models and initialization for Armarius.

This module defines SQLite tables for paradigms, analyses, and syntheses.
"""

import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime


class ArmariusDatabase:
    """Armarius SQLite database manager."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file.
                    Defaults to ~/.armarius/armarius.db
        """
        if db_path is None:
            db_path = Path.home() / ".armarius" / "armarius.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.initialize_schema()

    def initialize_schema(self):
        """Create tables if they don't exist and run migrations."""
        cursor = self.conn.cursor()

        # Papers table (extended for ingestion workflow)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id TEXT PRIMARY KEY,
            title TEXT,
            authors TEXT,
            year INTEGER,
            venue TEXT,
            venue_rank TEXT,
            doi TEXT UNIQUE,
            file_path TEXT,
            status TEXT DEFAULT 'unread',
            ocr_required INTEGER DEFAULT 0,
            ingested_at TEXT,
            
            -- Ingestion workflow fields (Phase 1)
            original_filename TEXT,
            current_filename TEXT,
            catalog_method TEXT,
            doi_source TEXT,
            ingest_status TEXT DEFAULT 'pending',
            error_message TEXT,
            last_verified_at TEXT
        )
        """)

        # Intake provenance tables (Phase 1A)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_roots (
            id TEXT PRIMARY KEY,
            canonical_doi TEXT,
            canonical_title TEXT,
            canonical_authors TEXT,
            canonical_year INTEGER,
            canonical_venue TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_blobs (
            id TEXT PRIMARY KEY,
            document_root_id TEXT NOT NULL,
            blob_sha256 TEXT NOT NULL,
            text_sha256 TEXT,
            source_filename TEXT NOT NULL,
            managed_filename TEXT NOT NULL,
            managed_path TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            page_count INTEGER,
            is_pdf_valid INTEGER NOT NULL DEFAULT 0,
            ocr_required INTEGER NOT NULL DEFAULT 0,
            ingest_state TEXT NOT NULL,
            ingest_reason TEXT,
            review_note TEXT,
            metadata_confidence_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (document_root_id) REFERENCES document_roots(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transform_runs (
            id TEXT PRIMARY KEY,
            run_type TEXT NOT NULL,
            engine_name TEXT NOT NULL,
            engine_version TEXT NOT NULL,
            rule_version TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            error_message TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS artifacts (
            id TEXT PRIMARY KEY,
            document_blob_id TEXT NOT NULL,
            artifact_type TEXT NOT NULL,
            path TEXT NOT NULL,
            artifact_sha256 TEXT NOT NULL,
            engine_name TEXT NOT NULL,
            engine_version TEXT NOT NULL,
            rule_version TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (document_blob_id) REFERENCES document_blobs(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lineage_edges (
            id TEXT PRIMARY KEY,
            from_kind TEXT NOT NULL,
            from_id TEXT NOT NULL,
            to_kind TEXT NOT NULL,
            to_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        # Paradigms table (NEW)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS paradigms (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL,
            yaml_content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            modified_at TEXT NOT NULL
        )
        """)

        # Analyses table (NEW)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            paper_id TEXT NOT NULL,
            paradigm_id TEXT NOT NULL,
            lens_name TEXT NOT NULL,
            content TEXT NOT NULL,
            word_count INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (paper_id) REFERENCES papers(id),
            FOREIGN KEY (paradigm_id) REFERENCES paradigms(id)
        )
        """)

        # Syntheses table (NEW)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS syntheses (
            id TEXT PRIMARY KEY,
            paradigm_id TEXT NOT NULL,
            concerto TEXT NOT NULL,
            analysis_ids TEXT NOT NULL,
            output_path TEXT NOT NULL,
            word_count INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (paradigm_id) REFERENCES paradigms(id)
        )
        """)

        # Run migrations for existing databases
        self._run_migrations()

        self.conn.commit()

    def _run_migrations(self):
        """Run database migrations for schema changes."""
        cursor = self.conn.cursor()

        # Check if new columns exist, add if missing
        cursor.execute("PRAGMA table_info(papers)")
        columns = {row[1] for row in cursor.fetchall()}

        root_columns = {row[1] for row in cursor.execute("PRAGMA table_info(document_roots)").fetchall()}
        root_migrations = [
            ("canonical_authors", "ALTER TABLE document_roots ADD COLUMN canonical_authors TEXT"),
            ("canonical_year", "ALTER TABLE document_roots ADD COLUMN canonical_year INTEGER"),
            ("canonical_venue", "ALTER TABLE document_roots ADD COLUMN canonical_venue TEXT"),
        ]
        for column_name, sql in root_migrations:
            if column_name not in root_columns:
                try:
                    cursor.execute(sql)
                except Exception as e:
                    print(f"Migration warning: {column_name} - {e}")

        blob_columns = {row[1] for row in cursor.execute("PRAGMA table_info(document_blobs)").fetchall()}
        blob_migrations = [
            ("ingest_reason", "ALTER TABLE document_blobs ADD COLUMN ingest_reason TEXT"),
            ("review_note", "ALTER TABLE document_blobs ADD COLUMN review_note TEXT"),
            ("metadata_confidence_json", "ALTER TABLE document_blobs ADD COLUMN metadata_confidence_json TEXT"),
        ]
        for column_name, sql in blob_migrations:
            if column_name not in blob_columns:
                try:
                    cursor.execute(sql)
                except Exception as e:
                    print(f"Migration warning: {column_name} - {e}")

        migrations = [
            ("original_filename", "ALTER TABLE papers ADD COLUMN original_filename TEXT"),
            ("current_filename", "ALTER TABLE papers ADD COLUMN current_filename TEXT"),
            ("catalog_method", "ALTER TABLE papers ADD COLUMN catalog_method TEXT"),
            ("doi_source", "ALTER TABLE papers ADD COLUMN doi_source TEXT"),
            ("ingest_status", "ALTER TABLE papers ADD COLUMN ingest_status TEXT DEFAULT 'pending'"),
            ("error_message", "ALTER TABLE papers ADD COLUMN error_message TEXT"),
            ("last_verified_at", "ALTER TABLE papers ADD COLUMN last_verified_at TEXT"),
        ]

        for column_name, sql in migrations:
            if column_name not in columns:
                try:
                    cursor.execute(sql)
                except Exception as e:
                    print(f"Migration warning: {column_name} - {e}")

    def save_paradigm(
        self, paradigm_id: str, name: str, paradigm_type: str, yaml_content: str
    ) -> bool:
        """Save or update paradigm to database.

        Args:
            paradigm_id: Unique paradigm identifier
            name: Paradigm name
            paradigm_type: Type (researcher/topic/school)
            yaml_content: Full YAML content

        Returns:
            True if successful
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        try:
            cursor.execute(
                """
            INSERT INTO paradigms (id, name, type, yaml_content, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                type = excluded.type,
                yaml_content = excluded.yaml_content,
                modified_at = excluded.modified_at
            """,
                (paradigm_id, name, paradigm_type, yaml_content, now, now),
            )

            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving paradigm: {e}")
            return False

    def get_paradigm(self, paradigm_id: str) -> Optional[dict]:
        """Get paradigm by ID.

        Args:
            paradigm_id: Paradigm identifier

        Returns:
            Paradigm dict or None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM paradigms WHERE id = ?", (paradigm_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_paradigms(self) -> list[dict]:
        """List all paradigms.

        Returns:
            List of paradigm dicts
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM paradigms ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

    def save_analysis(
        self,
        analysis_id: str,
        paper_id: str,
        paradigm_id: str,
        lens_name: str,
        content: str,
        word_count: int,
    ) -> bool:
        """Save analysis card to database.

        Args:
            analysis_id: Unique analysis identifier
            paper_id: Paper identifier
            paradigm_id: Paradigm identifier
            lens_name: Lens name
            content: Markdown content
            word_count: Word count

        Returns:
            True if successful
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        try:
            cursor.execute(
                """
            INSERT INTO analyses (id, paper_id, paradigm_id, lens_name, content, 
                                word_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (analysis_id, paper_id, paradigm_id, lens_name, content, word_count, now),
            )

            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return False

    def get_analyses_by_paradigm(self, paradigm_id: str) -> list[dict]:
        """Get all analyses for a paradigm.

        Args:
            paradigm_id: Paradigm identifier

        Returns:
            List of analysis dicts
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
        SELECT * FROM analyses 
        WHERE paradigm_id = ? 
        ORDER BY created_at DESC
        """,
            (paradigm_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def save_synthesis(
        self,
        synthesis_id: str,
        paradigm_id: str,
        concerto: str,
        analysis_ids: list[str],
        output_path: str,
        word_count: int,
    ) -> bool:
        """Save synthesis to database.

        Args:
            synthesis_id: Unique synthesis identifier
            paradigm_id: Paradigm identifier
            concerto: Concerto name
            analysis_ids: List of analysis IDs used
            output_path: Output file path
            word_count: Word count

        Returns:
            True if successful
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        import json

        analysis_ids_json = json.dumps(analysis_ids)

        try:
            cursor.execute(
                """
            INSERT INTO syntheses (id, paradigm_id, concerto, analysis_ids, 
                                  output_path, word_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    synthesis_id,
                    paradigm_id,
                    concerto,
                    analysis_ids_json,
                    output_path,
                    word_count,
                    now,
                ),
            )

            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving synthesis: {e}")
            return False

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

"""Intake and normalization services for Armarius."""

import hashlib
import json
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from armarius.database import ArmariusDatabase
from armarius.pdf_processing import PDFProcessor
from armarius.pdf_processing.artifacts import NormalizedArtifacts


@dataclass(slots=True)
class IntakeRecord:
    """Result of one intake operation."""

    document_root_id: str
    document_blob_id: str
    managed_path: Path
    ingest_state: str
    reason: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class IntakeService:
    """Coordinate intake and normalization around the PDF module boundary."""

    def __init__(self, db: ArmariusDatabase, processor: PDFProcessor, library_root: Path) -> None:
        """Initialize the intake service."""
        self.db = db
        self.processor = processor
        self.library_root = library_root

    @staticmethod
    def _derive_processing_stage(blob: Any, artifact_types: set[str]) -> str:
        """Derive a higher-level processing stage for one blob.

        Args:
            blob: Blob row payload.
            artifact_types: Artifact types generated for the blob.

        Returns:
            Queue-friendly processing stage label.
        """
        ingest_state = blob["ingest_state"]
        if ingest_state == "rejected":
            return "rejected"
        if ingest_state == "quarantine":
            return "quarantined"
        if ingest_state == "needs_ocr":
            return "needs_ocr"
        if ingest_state == "accepted" and "markdown" in artifact_types:
            return "ready_for_analysis"
        if ingest_state == "accepted":
            return "accepted_pending_normalize"
        return ingest_state

    def intake_file(self, source_path: Path) -> IntakeRecord:
        """Validate, fingerprint, and register an inbound file."""
        source_path = source_path.expanduser().resolve()
        validation = self.processor.validate_pdf(source_path)
        ingest_state = "accepted" if validation.is_valid else "rejected"
        ingest_reason = validation.reason
        target_dir = self.library_root / "_intake" / ingest_state
        target_dir.mkdir(parents=True, exist_ok=True)
        managed_name = self._sanitize_filename(source_path.name)
        managed_path = self._unique_path(target_dir / managed_name)
        shutil.copy2(source_path, managed_path)

        root_id = str(uuid.uuid4())
        blob_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        blob_sha256 = self._compute_sha256(managed_path)

        metadata = self.processor.extract_metadata(source_path) if validation.is_valid else None
        metadata_confidence = self.processor.extract_metadata_confidence(source_path) if validation.is_valid else None
        if validation.is_valid:
            try:
                preview = self.processor.process_pdf(managed_path)
                if not preview.extracted_text.strip():
                    ingest_state = "needs_ocr"
                    ingest_reason = "no_extractable_text"
                    target_dir = self.library_root / "needs_ocr"
                    target_dir.mkdir(parents=True, exist_ok=True)
                    new_path = self._unique_path(target_dir / managed_path.name)
                    managed_path.rename(new_path)
                    managed_path = new_path
                elif metadata is None or (not metadata.get("title") and not metadata.get("doi")):
                    ingest_state = "quarantine"
                    ingest_reason = "weak_metadata"
                    target_dir = self.library_root / "_intake" / "quarantine"
                    target_dir.mkdir(parents=True, exist_ok=True)
                    new_path = self._unique_path(target_dir / managed_path.name)
                    managed_path.rename(new_path)
                    managed_path = new_path
            except Exception as exc:
                ingest_state = "quarantine"
                ingest_reason = str(exc)
                target_dir = self.library_root / "_intake" / "quarantine"
                target_dir.mkdir(parents=True, exist_ok=True)
                new_path = self._unique_path(target_dir / managed_path.name)
                managed_path.rename(new_path)
                managed_path = new_path
        self.db.conn.execute(
            "INSERT INTO document_roots (id, canonical_doi, canonical_title, canonical_authors, canonical_year, canonical_venue, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                root_id,
                None if metadata is None else metadata.get("doi"),
                source_path.stem if metadata is None else (metadata.get("title") or source_path.stem),
                None if metadata is None else json.dumps(metadata.get("authors") or []),
                None if metadata is None else metadata.get("year"),
                None if metadata is None else metadata.get("venue"),
                ingest_state,
                now,
                now,
            ),
        )
        self.db.conn.execute(
            "INSERT INTO document_blobs (id, document_root_id, blob_sha256, text_sha256, source_filename, managed_filename, managed_path, mime_type, size_bytes, page_count, is_pdf_valid, ocr_required, ingest_state, ingest_reason, review_note, metadata_confidence_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                blob_id,
                root_id,
                blob_sha256,
                None,
                source_path.name,
                managed_path.name,
                str(managed_path),
                validation.detected_mime_type,
                managed_path.stat().st_size,
                validation.page_count,
                1 if validation.is_valid else 0,
                1 if ingest_state == "needs_ocr" else 0,
                ingest_state,
                ingest_reason,
                None,
                None if metadata_confidence is None else json.dumps(metadata_confidence, ensure_ascii=False),
                now,
            ),
        )
        self.db.conn.commit()
        return IntakeRecord(
            document_root_id=root_id,
            document_blob_id=blob_id,
            managed_path=managed_path,
            ingest_state=ingest_state,
            reason=ingest_reason,
            metadata=None if metadata is None else {
                "values": metadata,
                "confidence": metadata_confidence,
            },
        )

    def normalize_blob(self, blob_id: str) -> NormalizedArtifacts:
        """Generate and record normalized artifacts for one accepted blob."""
        blob = self.db.conn.execute(
            "SELECT * FROM document_blobs WHERE id = ?",
            (blob_id,),
        ).fetchone()
        if blob is None:
            raise ValueError(f"Unknown blob id: {blob_id}")
        if blob["ingest_state"] != "accepted":
            raise ValueError(f"Blob {blob_id} is not accepted")

        source_path = Path(blob["managed_path"])
        processing_result = self.processor.process_pdf(source_path)
        run_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        self.db.conn.execute(
            "INSERT INTO transform_runs (id, run_type, engine_name, engine_version, rule_version, status, started_at, finished_at, error_message) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                run_id,
                "normalize",
                self.processor.ENGINE_NAME,
                str(self.processor.ENGINE_VERSION),
                self.processor.RULE_VERSION,
                "completed",
                now,
                now,
                None,
            ),
        )

        blob_dir = self.library_root / "markdown" / "normalized" / blob_id
        blob_dir.mkdir(parents=True, exist_ok=True)
        raw_dir = self.library_root / "markdown" / "source" / blob_id
        raw_dir.mkdir(parents=True, exist_ok=True)
        manifest_dir = self.library_root / "markdown" / "manifests" / blob_id
        manifest_dir.mkdir(parents=True, exist_ok=True)
        table_dir = self.library_root / "artifacts" / "tables" / blob_id
        image_dir = self.library_root / "artifacts" / "images" / blob_id
        table_dir.mkdir(parents=True, exist_ok=True)
        image_dir.mkdir(parents=True, exist_ok=True)

        markdown_path = blob_dir / "document.md"
        raw_text_path = raw_dir / "document.txt"
        manifest_path = manifest_dir / "manifest.json"
        markdown_path.write_text(processing_result.markdown_text, encoding="utf-8")
        raw_text_path.write_text(processing_result.extracted_text, encoding="utf-8")
        root = self.db.conn.execute("SELECT * FROM document_roots WHERE id = ?", (blob["document_root_id"],)).fetchone()
        manifest_payload = {
            "source_path": str(source_path),
            "page_count": processing_result.page_count,
            "metadata": processing_result.metadata,
            "metadata_confidence": processing_result.metadata_confidence,
            "document_root": None if root is None else {
                "canonical_doi": root["canonical_doi"],
                "canonical_title": root["canonical_title"],
                "canonical_authors": root["canonical_authors"],
                "canonical_year": root["canonical_year"],
                "canonical_venue": root["canonical_venue"],
                "status": root["status"],
            },
            "metadata_confidence": None if not blob["metadata_confidence_json"] else json.loads(blob["metadata_confidence_json"]),
            "tables": processing_result.tables,
            "images": processing_result.images,
            "engine_name": self.processor.ENGINE_NAME,
            "engine_version": str(self.processor.ENGINE_VERSION),
            "rule_version": self.processor.RULE_VERSION,
            "transform_run_id": run_id,
        }
        manifest_path.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False), encoding="utf-8")

        table_paths: list[Path] = []
        for table in processing_result.tables:
            table_base = table_dir / f"table-{table['page']}-{table['table_index']}"
            csv_path = table_base.with_suffix(".csv")
            json_path = table_base.with_suffix(".json")
            csv_path.write_text(str(table.get("csv", "")), encoding="utf-8")
            json_payload = {key: value for key, value in table.items() if key != "csv"}
            json_path.write_text(json.dumps(json_payload, indent=2, ensure_ascii=False), encoding="utf-8")
            table_paths.extend([csv_path, json_path])

        image_paths: list[Path] = []
        for image in processing_result.images:
            image_path = image_dir / f"image-{image['page']}-{image['image_index']}.{image['ext']}"
            image_path.write_bytes(image.get("bytes", b""))
            image_paths.append(image_path)

        artifacts = [
            ("markdown", markdown_path),
            ("raw_text", raw_text_path),
            ("manifest", manifest_path),
        ]
        for path in table_paths:
            artifact_type = "table_csv" if path.suffix == ".csv" else "table_json"
            artifacts.append((artifact_type, path))
        for path in image_paths:
            artifacts.append(("image", path))

        for artifact_type, path in artifacts:
            self.db.conn.execute(
                "INSERT INTO artifacts (id, document_blob_id, artifact_type, path, artifact_sha256, engine_name, engine_version, rule_version, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    blob_id,
                    artifact_type,
                    str(path),
                    self._compute_sha256(path),
                    self.processor.ENGINE_NAME,
                    str(self.processor.ENGINE_VERSION),
                    self.processor.RULE_VERSION,
                    now,
                ),
            )
            self.db.conn.execute(
                "INSERT INTO lineage_edges (id, from_kind, from_id, to_kind, to_id, relation_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    "document_blob",
                    blob_id,
                    "artifact",
                    str(path),
                    f"generated_{artifact_type}",
                    now,
                ),
            )

        text_sha256 = self._compute_sha256(raw_text_path)
        self.db.conn.execute(
            "UPDATE document_blobs SET text_sha256 = ? WHERE id = ?",
            (text_sha256, blob_id),
        )
        self.db.conn.commit()

        return NormalizedArtifacts(
            markdown_path=markdown_path,
            raw_text_path=raw_text_path,
            manifest_path=manifest_path,
            table_paths=table_paths,
            image_paths=image_paths,
        )

    def intake_inbox(self) -> list[IntakeRecord]:
        """Process every file in the inbox directory."""
        inbox_dir = self.library_root / "inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)
        results: list[IntakeRecord] = []
        for path in sorted(p for p in inbox_dir.iterdir() if p.is_file()):
            results.append(self.intake_file(path))
        return results

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize a filename for managed storage."""
        safe = (
            filename.replace("/", "_")
            .replace("\\", "_")
            .replace("..", "_")
            .replace(":", "_")
            .replace("?", "_")
            .replace("*", "_")
            .replace("|", "_")
            .replace("<", "_")
            .replace(">", "_")
            .replace('"', "_")
        )
        return safe[:200] if len(safe) > 200 else safe

    @staticmethod
    def _unique_path(path: Path) -> Path:
        """Return a unique path if a collision exists."""
        if not path.exists():
            return path
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        counter = 1
        while True:
            candidate = parent / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    @staticmethod
    def _score_metadata_confidence(confidence: Optional[dict[str, Any]]) -> float:
        """Collapse field-level confidence payloads into one coarse score."""
        if not confidence:
            return 0.0
        scores = []
        for value in confidence.values():
            if isinstance(value, dict) and isinstance(value.get("confidence"), (int, float)):
                scores.append(float(value["confidence"]))
        return sum(scores) / len(scores) if scores else 0.0

    @classmethod
    def _derive_credibility(cls, root: Any, metadata_confidence: Optional[dict[str, Any]], artifact_types: set[str]) -> dict[str, Any]:
        """Return a small credibility summary for current workflow decisions."""
        score = cls._score_metadata_confidence(metadata_confidence)
        reasons = []
        doi = root["canonical_doi"] if root is not None and "canonical_doi" in root.keys() else None
        year = root["canonical_year"] if root is not None and "canonical_year" in root.keys() else None
        venue = root["canonical_venue"] if root is not None and "canonical_venue" in root.keys() else None
        if doi:
            score += 0.2
            reasons.append("has_doi")
        if year:
            score += 0.1
            reasons.append("has_year")
        if venue:
            score += 0.1
            reasons.append("has_venue")
        if "markdown" in artifact_types:
            score += 0.1
            reasons.append("normalized")
        score = min(score, 1.0)
        if score >= 0.75:
            level = "high"
        elif score >= 0.4:
            level = "medium"
        else:
            level = "low"
        return {"level": level, "score": round(score, 3), "reasons": reasons}

    @staticmethod
    def _compute_sha256(path: Path) -> str:
        """Compute SHA256 for a file."""
        digest = hashlib.sha256()
        with path.open("rb") as file_obj:
            for chunk in iter(lambda: file_obj.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()


    def trace_blob(self, blob_id: str) -> dict[str, Any]:
        """Return a provenance-oriented trace payload for one blob."""
        blob = self.db.conn.execute(
            "SELECT * FROM document_blobs WHERE id = ?",
            (blob_id,),
        ).fetchone()
        if blob is None:
            raise ValueError(f"Unknown blob id: {blob_id}")
        root = self.db.conn.execute(
            "SELECT * FROM document_roots WHERE id = ?",
            (blob["document_root_id"],),
        ).fetchone()
        artifacts = self.db.conn.execute(
            "SELECT artifact_type, path, engine_name, engine_version, rule_version, created_at FROM artifacts WHERE document_blob_id = ? ORDER BY created_at",
            (blob_id,),
        ).fetchall()
        artifact_payload = [dict(row) for row in artifacts]
        artifact_types = {artifact["artifact_type"] for artifact in artifact_payload}
        metadata_confidence = None if not blob["metadata_confidence_json"] else json.loads(blob["metadata_confidence_json"])
        credibility = self._derive_credibility(root, metadata_confidence, artifact_types)
        return {
            "blob_id": blob_id,
            "ingest_state": blob["ingest_state"],
            "ingest_reason": blob["ingest_reason"],
            "review_note": blob["review_note"],
            "managed_path": blob["managed_path"],
            "blob_sha256": blob["blob_sha256"],
            "text_sha256": blob["text_sha256"],
            "root": None if root is None else {
                "document_root_id": root["id"],
                "canonical_doi": root["canonical_doi"],
                "canonical_title": root["canonical_title"],
                "canonical_authors": root["canonical_authors"],
                "canonical_year": root["canonical_year"],
                "canonical_venue": root["canonical_venue"],
                "status": root["status"],
            },
            "metadata_confidence": metadata_confidence,
            "credibility": credibility,
            "artifacts": artifact_payload,
        }


    def propose_filename(self, blob_id: str) -> dict[str, Any]:
        """Propose a canonical filename for one blob."""
        blob = self.db.conn.execute(
            "SELECT * FROM document_blobs WHERE id = ?",
            (blob_id,),
        ).fetchone()
        if blob is None:
            raise ValueError(f"Unknown blob id: {blob_id}")
        root = self.db.conn.execute(
            "SELECT * FROM document_roots WHERE id = ?",
            (blob["document_root_id"],),
        ).fetchone()
        if root is None:
            raise ValueError(f"Missing document root for blob: {blob_id}")

        doi = root["canonical_doi"]
        title = root["canonical_title"] or Path(blob["source_filename"]).stem
        authors = json.loads(root["canonical_authors"] or '[]')
        year = root["canonical_year"]

        if doi:
            filename = doi.replace('/', '-') + '.pdf'
            strategy = 'doi'
        else:
            author = authors[0].split(',')[0].strip().lower() if authors else 'unknown'
            title_slug = ''.join(ch.lower() if ch.isalnum() else '_' for ch in title).strip('_')
            title_slug = '_'.join(part for part in title_slug.split('_') if part)[:80]
            year_part = str(year) if year else 'nd'
            filename = f"{year_part}_{author}_{title_slug}.pdf"
            strategy = 'year_author_title'

        filename = filename.replace('..', '_').replace('/', '_')
        return {
            'blob_id': blob_id,
            'strategy': strategy,
            'proposed_filename': filename,
            'managed_path': blob['managed_path'],
        }

    def apply_filename(self, blob_id: str) -> dict[str, Any]:
        """Apply the proposed canonical filename to one managed blob."""
        proposal = self.propose_filename(blob_id)
        blob = self.db.conn.execute(
            "SELECT * FROM document_blobs WHERE id = ?",
            (blob_id,),
        ).fetchone()
        old_path = Path(blob['managed_path'])
        new_path = old_path.with_name(self._sanitize_filename(proposal['proposed_filename']))
        new_path = self._unique_path(new_path)
        old_path.rename(new_path)
        now = datetime.now().isoformat()
        self.db.conn.execute(
            "UPDATE document_blobs SET managed_filename = ?, managed_path = ? WHERE id = ?",
            (new_path.name, str(new_path), blob_id),
        )
        self.db.conn.execute(
            "INSERT INTO lineage_edges (id, from_kind, from_id, to_kind, to_id, relation_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), 'document_blob', blob_id, 'managed_path', str(new_path), 'renamed_to', now),
        )
        self.db.conn.commit()
        return {
            'blob_id': blob_id,
            'old_path': str(old_path),
            'new_path': str(new_path),
            'strategy': proposal['strategy'],
        }

    def list_recent_blobs(
        self,
        limit: int = 20,
        states: Optional[list[str]] = None,
        processing_stages: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """List recent blobs for UI rendering."""
        query = "SELECT b.id, b.source_filename, b.managed_filename, b.ingest_state, b.managed_path, b.created_at, b.metadata_confidence_json, r.canonical_doi, r.canonical_title, r.canonical_year, r.canonical_venue FROM document_blobs b JOIN document_roots r ON r.id = b.document_root_id"
        params: list[Any] = []
        if states:
            placeholders = ", ".join("?" for _ in states)
            query += f" WHERE b.ingest_state IN ({placeholders})"
            params.extend(states)
        query += " ORDER BY b.created_at DESC LIMIT ?"
        params.append(limit)
        rows = self.db.conn.execute(query, tuple(params)).fetchall()
        payload = []
        for row in rows:
            item = dict(row)
            artifact_rows = self.db.conn.execute(
                "SELECT artifact_type FROM artifacts WHERE document_blob_id = ?",
                (row["id"],),
            ).fetchall()
            artifact_types = {artifact_row["artifact_type"] for artifact_row in artifact_rows}
            item["processing_stage"] = self._derive_processing_stage(row, artifact_types)
            metadata_confidence = None if not item.get("metadata_confidence_json") else json.loads(item["metadata_confidence_json"])
            item["credibility"] = self._derive_credibility(row, metadata_confidence, artifact_types)
            payload.append(item)
        if processing_stages:
            allowed = set(processing_stages)
            payload = [row for row in payload if row["processing_stage"] in allowed]
        return payload


    def get_queue_summary(self, stale_after_days: int = 3) -> dict[str, Any]:
        """Return queue-oriented counts for overview and operations views.

        Returns:
            Summary counts grouped by ingest and processing stages.
        """
        rows = self.db.conn.execute("SELECT id, ingest_state FROM document_blobs").fetchall()
        ingest_counts = {
            "accepted": 0,
            "quarantine": 0,
            "needs_ocr": 0,
            "rejected": 0,
        }
        processing_counts = {
            "accepted_pending_normalize": 0,
            "ready_for_analysis": 0,
            "needs_ocr": 0,
            "quarantined": 0,
            "rejected": 0,
            "normalized": 0,
        }
        stale_counts = {
            "total": 0,
            "accepted": 0,
            "quarantine": 0,
            "needs_ocr": 0,
            "rejected": 0,
        }
        credibility_counts = {
            "high": 0,
            "medium": 0,
            "low": 0,
            "unknown": 0,
        }

        for row in rows:
            ingest_state = row["ingest_state"]
            if ingest_state in ingest_counts:
                ingest_counts[ingest_state] += 1
            created_at = datetime.fromisoformat(
                self.db.conn.execute(
                    "SELECT created_at FROM document_blobs WHERE id = ?",
                    (row["id"],),
                ).fetchone()["created_at"]
            )
            if (datetime.now() - created_at).days >= stale_after_days:
                stale_counts["total"] += 1
                if ingest_state in stale_counts:
                    stale_counts[ingest_state] += 1
            artifact_rows = self.db.conn.execute(
                "SELECT artifact_type FROM artifacts WHERE document_blob_id = ?",
                (row["id"],),
            ).fetchall()
            artifact_types = {artifact_row["artifact_type"] for artifact_row in artifact_rows}
            try:
                metadata_row = self.db.conn.execute(
                    "SELECT confidence FROM metadata_candidates WHERE document_blob_id = ? ORDER BY created_at DESC LIMIT 1",
                    (row["id"],),
                ).fetchone()
            except Exception:
                metadata_row = None
            metadata_confidence = float(metadata_row["confidence"]) if metadata_row and metadata_row["confidence"] is not None else None
            credibility = self._derive_credibility(None, metadata_confidence, artifact_types)
            credibility_level = credibility.get("level", "unknown")
            credibility_counts[credibility_level if credibility_level in credibility_counts else "unknown"] += 1
            stage = self._derive_processing_stage(row, artifact_types)
            if stage in processing_counts:
                processing_counts[stage] += 1
            if "markdown" in artifact_types:
                processing_counts["normalized"] += 1

        return {
            "total_blobs": len(rows),
            "ingest": ingest_counts,
            "processing": processing_counts,
            "stale": stale_counts,
            "credibility": credibility_counts,
        }

    def update_ingest_state(self, blob_id: str, new_state: str, review_note: Optional[str] = None, reason: Optional[str] = None) -> dict[str, Any]:
        """Update the ingest state for one blob and move it if needed."""
        allowed_states = {"accepted", "quarantine", "needs_ocr", "rejected"}
        if new_state not in allowed_states:
            raise ValueError(f"Unsupported ingest state: {new_state}")
        blob = self.db.conn.execute(
            "SELECT * FROM document_blobs WHERE id = ?",
            (blob_id,),
        ).fetchone()
        if blob is None:
            raise ValueError(f"Unknown blob id: {blob_id}")

        old_path = Path(blob["managed_path"])
        target_dir_map = {
            "accepted": self.library_root / "_intake" / "accepted",
            "quarantine": self.library_root / "_intake" / "quarantine",
            "rejected": self.library_root / "_intake" / "rejected",
            "needs_ocr": self.library_root / "needs_ocr",
        }
        target_dir = target_dir_map[new_state]
        target_dir.mkdir(parents=True, exist_ok=True)
        new_path = self._unique_path(target_dir / old_path.name)
        if old_path != new_path:
            old_path.rename(new_path)

        now = datetime.now().isoformat()
        self.db.conn.execute(
            "UPDATE document_blobs SET managed_filename = ?, managed_path = ?, ingest_state = ?, ocr_required = ?, ingest_reason = COALESCE(?, ingest_reason), review_note = COALESCE(?, review_note) WHERE id = ?",
            (new_path.name, str(new_path), new_state, 1 if new_state == "needs_ocr" else 0, reason, review_note, blob_id),
        )
        self.db.conn.execute(
            "UPDATE document_roots SET status = ?, updated_at = ? WHERE id = ?",
            (new_state, now, blob["document_root_id"]),
        )
        self.db.conn.execute(
            "INSERT INTO lineage_edges (id, from_kind, from_id, to_kind, to_id, relation_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), 'document_blob', blob_id, 'ingest_state', new_state, 'state_transition', now),
        )
        self.db.conn.commit()
        return {
            'blob_id': blob_id,
            'old_path': str(old_path),
            'new_path': str(new_path),
            'new_state': new_state,
        }

    def batch_normalize(self, blob_ids: list[str]) -> list[NormalizedArtifacts]:
        """Normalize a batch of accepted blobs."""
        artifacts = []
        for blob_id in blob_ids:
            artifacts.append(self.normalize_blob(blob_id))
        return artifacts

    def get_blob_detail(self, blob_id: str) -> dict[str, Any]:
        """Return a detailed record for Web intake review."""
        payload = self.trace_blob(blob_id)
        proposal = self.propose_filename(blob_id)
        artifact_types = {artifact["artifact_type"] for artifact in payload.get("artifacts", [])}
        payload['processing_stage'] = self._derive_processing_stage(payload, artifact_types)
        payload['rename_proposal'] = proposal
        history_rows = self.db.conn.execute(
            "SELECT to_id, relation_type, created_at FROM lineage_edges WHERE from_kind = 'document_blob' AND from_id = ? ORDER BY created_at DESC",
            (blob_id,),
        ).fetchall()
        payload['transition_history'] = [
            {
                'state': row['to_id'],
                'relation_type': row['relation_type'],
                'created_at': row['created_at'],
            }
            for row in history_rows
            if row['relation_type'] == 'state_transition'
        ]
        return payload

    def list_recent_activity(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent blob state transitions for operations review."""
        rows = self.db.conn.execute(
            """
            SELECT le.from_id AS blob_id, le.to_id AS state, le.created_at, db.managed_filename
            FROM lineage_edges le
            JOIN document_blobs db ON db.id = le.from_id
            WHERE le.from_kind = 'document_blob' AND le.relation_type = 'state_transition'
            ORDER BY le.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                'blob_id': row['blob_id'],
                'managed_filename': row['managed_filename'],
                'state': row['state'],
                'created_at': row['created_at'],
            }
            for row in rows
        ]

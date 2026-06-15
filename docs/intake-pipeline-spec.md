# Intake Pipeline Specification

## Purpose

This document defines Armarius Phase 1A: the intake pipeline.

The intake pipeline is the first governance stage in the end-to-end literature workflow:

`Intake → Catalog → Analysis → Synthesis → Citation Governance → Argumentation`

Its job is not merely to "upload PDFs", but to safely receive files, hand them to a dedicated PDF processing module, normalize their content into reusable artifacts, establish document identity, and record provenance so later stages can operate on a trustworthy foundation.

---

## Goals

The intake pipeline must:

1. Accept user-provided files from a controlled inbox.
2. Detect whether a file is truly a PDF regardless of extension.
3. Sanitize unsafe filenames and decouple managed storage paths from user-supplied paths.
4. Generate stable fingerprints for tamper detection and lineage tracking.
5. Extract source text as versioned Markdown as early as possible.
6. Extract tables into machine-readable formats.
7. Extract useful images while filtering icon-like noise.
8. Resolve DOI when possible and generate a canonical naming proposal.
9. Separate accepted, rejected, quarantined, and OCR-required documents.
10. Persist all state transitions and artifacts in the local database.

---

## Non-Goals

The intake pipeline does not directly perform:

- semantic search ranking
- citation graph construction
- unread alert generation
- argument composition
- paradigm-based analysis
- synthesis generation
- final subject/venue/year catalog organization

Those belong to later stages.

---

## User Outcomes

After intake completes, the user should be able to see in the web UI and CLI:

- whether the file was accepted, rejected, quarantined, or marked as OCR-needed
- what canonical filename is proposed
- whether a DOI was detected
- whether text extraction succeeded
- whether tables and images were extracted
- every artifact generated from the original file
- every version of the same logical document across time
- whether the file bytes or extracted text changed

---

## Pipeline Stages

## Stage 1A: Safe Intake

### Inputs

- files dropped into inbox
- files passed via CLI arguments
- files uploaded via web UI

### Required checks

1. **File type validation**
   - do not trust extension alone
   - validate by MIME and/or magic bytes
   - accept extension mismatch if content is valid PDF
   - reject `.pdf` files that are not real PDFs

2. **Path isolation**
   - never trust parent directory names or nested inbound paths
   - move/copy inbound file into Armarius-managed space before further processing
   - preserve original source path only as metadata

3. **Filename sanitization**
   - normalize Unicode
   - remove control characters
   - avoid path traversal sequences
   - slugify or escape unsafe symbols
   - enforce max filename length

4. **Initial fingerprinting**
   - compute byte-level hash
   - store file size and timestamps
   - record intake engine version

5. **Initial state assignment**
   - accepted: valid PDF ready for normalization
   - rejected: invalid file or unrecoverable corruption
   - quarantined: suspicious or partially processable file needing inspection
   - needs_ocr: valid PDF but no reliable extractable text

### Outputs

- managed file in intake storage
- intake record in database
- first lineage link between source and managed blob

---

## Stage 1B: PDF Processing and Normalization

### Purpose

Generate reusable, versioned artifacts from the accepted PDF through a dedicated PDF processing module that may later be extracted into an independent package or service.

### PDF Processing Module Boundary

The system should treat PDF processing as a distinct module with a stable interface.

Responsibilities of the PDF processing module:

- validate real PDF structure
- read page and block content safely
- extract text, tables, and candidate images
- emit versioned artifacts and extraction manifests
- expose engine version and rule version metadata

Responsibilities outside the PDF processing module:

- intake state orchestration
- naming proposal and rename application
- document identity and lineage persistence
- web presentation and CLI ergonomics
- later catalog placement and downstream governance

This separation is intentional so the PDF processing layer can be extracted later with minimal API breakage.

## Required outputs

1. **Raw extraction representation**
   - page/block level extracted text
   - enough structure to support re-rendering and downstream verification

2. **Normalized Markdown**
   - readable by humans
   - versioned by extraction rules and engine version
   - derived only from source document content

3. **Structured tables**
   - save each extracted table as CSV and JSON
   - include extraction metadata such as page number and confidence

4. **Extracted images**
   - preserve original figures when useful
   - skip likely icons, bullets, separators, or low-information noise

5. **Metadata proposal**
   - title, authors, year, venue, DOI
   - indicate source and confidence of each field

6. **Canonical naming proposal**
   - DOI-first when available
   - otherwise follow configured fallback strategy

### Rerun behavior

Normalization must be rerunnable.

A rerun may be triggered by:

- extraction engine upgrade
- Markdown rendering rule update
- table extraction improvement
- image filtering rule change
- metadata resolution improvement
- naming rule update

Reruns must create new artifact versions without losing prior provenance.

---

## Security Model

## Threats to consider

- extension spoofing
- malformed or hostile filenames
- path traversal attempts
- malicious PDF payloads
- prompt injection embedded in PDF content
- unsafe Markdown/HTML rendering downstream

## Required defenses

1. Separate **source content storage** from **LLM-ready sanitized content**.
2. Treat extracted text as untrusted input.
3. Do not embed executable HTML into generated Markdown.
4. Store provenance for every extracted block or artifact where feasible.
5. Record engine version and rule version for reproducibility.
6. Make quarantine a first-class state rather than forcing binary accept/reject.

---

## Naming Strategy

## Priority order

Recommended default naming priority:

1. DOI
2. configured fallback composite
3. content hash

## Fallback composite options

The config should allow ordered fallback templates such as:

- `year_author_title`
- `year_venue_author`
- `author_year_title`
- `content_hash`

## Example config

```toml
[intake.naming]
primary = "doi"
fallback = ["year_author_title", "year_venue_author", "content_hash"]
max_filename_length = 120
slugify = true
```

## Naming principles

- naming must be deterministic for the same metadata set
- naming must be rerunnable when metadata rules change
- naming proposal and naming application should be separate actions
- original filename must always be preserved in provenance records

---

## Storage Layout

Recommended managed layout under the library root:

```text
library/
├── inbox/
├── _intake/
│   ├── accepted/
│   ├── rejected/
│   ├── quarantine/
│   └── manifests/
├── needs_ocr/
├── papers/
├── markdown/
│   ├── source/
│   ├── normalized/
│   └── manifests/
├── artifacts/
│   ├── tables/
│   └── images/
└── synthesis/
```

### Notes

- `inbox/` is the user-facing drop zone
- `_intake/accepted/` holds managed copies before later catalog placement
- `needs_ocr/` holds files that are valid but text-poor
- `papers/` is reserved for later catalog stage output
- Markdown and extracted assets are versioned artifacts, not replacements for the source PDF

---

## Database Requirements

The web UI should not infer state from the filesystem alone. The local database must be the primary status source.

## Core concepts

1. **Document root**
   - logical identity for one paper across versions and file mutations

2. **Document blob**
   - one concrete file version
   - tracks byte-level integrity

3. **Artifact**
   - Markdown, table, image, OCR text, metadata manifest

4. **Transform run**
   - one execution of intake or normalization with engine/rule versions

5. **Lineage edge**
   - explicit relationship between source blob and derived artifacts

## Recommended tables

### `document_roots`
- `id`
- `canonical_doi`
- `canonical_title`
- `status`
- `created_at`
- `updated_at`

### `document_blobs`
- `id`
- `document_root_id`
- `blob_sha256`
- `text_sha256`
- `source_filename`
- `managed_filename`
- `managed_path`
- `mime_type`
- `size_bytes`
- `page_count`
- `is_pdf_valid`
- `ocr_required`
- `ingest_state`
- `created_at`

### `artifacts`
- `id`
- `document_blob_id`
- `artifact_type` (`raw_text`, `markdown`, `table_csv`, `table_json`, `image`, `manifest`)
- `path`
- `artifact_sha256`
- `engine_name`
- `engine_version`
- `rule_version`
- `created_at`

### `transform_runs`
- `id`
- `run_type` (`intake`, `normalize`, `rename_proposal`, `rename_apply`)
- `engine_name`
- `engine_version`
- `rule_version`
- `status`
- `started_at`
- `finished_at`
- `error_message`

### `lineage_edges`
- `id`
- `from_kind`
- `from_id`
- `to_kind`
- `to_id`
- `relation_type`
- `created_at`

## Integrity model

To support tamper detection and document identity, Armarius should track at least:

- `blob_sha256` for exact file integrity
- `text_sha256` for extracted textual identity
- canonical document root identity for cross-version grouping

This allows the system to distinguish:

- same bytes
- different bytes but same text
- same paper across revised file versions
- suspicious mutation after prior ingestion

---

## Web UX Requirements

## Default mode

The intake page must support a one-click default path:

- drop/upload files
- click `Process Intake`
- use safe default settings
- show accepted/rejected/quarantined/OCR-needed outcomes

## Advanced mode

Expandable advanced options may include:

- validate by magic bytes only / MIME + magic bytes
- extract tables on/off
- extract images on/off
- image noise filtering thresholds
- naming strategy selection
- rerun normalization with a new rule version
- whether network DOI lookup is enabled

## Required columns in intake table

- source filename
- detected file type
- intake state
- normalization state
- DOI state
- canonical filename proposal
- blob fingerprint status
- last processed time

---

## CLI Requirements

Every web action in this stage should have a CLI equivalent.

## Commands

```bash
armarius intake run [FILES...]
armarius intake scan-inbox
armarius normalize run <DOC_OR_BLOB_ID>
armarius normalize rerun --all --rule-version <VERSION>
armarius rename propose <DOC_OR_BLOB_ID>
armarius rename apply <DOC_OR_BLOB_ID>
armarius trace show <DOC_OR_BLOB_ID>
```

## Command semantics

- `intake run`: validate, sanitize, fingerprint, and register inbound files
- `intake scan-inbox`: process files already placed into inbox
- `normalize run`: generate Markdown/tables/images for one accepted document
- `normalize rerun`: regenerate artifacts under newer rules
- `rename propose`: compute canonical naming without moving file
- `rename apply`: apply approved canonical naming or managed rename
- `trace show`: display provenance and lineage for one document family

---

## Operational Rules

1. Intake must be idempotent for the same source blob.
2. Reruns must never destroy prior artifacts without explicit pruning.
3. Canonical rename must be reversible through lineage records.
4. Rejected and quarantined files must remain inspectable.
5. Web status must be database-backed, not directory-scan-only.
6. Every artifact must know which blob and transform run produced it.

---

## Module Extraction Requirement

Implementation should assume the PDF processing layer may become an independent module in the future.

Recommended internal boundary for now:

- `armarius/pdf_processing/` for extraction and artifact generation
- service-level callers in intake/normalize orchestration layers
- no direct Streamlit-specific or Click-specific logic inside the PDF processing module

## Open Questions

1. Which PDF extraction engine should be primary for Markdown generation?
2. Should OCR be integrated in this stage or only flagged for later processing?
3. What heuristics best distinguish useful figures from icon noise?
4. When blob hash changes but text hash remains stable, should the UI treat it as a new version or a mutation of the same version?
5. Should note annotations embedded into PDFs create a new document blob automatically?
6. How much page/block provenance should be exposed in the user-facing Markdown?

---

## Proposed Milestone Breakdown

### Milestone A: Safe Intake Foundation
- inbox processing
- PDF validation and filename sanitization
- intake states and managed storage
- initial database records and blob fingerprints

### Milestone B: Normalized Artifact Generation
- raw extraction
- normalized Markdown output
- table extraction to CSV/JSON
- image extraction with noise filtering

### Milestone C: Identity, Naming, and Lineage
- DOI resolution and naming proposal
- rename proposal/apply workflow
- document root vs blob lineage model
- tamper detection and trace view


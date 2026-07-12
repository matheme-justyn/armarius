# Data Model & File Layout

> Status: current local-first data model for `tool-armarius`

This document describes the data model that Armarius actually uses today.

The rule for this version is simple:
- SQLite stores metadata, provenance, and workflow state
- the filesystem stores PDFs and generated artifacts
- Markdown remains the main human-readable output format

## 1. Current Storage Model

Armarius uses a hybrid local storage model:

- **SQLite** for structured records
- **filesystem folders** for managed intake state and source PDFs
- **Markdown / JSON artifacts** for generated outputs and manifests

This is the current shipped model. It is intentionally local-first and does not require a running external database service.

## 2. SQLite Schema (Current Product)

The exact schema lives in code, but the important current product tables are:

### `papers`
Used for paper-level metadata already represented in the local system.

Typical fields include:
- identifier
- title
- authors
- year
- venue
- DOI
- file path
- reading/status metadata

### `document_roots`
Represents the canonical logical document entity when multiple blob/artifact records relate to the same paper lifecycle.

Typical fields include:
- root id
- canonical title / DOI / authors / year / venue
- governance class
- lifecycle stage
- review status
- timestamps

### `document_blobs`
Represents a specific intake-managed PDF blob and its current state.

Typical fields include:
- blob id
- root linkage
- source filename / managed filename
- managed path
- SHA256 hashes
- ingest state
- ingest reason
- review note
- timestamps

This is the most important current workflow table for intake/review/provenance.

### `artifacts`
Represents generated artifacts derived from a blob.

Typical fields include:
- artifact id
- blob linkage
- artifact type
- path
- content / metadata hashes where applicable
- creation metadata

Examples:
- markdown output
- raw text output
- manifest file
- extracted support files

### `lineage_edges`
Represents provenance relationships between roots, blobs, and artifacts.

Typical fields include:
- from kind / id
- to kind / id
- relation type
- created timestamp

This allows trace-style inspection of how a PDF moved through the managed workflow.

### `paradigms`
Stores currently available paradigm definitions that the analysis flow can use.

### `analyses`
Stores generated paradigm-based analysis records.

### `syntheses`
Stores generated synthesis records derived from prior analysis outputs.

## 3. Current Filesystem Layout

The exact folder tree depends on the configured library path, but the current model is conceptually:

```text
<library-root>/
├── _inbox/                 # user drop zone / intake entry point
├── _intake/
│   ├── accepted/
│   ├── quarantine/
│   └── rejected/
├── needs_ocr/
├── papers/
├── markdown/
│   └── papers/
└── synthesis/
```

Additional support/config files may also appear under the library root.

## 4. Current Workflow States

The current intake/review flow revolves around a small set of operational states.

Common current states include:
- `accepted`
- `quarantine`
- `needs_ocr`
- `rejected`

In addition, the document root now carries stable governance metadata so workflow stage is not only inferred from folders:
- `governance_class`
- `lifecycle_stage`
- `review_status`

These states matter because the current web UI and CLI are queue-first:
- Dashboard summarizes state
- Library review works against stateful intake records
- downstream work depends on whether materials are operationally usable

## 5. Artifact Model

For the current product, an accepted PDF may produce one or more derived artifacts.

Current artifact classes include:
- normalized Markdown output
- raw extracted text
- manifest/provenance metadata
- auxiliary extracted resources when available

The important product rule is:
- the original PDF remains local
- derived artifacts are inspectable on disk
- SQLite keeps track of how those artifacts relate to the originating blob

## 6. What This Model Does Not Promise Yet

This document intentionally does **not** treat the following as current baseline data-model requirements:
- a production semantic vector index as part of every normal workflow
- citation graph persistence as a core required user path
- argument-engine session storage as a current flagship feature
- multi-user collaboration records
- hosted service synchronization

Those may appear in older roadmap material, but they are not required to describe the shipped local product.

## 7. Configuration Relationship

The active library root and related local paths come from user configuration.

Important current configuration responsibilities:
- choose the local library root
- choose the database path
- keep web/theme/language preferences local

The current implementation treats those paths as runtime configuration, not fixed global assumptions.

## 8. Source of Truth

When this document and older planning docs disagree, the current product source of truth is:
- the current code in `armarius/database.py`
- the current CLI / web workflow behavior
- the current README / PRD / workflow guide

This file should describe the shipped model, not every future model the project may someday adopt.

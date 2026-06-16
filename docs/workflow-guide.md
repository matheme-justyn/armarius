# Armarius Workflow Guide

## Purpose

This guide explains the full Armarius product workflow as one connected path.
It is the single overview page for how documents move from initial discovery to
analysis, synthesis, and final research output.

For the current installed-app model, Armarius is treated as one active
workspace per installation/runtime context. The UI therefore assumes a single
active library/workspace rather than a multi-library switcher.

The intended end-to-end workflow is:

`Phase 0 / Service Foundation → Intake → Catalog → Analysis → Synthesis → Citation Governance → Argumentation`

---

## How to read this guide

- **Purpose**: why this stage exists
- **Input**: what enters the stage
- **Output**: what should come out of the stage
- **Next handoff**: what the next stage expects
- **Current status**: whether the stage is already implemented, partial, or still planned

---

## 1. Phase 0 / Service Foundation

### Purpose

Establish the minimum working local service so the user can point Armarius at a
PDF library, scan files, and inspect the library through the web UI.

### Input

- A configured active workspace/library
- Local Armarius installation
- User settings such as web port and scan behavior

### Output

- A working local configuration
- A running web service
- A visible PDF library list with search and filter support

### Next handoff

Once the user can see the library and confirm the storage path is correct, the
workflow can move to intake and controlled processing.

### Current status

Implemented. This corresponds to the service foundation delivered in early
milestones and remains the operational base of the app.

---

## 2. Intake

### Purpose

Safely receive files and normalize them into a trustworthy, traceable intake
queue before downstream knowledge work begins.

### Input

- Files dropped into inbox
- Files passed through CLI
- Files uploaded via the web UI

### Output

- Validated PDF state
- Safe managed filenames and storage paths
- Fingerprints and provenance records
- Extracted text and derived artifacts when possible
- Intake states such as accepted, rejected, quarantined, or needs OCR

### Next handoff

Documents that pass intake become ready for review and catalog decisions.

### Current status

Implemented in the current product direction, with queue-based review and
normalization as the main operational flow.

---

## 3. Catalog

### Purpose

Assign stable document identity, fill core metadata, and organize accepted
papers into the managed library structure.

### Input

- Intake-approved documents
- Extracted metadata from PDF text
- DOI, title, author, venue, and year candidates
- Optional online enrichment results

### Output

- Canonical naming proposal or applied filename
- Structured metadata stored in the local database
- Managed library placement based on catalog method
- Consistent identity for later retrieval and analysis

### Next handoff

Cataloged papers become reliable units for analysis and synthesis workflows.

### Current status

Implemented in large part. Metadata extraction, DOI lookup, file naming, and
multiple catalog organization methods already exist, though the user-facing
documentation for this stage is still lighter than intake.

---

## 4. Analysis

### Purpose

Produce structured understanding of individual papers from one or more analytic
perspectives.

### Input

- Cataloged papers ready for downstream work
- Selected paradigms, lenses, or review perspectives
- User choices for what kind of analysis to generate

### Output

- Analysis cards or structured per-paper insights
- Intermediate artifacts that can be reused during synthesis
- A clearer view of methodology, claims, strengths, and gaps

### Next handoff

Analysis results become the raw material for cross-paper synthesis.

### Current status

Partially implemented. The product already has Paradigm Analysis UI and related
workflow structure, but the broader long-term analysis vision is not fully
complete.

---

## 5. Synthesis

### Purpose

Combine multiple analysis outputs into comparative, thematic, or narrative
research summaries.

### Input

- Analysis cards
- Selected paper sets
- User synthesis goals or framing questions

### Output

- Synthesis documents or structured review outputs
- Cross-paper comparisons
- Consolidated research understanding suitable for writing or further reasoning

### Next handoff

Synthesis can feed citation governance checks and eventually argumentation.

### Current status

Partially implemented. The Concerto Synthesis workflow exists in the web UI,
but the full roadmap for advanced review generation is still ahead.

---

## 6. Citation Governance

### Purpose

Ensure the library is not just processed, but also citation-aware and
operationally trustworthy for research work.

### Input

- Processed papers and their references
- Library inventory and metadata state
- Potential citation relationships across the collection

### Output

- Citation scan results
- Missing-paper alerts or unread alerts
- Citation graph inputs and governance signals

### Next handoff

Citation-aware context improves the quality and traceability of final argument
generation.

### Current status

Mostly planned. This is part of the intended workflow, but core pieces such as
citation scan and graph-oriented views are still deferred.

---

## 7. Argumentation

### Purpose

Turn the managed knowledge base into usable research output: claims, arguments,
or structured literature-review text with evidence traceability.

### Input

- User topic or thesis statement
- Retrieved chunks, notes, and synthesized material
- Evidence ranking or quality signals

### Output

- Structured argument blocks
- Claim-to-source mapping
- Citation-aware prose, outline, or bullet output

### Next handoff

This is the final output-facing stage for human writing, review, and reuse.

### Current status

Designed in the PRD, but not yet fully implemented as an end-user workflow.

---

## Current app workflow mapping

The current web UI does not expose every long-term stage as a complete
production-ready page yet. Right now the visible workflow is best understood as:

1. **Overview** — see setup and current workflow state
2. **Check library** — confirm the configured library and scan state
3. **Process inbox** — import and normalize new PDFs
4. **Review intake** — inspect states, rename proposals, and retries
5. **Paradigm analysis** — generate analysis outputs
6. **Concerto synthesis** — generate synthesis outputs

This means the present UI covers the service foundation, intake, part of
cataloging, and part of the analysis/synthesis flow. Citation governance and
argumentation remain roadmap stages.

---

## Status summary

| Stage | Current status |
|------|----------------|
| Phase 0 / Service Foundation | Implemented |
| Intake | Implemented |
| Catalog | Mostly implemented |
| Analysis | Partially implemented |
| Synthesis | Partially implemented |
| Citation Governance | Planned |
| Argumentation | Planned |

---

## Source documents

This guide is aligned with the following source documents:

- `docs/phase-0-service-foundation.md`
- `docs/intake-pipeline-spec.md`
- `docs/PRD.md`
- `docs/merge-roadmap/README.md`

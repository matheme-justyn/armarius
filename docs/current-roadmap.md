# Current Roadmap

## Scope boundaries

- **Core now**: local workspace flow for intake, review, analysis, and synthesis
- **Experimental**: search, agents, MCP, and eval tooling
- **Legacy reference**: older merge-roadmap and speculative design documents

> Status: active roadmap for the shipped `tool-armarius` product line

This file exists to answer one question only:

**What is actually left to build next, after the current local-first workflow has already shipped?**

It intentionally avoids repeating older broad design docs.

## Already Done

These are already real parts of the current product:
- local config and CLI setup
- Streamlit web workspace
- queue-first Dashboard / Library / Analysis / Synthesis / Guide flow
- intake/provenance/review foundation
- SQLite-backed local metadata/provenance model
- current Paradigm / Concerto workflow
- local/offline-capable testable baseline
- core docs aligned to shipped behavior

## Not Done Yet

Only keep features here if they are both:
- not fully shipped today
- still worth building in the near-to-medium term

### 1. Credibility Scoring
What it means:
- score or classify source credibility beyond raw metadata
- surface credibility in a way that helps review and downstream analysis

Why it is still missing:
- current workflow can ingest and analyze, but it does not yet provide a clear credibility layer the user can trust

### 2. Reader Personas / Multi-Perspective Review
What it means:
- generate or structure multiple review perspectives over the same source set
- make those perspectives explicit rather than hidden in one generic output

Why it is still missing:
- current Paradigm flow covers analysis direction, but not a dedicated persona-style review layer

### 3. Literature-Review Generation
What it means:
- generate reusable review-style output across multiple papers
- sit on top of existing intake + analysis outputs

Why it is still missing:
- current synthesis flow exists, but it is not yet a dedicated literature-review product surface

### 4. Optional Better Markdown Conversion
What it means:
- optionally support a richer conversion path for difficult PDFs
- remain optional, not required for baseline usage

Why it is still missing:
- current normalization path works, but some richer extraction ideas remain deferred

## Explicit Non-Goals For Now

These are not the next step unless product direction deliberately changes:
- React rewrite
- FastAPI-first architecture
- hosted multi-user mode
- mandatory vector/retrieval stack for normal operation
- argument engine as a current flagship workflow
- citation graph as a required current core surface

## Prioritization Rule

Build in this order:
1. features that strengthen the current shipped workflow
2. features that reuse current intake/provenance/analysis outputs
3. optional upgrades that stay local-first

Do not build in this order:
1. architecture rewrites first
2. broad platformization first
3. roadmap vanity features before workflow utility

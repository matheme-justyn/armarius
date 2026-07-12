# Armarius Product Requirements Document

> Status: active pre-release product document  
> Scope: current `tool-armarius` deliverable, with explicit notes on deferred work

## 1. Product Positioning

Armarius is a local-first academic knowledge workspace for turning a PDF library into a usable research flow.

The current product is **not** trying to deliver every long-term roadmap idea at once. This version focuses on a practical loop:

1. bring PDFs into a managed intake flow
2. inspect and review source material
3. generate paradigm-based analysis outputs
4. turn those outputs into audience-shaped or project-oriented synthesis drafts

All core data remains local and open-format. The current product combines:
- Python CLI
- Streamlit web UI
- SQLite metadata/provenance storage
- Markdown-based output artifacts

## 2. Product Goals

### Current goals

- make local PDF intake and review operationally reliable
- provide a clear queue-first workflow in the web UI
- support Paradigm Analysis and Concerto Synthesis as the current research workspace flow
- keep outputs inspectable in Markdown and metadata traceable in SQLite
- make the current system usable without requiring external services at runtime

### Non-goals for this version

The current release does **not** promise:
- browser-based PDF upload as the primary workflow
- production-ready citation graph visualization
- evidence-weighted Argue Engine
- full semantic retrieval stack as a required dependency
- React/FastAPI frontend architecture
- multi-user collaboration features

Those remain roadmap items, not current deliverables.

## 3. Target Users

### Primary user
- a researcher working locally with a personal PDF library
- comfortable with CLI plus a lightweight local web UI
- wants structure, traceability, and reusable outputs rather than a black-box summarizer

### Secondary user
- a developer or advanced user extending the workflow, paradigms, or synthesis templates
- needs open formats and predictable local behavior

## 4. Current Core Workflow

### Step 1: Dashboard
Purpose:
- show the workspace state
- surface queue counts and next actions
- orient the user before operating on materials

Current capabilities:
- high-level queue/state overview
- recommended next actions
- navigation into Library / Analysis / Synthesis

### Step 2: Library
Purpose:
- act as the source-material workspace
- handle intake, review, normalization visibility, and collection inspection

Current capabilities:
- scan configured library
- inspect source PDFs and basic metadata
- run intake flow from CLI and review resulting states in web UI
- inspect intake states such as accepted, quarantine, and needs OCR
- review provenance / rename / normalization-related outputs
- access cataloging helper content

### Step 3: Analysis
Purpose:
- generate paradigm-based reading outputs from prepared materials

Current capabilities:
- choose one or more paradigms
- point at a paper folder
- start analysis-card generation flow
- use the page as a dedicated analysis workspace rather than a bare form

### Step 4: Synthesis
Purpose:
- reshape analysis outputs into more usable drafts for a target audience or output style

Current capabilities:
- choose synthesis framing from the current Concerto workflow
- generate audience-shaped draft outputs from existing analysis artifacts

### Step 5: Guide / Tutorial
Purpose:
- explain what Armarius currently is
- map each page to its role in the real workflow
- separate current capability from deferred roadmap

Current capabilities:
- single-page workflow explanation
- companion summary of current page roles
- alignment with current sidebar/workflow structure

## 5. Functional Requirements

### 5.1 Configuration and local setup
The product must:
- initialize a local config file
- allow setting a library root path
- allow setting web port and theme/language preferences
- keep configuration local to the machine

### 5.2 Intake and provenance
The product must:
- intake PDF files into managed library states
- preserve provenance and traceability through SQLite-backed records
- support review-state updates such as accepted, quarantine, needs_ocr, and rejected
- support deterministic rename proposal/apply workflow
- produce normalization artifacts for accepted items where applicable

### 5.3 Library inspection
The product must:
- scan PDFs from the configured library
- show basic readability, file size, page count, and modified time information
- support queue-oriented inspection in the web UI
- help users decide what to do next in the intake/review flow

### 5.4 Analysis workflow
The product must:
- list available paradigms
- accept a paper folder plus selected paradigms
- trigger current analysis generation flow
- present analysis as a dedicated workspace in the UI

### 5.5 Synthesis workflow
The product must:
- expose the current synthesis flow as a dedicated workspace
- frame synthesis as output shaping, not a duplicate of analysis
- guide the user toward transforming prior analysis outputs into drafts

### 5.6 Documentation consistency
The product must:
- keep README, PRD, workflow guide, and sidebar spec aligned with current deliverable scope
- clearly distinguish implemented behavior from roadmap items

## 6. Quality Requirements

The current product should be:
- local-first
- testable without mandatory network access
- explicit about queue state and provenance
- usable through both CLI and Streamlit UI
- conservative about claiming unfinished features

## 7. Current Architecture Boundaries

### Included now
- Python package
- Click CLI
- Streamlit web UI
- SQLite metadata/provenance store
- Markdown output artifacts
- local PDF processing
- queue-first intake and review flow
- current Paradigm / Concerto workflow

### Deferred
- React/FastAPI production web stack
- citation graph UI as a core deliverable
- full semantic search as a required user path
- argument engine as a current user-facing feature
- multi-user / hosted collaboration

## 8. Milestone Interpretation

The repository still contains historical milestone language from broader design work. For the current product narrative, interpret milestones this way:

- completed: service foundation, intake/provenance foundation, current Streamlit workflow, current Paradigm/Concerto pages
- partial: some broader research-workspace ambitions are visible in docs and structure, but not fully productized
- deferred: semantic retrieval-heavy features, citation graph productization, argument engine, and frontend rewrite

## 9. Definition of Done for the Current Product Line

A change is considered aligned with the current Armarius product if it:
- improves the current local research workspace flow
- preserves local/open-format operation
- keeps README/PRD/UI/docs consistent
- passes local tests without depending on network-only model downloads
- does not present roadmap-only features as already usable

## 10. Immediate Roadmap

Near-term work that still fits the current product direction:
- continue tightening Dashboard / Library / Analysis / Synthesis clarity
- keep intake/review/provenance reliable
- improve cataloging help and workflow guidance
- refine current analysis/synthesis ergonomics
- reduce documentation drift across README, PRD, and technical docs

Longer-term but explicitly deferred work:
- richer retrieval stack
- citation graph visualization
- argument engine
- larger frontend rewrite

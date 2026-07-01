# Armarius Technology Stack

> Status: current implementation stack for `tool-armarius`  
> Purpose: describe what the product actually runs on today, and clearly mark deferred architecture

## 1. Stack Summary

Armarius currently ships as a **local Python application** with two main surfaces:
- a Click-based CLI
- a Streamlit-based web UI

Its current persistence and artifact model is:
- SQLite for metadata and provenance
- Markdown plus related files for generated artifacts
- local filesystem directories for managed intake and library state

This is the stack the product actually depends on today.

## 2. Current Runtime Stack

| Layer | Current choice | Why it exists now |
|------|----------------|-------------------|
| Application runtime | Python | Single-language local toolchain, strong PDF/data tooling |
| CLI | Click | Simple, stable command structure for init/serve/intake/review flows |
| Web UI | Streamlit | Fast local research workspace without building a separate frontend stack |
| Config | YAML + TOML | YAML for user config, TOML for project/web-related config patterns |
| Database | SQLite | Local-first persistence and provenance without a server dependency |
| Artifact format | Markdown + JSON + local files | Inspectable outputs, easy editor integration, portable storage |
| PDF processing | PyMuPDF (`fitz`) | Current PDF readability checks and processing pipeline |
| Tabular/UI support | pandas | Practical display and transformation support in Streamlit pages |
| Testing | pytest | Lightweight regression coverage across CLI, intake, UI helpers, storage |

## 3. Current Product Surfaces

### CLI
The CLI is the primary control surface for:
- initialization
- serving the local web UI
- intake commands
- trace/review/rename workflows
- developer-oriented local operation

### Streamlit Web UI
The Streamlit app is the current local workspace for:
- dashboard orientation
- library inspection and queue review
- analysis and synthesis task flow
- workflow explanation and settings

This is a deliberate current choice, not a placeholder that users should mentally replace with React right now.

## 4. Data and Storage Model

### SQLite
SQLite is the current source of truth for:
- intake/provenance records
- review state tracking
- normalization lineage
- analysis/synthesis metadata where applicable

Why SQLite now:
- zero external service requirement
- simple local portability
- easy test setup
- good fit for single-user/local-first workflow

### Filesystem-managed artifacts
The filesystem stores:
- source PDFs
- intake state folders
- markdown outputs
- manifests and related normalization artifacts

Why local files now:
- human-inspectable outputs
- editor-friendly workflow
- easy backup/versioning outside the app

## 5. Analysis and Synthesis Stack

The current analysis/synthesis layer is configuration-driven and local.

It currently depends on:
- paradigm definitions and loaders
- current Concerto synthesis flow
- local output generation patterns

It does **not** currently require a production semantic retrieval stack in order to be useful.

## 6. Testing and Offline Reliability

The current codebase is expected to be testable in a restricted local environment.

That means:
- unit/integration tests should not require a live network dependency by default
- local test runs should not fail just because a remote model cannot be downloaded
- fallback behavior is acceptable where it preserves deterministic local testability

This is why the current embedding layer supports an offline deterministic fallback for no-network test runs.

## 7. What Is Deferred, Not Current Stack

The repository still contains older or broader design discussions referencing technologies that are **not** the current required stack for this product line.

These are deferred / roadmap items, not current baseline dependencies:
- FastAPI as the main current web application runtime
- React as the current frontend
- WebSocket-heavy realtime architecture
- ChromaDB/Qdrant as a required end-user dependency for core workflow
- LlamaIndex/LiteLLM as a required current user path
- Cytoscape.js citation graph UI as a current deliverable
- Redis/Celery/server-side job infrastructure

Those may appear in historical planning documents, but they do not define what the shipped local tool currently needs.

## 8. Why the Current Stack Is Intentionally Small

The current stack is optimized for:
- local-first operation
- fewer moving parts
- easier debugging
- lower setup cost
- more reliable tests
- clearer alignment between product promise and shipped code

In practice, a smaller current stack is better than a larger aspirational stack that the product does not yet truly deliver.

## 9. Developer Workflow

The typical current developer loop is:

```bash
uv tool install --editable '.[web]'
armarius init
armarius serve
```

For development and testing:

```bash
uv sync --extra dev --extra web
UV_CACHE_DIR=.uv-cache uv run python -m pytest -q
```

## 10. Stack Boundaries for Future Work

Future work should preserve the current product contract unless the product direction is intentionally expanded.

Safe near-term changes:
- improving Streamlit workflow clarity
- improving CLI/review/provenance reliability
- refining docs and local ergonomics
- strengthening local test coverage

Changes that should be treated as explicit roadmap expansions:
- replacing Streamlit with a new frontend stack
- requiring hosted/vector/LLM services for baseline usage
- introducing a citation graph product surface as a core promise
- promoting argument generation to a current flagship feature

## 11. Source of Truth

For the current product story, treat these as the primary alignment documents:
- `README.md`
- `docs/PRD.md`
- `docs/workflow-guide.md`
- `docs/web-sidebar-spec.md`

If older technical or roadmap docs disagree with the current shipped behavior, the current shipped behavior wins until the product is intentionally expanded.

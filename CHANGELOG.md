# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Added step-purpose descriptions across each primary page so the UI explains what each step is for and stays aligned with the current implementation
- Reframed the Streamlit app as a research workspace with clearer Dashboard, Library, Analysis, Synthesis, and Guide roles
- Upgraded Analysis and Synthesis pages from bare forms into task-oriented workspaces with purpose and output framing
- Updated workflow and sidebar documentation to match the real Armarius product story and UIUX structure
- Updated `README.md` so usage guidance no longer promises browser upload, citation graph exploration, or Argue Engine flows that are not part of the current deliverable
- Rewrote `docs/PRD.md` and `docs/technology-stack.md` so product scope, shipped architecture, and deferred roadmap now match the current README and Streamlit-first deliverable.
- Rewrote `docs/data-model.md` and `docs/phase-0-technical-decisions.md` so storage/runtime decisions now describe the current local-first product instead of older aspirational architecture.
- Fixed `armarius/ui_common.py` theme application so light/dark rendering does not rely on undefined style variables


### Added
- Queue-oriented intake projection in `IntakeService`, including higher-level
  processing stages such as `accepted_pending_normalize` and
  `ready_for_analysis`.
- Dashboard operations overview with queue counts, recommended next actions,
  and stale-item visibility.
- Library intake queue presets for `Needs review`, `Needs OCR`, and
  `Ready for analysis`.
- Standalone workflow guide in `docs/workflow-guide.md`, now surfaced directly
  inside the web Tutorial page as the single-page explanation of the end-to-end
  Armarius workflow.

### Changed
- Shifted the web UI toward a queue-first operating model: Dashboard is now an
  overview surface, while Library remains the main execution workspace.
- Guide/Tutorial content now aligns with legacy design docs, current workflow,
  and recent updates.
- Trimmed the old inline Guide summary so it now acts as companion notes to the
  standalone workflow guide instead of duplicating the full workflow narrative.
- Simplified the main sidebar information architecture: workflow navigation and
  page navigation stay in the sidebar, while library/config editing moves to a
  dedicated Settings page.
- Further simplified the installed-app model by removing library switching from
  user-facing settings and keeping the active workspace read-only in the UI.

### Added
- **Intake pipeline foundation**: Added a dedicated `armarius/pdf_processing/` module boundary, intake orchestration service, provenance-oriented database tables, and new CLI commands for `intake`, `normalize`, and `trace`.
- **Versioned normalization artifacts**: Accepted PDFs can now generate Markdown, raw text, and manifest artifacts under managed library paths with transform and lineage records.

## [0.8.0] - 2026-06-15


## [0.7.1] - 2026-06-15

### Changed
- **Web launch defaults**: `armarius init` no longer implies that users should
  disable browser opening. `armarius serve` now respects
  `web.auto_open_browser` and opens the local web UI automatically by default.
- **Quick start guidance**: Updated `docs/phase-0-quickstart.md` to document
  the default browser-opening behavior instead of recommending `--no-browser`.

### Fixed
- **Long `armarius scan` feedback gap**: The CLI now prints a discovery message
  and per-file progress updates while validating PDFs, so large libraries no
  longer look frozen during scanning.

## [0.6.1] - 2026-06-14

### Fixed
- **`[evals]` install reproducibility**: Pinned the langchain family
  (`langchain`/`langchain-community`/`langchain-core` to `<0.3`,
  `langchain-openai` to `<0.2`) in the `evals` extra. ragas 0.4.3 hard-imports
  `langchain_community.chat_models.vertexai`, which was removed in
  langchain-community 0.4.x, so an unpinned install pulled langchain 1.x and
  `import ragas` failed. Re-locked `uv.lock` accordingly.

## [0.6.0] - 2026-06-14

### Added
- **Evaluation Suite (merged & cleaned from Capsa)**: New repo-root `evals/`
  directory targeting the merged agent/storage/MCP stack:
  - **RAGAS** — RAG quality (faithfulness, answer relevance) for QueryAgent /
    SummarizeAgent
  - **DeepEval** — agent-workflow correctness for the Orchestrator
  - **Promptfoo + Prompt-Guard/Presidio** — security testing (prompt injection,
    PII leakage) for the MCP server and CLI
  - Golden dataset, central `config.yaml`, and a combined report generator
- **`armarius.client.ArmariusClient`**: thin in-process API (`index()`/`query()`)
  over the storage + search stack, for scripts and evaluations.
- Optional `[evals]` dependency group (ragas, deepeval, datasets, presidio).
  Promptfoo is a separate Node.js tool.

### Changed
- Cleaned up the ported eval scripts: imports rewritten `capsa.*` → `armarius.*`;
  fixed the two security scripts that imported a non-existent `CapCLI` (now use
  `ArmariusClient`).

### Removed
- Stale `pdf/capsa/` duplicate (a pre-move copy referencing the old user path).

> Note: the eval scripts are ported but **not yet executed end-to-end** (running
> them requires LLM API keys and the `[evals]` deps); they are verified only at
> the import/compile level.

## [0.5.2] - 2026-06-14

### Fixed
- **`tests/test_quick_buttons.py` missing `import pytest`**: The
  `TestErrorHandling.test_permission_denied_handling` test called
  `pytest.skip(...)` but `pytest` was never imported (the import was commented
  out). On macOS, where `/root` does not exist, this raised
  `NameError: name 'pytest' is not defined` and failed the test. Replaced the
  commented-out import with a real `import pytest`.

## [0.5.1] - 2026-06-14

### Changed
- **Purge residual Cardex naming**: Renamed all remaining `Cardex`/`cardex`
  references to Armarius now that the package is `armarius`:
  - Config dir unified to `~/.armarius` (was inconsistent: `config.py` already
    used `.armarius` while `database.py`/`paradigm.py`/i18n still used `.cardex`)
  - Classes `CardexConfig` → `ArmariusConfig`, `CardexDatabase` → `ArmariusDatabase`
  - Database file `cardex.db` → `armarius.db`; workflow config
    `_cardex-config.toml` → `_armarius-config.toml`
  - Env vars `CARDEX_*` → `ARMARIUS_*` (code, Containerfile, docker-compose, podman.sh)
  - README "About the Name" rewritten with the correct Armarius etymology
    (the medieval monastic keeper of the *armarium*)
  - Regenerated `uv.lock` with the `armarius` package name
  - Removed local `cardex.egg-info` and `tmp/cardex-*` artifacts

## [0.5.0] - 2026-06-14

### Added
- **Contribution Workflow**: Documented the mandatory GitHub flow in
  [AGENTS.md](./AGENTS.md) — every change goes through an issue, a dedicated
  branch, an Angular-style PR, and is merged into `main` (no direct commits to
  `main`). AI agents must follow this flow.
- **Capsa Merge — Semantic Search & Multi-Agent Stack**: Integrated the Capsa
  project into Armarius as the core, adding net-new capabilities as subpackages
  of the `armarius` package (no changes to the existing SQLite metadata DB,
  Streamlit UI, or cataloging — hybrid architecture: SQLite for metadata +
  Qdrant for vectors):
  - `armarius/parser/` — PyMuPDF PDF parsing with bounding boxes and 3 chunking
    strategies (block / sentence / fixed), plus screenshot generation
  - `armarius/storage/` — `Embedder` (sentence-transformers), `VectorStore`
    (Qdrant local mode), `DocumentIndexer`, and `SemanticSearch`
  - `armarius/agents/` — multi-agent framework: `QueryAgent`, `CompareAgent`,
    `SummarizeAgent`, `CitationAgent`, and `Orchestrator`
  - `armarius/mcp/` — MCP server (`armarius-mcp`) exposing index/search/cite/
    compare/summarize tools for Claude Desktop
  - New CLI commands: `armarius index`, `armarius query`, `armarius index-status`
    (heavy deps lazy-imported so `--help` stays fast)
  - New dependencies: qdrant-client, sentence-transformers, pydantic,
    pydantic-settings, rich, tqdm; optional `[mcp]` extra
  - Storage paths/names aligned to `~/.armarius/` (was `~/.capsa/`)
  - Ported Capsa's test suite (33 passing, 6 skipped requiring real PDFs)
  - Carried Capsa's design docs into `docs/merge-roadmap/` as the forward roadmap
    (credibility scoring, reader personas, literature-review generation — design
    only, not yet implemented)

### Changed
- **Scaffolding Update**: Upgraded from my-vibe-scaffolding v1.10.0 to v1.13.0
  - Added OpenCode project-isolated database configuration (`.vscode/settings.json`)
  - Added Skills system documentation (SKILL_FORMAT_GUIDE, AGENTS_MD_GUIDE, SKILLS_USAGE_GUIDE)
  - Added bundles.yaml and workflows.yaml for task-based skill loading
  - Added ADR 0007: Agent Skills Ecosystem Integration
  - Updated AGENTS.md with "Default Skills for This Project" section
  - Benefits: Avoid multi-project database conflicts, better AI development workflow

## [0.4.0] - 2026-03-10

### Added
- **Complete Cataloging System** (M2 Milestone):
  - DOI-based file naming with intelligent fallback strategies
  - Metadata extraction from PDFs (title, authors, DOI, year)
  - Online DOI lookup via Crossref and Semantic Scholar APIs
  - Four catalog methods: flat, by_year, by_venue, custom categories
  - Re-cataloging system for switching organization methods
  - SQLite tracking with 7 new columns (original_filename, current_filename, catalog_method, doi_source, ingest_status, error_message, last_verified_at)
  - "目錄室" (Catalog Room) UI in Library tab with file browser and cataloging controls
  - "編目助手" (Catalog Assistant) as independent top-level tab with comprehensive tutorial

- **New Modules**:
  - `armarius/catalog_loader.py` (192 lines) - YAML-based catalog configuration loader
  - `armarius/catalog_room.py` (285 lines) - Catalog room UI with file browser
  - `armarius/catalog_assistant.py` (278 lines) - Educational catalog configuration guide
  - `armarius/cataloging.py` (434 lines) - Core cataloging logic and workflows
  - `armarius/metadata_extractor.py` (304 lines) - PDF metadata extraction
  - `armarius/doi_resolver.py` (374 lines) - External DOI lookup via APIs
  - `armarius/naming_strategy.py` (281 lines) - Filename generation from DOI/title
  - `armarius/ui_common.py` - Shared UI components and i18n helper

- **Configuration Templates**:
  - `catalogs/example.catalog.yaml` (141 lines) - Comprehensive catalog template
  - `catalogs/flat.catalog.yaml` (39 lines) - Flat directory structure
  - `catalogs/by_year.catalog.yaml` (39 lines) - Year-based organization
  - `catalogs/by_venue.catalog.yaml` (39 lines) - Venue-based organization
  - User configs in `~/.armarius/catalogs/` (Git-ignored)

- **i18n Enhancements**:
  - Added `[catalog_room]` section to app.toml (zh-TW and en-US)
  - Removed ALL hardcoded bilingual text patterns
  - Full translation coverage for catalog system UI

### Fixed
- **Critical Bug**: Variable name collision in `armarius/app.py` (line 592-596)
  - Changed `status` to `pdf_status` to prevent overwriting workflow status enum
  - Fixed catalog room not displaying due to incorrect status type check

### Changed
- **Architecture Refactoring**:
  - Moved Catalog Assistant from Library expander to independent Tab 3
  - Converted Catalog Assistant to pure tutorial/configuration guide
  - Integrated Catalog Room into Library tab as "目錄室" expander
  - Database schema extended with 7 new columns in papers table
- Updated `.gitignore` to exclude `~/.armarius/catalogs/`
- Updated version badges to 0.4.0

### Removed
- `armarius/pages/` directory (intentional single-page architecture)
  - Deleted `1_🎼_Paradigm_Analysis.py` (moved to main app)
  - Deleted `2_🎭_Concerto_Synthesis.py` (moved to main app)

## [0.3.0] - 2026-03-06

### Added
- **Paradigm System GUI**:
  - New two-page Streamlit interface for paradigm-driven analysis
  - Page 1: Paradigm Analysis - Select paradigm + papers → Generate analysis cards
  - Page 2: Concerto Synthesis - Select concerto + cards → Generate synthesis document
  - Paradigm and Concerto configuration file loaders (YAML-based)
  - Database schema for paradigms, analyses, and syntheses
  - Complete i18n support (zh-TW and en-US) for new pages
  - Example paradigm and concerto files in `~/.armarius/`

- **New Modules**:
  - `armarius/database.py` - SQLite database manager with paradigm/analysis tables
  - `armarius/paradigm.py` - Paradigm and Concerto configuration loaders
  - `armarius/pages/1_🎼_Paradigm_Analysis.py` - Paradigm analysis page
  - `armarius/pages/2_🎭_Concerto_Synthesis.py` - Concerto synthesis page

- **Documentation**:
  - Comprehensive GUI specification document (`docs/gui-paradigm-specification.md`)
  - Updated PRD with paradigm system workflows
  - 816-line detailed UI specification with component specs

### Changed
- Streamlit app now supports multipage architecture
- Updated README badges to version 0.3.0


## [0.2.0] - 2026-03-06

### Added
- **Version Display Improvements**:
  - Display Armarius software version at the bottom of sidebar (📦 Armarius 版本: v0.2.0)
  - Clearly distinguish between Armarius software version and Workflow version
  - Updated workflow status labels to explicitly show "Workflow 當前版本" and "Workflow 最新版本"
  - Updated "需要升版" message to "Workflow 需要升版" to avoid confusion
  - Full i18n support for new version display (zh-TW and en-US)

### Changed
- Improved version terminology in UI to prevent confusion between:
  - **Armarius Software Version** (e.g., 0.2.0) - Application features and bug fixes
  - **Library Workflow Version** (e.g., 1.0.0) - Folder structure definitions

## [0.1.3] - 2026-03-03

### Added
- **Library Workflow Management System**:
  - Status detection for library folders (uninitialized/initialized/outdated)
  - Linear workflow UI with guidance buttons
  - Automatic folder structure creation (`_input` for new PDFs, `_processed` for ingested files)
  - Version tracking via `_armarius-config.toml` (structured TOML config)
  - **Multiple workflow support** - choose from 3 pre-defined workflows:
    - `default` - Academic research with processing tracking (_input, _processed)
    - `simple` - Minimal setup with only _input folder
    - `advanced` - Detailed organization (_input, _processed, _archive, _rejected)
  - Workflows defined in `workflows/` directory for easy customization
  - Upgrade flow for version mismatches
  - Full i18n support for workflow UI and messages
  - **Library workflow version** (1.0.0) is now separate from **Armarius software version** (0.1.3)
    - Library workflow version tracks folder structure changes only
    - Allows independent evolution of software features and library structure

### Changed
- **BREAKING**: Input folder changed from `.input` to `_input` for Finder visibility on macOS
- **BREAKING**: Processed folder changed from `.processed` to `_processed` for consistency
- **BREAKING**: Version tracking changed from `.armarius-version` (plain text) to `_armarius-config.toml` (structured TOML)
- Added `toml>=0.10.2` dependency for TOML config file support

### Fixed
- Fixed `.library-workflow.toml.example` to include all required steps


## [0.1.2] - 2026-03-03

### Added
- **Interactive Tutorial Tab**: Split main content into Library and Tutorial tabs
  - Comprehensive tutorial covering Quick Start, Features, Quick Buttons, and Tips
  - Full i18n support (Traditional Chinese and English)
  - AI-friendly prompts for configuration - users can copy/paste to AI assistants
  - Step-by-step organization suggestions for PDF libraries
- **Library Path Management Improvements**:
  - App now prioritizes `library.default_path` over `library.root_path` on startup
  - Quick selection buttons: Default (⭐), Desktop (🖥️), Documents (📝), Downloads (📥)
  - Desktop button with cross-platform support (macOS/Windows/Linux)
  - Relative path display in PDF table for better UX
- **AI-Assisted Configuration**:
  - Copy-paste prompts for setting default library path
  - Copy-paste prompts for organizing PDF folder structure
  - No manual YAML editing required
- **Comprehensive Testing**:
  - 11 automated tests for path resolution, cross-platform support, and error handling
  - Test reports in `.worklog/2026-03-03-test-report.md`
  - Manual test checklist for UI validation

### Changed
- Replaced "主目錄" (Home) with "桌面" (Desktop) in quick selection buttons
- Tutorial tips now provide AI prompts instead of manual editing instructions
- Improved button layout with emoji-only labels and tooltips

### Fixed

### Fixed
- Fixed Light theme switching bug in Streamlit UI - replaced JavaScript injection with pure CSS approach
- Theme switching now properly applies for Light, Dark, and Follow System modes

### Added
- Complete containerization support with Podman/Docker
  - Multi-stage Containerfile with uv for fast dependency installation
  - docker-compose.yml for easy deployment
  - podman.sh helper script with build, run, logs, shell, status commands
  - Volume mounts for PDF library and config directory
  - Health checks and automatic restart
- Container documentation in docs/phase-0-quickstart.md

### Changed
- Theme implementation now uses CSS media queries instead of JavaScript
- Improved CSS variable structure for better theme consistency

## [0.1.1] - 2026-03-03

### Changed
- Restructured README to be product-focused (moved technical details to docs/)
- Added "Recommended Workflow" section with three usage options
- Added "Development Status" section for better project visibility
- Simplified documentation structure per my-vibe-scaffolding guidelines

### Documentation
- All SQL schemas and file layouts now in `docs/data-model.md`
- README reduced from 472 to 221 lines
- Updated Chinese README (README.zh-TW.md) to match new structure

## [0.1.0] - 2026-03-03

## [1.0.0] - YYYY-MM-DD

### Added
- Initial project setup using my-vibe-scaffolding template

---

**📌 注意 | Note**:
- 這是**專案層級**的 CHANGELOG（紀錄你專案的變更）
- 模板自身的變更歷史請查看：[.template/CHANGELOG.md](./.template/CHANGELOG.md)

- This is the **project-level** CHANGELOG (tracks YOUR project changes)
- For template's own change history, see: [.template/CHANGELOG.md](./.template/CHANGELOG.md)

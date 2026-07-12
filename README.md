# Armarius

[![Version](https://img.shields.io/badge/version-0.4.0-blue.svg)](./VERSION)
[![License](https://img.shields.io/badge/license-TBD-yellow.svg)](./LICENSE)

English | [繁體中文](./README.zh-TW.md)

> **Local-first research workspace** — from PDF intake to structured analysis and synthesis drafts

Armarius is a local-first research workspace designed for researchers working with PDF libraries. The current core product focuses on intake, review, analysis, and synthesis in open formats (SQLite + Markdown) with a self-hosted Streamlit workspace and CLI.

> ⚠️ **Pre-release**: This project is in active development (0.X versioning). Breaking changes may occur before 1.0.0 release.

## 📇 About the Name

**Armarius** is Latin for the medieval monastery's **keeper of the library and scriptorium** — the person responsible for the *armarium* (the book cupboard), who catalogued manuscripts, supervised their copying, and lent them out.

Long before search engines, the armarius was the human index of all recorded knowledge: deciding what was worth preserving, organizing it so it could be found, and shepherding it from one generation to the next. It was patient, meticulous, often invisible work.

Armarius honors that role and reimagines it for the digital age — where AI assists with the copying and cataloguing, but the human researcher remains the keeper who decides what matters.



---

- [What is Armarius?](#what-is-armarius)
- [Core Features](#core-features)
- [Quick Start](#quick-start)
- [Recommended Workflow](#recommended-workflow)
- [Documentation](#documentation)

---

## What is Armarius?

Today's Armarius is best understood as a queue-first local research workspace:

- **Library intake** - validate, normalize, review, rename, and track inbound PDFs
- **Analysis workflow** - turn prepared source material into structured analysis outputs
- **Synthesis workflow** - turn saved analyses into usable review/output drafts
- **Open local storage** - keep state in SQLite + Markdown artifacts
- **Self-hosted operation** - run the workflow locally through CLI + Streamlit

---

## ✨ Core Features
---
### 🎯 Design Philosophy

- **Fully Programmatic** - CLI-first, no GUI lock-in
- **Open Formats** - SQLite + Markdown (portable, Git-friendly)
- **Self-hosted** - Your data stays on your machine
- **Editor-agnostic** - Use VSCode, Obsidian, or any Markdown editor

### 💡 What Makes Armarius Different?

1. **Skill System** - Generate multiple views of the same paper
   - Apply different analytical lenses (methodology, security, evidence strength)
   - Extensible via YAML config files

2. **Evidence Grading** - Automatically assess source quality
   - Tier 1: Nature/Science/CORE A* journals + RCT methodology
   - Know which claims are backed by strong evidence

3. **Argue Engine** - Build evidence-backed arguments
   - Ask a research question
   - AI searches your library and ranks by evidence strength
   - Get structured arguments with inline citations

4. **Citation Alerts** - Track what you should read next
   - Papers cited multiple times but not yet in your library
   - Understand research lineage and networks


## 🚀 Quick Start

```bash
uv tool install --editable '.[web]'
armarius init
armarius serve
```

Open `http://localhost:8501` to view the web UI.

If you prefer a virtual environment instead of `uv tool`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[web]'
```

---
---

## 🔄 Recommended Workflow

### Option 1: VSCode + Web UI (Recommended)

1. **Initial setup**:
   ```bash
   armarius init  # Configure library workspace
   armarius serve # Start web service in background
   ```

2. **Daily workflow**:
   - Drop new PDFs into your library inbox folder
   - Run intake from CLI or review queues in the Web UI
   - Open `markdown/papers/` in your editor if you want to inspect normalization outputs
   - Use the Web UI for Dashboard, Library review, Paradigm Analysis, and Concerto Synthesis

3. **Writing mode**:
   - Run Paradigm Analysis on reviewed papers
   - Reframe outputs with Concerto Synthesis
   - Export or refine generated markdown artifacts in your editor

### Option 2: Pure Web UI

- Start `armarius serve`
- Use Dashboard to see queues and next actions
- Use Library to inspect intake, normalization, review states, and cataloging help
- Use Analysis and Synthesis pages for the current researcher workflow

### Option 3: CLI Power User

```bash
# Intake files directly
armarius intake run ~/Downloads/paper.pdf

# Process inbox and normalize accepted PDFs
armarius intake scan-inbox --normalize

# Inspect provenance
armarius trace list --state quarantine
armarius trace show <blob_id> --json-output

# Rename or review a blob
armarius rename propose <blob_id>
armarius review set-state <blob_id> needs_ocr
```

## 📖 Documentation

### Current product areas

- **Core product** - Intake, Library review, Analysis, Synthesis, workflow docs, and the local web workspace
- **Experimental** - Search, agents, MCP, and evaluation tooling that remain useful but are not the primary product path
- **Legacy / historical context** - older merge-roadmap and design notes kept for reference, not as the current source of truth

- **[PRD](./docs/PRD.md)** - Complete product requirements
- **[Data Model](./docs/data-model.md)** - Database schema and file layout
- **[Technology Stack](./docs/technology-stack.md)** - Why we chose each tool
- **[Phase 0 Spec](./docs/phase-0-service-foundation.md)** - Current development phase

### Tech Stack Overview

- **Application**: Python CLI + Streamlit web UI
- **Database**: SQLite
- **PDF Processing**: PyMuPDF
- **Configuration**: YAML + TOML
- **CLI**: Click
- **Current AI Workflow**: Paradigm / Concerto configuration-driven flows

See [docs/technology-stack.md](./docs/technology-stack.md) for detailed rationale.

---

## 🗓️ Development Status

**Current Phase**: Phase 1 - Building on completed M0, M1, M2

✅ **Milestones Completed (March 2026)**:

**M0 - Service Foundation**:
- Configuration system (`~/.armarius/config.yaml`, environment overrides)
- PDF scanner with basic metadata extraction (size, pages, readability)
- Streamlit web UI with library view, search, filtering, theme switching
- CLI commands (`armarius init`, `armarius serve`, `armarius scan`)
- i18n support (en-US, zh-TW) with live language switching

**M1 - Database & Deployment**:
- SQLite database with full schema (papers, paradigms, analyses, syntheses, notes, citations)
- Docker/Podman containerization with multi-arch support (amd64/arm64)
- Comprehensive build/deployment scripts (`scripts/build.sh`, `scripts/deploy.sh`)

**M4 (Partial) - Paradigm System**:
- YAML-based paradigm configuration (researcher/topic/school types)
- Multi-lens analysis workflow (Paradigm Analysis page)
- Concerto synthesis system (audience-specific output generation)
- Full Streamlit UI with 2 dedicated pages

**M2 - Ingest Pipeline** ✅ (Completed March 2026):
- Complete cataloging system with DOI-based file naming
- SQLite tracking with 7 new columns (original_filename, current_filename, catalog_method, doi_source, ingest_status, error_message, last_verified_at)
- Metadata extraction from PDFs (title, authors, DOI, year) with multiple fallback strategies
- Online DOI lookup via Crossref and Semantic Scholar APIs
- Intelligent file naming: DOI → safe filename, or title → filename with sanitization
- 4 catalog methods: flat, by_year, by_venue, custom categories
- Re-cataloging system for switching organization methods
- "編目助手" (Catalog Assistant) UI page with comprehensive tutorial
- Modules: `metadata_extractor.py`, `doi_resolver.py`, `naming_strategy.py`, `cataloging.py`, `catalog_assistant.py`

📋 **Next Milestones**:
- **M4**: Continue strengthening the current Paradigm / Concerto workflow
- **M5**: Citation graph and unread alerts
- **M6**: Complete Web UI v1 around paper detail and supporting views
- **M7**: Argument workflow after the retrieval layer is ready

---

## 🤝 Contributing

This project is primarily driven by the author's own needs, but community issues and feature suggestions are welcome.

To contribute code:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (follow conventions in [AGENTS.md](./AGENTS.md))
4. Push to your branch
5. Open a Pull Request

See [CONTRIBUTING.md](./CONTRIBUTING.md) for details

---

## 📄 License

License TBD - Will choose an open source license, see [LICENSE](./LICENSE)

---

## 🙏 Acknowledgments

Armarius is inspired by:
- Zotero (literature management)
- Obsidian (knowledge linking)
- LlamaIndex (RAG architecture)
- And all researchers struggling with academic research 📚

---

**Based on**: [my-vibe-scaffolding](https://github.com/matheme-justyn/my-vibe-scaffolding) v1.13.0

For more guidance on writing READMEs, see [.template/docs/README_GUIDE.md](./.template/docs/README_GUIDE.md)

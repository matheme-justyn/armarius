# Armarius

[![Version](https://img.shields.io/badge/version-0.4.0-blue.svg)](./VERSION)
[![License](https://img.shields.io/badge/license-TBD-yellow.svg)](./LICENSE)

English | [繁體中文](./README.zh-TW.md)

> **Academic Knowledge Management System** — Complete lifecycle from PDF to structured knowledge cards

Armarius is a fully programmatic academic literature management system designed for researchers. It has no dependency on any GUI application; all data is stored in open formats (SQLite + Markdown) and can be visualized through self-hosted web services.

> ⚠️ **Pre-release**: This project is in active development (0.X versioning). Breaking changes may occur before 1.0.0 release.

## 📇 About the Name

**Armarius** refers to the historical keeper of the **armarium** — the book cupboard or library press in monastic settings — and, by extension, the person responsible for coordinating book circulation and scriptorium work.

The name fits this project because the system is meant to steward a research library end to end: ingesting texts, organizing them, assigning analytical workflows, and preparing them for later synthesis and argumentation.

It also establishes a broader naming family for future modules based on historical knowledge-work roles such as **Rubricator**, **Emendator**, and **Ligator**.

---

- [What is Armarius?](#what-is-armarius)
- [Core Features](#core-features)
- [Quick Start](#quick-start)
- [Recommended Workflow](#recommended-workflow)
- [Documentation](#documentation)

---

## What is Armarius?

Armarius transforms your academic PDF collection into a queryable knowledge base:

- **Automatic metadata extraction** - Title, authors, venue, citations parsed automatically
- **Multi-angle summarization** - Generate different summaries with pluggable "Skills" (methodology, security, general, etc.)
- **Evidence grading** - Know which papers are backed by Nature/Science vs. preprints
- **Citation tracking** - See what you've cited but haven't read yet
- **AI argumentation** - Generate evidence-backed arguments from your library

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

> ⚠️ **Phase 0 in development** - Installation instructions below are planned, not yet functional.

```bash
# Install
pip install armarius

# Initialize (one-time setup)
armarius init
# This creates ~/.armarius/config.yaml and prompts for your PDF folder

# Start the web interface
armarius serve
# Open http://localhost:8501

# Or use CLI directly
armarius scan                          # Find all PDFs in configured folder
armarius ingest path/to/paper.pdf     # Process a single paper
armarius summarize --skill methodology # Generate methodology summary
```

---
---

## 🔄 Recommended Workflow

### Option 1: VSCode + Foam (Recommended)

1. **Initial setup**:
   ```bash
   armarius init  # Configure library folder
   armarius serve # Start web service in background
   ```

2. **Daily workflow**:
   - Drop new PDFs into your inbox folder
   - Armarius auto-scans and processes them
   - Open `markdown/papers/` in VSCode with Foam extension
   - Take notes, add tags, link between papers using `[[wikilinks]]`
   - Use web UI when you need citation graphs or argument generation

3. **Writing mode**:
   - Open Argue Engine in web UI
   - Input your thesis statement
   - Get evidence-backed argument with citations
   - Export to Markdown and refine in VSCode

### Option 2: Pure Web UI

- Start `armarius serve`
- Upload PDFs via web interface
- Read summaries, explore citation graph, generate arguments all in browser

### Option 3: CLI Power User

```bash
# Batch ingest
armarius ingest ~/Downloads/*.pdf

# Generate summaries for all papers
armarius summarize --all --skills general,methodology

# Search your library
armarius search "transformer architecture"

# Export to BibTeX
armarius export --format bibtex > library.bib
```

## 📖 Documentation

- **[PRD](./docs/PRD.md)** - Complete product requirements
- **[Data Model](./docs/data-model.md)** - Database schema and file layout
- **[Technology Stack](./docs/technology-stack.md)** - Why we chose each tool
- **[Phase 0 Spec](./docs/phase-0-service-foundation.md)** - Current development phase

### Tech Stack Overview

- **Backend**: Python + FastAPI
- **Frontend**: Streamlit (Phase 0-1) → React (Phase 2+)
- **Database**: SQLite + SQLAlchemy
- **AI/RAG**: LlamaIndex + LiteLLM (supports OpenAI, Anthropic, Ollama)
- **Vector Store**: ChromaDB
- **PDF Processing**: PyMuPDF
- **CLI**: Click

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
- Docker containerization with multi-arch support (amd64/arm64)
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
- **M4**: Complete traditional Skill system (general summaries)
- **M5**: Citation graph and unread alerts
- **M6**: Complete Web UI v1 (Paper Detail view, Citation Graph visualization)
- **M7**: Argue Engine (evidence-weighted argumentation)

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

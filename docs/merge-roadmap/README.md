# Merge Roadmap (from Capsa)

These documents originate from the **Capsa** project, which was merged into
Armarius (Armarius is the core). The working code Capsa already had —
bounding-box PDF parsing, Qdrant vector storage, semantic search, the
multi-agent framework, and the MCP server — now lives in the `armarius`
package (`armarius/parser`, `armarius/storage`, `armarius/agents`,
`armarius/mcp`).

The documents here describe **future** capabilities that were designed but
**not yet implemented**. They are kept as the forward roadmap:

- **[TECHNICAL_DECISIONS.md](./TECHNICAL_DECISIONS.md)** — Foundational
  technical decisions (Marker + PyMuPDF, DuckDB vs SQLite, Wiki layer, DOI
  pipeline). Note: Armarius already uses **SQLite** for metadata, so the
  DuckDB discussion is informational — see `DESIGN_VS_REALITY.md`.
- **[ADVANCED_FEATURES_DESIGN.md](./ADVANCED_FEATURES_DESIGN.md)** — Three
  advanced features: credibility scoring (predatory-journal detection),
  reader personas (multi-perspective review), and interactive
  literature-review generation.
- **[DESIGN_VS_REALITY.md](./DESIGN_VS_REALITY.md)** — Gap analysis between
  the design vision and the (then-)existing code, with recommended phased
  paths (A/B/C). The merge into Armarius corresponds to the **hybrid (Path C)**
  approach: keep the existing architecture, add capabilities incrementally.

## Status after the merge

| Capability | Status |
|------------|--------|
| PDF parsing + bounding boxes | ✅ Merged (`armarius/parser`) |
| Vector store + semantic search (Qdrant) | ✅ Merged (`armarius/storage`) |
| Multi-agent framework | ✅ Merged (`armarius/agents`) |
| MCP server | ✅ Merged (`armarius/mcp`) |
| SQLite metadata DB + cataloging + DOI | ✅ Pre-existing in Armarius |
| Credibility scoring | 📋 Designed, not implemented |
| Reader personas | 📋 Designed, not implemented |
| Literature-review generation | 📋 Designed, not implemented |
| Marker markdown conversion | 📋 Optional, not implemented |
| Wiki knowledge layer | 📋 Optional, not implemented |

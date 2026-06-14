# Phase 0 Technical Decisions

**Date**: 2026-03-03  
**Status**: Decided  
**Context**: Initial service foundation before any PDF processing

---

## Configuration System

**Decision**: YAML-based configuration at `~/.armarius/config.yaml`

**Rationale**:
- YAML is more readable than TOML for hierarchical configs
- User home directory (`~/.armarius/`) follows Unix convention for app configs
- Can be overridden by environment variables (`ARMARIUS_LIBRARY_ROOT`)

**Example**:
```yaml
library:
  root_path: ~/Documents/papers
  recursive_scan: true

web:
  host: localhost
  port: 8000
  
database:
  path: ~/.armarius/armarius.db
```

---

## Folder Structure

**Decision**: User-managed folders (no enforced structure in Phase 0)

**Rationale**:
- Users may already have existing PDF collections
- Phase 0 is about "discovery" not "organization"
- Phase 1 will introduce optional automatic organization

**User Experience**:
1. User points Armarius to their existing folder: `/Users/justyn/research/papers`
2. Armarius scans and lists all PDFs recursively
3. No files are moved or renamed in Phase 0

---

## CLI Framework

**Decision**: Click (Python CLI framework)

**Rationale**:
- Industry standard for Python CLIs
- Clean command definition: `@click.command()`
- Built-in help generation
- Parameter validation out-of-the-box

**Commands**:
- `armarius init` - Interactive configuration wizard
- `armarius serve` - Start web UI
- `armarius config show` - Display current config (Phase 0.5)
- `armarius scan` - CLI-only PDF scan (Phase 0.5)

---

## Web UI Technology

**Decision**: Streamlit for Phase 0

**Rationale**:
- **Speed**: Can build functional UI in 1-2 days
- **Zero frontend code**: Pure Python
- **Rapid iteration**: No build step, instant reload
- **Good enough**: Phase 0 only needs basic list view

**Migration Path**:
- Phase 0: Streamlit (list PDFs, search, settings)
- Phase 2: FastAPI + React (full-featured dashboard)
- Both can coexist during transition

**Trade-offs Accepted**:
- Less polished UI than React
- Limited customization
- Not ideal for complex interactions (OK for Phase 0 scope)

---

## File Scanner

**Decision**: Python `pathlib` + recursive glob

**Rationale**:
- Standard library (no dependencies)
- Cross-platform (Windows, macOS, Linux)
- Efficient for < 10,000 files
- Simple, readable code

**Implementation**:
```python
from pathlib import Path

def scan(root: Path, recursive: bool = True) -> List[Dict]:
    pattern = "**/*.pdf" if recursive else "*.pdf"
    return [
        {
            "path": str(p),
            "size": p.stat().st_size,
            "modified": p.stat().st_mtime
        }
        for p in root.glob(pattern) if p.is_file()
    ]
```

**Limitations Known**:
- Symbolic links follow default behavior
- Case sensitivity depends on filesystem
- No file type validation beyond `.pdf` extension (Phase 1 will add)

---

## Database

**Decision**: SQLite, but NOT used in Phase 0

**Rationale**:
- Phase 0 scans filesystem on-demand (no persistence)
- Database schema will be introduced in Phase 1 (with ingest pipeline)
- Keeps Phase 0 minimal: "See what you have, that's it"

**Phase 1 will add**:
- `papers` table (metadata storage)
- `summaries` table (Skill outputs)
- `citations` table (reference graph)

---

## Error Handling

**Decision**: Fail gracefully, log errors, continue scanning

**Behavior**:
- Unreadable folder → Skip, log warning, continue
- Invalid PDF → Include in list, mark as "needs verification" (Phase 1 feature)
- Permission denied → Log error, show in UI as "inaccessible"

**Philosophy**: Phase 0 is exploratory — show user what Armarius can see, including problems.

---

## Performance Targets

**Decision**: Support up to 10,000 PDFs in Phase 0

**Assumptions**:
- Typical researcher library: 500-2,000 papers
- Power users: up to 10,000
- Beyond 10,000: Phase 2 will add pagination/lazy loading

**Optimization Strategy**:
- Phase 0: Full scan on startup (acceptable for < 10,000 files)
- Phase 0.5: Cache scan results (invalidate on manual refresh)
- Phase 1: Database-backed listing (instant load)

---

## Testing Strategy

**Decision**: Pytest + manual testing for Phase 0

**Test Coverage**:
- Unit tests: Config loading, file scanning logic
- Integration tests: `armarius init` → `armarius serve` workflow
- Manual tests: Empty folder, 1000+ PDFs, nested 5+ levels deep

**CI/CD**: Not required for Phase 0 (manual validation sufficient)

---

## Non-Decisions (Deferred)

These are intentionally NOT decided in Phase 0:

- **File integrity checks** → Phase 1
- **Metadata extraction** → Phase 1
- **Naming strategies** → Phase 1
- **File organization** → Phase 1
- **Database schema** → Phase 1
- **Authentication** → Phase 3+

---

## Alternatives Considered

### Configuration Format: TOML vs. YAML

**Rejected**: TOML
- **Reason**: Less readable for nested configs (web.host vs [web] host)
- **Note**: TOML would be fine, but YAML is more common for app configs

### Web UI: FastAPI + React vs. Streamlit

**Rejected for Phase 0**: FastAPI + React
- **Reason**: 1 week development time vs. 1-2 days for Streamlit
- **Decision**: Use Streamlit for Phase 0, migrate to FastAPI+React in Phase 2

### Folder Management: Enforce structure vs. User freedom

**Rejected for Phase 0**: Enforce structure
- **Reason**: Users may have existing collections, Phase 0 is exploratory
- **Decision**: Phase 1 will introduce optional auto-organization

---

## Success Metrics

Phase 0 technical implementation is successful if:

- [ ] User can configure library path via `armarius init` in < 1 minute
- [ ] Scanning 1,000 PDFs completes in < 2 seconds
- [ ] Web UI loads and displays PDF list in < 1 second after scan
- [ ] Zero crashes on empty folders, permission errors, or mixed file types
- [ ] Config changes persist across `armarius serve` restarts

---

## References

- [Click Documentation](https://click.palletsprojects.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Python pathlib](https://docs.python.org/3/library/pathlib.html)

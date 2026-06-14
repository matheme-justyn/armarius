# Phase 0: Service Foundation

**Status**: Planning  
**Goal**: Establish basic service infrastructure and file discovery

---

## Objectives

Enable users to:
1. Configure a local folder for PDF management
2. Start the Armarius web service
3. View a list of PDFs in the configured folder via web browser

**Philosophy**: Phase 0 focuses on "seeing what you have" before any processing. No metadata extraction, no file movement — just discovery and listing.

---

## Architecture

### Configuration System

**Config file**: `~/.armarius/config.yaml`

```yaml
# Armarius Configuration

# Library root: where PDFs are located
library:
  root_path: ~/Documents/papers     # User configurable
  recursive_scan: true               # Include subfolders
  
# Database (prepared for Phase 1)
database:
  path: ~/.armarius/armarius.db
  
# Web UI
web:
  host: localhost
  port: 8000
  auto_open_browser: true
  
# Logging
logging:
  level: INFO
  path: ~/.armarius/logs/armarius.log
```

**Environment variable overrides**:
- `ARMARIUS_LIBRARY_ROOT` → `library.root_path`
- `ARMARIUS_WEB_PORT` → `web.port`

---

## CLI Commands

### `armarius init`

Initialize Armarius configuration.

```bash
$ armarius init

📂 Armarius Initialization
========================

Library root path [~/Documents/papers]: /Users/justyn/research/papers
Web UI port [8000]: 
Auto-open browser [yes]: 

✅ Configuration saved to ~/.armarius/config.yaml
✅ Created log directory: ~/.armarius/logs

Next steps:
  1. Place PDFs in /Users/justyn/research/papers
  2. Run 'armarius serve' to start the web UI
```

**Behavior**:
- Prompts for essential settings (library path, port)
- Creates `~/.armarius/` directory structure
- Writes `config.yaml` with user's choices
- Does NOT create library folder (user manages their own folders)

---

### `armarius serve`

Start the web UI service.

```bash
$ armarius serve

🚀 Armarius is running!
   Web UI: http://localhost:8000
   Library: /Users/justyn/research/papers
   PDFs found: 42 files
   
   Press Ctrl+C to stop
   
Scanning library...
✓ Scanned 42 PDFs in 0.3s
```

**Behavior**:
- Loads config from `~/.armarius/config.yaml`
- Scans library folder for PDFs
- Starts Streamlit web server
- Opens browser if `auto_open_browser: true`

---

## Web UI (Streamlit)

### Home View

```
┌─────────────────────────────────────────────────────────┐
│ 📚 Armarius - Academic Knowledge Management               │
├─────────────────────────────────────────────────────────┤
│ 📂 Library: /Users/justyn/research/papers               │
│    [⚙️ Settings]                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 🔍 Search: [________________]  [Refresh 🔄]            │
│                                                         │
│ ☑️ Include subfolders                                   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ 📄 42 PDFs found                                        │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────┬────────┬───────┐│
│ │ Filename                            │ Size   │ Path  ││
│ ├─────────────────────────────────────┼────────┼───────┤│
│ │ smith_2024_quantum.pdf              │ 2.3 MB │ /...  ││
│ │ chen_2023_neural_networks.pdf       │ 5.1 MB │ /...  ││
│ │ deep_learning_basics.pdf            │ 1.8 MB │ /sub/ ││
│ │ research_methods.pdf                │ 3.2 MB │ /...  ││
│ │ unreadable_scan.pdf                 │ 12 MB  │ /...  ││
│ │ ...                                 │        │       ││
│ └─────────────────────────────────────┴────────┴───────┘│
│                                                         │
│ 💡 Phase 0: Discovery only. Metadata extraction coming │
│    in Phase 1.                                          │
└─────────────────────────────────────────────────────────┘
```

### Settings View (Modal/Sidebar)

```
⚙️ Settings
───────────

Library Configuration:
  Root path: /Users/justyn/research/papers
  [Browse...] [Change]
  
  ☑️ Recursive scan (include subfolders)
  
Display Options:
  Items per page: [25 ▼]
  Sort by: [Modified date (newest) ▼]
  
[Save] [Cancel]
```

---

## File Scanner Module

**Location**: `armarius/scanner.py`

### Class: `PDFScanner`

```python
from pathlib import Path
from typing import List, Dict
from datetime import datetime

class PDFScanner:
    """Scans filesystem for PDF files"""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path).expanduser().resolve()
    
    def scan(self, recursive: bool = True) -> List[Dict]:
        """
        Scan directory for PDF files
        
        Args:
            recursive: Include subdirectories
            
        Returns:
            List of dicts with:
              - path: str (absolute path)
              - filename: str
              - size: int (bytes)
              - modified_at: float (unix timestamp)
              - relative_path: str (relative to root)
        """
        pattern = "**/*.pdf" if recursive else "*.pdf"
        pdf_files = []
        
        for pdf_path in self.root_path.glob(pattern):
            if pdf_path.is_file():
                stat = pdf_path.stat()
                pdf_files.append({
                    "path": str(pdf_path),
                    "filename": pdf_path.name,
                    "size": stat.st_size,
                    "modified_at": stat.st_mtime,
                    "relative_path": str(pdf_path.relative_to(self.root_path))
                })
        
        return sorted(pdf_files, key=lambda x: x["modified_at"], reverse=True)
    
    def count(self, recursive: bool = True) -> int:
        """Quick count without full scan"""
        pattern = "**/*.pdf" if recursive else "*.pdf"
        return sum(1 for _ in self.root_path.glob(pattern))
```

---

## Project Structure

```
armarius/
├── armarius/
│   ├── __init__.py
│   ├── cli.py              # Click commands (init, serve)
│   ├── config.py           # Config loading/validation
│   ├── scanner.py          # PDFScanner class
│   └── web/
│       ├── __init__.py
│       └── app.py          # Streamlit application
├── config/
│   └── armarius.yaml.example # Example configuration
├── tests/
│   ├── test_cli.py
│   ├── test_config.py
│   └── test_scanner.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Dependencies

### Core
- **Python** >= 3.10
- **Click** >= 8.0 (CLI framework)
- **PyYAML** >= 6.0 (config parsing)
- **Streamlit** >= 1.28 (web UI)

### Development
- **pytest** (testing)
- **black** (formatting)
- **mypy** (type checking)

---

## Success Criteria

Phase 0 is complete when:

- [ ] User can run `armarius init` and configure library path
- [ ] User can run `armarius serve` and web UI opens in browser
- [ ] Web UI displays list of PDFs in configured folder
- [ ] User can search/filter PDFs by filename
- [ ] User can toggle recursive scan on/off
- [ ] Manual refresh button updates the list
- [ ] No crashes when folder is empty or contains non-PDF files

---

## Non-Goals (Deferred to Phase 1+)

- ❌ PDF content reading
- ❌ Metadata extraction
- ❌ File integrity checks
- ❌ File renaming or moving
- ❌ Database operations
- ❌ OCR detection
- ❌ Thumbnail generation

---

## Development Timeline

**Estimated**: 2-3 days

- Day 1: CLI (init, serve) + Config system + Scanner
- Day 2: Streamlit UI (basic list view)
- Day 3: Search/filter + Settings + Testing

---

## Testing Strategy

### Unit Tests
- `test_config.py`: Config loading, validation, defaults
- `test_scanner.py`: File discovery, recursive scan, edge cases

### Integration Tests
- `test_cli.py`: Full init → serve workflow

### Manual Testing
- Empty folder (0 PDFs)
- Large folder (1000+ PDFs)
- Nested structure (5+ levels deep)
- Mixed file types (PDFs + non-PDFs)

---

## Next Phase

**Phase 1**: After Phase 0 is validated, we add:
- PDF file integrity checks
- Metadata extraction (title, authors, year)
- Database persistence
- Naming strategy system

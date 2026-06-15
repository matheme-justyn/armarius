# Phase 0 Quick Start Guide

Phase 0 implementation is complete! Here's how to test it:

## Installation

### Option 1: Native Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Armarius in development mode
pip install -e .
```

### Option 2: Container (Podman/Docker)

```bash
# Build container image
./podman.sh build

# Run container with your PDF library
./podman.sh run --library ~/Documents/papers --port 8501

# View web UI at http://localhost:8501
```

**Podman Helper Commands:**
```bash
./podman.sh status    # Check container status
./podman.sh logs      # View logs
./podman.sh stop      # Stop container
./podman.sh start     # Start existing container
./podman.sh shell     # Open shell in container
./podman.sh clean     # Remove container and image
```

**Container Features:**
- ✅ Multi-stage build with uv (fast dependency installation)
- ✅ Volume mounts for library and config
- ✅ Health checks for monitoring
- ✅ Automatic restart on failure
- ✅ Compatible with both Podman and Docker

## Testing with Sample Data

### 1. Create test library (optional)

```bash
# Create test directory
mkdir -p /tmp/armarius-test-library/papers

# Or use your own PDF folder
```

### 2. Initialize Armarius

```bash
armarius init --library-path /tmp/armarius-test-library
```

This creates `~/.armarius/config.yaml` with your settings.

By default, Armarius keeps browser auto-open enabled so the web UI can be launched with a normal click/open flow.

### 3. Scan your library (CLI)

```bash
armarius scan
```

Expected output:
```
🔍 Scanning: /tmp/armarius-test-library

📊 Statistics:
   Total PDFs: 3
   Readable: 3
   Unreadable: 0
   Total size: 0.01 MB
   Total pages: 3

📄 Sample files (first 10):
   ✅ Smith_2024_Quantum_Computing.pdf (0.00 MB)
   ✅ Chen_2024_Neural_Networks.pdf (0.00 MB)
   ✅ Lee_2023_Machine_Learning.pdf (0.00 MB)
```

### 4. Start Web UI

```bash
armarius serve
```

This launches Streamlit at http://localhost:8501

**Web UI Features:**
- 📊 Statistics overview (total PDFs, readable/unreadable count, total size)
- 📄 PDF list with filename, size, page count, modified time, path
- 🔍 Search/filter by filename
- 🔄 Manual refresh button (clears cache)
- ⚙️ Settings sidebar showing current config

## What's Working

✅ Configuration system (`~/.armarius/config.yaml`)  
✅ CLI commands (`init`, `scan`, `serve`)  
✅ PDF scanner (recursive, extracts metadata)  
✅ Streamlit UI (list, search, stats)  
✅ Environment variable overrides (`ARMARIUS_LIBRARY_ROOT`, `ARMARIUS_WEB_PORT`)

## What's NOT in Phase 0

❌ No metadata extraction (title, authors, year) - Phase 1  
❌ No database storage - Phase 1  
❌ No file organization - Phase 1  
❌ No AI features - Phase 2+

## Configuration File

Location: `~/.armarius/config.yaml`

```yaml
library:
  root_path: /tmp/armarius-test-library
  recursive_scan: true

database:
  path: ~/.armarius/armarius.db

web:
  host: localhost
  port: 8501
  auto_open_browser: true

logging:
  level: INFO
  path: ~/.armarius/logs/armarius.log
```

## Next Steps

To continue development:
1. Test with your own PDF collection
2. Report any bugs or unexpected behavior
3. Ready to implement Phase 1 (Ingest Pipeline) when you're satisfied with Phase 0

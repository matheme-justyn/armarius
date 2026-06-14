# Library Workflows

This directory contains workflow definitions for Armarius library initialization.

## Available Workflows

### 📚 Default - Academic Research

**File**: `default.toml`

**Best for**: Academic researchers who need full PDF processing pipeline

**Folder structure**:
- `_input`: Drop new PDF files here
- `_processed`: Ingested PDFs are moved here after processing

**Use when**: You want to track which PDFs have been processed and maintain a clean input folder.

---

### 📖 Simple - Minimal Setup

**File**: `simple.toml`

**Best for**: Personal reading, quick PDF organization

**Folder structure**:
- `_input`: All PDFs stay here (no processing tracking)

**Use when**: You don't need processing tracking and want the simplest possible setup.

---

### 🔬 Advanced - Detailed Organization

**File**: `advanced.toml`

**Best for**: Large research projects, collaborative teams, power users

**Folder structure**:
- `_input`: New PDFs waiting to be processed
- `_processed`: Successfully ingested PDFs
- `_archive`: Old or reference papers
- `_rejected`: PDFs that failed processing or are not relevant

**Use when**: You need fine-grained organization and categorization of your library.

---

## How Workflows Work

1. **Selection**: When initializing a new library, Armarius prompts you to choose a workflow
2. **Initialization**: Armarius creates the required folders based on the workflow definition
3. **Version Tracking**: The workflow choice is saved in `_armarius-config.toml`
4. **Consistency**: All future operations respect the chosen workflow structure

## Custom Workflows

To create a custom workflow:

1. Copy one of the existing `.toml` files
2. Modify the `[workflow.steps]` and `[folders]` sections
3. Place it in this directory with a descriptive name (e.g., `my-workflow.toml`)
4. Restart Armarius - your workflow will appear in the selection dropdown

## Version Management

All workflows share the same **Library Workflow Version** (currently `1.0.0`).

This version is **independent** from the Armarius software version:
- Armarius Software: `0.1.3` (features, bug fixes, UI improvements)
- Library Workflow: `1.0.0` (folder structure definitions)

When the folder structure changes, the workflow version increments and triggers migration steps.

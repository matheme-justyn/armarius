# Phase 0 Technical Decisions

> Status: historical phase document, rewritten to match the current shipped direction

This document now records the technical decisions that still matter for the current `tool-armarius` product line.

The short version:
- Python remains the main runtime
- CLI + Streamlit remain the current shipped interfaces
- SQLite + local files remain the current persistence model
- the repo is no longer just a thin phase-0 prototype; it already includes intake, provenance, and current analysis/synthesis workflow pieces

## 1. Runtime Language

**Decision**: Python

Why it still holds:
- one-language local toolchain
- good PDF/data tooling
- low friction for CLI and Streamlit
- fast iteration for a local-first research workspace

## 2. CLI Framework

**Decision**: Click

Why it still holds:
- the current CLI already relies on Click
- commands remain simple and readable
- command help and option parsing are stable
- it fits a local tool with many small operational commands

Current CLI responsibilities include:
- `armarius init`
- `armarius serve`
- `armarius scan`
- intake/review/trace/rename-related commands

## 3. Web UI

**Decision**: Streamlit is the current shipped web UI

This is the important update.

Older docs sometimes framed Streamlit as only a temporary phase-0 stopgap on the way to a FastAPI/React app. For the current product story, Streamlit is not just an experiment; it is the actual local workspace users operate today.

Why this still makes sense:
- low complexity
- no split frontend/backend stack required
- good enough for queue-first workflow pages
- fast to evolve while product language and workflow are still being refined

Current Streamlit responsibilities:
- Dashboard
- Library review and inspection
- Analysis workspace
- Synthesis workspace
- Guide / settings surfaces

## 4. Persistence Model

**Decision**: SQLite + local filesystem

Why it still holds:
- local-first and portable
- no service dependency
- good fit for provenance-oriented intake records
- easy to test

Current interpretation:
- SQLite is already part of the real product, not merely a future idea
- filesystem artifacts remain first-class outputs
- local PDF storage is part of the workflow contract

## 5. PDF Handling

**Decision**: local PDF inspection and processing with Python tooling, currently centered on PyMuPDF-based behavior

Why it still holds:
- current code already uses this path
- local execution matters more than distributed scale right now
- the product needs inspectable local behavior over infrastructure complexity

## 6. Product Boundary Decisions

The current product line explicitly favors:
- local operation over hosted architecture
- workflow clarity over large architectural expansion
- stable testability over network-required defaults

That leads to these practical decisions:
- no required external database
- no required hosted vector store
- no required online model download for baseline test success
- fallback behavior is acceptable when it preserves deterministic local verification

## 7. What Is Deferred

These remain deferred decisions, not current product commitments:
- FastAPI as the main current application server
- React as the main current frontend
- Redis/Celery style background infrastructure
- mandatory retrieval/vector stack for basic use
- citation graph as a current core interaction surface
- argument engine as a current baseline workflow

## 8. Testing Decision

**Decision**: local pytest-based regression coverage is part of the current product discipline

Why it matters now:
- the codebase is no longer just a throwaway prototype
- intake/provenance/workflow regressions are easy to introduce
- offline-capable verification is important in restricted environments

Current expectation:
- normal development should be verifiable with local pytest runs
- the shipped code should not depend on live network fetches merely to pass core tests

## 9. Document Rule

This file should describe the technical decisions that still govern the current product.

If an older phase-era assumption conflicts with current shipped behavior, update the document to the shipped behavior rather than preserving outdated future-facing language.

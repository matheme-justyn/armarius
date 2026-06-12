# Merge Blueprint from Capsa into Armarius

## Decision

Use **Armarius** (formerly Cardex) as the single surviving repository.

Reason:
- stronger product vision and data model
- clearer long-term architecture for research workflow management
- naming now aligned with the chosen historical-profession family
- Capsa provides the stronger implemented technical engine, but not the stronger final product identity

## What Armarius already has

- product framing and PRD
- hybrid SQLite + Markdown data model
- ingest and cataloging direction
- paradigm system concept
- workflow and self-hosted UI direction

## What Capsa contributes

- PDF parsing with bounding boxes
- chunking strategies
- vector storage and semantic search
- screenshot-backed citation evidence
- multi-agent orchestration baseline
- MCP server baseline
- stronger current test-backed core for local-first document intelligence

## Recommended target architecture

### 1. Library Layer
Armarius-owned concepts:
- papers / analyses / syntheses / notes / paradigms
- SQLite source of truth
- library workflows and curation states

### 2. Evidence Layer
Derived from Capsa:
- parser
- chunk model
- bounding boxes
- screenshot evidence
- semantic retrieval

### 3. Intelligence Layer
Merged direction:
- Armarius paradigm-guided analysis
- Capsa query / compare / summarize / citation orchestration
- future evidence quality and argumentation modules

### 4. Interface Layer
Merged direction:
- Armarius product-facing CLI / web UX
- Capsa MCP exposure for AI-tool integration

## Suggested module naming family

- `armarius` - main orchestrator / library steward
- `rubricator` - structure enrichment, highlighting, semantic markup
- `emendator` - validation, correction, citation checking, metadata QA
- `ligator` - bundling, export, synthesis assembly

## First migration steps

1. Rename project identity from Cardex to Armarius
2. Preserve Cardex-era product docs, but update naming rationale
3. Import Capsa parser/storage/agents concepts into Armarius design docs before code movement
4. Decide whether package namespace remains flat (`armarius.*`) or uses subpackages for imported concepts
5. Only after architecture alignment, start moving implementation code

## Current turn scope

This turn only establishes:
- the final name
- historical naming rationale
- merge blueprint
- primary repo decision

Actual code-porting from Capsa should happen in the next integration phase.

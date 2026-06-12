# Naming and Module Lineage

## Final project name: Armarius

**Armarius** is the selected final name for this project.

In medieval monastic settings, an **armarius** was the keeper of the **armarium** (book cupboard / book press) and often the person responsible for the scriptorium's book workflow: managing exemplars, assigning copying tasks, and overseeing writing materials and textual circulation.

This name is chosen because it matches the project's core purpose more precisely than the previous names:

- curating and organizing a research library
- managing the flow from raw documents to structured knowledge
- supporting downstream synthesis, comparison, and argumentation
- emphasizing the invisible labor behind preserving and activating texts

## Why not keep the previous names?

### Cardex

**Cardex** was a strong product name and carried an explicit tribute to the nearly extinct profession of card catalog filing and the invisible labor of library workers maintaining card catalogs.

However, it was tied to a more modern library infrastructure metaphor (card index / card catalog) rather than the deeper historical naming direction now preferred for the project.

### Capsa

**Capsa** was useful as a technical codename for a document container / evidence engine concept.

But the term refers more naturally to a **container** (book box, case) than to a profession. It is therefore better understood as a possible internal subsystem concept than as the primary product identity.

## Historical role references for future module naming

The following historical roles are intentionally preserved as a naming pool for future modules or subpackages.

### Armarius

- Role: keeper of the armarium; book-cupboard / library steward; often associated with scriptorium coordination
- Project fit: top-level orchestration, library management, workflow coordination
- Suggested future use: main product / orchestrator / library layer

### Rubricator

- Role: the specialist who added rubrics, red headings, initials, and structural visual markers after the body text was copied
- Project fit: structure enrichment, annotation, highlighting, semantic section labeling, presentation formatting
- Suggested future use: post-processing / annotation / structure-marking module

### Emendator

- Role: textual corrector / proofreader who compared copies against exemplars and corrected errors
- Project fit: validation, consistency checks, citation verification, metadata correction, quality review
- Suggested future use: verification / QA / correction module

### Ligator

- Role: binder who gathered written leaves and assembled them into a bound volume
- Project fit: packaging, export, synthesis, final assembly of outputs from many sources
- Suggested future use: export / compilation / bundle-generation module

## Naming principle

The naming direction for this project is now explicitly:

1. Prefer **historical knowledge-work professions**, especially ones tied to libraries, scriptoria, copying, cataloging, textual correction, or book production.
2. Prefer names that carry a **clear operational metaphor** for the software layer they represent.
3. Use names that can scale into a **module family**, not just a single repo name.
4. When a good historical term conflicts with existing software naming or creates excessive ambiguity, record it in design notes even if it is not chosen.

## Merge implication

Going forward, this repository should absorb the stronger technical engine ideas from the earlier `capsa` prototype while preserving the broader product architecture and historical naming direction already established here.

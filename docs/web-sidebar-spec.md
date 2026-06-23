# Web Sidebar Specification

## Problem Statement

The sidebar should help users orient themselves inside the research workflow, not compete with the main page for attention.

## Product Assumptions

1. One installed Armarius instance manages one active workspace at a time.
2. Main navigation should reflect the research workflow, not expose every low-level control.
3. Settings belong on a dedicated page instead of being mixed into operational navigation.
4. The main UI should feel like a research workspace, not an internal admin panel.

## Sidebar Responsibilities

The sidebar should contain only three groups, in this order:

1. **Workflow Navigator**
   - current step
   - next recommended step
   - queue/state-aware navigation

2. **Page Navigation**
   - Dashboard
   - Library
   - Analysis
   - Synthesis
   - Guide
   - Catalog Assistant
   - Settings

3. **Lightweight State Reference**
   - only small context markers when useful
   - no full settings forms
   - no path editing as a primary sidebar action

## Current Implementation Direction

- Main sidebar: workflow navigator + page navigation
- Main pages carry the actual task context and UIUX hierarchy
- Settings page: workspace path, config location, language, theme
- Dashboard: overall state + next actions
- Library: source-material workspace
- Analysis: Paradigm workspace
- Synthesis: Concerto workspace
- Guide: product explanation + workflow map

## Non-Goals

- no multi-library switcher in the main sidebar
- no duplication between sidebar controls and main-page controls
- no low-value configuration noise in the main navigation

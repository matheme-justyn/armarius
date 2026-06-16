# Web Sidebar Specification

## Problem Statement

The current sidebar mixes too many responsibilities:

- workflow progression
- page navigation
- library path editing
- runtime config display
- appearance preferences

This creates duplication and weak information hierarchy. It also exposes
controls that are either unstable in practice or not meaningful for the current
installed-app operating model.

## Product Assumptions

1. In installed usage, one Armarius instance is expected to manage one active
   library/workspace at a time.
2. Switching the library root from the main sidebar is not a primary workflow
   and can cause confusion or accidental drift.
3. Recursive scan should be treated as a product default, not as a user-facing
   toggle for the current phase.
4. Operational users primarily need:
   - where they are
   - what to do next
   - where settings live

## Sidebar Responsibilities

The sidebar should contain only three groups, in this order:

1. **Workflow Navigator**
   - current step
   - next recommended step
   - queue/state-aware navigation

2. **Page Navigation**
   - Overview
   - Library
   - Analysis
   - Synthesis
   - Guide
   - Catalog Assistant

3. **App Settings Entry**
   - a single link/button to a dedicated Settings page
   - no inline library root editing in the main sidebar
   - no library switching in the installed-app model
   - no inline config path dump beyond lightweight reference if needed

## Current Implementation Direction

- Main sidebar: workflow navigator + page navigation only
- Settings page: active library/workspace, config path, language, theme
- Recursive scan: hidden from UI and treated as the current default behavior

## Dedicated Settings Page

Settings should move into a dedicated page and include:

- active library path
- config file location
- language
- theme
- future advanced options

For the current phase:

- recursive scan is fixed as default behavior and should not be shown as a user
  option
- library switching may still exist internally, but should be presented in the
  dedicated Settings page only

## Dashboard / Library Split

- Dashboard = overview, queues, stale items, next actions
- Library = execution workspace
- Guide = explanation and design context

## Non-Goals

- no multi-library switcher in the main sidebar
- no duplicate workflow controls in multiple sidebar sections
- no exposing low-value toggles that users cannot meaningfully act on

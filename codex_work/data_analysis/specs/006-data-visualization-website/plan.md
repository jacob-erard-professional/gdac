# Implementation Plan: Data Visualization Website

**Branch**: `006-data-visualization-website` | **Date**: 2026-02-07 | **Spec**: `specs/006-data-visualization-website/spec.md`
**Input**: Feature request from user conversation (data visualization website for analyses in this repo).

**Note**: This template is filled in by the `/speckit.plan` command. See
`.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a standalone, read-only data visualization website that showcases the
analytics and sentiment outputs produced by this repository. The site will load
year-scoped artifacts from `outputs/analytics/<year>/` and `outputs/aux/<year>/`
and present interactive charts, tables, and timelines for key analyses (hashtags,
mentions, sentiment, ad impact, parent company impact, deep emotion impact).

## Technical Context

**Language/Version**: TypeScript or JavaScript (front-end), Python optional for build tooling
**Primary Dependencies**: TBD (frontend framework + charting library)
**Storage**: static assets + JSON/CSV/Parquet downloads from `outputs/*/<year>/`
**Testing**: basic UI smoke tests + data contract checks (optional)
**Target Platform**: static site (local dev + deployable to static hosting)
**Project Type**: data visualization website (read-only)
**Performance Goals**: fast local load, responsive charts, no server dependency
**Constraints**: no mutation of pipeline outputs; use existing artifacts
**Scale/Scope**: multi-year navigation, per-year dashboards, download links

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Outputs are year-scoped under `outputs/analytics/<year>/` and `outputs/aux/<year>/`.
- Raw data remains immutable; website is read-only.
- Pipeline remains unchanged; site consumes artifacts only.
- Documentation updates are planned.
- Optional workflows are clearly marked in the UI (some data may be missing).

## Project Structure

### Documentation (this feature)

```text
specs/006-data-visualization-website/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
site/                    # New static website (proposed)
├── public/
├── src/
│   ├── pages/
│   ├── components/
│   ├── data/
│   └── styles/
└── README.md
```

**Structure Decision**: Create a new `site/` directory with a static frontend.
Prefer a lightweight framework (Vite + React/Svelte) and a charting library
(ECharts/Plotly) for interactive visuals.

## Phase 0 — Research & Constraints

1. Inventory available artifacts in `outputs/analytics/<year>/` and `outputs/aux/<year>/`.
2. Identify formats (JSON/CSV/Parquet) and decide how to load each in-browser.
3. Decide charting library based on footprint and support for time series and bar charts.
4. Establish a minimum dataset contract (required vs optional files).

## Phase 1 — Data Model & UX Design

1. Define a unified client-side data model for:
   - hashtag frequency
   - mention frequency
   - ad sentiment
   - parent company sentiment (summary + timeslices)
   - deep sentiment (summary + timeslices)
2. Draft UI sitemap:
   - Home / Overview
   - Year selector
   - Hashtags/Mentions
   - Sentiment (BERTweet)
   - Deep Emotion
   - Parent Company Impact
   - Downloads
3. Define empty-state handling for missing optional artifacts.

## Phase 2 — Implementation

1. Scaffold `site/` with chosen framework.
2. Implement data loaders (JSON/CSV) with graceful fallbacks.
3. Build core pages and components:
   - year picker
   - summary cards
   - charts (bar, stacked, time series)
   - tables for top-N lists
4. Add download links and metadata display for reproducibility.
5. Add minimal styling and responsive layout.

## Phase 3 — Testing & Validation

1. Local smoke tests (dev server loads, charts render).
2. Data contract checks (file existence, schema validation).
3. Performance check on typical year datasets.

## Phase 4 — Documentation

1. Add `site/README.md` with setup and run instructions.
2. Update root `README.md` with visualization steps.
3. Document expected data inputs and optional features.

## Deliverables

- `site/` frontend application
- Data contract documentation
- Updated repository README

## Open Questions

- Preferred framework (React/Svelte/Vanilla)?
- Preferred charting library?
- Should the site load Parquet directly or rely on JSON/CSV exports?
- Desired hosting target (local only vs static deploy)?
